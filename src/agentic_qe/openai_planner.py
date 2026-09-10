from __future__ import annotations

import os
import sys
from pathlib import Path

from .contracts import PlannedValidation, PlannerMetadata, ValidationPlan


DEFAULT_MODEL = "gpt-5.6-luna"


def _require_sdk():
    try:
        from agents import Agent, Runner
        from agents.model_settings import ModelSettings
        from agents.mcp import MCPServerStdio
    except ImportError as exc:
        raise RuntimeError("OpenAI agent support is optional. Install with: pip install -e '.[agent]'") from exc
    return Agent, Runner, ModelSettings, MCPServerStdio


def build_validation_agent(*, model: str, mcp_server):
    Agent, _, ModelSettings, _ = _require_sdk()
    return Agent(
        name="Quality Validation Planner",
        model=model,
        instructions=(
            "You are a Senior Quality Engineering planning agent. Build a concise, executable validation plan for the "
            "supplied change. Use MCP context before finalizing it. Agent output is a proposal, not release authority. "
            "Every scenario MUST declare required_capabilities using only exact IDs returned by "
            "quality_capabilities().execution_capabilities. Never invent a supported capability. If a useful check has no "
            "registered execution capability, describe it as deferred research in rationale instead of presenting it as an "
            "executable scenario. Preserve human release accountability and never invent client or production data."
        ),
        output_type=ValidationPlan,
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
        reset_tool_choice=True,
    )


def build_planning_prompt(*, scenario: dict, relative_scenario: str, candidate_query_name: str | None = None) -> str:
    if scenario.get("sql"):
        sql_config = scenario["sql"]
        candidate = candidate_query_name or "good"
        candidate_queries = sql_config.get("candidate_queries", {})
        if candidate not in candidate_queries:
            raise ValueError(f"Unknown SQL candidate query {candidate!r}. Choose one of: {', '.join(sorted(candidate_queries))}")
        return (
            "Create a validation plan for this SQL/database scenario. First use "
            f"scenario_context('{relative_scenario}'), database_profile(scenario_path='{relative_scenario}', side='baseline'), "
            f"database_profile(scenario_path='{relative_scenario}', side='candidate', candidate_query_name='{candidate}'), "
            "and quality_capabilities(). Every executable scenario MUST populate required_capabilities with one or more "
            "exact IDs from quality_capabilities().execution_capabilities. Cover only checks the returned capability registry "
            "can actually execute, such as schema, key, duplicate-key, critical-field or database-profile validation. If a "
            "useful check is not currently executable, mention it in rationale as deferred/future research and do not create "
            "an executable scenario for it. Database tools expose metadata only; never request raw rows or credentials. "
            "Preserve human_release_approval=true and return only the structured ValidationPlan output."
        )

    source_path = scenario["source_dataset"]
    return (
        "Create a validation plan for this CSV/ETL scenario. First use "
        f"scenario_context('{relative_scenario}'), dataset_profile('{source_path}') and quality_capabilities(). Every "
        "executable scenario MUST populate required_capabilities with one or more exact IDs from "
        "quality_capabilities().execution_capabilities. Only declare scenarios supported by the registry; put unsupported "
        "ideas in rationale as deferred/future research. Preserve human_release_approval=true and include explicit "
        "decision-grade evidence requirements. Return only the structured ValidationPlan output."
    )


class OpenAIAgentsPlanGenerator:
    def __init__(self, model: str | None = None, candidate_query_name: str | None = None) -> None:
        self.model = model or os.getenv("AGENTIC_QE_MODEL") or DEFAULT_MODEL
        self.candidate_query_name = candidate_query_name

    def generate(self, *, scenario: dict, scenario_path: Path) -> PlannedValidation:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for --plan-source=openai. Use embedded/file planning for deterministic CI.")

        _, Runner, _, MCPServerStdio = _require_sdk()
        workspace = Path(os.getenv("AGENTIC_QE_WORKSPACE", os.getcwd())).resolve()
        relative_scenario = str(scenario_path.resolve().relative_to(workspace))
        mcp_env = {"AGENTIC_QE_WORKSPACE": str(workspace)}

        if scenario.get("sql"):
            sql_config = scenario["sql"]
            if str(sql_config.get("engine", "sqlite")).lower() == "sqlalchemy-env":
                for env_name in (str(sql_config.get("baseline_url_env", "")), str(sql_config.get("candidate_url_env", ""))):
                    if env_name and os.getenv(env_name):
                        mcp_env[env_name] = os.environ[env_name]
            prompt = build_planning_prompt(scenario=scenario, relative_scenario=relative_scenario, candidate_query_name=self.candidate_query_name)
        else:
            source_path = str((scenario_path.parent / scenario["source_dataset"]).resolve().relative_to(workspace))
            prompt = build_planning_prompt(scenario={**scenario, "source_dataset": source_path}, relative_scenario=relative_scenario)

        async def run_agent() -> ValidationPlan:
            async with MCPServerStdio(
                name="Agentic QE Context",
                params={"command": sys.executable, "args": ["-m", "agentic_qe.mcp_server"], "cwd": str(workspace), "env": mcp_env},
                cache_tools_list=True,
                use_structured_content=True,
            ) as server:
                agent = build_validation_agent(model=self.model, mcp_server=server)
                result = await Runner.run(agent, prompt, max_turns=8)
                output = result.final_output
                if not isinstance(output, ValidationPlan):
                    output = ValidationPlan.model_validate(output)
                return output.model_copy(update={"generated_by": f"openai-agents:{self.model}"})

        import asyncio

        plan = asyncio.run(run_agent())
        return PlannedValidation(
            plan=plan,
            metadata=PlannerMetadata(
                provider="openai-agents",
                model=self.model,
                transport="stdio",
                tool_server="Agentic QE Context",
                live_model_call=True,
                notes=[
                    "Agent was given read-only MCP context tools.",
                    "Plan scenarios must declare exact deterministic execution capabilities.",
                    "Plan-to-execution coverage is evaluated independently before the final release signal.",
                    "Database profiles expose metadata, not raw rows or credentials.",
                    "SQL candidate planning context is aligned with the candidate selected for execution.",
                ],
            ),
        )

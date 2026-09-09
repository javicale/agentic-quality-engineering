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
            "You are a Senior Quality Engineering planning agent. Build a concise, executable validation plan "
            "for the supplied change. Use the MCP context tools before finalizing the plan. Do not weaken human "
            "release accountability. Prefer risk-based scenarios, explicit assertions, decision-grade evidence, "
            "and differential testing for data transformations. Never invent production/client identifiers or data."
        ),
        output_type=ValidationPlan,
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
        reset_tool_choice=True,
    )


class OpenAIAgentsPlanGenerator:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("AGENTIC_QE_MODEL") or DEFAULT_MODEL

    def generate(self, *, scenario: dict, scenario_path: Path) -> PlannedValidation:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is required for --plan-source=openai. Use embedded/file planning for deterministic CI."
            )

        _, Runner, _, MCPServerStdio = _require_sdk()
        workspace = Path(os.getenv("AGENTIC_QE_WORKSPACE", os.getcwd())).resolve()
        relative_scenario = str(scenario_path.resolve().relative_to(workspace))
        mcp_env = {"AGENTIC_QE_WORKSPACE": str(workspace)}

        if scenario.get("sql"):
            sql_config = scenario["sql"]
            if str(sql_config.get("engine", "sqlite")).lower() == "sqlalchemy-env":
                for env_name in (
                    str(sql_config.get("baseline_url_env", "")),
                    str(sql_config.get("candidate_url_env", "")),
                ):
                    if env_name and os.getenv(env_name):
                        mcp_env[env_name] = os.environ[env_name]
            prompt = (
                "Create a validation plan for this SQL/database scenario. Before producing the final structured plan, "
                f"use scenario_context('{relative_scenario}'), then database_profile(scenario_path='{relative_scenario}', "
                "side='baseline'), database_profile(scenario_path='" + relative_scenario + "', side='candidate', "
                "candidate_query_name='good'), and quality_capabilities(). Cover schema drift, missing/extra/duplicate "
                "business keys, critical-field transformation integrity, evidence and observability. Database profile "
                "tools expose metadata only; never request raw rows or credentials. Preserve human_release_approval=true "
                "and return only the structured ValidationPlan output."
            )
        else:
            source_path = str((scenario_path.parent / scenario["source_dataset"]).resolve().relative_to(workspace))
            prompt = (
                "Create a validation plan for this scenario. Before producing the final structured plan, use the MCP "
                f"tools to inspect scenario_context('{relative_scenario}'), dataset_profile('{source_path}') and "
                "quality_capabilities(). The plan must preserve human_release_approval=true and include explicit "
                "evidence requirements. Return only the structured ValidationPlan output."
            )

        async def run_agent() -> ValidationPlan:
            async with MCPServerStdio(
                name="Agentic QE Context",
                params={
                    "command": sys.executable,
                    "args": ["-m", "agentic_qe.mcp_server"],
                    "cwd": str(workspace),
                    "env": mcp_env,
                },
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
                    "Database profiles expose metadata, not raw rows or credentials.",
                    "Plan is evaluated by a deterministic gate before execution.",
                ],
            ),
        )

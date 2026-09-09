from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .contracts import PlannedValidation, PlannerMetadata, ValidationPlan


class ValidationPlanGenerator(Protocol):
    def generate(self, *, scenario: dict, scenario_path: Path) -> PlannedValidation:
        ...


class EmbeddedPlanGenerator:
    def generate(self, *, scenario: dict, scenario_path: Path) -> PlannedValidation:
        plan = ValidationPlan.model_validate(
            {
                **scenario["validation_plan"],
                "generated_by": "embedded",
                "rationale": "Repository-owned deterministic baseline plan.",
            }
        )
        return PlannedValidation(
            plan=plan,
            metadata=PlannerMetadata(
                provider="embedded",
                live_model_call=False,
                notes=["No model call was made."],
            ),
        )


class FilePlanGenerator:
    def __init__(self, plan_path: str | Path) -> None:
        self.plan_path = Path(plan_path)

    def generate(self, *, scenario: dict, scenario_path: Path) -> PlannedValidation:
        payload = json.loads(self.plan_path.read_text(encoding="utf-8"))
        if "plan" in payload and "metadata" in payload:
            planned = PlannedValidation.model_validate({"plan": payload["plan"], "metadata": payload["metadata"]})
        else:
            planned = PlannedValidation(
                plan=ValidationPlan.model_validate(payload),
                metadata=PlannerMetadata(
                    provider="file",
                    live_model_call=False,
                    notes=[f"Loaded from {self.plan_path}."],
                ),
            )
        return planned


def get_plan_generator(
    provider: str,
    *,
    plan_path: str | None = None,
    model: str | None = None,
) -> ValidationPlanGenerator:
    normalized = provider.strip().lower()
    if normalized == "embedded":
        return EmbeddedPlanGenerator()
    if normalized == "file":
        if not plan_path:
            raise ValueError("--plan is required when --plan-source=file")
        return FilePlanGenerator(plan_path)
    if normalized == "openai":
        from .openai_planner import OpenAIAgentsPlanGenerator

        return OpenAIAgentsPlanGenerator(model=model)
    raise ValueError(f"Unsupported plan provider: {provider}")

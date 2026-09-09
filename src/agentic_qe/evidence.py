from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import ExecutionGateResult, PlannedValidation
from .models import DifferentialResult, EvalResult


def build_evidence(
    *,
    scenario: dict[str, Any],
    candidate_path: str,
    planned_validation: PlannedValidation,
    eval_result: EvalResult,
    execution_gate: ExecutionGateResult,
    differential_result: DifferentialResult | None,
    run_id: str,
) -> dict[str, Any]:
    differential = differential_result.to_dict() if differential_result else None
    return {
        "schema_version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "scenario": {
            "id": scenario["id"],
            "title": scenario["title"],
            "risk": scenario["risk"],
        },
        "candidate": candidate_path,
        "planner": planned_validation.metadata.model_dump(mode="json"),
        "validation_plan": planned_validation.plan.model_dump(mode="json"),
        "agent_eval": eval_result.to_dict(),
        "execution_gate": execution_gate.model_dump(mode="json"),
        "differential": differential,
        "summary": {
            "execution_allowed": execution_gate.allowed,
            "validation_status": differential_result.status if differential_result else "NOT_RUN",
            "difference_count": differential_result.difference_count if differential_result else 0,
            "eval_score": eval_result.score,
            "eval_threshold": eval_result.threshold,
        },
    }


def write_json(data: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import DifferentialResult, EvalResult


def build_evidence(
    *,
    scenario: dict[str, Any],
    candidate_path: str,
    eval_result: EvalResult,
    differential_result: DifferentialResult,
    run_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "scenario": {
            "id": scenario["id"],
            "title": scenario["title"],
            "risk": scenario["risk"],
        },
        "candidate": candidate_path,
        "agent_eval": eval_result.to_dict(),
        "differential": differential_result.to_dict(),
        "summary": {
            "validation_status": differential_result.status,
            "difference_count": differential_result.difference_count,
            "eval_score": eval_result.score,
            "eval_threshold": eval_result.threshold,
        },
    }


def write_json(data: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

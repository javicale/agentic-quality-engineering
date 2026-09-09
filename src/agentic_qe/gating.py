from __future__ import annotations

from .contracts import ExecutionGateResult, ValidationPlan
from .models import EvalResult


def decide_execution_gate(
    *,
    plan: ValidationPlan,
    eval_result: EvalResult,
    allow_warn_plan: bool = False,
) -> ExecutionGateResult:
    reasons: list[str] = []

    if eval_result.status != "PASS" and not allow_warn_plan:
        reasons.append(
            f"Validation-plan eval score {eval_result.score}/{eval_result.max_score} "
            f"is below threshold {eval_result.threshold}."
        )

    if not plan.human_release_approval:
        reasons.append("Plan removed the mandatory human release-approval boundary.")

    if not plan.scenarios:
        reasons.append("Plan contains no executable validation scenarios.")

    allowed = not reasons
    return ExecutionGateResult(
        allowed=allowed,
        status="PASS" if allowed else "BLOCKED",
        reasons=reasons,
        required_human_approval=True,
    )

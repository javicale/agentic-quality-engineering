from __future__ import annotations

from .contracts import ExecutionGateResult
from .models import DifferentialResult, EvalResult, ReleaseSignal


RISK_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def decide_release(
    *,
    scenario_risk: str,
    eval_result: EvalResult,
    differential_result: DifferentialResult | None,
    execution_gate: ExecutionGateResult | None = None,
) -> ReleaseSignal:
    risk = scenario_risk.upper()
    blocking_reasons: list[str] = []
    conditions: list[str] = []

    if execution_gate is not None and not execution_gate.allowed:
        return ReleaseSignal(
            decision="NO_GO",
            residual_risk="HIGH",
            blocking_reasons=[
                "Validation execution was blocked before test execution.",
                *execution_gate.reasons,
            ],
            conditions=[],
        )

    if differential_result is None:
        return ReleaseSignal(
            decision="NO_GO",
            residual_risk="HIGH",
            blocking_reasons=["No differential execution result is available."],
            conditions=[],
        )

    critical_difference = any(
        item.severity in {"CRITICAL", "HIGH"}
        for item in differential_result.differences
    )

    if differential_result.status == "FAIL" and (
        critical_difference or RISK_ORDER.get(risk, 3) >= RISK_ORDER["HIGH"]
    ):
        blocking_reasons.append(
            "High-impact differential validation failed for a high/critical-risk scenario."
        )
        return ReleaseSignal(
            decision="NO_GO",
            residual_risk="HIGH",
            blocking_reasons=blocking_reasons,
            conditions=[],
        )

    if differential_result.status == "FAIL":
        conditions.append("Resolve or explicitly accept the remaining differential findings.")

    if eval_result.status != "PASS":
        conditions.append(
            "Validation-plan eval is below the configured quality threshold and requires review."
        )

    if conditions:
        return ReleaseSignal(
            decision="CONDITIONAL_GO",
            residual_risk="MEDIUM",
            blocking_reasons=[],
            conditions=conditions,
        )

    return ReleaseSignal(
        decision="GO",
        residual_risk="LOW",
        blocking_reasons=[],
        conditions=[],
    )

from __future__ import annotations

from .contracts import ValidationPlan
from .models import EvalDimension, EvalResult


def evaluate_validation_plan(plan: ValidationPlan | dict) -> EvalResult:
    if not isinstance(plan, ValidationPlan):
        plan = ValidationPlan.model_validate(plan)

    dimensions: list[EvalDimension] = []

    scenarios = plan.scenarios
    risk_tags = set(plan.risk_coverage)
    evidence = set(plan.evidence)

    dimensions.append(
        EvalDimension(
            name="risk_coverage",
            score=20 if {"functional", "data-integrity"}.issubset(risk_tags) else 10,
            max_score=20,
            rationale="Plan should cover functional behavior and data integrity.",
        )
    )

    explicit_expected = bool(scenarios) and all(
        item.expected and item.assertion for item in scenarios
    )
    dimensions.append(
        EvalDimension(
            name="expected_result_specificity",
            score=20 if explicit_expected else 5,
            max_score=20,
            rationale="Every scenario should state an assertion and an explicit expected result.",
        )
    )

    required_evidence = {"structured-result", "execution-events"}
    dimensions.append(
        EvalDimension(
            name="evidence_requirements",
            score=15 if required_evidence.issubset(evidence) else 5,
            max_score=15,
            rationale="Decision-grade evidence should include structured results and execution events.",
        )
    )

    dimensions.append(
        EvalDimension(
            name="differential_testing",
            score=15 if plan.differential_testing else 0,
            max_score=15,
            rationale="Data transformations should define a differential comparison strategy.",
        )
    )

    dimensions.append(
        EvalDimension(
            name="human_accountability",
            score=20 if plan.human_release_approval else 0,
            max_score=20,
            rationale="Agent-assisted validation must preserve human release accountability.",
        )
    )

    grounded = bool(plan.requested_tools) or plan.generated_by == "embedded"
    dimensions.append(
        EvalDimension(
            name="tool_grounding",
            score=10 if grounded else 0,
            max_score=10,
            rationale="Agent-generated plans should declare the tools/capabilities used to ground the plan.",
        )
    )

    score = sum(item.score for item in dimensions)
    max_score = sum(item.max_score for item in dimensions)
    threshold = 80

    return EvalResult(
        status="PASS" if score >= threshold else "WARN",
        score=score,
        max_score=max_score,
        threshold=threshold,
        dimensions=dimensions,
    )

from __future__ import annotations

from .models import EvalDimension, EvalResult


def evaluate_validation_plan(plan: dict) -> EvalResult:
    dimensions: list[EvalDimension] = []

    scenarios = plan.get("scenarios", [])
    risk_tags = {str(item).lower() for item in plan.get("risk_coverage", [])}
    evidence = {str(item).lower() for item in plan.get("evidence", [])}

    dimensions.append(
        EvalDimension(
            name="risk_coverage",
            score=20 if {"functional", "data-integrity"}.issubset(risk_tags) else 10,
            max_score=20,
            rationale="Plan should cover functional behavior and data integrity.",
        )
    )

    explicit_expected = bool(scenarios) and all(
        item.get("expected") and item.get("assertion") for item in scenarios
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
            score=20 if required_evidence.issubset(evidence) else 10,
            max_score=20,
            rationale="Decision-grade evidence should include structured results and execution events.",
        )
    )

    dimensions.append(
        EvalDimension(
            name="differential_testing",
            score=20 if plan.get("differential_testing") is True else 0,
            max_score=20,
            rationale="Data transformations should define a differential comparison strategy.",
        )
    )

    dimensions.append(
        EvalDimension(
            name="human_accountability",
            score=20 if plan.get("human_release_approval") is True else 0,
            max_score=20,
            rationale="Agent-assisted validation must preserve human release accountability.",
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

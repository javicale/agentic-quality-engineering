from __future__ import annotations

from collections.abc import Iterable

from .contracts import ValidationPlan
from .models import EvalDimension, EvalResult


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def _corpus(values: Iterable[str]) -> str:
    return " | ".join(_normalize(value) for value in values if value)


def _contains_any(corpus: str, signals: set[str]) -> bool:
    return any(_normalize(signal) in corpus for signal in signals)


def _is_specific(value: str) -> bool:
    normalized = _normalize(value)
    vague = {
        "looks correct",
        "works",
        "works correctly",
        "acceptable",
        "valid",
        "pass",
        "passes",
        "inspect output",
    }
    return len(normalized) >= 12 and normalized not in vague


def evaluate_validation_plan(plan: ValidationPlan | dict) -> EvalResult:
    """Score an agent plan deterministically without requiring magic exact tags.

    Agent-generated text is expected to be natural language. The evaluator therefore
    normalizes a small, auditable taxonomy of signals instead of requiring literal
    fixture tokens such as ``data-integrity`` or ``execution-events``.
    """
    if not isinstance(plan, ValidationPlan):
        plan = ValidationPlan.model_validate(plan)

    dimensions: list[EvalDimension] = []
    scenarios = plan.scenarios

    risk_corpus = _corpus(plan.risk_coverage)
    functional_signals = {
        "functional",
        "behavior",
        "precision",
        "rounding",
        "truncation",
        "formatting",
        "representation",
        "transformation",
        "regression",
    }
    integrity_signals = {
        "data integrity",
        "integrity",
        "record",
        "key",
        "duplicate",
        "duplication",
        "loss",
        "null",
        "blank",
        "mutation",
        "completeness",
        "reconciliation",
    }
    functional_covered = _contains_any(risk_corpus, functional_signals)
    integrity_covered = _contains_any(risk_corpus, integrity_signals)
    risk_score = 20 if functional_covered and integrity_covered else 10 if functional_covered or integrity_covered else 0
    dimensions.append(
        EvalDimension(
            name="risk_coverage",
            score=risk_score,
            max_score=20,
            rationale=(
                "Plan should cover functional behavior and data integrity. "
                f"Detected functional={functional_covered}, data_integrity={integrity_covered}."
            ),
        )
    )

    explicit_expected = bool(scenarios) and all(
        _is_specific(item.assertion) and _is_specific(item.expected) for item in scenarios
    )
    dimensions.append(
        EvalDimension(
            name="expected_result_specificity",
            score=20 if explicit_expected else 5,
            max_score=20,
            rationale="Every scenario should state a non-vague assertion and explicit expected result.",
        )
    )

    evidence_items = list(plan.evidence)
    for scenario in scenarios:
        evidence_items.extend(scenario.evidence)
    evidence_corpus = _corpus(evidence_items)
    structured_signals = {
        "structured result",
        "machine readable",
        "json",
        "csv",
        "report",
        "result",
        "comparison",
        "artifact",
        "checksum",
        "failure sample",
    }
    execution_signals = {
        "execution event",
        "execution",
        "event",
        "log",
        "trace",
        "timestamp",
        "run id",
        "environment",
        "version",
    }
    structured_evidence = _contains_any(evidence_corpus, structured_signals)
    execution_evidence = _contains_any(evidence_corpus, execution_signals)
    evidence_score = 15 if structured_evidence and execution_evidence else 8 if structured_evidence or execution_evidence else 0
    dimensions.append(
        EvalDimension(
            name="evidence_requirements",
            score=evidence_score,
            max_score=15,
            rationale=(
                "Decision-grade evidence should include structured results and execution events. "
                f"Detected structured={structured_evidence}, execution={execution_evidence}."
            ),
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

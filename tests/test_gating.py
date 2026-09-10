import json
from pathlib import Path

from agentic_qe.contracts import ValidationPlan
from agentic_qe.evals import evaluate_validation_plan
from agentic_qe.gating import decide_execution_gate


EXAMPLE = Path("examples/etl-decimal-precision")


def plan(name: str) -> ValidationPlan:
    return ValidationPlan.model_validate(json.loads((EXAMPLE / name).read_text()))


def test_strong_plan_is_allowed_to_execute():
    candidate = plan("agent-proposal-good.json")
    gate = decide_execution_gate(plan=candidate, eval_result=evaluate_validation_plan(candidate))
    assert gate.allowed is True
    assert gate.status == "PASS"


def test_weak_plan_is_blocked_before_execution():
    candidate = plan("agent-proposal-weak.json")
    gate = decide_execution_gate(plan=candidate, eval_result=evaluate_validation_plan(candidate))
    assert gate.allowed is False
    assert gate.status == "BLOCKED"
    assert any("human" in reason.lower() for reason in gate.reasons)
    assert any("required_capability" in reason for reason in gate.reasons)


def test_legacy_plan_without_capability_mapping_is_not_executable_under_v4():
    candidate = ValidationPlan.model_validate({
        "objective": "Legacy otherwise-strong plan.",
        "risk_coverage": ["functional", "data integrity"],
        "differential_testing": True,
        "human_release_approval": True,
        "evidence": ["structured result", "execution events"],
        "requested_tools": ["quality_capabilities"],
        "rationale": "Predates V4 traceability.",
        "generated_by": "legacy",
        "scenarios": [{
            "name": "legacy_scenario",
            "assertion": "candidate must match the deterministic expectation",
            "expected": "candidate matches the deterministic expectation exactly",
            "priority": "HIGH",
            "evidence": ["structured result"],
        }],
    })
    gate = decide_execution_gate(plan=candidate, eval_result=evaluate_validation_plan(candidate))
    assert gate.status == "BLOCKED"
    assert any("required_capability" in reason for reason in gate.reasons)

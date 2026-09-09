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

import json
from pathlib import Path

from agentic_qe.contracts import ValidationPlan
from agentic_qe.evals import evaluate_validation_plan


EXAMPLE = Path("examples/etl-decimal-precision")


def load_plan(name: str) -> ValidationPlan:
    return ValidationPlan.model_validate(json.loads((EXAMPLE / name).read_text()))


def test_strong_agent_plan_passes_eval():
    result = evaluate_validation_plan(load_plan("agent-proposal-good.json"))
    assert result.status == "PASS"
    assert result.score == result.max_score == 100


def test_weak_agent_plan_warns():
    result = evaluate_validation_plan(load_plan("agent-proposal-weak.json"))
    assert result.status == "WARN"
    assert result.score < result.threshold

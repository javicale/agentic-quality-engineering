from agentic_qe.contracts import ExecutionGateResult
from agentic_qe.models import DifferentialResult, EvalDimension, EvalResult
from agentic_qe.release import decide_release


def passing_eval() -> EvalResult:
    return EvalResult(
        status="PASS",
        score=100,
        max_score=100,
        threshold=80,
        dimensions=[EvalDimension("all", 100, 100, "ok")],
    )


def test_release_go_when_gate_and_differential_pass():
    signal = decide_release(
        scenario_risk="HIGH",
        eval_result=passing_eval(),
        differential_result=DifferentialResult("PASS", 2, 0, []),
        execution_gate=ExecutionGateResult(allowed=True, status="PASS"),
    )
    assert signal.decision == "GO"


def test_release_no_go_when_execution_gate_blocks():
    signal = decide_release(
        scenario_risk="HIGH",
        eval_result=passing_eval(),
        differential_result=None,
        execution_gate=ExecutionGateResult(
            allowed=False,
            status="BLOCKED",
            reasons=["weak agent plan"],
        ),
    )
    assert signal.decision == "NO_GO"
    assert any("weak agent plan" in reason for reason in signal.blocking_reasons)

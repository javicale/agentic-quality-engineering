from agentic_qe.models import Difference, DifferentialResult, EvalResult
from agentic_qe.release import decide_release


GOOD_EVAL = EvalResult(
    status="PASS",
    score=100,
    max_score=100,
    threshold=80,
    dimensions=[],
)


def test_high_risk_critical_difference_blocks_release():
    differential = DifferentialResult(
        status="FAIL",
        compared_rows=1,
        difference_count=1,
        differences=[
            Difference(
                row_key="A-1",
                field="value",
                expected="0.00",
                observed="0",
                severity="CRITICAL",
                message="precision lost",
            )
        ],
    )

    signal = decide_release(
        scenario_risk="HIGH",
        eval_result=GOOD_EVAL,
        differential_result=differential,
    )

    assert signal.decision == "NO_GO"
    assert signal.residual_risk == "HIGH"


def test_clean_validation_produces_go():
    differential = DifferentialResult(
        status="PASS",
        compared_rows=1,
        difference_count=0,
        differences=[],
    )

    signal = decide_release(
        scenario_risk="HIGH",
        eval_result=GOOD_EVAL,
        differential_result=differential,
    )

    assert signal.decision == "GO"

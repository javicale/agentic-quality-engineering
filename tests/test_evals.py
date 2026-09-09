from agentic_qe.evals import evaluate_validation_plan


def test_complete_validation_plan_passes_eval():
    plan = {
        "risk_coverage": ["functional", "data-integrity"],
        "differential_testing": True,
        "human_release_approval": True,
        "evidence": ["structured-result", "execution-events"],
        "scenarios": [
            {
                "assertion": "exact comparison",
                "expected": "value preserved",
            }
        ],
    }

    result = evaluate_validation_plan(plan)

    assert result.status == "PASS"
    assert result.score == result.max_score == 100


def test_weak_plan_requires_review():
    result = evaluate_validation_plan({"scenarios": []})

    assert result.status == "WARN"
    assert result.score < result.threshold

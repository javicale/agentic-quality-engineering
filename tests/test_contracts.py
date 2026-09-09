from agentic_qe.contracts import ValidationPlan


def test_validation_plan_normalizes_tokens():
    plan = ValidationPlan.model_validate(
        {
            "risk_coverage": ["Functional", "DATA-INTEGRITY", "functional"],
            "differential_testing": True,
            "human_release_approval": True,
            "evidence": ["Structured-Result", "execution-events"],
            "requested_tools": ["Scenario_Context", "scenario_context"],
            "scenarios": [
                {
                    "name": "precision",
                    "assertion": "exact match",
                    "expected": "precision preserved",
                }
            ],
        }
    )

    assert plan.risk_coverage == ["functional", "data-integrity"]
    assert plan.evidence == ["structured-result", "execution-events"]
    assert plan.requested_tools == ["scenario_context"]

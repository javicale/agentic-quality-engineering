import json
from pathlib import Path

from agentic_qe.evals import evaluate_validation_plan


FIXTURE = Path("examples/sql-etl-reconciliation/live-plan-verified-2026-09-09.json")


def test_verified_live_sql_plan_remains_a_valid_regression_fixture():
    plan = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = evaluate_validation_plan(plan)
    assert result.status == "PASS"
    assert result.score == 100
    assert plan["human_release_approval"] is True
    assert plan["differential_testing"] is True
    assert len(plan["scenarios"]) == 8

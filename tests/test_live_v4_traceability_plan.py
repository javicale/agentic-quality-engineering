import json
from pathlib import Path

from agentic_qe.contracts import ValidationPlan
from agentic_qe.evals import evaluate_validation_plan
from agentic_qe.gating import decide_execution_gate
from agentic_qe.sql_pipeline import execute_sql_pipeline


PLAN = Path("examples/sql-etl-reconciliation/live-plan-v4-traceable-2026-09-09.json")
SCENARIO = "examples/sql-etl-reconciliation/scenario.json"


def test_verified_v4_live_plan_declares_registered_execution_capabilities():
    plan = ValidationPlan.model_validate(json.loads(PLAN.read_text(encoding="utf-8")))
    evaluation = evaluate_validation_plan(plan)
    gate = decide_execution_gate(plan=plan, eval_result=evaluation)
    assert evaluation.status == "PASS"
    assert evaluation.score == 90
    assert gate.status == "PASS"
    assert len(plan.scenarios) == 5
    assert all(scenario.required_capabilities for scenario in plan.scenarios)


def test_verified_v4_live_plan_replays_with_complete_traceability(tmp_path):
    result = execute_sql_pipeline(
        scenario_path=SCENARIO,
        output_dir=str(tmp_path),
        candidate_query_name="good",
        plan_source="file",
        plan_path=str(PLAN),
    )
    trace = result["traceability"]
    assert result["release"]["decision"] == "GO"
    assert result["release"]["residual_risk"] == "LOW"
    assert trace["coverage_gate"]["status"] == "PASS"
    assert trace["summary"] == {
        "planned_scenarios": 5,
        "passed": 5,
        "failed": 0,
        "not_executed": 0,
        "supported": 5,
        "deferred": 0,
        "unsupported": 0,
    }

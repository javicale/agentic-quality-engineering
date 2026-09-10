import json

from agentic_qe.sql_pipeline import execute_sql_pipeline

SCENARIO = "examples/sql-etl-reconciliation/scenario.json"


def test_sql_pipeline_good_candidate_go(tmp_path):
    result = execute_sql_pipeline(scenario_path=SCENARIO, output_dir=str(tmp_path / "good"), candidate_query_name="good")
    assert result["release"]["decision"] == "GO"
    assert result["differential"]["difference_count"] == 0
    evidence = json.loads((tmp_path / "good" / "evidence.json").read_text())
    assert evidence["database"]["raw_rows_exposed_to_agent"] is False
    scope = json.loads((tmp_path / "good" / "execution-scope.json").read_text())
    assert scope["scenario_level_traceability"] == "NOT_IMPLEMENTED"
    assert all(item["status"] == "PASS" for item in scope["deterministic_checks"])


def test_sql_pipeline_regression_no_go(tmp_path):
    result = execute_sql_pipeline(scenario_path=SCENARIO, output_dir=str(tmp_path / "bad"), candidate_query_name="regression")
    assert result["release"]["decision"] == "NO_GO"
    assert result["differential"]["difference_count"] >= 3
    statuses = {item["id"]: item["status"] for item in result["execution_scope"]["deterministic_checks"]}
    assert statuses["business-key-reconciliation"] == "FAIL"
    assert statuses["critical-field-differential"] == "FAIL"

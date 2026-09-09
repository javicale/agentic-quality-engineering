import json

from agentic_qe.sql_pipeline import execute_sql_pipeline

SCENARIO = "examples/sql-etl-reconciliation/scenario.json"


def test_sql_pipeline_good_candidate_go(tmp_path):
    result = execute_sql_pipeline(scenario_path=SCENARIO, output_dir=str(tmp_path / "good"), candidate_query_name="good")
    assert result["release"]["decision"] == "GO"
    assert result["differential"]["difference_count"] == 0
    evidence = json.loads((tmp_path / "good" / "evidence.json").read_text())
    assert evidence["database"]["raw_rows_exposed_to_agent"] is False


def test_sql_pipeline_regression_no_go(tmp_path):
    result = execute_sql_pipeline(scenario_path=SCENARIO, output_dir=str(tmp_path / "bad"), candidate_query_name="regression")
    assert result["release"]["decision"] == "NO_GO"
    assert result["differential"]["difference_count"] >= 3

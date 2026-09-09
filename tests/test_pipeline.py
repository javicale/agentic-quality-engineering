import json
from pathlib import Path

from agentic_qe.pipeline import execute_pipeline, generate_validation_plan


SCENARIO = "examples/etl-decimal-precision/scenario.json"
GOOD = "examples/etl-decimal-precision/candidate-good.csv"
REGRESSION = "examples/etl-decimal-precision/candidate-regression.csv"
GOOD_PLAN = "examples/etl-decimal-precision/agent-proposal-good.json"
WEAK_PLAN = "examples/etl-decimal-precision/agent-proposal-weak.json"


def test_embedded_pipeline_produces_go_and_v2_evidence(tmp_path: Path):
    result = execute_pipeline(
        scenario_path=SCENARIO,
        candidate_path=GOOD,
        output_dir=str(tmp_path),
    )
    assert result["release"]["decision"] == "GO"
    assert result["execution_gate"]["allowed"] is True
    evidence = json.loads((tmp_path / "evidence.json").read_text())
    assert evidence["schema_version"] == "2.0"
    assert evidence["planner"]["provider"] == "embedded"
    assert (tmp_path / "validation-plan.json").exists()
    assert (tmp_path / "execution-gate.json").exists()


def test_regression_produces_no_go(tmp_path: Path):
    result = execute_pipeline(
        scenario_path=SCENARIO,
        candidate_path=REGRESSION,
        output_dir=str(tmp_path),
    )
    assert result["release"]["decision"] == "NO_GO"
    assert result["differential"]["difference_count"] > 0


def test_strong_file_agent_plan_executes(tmp_path: Path):
    result = execute_pipeline(
        scenario_path=SCENARIO,
        candidate_path=GOOD,
        output_dir=str(tmp_path),
        plan_source="file",
        plan_path=GOOD_PLAN,
    )
    assert result["planner"]["provider"] == "file"
    assert result["eval"]["score"] == 100
    assert result["release"]["decision"] == "GO"


def test_weak_agent_plan_is_blocked_before_data_execution(tmp_path: Path):
    result = execute_pipeline(
        scenario_path=SCENARIO,
        candidate_path=GOOD,
        output_dir=str(tmp_path),
        plan_source="file",
        plan_path=WEAK_PLAN,
    )
    assert result["execution_gate"]["status"] == "BLOCKED"
    assert result["differential"] is None
    assert result["release"]["decision"] == "NO_GO"
    events = (tmp_path / "events.jsonl").read_text()
    assert "execution.skipped" in events
    assert "test_data.loaded" not in events


def test_plan_command_contract_for_file_provider():
    result = generate_validation_plan(
        scenario_path=SCENARIO,
        provider="file",
        plan_path=GOOD_PLAN,
    )
    assert result["metadata"]["provider"] == "file"
    assert result["execution_gate"]["allowed"] is True

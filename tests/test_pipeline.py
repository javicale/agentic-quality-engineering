from pathlib import Path

from agentic_qe.pipeline import execute_pipeline


ROOT = Path(__file__).parents[1]
SCENARIO = ROOT / "examples" / "etl-decimal-precision" / "scenario.json"


def test_good_candidate_generates_go_and_evidence(tmp_path):
    candidate = ROOT / "examples" / "etl-decimal-precision" / "candidate-good.csv"

    result = execute_pipeline(
        scenario_path=str(SCENARIO),
        candidate_path=str(candidate),
        output_dir=str(tmp_path),
    )

    assert result["release"]["decision"] == "GO"
    assert (tmp_path / "evidence.json").exists()
    assert (tmp_path / "events.jsonl").exists()


def test_regression_candidate_generates_no_go(tmp_path):
    candidate = ROOT / "examples" / "etl-decimal-precision" / "candidate-regression.csv"

    result = execute_pipeline(
        scenario_path=str(SCENARIO),
        candidate_path=str(candidate),
        output_dir=str(tmp_path),
    )

    assert result["release"]["decision"] == "NO_GO"
    assert result["differential"]["difference_count"] == 4

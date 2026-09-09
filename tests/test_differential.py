from agentic_qe.data import load_csv
from agentic_qe.differential import compare_datasets


def test_differential_passes_good_candidate():
    expected = load_csv("examples/etl-decimal-precision/expected.csv")
    candidate = load_csv("examples/etl-decimal-precision/candidate-good.csv")
    result = compare_datasets(expected, candidate, key_field="record_id", critical_fields=["odometer_start", "odometer_end"])
    assert result.status == "PASS"
    assert result.difference_count == 0


def test_differential_detects_precision_regression():
    expected = load_csv("examples/etl-decimal-precision/expected.csv")
    candidate = load_csv("examples/etl-decimal-precision/candidate-regression.csv")
    result = compare_datasets(expected, candidate, key_field="record_id", critical_fields=["odometer_start", "odometer_end"])
    assert result.status == "FAIL"
    assert result.difference_count > 0

from agentic_qe.profile import profile_csv


def test_profile_reports_decimal_scale_without_exposing_rows():
    result = profile_csv("examples/etl-decimal-precision/source.csv")
    assert result["row_count"] > 0
    assert "odometer_start" in result["columns"]
    scales = result["profiles"]["odometer_start"]["decimal_scale_distribution"]
    assert scales.get(2, scales.get("2")) > 0
    assert "rows" not in result

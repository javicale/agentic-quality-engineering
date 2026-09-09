from agentic_qe.differential import compare_datasets


def test_exact_representation_passes():
    expected = [{"record_id": "A-1", "value": "0.00"}]
    candidate = [{"record_id": "A-1", "value": "0.00"}]

    result = compare_datasets(
        expected,
        candidate,
        key_field="record_id",
        critical_fields=["value"],
    )

    assert result.status == "PASS"
    assert result.difference_count == 0


def test_decimal_rounding_is_detected_as_critical():
    expected = [{"record_id": "A-1", "value": "0.00"}]
    candidate = [{"record_id": "A-1", "value": "0"}]

    result = compare_datasets(
        expected,
        candidate,
        key_field="record_id",
        critical_fields=["value"],
    )

    assert result.status == "FAIL"
    assert result.difference_count == 1
    assert result.differences[0].severity == "CRITICAL"

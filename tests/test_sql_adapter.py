from pathlib import Path

import pytest

from agentic_qe.sql_adapter import SQLiteDatabaseAdapter, compare_query_snapshots

SETUP = Path("examples/sql-etl-reconciliation/setup.sql")


def make_adapter(tmp_path):
    adapter = SQLiteDatabaseAdapter(tmp_path / "test.db")
    adapter.initialize_from_script(SETUP)
    return adapter


def test_good_sql_candidate_passes(tmp_path):
    adapter = make_adapter(tmp_path)
    baseline = adapter.query("SELECT transaction_id, amount, status, event_time FROM source_transactions ORDER BY transaction_id")
    candidate = adapter.query("SELECT transaction_id, amount, status, event_time FROM target_transactions_good ORDER BY transaction_id")
    result = compare_query_snapshots(baseline, candidate, key_field="transaction_id", critical_fields=["amount", "status", "event_time"])
    assert result.status == "PASS"
    assert result.difference_count == 0
    assert result.compared_rows == 3


def test_regression_detects_precision_and_missing_row(tmp_path):
    adapter = make_adapter(tmp_path)
    baseline = adapter.query("SELECT transaction_id, amount, status, event_time FROM source_transactions ORDER BY transaction_id")
    candidate = adapter.query("SELECT transaction_id, amount, status, event_time FROM target_transactions_regression ORDER BY transaction_id")
    result = compare_query_snapshots(baseline, candidate, key_field="transaction_id", critical_fields=["amount", "status", "event_time"])
    assert result.status == "FAIL"
    assert result.difference_count >= 3
    assert any(item.row_key == "TX-001" and item.field == "amount" for item in result.differences)
    assert any(item.row_key == "TX-003" for item in result.differences)


def test_read_only_query_boundary(tmp_path):
    adapter = make_adapter(tmp_path)
    with pytest.raises(ValueError, match="read-only"):
        adapter.query("DELETE FROM source_transactions")

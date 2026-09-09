from pathlib import Path

import pytest

from agentic_qe.sql_adapter import QuerySnapshot, SQLiteDatabaseAdapter, compare_query_snapshots

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
    assert any("transaction_id=TX-001" in item.row_key and item.field == "amount" for item in result.differences)
    assert any("transaction_id=TX-003" in item.row_key for item in result.differences)


def test_schema_drift_is_explicit_finding(tmp_path):
    adapter = make_adapter(tmp_path)
    baseline = adapter.query("SELECT transaction_id, amount, status, event_time FROM source_transactions ORDER BY transaction_id")
    candidate = adapter.query("SELECT transaction_id, amount, status FROM target_transactions_good ORDER BY transaction_id")
    result = compare_query_snapshots(baseline, candidate, key_field="transaction_id", critical_fields=["event_time"])
    assert result.status == "FAIL"
    assert any(item.row_key == "__schema__" and item.field == "event_time" for item in result.differences)


def test_duplicate_business_key_is_not_silently_overwritten():
    baseline = QuerySnapshot(
        columns=["transaction_id", "amount"],
        rows=[{"transaction_id": "TX-1", "amount": "1.00"}],
        provider="test",
    )
    candidate = QuerySnapshot(
        columns=["transaction_id", "amount"],
        rows=[
            {"transaction_id": "TX-1", "amount": "1.00"},
            {"transaction_id": "TX-1", "amount": "1.00"},
        ],
        provider="test",
    )
    result = compare_query_snapshots(baseline, candidate, key_field="transaction_id", critical_fields=["amount"])
    assert result.status == "FAIL"
    assert any(item.field == "__key__" and item.severity == "CRITICAL" for item in result.differences)


def test_composite_business_key_reconciliation():
    baseline = QuerySnapshot(
        columns=["tenant", "transaction_id", "amount"],
        rows=[
            {"tenant": "A", "transaction_id": "1", "amount": "1.00"},
            {"tenant": "B", "transaction_id": "1", "amount": "2.00"},
        ],
        provider="test",
    )
    candidate = QuerySnapshot(
        columns=["tenant", "transaction_id", "amount"],
        rows=[
            {"tenant": "A", "transaction_id": "1", "amount": "1.00"},
            {"tenant": "B", "transaction_id": "1", "amount": "2.01"},
        ],
        provider="test",
    )
    result = compare_query_snapshots(
        baseline,
        candidate,
        key_fields=["tenant", "transaction_id"],
        critical_fields=["amount"],
    )
    assert result.status == "FAIL"
    assert result.difference_count == 1
    assert result.differences[0].row_key == "tenant=B | transaction_id=1"
    assert result.differences[0].severity == "CRITICAL"


def test_database_profile_reports_key_cardinality(tmp_path):
    adapter = make_adapter(tmp_path)
    profile = adapter.profile(
        "SELECT transaction_id, amount, status, event_time FROM source_transactions",
        key_fields=["transaction_id"],
    )
    assert profile["row_count"] == 3
    assert profile["distinct_key_count"] == 3
    assert profile["duplicate_key_count"] == 0
    assert "rows" not in profile


def test_read_only_query_boundary(tmp_path):
    adapter = make_adapter(tmp_path)
    with pytest.raises(ValueError, match="read-only"):
        adapter.query("DELETE FROM source_transactions")
    with pytest.raises(ValueError, match="Mutating"):
        adapter.query("WITH changed AS (DELETE FROM source_transactions RETURNING *) SELECT * FROM changed")

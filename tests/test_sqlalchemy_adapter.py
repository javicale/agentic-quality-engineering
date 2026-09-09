import sqlite3

import pytest

from agentic_qe.sql_adapter import SQLAlchemyDatabaseAdapter


pytestmark = pytest.mark.database_integration


def test_sqlalchemy_adapter_resolves_url_from_environment_without_exposing_it(tmp_path, monkeypatch):
    pytest.importorskip("sqlalchemy")
    database_path = tmp_path / "portable.db"
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            CREATE TABLE transactions (
              tenant TEXT NOT NULL,
              transaction_id TEXT NOT NULL,
              amount TEXT NOT NULL
            );
            INSERT INTO transactions VALUES
              ('A', '1', '10.25'),
              ('B', '1', '20.50');
            """
        )
        connection.commit()
    finally:
        connection.close()

    database_url = f"sqlite+pysqlite:///{database_path}"
    monkeypatch.setenv("TEST_DATABASE_URL", database_url)
    adapter = SQLAlchemyDatabaseAdapter("TEST_DATABASE_URL")
    snapshot = adapter.query(
        "SELECT tenant, transaction_id, amount FROM transactions ORDER BY tenant"
    )
    profile = adapter.profile(
        "SELECT tenant, transaction_id, amount FROM transactions ORDER BY tenant",
        key_fields=["tenant", "transaction_id"],
    )
    assert snapshot.provider == "sqlalchemy-env"
    assert snapshot.row_count == 2
    assert profile["distinct_key_count"] == 2
    assert profile["duplicate_key_count"] == 0
    assert database_url not in str(profile)

from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .differential import compare_tabular
from .models import Difference, DifferentialResult


_READ_ONLY = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)
_MUTATING_TOKEN = re.compile(
    r"\b(insert|update|delete|merge|drop|alter|create|replace|truncate|attach|detach|vacuum|pragma|grant|revoke)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class QuerySnapshot:
    columns: list[str]
    rows: list[dict[str, str | None]]
    provider: str = "unknown"

    @property
    def row_count(self) -> int:
        return len(self.rows)


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.hex()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            pass
    return str(value)


def _validate_read_only_query(query: str) -> None:
    stripped = query.strip()
    if not _READ_ONLY.match(stripped):
        raise ValueError("Only read-only SELECT/CTE queries are allowed.")
    statements = [part for part in stripped.split(";") if part.strip()]
    if len(statements) != 1:
        raise ValueError("Exactly one read-only SQL statement is allowed.")
    if _MUTATING_TOKEN.search(stripped):
        raise ValueError("Mutating SQL is not allowed in the Database Differential Adapter.")


def profile_snapshot(snapshot: QuerySnapshot, *, key_fields: list[str] | None = None) -> dict[str, Any]:
    keys = key_fields or []
    null_counts = {
        column: sum(1 for row in snapshot.rows if row.get(column) is None)
        for column in snapshot.columns
    }
    key_values: list[tuple[str | None, ...]] = []
    if keys and all(field in snapshot.columns for field in keys):
        key_values = [tuple(row.get(field) for field in keys) for row in snapshot.rows]
    distinct_key_count = len(set(key_values)) if keys else None
    duplicate_key_count = (
        len(key_values) - distinct_key_count if distinct_key_count is not None else None
    )
    return {
        "provider": snapshot.provider,
        "columns": snapshot.columns,
        "row_count": snapshot.row_count,
        "null_counts": null_counts,
        "key_fields": keys,
        "distinct_key_count": distinct_key_count,
        "duplicate_key_count": duplicate_key_count,
    }


class SQLiteDatabaseAdapter:
    """Deterministic SQLite adapter used by the credential-free V3 reference pipeline."""

    provider = "sqlite"

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).resolve()

    def initialize_from_script(self, script_path: str | Path) -> None:
        """Create a synthetic/local fixture outside the Agent/MCP read-only boundary."""
        script = Path(script_path).read_text(encoding="utf-8")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        if self.database_path.exists():
            self.database_path.unlink()
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(script)

    def query(self, sql: str) -> QuerySnapshot:
        _validate_read_only_query(sql)
        uri = f"file:{self.database_path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            cursor = connection.execute(sql)
            columns = [item[0] for item in cursor.description or []]
            rows = [
                {column: _stringify(value) for column, value in zip(columns, row)}
                for row in cursor.fetchall()
            ]
        return QuerySnapshot(columns=columns, rows=rows, provider=self.provider)

    def profile(self, sql: str, *, key_fields: list[str] | None = None) -> dict[str, Any]:
        return profile_snapshot(self.query(sql), key_fields=key_fields)


class SQLAlchemyDatabaseAdapter:
    """Portable read-only adapter whose database URL is resolved only from an environment variable."""

    provider = "sqlalchemy-env"

    def __init__(self, url_env: str) -> None:
        self.url_env = url_env

    def query(self, sql: str) -> QuerySnapshot:
        _validate_read_only_query(sql)
        database_url = os.getenv(self.url_env)
        if not database_url:
            raise RuntimeError(f"Database URL environment variable {self.url_env!r} is not configured.")
        try:
            from sqlalchemy import create_engine, text
        except ImportError as exc:
            raise RuntimeError(
                "SQLAlchemy support is optional. Install with: pip install -e '.[database]'"
            ) from exc

        engine = create_engine(database_url)
        try:
            with engine.connect() as connection:
                result = connection.execute(text(sql))
                columns = list(result.keys())
                rows = [
                    {column: _stringify(row._mapping[column]) for column in columns}
                    for row in result
                ]
        finally:
            engine.dispose()
        return QuerySnapshot(columns=columns, rows=rows, provider=self.provider)

    def profile(self, sql: str, *, key_fields: list[str] | None = None) -> dict[str, Any]:
        return profile_snapshot(self.query(sql), key_fields=key_fields)


def compare_query_snapshots(
    baseline: QuerySnapshot,
    candidate: QuerySnapshot,
    *,
    key_field: str | None = None,
    key_fields: list[str] | None = None,
    critical_fields: list[str] | None = None,
) -> DifferentialResult:
    critical_fields = critical_fields or []
    keys = key_fields or ([key_field] if key_field else [])
    if not keys:
        raise ValueError("At least one SQL differential key field is required.")

    schema_differences: list[Difference] = []
    baseline_columns = set(baseline.columns)
    candidate_columns = set(candidate.columns)

    for column in sorted(baseline_columns - candidate_columns):
        schema_differences.append(
            Difference(
                row_key="__schema__",
                field=column,
                expected="present",
                observed="missing",
                severity="CRITICAL",
                message=f"Required baseline column '{column}' is missing from candidate query.",
            )
        )
    for column in sorted(candidate_columns - baseline_columns):
        schema_differences.append(
            Difference(
                row_key="__schema__",
                field=column,
                expected="absent",
                observed="present",
                severity="HIGH",
                message=f"Candidate query exposes extra column '{column}'.",
            )
        )

    missing_keys = [
        field for field in keys
        if field not in baseline_columns or field not in candidate_columns
    ]
    for field in missing_keys:
        schema_differences.append(
            Difference(
                row_key="__schema__",
                field=field,
                expected="key present in both queries",
                observed="missing from one or both queries",
                severity="CRITICAL",
                message="Every differential key field must exist in both query results.",
            )
        )
    if missing_keys:
        return DifferentialResult(
            status="FAIL",
            compared_rows=0,
            difference_count=len(schema_differences),
            differences=schema_differences,
        )

    common_columns = baseline_columns & candidate_columns
    baseline_rows = [
        {field: value for field, value in row.items() if field in common_columns}
        for row in baseline.rows
    ]
    candidate_rows = [
        {field: value for field, value in row.items() if field in common_columns}
        for row in candidate.rows
    ]
    row_result = compare_tabular(
        baseline_rows,
        candidate_rows,
        key_fields=keys,
        critical_fields=[field for field in critical_fields if field in common_columns],
    )
    differences = [*schema_differences, *row_result.differences]
    return DifferentialResult(
        status="FAIL" if differences else "PASS",
        compared_rows=row_result.compared_rows,
        difference_count=len(differences),
        differences=differences,
    )

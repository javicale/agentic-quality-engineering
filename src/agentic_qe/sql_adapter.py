from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .differential import compare_datasets
from .models import Difference, DifferentialResult


_READ_ONLY = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


@dataclass(frozen=True)
class QuerySnapshot:
    columns: list[str]
    rows: list[dict[str, str | None]]

    @property
    def row_count(self) -> int:
        return len(self.rows)


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _validate_read_only_query(query: str) -> None:
    stripped = query.strip()
    if not _READ_ONLY.match(stripped):
        raise ValueError("Only read-only SELECT/CTE queries are allowed.")
    statements = [part for part in stripped.split(";") if part.strip()]
    if len(statements) != 1:
        raise ValueError("Exactly one read-only SQL statement is allowed.")


class SQLiteDatabaseAdapter:
    """Deterministic, read-only query adapter used by the V3 reference pipeline."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).resolve()

    def initialize_from_script(self, script_path: str | Path) -> None:
        """Create a synthetic/local database fixture outside the Agent/MCP boundary."""
        script = Path(script_path).read_text(encoding="utf-8")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
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
        return QuerySnapshot(columns=columns, rows=rows)

    def profile(self, sql: str) -> dict[str, Any]:
        snapshot = self.query(sql)
        null_counts = {
            column: sum(1 for row in snapshot.rows if row.get(column) is None)
            for column in snapshot.columns
        }
        return {
            "engine": "sqlite",
            "columns": snapshot.columns,
            "row_count": snapshot.row_count,
            "null_counts": null_counts,
        }


def compare_query_snapshots(
    baseline: QuerySnapshot,
    candidate: QuerySnapshot,
    *,
    key_field: str,
    critical_fields: list[str] | None = None,
) -> DifferentialResult:
    critical_fields = critical_fields or []
    schema_differences: list[Difference] = []

    baseline_columns = set(baseline.columns)
    candidate_columns = set(candidate.columns)

    for column in sorted(baseline_columns - candidate_columns):
        schema_differences.append(
            Difference(
                row_key="<schema>",
                field=column,
                expected="present",
                observed="missing",
                severity="HIGH",
                message=f"Required baseline column '{column}' is missing from candidate query.",
            )
        )

    for column in sorted(candidate_columns - baseline_columns):
        schema_differences.append(
            Difference(
                row_key="<schema>",
                field=column,
                expected="absent",
                observed="present",
                severity="MEDIUM",
                message=f"Candidate query exposes extra column '{column}'.",
            )
        )

    if key_field not in baseline_columns or key_field not in candidate_columns:
        schema_differences.append(
            Difference(
                row_key="<schema>",
                field=key_field,
                expected="key present in both queries",
                observed="missing from one or both queries",
                severity="CRITICAL",
                message="The differential key field must exist in both query results.",
            )
        )
        return DifferentialResult(
            status="FAIL",
            compared_rows=0,
            difference_count=len(schema_differences),
            differences=schema_differences,
        )

    comparable_fields = [
        field for field in critical_fields
        if field in baseline_columns and field in candidate_columns
    ]
    row_result = compare_datasets(
        baseline.rows,
        candidate.rows,
        key_field=key_field,
        critical_fields=comparable_fields,
    )

    differences = [*schema_differences, *row_result.differences]
    return DifferentialResult(
        status="FAIL" if differences else "PASS",
        compared_rows=row_result.compared_rows,
        difference_count=len(differences),
        differences=differences,
    )


def compare_database_queries(
    *,
    database_path: str | Path,
    baseline_query: str,
    candidate_query: str,
    key_field: str,
    critical_fields: list[str] | None = None,
) -> DifferentialResult:
    adapter = SQLiteDatabaseAdapter(database_path)
    baseline = adapter.query(baseline_query)
    candidate = adapter.query(candidate_query)
    return compare_query_snapshots(
        baseline,
        candidate,
        key_field=key_field,
        critical_fields=critical_fields,
    )

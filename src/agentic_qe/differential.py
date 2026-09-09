from __future__ import annotations

from collections.abc import Iterable

from .models import Difference, DifferentialResult


def _display_key(row: dict[str, str | None], key_fields: list[str]) -> str:
    return " | ".join(f"{field}={row.get(field, '<MISSING>')}" for field in key_fields)


def _index_rows(
    rows: list[dict[str, str | None]],
    *,
    key_fields: list[str],
    side: str,
) -> tuple[dict[str, dict[str, str | None]], list[Difference]]:
    indexed: dict[str, dict[str, str | None]] = {}
    findings: list[Difference] = []

    for position, row in enumerate(rows, start=1):
        missing = [field for field in key_fields if field not in row]
        if missing:
            findings.append(
                Difference(
                    row_key=f"{side}:row#{position}",
                    field="__key__",
                    expected=", ".join(key_fields),
                    observed=", ".join(sorted(row)),
                    severity="CRITICAL",
                    message=f"{side.capitalize()} row is missing key field(s): {', '.join(missing)}.",
                )
            )
            continue

        key = _display_key(row, key_fields)
        if key in indexed:
            findings.append(
                Difference(
                    row_key=key,
                    field="__key__",
                    expected="unique key",
                    observed="duplicate key",
                    severity="CRITICAL",
                    message=f"{side.capitalize()} contains duplicate business-key values.",
                )
            )
            continue
        indexed[key] = row

    return indexed, findings


def compare_tabular(
    expected_rows: list[dict[str, str | None]],
    candidate_rows: list[dict[str, str | None]],
    *,
    key_fields: list[str],
    critical_fields: Iterable[str],
) -> DifferentialResult:
    """Deterministically reconcile two tabular result sets.

    Supports composite business keys and explicitly reports missing keys and duplicate
    keys rather than silently overwriting them in a dictionary index.
    """
    if not key_fields:
        raise ValueError("At least one key field is required for differential comparison.")

    critical = set(critical_fields)
    expected, expected_key_findings = _index_rows(
        expected_rows,
        key_fields=key_fields,
        side="expected",
    )
    candidate, candidate_key_findings = _index_rows(
        candidate_rows,
        key_fields=key_fields,
        side="candidate",
    )

    differences: list[Difference] = [*expected_key_findings, *candidate_key_findings]
    all_keys = sorted(set(expected) | set(candidate))

    for key in all_keys:
        expected_row = expected.get(key)
        candidate_row = candidate.get(key)

        if expected_row is None:
            differences.append(
                Difference(
                    row_key=key,
                    field="__row__",
                    expected=None,
                    observed="unexpected row",
                    severity="HIGH",
                    message="Candidate contains a row not present in expected output.",
                )
            )
            continue

        if candidate_row is None:
            differences.append(
                Difference(
                    row_key=key,
                    field="__row__",
                    expected="expected row",
                    observed=None,
                    severity="CRITICAL",
                    message="Candidate is missing an expected row.",
                )
            )
            continue

        fields = sorted(set(expected_row) | set(candidate_row))
        for field in fields:
            if field in key_fields:
                continue
            expected_value = expected_row.get(field)
            candidate_value = candidate_row.get(field)
            if expected_value != candidate_value:
                severity = "CRITICAL" if field in critical else "MEDIUM"
                differences.append(
                    Difference(
                        row_key=key,
                        field=field,
                        expected=expected_value,
                        observed=candidate_value,
                        severity=severity,
                        message="Candidate value differs from expected output.",
                    )
                )

    return DifferentialResult(
        status="PASS" if not differences else "FAIL",
        compared_rows=len(all_keys),
        difference_count=len(differences),
        differences=differences,
    )


def compare_datasets(
    expected_rows: list[dict[str, str | None]],
    candidate_rows: list[dict[str, str | None]],
    *,
    key_field: str,
    critical_fields: list[str],
) -> DifferentialResult:
    """Backwards-compatible single-key wrapper for the existing CSV pipeline."""
    return compare_tabular(
        expected_rows,
        candidate_rows,
        key_fields=[key_field],
        critical_fields=critical_fields,
    )

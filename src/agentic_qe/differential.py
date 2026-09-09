from __future__ import annotations

from .models import Difference, DifferentialResult


def compare_datasets(
    expected_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    *,
    key_field: str,
    critical_fields: list[str],
) -> DifferentialResult:
    expected = {row[key_field]: row for row in expected_rows}
    candidate = {row[key_field]: row for row in candidate_rows}

    differences: list[Difference] = []
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
            if field == key_field:
                continue
            expected_value = expected_row.get(field)
            candidate_value = candidate_row.get(field)
            if expected_value != candidate_value:
                severity = "CRITICAL" if field in critical_fields else "MEDIUM"
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

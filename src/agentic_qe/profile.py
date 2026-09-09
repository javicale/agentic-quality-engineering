from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any


_DECIMAL_RE = re.compile(r"^-?\d+\.(\d+)$")


def profile_csv(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    with target.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []

    profiles: dict[str, Any] = {}
    for field in fields:
        values = [str(row.get(field, "")) for row in rows]
        scales = Counter()
        lengths = Counter()
        blank_count = 0
        for value in values:
            if value == "":
                blank_count += 1
            lengths[len(value)] += 1
            match = _DECIMAL_RE.match(value)
            if match:
                scales[len(match.group(1))] += 1

        profiles[field] = {
            "blank_count": blank_count,
            "length_distribution": dict(sorted(lengths.items())),
            "decimal_scale_distribution": dict(sorted(scales.items())),
        }

    return {
        "file": target.name,
        "row_count": len(rows),
        "columns": fields,
        "profiles": profiles,
    }

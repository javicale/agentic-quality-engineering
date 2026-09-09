from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_scenario(path: str | Path) -> dict[str, Any]:
    scenario_path = Path(path)
    with scenario_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    required = {
        "id",
        "title",
        "risk",
        "key_field",
        "validation_plan",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"Scenario missing required fields: {', '.join(missing)}")

    has_file_dataset = "expected_dataset" in data
    has_sql_config = "sql" in data
    if not has_file_dataset and not has_sql_config:
        raise ValueError("Scenario must define either expected_dataset or sql configuration.")

    return data


def load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

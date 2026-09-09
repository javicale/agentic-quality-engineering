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
        "expected_dataset",
        "validation_plan",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"Scenario missing required fields: {', '.join(missing)}")

    return data


def load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

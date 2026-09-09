from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class EventRecorder:
    def __init__(self) -> None:
        self.run_id = str(uuid4())
        self.events: list[dict[str, Any]] = []

    def record(self, event: str, **attributes: Any) -> None:
        self.events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "run_id": self.run_id,
                "event": event,
                "attributes": attributes,
            }
        )

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for item in self.events:
                handle.write(json.dumps(item, sort_keys=True) + "\n")

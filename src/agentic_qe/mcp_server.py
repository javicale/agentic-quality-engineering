from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .profile import profile_csv


def _workspace_root() -> Path:
    return Path(os.getenv("AGENTIC_QE_WORKSPACE", os.getcwd())).resolve()


def _safe_path(raw_path: str, *, suffixes: set[str]) -> Path:
    root = _workspace_root()
    candidate = (root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path is outside the configured Agentic QE workspace.") from exc
    if candidate.suffix.lower() not in suffixes:
        raise ValueError(f"Unsupported file type: {candidate.suffix}")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def scenario_context(scenario_path: str) -> dict[str, Any]:
    path = _safe_path(scenario_path, suffixes={".json"})
    scenario = json.loads(path.read_text(encoding="utf-8"))
    return {
        "id": scenario["id"],
        "title": scenario["title"],
        "risk": scenario["risk"],
        "key_field": scenario["key_field"],
        "critical_fields": scenario.get("critical_fields", []),
        "source_dataset": scenario.get("source_dataset"),
        "expected_dataset": scenario.get("expected_dataset"),
    }


def dataset_profile(dataset_path: str) -> dict[str, Any]:
    path = _safe_path(dataset_path, suffixes={".csv"})
    return profile_csv(path)


def quality_capabilities() -> dict[str, Any]:
    return {
        "capabilities": [
            "csv-differential-testing",
            "validation-plan-evals",
            "execution-gating",
            "structured-evidence",
            "event-observability",
            "risk-based-release-decision",
        ],
        "constraints": [
            "read-only-context-tools",
            "workspace-path-boundary",
            "human-release-approval-required",
        ],
    }


def build_mcp_server():
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError(
            "MCP support is optional. Install with: pip install -e '.[agent]'"
        ) from exc

    server = MCPServer(
        "Agentic QE Context",
        instructions=(
            "Provide read-only, sanitized quality context. Never expose files outside the configured workspace."
        ),
    )

    server.tool()(scenario_context)
    server.tool()(dataset_profile)
    server.tool()(quality_capabilities)
    return server


try:
    mcp = build_mcp_server()
except RuntimeError:
    mcp = None


def main() -> None:
    server = mcp or build_mcp_server()
    server.run()


if __name__ == "__main__":
    main()

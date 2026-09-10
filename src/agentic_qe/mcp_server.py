from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .profile import profile_csv
from .sql_adapter import SQLAlchemyDatabaseAdapter, SQLiteDatabaseAdapter
from .traceability import capability_catalog


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
    keys = scenario.get("key_fields") or ([scenario["key_field"]] if scenario.get("key_field") else [])
    return {
        "id": scenario["id"],
        "title": scenario["title"],
        "risk": scenario["risk"],
        "key_fields": keys,
        "critical_fields": scenario.get("critical_fields", []),
        "source_dataset": scenario.get("source_dataset"),
        "expected_dataset": scenario.get("expected_dataset"),
        "sql_engine": scenario.get("sql", {}).get("engine"),
    }


def dataset_profile(dataset_path: str) -> dict[str, Any]:
    path = _safe_path(dataset_path, suffixes={".csv"})
    return profile_csv(path)


def _scenario_database_profile(*, scenario_path: str, side: str, candidate_query_name: str) -> dict[str, Any]:
    path = _safe_path(scenario_path, suffixes={".json"})
    scenario = json.loads(path.read_text(encoding="utf-8"))
    sql_config = scenario.get("sql")
    if not sql_config:
        raise ValueError("Scenario does not define SQL database configuration.")
    keys = scenario.get("key_fields") or ([scenario["key_field"]] if scenario.get("key_field") else [])
    engine = str(sql_config.get("engine", "sqlite")).lower()
    if side not in {"baseline", "candidate"}:
        raise ValueError("side must be baseline or candidate.")
    query = sql_config["baseline_query"] if side == "baseline" else sql_config["candidate_queries"][candidate_query_name]

    if engine == "sqlite":
        setup_script = (path.parent / sql_config["setup_script"]).resolve()
        setup_script.relative_to(path.parent.resolve())
        with tempfile.TemporaryDirectory(prefix="agentic-qe-mcp-") as temp_dir:
            adapter = SQLiteDatabaseAdapter(Path(temp_dir) / "profile.db")
            adapter.initialize_from_script(setup_script)
            return adapter.profile(query, key_fields=keys)

    if engine == "sqlalchemy-env":
        env_name = str(sql_config["baseline_url_env"] if side == "baseline" else sql_config["candidate_url_env"])
        return SQLAlchemyDatabaseAdapter(env_name).profile(query, key_fields=keys)

    raise ValueError(f"Unsupported SQL engine: {engine}")


def database_profile(database_path: str = "", query: str = "", scenario_path: str = "", side: str = "baseline", candidate_query_name: str = "good", key_fields: list[str] | None = None) -> dict[str, Any]:
    """Return database metadata only; never connection URLs, credentials or raw rows."""
    if scenario_path:
        return _scenario_database_profile(scenario_path=scenario_path, side=side, candidate_query_name=candidate_query_name)
    if not database_path or not query:
        raise ValueError("Provide scenario_path or both database_path and query.")
    path = _safe_path(database_path, suffixes={".db", ".sqlite", ".sqlite3"})
    return SQLiteDatabaseAdapter(path).profile(query, key_fields=key_fields or [])


def quality_capabilities() -> dict[str, Any]:
    execution_capabilities = capability_catalog()
    return {
        "execution_capabilities": execution_capabilities,
        "capabilities": [item["id"] for item in execution_capabilities],
        "constraints": [
            "read-only-context-tools",
            "workspace-path-boundary",
            "database-rows-not-exposed-to-agent",
            "database-credentials-never-returned-to-agent",
            "scenario-capability-declaration-required",
            "high-critical-uncovered-scenarios-block-release",
            "human-release-approval-required",
        ],
    }


def build_mcp_server():
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError("MCP support is optional. Install with: pip install -e '.[agent]'") from exc

    server = MCPServer(
        "Agentic QE Context",
        instructions=(
            "Provide read-only, sanitized quality context. Never expose files outside the configured workspace, "
            "raw database rows, connection URLs or credentials. Execution capabilities are authoritative IDs for "
            "plan-to-execution traceability."
        ),
    )
    server.tool()(scenario_context)
    server.tool()(dataset_profile)
    server.tool()(database_profile)
    server.tool()(quality_capabilities)
    return server


try:
    mcp = build_mcp_server()
except RuntimeError:
    mcp = None


def main() -> None:
    (mcp or build_mcp_server()).run()


if __name__ == "__main__":
    main()

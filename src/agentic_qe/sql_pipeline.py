from __future__ import annotations

from pathlib import Path
from typing import Any

from .data import load_scenario
from .evals import evaluate_validation_plan
from .evidence import build_evidence, write_json
from .gating import decide_execution_gate
from .observability import EventRecorder
from .planner import get_plan_generator
from .release import decide_release
from .sql_adapter import (
    SQLAlchemyDatabaseAdapter,
    SQLiteDatabaseAdapter,
    compare_query_snapshots,
    profile_snapshot,
)


def _key_fields(scenario: dict[str, Any]) -> list[str]:
    if scenario.get("key_fields"):
        return [str(item) for item in scenario["key_fields"]]
    if scenario.get("key_field"):
        return [str(scenario["key_field"])]
    raise ValueError("SQL scenario requires key_field or key_fields.")


def _build_adapters(sql_config: dict[str, Any], *, base_dir: Path):
    engine = str(sql_config.get("engine", "sqlite")).lower()
    if engine == "sqlite":
        database_path = (base_dir / sql_config["database"]).resolve()
        setup_script = (base_dir / sql_config["setup_script"]).resolve()
        adapter = SQLiteDatabaseAdapter(database_path)
        adapter.initialize_from_script(setup_script)
        return engine, adapter, adapter, database_path.name
    if engine == "sqlalchemy-env":
        baseline = SQLAlchemyDatabaseAdapter(str(sql_config["baseline_url_env"]))
        candidate = SQLAlchemyDatabaseAdapter(str(sql_config["candidate_url_env"]))
        return engine, baseline, candidate, "environment-backed databases"
    raise ValueError(f"Unsupported SQL engine: {engine}")


def _build_execution_scope(
    *,
    differential,
    profiles: dict[str, Any] | None,
    critical_fields: list[str],
    planned_scenario_count: int,
    release_decision: str,
) -> dict[str, Any]:
    """Describe what deterministic execution actually proved in this run.

    The agent may propose broader scenarios than one adapter invocation executes. This
    artifact prevents a GO signal from being misread as one-to-one completion of every
    scenario in the generated plan.
    """
    if differential is None:
        checks = [
            {"id": "projected-schema-differential", "status": "NOT_RUN"},
            {"id": "business-key-reconciliation", "status": "NOT_RUN"},
            {"id": "duplicate-key-detection", "status": "NOT_RUN"},
            {"id": "critical-field-differential", "status": "NOT_RUN"},
            {"id": "database-metadata-profile", "status": "NOT_RUN"},
        ]
    else:
        findings = differential.differences
        schema_failed = any(item.row_key == "__schema__" for item in findings)
        key_failed = any(item.field in {"__key__", "__row__"} for item in findings)
        duplicate_failed = any(
            item.field == "__key__" and item.observed == "duplicate key"
            for item in findings
        )
        critical_failed = any(item.field in set(critical_fields) for item in findings)
        profile_available = profiles is not None
        checks = [
            {"id": "projected-schema-differential", "status": "FAIL" if schema_failed else "PASS"},
            {"id": "business-key-reconciliation", "status": "FAIL" if key_failed else "PASS"},
            {"id": "duplicate-key-detection", "status": "FAIL" if duplicate_failed else "PASS"},
            {"id": "critical-field-differential", "status": "FAIL" if critical_failed else "PASS"},
            {"id": "database-metadata-profile", "status": "PASS" if profile_available else "NOT_RUN"},
        ]

    return {
        "planned_scenario_count": planned_scenario_count,
        "scenario_level_traceability": "NOT_IMPLEMENTED",
        "release_decision_basis": (
            "Release policy uses the deterministic checks executed by this adapter, the plan eval/execution gate, "
            "and scenario risk. It does not claim that every natural-language scenario in the agent plan was executed."
        ),
        "release_decision": release_decision,
        "deterministic_checks": checks,
    }


def execute_sql_pipeline(
    *,
    scenario_path: str,
    output_dir: str,
    candidate_query_name: str = "good",
    plan_source: str = "embedded",
    plan_path: str | None = None,
    model: str | None = None,
    allow_warn_plan: bool = False,
) -> dict[str, Any]:
    scenario_file = Path(scenario_path).resolve()
    scenario = load_scenario(scenario_file)
    base_dir = scenario_file.parent
    sql_config = scenario["sql"]
    keys = _key_fields(scenario)

    candidate_queries = sql_config["candidate_queries"]
    if candidate_query_name not in candidate_queries:
        raise ValueError(
            f"Unknown candidate query '{candidate_query_name}'. "
            f"Choose one of: {', '.join(sorted(candidate_queries))}"
        )

    recorder = EventRecorder()
    recorder.record(
        "sql_pipeline.started",
        scenario_id=scenario["id"],
        risk=scenario["risk"],
        engine=sql_config.get("engine", "sqlite"),
        candidate_query=candidate_query_name,
        plan_source=plan_source,
        key_fields=keys,
    )

    generator = get_plan_generator(
        plan_source,
        plan_path=plan_path,
        model=model,
        candidate_query_name=candidate_query_name,
    )
    planned = generator.generate(scenario=scenario, scenario_path=scenario_file)
    eval_result = evaluate_validation_plan(planned.plan)
    execution_gate = decide_execution_gate(
        plan=planned.plan,
        eval_result=eval_result,
        allow_warn_plan=allow_warn_plan,
    )
    recorder.record(
        "execution_gate.completed",
        allowed=execution_gate.allowed,
        status=execution_gate.status,
        reasons=execution_gate.reasons,
    )

    differential = None
    profiles: dict[str, Any] | None = None
    engine_name = str(sql_config.get("engine", "sqlite"))
    database_label = "not-executed"
    if execution_gate.allowed:
        engine_name, baseline_adapter, candidate_adapter, database_label = _build_adapters(
            sql_config,
            base_dir=base_dir,
        )
        recorder.record(
            "database.adapters.ready",
            engine=engine_name,
            credential_material_logged=False,
        )

        baseline_query = sql_config["baseline_query"]
        candidate_query = candidate_queries[candidate_query_name]
        baseline = baseline_adapter.query(baseline_query)
        candidate = candidate_adapter.query(candidate_query)
        profiles = {
            "baseline": profile_snapshot(baseline, key_fields=keys),
            "candidate": profile_snapshot(candidate, key_fields=keys),
        }
        recorder.record(
            "database.queries.loaded",
            baseline_rows=baseline.row_count,
            candidate_rows=candidate.row_count,
            baseline_columns=baseline.columns,
            candidate_columns=candidate.columns,
            candidate_duplicate_keys=profiles["candidate"]["duplicate_key_count"],
        )

        differential = compare_query_snapshots(
            baseline,
            candidate,
            key_fields=keys,
            critical_fields=scenario.get("critical_fields", []),
        )
        recorder.record(
            "sql_differential.completed",
            status=differential.status,
            difference_count=differential.difference_count,
        )
    else:
        recorder.record("execution.skipped", reason="validation_plan_gate_blocked")

    signal = decide_release(
        scenario_risk=scenario["risk"],
        eval_result=eval_result,
        differential_result=differential,
        execution_gate=execution_gate,
    )
    recorder.record(
        "release_decision.completed",
        decision=signal.decision,
        residual_risk=signal.residual_risk,
    )

    execution_scope = _build_execution_scope(
        differential=differential,
        profiles=profiles,
        critical_fields=scenario.get("critical_fields", []),
        planned_scenario_count=len(planned.plan.scenarios),
        release_decision=signal.decision,
    )
    recorder.record(
        "execution_scope.recorded",
        scenario_level_traceability=execution_scope["scenario_level_traceability"],
        deterministic_check_count=len(execution_scope["deterministic_checks"]),
    )

    evidence = build_evidence(
        scenario=scenario,
        candidate_path=f"database::{engine_name}::{candidate_query_name}",
        planned_validation=planned,
        eval_result=eval_result,
        execution_gate=execution_gate,
        differential_result=differential,
        run_id=recorder.run_id,
    )
    evidence["schema_version"] = "3.1"
    evidence["database"] = {
        "engine": engine_name,
        "database": database_label,
        "candidate_query": candidate_query_name,
        "key_fields": keys,
        "profiles": profiles,
        "raw_rows_exposed_to_agent": False,
        "connection_urls_recorded": False,
    }
    evidence["execution_scope"] = execution_scope

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(planned.model_dump(mode="json"), output / "validation-plan.json")
    write_json(eval_result.to_dict(), output / "eval-result.json")
    write_json(execution_gate.model_dump(mode="json"), output / "execution-gate.json")
    write_json(execution_scope, output / "execution-scope.json")
    write_json(evidence, output / "evidence.json")
    write_json(signal.to_dict(), output / "release-signal.json")
    if profiles is not None:
        write_json(profiles, output / "database-profile.json")
    if differential is not None:
        write_json(differential.to_dict(), output / "database-differential.json")
    recorder.write_jsonl(output / "events.jsonl")

    return {
        "run_id": recorder.run_id,
        "eval": eval_result.to_dict(),
        "execution_gate": execution_gate.model_dump(mode="json"),
        "database_profiles": profiles,
        "execution_scope": execution_scope,
        "differential": differential.to_dict() if differential else None,
        "release": signal.to_dict(),
    }

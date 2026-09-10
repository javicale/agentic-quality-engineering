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
from .sql_adapter import SQLAlchemyDatabaseAdapter, SQLiteDatabaseAdapter, compare_query_snapshots, profile_snapshot
from .traceability import apply_traceability_policy, build_plan_traceability, build_sql_capability_results


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


def _legacy_execution_scope(*, traceability: dict[str, Any], capability_results: dict[str, dict[str, Any]], release_decision: str) -> dict[str, Any]:
    return {
        "planned_scenario_count": traceability["summary"]["planned_scenarios"],
        "scenario_level_traceability": "IMPLEMENTED",
        "release_decision_basis": "Release policy uses deterministic adapter results plus scenario-level plan-to-execution traceability. HIGH/CRITICAL uncovered plan scenarios block release.",
        "release_decision": release_decision,
        "deterministic_checks": list(capability_results.values()),
    }


def execute_sql_pipeline(*, scenario_path: str, output_dir: str, candidate_query_name: str = "good", plan_source: str = "embedded", plan_path: str | None = None, model: str | None = None, allow_warn_plan: bool = False) -> dict[str, Any]:
    scenario_file = Path(scenario_path).resolve()
    scenario = load_scenario(scenario_file)
    base_dir = scenario_file.parent
    sql_config = scenario["sql"]
    keys = _key_fields(scenario)
    candidate_queries = sql_config["candidate_queries"]
    if candidate_query_name not in candidate_queries:
        raise ValueError(f"Unknown candidate query '{candidate_query_name}'. Choose one of: {', '.join(sorted(candidate_queries))}")

    recorder = EventRecorder()
    recorder.record("sql_pipeline.started", scenario_id=scenario["id"], risk=scenario["risk"], engine=sql_config.get("engine", "sqlite"), candidate_query=candidate_query_name, plan_source=plan_source, key_fields=keys)
    generator = get_plan_generator(plan_source, plan_path=plan_path, model=model, candidate_query_name=candidate_query_name)
    planned = generator.generate(scenario=scenario, scenario_path=scenario_file)
    eval_result = evaluate_validation_plan(planned.plan)
    execution_gate = decide_execution_gate(plan=planned.plan, eval_result=eval_result, allow_warn_plan=allow_warn_plan)
    recorder.record("execution_gate.completed", allowed=execution_gate.allowed, status=execution_gate.status, reasons=execution_gate.reasons)

    differential = None
    profiles: dict[str, Any] | None = None
    engine_name = str(sql_config.get("engine", "sqlite"))
    database_label = "not-executed"
    if execution_gate.allowed:
        engine_name, baseline_adapter, candidate_adapter, database_label = _build_adapters(sql_config, base_dir=base_dir)
        recorder.record("database.adapters.ready", engine=engine_name, credential_material_logged=False)
        baseline_query = sql_config["baseline_query"]
        candidate_query = candidate_queries[candidate_query_name]
        baseline = baseline_adapter.query(baseline_query)
        candidate = candidate_adapter.query(candidate_query)
        profiles = {"baseline": profile_snapshot(baseline, key_fields=keys), "candidate": profile_snapshot(candidate, key_fields=keys)}
        recorder.record("database.queries.loaded", baseline_rows=baseline.row_count, candidate_rows=candidate.row_count, baseline_columns=baseline.columns, candidate_columns=candidate.columns, candidate_duplicate_keys=profiles["candidate"]["duplicate_key_count"])
        differential = compare_query_snapshots(baseline, candidate, key_fields=keys, critical_fields=scenario.get("critical_fields", []))
        recorder.record("sql_differential.completed", status=differential.status, difference_count=differential.difference_count)
    else:
        recorder.record("execution.skipped", reason="validation_plan_gate_blocked")

    capability_results = build_sql_capability_results(differential=differential, profiles=profiles, critical_fields=scenario.get("critical_fields", []), eval_passed=eval_result.status == "PASS", gate_allowed=execution_gate.allowed, human_release_approval=planned.plan.human_release_approval)
    traceability = build_plan_traceability(plan=planned.plan, capability_results=capability_results)
    recorder.record("plan_traceability.completed", coverage_gate=traceability["coverage_gate"]["status"], planned_scenarios=traceability["summary"]["planned_scenarios"], passed=traceability["summary"]["passed"], failed=traceability["summary"]["failed"], not_executed=traceability["summary"]["not_executed"])

    signal = decide_release(scenario_risk=scenario["risk"], eval_result=eval_result, differential_result=differential, execution_gate=execution_gate)
    signal = apply_traceability_policy(signal, traceability)
    recorder.record("release_decision.completed", decision=signal.decision, residual_risk=signal.residual_risk, traceability_gate=traceability["coverage_gate"]["status"])
    execution_scope = _legacy_execution_scope(traceability=traceability, capability_results=capability_results, release_decision=signal.decision)

    evidence = build_evidence(scenario=scenario, candidate_path=f"database::{engine_name}::{candidate_query_name}", planned_validation=planned, eval_result=eval_result, execution_gate=execution_gate, differential_result=differential, run_id=recorder.run_id)
    evidence["schema_version"] = "4.0"
    evidence["database"] = {"engine": engine_name, "database": database_label, "candidate_query": candidate_query_name, "key_fields": keys, "profiles": profiles, "raw_rows_exposed_to_agent": False, "connection_urls_recorded": False}
    evidence["execution_scope"] = execution_scope
    evidence["plan_traceability"] = traceability

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(planned.model_dump(mode="json"), output / "validation-plan.json")
    write_json(eval_result.to_dict(), output / "eval-result.json")
    write_json(execution_gate.model_dump(mode="json"), output / "execution-gate.json")
    write_json(traceability, output / "plan-traceability.json")
    write_json(execution_scope, output / "execution-scope.json")
    write_json(evidence, output / "evidence.json")
    write_json(signal.to_dict(), output / "release-signal.json")
    if profiles is not None:
        write_json(profiles, output / "database-profile.json")
    if differential is not None:
        write_json(differential.to_dict(), output / "database-differential.json")
    recorder.write_jsonl(output / "events.jsonl")

    return {"run_id": recorder.run_id, "eval": eval_result.to_dict(), "execution_gate": execution_gate.model_dump(mode="json"), "database_profiles": profiles, "execution_scope": execution_scope, "traceability": traceability, "differential": differential.to_dict() if differential else None, "release": signal.to_dict()}

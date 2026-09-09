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
from .sql_adapter import SQLiteDatabaseAdapter, compare_query_snapshots


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

    database_path = (base_dir / sql_config["database"]).resolve()
    setup_script = (base_dir / sql_config["setup_script"]).resolve()
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
        engine="sqlite",
        candidate_query=candidate_query_name,
        plan_source=plan_source,
    )

    generator = get_plan_generator(plan_source, plan_path=plan_path, model=model)
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
    if execution_gate.allowed:
        adapter = SQLiteDatabaseAdapter(database_path)
        adapter.initialize_from_script(setup_script)
        recorder.record(
            "database.fixture_initialized",
            engine="sqlite",
            database=database_path.name,
        )

        baseline_query = sql_config["baseline_query"]
        candidate_query = candidate_queries[candidate_query_name]
        baseline = adapter.query(baseline_query)
        candidate = adapter.query(candidate_query)
        profiles = {
            "baseline": adapter.profile(baseline_query),
            "candidate": adapter.profile(candidate_query),
        }
        recorder.record(
            "database.queries_loaded",
            baseline_rows=baseline.row_count,
            candidate_rows=candidate.row_count,
            baseline_columns=baseline.columns,
            candidate_columns=candidate.columns,
        )

        differential = compare_query_snapshots(
            baseline,
            candidate,
            key_field=scenario["key_field"],
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

    evidence = build_evidence(
        scenario=scenario,
        candidate_path=f"sqlite://{database_path.name}::{candidate_query_name}",
        planned_validation=planned,
        eval_result=eval_result,
        execution_gate=execution_gate,
        differential_result=differential,
        run_id=recorder.run_id,
    )
    evidence["database"] = {
        "engine": "sqlite",
        "database": database_path.name,
        "candidate_query": candidate_query_name,
        "profiles": profiles,
        "raw_rows_exposed_to_agent": False,
    }

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(planned.model_dump(mode="json"), output / "validation-plan.json")
    write_json(eval_result.to_dict(), output / "eval-result.json")
    write_json(execution_gate.model_dump(mode="json"), output / "execution-gate.json")
    write_json(evidence, output / "evidence.json")
    write_json(signal.to_dict(), output / "release-signal.json")
    if profiles is not None:
        write_json(profiles, output / "database-profile.json")
    recorder.write_jsonl(output / "events.jsonl")

    return {
        "run_id": recorder.run_id,
        "eval": eval_result.to_dict(),
        "execution_gate": execution_gate.model_dump(mode="json"),
        "database_profiles": profiles,
        "differential": differential.to_dict() if differential else None,
        "release": signal.to_dict(),
    }

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import load_csv, load_scenario
from .differential import compare_datasets
from .evals import evaluate_validation_plan
from .evidence import build_evidence, write_json
from .gating import decide_execution_gate
from .observability import EventRecorder
from .planner import get_plan_generator
from .release import decide_release
from .traceability import apply_traceability_policy, build_csv_capability_results, build_plan_traceability


def generate_validation_plan(*, scenario_path: str, provider: str, plan_path: str | None = None, model: str | None = None, candidate_query_name: str | None = None) -> dict:
    scenario_file = Path(scenario_path).resolve()
    scenario = load_scenario(scenario_file)
    generator = get_plan_generator(provider, plan_path=plan_path, model=model, candidate_query_name=candidate_query_name)
    planned = generator.generate(scenario=scenario, scenario_path=scenario_file)
    eval_result = evaluate_validation_plan(planned.plan)
    gate = decide_execution_gate(plan=planned.plan, eval_result=eval_result)
    return {"plan": planned.plan.model_dump(mode="json"), "metadata": planned.metadata.model_dump(mode="json"), "eval": eval_result.to_dict(), "execution_gate": gate.model_dump(mode="json")}


def execute_pipeline(*, scenario_path: str, candidate_path: str, output_dir: str, plan_source: str = "embedded", plan_path: str | None = None, model: str | None = None, allow_warn_plan: bool = False) -> dict:
    scenario_file = Path(scenario_path).resolve()
    scenario = load_scenario(scenario_file)
    base_dir = scenario_file.parent
    expected_path = (base_dir / scenario["expected_dataset"]).resolve()
    candidate_file = Path(candidate_path).resolve()
    output = Path(output_dir)

    recorder = EventRecorder()
    recorder.record("pipeline.started", scenario_id=scenario["id"], candidate=str(candidate_file), risk=scenario["risk"], plan_source=plan_source)
    generator = get_plan_generator(plan_source, plan_path=plan_path, model=model)
    recorder.record("planner.started", provider=plan_source)
    planned = generator.generate(scenario=scenario, scenario_path=scenario_file)
    recorder.record("planner.completed", provider=planned.metadata.provider, model=planned.metadata.model, live_model_call=planned.metadata.live_model_call, generated_by=planned.plan.generated_by)

    eval_result = evaluate_validation_plan(planned.plan)
    recorder.record("agent_eval.completed", status=eval_result.status, score=eval_result.score, threshold=eval_result.threshold)
    execution_gate = decide_execution_gate(plan=planned.plan, eval_result=eval_result, allow_warn_plan=allow_warn_plan)
    recorder.record("execution_gate.completed", allowed=execution_gate.allowed, status=execution_gate.status, reasons=execution_gate.reasons)

    differential = None
    if execution_gate.allowed:
        expected_rows = load_csv(expected_path)
        candidate_rows = load_csv(candidate_file)
        recorder.record("test_data.loaded", expected_rows=len(expected_rows), candidate_rows=len(candidate_rows))
        differential = compare_datasets(expected_rows, candidate_rows, key_field=scenario["key_field"], critical_fields=scenario.get("critical_fields", []))
        recorder.record("differential.completed", status=differential.status, difference_count=differential.difference_count)
    else:
        recorder.record("execution.skipped", reason="validation_plan_gate_blocked")

    capability_results = build_csv_capability_results(differential=differential, critical_fields=scenario.get("critical_fields", []), eval_passed=eval_result.status == "PASS", gate_allowed=execution_gate.allowed, human_release_approval=planned.plan.human_release_approval)
    traceability = build_plan_traceability(plan=planned.plan, capability_results=capability_results)
    recorder.record("plan_traceability.completed", coverage_gate=traceability["coverage_gate"]["status"], planned_scenarios=traceability["summary"]["planned_scenarios"], passed=traceability["summary"]["passed"], not_executed=traceability["summary"]["not_executed"])

    signal = decide_release(scenario_risk=scenario["risk"], eval_result=eval_result, differential_result=differential, execution_gate=execution_gate)
    signal = apply_traceability_policy(signal, traceability)
    recorder.record("release_decision.completed", decision=signal.decision, residual_risk=signal.residual_risk, traceability_gate=traceability["coverage_gate"]["status"])
    recorder.record("pipeline.completed", decision=signal.decision)

    evidence = build_evidence(scenario=scenario, candidate_path=str(candidate_file), planned_validation=planned, eval_result=eval_result, execution_gate=execution_gate, differential_result=differential, run_id=recorder.run_id)
    evidence["schema_version"] = "4.0"
    evidence["plan_traceability"] = traceability

    output.mkdir(parents=True, exist_ok=True)
    write_json(planned.model_dump(mode="json"), output / "validation-plan.json")
    write_json(eval_result.to_dict(), output / "eval-result.json")
    write_json(execution_gate.model_dump(mode="json"), output / "execution-gate.json")
    write_json(traceability, output / "plan-traceability.json")
    write_json(evidence, output / "evidence.json")
    write_json(signal.to_dict(), output / "release-signal.json")
    recorder.write_jsonl(output / "events.jsonl")

    return {"run_id": recorder.run_id, "plan": planned.plan.model_dump(mode="json"), "planner": planned.metadata.model_dump(mode="json"), "eval": eval_result.to_dict(), "execution_gate": execution_gate.model_dump(mode="json"), "traceability": traceability, "differential": differential.to_dict() if differential else None, "release": signal.to_dict()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentic-qe", description="Run the Agentic Quality Engineering reference pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan", help="Generate and evaluate a validation plan.")
    plan_parser.add_argument("--scenario", required=True)
    plan_parser.add_argument("--provider", choices=["embedded", "file", "openai"], default="embedded")
    plan_parser.add_argument("--plan")
    plan_parser.add_argument("--model")
    plan_parser.add_argument("--candidate-query", help="Named SQL candidate query to profile during planning; ignored for CSV scenarios.")
    plan_parser.add_argument("--output", default="validation-plan-result.json")
    run_parser = subparsers.add_parser("run", help="Execute one validation scenario.")
    run_parser.add_argument("--scenario", required=True)
    run_parser.add_argument("--candidate", required=True)
    run_parser.add_argument("--output", default="artifacts")
    run_parser.add_argument("--plan-source", choices=["embedded", "file", "openai"], default="embedded")
    run_parser.add_argument("--plan")
    run_parser.add_argument("--model")
    run_parser.add_argument("--allow-warn-plan", action="store_true")
    run_parser.add_argument("--enforce-release", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "plan":
        result = generate_validation_plan(scenario_path=args.scenario, provider=args.provider, plan_path=args.plan, model=args.model, candidate_query_name=args.candidate_query)
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"provider={result['metadata']['provider']} eval={result['eval']['score']}/{result['eval']['max_score']} gate={result['execution_gate']['status']}")
        return
    result = execute_pipeline(scenario_path=args.scenario, candidate_path=args.candidate, output_dir=args.output, plan_source=args.plan_source, plan_path=args.plan, model=args.model, allow_warn_plan=args.allow_warn_plan)
    release = result["release"]
    diff_count = result["differential"]["difference_count"] if result["differential"] else 0
    print(f"decision={release['decision']} residual_risk={release['residual_risk']} gate={result['execution_gate']['status']} traceability={result['traceability']['coverage_gate']['status']} differences={diff_count} eval={result['eval']['score']}/{result['eval']['max_score']}")
    if args.enforce_release and release["decision"] == "NO_GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

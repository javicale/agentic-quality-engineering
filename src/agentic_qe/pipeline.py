from __future__ import annotations

import argparse
from pathlib import Path

from .data import load_csv, load_scenario
from .differential import compare_datasets
from .evals import evaluate_validation_plan
from .evidence import build_evidence, write_json
from .observability import EventRecorder
from .release import decide_release


def execute_pipeline(
    *,
    scenario_path: str,
    candidate_path: str,
    output_dir: str,
) -> dict:
    scenario_file = Path(scenario_path).resolve()
    scenario = load_scenario(scenario_file)
    base_dir = scenario_file.parent

    expected_path = (base_dir / scenario["expected_dataset"]).resolve()
    candidate_file = Path(candidate_path).resolve()
    output = Path(output_dir)

    recorder = EventRecorder()
    recorder.record(
        "pipeline.started",
        scenario_id=scenario["id"],
        candidate=str(candidate_file),
        risk=scenario["risk"],
    )

    eval_result = evaluate_validation_plan(scenario["validation_plan"])
    recorder.record(
        "agent_eval.completed",
        status=eval_result.status,
        score=eval_result.score,
        threshold=eval_result.threshold,
    )

    expected_rows = load_csv(expected_path)
    candidate_rows = load_csv(candidate_file)
    recorder.record(
        "test_data.loaded",
        expected_rows=len(expected_rows),
        candidate_rows=len(candidate_rows),
    )

    differential = compare_datasets(
        expected_rows,
        candidate_rows,
        key_field=scenario["key_field"],
        critical_fields=scenario.get("critical_fields", []),
    )
    recorder.record(
        "differential.completed",
        status=differential.status,
        difference_count=differential.difference_count,
    )

    evidence = build_evidence(
        scenario=scenario,
        candidate_path=str(candidate_file),
        eval_result=eval_result,
        differential_result=differential,
        run_id=recorder.run_id,
    )

    signal = decide_release(
        scenario_risk=scenario["risk"],
        eval_result=eval_result,
        differential_result=differential,
    )
    recorder.record(
        "release_decision.completed",
        decision=signal.decision,
        residual_risk=signal.residual_risk,
    )
    recorder.record("pipeline.completed", decision=signal.decision)

    output.mkdir(parents=True, exist_ok=True)
    write_json(eval_result.to_dict(), output / "eval-result.json")
    write_json(evidence, output / "evidence.json")
    write_json(signal.to_dict(), output / "release-signal.json")
    recorder.write_jsonl(output / "events.jsonl")

    return {
        "run_id": recorder.run_id,
        "eval": eval_result.to_dict(),
        "differential": differential.to_dict(),
        "release": signal.to_dict(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-qe",
        description="Run the Agentic Quality Engineering reference pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute one validation scenario.")
    run_parser.add_argument("--scenario", required=True)
    run_parser.add_argument("--candidate", required=True)
    run_parser.add_argument("--output", default="artifacts")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "run":
        result = execute_pipeline(
            scenario_path=args.scenario,
            candidate_path=args.candidate,
            output_dir=args.output,
        )
        release = result["release"]
        print(
            f"decision={release['decision']} residual_risk={release['residual_risk']} "
            f"differences={result['differential']['difference_count']} "
            f"eval={result['eval']['score']}/{result['eval']['max_score']}"
        )


if __name__ == "__main__":
    main()

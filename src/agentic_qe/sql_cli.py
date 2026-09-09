from __future__ import annotations

import argparse

from .sql_pipeline import execute_sql_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agentic-qe-sql",
        description="Run the SQL/Database Differential Adapter reference pipeline.",
    )
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--candidate-query", choices=["good", "regression"], default="good")
    parser.add_argument("--output", default="sql-artifacts")
    parser.add_argument("--plan-source", choices=["embedded", "file", "openai"], default="embedded")
    parser.add_argument("--plan")
    parser.add_argument("--model")
    parser.add_argument("--allow-warn-plan", action="store_true")
    parser.add_argument("--enforce-release", action="store_true")
    args = parser.parse_args()

    result = execute_sql_pipeline(
        scenario_path=args.scenario,
        output_dir=args.output,
        candidate_query_name=args.candidate_query,
        plan_source=args.plan_source,
        plan_path=args.plan,
        model=args.model,
        allow_warn_plan=args.allow_warn_plan,
    )
    release = result["release"]
    diff_count = result["differential"]["difference_count"] if result["differential"] else 0
    print(
        f"decision={release['decision']} residual_risk={release['residual_risk']} "
        f"gate={result['execution_gate']['status']} differences={diff_count} "
        f"eval={result['eval']['score']}/{result['eval']['max_score']}"
    )
    if args.enforce_release and release["decision"] == "NO_GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

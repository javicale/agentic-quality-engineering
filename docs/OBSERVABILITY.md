# Test and Agent Observability — V2

Every pipeline run emits JSONL events with a stable `run_id`.

V2 adds planning and gate events before test execution:

```text
pipeline.started
planner.started
planner.completed
agent_eval.completed
execution_gate.completed
[execution.skipped | test_data.loaded]
[differential.completed]
release_decision.completed
pipeline.completed
```

This allows a future telemetry backend to distinguish:

- model/planner behavior;
- plan-quality failures;
- execution failures;
- product/data differentials;
- release-policy decisions.

The current JSONL recorder is intentionally simple. The next observability adapter can translate these events into OpenTelemetry spans/log records without changing domain behavior.

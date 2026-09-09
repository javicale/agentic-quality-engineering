# Test Observability

Traditional test reports answer: **what passed or failed?**

Test observability should also answer:

- what scenario was running?
- what risk did it represent?
- what data was loaded?
- what did the agent eval score?
- where did the execution diverge?
- what evidence supports the result?
- what release decision consumed that evidence?

## Event model

Each JSONL event contains:

```json
{
  "timestamp": "ISO-8601 UTC",
  "run_id": "correlation id",
  "event": "differential.completed",
  "attributes": {}
}
```

Current events include:

- `pipeline.started`
- `agent_eval.completed`
- `test_data.loaded`
- `differential.completed`
- `release_decision.completed`
- `pipeline.completed`

The `run_id` correlates events with evidence and release signals.

A future adapter can export the same semantic events to OpenTelemetry, Grafana, an evidence store or another observability platform.

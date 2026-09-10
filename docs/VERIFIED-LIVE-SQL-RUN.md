# Verified Live Agentic QE SQL Run

**Date:** 2026-09-09  
**Workflow run:** `34423451179`  
**Provider:** OpenAI Agents SDK  
**Model:** `gpt-5.6-luna`  
**MCP transport:** stdio  
**Scenario:** `sql-etl-reconciliation`  
**Candidate:** `good`

## Result

A real model call generated a structured SQL/database `ValidationPlan` after reading only sanitized scenario context and database profiles through MCP.

Observed end-to-end result:

```text
gpt-5.6-luna
  → scenario_context
  → database_profile(baseline)
  → database_profile(candidate=good)
  → quality_capabilities
  → structured ValidationPlan
  → deterministic eval 100/100
  → execution gate PASS
  → SQLite source/target differential
  → 3 rows compared
  → 0 differences
  → GO / LOW
  → exit code 0
```

Human release approval remained mandatory.

A sanitized copy of the generated plan is retained at:

`examples/sql-etl-reconciliation/live-plan-verified-2026-09-09.json`

No API key, database credential, connection URL, client identifier, employer data, or production data is stored in that fixture.

## What the agent did well

The plan explicitly used database metadata observed through MCP: four projected columns, three rows, three distinct business keys, zero duplicate keys, and zero nulls. It proposed schema, business-key, duplicate-key, nullability, critical-field, observability, and release-governance checks and retained human accountability.

The deterministic evaluator scored the plan **100/100** and the execution gate allowed validation.

## Important engineering finding: plan quality is not execution coverage

The agent proposed eight natural-language scenarios, including mutation testing. A single SQL differential run did **not** execute eight independent scenarios. The release `GO` was produced by the deterministic checks actually implemented by the adapter: projected-schema comparison, business-key reconciliation, duplicate-key detection, critical-field comparison, database profiling, the plan/eval gate, and release policy.

Therefore this run must not be described as “8/8 agent scenarios executed.” V3.1 adds an `execution-scope.json` artifact and embeds the same scope in evidence so future runs state exactly what deterministic checks were executed. Scenario-level plan-to-execution traceability remains explicitly marked `NOT_IMPLEMENTED` rather than being implied.

This is a useful QE finding: **a high-quality agent plan and a green execution are different claims, and evidence must distinguish them.**

## Candidate-context defect found and fixed

The first SQL planner implementation always profiled the named candidate `good`. That happened to match this verification run, but it would have been incorrect for a future `regression` or `schema_drift` live run.

The planner now receives the candidate query name explicitly. The manual live workflow passes the same candidate to both MCP planning and deterministic execution, and a regression test prevents the planning prompt from silently reverting to `good`.

## Workflow evolution

The permanent `Live Agentic QE Planning` workflow now supports:

- `csv-good`
- `csv-regression`
- `sql-good`
- `sql-regression`
- `sql-schema-drift`

The one-time SQL trigger used for this verification was removed after the run.

## Current interpretation

This experiment demonstrates that an agent can use metadata-only MCP database context to produce a strong SQL validation proposal that passes an independent deterministic plan gate, after which a separate deterministic adapter can produce decision-grade database evidence.

It does **not** establish production readiness, prove that every proposed scenario is executed, or validate enterprise SQL Server/PostgreSQL behavior.

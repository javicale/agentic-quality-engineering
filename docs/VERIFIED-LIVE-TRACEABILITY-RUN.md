# Verified Live V4 Plan-to-Execution Traceability Run

**Date:** 2026-09-09  
**Workflow run:** `34425509444`  
**Provider:** OpenAI Agents SDK  
**Model:** `gpt-5.6-luna`  
**MCP transport:** stdio  
**Scenario:** `sql-etl-reconciliation`  
**Candidate:** `good`

## Purpose

This was the closing experiment for the current learning phase. V3 had already shown that a live agent could use metadata-only database context to produce a strong SQL validation plan, but it also exposed a gap: a good plan was not the same thing as proof that every planned scenario executed.

V4 added an explicit deterministic capability registry and required every executable scenario to declare `required_capabilities`. This run tested whether a live model could stay inside that contract and whether release evidence could trace each planned scenario to actual execution.

## End-to-end result

```text
gpt-5.6-luna
  → scenario_context
  → database_profile(baseline)
  → database_profile(candidate=good)
  → quality_capabilities / execution_capabilities
  → structured ValidationPlan
  → plan eval 90/100 — PASS
  → pre-execution gate PASS
  → SQLite differential: 3 rows / 0 differences
  → plan traceability: 5 planned / 5 supported / 5 passed
  → deferred: 0
  → unsupported: 0
  → coverage gate PASS
  → GO / LOW
  → exit code 0
```

Human release approval remained mandatory.

## What the agent planned

The model produced five executable scenarios and used only registered capability IDs:

| Planned scenario | Priority | Required capability | Result |
| --- | --- | --- | --- |
| Projected schema equality | HIGH | `projected-schema-differential` | SUPPORTED / PASS |
| Business-key reconciliation | CRITICAL | `business-key-reconciliation` | SUPPORTED / PASS |
| Duplicate business-key detection | HIGH | `duplicate-key-detection` | SUPPORTED / PASS |
| Critical-field differential | CRITICAL | `critical-field-differential` | SUPPORTED / PASS |
| Database metadata profile consistency | HIGH | `database-metadata-profile` | SUPPORTED / PASS |

The agent explicitly moved unimplemented ideas—aggregate reconciliation, precision/tolerance analysis, query-plan/performance validation and row-level forensic inspection—into its rationale as deferred research instead of pretending those checks were executable.

## Eval interpretation

The deterministic plan evaluator scored the plan **90/100**, above the 80-point PASS threshold. The only partial dimension was risk coverage: the risk list strongly described integrity concerns but did not explicitly name a separate functional/transformation risk signal under the evaluator's current taxonomy.

This score was intentionally retained. The objective of V4 is not to optimize model wording for 100/100; it is to keep evaluation, execution coverage and release authority separate and auditable.

## Traceability evidence

`plan-traceability.json` reported:

```text
planned_scenarios = 5
supported         = 5
deferred          = 0
unsupported       = 0
passed            = 5
failed            = 0
not_executed      = 0
coverage_gate     = PASS
```

Every scenario points to deterministic execution evidence such as `database-differential.json` or `database-profile.json`.

## Negative control

Normal CI also contains a deliberately unsupported HIGH-priority scenario requiring `mutation-testing`.

That fixture proves the inverse property:

```text
Plan eval PASS
+ CSV differential PASS
+ HIGH scenario requires unknown capability
→ mapping UNSUPPORTED
→ execution NOT_EXECUTED
→ coverage gate BLOCKED
→ NO_GO / HIGH
```

An agent therefore cannot obtain release authority simply by naming a capability that the deterministic system does not implement.

## Preserved artifact

A sanitized copy of the live V4 plan is retained at:

`examples/sql-etl-reconciliation/live-plan-v4-traceable-2026-09-09.json`

No API key, database credential, connection URL, client identifier, employer data, production schema or production row is stored in the fixture.

## Conclusion

The current lab phase now demonstrates four separately testable claims:

1. the agent can propose a structured validation plan;
2. a deterministic eval and pre-execution gate decide whether that proposal may execute;
3. each executable plan scenario is mapped to a registered deterministic capability and evidence result;
4. incomplete HIGH/CRITICAL coverage can block release independently of a green partial execution.

This is the intended stopping point for the current learning phase. Additional adapters or telemetry should be driven by a new research question rather than by feature accumulation.

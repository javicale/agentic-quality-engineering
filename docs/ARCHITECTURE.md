# Architecture — Agentic QE V2

## Goal

V2 separates **agent creativity** from **quality authority**.

An LLM may propose how to validate a change, but deterministic components decide whether that plan is good enough to execute and whether the resulting evidence supports release.

```text
Change / Risk
      ↓
Read-only MCP context
      ↓
Agent validation planner
      ↓
Structured ValidationPlan
      ↓
Deterministic Plan Evals
      ↓
Execution Gate ───── BLOCKED → Evidence + NO_GO
      ↓ PASS
Test Data
      ↓
Automated / Differential Execution
      ↓
Observability Events
      ↓
Normalized Evidence
      ↓
Risk-based Release Decision
      ↓
Human approval boundary
```

## Components

### Domain/core

- `contracts.py` — strict structured contracts for agent plans and execution gates.
- `evals.py` — deterministic validation-plan scoring.
- `gating.py` — blocks weak or unsafe plans before execution.
- `differential.py` — deterministic source/expected/candidate comparison.
- `release.py` — release-signal policy.
- `evidence.py` — normalized evidence artifact.
- `observability.py` — append-only run events.

### Agent layer

- `planner.py` — provider-neutral planning interface.
- `openai_planner.py` — optional OpenAI Agents SDK adapter.
- `mcp_server.py` — read-only MCP tool server for scenario/data-profile context.

## Why this split matters

A model is probabilistic. Test execution, evidence, and release policy should not silently become probabilistic just because an agent participates.

V2 therefore treats the LLM as a **proposal generator** and keeps authority in independently testable contracts, evals, gates, evidence, and human accountability.

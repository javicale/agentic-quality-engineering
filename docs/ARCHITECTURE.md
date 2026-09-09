# Architecture — Agentic QE Learning Lab

## Working hypothesis

Agent reasoning can be useful for validation planning **without making quality authority probabilistic**, provided planning, execution, evidence and release responsibility remain separated.

```text
Change / Risk
      ↓
Read-only MCP Context
      ↓
Agent ValidationPlan
      ↓
Deterministic Plan Eval
      ↓
Execution Gate ───── BLOCKED → Evidence + NO_GO
      ↓ PASS
┌───────────────────────────────────┐
│ Deterministic experiment adapters │
│  CSV / ETL       SQL / Database   │
└───────────────────────────────────┘
      ↓
Differential Result
      ↓
Observability + Evidence
      ↓
Risk-based Release Signal
      ↓
Human Decision
```

## Components

### Core quality controls

- `contracts.py` — structured agent/output contracts.
- `evals.py` — deterministic validation-plan scoring.
- `gating.py` — pre-execution trust boundary.
- `differential.py` — tabular reconciliation, including composite and duplicate-key detection.
- `release.py` — reference release-signal policy.
- `evidence.py` — normalized evidence.
- `observability.py` — append-only experiment events.

### Agent experiment

- `planner.py` — planning interface.
- `openai_planner.py` — optional OpenAI Agents SDK experiment, aware of CSV and SQL scenarios.
- `mcp_server.py` — read-only scenario/dataset/database metadata tools.

### CSV experiment

- `pipeline.py` — CSV/ETL orchestration.
- `profile.py` — privacy-conscious CSV profiling.

### SQL/database experiment

- `sql_adapter.py` — SQLite reference adapter and environment-backed SQLAlchemy portability adapter.
- `sql_pipeline.py` — SQL orchestration and evidence integration.
- `sql_cli.py` — `agentic-qe-sql` CLI.

## Boundaries under test

### Agent boundary

The agent proposes. It cannot bypass deterministic evals or the execution gate.

### MCP boundary

The model receives metadata intended to be sufficient for planning without raw database rows or credentials.

### Database boundary

The code applies a read-only statement restriction. Real database permissions remain the actual security control and should use least privilege.

### Release boundary

A passing plan does not imply a passing system. Differential findings feed a separate release signal, and human accountability remains explicit.

## Current limitation

This architecture has been exercised only through a small synthetic lab and one retained live-agent scenario. It should be interpreted as a testable research scaffold, not as an enterprise architecture claim.

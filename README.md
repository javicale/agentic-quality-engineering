# Agentic Quality Engineering Lab

[![Agentic QE Quality Gate](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml/badge.svg)](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml)

> **Exploration status:** active learning / R&D lab. This repository documents executable experiments while I study how agentic workflows, MCP, evals, differential testing, observability and evidence could augment Quality Engineering. It is **not presented as a production-ready framework or as proof of long-term Agentic AI expertise**.

I am approaching Agentic Quality Engineering from a senior QA/QE perspective: start with familiar quality problems, form a research question, build the smallest useful experiment, observe what fails, and record what I learned.

## Research question

> **Where can probabilistic AI increase validation capacity without weakening deterministic quality controls, evidence or human accountability?**

```text
Change / Risk
      ↓
Read-only Context / MCP Tools
      ↓
Agent proposes ValidationPlan
      ↓
Deterministic Eval
      ↓
Execution Gate ─── BLOCKED → Evidence → NO_GO
      ↓ PASS
┌──────────────────────────────┐
│ Deterministic Validation     │
│  • CSV / ETL                │
│  • SQL / Database           │
└──────────────────────────────┘
      ↓
Observability + Evidence
      ↓
Risk-based Release Signal
      ↓
Human Decision
```

This is a hypothesis under investigation, not a claimed industry standard.

## What this repository is — and is not

**It is:**

- a learning lab built from executable experiments;
- a bridge between emerging Agentic AI concepts and established QA/QE practices;
- a place to test MCP context, agent evals, execution gating and differential validation;
- a record of findings, mistakes, limitations and next questions;
- intentionally based on synthetic / sanitized scenarios.

**It is not:**

- a production framework;
- a benchmark proving agent reliability;
- a replacement for QA judgment;
- a claim that an LLM should own release decisions;
- a representation of any client, employer, proprietary system or production dataset.

## Research method

```text
Research question
      ↓
Concept to understand
      ↓
Small experiment
      ↓
Observed result
      ↓
What failed / surprised me?
      ↓
QE implication
      ↓
Next hypothesis
```

See [Research Notes](docs/RESEARCH-NOTES.md) and [Learning Roadmap](docs/LEARNING-ROADMAP.md).

## Experiments completed so far

| Experiment | Research question | What was tested | Current finding |
| --- | --- | --- | --- |
| **E1 — Deterministic differential baseline** | Can release evidence be separated from simple test pass/fail? | CSV source-to-expected comparison, evidence and risk-based signal | Deterministic evidence provides the baseline an agent should not bypass. |
| **E2 — Agent planning + MCP** | Can an agent propose a validation plan while deterministic controls retain authority? | OpenAI Agents SDK, read-only MCP context, structured plan, eval and execution gate | Yes in the reference scenario, but the first live run also exposed a defect in the evaluator itself. |
| **E3 — SQL / Database Differential** | Can the same pattern validate database transformations without giving the agent raw database data or credentials? | SQLite reference execution, SQLAlchemy portability contract, schema/key/row/field reconciliation, MCP metadata profiles and a verified live SQL agent run | The live SQL experiment reached `100/100 → PASS → GO / LOW`; it also exposed the need to separate plan quality from execution coverage. |

## Most useful findings so far

The first live agent run produced a reasonable validation plan but initially scored **80/100** because the evaluator required overly literal tags. I treated that as an **evaluator defect**, corrected the deterministic taxonomy, and retained the captured live plan as a regression fixture.

The first live SQL agent run produced an excellent **100/100** plan, but it also proposed broader work such as mutation checks that a single SQL differential invocation did not execute. That exposed a second quality problem: **a strong plan and a green execution are different claims**. V3.1 therefore records `execution-scope.json` so a release signal cannot be casually interpreted as “every agent scenario ran.”

See [Verified Live Run](docs/VERIFIED-LIVE-RUN.md) and [Verified Live SQL Run](docs/VERIFIED-LIVE-SQL-RUN.md).

## E3 — SQL / Database Differential

The database experiment now tests four separate concerns:

```text
Read-only SQL
   ↓
Projected schema comparison
   ↓
Business-key reconciliation
   ↓
Row + critical-field differential
   ↓
Evidence + explicit execution scope
   ↓
Release signal
```

The differential layer explicitly detects:

- missing or extra projected columns;
- missing and unexpected rows;
- duplicate business keys rather than silently overwriting them;
- composite business keys;
- exact critical-field differences such as `0.00` versus `0`;
- row count, null count and key-cardinality signals.

### Verified live Agentic SQL path

On **2026-09-09**, a real `gpt-5.6-luna` call used read-only MCP `scenario_context`, baseline/candidate `database_profile`, and `quality_capabilities` to create a structured SQL validation plan. The plan scored **100/100**, the execution gate passed, the deterministic adapter compared 3 rows with 0 differences, and the reference release policy produced **`GO / LOW`**.

```text
gpt-5.6-luna
   ↓
metadata-only MCP database context
   ↓
SQL ValidationPlan — 100/100
   ↓
Execution Gate PASS
   ↓
3 rows / 0 differences
   ↓
GO / LOW
```

The sanitized live plan is retained at [live-plan-verified-2026-09-09.json](examples/sql-etl-reconciliation/live-plan-verified-2026-09-09.json).

### Reproduce the SQLite experiment

Good path:

```bash
agentic-qe-sql \
  --scenario examples/sql-etl-reconciliation/scenario.json \
  --candidate-query good \
  --output sql-artifacts-good \
  --enforce-release
```

Regression path:

```bash
agentic-qe-sql \
  --scenario examples/sql-etl-reconciliation/scenario.json \
  --candidate-query regression \
  --output sql-artifacts-regression \
  --enforce-release
```

Schema-drift path:

```bash
agentic-qe-sql \
  --scenario examples/sql-etl-reconciliation/scenario.json \
  --candidate-query schema_drift \
  --output sql-artifacts-schema-drift \
  --enforce-release
```

The good path reaches `GO / LOW`. The regression and missing-column paths deterministically produce `NO_GO` in the HIGH-risk reference scenario.

### Portable database boundary

SQLite remains the credential-free deterministic reference. A separate `SQLAlchemyDatabaseAdapter` resolves connection URLs **only from environment variables** and is tested in CI against a temporary database.

The URL value is not returned in database profiles, evidence or agent-visible MCP output. SQL Server, PostgreSQL and other SQLAlchemy-supported dialects can use the same experiment boundary when the appropriate DBAPI/driver is installed; that does **not** imply those enterprise integrations have already been production-validated here.

See [V3 SQL / Database Differential](docs/V3-SQL-DATABASE-DIFFERENTIAL.md).

## Agent + MCP database boundary

The MCP server exposes four tools:

- `scenario_context` — sanitized scenario/risk context;
- `dataset_profile` — CSV structure without raw rows;
- `database_profile` — projected columns, row count, null counts and key-cardinality metadata without raw database rows or connection URLs;
- `quality_capabilities` — deterministic capabilities and constraints.

For SQL scenarios, the OpenAI planner uses the **same named candidate query selected for execution**. A regression test prevents planning context from silently falling back to `good` when `regression` or `schema_drift` is being validated.

## Execution scope vs. plan scope

`eval-result.json` answers: **Is the agent's proposed plan good enough to trust as a proposal?**

`execution-scope.json` answers: **What deterministic checks did this adapter invocation actually execute?**

Those are intentionally separate. Current SQL runs record schema differential, business-key reconciliation, duplicate-key detection, critical-field differential and database profiling. Scenario-level one-to-one traceability between every natural-language plan scenario and an executable check is still marked `NOT_IMPLEMENTED` rather than being implied.

## Current implementation

The lab currently contains:

- deterministic CSV differential testing;
- optional OpenAI Agents SDK planning;
- read-only MCP context tools;
- structured `ValidationPlan` contracts;
- deterministic plan evals;
- a pre-execution gate;
- structured evidence and append-only observability events;
- SQLite SQL source/target experiments;
- schema drift, duplicate-key and composite-key validation;
- optional environment-backed SQLAlchemy adapter;
- explicit SQL execution-scope evidence;
- `GO / CONDITIONAL_GO / NO_GO` reference release signals;
- normal CI with no live model call;
- a manual workflow for deliberate CSV or SQL live-agent experiments.

The implementation should be read as **experimental scaffolding used to learn**, not as a finished platform.

## Safety boundaries

- synthetic or sanitized data only;
- no client ticket IDs, production schemas or proprietary assets;
- API/database secrets remain outside source control;
- MCP tools are workspace-bounded and metadata-oriented;
- raw database rows and connection URLs are excluded from MCP profiles;
- SQL validation accepts one read-only `SELECT` / CTE statement and rejects common mutation tokens;
- database permissions must still enforce least-privilege read-only access in real integrations;
- agent output is a proposal, not release authority;
- live model calls are manual, not part of normal CI.

## CI contracts

Every push/PR to `main` runs three independent jobs:

1. **deterministic-validation** — CSV baseline, weak-plan blocking, SQL good path, SQL regression `NO_GO`, SQL schema-drift `NO_GO`, duplicate/composite-key tests and evidence upload;
2. **agent-mcp-contract** — actual Agent/MCP dependency contracts and metadata-only database profiling, without an external model call;
3. **database-portability-contract** — SQLAlchemy environment-backed adapter against a temporary database, without external infrastructure or credentials.

## Manual live experiments

The `Live Agentic QE Planning` workflow supports:

- `csv-good`
- `csv-regression`
- `sql-good`
- `sql-regression`
- `sql-schema-drift`

A selected SQL candidate is passed consistently to both agent planning/MCP profiling and deterministic execution.

## Current limitations

- only a small number of synthetic scenarios have been explored;
- two verified live-agent scenarios are retained so far: CSV and SQL good paths;
- evaluator weights and threshold are illustrative, not empirically calibrated;
- scenario-level plan-to-execution traceability is not yet implemented;
- SQLAlchemy proves an adapter contract, not enterprise database production readiness;
- SQL Server/PostgreSQL-specific operational behavior is not yet validated here;
- release signals are reference policy logic, not organizational governance;
- observability remains lightweight rather than a full telemetry platform;
- no claim is made that agent-generated plans outperform experienced QA engineers;
- no production ROI, reliability or safety conclusions should be inferred from this lab.

## Next direction

Priority remains **understanding before expanding**. The highest-value next experiment is scenario-level plan-to-execution traceability: make every agent-planned check declare the deterministic capability that will execute it, then prove or defer it explicitly in evidence.

---

**Author:** Javier Capa — Senior Quality Software Engineer  
**Repository intent:** public learning lab connecting established Quality Engineering practice with emerging Agentic AI concepts.

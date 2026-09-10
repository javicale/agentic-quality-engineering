# Agentic Quality Engineering Lab

[![Agentic QE Quality Gate](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml/badge.svg)](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml)

> **Exploration status:** active learning / R&D lab. This repository documents executable experiments while I study how agentic workflows, MCP, evals, differential testing, observability, evidence and plan-to-execution traceability could augment Quality Engineering. It is **not presented as a production-ready framework or as proof of long-term Agentic AI expertise**.

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
Pre-execution Gate
      ↓
Scenario → Required Capability Mapping
      ↓
Deterministic Validation
      ↓
Plan-to-Execution Traceability
      ↓
Coverage Gate
      ↓
Observability + Evidence
      ↓
Risk-based Release Signal
      ↓
Human Decision
```

This is a hypothesis under investigation, not a claimed industry standard.

## Experiments completed

| Experiment | Research question | What was tested | Current finding |
| --- | --- | --- | --- |
| **E1 — Deterministic differential baseline** | Can release evidence be separated from simple test pass/fail? | CSV source-to-expected comparison, evidence and risk-based signal | Deterministic evidence provides the baseline an agent should not bypass. |
| **E2 — Agent planning + MCP** | Can an agent propose a validation plan while deterministic controls retain authority? | OpenAI Agents SDK, read-only MCP context, structured plan, eval and execution gate | Yes in the reference scenario; the first live run also exposed an evaluator defect. |
| **E3 — SQL / Database Differential** | Can the pattern validate database transformations without exposing raw database data or credentials? | SQLite, SQLAlchemy portability, schema/key/row/field reconciliation, metadata-only MCP and a verified live SQL run | Technically feasible in the synthetic lab; the live run exposed that plan quality and execution coverage are different claims. |
| **E4 — Plan-to-Execution Traceability** | Can every executable agent scenario be tied to deterministic capability and evidence? | `required_capabilities`, capability registry, scenario mapping, execution results and coverage-aware release policy | Yes for registered capabilities; incomplete HIGH/CRITICAL coverage now blocks release even if another deterministic check is green. |

## Main findings

The lab produced three findings that shaped the architecture:

1. **The evaluator must itself be testable.** The first live plan initially scored 80/100 because the evaluator relied on overly literal tags; the evaluator was corrected and the plan retained as a regression fixture.
2. **Plan quality is not execution coverage.** The first live SQL plan scored 100/100 while proposing broader checks than one SQL differential invocation actually executed.
3. **Coverage must affect release authority.** V4 makes every executable scenario declare deterministic capabilities and blocks `GO` when HIGH/CRITICAL plan coverage is unsupported, deferred or failed.

See [Verified Live Run](docs/VERIFIED-LIVE-RUN.md), [Verified Live SQL Run](docs/VERIFIED-LIVE-SQL-RUN.md), and [Plan-to-Execution Traceability](docs/PLAN-TO-EXECUTION-TRACEABILITY.md).

## V4 — Plan-to-Execution Traceability

Every executable scenario now declares `required_capabilities` using IDs from the deterministic capability registry exposed through MCP `quality_capabilities()`.

```text
ValidationScenario
      ↓
required_capabilities[]
      ↓
Capability Registry
      ↓
SUPPORTED / DEFERRED / UNSUPPORTED
      ↓
PASS / FAIL / NOT_EXECUTED
      ↓
Scenario evidence refs
      ↓
Coverage Gate
PASS / WARN / BLOCKED
      ↓
Release policy
```

A strong plan is no longer sufficient by itself. The final release signal accounts for what the system can actually execute:

- all planned scenarios covered and passing → preserve the deterministic release decision;
- incomplete LOW/MEDIUM coverage → at least `CONDITIONAL_GO / MEDIUM`;
- incomplete HIGH/CRITICAL coverage → `NO_GO / HIGH`.

The repository includes an intentionally unsupported HIGH-priority `mutation-testing` fixture. Its plan eval and CSV differential can both pass, but the capability registry marks the scenario `UNSUPPORTED`, the traceability gate becomes `BLOCKED`, and the final decision is `NO_GO / HIGH`.

That is the core V4 safety property.

## Deterministic execution capabilities

Current registry:

- `csv-record-differential`
- `projected-schema-differential`
- `business-key-reconciliation`
- `duplicate-key-detection`
- `critical-field-differential`
- `database-metadata-profile`
- `validation-plan-eval`
- `execution-gating`
- `structured-evidence`
- `execution-observability`
- `human-release-approval`

An agent cannot create a capability by naming one. Unknown capability IDs remain `UNSUPPORTED`.

## SQL / Database Differential

The SQL experiment includes:

- projected schema drift detection;
- missing and unexpected rows;
- duplicate and composite business keys;
- exact critical-field differential such as `0.00` versus `0`;
- row/null/key-cardinality profiles;
- SQLite deterministic reference execution;
- optional SQLAlchemy environment-backed portability;
- metadata-only MCP database context;
- verified live `gpt-5.6-luna` SQL planning.

The live SQL path previously reached:

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

That historical V3.1 plan predates the V4 `required_capabilities` contract. It remains preserved as evidence of the original experiment, but historical plans are not silently upgraded to V4 executable evidence.

## Evidence model

V4 separates four claims:

1. `eval-result.json` — **Was the agent proposal good enough?**
2. `execution-gate.json` — **Was it permitted to execute?**
3. `plan-traceability.json` — **Which planned scenarios were actually supported and executed?**
4. `release-signal.json` — **What does the combined evidence permit us to say about release?**

`evidence.json` uses schema version `4.0` and embeds the traceability structure. SQL runs also retain `execution-scope.json` as a compatibility summary, with scenario-level traceability marked `IMPLEMENTED`.

## Agent + MCP boundary

The MCP server exposes four read-only tools:

- `scenario_context` — sanitized scenario/risk context;
- `dataset_profile` — CSV structure without raw rows;
- `database_profile` — projected columns, row counts, null counts and key-cardinality metadata without raw rows or connection URLs;
- `quality_capabilities` — the exact deterministic capability registry and governance constraints available to agent planning.

The OpenAI planner is instructed to use exact capability IDs returned by `quality_capabilities().execution_capabilities`. Useful checks without an implementation must be described as deferred research rather than presented as executable scenarios.

## Safety boundaries

- synthetic or sanitized data only;
- no client ticket IDs, production schemas or proprietary assets;
- API/database secrets remain outside source control;
- MCP tools are workspace-bounded and metadata-oriented;
- raw database rows and connection URLs are excluded from MCP profiles;
- SQL validation accepts a single read-only `SELECT` / CTE statement and rejects common mutation tokens;
- real database permissions must still enforce least-privilege read-only access;
- agent output is a proposal, not release authority;
- HIGH/CRITICAL uncovered planned scenarios block release;
- human release approval remains mandatory;
- live model calls are manual, not part of normal CI.

## CI contracts

Every push/PR to `main` runs three independent jobs:

1. **deterministic-validation** — CSV and SQL good/regression/schema-drift paths, weak-plan pre-execution blocking, unsupported-HIGH traceability blocking, and evidence upload;
2. **agent-mcp-contract** — Agent/MCP contracts, metadata-only database profiling and authoritative execution capability registry, without an external model call;
3. **database-portability-contract** — environment-backed SQLAlchemy adapter against a temporary database without external infrastructure or credentials.

## Manual live experiments

`Live Agentic QE Planning` supports:

- `csv-good`
- `csv-regression`
- `sql-good`
- `sql-regression`
- `sql-schema-drift`

A selected SQL candidate is passed consistently to both agent planning/MCP profiling and deterministic execution.

## Current limitations

- experiments use a small number of synthetic scenarios;
- evaluator weights and threshold are illustrative, not empirically calibrated;
- SQLAlchemy proves an adapter contract, not enterprise database production readiness;
- SQL Server/PostgreSQL-specific operational behavior is not validated here;
- release signals are reference policy logic, not organizational governance;
- observability is lightweight rather than a full telemetry platform;
- no claim is made that agent-generated plans outperform experienced QA engineers;
- no production ROI, reliability or safety conclusions should be inferred from this lab.

## Phase status

**The current learning phase is feature-complete at V4.**

The objective was not to build a production platform. It was to establish and test a defensible boundary between probabilistic planning and deterministic quality authority:

```text
Plan → Eval → Permission → Capability Mapping → Execution → Evidence → Coverage Gate → Release Signal → Human Decision
```

Further adapters or telemetry should be added only when a new research question justifies them, not to inflate repository scope.

---

**Author:** Javier Capa — Senior Quality Software Engineer  
**Repository intent:** public learning lab connecting established Quality Engineering practice with emerging Agentic AI concepts.

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

## Experiments completed

| Experiment | Research question | Current finding |
| --- | --- | --- |
| **E1 — Deterministic differential baseline** | Can release evidence be separated from simple test pass/fail? | Deterministic evidence provides a baseline an agent cannot bypass. |
| **E2 — Agent planning + MCP** | Can an agent propose validation while deterministic controls retain authority? | Yes in the reference scenario; the first live run also exposed an evaluator defect. |
| **E3 — SQL / Database Differential** | Can the same pattern validate database transformations without exposing raw database data or credentials? | Yes in the synthetic lab; the first live SQL run exposed that plan quality and execution coverage are different claims. |
| **E4 — Plan-to-Execution Traceability** | Can every executable agent scenario be tied to deterministic capability and evidence? | Yes for registered capabilities; HIGH/CRITICAL uncovered work now blocks release. A final live V4 run mapped and passed all 5 planned SQL scenarios. |

## Verified final V4 live run

On **2026-09-09**, a real `gpt-5.6-luna` run used metadata-only MCP database context and the deterministic execution-capability registry to produce a traceable SQL validation plan:

```text
gpt-5.6-luna
   ↓
MCP scenario + sanitized DB profiles + execution capabilities
   ↓
ValidationPlan — 90/100 PASS
   ↓
Pre-execution Gate PASS
   ↓
SQL differential — 3 rows / 0 differences
   ↓
Plan traceability — 5 planned / 5 supported / 5 passed
   ↓
0 deferred / 0 unsupported / 0 not executed
   ↓
Coverage Gate PASS
   ↓
GO / LOW
```

The model used only registered capability IDs and moved unsupported ideas into rationale as deferred research instead of presenting them as executable checks. See [Verified Live V4 Traceability Run](docs/VERIFIED-LIVE-TRACEABILITY-RUN.md).

## Main findings

1. **The evaluator must itself be testable.** The first live plan exposed an overly literal evaluator taxonomy.
2. **Plan quality is not execution coverage.** The first live SQL plan scored 100/100 while proposing broader work than one adapter invocation executed.
3. **Coverage must affect release authority.** V4 binds scenarios to deterministic capabilities and evidence before a final release signal is accepted.

## V4 safety property

Every executable `ValidationScenario` declares one or more exact `required_capabilities` from the deterministic registry exposed by MCP `quality_capabilities()`.

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
Evidence refs
      ↓
Coverage Gate
PASS / WARN / BLOCKED
      ↓
Release policy
```

Release policy treats coverage as a real input:

- all planned scenarios covered and passing → preserve the deterministic release decision;
- incomplete LOW/MEDIUM coverage → at least `CONDITIONAL_GO / MEDIUM`;
- incomplete HIGH/CRITICAL coverage → `NO_GO / HIGH`.

The repository includes a negative-control fixture where a strong plan and green CSV differential still end in `NO_GO / HIGH` because a HIGH scenario requests unregistered `mutation-testing`.

## Execution capability registry

Current deterministic IDs:

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

Unknown IDs remain `UNSUPPORTED`; an agent cannot create execution authority by naming a capability.

## Evidence model

V4 separates four claims:

1. `eval-result.json` — **Was the proposal good enough?**
2. `execution-gate.json` — **Was the proposal permitted to execute?**
3. `plan-traceability.json` — **Which planned scenarios were actually supported and executed?**
4. `release-signal.json` — **What does the combined evidence permit us to say about release?**

`evidence.json` uses schema version `4.0` and embeds traceability. SQL runs also retain `execution-scope.json` as a compatibility summary.

## SQL / database experiment

The deterministic SQL layer covers projected schema drift, missing/unexpected rows, duplicate/composite business keys, exact critical-field differences, database metadata profiles, SQLite reference execution and an optional environment-backed SQLAlchemy portability adapter. MCP exposes database metadata only—never raw rows, connection URLs or credentials.

## Safety boundaries

- synthetic or sanitized data only;
- no client ticket IDs, production schemas or proprietary assets;
- API/database secrets remain outside source control;
- MCP tools are workspace-bounded and metadata-oriented;
- SQL execution is read-only by contract and should also use least-privilege DB identities in real environments;
- agent output is a proposal, not release authority;
- HIGH/CRITICAL uncovered scenarios block release;
- human release approval remains mandatory;
- live model calls are manual and separate from normal CI.

## CI contracts

Every push/PR to `main` validates:

1. **deterministic-validation** — CSV/SQL good and negative paths, weak-plan blocking, unsupported-HIGH traceability blocking and evidence upload;
2. **agent-mcp-contract** — real Agent/MCP contracts, metadata-only database profiling and the authoritative capability registry without a live model call;
3. **database-portability-contract** — SQLAlchemy adapter behavior against temporary infrastructure without credentials.

## Documentation

- [Plan-to-Execution Traceability](docs/PLAN-TO-EXECUTION-TRACEABILITY.md)
- [Verified Live V4 Traceability Run](docs/VERIFIED-LIVE-TRACEABILITY-RUN.md)
- [Verified Live SQL Run](docs/VERIFIED-LIVE-SQL-RUN.md)
- [Verified Live CSV Run](docs/VERIFIED-LIVE-RUN.md)
- [V3 SQL / Database Differential](docs/V3-SQL-DATABASE-DIFFERENTIAL.md)
- [Architecture](docs/ARCHITECTURE.md)

## Current limitations

- experiments use a small number of synthetic scenarios;
- evaluator weights and threshold are illustrative rather than empirically calibrated;
- SQLAlchemy proves an adapter contract, not enterprise database production readiness;
- SQL Server/PostgreSQL-specific operational behavior is not validated here;
- release signals are reference policy logic, not organizational governance;
- observability is lightweight rather than a full telemetry platform;
- no claim is made that agent-generated plans outperform experienced QA engineers;
- no production ROI, reliability or safety conclusions should be inferred from this lab.

## Phase status

**The current learning phase is complete at V4.**

The lab now implements and verifies the boundary it set out to study:

```text
Plan
 → Eval
 → Permission
 → Capability Mapping
 → Execution
 → Scenario Evidence
 → Coverage Gate
 → Release Signal
 → Human Decision
```

Further adapters, agents or telemetry should be added only when a new research question justifies them—not to inflate repository scope.

---

**Author:** Javier Capa — Senior Quality Software Engineer  
**Repository intent:** public learning lab connecting established Quality Engineering practice with emerging Agentic AI concepts.

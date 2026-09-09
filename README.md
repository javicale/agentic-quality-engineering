# Agentic Quality Engineering Lab

[![Agentic QE Quality Gate](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml/badge.svg)](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml)

> **Exploration status:** active learning / R&D lab. This repository documents experiments while I study how agentic workflows, MCP, evals, differential testing, observability and evidence could augment Quality Engineering. It is **not presented as a production-ready framework or as proof of long-term Agentic AI expertise**.

I am approaching Agentic Quality Engineering from a senior QA/QE perspective: start with familiar quality problems, form a research question, build the smallest useful experiment, observe what fails, and record what I learned.

## What I am trying to understand

The central question is:

> **Where can probabilistic AI increase validation capacity without weakening deterministic quality controls, evidence or human accountability?**

The current exploration looks at this possible flow:

```text
Change / Risk
      ↓
Context / Tools
      ↓
Agent proposes a Validation Plan
      ↓
Deterministic Eval
      ↓
Execution Gate
      ↓
Deterministic Validation
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
- a way to connect new Agentic AI concepts with established QA/QE practices;
- a place to test ideas such as MCP context, agent evals, execution gating and differential testing;
- a record of findings, mistakes, limitations and next questions;
- intentionally based on synthetic / sanitized scenarios.

**It is not:**

- a production framework;
- a benchmark proving agent reliability;
- a replacement for QA judgment;
- a claim that an LLM should own release decisions;
- a representation of any client, employer, proprietary system or production dataset.

## Research method

Instead of expanding features for their own sake, new work should follow this loop:

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
| **E3 — SQL differential experiment** | Can the same QE pattern work against database queries without giving an agent raw production data? | SQLite/SQLAlchemy reference adapters, schema/row reconciliation, sanitized database metadata | The pattern is technically feasible in a synthetic lab; production database applicability is still unproven. |

### Most useful finding so far

The first live agent run produced a reasonable validation plan but initially scored **80/100** because my evaluator required overly literal tags. I treated that as an **evaluator defect**, corrected the deterministic taxonomy, and kept the captured live plan as a regression fixture.

That matters more to this research than simply adding another adapter: **the system evaluating an agent must itself be testable.**

See [Verified Live Run](docs/VERIFIED-LIVE-RUN.md).

## Concepts I am currently learning

- What makes an **agent** different from a normal LLM call?
- When is **MCP** actually useful instead of ordinary application code or APIs?
- What makes an **eval** trustworthy enough to gate execution?
- How should agent output be observed, replayed and audited?
- Which decisions should remain deterministic?
- Where should human approval be mandatory?
- How can these ideas fit naturally into STLC, shift-left and risk-based testing rather than becoming an AI side project?

## Current implementation

The code exists to make the questions concrete. Today the lab contains:

- deterministic CSV differential testing;
- an optional OpenAI Agents SDK planning experiment;
- read-only MCP context tools;
- structured `ValidationPlan` contracts;
- deterministic plan evals;
- a pre-execution gate;
- structured evidence and observability events;
- synthetic database source/target differential experiments;
- SQLite and optional SQLAlchemy reference adapters;
- `GO / CONDITIONAL_GO / NO_GO` reference release signals;
- CI tests that do not require a live model call;
- a manual workflow for deliberately triggered live-agent experiments.

The implementation should be read as **experimental scaffolding used to learn**, not as a finished platform.

## Reference scenarios

### Decimal precision experiment

```text
Good candidate
→ Plan Eval PASS
→ Execution Gate PASS
→ Differential PASS
→ GO / LOW
```

```text
Regression candidate
→ Differential FAIL
→ NO_GO / HIGH
```

```text
Weak agent plan
→ Plan Eval WARN
→ Execution Gate BLOCKED
→ Tests are NOT executed
→ NO_GO / HIGH
```

### SQL / database experiment

```text
Synthetic source query
      ↓
Expected transformation query
      ↓
Candidate query
      ↓
Schema + key + critical-field reconciliation
      ↓
Evidence / release signal
```

The database experiment is intentionally portable and synthetic. It does **not** establish production readiness for SQL Server, PostgreSQL, enterprise ETL workloads or production credentials.

See [V3 SQL Database Differential Experiment](docs/V3-SQL-DATABASE-DIFFERENTIAL.md).

## Safety boundaries used in the experiments

- synthetic or sanitized data only;
- no client ticket IDs, production schemas or proprietary assets;
- API secrets remain outside source control;
- MCP tools are read-only and workspace-bounded;
- database metadata can be exposed without returning raw rows;
- agent output is treated as a proposal, not release authority;
- live model calls are manual, not part of normal CI.

## Running the lab

Core deterministic experiments:

```bash
python -m pip install -e ".[dev]"
pytest -m "not integration and not database_integration"
```

Agent/MCP contract tests without an external model call:

```bash
python -m pip install -e ".[dev,agent]"
pytest -m "not database_integration"
```

Optional SQLAlchemy database adapter tests:

```bash
python -m pip install -e ".[dev,database]"
pytest -m database_integration
```

A live agent run is intentionally separate and manual. See [Live Agent Run](docs/LIVE-AGENT-RUN.md).

## Repository map

```text
.
├── docs/
│   ├── RESEARCH-NOTES.md
│   ├── LEARNING-ROADMAP.md
│   ├── VERIFIED-LIVE-RUN.md
│   └── V3-SQL-DATABASE-DIFFERENTIAL.md
├── examples/
│   ├── etl-decimal-precision/
│   └── sql-etl-reconciliation/
├── schemas/
├── src/agentic_qe/
├── tests/
└── .github/workflows/
```

## Current limitations

These limitations are intentional and important:

- only a small number of synthetic scenarios have been explored;
- only one verified live-agent scenario is retained as evidence so far;
- evaluator weights and threshold are illustrative, not empirically calibrated;
- database adapters are reference experiments, not validated enterprise connectors;
- release signals are reference policy logic, not organizational governance;
- observability is currently lightweight and not a full telemetry platform;
- no claim is made that agent-generated plans outperform experienced QA engineers;
- no production ROI, reliability or safety conclusions should be inferred from this lab.

## Next direction

For now, the priority is **understanding before expanding**.

The next work should focus on learning questions and controlled experiments around:

1. agents vs. normal LLM calls;
2. MCP value and boundaries;
3. eval design and failure modes;
4. observability and replayability;
5. human-in-the-loop release governance;
6. only then, additional real QE execution adapters when they answer a clear research question.

---

**Author:** Javier Capa — Senior Quality Software Engineer  
**Repository intent:** public learning lab connecting established Quality Engineering practice with emerging Agentic AI concepts.

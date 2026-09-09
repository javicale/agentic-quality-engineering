# Agentic Quality Engineering

[![Agentic QE Quality Gate](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml/badge.svg)](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml)

A working Proof of Concept for **evidence-driven, agent-assisted Quality Engineering**.

This repository explores a Quality Engineering pipeline in which automation and agents increase validation capacity while **release accountability remains human-governed**.

```text
Change / Risk
      ↓
Test Data
      ↓
Agent Evals
      ↓
Automated Execution
      ↓
Differential Testing
      ↓
Observability
      ↓
Evidence
      ↓
Risk-based Release Decision
```

> This is not an "AI writes tests" demo. The goal is to make quality decisions more **observable, reproducible, auditable and risk-aware**.

## What this PoC demonstrates

- Synthetic test-data scenarios with no client or production data.
- A deterministic **agent-evaluation layer** that scores a proposed validation plan.
- Automated **differential testing** between expected and candidate datasets.
- Structured execution events for **test observability**.
- Normalized, machine-readable **evidence artifacts**.
- A simple **risk-based release decision engine**.
- A CI quality gate that runs the pipeline and tests without secrets.

## Reference scenario: decimal precision in ETL

The included scenario models a generic ETL regression in which decimal values such as `0.00` must retain their declared precision.

Two candidate datasets are provided:

- `candidate-good.csv` preserves the expected representation and produces a `GO` signal.
- `candidate-regression.csv` rounds decimal values and produces a `NO_GO` signal.

The example is synthetic and intentionally contains no employer, client, ticket, system or production identifiers.

## Repository structure

```text
.
├── .github/workflows/
│   └── quality-pipeline.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── EVALUATION-MODEL.md
│   ├── OBSERVABILITY.md
│   └── RELEASE-DECISION.md
├── examples/
│   └── etl-decimal-precision/
│       ├── scenario.json
│       ├── source.csv
│       ├── expected.csv
│       ├── candidate-good.csv
│       └── candidate-regression.csv
├── schemas/
│   ├── eval-result.schema.json
│   ├── evidence.schema.json
│   └── release-signal.schema.json
├── src/agentic_qe/
│   ├── data.py
│   ├── differential.py
│   ├── evals.py
│   ├── evidence.py
│   ├── models.py
│   ├── observability.py
│   ├── pipeline.py
│   └── release.py
└── tests/
```

## Run locally

Requires Python 3.11+.

```bash
python -m pip install -e ".[dev]"
pytest
```

Run the reference pipeline:

```bash
agentic-qe run \
  --scenario examples/etl-decimal-precision/scenario.json \
  --candidate examples/etl-decimal-precision/candidate-good.csv \
  --output artifacts
```

Run the intentionally regressed candidate:

```bash
agentic-qe run \
  --scenario examples/etl-decimal-precision/scenario.json \
  --candidate examples/etl-decimal-precision/candidate-regression.csv \
  --output artifacts-regression
```

The CLI writes:

```text
artifacts/
├── eval-result.json
├── evidence.json
├── events.jsonl
└── release-signal.json
```

## Release decision model

The current PoC emits one of three signals:

- **GO** — required validation passed and residual risk is within policy.
- **CONDITIONAL_GO** — no release-blocking failure was observed, but evidence or eval quality is incomplete.
- **NO_GO** — a critical/high-risk validation failed or release policy was violated.

This is intentionally a reference model, not a universal release policy.

## Agent evals

The "agent" boundary is represented through a proposed validation plan and a deterministic evaluator. This keeps CI reproducible and avoids pretending an LLM is required for every step.

The evaluator checks dimensions such as:

- risk coverage;
- expected-result specificity;
- evidence requirements;
- differential-testing intent;
- human approval requirement.

A future model adapter can generate the plan, but the **eval contract remains independent of the model provider**.

## Engineering principles

- **Evidence over assertion.**
- **Risk coverage over test-count vanity metrics.**
- **Deterministic foundations before autonomous behavior.**
- **Observability before unexplained automation.**
- **Human release accountability even when agents participate.**
- **Provider-independent contracts for agent outputs and evals.**

## Next extensions

- pluggable LLM/MCP agent adapters;
- schema/contract validation;
- Playwright execution adapter;
- database/SQL differential adapter;
- OpenTelemetry-compatible traces;
- richer risk aggregation;
- policy-as-code release gates;
- human approval workflow;
- historical evidence and trend analysis.

---

**Author:** Javier Capa — Senior Quality Software Engineer

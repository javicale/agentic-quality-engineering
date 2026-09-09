# Agentic Quality Engineering

[![Agentic QE Quality Gate](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml/badge.svg)](https://github.com/javicale/agentic-quality-engineering/actions/workflows/quality-pipeline.yml)

An executable Proof of Concept for **evidence-driven, agent-assisted Quality Engineering** where an LLM can propose validation strategy, but deterministic evals, execution gates, evidence and human accountability control what is allowed to happen.

```text
Change / Risk
      ↓
Read-only MCP Context
      ↓
Agent Validation Planner
      ↓
Structured ValidationPlan
      ↓
Deterministic Agent Evals
      ↓
Execution Gate ──── BLOCKED → Evidence → NO_GO
      ↓ PASS
Automated Execution
      ↓
Differential Testing
      ↓
Observability
      ↓
Evidence
      ↓
Risk-based Release Decision
      ↓
Human Approval Boundary
```

> **V2 principle:** agents may increase validation capacity; they do not silently inherit release authority.

## Why this is different from an “AI writes tests” demo

The model is only one component in the system. Its output is treated as an **untrusted proposal** until it passes deterministic quality checks.

V2 demonstrates:

- a real, optional **OpenAI Agents SDK** planning adapter;
- a read-only **MCP v2** context server;
- strict structured `ValidationPlan` output;
- independent **agent evals**;
- a pre-execution **quality gate** that blocks weak agent plans;
- automated differential data testing;
- append-only observability events;
- normalized machine-readable evidence;
- risk-based `GO / CONDITIONAL_GO / NO_GO` decisions;
- preservation of human release accountability;
- deterministic CI with **no API key required**;
- a manual live-agent workflow for real model runs when a secret is configured.

## Reference scenario

The repository uses a synthetic ETL scenario: decimal values such as `0.00` must retain their declared precision after transformation.

Three behaviors are demonstrated:

```text
Strong plan + good candidate
→ Plan Eval PASS
→ Execution Gate PASS
→ Differential PASS
→ GO / LOW
```

```text
Strong plan + regression candidate
→ Plan Eval PASS
→ Execution Gate PASS
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

That third path is the central V2 safety property.

## Verified live agent run

On **2026-09-09**, the `Live Agentic QE Planning` workflow completed end-to-end with a real OpenAI model call through the OpenAI Agents SDK and read-only MCP context.

```text
gpt-5.6-luna
→ MCP-grounded ValidationPlan
→ deterministic eval PASS
→ execution gate PASS
→ 3 rows compared
→ 0 differences
→ GO / LOW
→ exit code 0
```

The agent generated four scenarios covering decimal precision, record integrity, invalid/null handling, and ETL observability/reproducibility. Human release approval remained mandatory.

The live run also exposed an evaluator defect: exact fixture tags under-scored valid natural-language risk and evidence requirements. The evaluator was hardened to use a deterministic normalized signal taxonomy, and the sanitized live plan is now a permanent regression fixture that must score **100/100** while the intentionally weak plan remains blocked.

See [Verified Live Run](docs/VERIFIED-LIVE-RUN.md) and the sanitized [live plan fixture](examples/etl-decimal-precision/live-plan-verified-2026-09-09.json).

## Architecture

```text
src/agentic_qe/
├── contracts.py       # strict agent/output contracts
├── planner.py         # provider-neutral planning interface
├── openai_planner.py  # optional live OpenAI Agents SDK adapter
├── mcp_server.py      # read-only MCP context tools
├── profile.py         # privacy-conscious dataset profiling
├── evals.py           # deterministic plan evaluation
├── gating.py          # pre-execution trust boundary
├── differential.py    # deterministic data comparison
├── observability.py   # run events
├── evidence.py        # evidence normalization
├── release.py         # risk-based release policy
└── pipeline.py        # CLI/orchestration
```

See [Architecture](docs/ARCHITECTURE.md), [V2 Agentic Planning](docs/V2-AGENTIC-PLANNING.md), [MCP Tools](docs/MCP-TOOLS.md), [Security Boundaries](docs/SECURITY-BOUNDARIES.md), and [Verified Live Run](docs/VERIFIED-LIVE-RUN.md).

## Planning modes

### 1. Embedded — deterministic baseline

No LLM, no secret:

```bash
agentic-qe run \
  --scenario examples/etl-decimal-precision/scenario.json \
  --candidate examples/etl-decimal-precision/candidate-good.csv \
  --output artifacts \
  --enforce-release
```

### 2. File — replay an agent plan

```bash
agentic-qe run \
  --scenario examples/etl-decimal-precision/scenario.json \
  --candidate examples/etl-decimal-precision/candidate-good.csv \
  --plan-source file \
  --plan examples/etl-decimal-precision/agent-proposal-good.json \
  --output artifacts-agent \
  --enforce-release
```

Use the intentionally weak proposal to prove the execution gate:

```bash
agentic-qe run \
  --scenario examples/etl-decimal-precision/scenario.json \
  --candidate examples/etl-decimal-precision/candidate-good.csv \
  --plan-source file \
  --plan examples/etl-decimal-precision/agent-proposal-weak.json \
  --output artifacts-weak \
  --enforce-release
```

### 3. OpenAI — live agent + MCP

Install optional dependencies:

```bash
python -m pip install -e ".[dev,agent]"
export OPENAI_API_KEY="..."
```

Generate a plan:

```bash
agentic-qe plan \
  --scenario examples/etl-decimal-precision/scenario.json \
  --provider openai \
  --model gpt-5.6-luna \
  --output live-plan-result.json
```

Then replay that plan through deterministic execution:

```bash
agentic-qe run \
  --scenario examples/etl-decimal-precision/scenario.json \
  --candidate examples/etl-decimal-precision/candidate-good.csv \
  --plan-source file \
  --plan live-plan-result.json \
  --output live-artifacts \
  --enforce-release
```

See [Live Agent Run](docs/LIVE-AGENT-RUN.md).

## MCP context boundary

The agent receives three read-only tools:

- `scenario_context` — sanitized risk/change metadata;
- `dataset_profile` — columns, row counts and shape/decimal-scale distributions without raw rows;
- `quality_capabilities` — deterministic capabilities and constraints.

All path access is confined to `AGENTIC_QE_WORKSPACE`.

The reference live adapter uses MCP over **stdio**. The server can later move to Streamable HTTP without changing the domain contracts.

## Agent evaluation model

| Dimension | Weight |
| --- | ---: |
| Risk coverage | 20 |
| Expected-result specificity | 20 |
| Evidence requirements | 15 |
| Differential testing | 15 |
| Human accountability | 20 |
| Tool grounding | 10 |
| **Total** | **100** |

Default pass threshold: **80**.

The evaluator is deterministic and accepts normalized natural-language signals rather than requiring magic exact tags. The weights are a reference model, not a universal QA standard. See [Evaluation Model](docs/EVALUATION-MODEL.md).

## Evidence produced

Each run writes:

```text
artifacts/
├── validation-plan.json
├── eval-result.json
├── execution-gate.json
├── evidence.json
├── events.jsonl
└── release-signal.json
```

This separates:

- what the agent proposed;
- how the proposal scored;
- whether execution was permitted;
- what tests observed;
- what release policy concluded.

## CI strategy

Normal push/PR CI has two jobs:

1. **Deterministic validation** — core tests, good-candidate execution and proof that a weak plan is blocked.
2. **Agent + MCP contract** — installs the real optional OpenAI Agents SDK and MCP packages and tests integration contracts without making an external model call.

A separate `Live Agentic QE Planning` workflow is **manual-only** and uses `OPENAI_API_KEY` only when explicitly triggered.

## Repository structure

```text
.
├── .github/workflows/
│   ├── quality-pipeline.yml
│   └── agent-live-smoke.yml
├── docs/
│   └── VERIFIED-LIVE-RUN.md
├── examples/etl-decimal-precision/
│   ├── scenario.json
│   ├── source.csv
│   ├── expected.csv
│   ├── candidate-good.csv
│   ├── candidate-regression.csv
│   ├── agent-proposal-good.json
│   ├── agent-proposal-weak.json
│   └── live-plan-verified-2026-09-09.json
├── schemas/
│   ├── validation-plan.schema.json
│   ├── execution-gate.schema.json
│   ├── eval-result.schema.json
│   ├── evidence.schema.json
│   └── release-signal.schema.json
├── src/agentic_qe/
└── tests/
    └── integration/
```

## Local development

Core only:

```bash
python -m pip install -e ".[dev]"
pytest -m "not integration"
```

With Agent/MCP contracts:

```bash
python -m pip install -e ".[dev,agent]"
pytest
```

## Roadmap

V2 establishes the trusted agent-planning boundary. Next extensions:

- Playwright execution adapter;
- SQL/database differential adapter;
- OpenTelemetry spans/logs;
- MCP Streamable HTTP deployment;
- tool-input/output guardrails;
- human approval/interrupt workflow;
- signed evidence manifests;
- policy-as-code release gates;
- historical eval datasets and regression evals;
- multi-agent specialization for data, API, UI and release-risk analysis.

---

**Author:** Javier Capa — Senior Quality Software Engineer

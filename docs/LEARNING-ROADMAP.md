# Learning Roadmap — Agentic Quality Engineering

This roadmap is for understanding the concepts behind the lab before expanding the implementation further.

## Stage 1 — Agent fundamentals

### Learn

- LLM call vs. tool-using agent;
- model instructions, context and structured output;
- deterministic code vs. probabilistic model behavior;
- what an agent loop actually adds.

### Be able to explain

> Why would I use an agent here instead of asking an LLM for JSON once?

### Lab mapping

- `openai_planner.py`
- structured `ValidationPlan`
- embedded/file planners as non-agent baselines.

### Exit criterion

I can explain the architectural difference without referring to vendor marketing terms.

---

## Stage 2 — MCP and tool boundaries

### Learn

- MCP client/server/tool concepts;
- what problem MCP solves;
- read-only vs. write tools;
- least-privilege context;
- why exposing metadata may be safer than exposing raw data.

### Be able to explain

> What does MCP give this experiment that a normal Python function or REST API would not?

### Lab mapping

- `mcp_server.py`
- `scenario_context`
- `dataset_profile`
- `database_profile`
- `quality_capabilities`.

### Exit criterion

I can identify cases where MCP is useful and cases where it would be unnecessary complexity.

---

## Stage 3 — Evals and guardrails

### Learn

- what an eval is;
- golden datasets;
- deterministic vs. model-based grading;
- precision/recall trade-offs in a gate;
- false passes and false blocks;
- calibration and regression evals.

### Be able to explain

> Why should anyone trust the evaluator that decides whether an agent plan may execute?

### Lab mapping

- `evals.py`
- weak-plan fixture;
- verified live-plan regression fixture;
- execution gate.

### Exit criterion

I can describe the first evaluator defect in this repo and why fixing the evaluator was more important than tuning the prompt.

---

## Stage 4 — Observability and evidence

### Learn

- logs vs. metrics vs. traces;
- run IDs and correlation;
- replayability;
- decision-grade evidence;
- distinguishing model proposal, execution result and release decision.

### Be able to explain

> If the agent makes a poor decision, what evidence lets me reconstruct why?

### Lab mapping

- `events.jsonl`
- `evidence.json`
- `validation-plan.json`
- `eval-result.json`
- `execution-gate.json`
- `release-signal.json`.

### Exit criterion

I can trace one run from input context to final release signal without relying on the model's narrative.

---

## Stage 5 — Human-in-the-loop governance

### Learn

- approval boundaries;
- automation authority vs. recommendation authority;
- residual risk;
- escalation conditions;
- auditability.

### Be able to explain

> What may the agent recommend, what may it execute, and what must remain a human decision?

### Lab mapping

- `human_release_approval` in the validation plan;
- execution gate;
- reference release policy.

### Exit criterion

I can describe the authority boundaries of the lab in plain QA governance language.

---

## Stage 6 — Apply to familiar QE problems

Only after the earlier stages are understood, use additional experiments to answer specific questions in familiar domains such as:

- ETL/source-to-target validation;
- API contract testing;
- UI automation with Playwright;
- test-data setup;
- regression selection;
- release-risk evidence.

The goal is not to collect adapters. The goal is to learn **where agentic patterns create measurable QE value and where deterministic automation remains the better tool.**

## Current stop condition

Do not expand to multi-agent orchestration, production SQL connectors, OpenTelemetry infrastructure or policy-as-code simply because they are technically possible. Add them only when a research question requires them.

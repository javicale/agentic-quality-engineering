# Research Notes

This document records what I am learning while exploring Agentic Quality Engineering. The purpose is to preserve questions, observations and limitations — not to present experimental results as established best practices.

## Research framing

My starting point is Quality Engineering, not Agentic AI research. I already understand validation strategy, automation, ETL/data quality, risk and release evidence. The new question is how emerging agentic patterns may — or may not — improve those practices.

A useful experiment should answer a question I can explain in QA/QE terms.

---

## E1 — Deterministic evidence before agents

### Question

Before introducing an agent, can I make the validation flow explicit enough that results are reproducible and release evidence is separate from test execution?

### Experiment

A synthetic decimal-precision ETL scenario compares expected and candidate CSV data by key and critical fields, then emits normalized evidence and a reference release signal.

### Finding

A deterministic baseline is useful because it gives the agent a boundary: an agent may propose what to validate, but the actual comparison and evidence do not have to become probabilistic.

### Limitation

This is a tiny synthetic case. It does not prove the release model is appropriate for a real organization.

### What I learned

Agentic QE makes more sense to me when the deterministic part is designed first. Otherwise it is difficult to know what authority the agent is actually receiving.

---

## E2 — Agent-generated validation plan + deterministic gate

### Question

Can an LLM-based agent propose a validation strategy while a separate deterministic component decides whether that proposal is good enough to execute?

### Experiment

The lab introduced:

- read-only MCP context;
- structured `ValidationPlan` output;
- deterministic plan scoring;
- an execution gate;
- human release approval as a required boundary.

A live OpenAI Agents SDK run was executed against the synthetic decimal-precision scenario.

### Result

The live plan passed and the downstream deterministic validation finished with no differences.

More importantly, the first plan scored only **80/100** even though its content was reasonable.

### What went wrong

The evaluator expected exact fixture-style tags such as `data-integrity` and `execution-events`. Natural-language equivalents were under-scored.

### Engineering response

I classified this as an evaluator defect instead of forcing the agent to use magic words. The evaluator was changed to use a small normalized, deterministic signal taxonomy. The captured live plan became a permanent regression fixture.

### What I learned

An evaluator is not automatically trustworthy just because it is deterministic. **The evaluator itself needs tests, calibration and failure analysis.**

### Limitation

One successful live run is not evidence that agents reliably create strong validation plans. A larger golden dataset and repeated evaluations would be needed before making that claim.

---

## E3 — SQL / database differential experiment

### Question

Can the same pattern be applied to database-backed ETL validation while exposing only sanitized metadata to an agent?

### Experiment

Portable database reference adapters execute read-only expected and candidate queries and compare:

- returned schema;
- row identity/completeness;
- critical fields;
- exact string representation where precision matters.

A read-only MCP tool returns database metadata such as columns, row count and null counts without returning raw rows.

### Result

The synthetic good path reconciles successfully. The synthetic regression path detects representation changes and a missing record and produces `NO_GO` under the reference release policy.

### What I learned

Separating **agent context** from **deterministic execution data** is a useful design idea: the agent may not need the underlying records to reason about validation strategy.

### Limitation

The current adapters exist to make the experiment portable. This does not prove the design is ready for SQL Server, PostgreSQL, large datasets, distributed ETL, performance constraints or production credentials.

---

## Open questions

These are more important than adding another feature right now:

1. What precisely makes an agent preferable to a normal LLM call in a QE workflow?
2. When does MCP reduce coupling, and when is it unnecessary abstraction?
3. How should an eval dataset be built and calibrated from real QA outcomes?
4. What telemetry is needed to diagnose agent planning failures?
5. How should human review work when an agent plan is technically valid but contextually poor?
6. How can residual risk be represented without pretending that a formula replaces judgment?
7. Which Agentic QE patterns remain useful after removing the LLM entirely?

## Research rule going forward

Do not add a new adapter, agent or architecture layer unless it answers a clearly written research question.

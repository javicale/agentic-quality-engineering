# Architecture

## Purpose

The PoC separates **agent behavior**, **deterministic validation**, **observability**, **evidence**, and **release policy** so that one layer can evolve without making the entire quality system opaque.

## Pipeline

```text
Scenario / Risk
      │
      ├── Validation Plan ──> Agent Eval
      │
      ├── Expected Data
      │
      └── Candidate Data
              │
              v
      Differential Engine
              │
              ├── Structured Events
              ├── Evidence Artifact
              └── Release Policy
                       │
                       v
               GO / CONDITIONAL_GO / NO_GO
```

## Design boundaries

### 1. Scenario contract

Defines risk, test data, critical fields and the validation-plan contract.

### 2. Agent-eval contract

Evaluates whether a proposed validation plan is good enough to execute. The current implementation is deterministic. A future LLM or MCP agent can generate the plan without changing the evaluator interface.

### 3. Differential engine

Compares expected and observed output as data, not screenshots or prose. Differences are normalized with severity.

### 4. Observability

Every important transition emits a structured event with a `run_id`.

### 5. Evidence

Evidence combines scenario context, eval quality and differential findings into one machine-readable artifact.

### 6. Release policy

Release policy consumes evidence signals. It does not perform testing itself.

## Why this separation matters

Agentic systems fail when generation, execution and judgment are collapsed into a single opaque prompt. Quality Engineering needs independent contracts so outputs can be evaluated, replayed and governed.

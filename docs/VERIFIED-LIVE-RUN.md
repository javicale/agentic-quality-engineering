# Verified Live Agentic QE Run

**Date:** 2026-09-09  
**Workflow:** `Live Agentic QE Planning`  
**Workflow run:** `34388759682`  
**Provider:** OpenAI Agents SDK  
**Model:** `gpt-5.6-luna`  
**MCP transport:** stdio  
**Scenario:** `etl-decimal-precision`  
**Candidate:** `candidate-good.csv`

## Result

The live agent generated a structured `ValidationPlan` through read-only MCP context and the plan was then replayed through the deterministic Quality Engineering pipeline.

Observed pipeline result:

```text
Live model call
  → structured ValidationPlan generated
  → deterministic plan eval PASS
  → execution gate PASS
  → 3 rows compared
  → 0 differences
  → release decision GO
  → residual risk LOW
  → exit code 0
```

The execution gate preserved `required_human_approval: true`.

## Plan produced by the live agent

The agent proposed four validation scenarios covering:

1. exact decimal value and two-decimal scale preservation;
2. record identity and completeness;
3. blank/null/parse validity for critical fields;
4. observability and reproducibility of the ETL run.

It also requested the repository's deterministic capabilities for differential testing, plan evals, execution gating, structured evidence, event observability and risk-based release decisions.

A sanitized copy of the live plan is retained at:

`examples/etl-decimal-precision/live-plan-verified-2026-09-09.json`

No API key, raw secret, client identifier, employer data or production data is stored in that fixture.

## Engineering finding from the first live run

The first live plan initially scored **80/100**, exactly at the pass threshold, even though it contained meaningful natural-language risk and evidence requirements. The cause was not the agent plan; the V2 evaluator required exact fixture tags such as `data-integrity` and `execution-events`.

That finding was treated as an evaluator defect rather than as a reason to tune the agent to magic words.

The evaluator was hardened to use a deterministic normalized signal taxonomy. The captured live plan is now a permanent regression fixture and must score **100/100**, while the intentionally weak plan remains below the execution threshold.

This is an example of the intended architecture: **agent behavior is evaluated, but the evaluator itself is also testable and subject to quality engineering.**

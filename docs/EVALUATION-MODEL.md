# Agent Evaluation Model

The current evaluator scores a validation plan across five dimensions, each worth 20 points:

| Dimension | Intent |
|---|---|
| Risk coverage | Covers functional behavior and data integrity |
| Expected-result specificity | States explicit assertions and expected outcomes |
| Evidence requirements | Requests structured results and execution events |
| Differential testing | Compares candidate behavior/data against an expected baseline |
| Human accountability | Preserves human approval for release decisions |

A score of **80/100** or higher is considered `PASS`.

The purpose is not to claim that five checks are a complete agent-evaluation science. The purpose is to demonstrate the architecture:

```text
Agent output → independent eval → execution eligibility / review
```

Future evals can measure:

- hallucination rate;
- test relevance;
- risk coverage recall;
- duplicate test generation;
- unsafe tool use;
- requirement traceability;
- evidence completeness;
- regression-detection effectiveness.

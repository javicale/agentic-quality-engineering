# Validation Plan Evaluation Model — V2

Agent output is scored independently before execution.

| Dimension | Weight | Intent |
| --- | ---: | --- |
| Risk coverage | 20 | Functional and data-integrity risks are represented. |
| Expected-result specificity | 20 | Scenarios contain explicit, non-vague assertions and expected outcomes. |
| Evidence requirements | 15 | Structured results and execution events are required. |
| Differential testing | 15 | Data transformations use an explicit comparison strategy. |
| Human accountability | 20 | Release approval remains human-governed. |
| Tool grounding | 10 | Agent plans declare context/capabilities used to ground the plan. |
| **Total** | **100** | |

Default threshold: **80**.

A score below threshold produces `WARN`; the execution gate blocks WARN plans by default.

## Deterministic natural-language evaluation

The evaluator deliberately does **not** call an LLM to judge another LLM. It uses an auditable, normalized taxonomy of signals.

Examples:

- risk coverage recognizes deterministic signals such as `precision`, `rounding`, `regression`, `record`, `duplicate`, `null`, `completeness`, and explicit `functional` / `data-integrity` labels;
- evidence coverage recognizes both canonical tags and natural-language forms such as `machine-readable report`, `comparison result`, `execution log`, `event`, `timestamp`, and `environment`;
- expected results must be substantive rather than vague phrases such as `looks correct`.

This avoids a brittle exact-tag contract while keeping evaluation deterministic, inspectable and reproducible.

## Live-plan regression fixture

The first successful live OpenAI Agents SDK + MCP run produced a natural-language validation plan. That sanitized plan is committed at:

`examples/etl-decimal-precision/live-plan-verified-2026-09-09.json`

It is part of the automated eval regression suite and must score **100/100** under the hardened deterministic evaluator.

The threshold and taxonomy remain reference defaults and should be calibrated with empirical project outcomes rather than treated as universal industry standards.

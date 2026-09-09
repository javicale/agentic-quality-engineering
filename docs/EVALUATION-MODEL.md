# Validation Plan Evaluation Model — V2

Agent output is scored independently before execution.

| Dimension | Weight | Intent |
| --- | ---: | --- |
| Risk coverage | 20 | Functional and data-integrity risks are represented. |
| Expected-result specificity | 20 | Scenarios contain explicit assertions and expected outcomes. |
| Evidence requirements | 15 | Structured results and execution events are required. |
| Differential testing | 15 | Data transformations use an explicit comparison strategy. |
| Human accountability | 20 | Release approval remains human-governed. |
| Tool grounding | 10 | Agent plans declare context/capabilities used to ground the plan. |
| **Total** | **100** | |

Default threshold: **80**.

A score below threshold produces `WARN`; the execution gate blocks WARN plans by default.

The threshold is illustrative and should be calibrated with empirical project outcomes rather than treated as a universal industry standard.

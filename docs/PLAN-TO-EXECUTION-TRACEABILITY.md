# V4 — Plan-to-Execution Traceability

V4 closes the main evidence gap found during the first live SQL agent experiment: **plan quality is not execution coverage**.

A validation plan can be coherent, risk-aware and score 100/100 while still proposing checks that the current deterministic system cannot execute. V4 makes that distinction machine-readable and release-relevant.

## Contract

Every executable `ValidationScenario` declares one or more exact `required_capabilities`.

```text
Agent ValidationScenario
        ↓
required_capabilities[]
        ↓
Deterministic Capability Registry
        ↓
SUPPORTED / DEFERRED / UNSUPPORTED
        ↓
Actual capability result
PASS / FAIL / NOT_EXECUTED
        ↓
Scenario evidence refs
        ↓
Coverage Gate
PASS / WARN / BLOCKED
        ↓
Release policy
```

## Capability registry

The registry is code-owned, deterministic and exposed to the agent through `quality_capabilities().execution_capabilities`.

Current execution capabilities include:

- `csv-record-differential`
- `projected-schema-differential`
- `business-key-reconciliation`
- `duplicate-key-detection`
- `critical-field-differential`
- `database-metadata-profile`
- `validation-plan-eval`
- `execution-gating`
- `structured-evidence`
- `execution-observability`
- `human-release-approval`

An agent may not make a capability real by naming it. Unknown identifiers remain `UNSUPPORTED`.

## Scenario mapping states

- `SUPPORTED` — every declared capability exists and produced an execution result for the run.
- `DEFERRED` — a registered capability was not executed in this run, or no executable mapping is available.
- `UNSUPPORTED` — at least one declared capability is not in the deterministic registry.

Execution is recorded separately as:

- `PASS`
- `FAIL`
- `NOT_EXECUTED`

This prevents a plan scenario from being marked passed merely because the overall adapter returned green.

## Release policy

Traceability is a release input, not decorative metadata.

| Coverage gap | V4 policy |
| --- | --- |
| All planned scenarios PASS | Preserve the deterministic release decision |
| LOW/MEDIUM scenario incomplete | At least `CONDITIONAL_GO / MEDIUM` |
| HIGH/CRITICAL scenario incomplete | `NO_GO / HIGH` |
| Any mapped scenario FAIL | Existing differential policy plus traceability evidence applies |

A dedicated regression fixture proves the key property:

```text
Strong plan eval
      ↓ 100/100
Green CSV differential
      ↓ PASS
HIGH scenario requires mutation-testing
      ↓
Capability registry: UNSUPPORTED
      ↓
Traceability Gate: BLOCKED
      ↓
NO_GO / HIGH
```

The system therefore cannot convert a strong agent proposal plus a partial green execution into an unjustified `GO`.

## Pre-execution declaration gate

V4 also requires every validation scenario to declare `required_capabilities` before execution. Historical plans created before V4 can still be parsed for audit/regression purposes, but replaying them through the V4 execution gate requires an explicit capability mapping.

This preserves provenance without silently upgrading old evidence claims.

## Evidence

Every V4 run writes `plan-traceability.json` and embeds the same structure inside `evidence.json` (schema version `4.0`).

For every plan scenario it records:

- scenario name and priority;
- declared capabilities;
- mapping state;
- actual execution state;
- unsupported/deferred capabilities;
- capability-level results;
- evidence references.

SQL runs keep `execution-scope.json` as a compatibility summary, but `plan-traceability.json` is the canonical scenario-level artifact.

## Research conclusion for this phase

The lab now separates four distinct claims:

1. **Plan quality** — deterministic agent eval.
2. **Permission to execute** — pre-execution gate.
3. **What actually ran** — deterministic capability results and scenario traceability.
4. **What may be released** — risk-based release policy plus traceability coverage gate and human accountability.

That separation is the main architectural conclusion of the current Agentic QE learning phase.

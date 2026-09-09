# Risk-based Release Decision

The release engine is intentionally small and explicit.

## Signals

### GO

Produced when:

- deterministic validation passes; and
- the validation-plan eval meets threshold.

Residual risk: `LOW`.

### CONDITIONAL_GO

Produced when there is no policy-defined blocker, but validation quality or remaining findings require explicit review.

Residual risk: `MEDIUM`.

### NO_GO

Produced when a high/critical-risk scenario has a high-impact differential failure.

Residual risk: `HIGH`.

## Important constraint

This PoC does **not** claim that software releases can be reduced to one formula. A real implementation should calibrate policy using:

- product criticality;
- regulatory requirements;
- customer impact;
- historical defect data;
- change exposure;
- rollback capability;
- observability confidence;
- business tolerance.

The engineering point is that the decision should be **explicit, inspectable and supported by evidence**.

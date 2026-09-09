# Release Decision — V2

The release engine emits `GO`, `CONDITIONAL_GO`, or `NO_GO`.

## New V2 rule: execution gate first

If the validation plan fails the execution gate, tests are not run and the release signal is `NO_GO` with the gate reasons preserved as evidence.

This distinguishes two failure classes:

1. **The validation strategy is not trustworthy enough to execute.**
2. **The strategy was acceptable, but execution found a product/data problem.**

## Current reference policy

- Gate blocked → `NO_GO / HIGH`.
- High-impact differential failure in a high/critical-risk scenario → `NO_GO / HIGH`.
- Non-blocking findings or a WARN eval explicitly overridden → `CONDITIONAL_GO / MEDIUM`.
- Passing eval + gate + differential → `GO / LOW`.

A `GO` is not a claim of zero defects. It is a statement that the represented risks passed the configured evidence policy.

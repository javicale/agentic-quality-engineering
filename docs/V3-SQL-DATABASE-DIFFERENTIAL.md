# V3 — SQL / Database Differential Adapter

V3 extends the Agentic Quality Engineering reference system from file-based CSV comparisons to a database-aware validation boundary.

```text
Change / Risk
      ↓
Agent / MCP Context
      ↓
Sanitized Database Metadata
      ↓
Validation Plan Eval
      ↓
Execution Gate
      ↓
Read-only SQL Queries
      ↓
Schema Differential
      ↓
Row Reconciliation
      ↓
Critical-field Differential
      ↓
Observability + Evidence
      ↓
Risk-based Release Decision
```

## Reference adapter

SQLite is used for the reference implementation so CI stays deterministic, credential-free and reproducible while still exercising real SQL execution, schema discovery and keyed row reconciliation.

The database boundary is isolated in `sql_adapter.py`, allowing SQL Server or PostgreSQL adapters to reuse the same differential, evidence and release contracts later.

## Safety boundary

The adapter:

- permits only one `SELECT` or `WITH` statement per query;
- opens validation queries in SQLite read-only mode;
- exposes only columns, row counts and null counts through MCP `database_profile`;
- never exposes raw database rows to the agent;
- confines MCP database paths to `AGENTIC_QE_WORKSPACE`;
- keeps fixture/database mutation outside the Agent/MCP boundary.

## Differential layers

1. **Schema compatibility** — missing baseline columns are HIGH severity; a missing key is CRITICAL.
2. **Row reconciliation** — missing and extra keys are detected deterministically.
3. **Critical-field fidelity** — exact representation is compared, including values such as `0.00` versus `0`.
4. **Release policy** — high-impact findings in a HIGH-risk scenario force `NO_GO`.

## Reproduce

Good path:

```bash
agentic-qe-sql \
  --scenario examples/sql-etl-reconciliation/scenario.json \
  --candidate-query good \
  --output sql-artifacts-good \
  --enforce-release
```

Regression path:

```bash
agentic-qe-sql \
  --scenario examples/sql-etl-reconciliation/scenario.json \
  --candidate-query regression \
  --output sql-artifacts-regression \
  --enforce-release
```

The regression fixture intentionally changes `0.00` to `0`, changes `125.50` to `125.5`, and drops transaction `TX-003`.

## Production evolution

Next database adapters should preserve the same query-snapshot and differential contracts while changing connection mechanics:

- SQL Server through `pyodbc` or an organization-approved driver;
- PostgreSQL through `psycopg`;
- secrets supplied only through environment/secret stores;
- least-privilege read-only database identities;
- query allowlists and environment-specific connection policies.

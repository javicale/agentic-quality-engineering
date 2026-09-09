# V3 — SQL / Database Differential Adapter

V3 extends the Agentic Quality Engineering pipeline from file-based ETL validation to database-backed source/target reconciliation.

## Quality flow

```text
Change / Risk
      ↓
Read-only MCP database profile
      ↓
Agent ValidationPlan
      ↓
Deterministic Agent Eval
      ↓
Execution Gate
      ↓
Expected DB query ───────┐
                         ├─→ Schema + Key + Row + Field Differential
Candidate DB query ──────┘
                                      ↓
                             Observability + Evidence
                                      ↓
                         Risk-based Release Decision
                                      ↓
                           Human Approval Boundary
```

The database adapter does not grant the model arbitrary SQL execution. The agent receives only sanitized profiles from repository-defined read-only queries.

## What V3 validates

The adapter detects:

- projected schema drift;
- missing and unexpected rows;
- duplicate business keys;
- composite-key mismatches;
- critical-field value regressions;
- row-count and key-cardinality anomalies;
- null-count and result-type profile changes.

The same `DifferentialResult` and release policy used by the file pipeline are reused, so a high-risk database regression becomes a deterministic `NO_GO`.

## Reference adapter: SQLite scripts

CI uses repository-owned SQL fixtures to create ephemeral SQLite databases in memory. This keeps the example deterministic, portable and credential-free.

```bash
agentic-qe-db run \
  --scenario examples/sql-differential/scenario.json \
  --output artifacts-database \
  --enforce-release
```

Expected result:

```text
decision=GO residual_risk=LOW gate=PASS differences=0
```

Regression fixture:

```bash
agentic-qe-db run \
  --scenario examples/sql-differential/scenario.json \
  --candidate-source candidate-regression.sql \
  --output artifacts-database-regression \
  --enforce-release
```

Expected result:

```text
duplicate key + critical value differences + unexpected row
→ Differential FAIL
→ NO_GO / HIGH
```

Projected schema drift:

```bash
agentic-qe-db run \
  --scenario examples/sql-differential/scenario.json \
  --candidate-query-file query-schema-drift.sql \
  --output artifacts-database-schema-drift \
  --enforce-release
```

## Portable adapter: SQLAlchemy environment URLs

Production-like connections are optional and use SQLAlchemy 2.x. Connection URLs are resolved from environment variables; the URL itself is never written to evidence or returned through MCP.

Install:

```bash
python -m pip install -e ".[database]"
```

Example scenario target:

```json
{
  "provider": "sqlalchemy-env",
  "url_env": "CANDIDATE_DATABASE_URL",
  "query_file": "candidate-query.sql"
}
```

For Microsoft SQL Server, use a supported SQLAlchemy SQL Server dialect/driver such as `mssql+pyodbc` and install the corresponding DBAPI/ODBC driver in the execution environment. PostgreSQL and other SQLAlchemy dialects can use the same adapter contract.

The repository CI validates the SQLAlchemy adapter against a temporary SQLite database so portability is tested without requiring external infrastructure.

## MCP database boundary

V3 adds `database_profile(scenario_path, side)`.

The tool returns only provider name, row count, projected columns, null counts, value type categories, distinct key count and duplicate key count. It never returns connection URLs, credentials or raw database rows.

For real databases, use least-privilege read-only credentials.

## Read-only enforcement

The adapter accepts `SELECT` / read-only CTE queries and rejects common mutating SQL tokens including `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT` and `REVOKE`.

This is defense in depth, not a substitute for database permissions.

## Evidence

A database run emits:

```text
artifacts-database/
├── validation-plan.json
├── eval-result.json
├── execution-gate.json
├── expected-database-profile.json
├── candidate-database-profile.json
├── database-differential.json
├── evidence.json
├── release-signal.json
└── events.jsonl
```

Database evidence uses schema version `3.0` and stores only sanitized target identifiers.

## V3 design principle

**The model may decide what should be validated; deterministic adapters decide what the data actually says.**

That separation keeps agent reasoning useful while preserving reproducibility, auditability and human release accountability.

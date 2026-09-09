# V3 — SQL / Database Differential Experiment

## Research question

**Can an Agentic QE pattern validate database transformations while keeping database evidence deterministic and withholding raw rows/credentials from the agent?**

V3 is an experiment, not a production database framework.

```text
Change / Risk
      ↓
Agent + read-only MCP metadata
      ↓
ValidationPlan
      ↓
Deterministic Eval + Execution Gate
      ↓
Baseline SQL ────────────┐
                         ├─→ Schema + Key + Row + Field Differential
Candidate SQL ───────────┘
                                      ↓
                             Observability + Evidence
                                      ↓
                         Risk-based Release Signal
                                      ↓
                              Human Decision
```

## Reference implementation

SQLite is the public deterministic reference so CI can execute real SQL without external infrastructure or credentials.

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

Schema drift:

```bash
agentic-qe-sql \
  --scenario examples/sql-etl-reconciliation/scenario.json \
  --candidate-query schema_drift \
  --output sql-artifacts-schema-drift \
  --enforce-release
```

The regression fixture changes exact decimal representation and omits an expected transaction. The schema-drift candidate removes a projected baseline column.

## Differential layers

### 1. Projected schema

Missing baseline columns become explicit `__schema__` findings. Missing business-key columns are CRITICAL.

### 2. Business-key reconciliation

The shared tabular differential engine supports one or more key fields. It explicitly detects duplicate keys instead of silently overwriting duplicate rows during indexing.

Composite keys are rendered deterministically, e.g.:

```text
tenant=B | transaction_id=1
```

### 3. Row reconciliation

Missing expected rows are CRITICAL. Unexpected candidate rows are HIGH.

### 4. Critical-field fidelity

Critical fields use exact representation comparison, so values such as `0.00` and `0` are not treated as equivalent merely because they have the same numeric meaning.

### 5. Release policy

The experiment reuses the existing release policy. High-impact differential findings in a HIGH-risk scenario produce `NO_GO / HIGH`.

## Database profiles

Profiles expose metadata only:

- provider;
- projected columns;
- row count;
- null counts;
- key fields;
- distinct-key count;
- duplicate-key count.

No raw rows are included.

## SQLAlchemy portability experiment

`SQLAlchemyDatabaseAdapter` resolves a database URL from a named environment variable at execution time.

Install:

```bash
python -m pip install -e ".[database]"
```

Example experimental configuration:

```json
{
  "sql": {
    "engine": "sqlalchemy-env",
    "baseline_url_env": "BASELINE_DATABASE_URL",
    "candidate_url_env": "CANDIDATE_DATABASE_URL",
    "baseline_query": "SELECT ...",
    "candidate_queries": {
      "default": "SELECT ..."
    }
  }
}
```

The URL value is not stored in the scenario, returned by `database_profile`, or written to evidence/observability.

The same adapter contract can technically use SQL Server, PostgreSQL or other SQLAlchemy-supported dialects when the corresponding DBAPI/driver is installed. This lab has **not** established production readiness for those systems.

CI validates portability through SQLAlchemy against a temporary SQLite database.

## MCP experiment boundary

For SQL scenarios, the agent is instructed to inspect:

- `scenario_context(...)`;
- `database_profile(..., side='baseline')`;
- `database_profile(..., side='candidate')`;
- `quality_capabilities()`.

The SQLite reference is profiled in a temporary database. For environment-backed scenarios, the URL environment variables are passed into the MCP subprocess but their values remain outside model-visible structured output.

## Read-only defense in depth

The adapter accepts a single `SELECT` / read-only CTE statement and rejects common mutation tokens including `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`, `REPLACE`, `TRUNCATE`, `ATTACH`, `DETACH`, `VACUUM`, `PRAGMA`, `GRANT` and `REVOKE`.

This check is not a SQL security sandbox. A real experiment must also use least-privilege read-only database identities.

## Evidence

SQL runs produce the normal plan/eval/gate/evidence/release artifacts plus:

```text
database-profile.json
database-differential.json
```

Database evidence uses schema version `3.0` and records that raw rows were not exposed to the agent and connection URLs were not recorded.

## CI evidence

V3 is exercised by three independent contracts:

1. `deterministic-validation` — SQL good path, regression `NO_GO`, schema-drift `NO_GO`, duplicate/composite-key unit tests;
2. `agent-mcp-contract` — metadata-only `database_profile` through the actual MCP dependency;
3. `database-portability-contract` — environment-backed SQLAlchemy adapter without external infrastructure.

## Current conclusion

The experiment supports the hypothesis that **agent planning can be separated from deterministic database observation** in a small synthetic QE workflow.

It does not yet answer whether the approach is sufficiently scalable, observable, performant or safe for enterprise production ETL. Those remain future research questions.

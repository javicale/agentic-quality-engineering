# MCP Tools — Agentic QE Lab

The MCP surface is intentionally small, read-only and privacy-conscious. The purpose of these tools is to explore how much context an agent needs to plan useful validation without automatically receiving the underlying records or credentials.

## `scenario_context`

Returns sanitized scenario metadata:

- scenario id/title;
- risk level;
- business-key fields;
- critical fields;
- dataset filenames when applicable;
- SQL engine identifier when applicable.

## `dataset_profile`

For CSV experiments, returns structural information such as columns, row count, blank counts and representation distributions. Raw rows are intentionally excluded.

## `database_profile`

For database experiments, returns:

- provider;
- projected columns;
- row count;
- null counts;
- key fields;
- distinct-key count;
- duplicate-key count.

Preferred scenario-based usage:

```text
database_profile(
  scenario_path='examples/sql-etl-reconciliation/scenario.json',
  side='baseline'
)
```

or:

```text
database_profile(
  scenario_path='examples/sql-etl-reconciliation/scenario.json',
  side='candidate',
  candidate_query_name='good'
)
```

For the public SQLite scenario the tool creates an ephemeral database from the synthetic fixture. It also retains direct workspace-confined SQLite profiling for backwards compatibility.

Raw rows, connection URLs and credentials are not returned.

## `quality_capabilities`

Lists deterministic capabilities and constraints, including CSV/SQL differential validation, schema drift, row reconciliation, composite/duplicate keys, plan evals, execution gating, evidence and release signals.

## Workspace boundary

File-backed operations are restricted to `AGENTIC_QE_WORKSPACE`.

## Database credential boundary

Environment-backed connection URLs are resolved from named environment variables. Their values remain outside MCP structured output. Real experiments should use least-privilege read-only credentials.

## Transport

The reference agent experiment uses MCP over **stdio**. Transport evolution is deliberately separate from the current learning question.

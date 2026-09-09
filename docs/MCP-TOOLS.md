# MCP Tools

V2 exposes a small read-only MCP surface.

## `scenario_context`

Returns sanitized scenario metadata:

- scenario id/title;
- risk level;
- key field;
- critical fields;
- dataset filenames.

It does not return client identifiers, credentials, or arbitrary files.

## `dataset_profile`

Returns structural information about a CSV dataset:

- columns;
- row count;
- blank counts;
- value-length distributions;
- decimal-scale distributions.

The tool intentionally does **not** return raw rows. This demonstrates a privacy-preserving context pattern: give the agent enough signal to plan tests without automatically exposing the underlying records.

## `quality_capabilities`

Lists the deterministic capabilities available to the pipeline and its safety constraints.

## Path boundary

All file tools are restricted to `AGENTIC_QE_WORKSPACE`. Attempts to read outside that directory are rejected.

## Transport

The reference OpenAI adapter launches the MCP server over **stdio**. The server itself is compatible with the MCP SDK and can later be exposed through Streamable HTTP for a deployed environment.

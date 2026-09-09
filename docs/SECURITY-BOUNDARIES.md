# Security and Trust Boundaries

Agentic Quality Engineering should not mean unrestricted model access to engineering systems.

## Current controls

### 1. Read-only MCP tools

The planning agent receives context tools, not mutation tools. It cannot alter datasets, tests, release policy, or repository files through this MCP server.

### 2. Workspace path confinement

MCP file access is resolved beneath `AGENTIC_QE_WORKSPACE`. Path traversal outside the workspace is rejected.

### 3. No production/client data in the repository

All reference assets are synthetic.

### 4. Deterministic eval gate

Model output is evaluated independently. A poor score can stop execution.

### 5. Human release accountability

`human_release_approval=true` is a required boundary. A plan that removes it is blocked.

### 6. No API secret in normal CI

Push/PR CI tests SDK contracts without making a live model call. The API key is only used in the manually triggered live-agent workflow.

## Future controls

- tool-input and tool-output guardrails;
- per-tool approval policies;
- signed evidence manifests;
- policy-as-code authorization;
- tenant/workspace isolation;
- secret scanning and redaction;
- immutable evidence storage;
- model/provider allow-lists.

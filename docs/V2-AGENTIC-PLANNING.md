# V2 Agentic Planning

## Planning modes

The same pipeline supports three plan sources:

### `embedded`

Repository-owned deterministic plan. This is the default for CI and requires no model or secret.

### `file`

Loads a structured plan from JSON. This is useful for replaying a previous agent output, testing golden plans, or validating an externally generated plan.

### `openai`

Runs a real planning agent using the optional OpenAI Agents SDK adapter and the local Agentic QE MCP server.

## The agent's role

The agent is asked to:

1. inspect the sanitized scenario through MCP;
2. inspect a structural dataset profile rather than raw production rows;
3. discover available quality capabilities;
4. propose explicit risk-based validation scenarios;
5. request evidence;
6. preserve human release approval.

It returns a strict `ValidationPlan` structured output.

## The agent does not decide release

The generated plan is immediately evaluated by deterministic code. The execution gate can block the plan before any candidate dataset is tested.

This prevents a weak or overly permissive model output from automatically becoming execution policy.

## Replayability

A live plan can be saved and replayed later with `--plan-source file`. This separates model variability from deterministic test execution and makes incidents reproducible.

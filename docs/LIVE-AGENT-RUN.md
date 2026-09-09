# Running the Live Planning Agent

The repository is fully useful without an API key. A live model call is an optional V2 capability.

## Install agent dependencies

```bash
python -m pip install -e ".[dev,agent]"
```

## Configure credentials

```bash
export OPENAI_API_KEY="..."
export AGENTIC_QE_MODEL="gpt-5.6-luna"
```

Use the least expensive model that meets the planning quality you need; the model is configurable rather than embedded in release policy.

## Generate a live plan

```bash
agentic-qe plan \
  --scenario examples/etl-decimal-precision/scenario.json \
  --provider openai \
  --model gpt-5.6-luna \
  --output live-plan-result.json
```

The result contains:

- structured plan;
- planner metadata;
- deterministic eval;
- execution-gate result.

## Replay the plan deterministically

```bash
agentic-qe run \
  --scenario examples/etl-decimal-precision/scenario.json \
  --candidate examples/etl-decimal-precision/candidate-good.csv \
  --plan-source file \
  --plan live-plan-result.json \
  --output artifacts-live \
  --enforce-release
```

## GitHub Actions

`agent-live-smoke.yml` is manual-only. Add `OPENAI_API_KEY` as a repository Actions secret, then trigger the workflow and choose a model. Normal push/PR CI never consumes the secret or calls a model.

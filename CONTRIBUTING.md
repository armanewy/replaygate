# Contributing

## Prerequisites

- Python 3.11+
- Temporal extra dependencies for replay: installed through `.[temporal]`

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,temporal]"
```

Windows PowerShell equivalent:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,temporal]"
```

## Common Commands

```bash
make test
make lint
make verify-example-pass
make verify-example-fail
```

Equivalent direct commands:

```bash
python -m pytest
python -m ruff check replaygate tests examples
python -m replaygate.cli verify --config examples/temporal/replaygate.pass.yaml
python -m replaygate.cli verify --config examples/temporal/replaygate.yaml
```

## Regenerating Temporal Fixtures

The checked-in Temporal histories are generated from a local Temporal test environment:

```bash
python -m examples.temporal.generate_histories
```

This rewrites the fixture files under `examples/temporal/histories/`.

## Adding a New Adapter

1. Implement `WorkflowAdapter` in `replaygate/adapters/<engine>/`.
2. Add the engine to `WorkflowEngine`.
3. Register the adapter in `replaygate/adapters/registry.py`.
4. Reuse the shared verifier, policy, and report renderers.
5. Add contract and integration tests before expanding docs.

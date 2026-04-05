# Replay Gate

Replay Gate is a deployment-safety CLI for durable workflows.

It answers one question before rollout:

> Will this workflow code change break representative historical executions when the orchestrator replays them?

## Why This Exists

Durable workflow systems can wedge production executions even when normal tests pass. The dangerous change is often not a unit-test failure. It is a replay mismatch against existing workflow history.

Replay Gate is a pre-deploy safety gate for that class of failure.

## MVP Scope

### What works today

- real Temporal replay using the Temporal Python SDK
- local/file-based history ingestion
- typed YAML config
- `replay-gate verify`, `init`, and `explain`
- JSON, Markdown, and console reports
- policy thresholds with non-zero exit codes
- passing and failing Temporal example configs
- GitHub composite action wrapper
- unit, integration, and golden tests

### Intentionally out of scope

- live Temporal cluster fetching
- Azure Durable Functions and Step Functions adapters
- SaaS backend or web UI
- billing, auth, tenancy, or a database
- payload codec support beyond `none`

## Real Vs Deferred

### Real

- history discovery from local files
- Temporal workflow module loading
- replay execution via `temporalio.worker.Replayer`
- nondeterminism and workflow-type failure classification
- deterministic reports
- GitHub Action wrapper

### Deferred, not faked

- live-cluster history acquisition
- non-Temporal adapters
- advanced payload redaction plugins
- encrypted payload codec integration

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,temporal]"
```

Run the passing sample:

```bash
python -m replaygate.cli verify --config examples/temporal/replaygate.pass.yaml
```

Run the failing sample:

```bash
python -m replaygate.cli verify --config examples/temporal/replaygate.yaml
```

Explain the generated failing report:

```bash
python -m replaygate.cli explain --report examples/temporal/artifacts/report.json
```

Initialize a new config:

```bash
python -m replaygate.cli init --output replaygate.yaml
```

## Sample Output

Failing Temporal example:

```text
Replay Gate: FAILED
Project: replay-gate-examples
Engine: temporal
Histories checked: 2
Passed: 1
Failed: 1
Errors: 0
Skipped: 0

Top failures:
1. PaymentWorkflow / histories/payment_history.json
   kind: nondeterminism
   summary: Replay failed due to a command mismatch during replay.

Policy:
- max_failures=0 -> violated (1 observed)
- fail_on=nondeterminism -> violated
```

Checked-in sample reports live under `examples/temporal/expected/`.

## Testing

```bash
make test
make lint
```

Equivalent direct commands:

```bash
python -m pytest
python -m ruff check replaygate tests examples
```

## Security And Data Handling

- Workflow histories should be treated as sensitive data.
- Replay Gate is local-only by default and does not upload anything.
- Raw payload bodies are not emitted in report details by default.
- The repo examples use sanitized fixture inputs only.

## GitHub Action

Use the local composite action from this repo:

```yaml
- uses: ./.github/actions/replay-gate
  with:
    config: examples/temporal/replaygate.pass.yaml
```

See `.github/workflows/ci.yml` for a working example.

## Extension Path

Future engines should implement `WorkflowAdapter` and reuse the shared verification, policy, and reporting core. See [ARCHITECTURE.md](./ARCHITECTURE.md), [DECISIONS.md](./DECISIONS.md), [ROADMAP.md](./ROADMAP.md), and [CONTRIBUTING.md](./CONTRIBUTING.md).

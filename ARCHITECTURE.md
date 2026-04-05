# Architecture

## System Overview

Replay Gate is a local-first verification CLI for workflow-code deployments. The current MVP focuses on Temporal, but the architecture keeps the verification core engine-agnostic.

High-level flow:

1. Load typed YAML config.
2. Select an engine adapter.
3. Discover workflow history artifacts.
4. Load the candidate workflow package.
5. Replay each selected history.
6. Normalize failures into Replay Gate domain models.
7. Apply policy thresholds.
8. Emit console, JSON, Markdown, and HTML outputs.
9. Exit non-zero on policy failure.

## Core Abstractions

### Domain models

`replaygate/models.py` defines the shared types used across the pipeline:

- `WorkflowHistoryArtifact`
- `ReplayCandidate`
- `ReplayResult`
- `ReplayFailure`
- `PolicyDecision`
- `VerificationReport`
- `WorkflowTypeBreakdown`
- `ArtifactManifest`

These models are engine-agnostic and intentionally stable so adapters can evolve without changing report consumers.

### Adapter contract

`replaygate/adapters/base.py` defines the contract each engine adapter must satisfy:

- `load_candidate(config, config_path)`
- `discover_histories(config, config_path)`
- `replay_artifact(artifact, candidate, config, config_path)`

The core verifier never needs to know Temporal details directly. It only coordinates adapter calls and applies shared policy/reporting logic.

## Temporal Adapter

The Temporal adapter lives under `replaygate/adapters/temporal/`.

### Loader

`loader.py` discovers filesystem artifacts and parses a small Replay Gate history envelope:

```json
{
  "workflow_id": "payment-demo",
  "run_id": "...",
  "workflow_type": "PaymentWorkflow",
  "history": {
    "events": [...]
  }
}
```

The inner `history` object is real Temporal history JSON from `WorkflowHistory.to_json_dict()`.

### Replayer

`replayer.py` uses the real Temporal Python SDK:

- imports the configured workflows module
- extracts registered workflow classes
- builds `temporalio.worker.Replayer`
- replays a `WorkflowHistory.from_json(...)`

This is not mocked. Replay compatibility is determined by the SDK itself.

### Classifier

`classifier.py` translates Temporal exceptions into stable product failures:

- `nondeterminism`
- `unknown_workflow_type`
- `payload_decode_error`
- `adapter_error`
- `corrupted_history`

That keeps CLI output useful and avoids exposing raw SDK exceptions as the primary UX.

## Verification Flow

The orchestration lives in `replaygate/verifier.py`.

1. Parse config with Pydantic.
2. Build the configured adapter.
3. Load candidate workflow metadata.
4. Discover artifacts from configured sources.
5. Filter by workflow type and selection cap.
6. Replay each artifact.
7. Build a typed report summary, failure breakdown, workflow breakdown, and artifact manifest.
8. Evaluate policy.
9. Write requested outputs.

If initialization fails before replay starts, the verifier still emits a normalized `environment_error` report rather than crashing without an artifact.

## Policy Flow

`replaygate/policy.py` evaluates:

- `max_failures`
- `max_unknown`
- `fail_on`

The policy layer is engine-agnostic. Adapters only produce normalized results; the core decides whether rollout should be blocked.

## Reporting Flow

Reporting is split by surface:

- `reporting/console.py`
- `reporting/json_report.py`
- `reporting/markdown_report.py`
- `reporting/html_report.py`
- `reporting/view_models.py`

All renderers consume the same canonical `VerificationReport` model. Shared presenter logic lives in `view_models.py` so the CLI, GitHub markdown summary, and HTML report stay aligned.

The JSON report is stable and machine-readable. The Markdown report is job-summary friendly. The HTML report is the static investigation surface. The console summary is optimized for CI and local terminal feedback.

By default, raw payload bodies are not included in report details.

## Future Adapter Path

To add Azure Durable Functions or Step Functions later:

1. Implement a new adapter that satisfies `WorkflowAdapter`.
2. Add engine-specific discovery and replay normalization.
3. Reuse the existing policy and reporting stack unchanged.

The core deliberately avoids Temporal-specific concepts outside the Temporal adapter package so those future engines can slot in without reworking the verification pipeline.

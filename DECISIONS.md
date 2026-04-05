# Decisions

## D-001: Temporal-first for MVP

Replay Gate only fully implements Temporal in the MVP. Durable workflow replay risks are real for several engines, but trying to cover Azure Durable Functions and Step Functions now would dilute the quality of the core verification path. The architecture will keep adapters explicit so those engines can be added later.

## D-002: Python 3.11-3.13 for delivery speed and testability

Python provides fast iteration for CLI tooling, strong library support for typed config and reporting, and an easy path to deterministic automated tests. The MVP will use:

- `typer` for the CLI
- `pydantic` for typed models
- `PyYAML` for config loading
- `rich` for console output
- `pytest` for tests

The project currently caps support below Python 3.14 because core binary dependencies in the MVP stack are not yet reliable there.

## D-003: CLI-first before any web surface

The first trustworthy product surface is a local CLI and CI gate. This keeps the MVP close to real developer workflows and avoids fake SaaS scaffolding.

## D-004: Honest Temporal integration

The Temporal adapter uses the real Temporal Python SDK replay path against checked-in history fixtures. Live-cluster fetching is intentionally deferred so the MVP stays local-first and deterministic. The current implementation is real for module loading, history parsing, replay execution, and failure classification. Only cluster-history acquisition is deferred.

## D-005: Checked-in sanitized histories over live cluster coupling

The MVP ships with sanitized Temporal history envelopes generated from a local Temporal test environment. This keeps tests deterministic and allows the example command to run without external infrastructure while still exercising a real replay engine.

## D-006: Default to suppressing raw payloads in report details

Reports are designed to be useful without copying raw workflow payload bodies into JSON or Markdown outputs. The MVP keeps report details metadata-light and exposes a placeholder redaction hook for future customization.

## D-007: One canonical report model drives every UX surface

The CLI, GitHub markdown summary, JSON artifact, and static HTML report all render from the same `VerificationReport` structure. Shared presentation logic lives in `reporting/view_models.py` so failure wording, counts, workflow grouping, and artifact references stay consistent across surfaces.

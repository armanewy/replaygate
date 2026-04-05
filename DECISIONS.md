# Decisions

## D-001: Temporal-first for MVP

Replay Gate only fully implements Temporal in the MVP. Durable workflow replay risks are real for several engines, but trying to cover Azure Durable Functions and Step Functions now would dilute the quality of the core verification path. The architecture will keep adapters explicit so those engines can be added later.

## D-002: Python 3.11+ for delivery speed and testability

Python provides fast iteration for CLI tooling, strong library support for typed config and reporting, and an easy path to deterministic automated tests. The MVP will use:

- `typer` for the CLI
- `pydantic` for typed models
- `PyYAML` for config loading
- `rich` for console output
- `pytest` for tests

## D-003: CLI-first before any web surface

The first trustworthy product surface is a local CLI and CI gate. This keeps the MVP close to real developer workflows and avoids fake SaaS scaffolding.

## D-004: Honest Temporal integration

The Temporal adapter will use a real integration where practical. If live-cluster fetching or full SDK replay is not feasible inside the MVP, the repository will still implement a real adapter boundary, real history parsing, real classification, and deterministic fixture-backed verification. Any mocked or simulated behavior will be documented explicitly.

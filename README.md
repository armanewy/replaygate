# Replay Gate

Replay Gate is a deployment-safety CLI for durable workflows.

It answers one question before rollout:

> Will this workflow code change break representative historical executions when the orchestrator replays them?

## Status

This repository is being built as a real MVP.

Current plan:

- Temporal-first implementation
- Adapter-based core
- Local/file-based history verification first
- Honest boundaries around what is real versus mocked

## Planned MVP

- `replay-gate verify --config replaygate.yaml`
- Determinism-focused verification pipeline
- JSON, Markdown, and console reports
- Policy-based pass/fail exit codes
- Temporal adapter with fixture-based local replay support
- GitHub Action wrapper

## Repository Guides

- [ROADMAP.md](./ROADMAP.md)
- [DECISIONS.md](./DECISIONS.md)

More complete usage and architecture docs will land as implementation progresses.

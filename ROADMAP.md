# Roadmap

## Goal

Ship a working MVP for pre-deploy workflow replay verification with a real Temporal-first path and a clean adapter model for future engines.

## Milestones

### Milestone 0: Bootstrap

- [x] Initialize git repository
- [x] Choose Python 3.11+ CLI-first stack
- [x] Add initial `README.md`
- [x] Add `ROADMAP.md`
- [x] Add `DECISIONS.md`
- [x] Add initial project metadata and tooling

### Milestone 1: Core skeleton

- [x] Typed config schema
- [x] Domain models
- [x] CLI skeleton
- [x] Base adapter interface
- [x] Test harness

### Milestone 2: Verification engine

- [x] Verification orchestration
- [x] Policy engine
- [x] JSON report generation
- [x] Markdown report generation
- [x] Unit tests

### Milestone 3: Temporal adapter

- [x] Filesystem history discovery
- [x] Temporal replay path or best honest vertical slice
- [x] Temporal error classification
- [x] Integration tests

### Milestone 4: CI packaging

- [x] GitHub Action wrapper
- [x] Example workflow
- [x] Console UX polish
- [x] Golden tests

### Milestone 5: MVP hardening

- [x] Architecture documentation
- [x] Security and privacy notes
- [x] Demo artifacts
- [x] End-to-end verification
- [x] Final cleanup

## Guardrails

- Prefer smaller real coverage over broad fake coverage.
- Keep all outputs deterministic and testable.
- Local-first by default.
- Document every meaningful tradeoff in `DECISIONS.md`.

## Replay Gate — FAILED
**Tool:** 0.1.0  
**Project:** replay-gate-examples  
**Engine:** temporal  
**Config:** `examples/temporal/replaygate.yaml`  
**Git SHA:** `ebff8c6`  
**Histories checked:** 2  
**Passed:** 1  
**Failed:** 1  
**Skipped:** 0  
**Errors:** 0  
**Workflow types covered:** 2

### Policy decision
This change fails replay safety policy.

Violations:
- `max_failures=0 -> violated (1 observed)`
- `fail_on=nondeterminism -> violated`

### Failure breakdown
- nondeterminism: 1

### Workflow type breakdown

| Workflow type | Checked | Passed | Failed | Skipped | Errors | Dominant failure | Risk | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| PaymentWorkflow | 1 | 0 | 1 | 0 | 0 | nondeterminism | critical | nondeterminism detected |
| RefundWorkflow | 1 | 1 | 0 | 0 | 0 | none | low | all passed |

### Top failing histories
1. `histories/payment_history.json` — `PaymentWorkflow`  
   **Kind:** nondeterminism  
   **Summary:** Replay failed due to a command mismatch during replay.  
   **Likely cause:** The candidate workflow emitted a different command sequence than the historical execution.  
   **Hint:** Review recent workflow code changes and add Temporal versioning or patch gates before deploying.

### Artifacts
- JSON: `artifacts/report.json`
- Markdown: `artifacts/report.md`
- HTML: `artifacts/report.html`

## Replay Gate — FAILED
**Tool:** 0.1.0  
**Project:** payments-workflows  
**Engine:** temporal  
**Config:** `examples/temporal/replaygate.yaml`  
**Git SHA:** `abc123`  
**Histories checked:** 1  
**Passed:** 0  
**Failed:** 1  
**Skipped:** 0  
**Errors:** 0  
**Workflow types covered:** 1

### Policy decision
This change fails replay safety policy.

Violations:
- `max_failures=0 -> violated (1 observed)`

### Failure breakdown
- nondeterminism: 1

### Workflow type breakdown

| Workflow type | Checked | Passed | Failed | Skipped | Errors | Dominant failure | Risk | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| PaymentWorkflow | 1 | 0 | 1 | 0 | 0 | nondeterminism | critical | nondeterminism detected |

### Top failing histories
1. `histories/payment.json` — `PaymentWorkflow`  
   **Kind:** nondeterminism  
   **Summary:** command mismatch during replay  
   **Likely cause:** workflow command sequence changed  
   **Hint:** add Temporal versioning or patch gates

### Artifacts
- JSON: `artifacts/report.json`
- Markdown: `artifacts/report.md`
- HTML: `artifacts/report.html`

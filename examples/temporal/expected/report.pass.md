## Replay Gate — PASSED
**Tool:** 0.1.0  
**Project:** replay-gate-examples  
**Engine:** temporal  
**Config:** `examples/temporal/replaygate.pass.yaml`  
**Git SHA:** `ebff8c6`  
**Histories checked:** 2  
**Passed:** 2  
**Failed:** 0  
**Skipped:** 0  
**Errors:** 0  
**Workflow types covered:** 2

### Policy decision
This change passes replay safety policy.

Violations:
- none

### Failure breakdown
- none

### Workflow type breakdown

| Workflow type | Checked | Passed | Failed | Skipped | Errors | Dominant failure | Risk | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| PaymentWorkflow | 1 | 1 | 0 | 0 | 0 | none | low | all passed |
| RefundWorkflow | 1 | 1 | 0 | 0 | 0 | none | low | all passed |

### Top failing histories
- none
### Artifacts
- JSON: `artifacts/report.pass.json`
- Markdown: `artifacts/report.pass.md`
- HTML: `artifacts/report.pass.html`

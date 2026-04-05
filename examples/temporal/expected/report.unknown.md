## Replay Gate — FAILED
**Tool:** 0.1.0  
**Project:** replay-gate-examples  
**Engine:** temporal  
**Config:** `examples/temporal/replaygate.unknown.yaml`  
**Git SHA:** `ebff8c6`  
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
- `max_unknown=0 -> violated (1 observed)`
- `fail_on=unknown_workflow_type -> violated`

### Failure breakdown
- unknown_workflow_type: 1

### Workflow type breakdown

| Workflow type | Checked | Passed | Failed | Skipped | Errors | Dominant failure | Risk | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| LegacyWorkflow | 1 | 0 | 1 | 0 | 0 | unknown_workflow_type | high | unknown_workflow_type detected |

### Top failing histories
1. `histories/legacy_history.json` — `LegacyWorkflow`  
   **Kind:** unknown_workflow_type  
   **Summary:** Workflow type not registered in the verification environment.  
   **Likely cause:** The history references a workflow type that was not loaded from the candidate module.  
   **Hint:** Register the missing workflow type in the candidate module or exclude that history from this verification run.

### Artifacts
- JSON: `artifacts/report.unknown.json`
- Markdown: `artifacts/report.unknown.md`
- HTML: `artifacts/report.unknown.html`

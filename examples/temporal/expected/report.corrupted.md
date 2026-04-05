## Replay Gate — ERROR
**Tool:** 0.1.0  
**Project:** replay-gate-examples  
**Engine:** temporal  
**Config:** `examples/temporal/replaygate.corrupted.yaml`  
**Git SHA:** `ebff8c6`  
**Histories checked:** 1  
**Passed:** 0  
**Failed:** 0  
**Skipped:** 0  
**Errors:** 1  
**Workflow types covered:** 0

### Policy decision
This change fails replay safety policy.

Violations:
- `max_failures=0 -> violated (1 observed)`
- `max_unknown=0 -> violated (1 observed)`
- `fail_on=corrupted_history -> violated`

### Failure breakdown
- corrupted_history: 1

### Workflow type breakdown

| Workflow type | Checked | Passed | Failed | Skipped | Errors | Dominant failure | Risk | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| unknown-workflow | 1 | 0 | 0 | 0 | 1 | corrupted_history | medium | corrupted_history detected |

### Top failing histories
1. `histories/corrupted_history.json` — `unknown-workflow`  
   **Kind:** corrupted_history  
   **Summary:** History artifact could not be decoded.  
   **Likely cause:** The file was not valid JSON or did not match the expected Temporal history envelope format.  
   **Hint:** Regenerate the history fixture with the provided script or repair the artifact format before verifying.

### Artifacts
- JSON: `artifacts/report.corrupted.json`
- Markdown: `artifacts/report.corrupted.md`
- HTML: `artifacts/report.corrupted.html`

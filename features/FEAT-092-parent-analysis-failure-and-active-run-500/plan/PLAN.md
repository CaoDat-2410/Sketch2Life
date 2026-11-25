# FEAT-092 plan (Rev 1)

## Scope
- A. Declare the 8 optional provenance fields on `ParentActivityV1`; refresh OpenAPI golden.
- B. Modal drawing wait: a remote exception that is not a timeout and not a dispatch/transport failure
  after the call was accepted and the function ran to completion is a terminal worker failure
  (recoverable, retake allowed), not outcome-unknown. Timeouts stay outcome-unknown.
- C. App: `AWAITING_RECONCILIATION` must not spin silently for the whole budget; show an explicit
  "kết quả chưa rõ" message with a close-run action after a short grace period.

## Out of scope
Root-causing the Modal `AttributeError` itself (needs Modal logs from the deploy workspace); SVG guide redesign.

## Acceptance criteria
1. `ParentMainActivityV1.model_validate` accepts a suggestion-based snapshot containing the 8 fields.
2. A worker `AttributeError` from `call.get` yields `ModalFunctionExecutionFailed`, so the run ends
   `INPUT_REVIEW` + `job_state FAILED` with a retryable error; `TimeoutError` still yields outcome-unknown.
3. App surfaces a message (not endless spinner) for `AWAITING_RECONCILIATION`.
4. Unit/contract tests for 1-3 pass; `tools/validate_repository_security.py` passes.

# Plan Rev8 — reconcile a Modal dispatch rejected before call creation

**Status:** Approved under the owner's direct request on 2026-11-25 to repair the real Parent flow and complete two Android E2E runs with distinct synthetic drawings, topics, scripts, and videos. This is a narrow amendment to Plan Rev7 and Addendum 13.

## Evidence and diagnosis

- The current drawing attempt failed at `stage=function_spawn` with SDK type `ResourceExhaustedError` and no `modal_call_id`.
- The running Modal app inventory showed zero active tasks after the failure.
- Modal's Python SDK 1.6.3 creates a `FunctionCall` only after the server returns a function-call ID from the invocation request. Modal's invocation documentation says inputs exceeding platform limits are rejected with `ResourceExhaustedError`: [Function invocation methods](https://modal.com/docs/guide/function-invocation-methods).
- Therefore this exact response is a provider rejection before a worker call was accepted. It is distinct from a timeout, connection loss, or any failure after a call ID, which remain uncertain and must never be retried automatically.
- The current generic error mapper incorrectly treated the explicit pre-dispatch rejection as an unknown outcome, leaving the UI waiting and the run in `AWAITING_RECONCILIATION`.

## Scope

1. Add typed `ModalFunctionDispatchRejected` handling only for Modal `ResourceExhaustedError` thrown while `Function.spawn` is creating the call. Log the bounded status code, workload, stage, safe correlation refs, elapsed time, and `modal_call_id=None`; never log raw SDK message/details, prompt, image, token, or credentials.
2. Treat this response as a known, recoverable pre-dispatch failure. Preserve scratch cleanup. Do not change handling of timeouts, transport failures, missing call identity, worker failures, or any exception after a call ID; those remain uncertain and are not retried.
3. Add one bounded backoff retry for the same unchanged input only after the exact `ResourceExhaustedError` rejection. A second explicit rejection becomes a retryable UI error; an ambiguous result stops immediately.
4. Add a local/test-only application-repository reconciliation operation for the already affected run. It must use a row lock and CAS against the exact run state (`INPUT_PROCESSING` / `AWAITING_RECONCILIATION`), input revision, run revision, error code, and retained attached-drawing hash. It records an audit action with safe decision `MODAL_RESOURCE_EXHAUSTED_NO_CALL_ID` and returns the run to `QUEUED`. It cannot delete or replace data and is safe to replay; a replay must not change a different state or dispatch work.
5. Let the authenticated Parent UI resume that queued revision through the existing recovery endpoint once. The existing `start_drawing_analysis` CAS remains the only worker dispatch guard. If status changes or the endpoint returns 409, do not send another request.
6. Add focused tests for typed rejection, retry bound, ambiguous errors, CAS/audit behavior, and UI state. Rebuild only the isolated FEAT-085 API and root Expo bundle as required; continue the same existing synthetic run through the actual Android UI.
7. After the recovered first run completes, execute the second run with a different topic and independently generated child-style drawing. Continue through normal activity choice, story review, video admission, safety/technical checks, and Android playback. Record scripts, videos, per-stage timings, call IDs, sanitized logs, and screenshots in the Rev7 evidence folder.

## Preserved requirements

- No fixture or mocked inference; no quota, parser, quality, consent, upload-scan, admission, or safety bypass.
- Never retry an accepted or possibly accepted Modal call. A call ID, timeout, transport error, or any post-spawn failure remains uncertain and non-retryable without explicit reconciliation.
- No direct SQL/data edits, run deletion, profile/consent changes, credential disclosure, unrelated container changes, worktree use, commit, or push.

## Acceptance

- The current rejected dispatch is reconciled through the audited repository operation, then resumes through the real Android UI without uploading the drawing again.
- The code distinguishes explicit server rejection from uncertain outcomes and does not leave the Parent UI in an unbounded spinner for a known rejection.
- Two distinct Android Parent runs complete through actual Modal drawing/activity/story/video paths and playback, or each remaining provider/gate blocker is recorded with exact safe evidence and no unsafe retry.

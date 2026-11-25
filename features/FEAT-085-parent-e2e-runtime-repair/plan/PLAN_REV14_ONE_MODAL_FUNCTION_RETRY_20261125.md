# Plan Rev14 — one real Modal Function retry from Parent UI

## Objective

Use one normal Parent UI drawing-analysis request to determine whether the Modal CPU Sandbox limits notice is related to the previously observed `ResourceExhaustedError`, while preserving all application gates.

## Evidence and scope

- The deployed worker is invoked from the backend with `modal.Function.from_name(...).spawn(...)` and runs the drawing model on L40S; the screenshot notice describes CPU Sandbox limits. These are different Modal invocation primitives.
- The active Modal profile/environment and app deployment are checked before the one request.
- Use a synthetic child-style drawing and the authenticated Android Parent UI. Do not call the worker directly or send a hand-built payload.
- Before dispatch, prevent prior-run context from leaking into the new topic path. The Android flow currently retains the previous `idea` value when `beginTopicPath()` starts; clear it and add a focused regression check so the butterfly run is not paired with the bicycle idea.
- Submit at most one drawing-analysis request. If Modal returns a call ID, poll that same call and do not resubmit. If the request is rejected before a call ID, record the safe error category and stop.
- No video request, quota bypass, quality/safety bypass, Modal deployment/capacity/billing change, credential change, or second retry is in scope.

## Acceptance criteria

1. Record active Modal profile, environment, SDK version, app/function state, and pre-call stats without exposing credentials.
2. Verify the prior idea is cleared on a new topic path; focused regression check passes.
3. Record whether the Parent UI request is accepted (`modal_call_id`) or rejected (`RESOURCE_EXHAUSTED`/other typed error), with safe stage timings.
4. If accepted, record the existing worker outcome and output-contract reason, if any.
5. Compare the observed outcome with the CPU Sandbox notice and classify it as related, unrelated, or inconclusive based on the actual call path and error.
6. Save sanitized evidence in `evidence/ANDROID_PARENT_TWO_E2E_20261125/` and update FEAT-085 status/context.

## Stop conditions

- Stop after one accepted call reaches a terminal result.
- Stop immediately after one pre-call rejection; do not retry again.
- Stop if emulator, authentication, run state, or image provenance cannot be confirmed without creating a duplicate request.
- Do not claim the two-run E2E is complete unless both different-topic Parent flows reach their approved terminal success criteria, including video playback.

## Execution result — 2026-11-25

- Focused stale-idea regression: **2 passed**. A new topic path clears the prior idea before entering the next flow.
- One authenticated Android Parent UI request was submitted with a synthetic crayon butterfly drawing and a different topic from Run 1. The backend made its configured bounded `Function.spawn` attempts; both were rejected with `ResourceExhaustedError` before a call ID. The run did not reach drawing inference, activity selection, story, or video. The stop condition was followed; no further inference was sent.
- The CPU Sandbox limits notice is not the direct failure shown in this attempt: this backend path uses a Modal GPU Function via `Function.spawn`, not a CPU Sandbox. The exact platform account/compute/rate limit behind `RESOURCE_EXHAUSTED` remains undisclosed by the safe diagnostic.
- The separate owner-pasted accepted-call log shows a previous Qwen3.8 inference that failed the box contract (`BOX_INVALID`). Local strict parser/prompt changes now classify box errors precisely; `pytest deployment/modal/srs_v23/tests/test_drawing_understanding_v2.py -q` passed (**24 passed**). Deployment of this local worker change is not verified.
- Topic entry in this attempt was also checked: the catalog normalized `con trung` to `Côn trùng`; `butterfly` matched a catalog alias and normalized to `con bướm` without invoking AI. Custom inputs not resolved by catalog are routed to the separate AI validation workload, subject to its feature/policy gates.
- Evidence and complete outcomes: `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`.

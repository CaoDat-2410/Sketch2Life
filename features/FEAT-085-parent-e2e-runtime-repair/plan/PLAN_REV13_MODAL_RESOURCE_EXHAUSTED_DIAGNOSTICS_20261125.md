# Plan Rev13 — diagnose Modal pre-call resource rejection

**Status:** Approved under the project owner's direct request to fix Parent runtime errors and complete two real Android Parent E2E runs; this plan narrows the next safe diagnostic step after Addendum 14's stop condition.

## Evidence

- The Android Parent UI uploaded the synthetic bicycle drawing and created a run. The drawing Modal adapter staged 884,847 bytes in its scratch Volume.
- `Function.spawn` returned Modal SDK `ResourceExhaustedError` twice, with `modal_call_id=None`. No worker log or function-call ID exists, so the model did not start.
- `modal app info` confirms `sketch2life-srs23-drawing-vlm-dev` is deployed and exposes `analyze-drawing` configured for one L40S container. Read-only app logs show no worker start for this attempt.
- The adapter logs only the exception type and discards gRPC status/details. The current evidence cannot distinguish account/resource capacity, invocation rate, platform limits, or another server-side rejection.

## Scope

1. Add a small, allowlisted diagnostic mapper for `ResourceExhaustedError` at `Function.spawn`: gRPC status name, a bounded reason category derived from recognized server-detail patterns, and a one-way fingerprint/length of any unrecognized detail. Never log raw exception message/details, payload, image, prompt, tokens, or credentials.
2. Add focused unit coverage for recognized categories, unknown details, absent fields, and secret-like content remaining absent from logs. Preserve the existing one-retry bound and all unknown-outcome handling.
3. Run the repository security validator and focused tests; rebuild only the existing FEAT-085 API container with `--no-deps`. Preserve the database and all other containers/volumes.
4. Inspect the existing run through authenticated Android UI/status. After the diagnostic build is healthy, resume that same input through its existing authenticated recovery action exactly once. If the provider returns a call ID, do not repeat the inference; continue the accepted job. If Modal again explicitly rejects before a call ID, stop and report the newly classified reason without sending another request.
5. Continue the approved two-run E2E only after the current drawing job is accepted and completes. Keep the second run on a different topic and independently generated child-style drawing; use existing quota, parser, safety, and video gates.

## Acceptance and safety

- The pre-call rejection is logged with a safe, useful reason category and no raw provider detail.
- A focused test proves the mapper's behavior; API health passes after the targeted rebuild.
- At most one new UI resume is sent after this diagnostic change. A call ID means accepted work and is never retried.
- No Modal deployment/configuration, GPU capacity, billing, credentials, database rows, gates, or unrelated services are changed in this amendment.
- No fixtures, direct DB edits, Computer Use, real-child data, commit, or push.

## Execution result — 2026-11-25

- Safe diagnostics and focused tests are implemented; the API health check passed after a targeted `--no-deps` rebuild.
- The one approved Android UI resume was explicitly rejected again before call creation. The safe category was `ACCOUNT_QUOTA_OR_LIMIT`; Modal function statistics show zero accepted inputs and zero containers. Per the stop condition, no more inference was sent.
- The two-run E2E acceptance is **not met**: no drawing model call, activity result, story, or video was produced; the second run was not submitted.
- Full timings and evidence are recorded in `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`.


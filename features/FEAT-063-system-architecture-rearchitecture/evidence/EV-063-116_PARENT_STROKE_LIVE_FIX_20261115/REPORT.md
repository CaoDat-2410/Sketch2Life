# Rev87.20 — Parent construction-stroke live diagnosis and fix

**Date:** 2026-11-15<br>
**Status:** PARTIAL — the live Qwen guide still fails the hard geometry gate.<br>
**Environment:** Modal `dev`, `sketch2life-srs23-language-audio-dev`, Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.<br>
**Input:** synthetic topic `con mèo`; no child profile, photo, voice, consent, account data, or video.

## Result

The prompt/diagnostic correction addressed the first live failure (the final stage lacked an identifying feature stroke), but the one permitted final inference did not produce a usable guide. Qwen returned only **2 strokes for 8 stages** and both had duplicate geometry. The worker correctly rejected the output with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID` / `DUPLICATE_STROKE_GEOMETRY`. The aggregate geometry was only 70 characters, below the 16,384-character cap; this was neither a timeout nor an aggregate-size failure. No SVG/API guide or render was produced.

The failure means the Parent AI construction-guide path is **not verified as working** for this topic. The final-feature prompt change alone is insufficient. The hard duplicate-geometry and stage gates remain intact; no gate was relaxed and no generated output was substituted.

## Attempts and timings

| Attempt | Local/API outcome | Modal call | Worker/model details |
|---|---|---|---|
| 000 | HTTP 504 `MODAL_OUTCOME_UNKNOWN`, 2.636 s. Modal function was not found because the app was stopped; no GPU inference was dispatched. | None | `NotFoundError` before spawn. |
| 001 | HTTP 502 `MODAL_WORKER_FAILED_TERMINAL`, 194.418 s; request `9c4e0ec2-0d87-489d-b02f-fc05602b1b20`. | `fc-01M7EQJHZHNSKEP2EPT1Z29V9Z` | Worker 175.036 s; rejected `SVG_CONSTRUCTION_GUIDE_FINAL_FEATURE_MISSING`. Diagnostics showed 11 expected source paths, 13 strokes, 7 stages, 1,327 geometry chars, no unassigned strokes or unknown anchors. |
| 002 | HTTP 502 `MODAL_WORKER_FAILED_TERMINAL`, 189.152 s; request `cef0583e-dc59-4850-9233-9bc58adccd3e`. | `fc-01M7ER3Y7XE7NFCP6EPVX2CGMG` | Worker failure at output parse/source identity validation; `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`, reason `DUPLICATE_STROKE_GEOMETRY`, 2 strokes, 8 stages, 70 geometry chars, 11 source paths. Model inference 115.556 s; model load 17.245 s; catalog query expansion 38.624 s. |

Attempt 002 is the single final real inference authorized by Rev87.20. No retry or third inference was issued. The earlier attempt 001 and its correction remain separately recorded in this evidence folder.

## Changes and local verification

The worker prompt now explicitly requires an identifying `feature` stroke in the final stage and ties it to the final stage's `stroke_ids`. The parser still rejects a guide when that feature is absent and emits safe feature-count/stage-index diagnostics. A focused regression test checks the feature-stage mismatch. During test execution, the new test initially referenced a nonexistent exception attribute; the assertion was corrected to use the existing `error_code` field.

After the correction:

- Modal worker contract tests: **27 passed** (two Python asyncio event-loop deprecation warnings).
- Backend construction-guide/unit/API contracts: **12 passed**.
- Parent mobile SVG source contract: **3 passed**.
- `git diff --check` on the two code/test files: passed.

These checks cover deterministic contracts, not Qwen output quality. The model's two duplicate strokes in attempt 002 demonstrate that this remaining defect is in live generation, not an untested API timeout.

## Deployment and shutdown

The language/audio app was redeployed to Modal `dev` as deployment v2. CPU `/health` returned `status=ok`, the pinned Qwen checkpoint and SVG catalog `ready`, `gpu_allocated=false`, and `inference_executed=false`. The health request did not generate anything. After attempt 002, the app was stopped and `modal app info` confirmed `State: stopped` at 2026-11-15 11:45 SE Asia Standard Time.

## Evidence files

- `attempt_000_*`: no-dispatch preflight.
- `attempt_001_*`: first inference and its worker failure.
- `attempt_002_*`: final inference request/response summary and handler log.
- `modal_worker_final_logs.txt`: full Modal call logs with phase timings and safe geometry diagnostics; raw model output is not included.
- `health_after_redeploy.json`, `modal_app_stopped.txt`, and `modal_deploy_after_fix.json`: readiness, final app state, and deployment record.
- `test_results.txt`: focused tests before and after the prompt/diagnostic correction.
- `run_parent_construction_guide.py`: one-shot reproducibility harness. It bypasses only local identity/database authorization and calls the actual Parent route, Modal client, worker and response validation.

## Remaining work

Do not expose this AI draft path as a successful drawing guide. A follow-up should address the model's failure to produce distinct, meaningful construction strokes for all stages. Prefer a source-conditioned hybrid that derives/reuses trusted SVG geometry and lets the model assign semantic parts, stage order and child-readable instructions, with deterministic validation and adult review. Any new inference budget/deployment requires a new bounded plan. No Android UI, Firebase E2E, Teacher presentation, or visual child-readability evaluation is claimed here.

SRS §§1–31 are unchanged. The appended SRS §32.34 is environment-specific evidence only; the SRS remains unsigned.

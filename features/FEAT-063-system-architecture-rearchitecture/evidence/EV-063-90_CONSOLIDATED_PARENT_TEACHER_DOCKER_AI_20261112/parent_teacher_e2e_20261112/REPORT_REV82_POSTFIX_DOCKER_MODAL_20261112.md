# Rev82 post-fix Docker and Modal verification — 2026-11-12

## Scope and safety

- Synthetic-only local Firebase Auth Emulator and Docker data; no real child data or production Firebase.
- No fixture response counted as a pass. No video request was made.
- The existing Parent sketch-guide AI output was reused as evidence; it was not regenerated.
- The failed Parent drawing run (`DRAWING_OUTCOME_UNKNOWN`, `retryable=false`) was not retried.
- No other Parent AI inference was started after the bounded Teacher visual verification failed. This follows Rev82 Plan §21.
- Existing shared Modal Apps were not stopped. After the request, `modal container list -e dev --json` returned an empty list; no GPU worker remained active.

## Setup

- Docker stack `rev79-parent-local-20261112`: API, Modal health, Firebase Auth Emulator, MinIO, PostgreSQL, Redis and ClamAV were running; all declared health checks were healthy.
- The local Teacher seed was already present. The seed reconciled its Firebase Auth Emulator password and reused its existing organization, class, identity and assignment; it did not create duplicate entities.
- The FLUX dev app deployed successfully in 18.079 seconds after setting the local Modal CLI to UTF-8. The failed initial deploy was a Windows `charmap` log-encoding error before app publication.
- FLUX `/health` returned `status=ok`, `gpu_allocated=false`, `inference_executed=false`; no warmup was issued.

## AI/API outcomes

| Workflow | API result | Model / worker | Timing | Result |
|---|---|---|---:|---|
| Teacher lesson-plan suggestion | HTTP 200 | Qwen/Qwen3.5-9B | 240.981 s | PASS; synthetic plan created for review |
| Teacher Sketch Deck | HTTP 200 | Qwen/Qwen3.5-9B | 90.303 s | PASS; five-slide draft returned, review required |
| Teacher lesson visual, post-fix | HTTP 502 | FLUX.3 Image Klein, L40S | 398.967 s API; 91.883 s worker | FAIL at `progressive_panel_quality_gate`; no image returned |
| Parent fresh end-to-end AI flow | Not started | — | — | BLOCKED by the non-retryable unknown outcome on the existing seeded Parent run and the stop-after-failure limit in Plan §21 |
| Parent line-sketch guide | No new request | FLUX.3 Image Klein | Existing evidence | Prior successful synthetic result reused; no repeat call |

### Teacher visual failure details

The request passed authentication, organization authorization, request and reviewed-plan validation, checkpoint verification, GPU preflight, prompt upsampling, FLUX model load and image inference. The structured worker log then confirmed a terminal `WorkerContractError`:

`MODAL_PROGRESSIVE_GUIDE_STROKES_CHANGED`

The first three transitions retained 81.55%, 82.78% and 90.53% of the previous panel's ink. The Step 4 → Step 5 transition retained 9.46%, below the approved 12% hard floor; panel ink coverage fell from 1.7576% to 0.2328%. The worker rejected the candidate before encoding/returning it. This is a progression/retention gate rejection, not JSON parsing, API authorization, missing model, GPU inference, or worker crash-loop failure.

Worker timings: GPU preflight 4.617 s; prompt upsampling 57.615 s; FLUX model load 6.546 s; image inference 6.716 s; quality gate 0.216 s. About 307 seconds of the end-to-end API wait were outside the worker's recorded 91.883 seconds; current logs do not attribute that remainder to a single cause.

The exact call ID, request ID, stage timings and numeric transition diagnostics are in `results_rev82_postfix_20261112/teacher/lesson_visual_worker_diagnostics.json`. The API summary/error and the actual Teacher plan/deck outputs are saved in the same directory. There is no generated lesson-visual image to show because the worker rejected it.

## Parent workflow status

The seeded Parent's active run remains an unknown, non-retryable drawing-analysis outcome. The earlier full-flow runner stopped before activity selection because it had no subject-confirmed run eligible for the next step. To avoid repeating an unknown provider call, this verification did not create another Parent account or send drawing-analysis, activity-suggestion, or story-generation requests. The Parent AI flow therefore remains incomplete in this verification.

The prior successful generated deer line-sketch guide remains under `outputs/parent_ai/`; it was not regenerated. Existing unit coverage for Parent activity/schema and worker contracts was completed earlier in this Rev82 task (30 backend tests; 90 Modal tests, 4 skipped). This continuation adds 10/10 focused FLUX panel-quality tests.

## Remaining gate decision

The live output hit the 12% floor by 2.54 percentage points on one transition, after three strong transitions. A possible next adjustment is to permit one transition at or above 8% only in an 8-step guide, while preserving rejection below 8%, multiple low-retention transitions, blank/dense panels, invalid layout and sequences without meaningful progression. This change was not deployed: Plan §21 requires stopping paid calls and deployments after the single post-fix failure. A new bounded deployment and one verification request require a new owner-approved plan amendment.

## Evidence files

- `results_rev82_postfix_20261112/teacher/lesson_plan_suggestion.json` — real Qwen API result.
- `results_rev82_postfix_20261112/teacher/sketch_deck_response.json` — real five-slide Teacher deck result.
- `results_rev82_postfix_20261112/teacher/teacher_reviewed_plan_input.json` — reviewed synthetic request sent to the deck/visual APIs.
- `results_rev82_postfix_20261112/teacher/lesson_visual_postfix_summary.json` and `lesson_visual_postfix_error.json` — API result.
- `results_rev82_postfix_20261112/teacher/lesson_visual_worker_diagnostics.json` — structured Modal worker and transition diagnostics.
- `REPORT_PARENT_TEACHER_ANDROID_MODAL_E2E_20261112.md` — earlier Android/Parent attempt and its limitations.

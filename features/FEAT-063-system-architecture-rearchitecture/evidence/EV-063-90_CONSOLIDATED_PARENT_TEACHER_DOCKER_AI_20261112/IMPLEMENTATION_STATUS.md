# EV-063-90 — Rev81 implementation and Rev82 runtime record

**Date:** 2026-11-12 (Asia/Saigon)

**Status:** IN PROGRESS / PARTIAL. This file records the owner-approved Rev81 implementation plus bounded Rev82 runtime follow-up; it is not a completion claim.

## Approval and acceptance

- Owner instruction: “implement plan, make sure no fixture”.
- Approved plan: `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV81_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112.md`.
- SHA-256: `6BE36B78F949177FA87DCED2EA620713BFE8A8EFE092B844AD20EC83B7CF71C6`.
- Updated plan SHA-256 after owner clarifications and Modal Docker startup correction: `E8313747501660C70491FA0A56C029D7DB7773677434AC8132FE2F3CF218560D`.
- Latest approved plan SHA-256 after the no-product-request cost clarification and Modal Containers review: `494F55A33D56CD0E90D6217A29A6719E08DE2C3ED4CB8D251DF2EC2AFA75960F`.
- No fixture/mock/hardcoded response may drive the product workflow or count as E2E evidence. Local synthetic data is acceptable only through the real backend; unavailable services must surface an explicit error.
- Video inference, production data/publication, real-child test data, root `.env`/secret edits, destructive reset, commit and push are excluded.
- Owner clarifications: adaptive 4–8 guide stages (Rev60 still says 3–5; SRS remains unchanged); on-demand guide generation for lesson without guide; HTTPS YouTube/Vimeo embeds only.
- Docker Modal startup correction: reuse already-deployed drawing-VLM/language-audio/FLUX apps without redeploying them on each Compose start, run no-output worker warmups, then per-app `/health`; no permanent minimum GPU containers, no video/SAM2, and never stop shared Modal apps during Compose shutdown. Warmup may incur temporary GPU/model-load cost.

## Work package log

| Package | Result | Evidence |
|---|---|---|
| WP0 — approval and no-fixture baseline | PASS | Plan §8.1, `approvals/TASK_APPROVAL.md`, feature status/context |
| WP1 — Parent line-sketch construction and mismatch/retake flow | PARTIAL — prior guide reused; new Qwen3.5 drawing analysis and adult confirmation passed. New Teacher FLUX visual passed its mechanical gate as a review-required draft. | Rev82 bounded report and actual AI image below |
| WP2 — Parent activity pin and story input | PARTIAL — catalog-first activity worker returned valid JSON with three fallback drafts; backend rejected one positive unsafe-action match and two missing outdoor-location markers. Story was skipped. | Rev82 bounded report and worker output below |
| WP3 — Teacher editable, media-bearing presentation and review | PARTIAL — existing Teacher plan and five-slide Sketch Deck passed; a new lesson visual was generated. Presentation UI review/playback was not part of the §22 bounded API pass. | Prior Teacher outputs and new visual below |
| WP4 — Docker/local runtime and idempotent seed | PARTIAL — API and core dependencies healthy; Modal sidecar DEGRADED, drawing/FLUX health probes time out and language/audio functions are NotFound. | E2E report and `parent_teacher_e2e_20261112/logs/modal_startup_health_summary.json` |
| WP5 — real UI/API and bounded non-video Modal verification | PARTIAL — real Parent registration/profile/drawing/confirmation and Teacher AI APIs exercised. Parent activity gate failed; no story/video call. No fixture response counted. | Rev82 bounded report and allowlisted diagnostics below |

## No-fixture audit

Partial audit is recorded in the E2E reports. No fixture response or hardcoded output drove the Parent workflow; a generated synthetic drawing was used as input. Actual Teacher visual and Parent activity worker outputs are retained as synthetic AI evidence. Parent activity was rejected by the backend gate; the visual remains a Teacher-review draft. No non-AI UI screenshots are represented as AI evidence.

## Modal Containers and startup check — 2026-11-12

- Modal's official debugging guide describes Containers as running runtime instances: list active container IDs, open a debug shell, execute a command, and inspect live profiling/logs. The official Apps guide describes deployed Apps as persistent definitions until stopped; their Functions are invoked independently. The official cold-start guide explains that `scaledown_window`, `min_containers` and `buffer_containers` trade latency for resource use. References: [debugging and live containers](https://modal.com/docs/guide/developing-debugging), [Apps and Functions](https://modal.com/docs/guide/apps), [cold starts and warm containers](https://modal.com/docs/guide/cold-start), [pricing](https://modal.com/pricing).
- System fit: keep deployed Apps/Functions as the AI service architecture. The Modal dashboard Containers page is for viewing/debugging the temporary worker containers created by Modal. Docker uses an internal warmup Function invocation and `/health` checks; it does not create/deploy a Modal Container as a persistent product service.
- Warmup semantics: each configured worker receives one exact internal control envelope. This is still a real Modal Function invocation and can incur GPU/model-load plus idle scaledown cost; it carries no product input and performs no inference or output generation. No minimum GPU containers are configured. Apps may stay listed while live containers scale to zero.
- Verification command: `python -m pytest deployment/modal/srs_v23/tests -q -rs --basetemp .pytest-modal-containers-review-20261112` — **109 passed, 4 skipped**. All four skips are Qwen parser tests requiring the Modal worker image's `lmformatenforcer` dependency, which is not installed in the local host environment; no fixture output was used as workflow evidence.
- Static checks: targeted Ruff, `compileall` for changed Modal Python modules, and `docker compose config --quiet` — **PASS**.
- Docker runtime check: `docker info --format '{{.ServerVersion}}'` — **BLOCKED**; Docker CLI could not access `npipe:////./pipe/dockerDesktopLinuxEngine` (`permission denied`). No Docker containers, Modal Apps, warmup calls, product AI calls or model inference were started by this check. Live deployment/readiness and actual billing remain unverified.

## Runtime cleanup

- Stopped only the Metro process started for this emulator run and restored pnpm Metro links from the saved pre-test snapshot.
- Removed temporary Android UI-inspection XML and local internal screenshot/email scratch files where present.
- Left the user's Docker stack, emulator, shared Modal Apps, volumes and project-root `.env` running/unchanged. No Modal app was deployed or stopped by this E2E run.

## Rev81 Android + Modal real workflow verification — 2026-11-12

See [`parent_teacher_e2e_20261112/REPORT_PARENT_TEACHER_ANDROID_MODAL_E2E_20261112.md`](parent_teacher_e2e_20261112/REPORT_PARENT_TEACHER_ANDROID_MODAL_E2E_20261112.md) for routes, call IDs, timing, worker failure stages, local state and evidence limits.

- Parent Android used the live Expo UI, Docker API and Firebase Auth Emulator with synthetic-only data. Parent sign-in/profile, StoryRun creation, drawing attachment and read-only run retrieval were reached.
- FLUX guide failed cumulative-stroke quality validation. Qwen3.5 drawing inference completed but JSON parsing failed; API first returned `MODAL_OUTCOME_UNKNOWN`, and the terminal worker log later confirmed `MODAL_MODEL_OUTPUT_INVALID`. The StoryRun remains `AWAITING_RECONCILIATION`; no retry was sent.
- Activity and story calls were not made because subject confirmation did not pass. Video was excluded. Parent story-run collection GET returned 405.
- Teacher presentation was not started: local DB has no Teacher/org/class or Teacher-authored reviewed lesson (one Parent library seed exists); language/audio Modal functions resolve as `NotFoundError`.
- Docker Modal health sidecar is `DEGRADED`: drawing/FLUX warmups passed but their app `/health` probes timed out; language/audio function discovery failed. No accepted AI artifact exists, so AI result and screenshot directories remain empty.

## Rev82 bounded post-fix verification — 2026-11-12

- Focused FLUX progression tests: 10/10 passed. Existing Teacher lesson-plan and Sketch Deck APIs returned real Qwen3.5 outputs (240.981 s and 90.303 s); the five-slide deck remains a review-required draft.
- Existing Teacher seed identity/org/class assignment was reused idempotently. Docker stack services were healthy. The approved FLUX app update deployed successfully; CPU `/health` passed without GPU or inference, and the Modal container list was empty after the one verification call.
- One real Teacher visual API call passed GPU preflight, Qwen prompt upsampling, FLUX load and inference, then failed at the quality gate: Step 4 → Step 5 retained 9.46%, below the 12% floor. API returned terminal 502 after 398.967 s; worker duration was 91.883 s. Exact diagnostics: `parent_teacher_e2e_20261112/results_rev82_postfix_20261112/teacher/lesson_visual_worker_diagnostics.json`.
- No retry or additional paid call was made. Parent fresh AI remained stopped because the seeded run is `DRAWING_OUTCOME_UNKNOWN`/non-retryable and Rev82 Plan §21 requires stopping after this failure. Video was not called.
- Detailed report: `parent_teacher_e2e_20261112/REPORT_REV82_POSTFIX_DOCKER_MODAL_20261112.md`. Current status is partial, not complete; the generated Teacher visual image and full visual presentation were not returned.

## Rev82 §22 bounded real AI continuation — 2026-11-12

- The approved 8% single-transition floor passed focused image-mask tests. One real authenticated Teacher visual API call returned HTTP 200 in 412.987 s; the generated 8-step image is in `parent_teacher_e2e_20261112/results_rev82_final_20261112/teacher/teacher_lesson_visual_candidate.png`. It is a draft requiring Teacher review; visual inspection found sparse/repeated intermediate stages.
- One fresh synthetic Parent was registered through the backend/Auth Emulator. Role, consent-policy read, child-profile creation, StoryRun, drawing analysis (Qwen3.5: `con hươu`, 0.90, topic match) and adult confirmation passed. Activity AI returned valid `NO_MATCH` JSON with three drafts, but the backend returned 502 `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` / `UNSAFE_ACTION_TEXT`; two drafts also lacked explicit outdoor setting. Story generation was stopped by the prerequisite rule.
- The fallback prompt was clarified to require a named outdoor place per activity and safe adult-prepared materials. Safety/outdoor gates were not weakened. Parent worker/prompt/service focused tests passed **30/30** and targeted Ruff passed. This prompt edit occurred after the single allowed live activity call and has not been deployed or live-verified.
- Worker/API times, call IDs, hashes and allowlisted phases are in `parent_teacher_e2e_20261112/results_rev82_final_20261112/parent/parent_modal_worker_diagnostics.json`. Full report: `parent_teacher_e2e_20261112/REPORT_REV82_LIMITED_PARENT_TEACHER_20261112.md`.
- The owner stopped three Modal Apps after the run. They were not restarted. No retry, story, video, production Auth, real-child data, credential/token evidence or commit/push/merge occurred. Plan Rev82 §22's four-call cap is now consumed by one Teacher visual, one Parent drawing and one Parent activity inference; a new live activity attempt requires a new approved plan amendment.

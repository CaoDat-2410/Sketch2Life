# Plan Revision 58 — Complete the real Parent flow through a silent LTX video

**Date:** 2026-11-21  
**Status:** APPROVED by the owner’s direct instruction “fix nếu có bug, nào chạy đc vid thì mới dừng”  
**Feature:** FEAT-081 Parent mobile/API integration  
**Product authority:** FEAT-063 v2.7-draft, Rev57 baseline with local amendments through Rev73. Sections 1–31 are target requirements; §32 is environment-specific evidence. The SRS remains unsigned.

## 1. Goal

Continue the real Parent workflow on Android until one new synthetic session produces and plays a silent LTX-2.5 video candidate derived from that session’s drawing and adult-confirmed story. Diagnose and fix concrete defects encountered along the path; do not stop at a health check, isolated worker call, fixture, mock, or API-only smoke test.

The user’s instruction authorizes implementation and diagnosis-guided live testing through a rendered video. This plan pins that scope. It does not authorize bypassing consent, synthetic-data, ownership, confirmed-story, model-safety, or production admission rules.

## 2. Observed starting point

- The real Android app is on the Parent workflow; the latest same-profile StoryRun `b05c2b46-e760-4643-824b-b30b5387453f` is `SCRIPT_GENERATION_UNKNOWN`. Its second story revision is `AWAITING_RECONCILIATION`, its provider call ID is absent, and the active-owner lock is held. It must not be replayed or manually edited.
- The task API container is healthy at `127.0.0.1:58100`, but `SKETCH2LIFE_PARENT_VIDEO_DEV_CANDIDATE_ENABLED=false`.
- The FEAT-081 source has a local synthetic-only Parent video-candidate API, persistence/service, Modal adapter, and UI hooks. The FEAT-081 `deployment/modal/srs_v23/video_app.py` is still a scaffold and the named video app is absent from the current Modal deployment inventory.
- A separately reviewed FEAT-067 worktree contains an LTX-2.5/L40S worker that previously produced a silent MP4 candidate. That historical candidate was not produced by this FEAT-081 Android UI path, did not pass product safety/admission, and does not prove the current Modal account has the model checkpoint.
- The current Modal model Volume has no visible `ltx-2.5` directory. Model access, checkpoint presence, and runtime readiness must be verified before GPU inference.

## 3. Invariants and boundaries

1. Use LTX-2.5 on Modal L40S as required by the current SRS. Do not substitute Wan, another model, or another GPU class.
2. Use only a synthetic Parent profile and a newly generated synthetic drawing. No real child image, account, transcript, or identifying data enters the test.
3. The generated video is silent; no narration, audio track, or TTS call is part of this plan.
4. Preserve the exact source drawing and adult-confirmed story revision/hash throughout video generation. LTX prompts describe only the approved scene action and camera motion; visual guides may anchor required props/placement without changing the story.
5. Keep the old `SCRIPT_GENERATION_UNKNOWN` run immutable. Reconcile it using provider logs/metadata only. If its outcome cannot be proven, leave its lock and records intact and use a different synthetic profile/account for the new E2E.
6. The existing local/test video-candidate route is a technical preview path. Do not present it as quota-backed or production-ready. Its response must continue to say `product_playable=false` and `safety_validation=NOT_RUN`; the Parent UI must label the result as a private candidate preview.
7. Do not disable, lower, or bypass schema, subject confirmation, adult story confirmation, ownership, source-integrity, output validation, or safety gates. No direct database mutation or direct Modal inference outside the UI-triggered backend workflow.
8. No blind retry. Every repeat inference must follow a concrete, recorded defect and a code/configuration correction. Preserve call IDs, stage timings, bounded error codes, and hashes; never log raw prompt text, image bytes, access tokens, or child data.
9. Do not touch quota/payment state or change quota policy. Use only the already-scoped synthetic local candidate path. If an enforced admission gate blocks it, report the exact gate and do not bypass it.
10. Deploy only the task-required Modal app(s); do not warm/keep GPU containers idle. Stop task-used apps after the E2E and verify zero live tasks.
11. No commit or push.

## 4. Work plan

### M0 — Reconcile the ambiguous story request and validate the runtime (read-only)

- Confirm the exact run/revision/job state and active-owner lock through the normal database read path; do not print profile/account identifiers.
- Query Modal app logs for the language/audio story function around the recorded request time. Inspect only scratch-volume path names/metadata for the matching attempt; do not read request or model-output contents.
- Determine whether the failed `Function.spawn` call produced a provider call. If no provider call can be proven, retain the ambiguous state anyway; never replay the same attempt.
- Inspect the exact SRS §31.17/§31.22/§32 video requirements, the FEAT-081 candidate API and current API schema, Modal worker code, and available checkpoint manifest.
- Verify the emulator, Docker API/DB/MinIO/ClamAV, current Modal profile/environment, and available synthetic account/profile. Record starting state and costs/time evidence without exposing secrets.

### M1 — Repair Modal dispatch diagnostics without making unknown calls retryable

- Add explicit structured stage events around function resolution, scratch upload, `spawn`, call-reference validation, polling, and result collection for the story worker.
- Record safe exception class/module, elapsed time, request/job/generation/attempt IDs, and whether a provider call ID was obtained. Do not record exception messages, payloads, prompts, images, or credentials.
- Distinguish failures proven to occur before dispatch from ambiguous failures after dispatch. The ambiguous class remains non-retryable and keeps its lock until reconciled; only a proven pre-dispatch failure may use the existing explicit recovery contract.
- Add focused unit/contract coverage for both paths and preserve the existing worker error mapping.

### M2 — Install and verify the pinned LTX-2.5 Modal worker

- Port the reviewed, pinned FEAT-067 LTX-2.5 worker implementation into the FEAT-081 worktree without changing the source worktree. Preserve its model/code revisions, L40S profile, silent output, input hashes, output manifest, private scratch paths, and safety metadata.
- Implement the approved image-guide conditioning needed to keep a required scene prop in its story-approved location. Use LTX’s documented pixel-frame `ImageGuide` conditioning; retain the original child drawing as frame-zero `ImageReplace`. The guide may add a prop anchor, but may not redraw/replace the source or introduce a new story action.
- Verify Modal Secret/model access without displaying token values. If the exact checkpoint is absent, use the existing downloader to populate the named Modal Volume and verify its pinned manifest/checksums before GPU use. Do not store model weights in Docker.
- Deploy the video app and run CPU-only `/health`, model-manifest status, and runtime preflight before any video request. Confirm the exact function name `generate-silent-story-video` resolves from the backend’s Modal identity.
- Fix any deploy/import/runtime incompatibility revealed by these checks before sending inference.

### M3 — Enable the existing synthetic candidate route in the task Docker stack

- Enable the candidate capability only in the task’s local/test API container, with `synthetic_pilot_enabled=true` and `ai_provider=modal_dev`. Never change `.env.example` secrets or commit actual `.env` values.
- Rebuild/restart only the task API container with its existing Postgres and MinIO volumes. Run migration status and health checks; do not reset the database or seed duplicates.
- Confirm the candidate API rejects non-synthetic profiles and unconfirmed/stale stories, and that idempotency plus the one-active-candidate constraint remain in force.
- Confirm candidate status and private preview endpoints are mounted in OpenAPI and the Parent client uses those endpoints.

### M4 — Complete the UI path up to a confirmed story

- Use the Android emulator and the real Parent UI, not the visual preview harness.
- Keep the unknown run untouched. Use an existing distinct synthetic profile/account if available; otherwise create one synthetic test account/profile through the app’s normal registration/profile flow and remove only the account/profile created for this task after evidence capture when supported by normal authenticated cleanup APIs.
- Perform the real Parent path: profile/consent eligibility → optional topic or lesson → optional SVG guide → capture/upload synthetic drawing → live Qwen drawing understanding → adult subject/context confirmation → catalog-first activity choice/persistence → live Qwen story generation → adult confirmation of the exact story revision/hash.
- If the activity response is rejected after successful inference, inspect the bounded quality-gate diagnostic and worker contract. A concrete output-instruction mismatch may be repaired in the worker prompt/parser and covered by its focused contract test; keep all backend safety, quality, age, and ownership gates unchanged. Retry only from the existing UI after that code fix.
- If story generation fails, use worker call logs and the exact terminal code to identify and fix the cause. For a proven quality failure `STORY_OUTPUT_INVALID`, use only the SRS §6.1.1 adult-directed rewrite transition: preserve the failed revision, submit a fresh idempotency key from the UI, and revalidate unchanged drawing, subject, context and selected activity. Unknown outcomes and every other terminal failure remain non-retryable.

### M5 — Generate, persist, retrieve, and play one real silent video candidate

- Start candidate generation only from the confirmed story screen in the real Android UI. Preserve the exact confirmed story hash and the same source drawing hash.
- Poll the candidate endpoint through the UI; record upload, Modal call, model load, scene inference, assembly, output validation, and persistence durations/call IDs.
- Validate the returned MP4/container, video stream, dimensions/frame rate/duration, no audio stream, candidate manifest, and source/story hash lineage. Fail closed on any mismatch.
- Retrieve the private candidate using the authenticated preview endpoint and play it in the Android Parent UI. Do not expose public URLs or mark the candidate product-ready.
- Review the video against the drawing and confirmed storyboard. If a required prop/action is missing or the source drawing is not recognizably preserved, diagnose the specific cause and adjust guide/prompt/conditioning before another bounded inference.

### M6 — Evidence and cleanup

- Store the plan-linked run report, sanitized API/Modal logs, call IDs and timings, hashes, API status summary, MP4 validation metadata, screenshots of the real story confirmation/loading/video playback, and visual review under `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/`.
- Record known boundary: a private candidate with `safety_validation=NOT_RUN` is not product acceptance or production playback readiness.
- Stop only Modal apps used by this task, confirm zero tasks, and leave shared model/scratch volumes and unrelated Docker projects intact.
- Update FEAT-081 `CONTEXT.md`, `status/STATUS.md`, and the evidence index with results, limitations, and remaining blockers.

## 5. Acceptance criteria

1. The old ambiguous StoryRun is not replayed, manually edited, or silently released from its active-owner lock.
2. Dispatch logs identify a safe stage and exception class for any new failure, while ambiguous post-dispatch results remain non-retryable.
3. The pinned LTX-2.5 worker is deployed, its health/model manifest/runtime are verified, and the backend resolves the exact Modal function name.
4. A real Android UI Parent flow reaches a persisted, adult-confirmed story with a live AI drawing analysis and a persisted activity selection; no fixtures or direct inference calls are used.
5. The UI-triggered backend request produces a valid silent LTX-2.5 MP4 candidate derived from the same confirmed drawing/story; authenticated preview playback succeeds in the Android UI.
6. Candidate metadata continues to state `product_playable=false` and `safety_validation=NOT_RUN`; no product-readiness claim is made.
7. Evidence is reproducible, sanitized, stored in the FEAT-081 evidence folder, and task-used Modal apps end with zero live tasks.

## 6. Allowed files

- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/CONTEXT.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/**`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/infrastructure/ai/modal_silent_story_video.py`
- `backend/src/sketch2life/application/services/parent_video_candidate_service.py`
- `backend/src/sketch2life/application/ports/parent_video_candidates.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_video_candidate_repository.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_video_candidates.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/tests/unit/test_modal_story_function_client.py`
- `backend/tests/unit/test_parent_video_candidate_service.py`
- `backend/tests/contract/test_parent_video_candidate_api.py`
- `deployment/modal/srs_v23/video_app.py`
- `deployment/modal/srs_v23/contracts.py`
- `deployment/modal/srs_v23/workloads.json`
- `deployment/modal/srs_v23/story_image_guides.py`
- `deployment/modal/srs_v23/story_visual_plan.py`
- `deployment/modal/srs_v23/tests/test_silent_story_contract.py`
- `deployment/modal/srs_v23/tests/test_silent_video_prompt.py`
- `deployment/modal/srs_v23/tests/test_video_app_contract.py`
- `deployment/modal/srs_v23/tests/test_story_image_guides.py`
- `deployment/modal/srs_v23/tests/test_story_visual_plan.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `deployment/modal/srs_v23/worker_observability.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `backend/tests/unit/test_parent_activity_worker_contract.py`
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/tests/unit/test_parent_activity_suggestions.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts`
- `apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts`
- `apps/ui-mobile/src/parent/application/use-cases/ParentPlatformUseCases.ts`
- `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/components/ParentAiLoadingState.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx`
- `apps/ui-mobile/tests/videoCandidateProgress.test.ts`
- `apps/ui-mobile/tests/parentSrsBehavior.test.ts`
- `compose.yaml`

Any additional file needed to fix a concrete defect must be added to this allowlist before it is edited, with its reason recorded in the plan’s execution log.

## 8. M0 execution log — source-dependent files added before implementation

- **2026-11-21:** Read-only source review found the reviewed LTX app depends on the shared worker contract/workload registry and two deterministic visual-guide modules; none of the latter two are present in FEAT-081. It also found the actual Parent screen name is `VideoCandidateScreen.tsx`, not `VideoScreen.tsx`. These exact dependencies were added to §6 before any implementation. The current working plan therefore includes the complete file paths needed for the video worker and UI; no source files have been edited under Rev58 yet.

## M5 UI-state correction — distinguish reconciliation from active inference

- **2026-11-21 observation:** The emulator displayed `SCRIPT_GENERATION_UNKNOWN` as “Máy chủ đang tạo câu chuyện”, with an animated spinner and a `00:14` elapsed timer. The timer starts when `ParentAiLoadingState` mounts, so it resets on screen reopen and does not measure Modal execution. The UI therefore implies live inference even though the run is in reconciliation and must not be resubmitted.
- **Provider history check:** Modal `function calls` for `sketch2life-srs23-language-audio-dev/generate-story-and-storyboard` returned zero calls in `2026-11-21T09:10:00Z`–`09:20:00Z`, the backend dispatch window. The 24-hour listing contained three calls at later times, none in this window. The backend still lacks a durable provider call ID for this attempt. Per §3.5 and SRS reconciliation rules, retain the run as unknown; this read-only result does not authorize replay or release of its active-owner lock.
- **Authorized UI repair:** distinguish `SCRIPT_GENERATION_UNKNOWN`/`AWAITING_RECONCILIATION` from a known active `SCRIPT_GENERATING` request. Show a static reconciliation status, explain that Modal acceptance/result is unconfirmed, hide the local mount-relative timer and active spinner, and keep all duplicate-request actions blocked. Keep the existing spinner only for confirmed in-progress work. Do not change backend state, unlock the run, submit any AI/video request, or alter safety/ownership gates.
- **Files added to §6 before editing:** `ParentExpoApp.tsx`, `StoryScreen.tsx`, `ParentAiLoadingState.tsx`, and `parentSrsBehavior.test.ts`; the existing loading component is reused only for this truthful state distinction. Run focused mobile typecheck/test checks after the change. No Modal deployment or inference is part of this correction.

## M4 activity-output correction — remove model-generated prose from deterministic fields

- **2026-11-21 live evidence:** two UI-triggered Qwen3.5 fallback calls (`fc-01M7ZB7X1Z1T4E6FEZP3WCXPXB`, `fc-01M7ZBBSZ28N0QTHJDM71JK2T1`) reached the worker and completed in 91,891 ms and 39,262 ms. Both produced the same safe diagnostic: `fallback_activities[0].objective`, 47 characters, `dangling_word`; 827 output tokens, 1,400-token cap not reached. The raw generated sentence is deliberately not persisted or logged. A second request without a contract/prompt change reproduced the same failure.
- **Source review:** the model is required to invent complete short Vietnamese sentences for `objective`, `preparation_text`, and `safety_notes`; the worker and backend then independently parse the same fields for terminal punctuation and dangling tails. The SRS requires useful activity objectives, preparation, safety, selection and adult review, but does not require the model to author those specific prose fields. Instructions are already rendered deterministically after model markers.
- **Authorized repair:** change only the internal Modal worker contract so Qwen returns position-specific markers for objective, preparation and safety fields. Render those three user-facing fields from bounded Vietnamese templates keyed to the fixed activity type/order and confirmed subject. Keep the public Parent API response schema unchanged. Leave the backend quality gate, sentence-completeness checks for rendered output, outdoor/Montessori/child-agency/adult-support checks, safety markers, age/topic/context/candidate matching, uniqueness, unsafe-action/PII checks, exactly-three fallback rule and catalog-first behavior unchanged.
- **Files added to §6 before editing:** `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`; `language_audio_app.py` and `backend/tests/unit/test_parent_activity_worker_contract.py` are already allowlisted. Add regression coverage for every marker-to-template mapping, maximum lengths, and rejection of wrong/missing markers.
- **Retest:** run focused Modal worker and backend activity-contract tests; deploy only the language/audio Modal app; check CPU readiness without model warm-up; then allow at most one new fallback request from the real Android UI on this unchanged synthetic run. No direct worker/API inference, retry loop, or safety/quality-gate bypass. If another field fails, stop and use its safe field/reason diagnostics before any further inference.

## M4.1 parser resilience — distinguish Vietnamese homographs and reject duplicate keys

- **Observed:** the same sentence-tail heuristic in the Modal worker and backend folds away Vietnamese diacritics before comparing its final word. That conflates valid topic nouns such as `lá`, `chó`, `voi`, and `đó` with incomplete function words `là`, `cho`, `với`, and `do`, so valid child-subject text can be rejected as incomplete. The Parent activity JSON parser also uses default `json.loads`, which silently accepts duplicate object keys and keeps the last value.
- **Authorized repair:** normalize Vietnamese text to NFC and compare grammatical tail words/phrases with diacritics preserved; retain the existing punctuation, clipped-consonant, and known incomplete-phrase checks. Add duplicate-key rejection to the Parent activity model-output parser, mapping it to the existing safe invalid-JSON worker error. Do not relax catalog, age, context, Montessori, safety, PII, uniqueness, output-shape, or adult-review checks.
- **Files added to §6 before editing:** `backend/src/sketch2life/application/services/parent_activity_suggestions.py` and `backend/tests/unit/test_parent_activity_suggestions.py`. The Modal source and contract test are already allowlisted above.
- **Regression coverage:** valid sentence endings containing `lá`, `chó`, `voi`, and `đó` must pass in both worker and backend; known dangling endings such as `là`, `cho`, `với`, and `do` plus existing incomplete phrases must remain rejected. Duplicate keys at the root and within nested activity objects must fail closed without including raw model text in errors or logs.
- **Verification:** run the focused Modal activity parser tests, backend activity worker contract, and backend activity quality-gate suite. After these pass, continue the single approved UI-triggered fallback inference under Addendum 115; do not add inference retries or weaken a gate.

## 9. M4 execution amendment — Parent activity safety-note output contract

- **2026-11-21:** The real Parent UI dispatched `parent.activity.suggest` to Qwen3.5 successfully (804 output tokens; Modal call `fc-01M7Z0SE2RYWJAQTJAM2K5E6HS`). The backend rejected the three fallback activities with `SAFETY_NOTE_MISSING`; no activity was persisted. Source review found the worker prompt only bounded `safety_notes` to 53 characters while the unchanged backend gate requires an explicit recognized precaution marker (`không`, `tránh`, `an toàn`, `giám sát`, or `đảm bảo`). This is a concrete prompt/quality-contract mismatch, not a reason to weaken the gate.
- **Allowed before edit:** add only `deployment/modal/srs_v23/language_audio_app.py` and `backend/tests/unit/test_parent_activity_worker_contract.py` to §6. The repair must instruct safety notes to state a topic-appropriate precaution using an explicit marker, preserve the current response schema/parser and all backend safety/quality gates, and add focused prompt-contract coverage. No gate relaxation or unrelated worker change is authorized.
- **Retry condition:** after focused tests pass and the language/audio app is redeployed, retry the existing Parent activity suggestion once from the real Android UI. Do not call the worker directly or repeat inference before the repair.
- **2026-11-21 follow-up:** that single UI retry reached the pinned Qwen3.5 model and completed inference, but the worker parser rejected `fallback_activities[0].safety_notes` as `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` / `dangling_word` (794 tokens, 88,846 ms). No activity was persisted. This is a concrete output-completeness defect, not a timeout. A second prompt repair may tighten the safety-note body target to 40 characters (the schema's 52-character ceiling remains unchanged), retain the explicit precaution-marker requirement, and add a regression assertion. After offline tests and redeployment pass, one new UI-triggered activity inference is authorized for this diagnosed defect. Do not request the inference again without this code correction.
- **2026-11-21 follow-up:** the next UI call reached Qwen3.5 and completed 888 output tokens in 139,489 ms, then failed at `output_parse_and_contract_validation`: `fallback_activities[0].objective` was rejected as `terminator_invalid`; no activity was persisted. The LMFE contract already requires an external ASCII period in `terminator`, while model prose can also place terminal punctuation in `body`. A narrow worker normalization may strip only terminal sentence punctuation from `body` when `terminator == "."`, then append exactly one period; it must still reject a wrong terminator, empty body, dangling sentence, unsafe note, or any backend-gate failure. Add parser regression coverage and allow one new UI attempt after focused tests and redeployment. Do not retry without this correction.
- **2026-11-21 story outcome:** the UI-triggered `story.generate` call `fc-01M7Z27C3S4QATFJZGHCCZ45TP` reached Qwen3.5-9B and ended with worker event `STORY_TEXT_INCOMPLETE`; safe diagnostics identify only `scenes[4].action` as incomplete (body length 57/60, model EOS allowed, token limit not reached). The Modal app log proves a terminal `worker_failed` event, and the backend returned `STORY_OUTPUT_INVALID`; this is not an unknown outcome or a timeout. The app now exposes the exact Rev73 UI rewrite action with three rewrites remaining. Before that adult action, a prompt-only correction may narrow action-body target to 24–40 characters (schema ceiling remains 60), and the story contract suite must assert the target while preserving five scenes, all schemas and quality gates. Add `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py` to §6 before editing. After tests and redeployment, use the approved UI rewrite with a fresh key; preserve the failed revision and all run inputs. No direct API/worker call or replay.

## 7. Explicit exclusions

- No product quota/payment implementation, billing mutation, or quota bypass.
- No production safety/admission relaxation, public asset promotion, public playback, or claim that this technical preview is `VIDEO_READY`.
- No change to LTX model/GPU class, no Wan substitution, no audio/narration, and no real-child media.
- No blind retry, parallel GPU dispatch, direct database mutation, or replay of an outcome-unknown request.
- No commit or push.

## M4 execution amendment — shorten all generated sentence targets after rewrite rejection

- **2026-11-21:** The first adult-directed rewrite from the real Android UI was dispatched once with a fresh key and completed Qwen3.5 inference (`fc-01M7Z301MEVNSV4T796KZZAPCG`, 931 tokens, 76,397 ms). The worker completed JSON parsing and rejected only `scenes[2].narration` as `STORY_TEXT_INCOMPLETE` (49 characters; model EOS allowed; token ceiling not reached). Backend returned the deterministic `STORY_OUTPUT_INVALID` quality result. The UI remains on the same-run adult rewrite recovery screen; prior failed revisions remain immutable.
- **Concrete cause:** story prompt targets still permit long prose for story sections and narration, and the first incomplete scene action repair did not constrain these fields. This is an output-instruction issue; no evidence indicates dispatch timeout, token truncation, or a failed safety check.
- **Authorized before edit:** only the existing allowlisted `deployment/modal/srs_v23/language_audio_app.py` and `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py` may change for this repair. Keep parser/schema ceilings, five-scene contract, sentence-completeness validation, subject/activity/context checks, all safety/ownership gates, and adult review unchanged.
- **Repair:** make all prose targets concise and completion-oriented: story section sentence bodies 35–50 characters, scene action bodies 20–32, and scene narration bodies 20–35; retain existing schema maxima. Prompt each as one simple complete Vietnamese sentence with an explicit external terminator, one main clause, and no trailing conjunction. Add focused prompt-contract assertions for every target. Do not loosen or bypass any validator.
- **Retest:** run the focused story-worker test suite with the Modal virtualenv, redeploy only `sketch2life-srs23-language-audio-dev`, verify readiness, then send at most one additional adult-directed rewrite from the real UI with a fresh key after confirming the run is still eligible and drawing/subject/context/activity hashes are unchanged. Do not replay either previous call or use direct API/worker inference.
- **Conditional video:** only if this rewrite produces a valid revision, the adult reviews and confirms its exact current hash, and existing consent/admission/ownership/safety checks pass, continue to the already-approved single silent video candidate. No quota/payment calls or bypass; candidate stays private with `product_playable=false` and `safety_validation=NOT_RUN`.
- **Stop conditions:** unknown outcome, non-`STORY_OUTPUT_INVALID` failure, changed input hash, exhausted three-rewrite SRS cap, or any safety/consent/admission issue. No database edits, new account/profile/run, gate weakening, direct inference, unrelated service shutdown, commit, or push.

## M5 execution amendment — recover the verified LTX output rejected by a redundant metadata contract

- **Owner authorization:** the owner’s direct instruction to continue fixing concrete defects until the video runs authorizes this diagnosis-guided repair. This amendment preserves the one video inference already submitted; it authorizes no second GPU generation.
- **Observed result:** Android displayed `VIDEO_WORKER_OUTPUT_INVALID` after the Modal call `fc-01M7Z3S0AAJ89HCJ6Q8CM2STT0` completed all five LTX-2.5 scene inferences, silent assembly, and worker-side MP4 validation in 474,757 ms. The successful output is still bound to the same job/generation/attempt and stored in the task’s Modal scratch volume.
- **Root cause:** `video_app.py` writes `width`, `height`, `fps`, and `video_codec` to the SHA-256-bound output manifest but omits those four redundant fields from `_build_silent_story_output_payload`. The backend currently requires each value in both the worker result and manifest, so it rejects an otherwise complete output. This is a worker/backend contract mismatch, not an LTX inference or media-render failure.
- **Authorized files:** the existing Rev58 allowlist plus `backend/src/sketch2life/application/ports/parent_video_candidates.py` and `backend/src/sketch2life/infrastructure/persistence/parent_video_candidate_repository.py`; these are needed to define and implement one guarded, owner-scoped recovery transition through the normal authenticated status route.
- **Repair:** (1) include the four validated media fields in future worker result JSON and add a worker-contract regression test; (2) have backend validation use the hash-verified manifest as the canonical source for these redundant media fields only when a worker result omits them, while rejecting any supplied value that disagrees; keep MP4 size/hash, manifest hash, model/checkpoint/code pin, source/story lineage, dimensions, frame rate, duration, codec, zero-audio, private-candidate, and safety metadata checks intact; (3) on the authenticated current-status path, permit exactly one recovery of this run’s existing `FAILED` record only when its error is `VIDEO_WORKER_OUTPUT_INVALID`, the saved Modal call/attempt references exist, and no recovery marker exists. Mark it as recovery-in-progress before reading the same completed call; revalidate the same bytes/manifest, persist to the existing private candidate asset reference, and transition through the repository to `CANDIDATE_READY`. Preserve a sanitized recovery provenance marker. If revalidation fails, set a distinct terminal recovery failure so polling cannot loop. Do not modify DB directly, create another candidate/run/attempt, redispatch inference, or change any safety/admission gate.
- **Verification:** add focused regression tests for worker result completeness, manifest-only compatibility, rejection of mismatched media metadata, and the one-shot repository/service recovery guard. Run those tests, deploy the corrected video worker without invoking its generation function, rebuild only the task API, and use Android’s existing status polling to recover and play the already-produced MP4 through the authenticated private preview. Record the same-call lineage and final media validation.
- **Stop conditions:** if call IDs or hashes do not match, the scratch output cannot be read, manifest/output integrity fails, any hard gate fails, or the one-shot recovery is already marked/consumed, leave the candidate failed and stop; do not generate another video under this amendment.

## M5 execution amendment — load the root environment into the task API

- **2026-11-21 observation:** the existing Android seed account authenticated with Firebase, but the task API returned `503 IDENTITY_PROVIDER_UNAVAILABLE` from `/api/auth/v1/me`. Safe inspection of `s2l-feat081-rev23-api-1` showed `auth_provider=development`, no Firebase project or Admin credential, and `ai_provider=disabled`. The Compose project was launched with working directory `.codex-worktrees/fe`, so Compose did not discover the single root `<local-machine-path> The root environment already contains the Firebase and Modal development configuration; it is not missing from the user's setup.
- **Authorized operational repair:** recreate only `s2l-feat081-rev23-api-1` from the same worktree Compose files while explicitly passing `--env-file <local-machine-path> Keep the existing project name, ports, Postgres/MinIO/ClamAV containers, volumes, and task data. Do not edit or print `.env`; do not run migrations, seed accounts, modify profiles, issue a new AI/video request, or change quota/payment settings.
- **Verification:** confirm from inside the API container only non-secret facts: Firebase provider is selected, project is configured, Admin credentials are present without printing them, Modal dev provider is selected, and Firebase Admin initializes. Then verify API health, sign into the same existing synthetic account in Android, and let the authenticated Parent UI status refresh recover the exact saved video call authorized by Addendum 112. No new inference is allowed.
- **Additional files:** no source files are added to the allowlist. This amendment changes only the task container's runtime configuration and feature-local evidence/status records.
- **Stop conditions:** if Firebase Admin initialization fails, run/profile ownership differs, the candidate/call/hash differs, or the recovery marker is absent/consumed, stop without creating an account/run or sending another request.

## M5 execution result — existing seed account does not own the saved candidate

- **2026-11-21 21:13 +07:** Addendum 113's API runtime repair succeeded. Only the task API was recreated using the root `.env`; Firebase Admin initialized, `/health` returned 200, and Android signed into the existing seed Parent account.
- The account-scoped profile list included `SyntheticRev58Turtle`, but its Android Story History was empty. A read-only DB comparison found the existing target run `e54a3543-ccab-4c3b-8a19-51aca314cd46` is owned by a different Firebase principal and does not reference that seed account's `SyntheticRev58Turtle` profile. The exact video candidate was therefore not reachable through this authenticated UI. The separate pending `SyntheticTurtleRev22` run was left untouched.
- A follow-up read-only Firebase Admin lookup confirmed the target profile owner still maps to an enabled Firebase Auth account with an email/password provider. No identifier or credential was recorded, and no Firebase account state was changed.
- After the owner selected the existing-account path, a redacted comparison confirmed the Parent email in root `.env` still maps to a different Firebase Auth user. Both credential fields are present; no sign-in attempt or credential disclosure occurred.
- After the owner directed continuation using the currently logged-in account, the real Home card and `Tiếp tục` UI opened its active run `b05c2b46-e760-4643-824b-b30b5387453f`. A read-only DB check confirmed `SCRIPT_GENERATION_UNKNOWN` / `AWAITING_RECONCILIATION`, `STORY_OUTCOME_UNKNOWN`, `retryable=false`, and no provider job ID; last update was 2026-11-21 16:13:47 +07. The UI explicitly prohibited resubmission, and a status-only wait left it unchanged. This active-owner lock prevents a new session on the same Parent account. No retry, cancellation, new run, direct DB edit, AI request, or video request occurred.
- **Stop condition invoked:** no recovery/status call was made for the target candidate, no account/run was created, no AI/video inference was sent, and no quota was accessed. Evidence: `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/M5_ACCOUNT_SCOPE_CHECK.md`, screenshots/XML `57_target_home` and `58_target_history`.
- Resume only after the existing account that owns the candidate is available through the root seed configuration, or after a separately approved new run/video inference. Modal inventory at this checkpoint: drawing app deployed with 0 tasks, language/audio app stopped, expected video-candidate app not found in `dev`; no live GPU task listed. The old call was not fetched.


## Addendum 117 — prevent accepted truncated activity text and harden AI JSON parsing

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction to check content and parsers across the system and fix avoidable AI errors.
- **Observed live result:** the one approved Parent UI activity request completed successfully with HTTP 200, three fallback activities, Qwen3.5-9B, and 104.515 seconds end-to-end. Review of its accessibility output found a materials field cut at the worker's 60-character constrained-schema ceiling; the parser accepted the incomplete value. This is a content defect after successful inference, not a timeout. The raw model response is not retained or added to logs/evidence.
- **Additional parser findings:** Parent topic-subject JSON parsers use default `json.loads`, which silently accepts duplicate object keys; the backend builds worker candidate context by coercing and slicing catalog fields, which can cut a long field mid-word and weaken ranking context.
- **Authorized files:** `deployment/modal/srs_v23/language_audio_app.py`; `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`; `deployment/modal/srs_v23/tests/test_parent_topic_subjects_contract.py`; `backend/src/sketch2life/application/services/parent_activity_suggestions.py`; `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`; `backend/tests/unit/test_parent_activity_suggestions.py`; `backend/tests/unit/test_parent_activity_worker_contract.py`; and this feature's plan, approval, status, context, and evidence records.
- **Repair:** make all user-visible Parent activity-fallback text fields complete and semantically aligned by using strict internal marker values and bounded worker-rendered Vietnamese templates for title, objective, materials, preparation, instructions, observation, and safety. Preserve the external API schema. Do not accept free-form text truncated at a constrained decoder limit. Use one duplicate-key rejecting JSON hook in Parent topic-subject parsers. For backend catalog context, require validated strings and create bounded word-boundary excerpts only when Modal input limits require them; preserve the source lesson unchanged and emit only a sanitized truncation count. Keep topic, subject, age, catalog, Montessori, privacy, uniqueness, hard-safety, and adult-review gates unchanged.
- **System parser audit:** inspect the current Modal and backend output-contract paths for drawing/VLM, topic suggestions, SVG guide, lesson/Teacher guide, Parent activity, story, and silent video. Run available offline parser/contract tests for the audited paths. Record verified behavior and remaining gaps; change only code with a concrete reproducible defect, within the allowlist above. No raw model text, image, tokens, child data, or credentials in logs/evidence.
- **Verification:** run the focused Parent activity/topic suites and the available offline output-contract suites for the other audited AI paths; run Python compile checks; rebuild/recreate only the task API if the backend change requires it; deploy only `sketch2life-srs23-language-audio-dev` after offline tests and verify CPU readiness. Do not send another inference: the one approved UI activity inference has already been consumed. Preserve the current real UI result and record its call ID, safe phase diagnostics, duration, and content defect in feature-local evidence.
- **Limits:** no gate bypass or weakening, no new account/profile/run, no direct API/worker inference, no replay/retry, no story/video generation under this amendment, no quota/payment access, no migration, no unrelated service shutdown, no commit/push.
## Addendum 117 test-scope clarification — video output metadata regression

- The static system audit found one failing video contract test: its `final_details` fixture provides only duration/audio count, while the current silent-video payload contract correctly requires width, height, FPS, and codec as well. This is a stale test fixture; no video inference was performed and no production video code change is authorized by this finding.
- Add `deployment/modal/srs_v23/tests/test_silent_story_contract.py` to the allowlist solely to align that fixture with the current output contract. The existing video hard gates and payload validation remain unchanged.
- Run Windows pytest with a short explicit `--basetemp` because the default shared temp directory currently overflows during parallel test collection.
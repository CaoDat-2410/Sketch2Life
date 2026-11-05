# EV-063-42 - AI flow SRS alignment and Teacher deck POC

**Date:** 2026-11-04 (Asia/Saigon)
**Status:** PARTIAL. Local schema/business-rule implementation and API verification completed; one Parent story worker call failed before inference, and the FLUX visual call did not produce an image.
**Canonical product source:** FEAT-063 SRS v2.3-draft, especially Parent order in ??4/31.4, Story in ??6.2/6.2.2, Teacher Sketch Deck and lesson visuals in ??6.2.1/31.4, and BR-13/BR-55/BR-53.

## Scope and guardrails

- Synthetic butterfly artwork and synthetic approved lesson fixture only; no real child or lesson data.
- No video generation, publication, quota charge, Whisper, TTS, or downstream video pipeline call.
- Parent activities were not selected because the SRS places them after playable video. This run did not produce a video.
- The SRS was not changed. Every output remains a draft. Modal model Volumes were preserved.
- One inference per workload; no automatic or manual retry after an unknown/failed call.

## Implementation changes

1. Added a versioned Parent story contract with adult-confirmed subject, exact age 36-120 months, visible drawing anchors, context and artwork lineage, Vietnamese output, 5-15 ordered scenes, 30-90 seconds total duration, contiguous scene timing, per-scene narration/visual prompts/character anchors, and immutable draft revisions.
2. Enforced Parent business rules: no activity preselection, no lesson/roster fields, exact age required, subject confirmation required, optimistic revision checks, one initial draft plus at most three AI rewrites, and no hand-edited scene endpoint. A story must be confirmed by an adult before downstream video admission.
3. Added a known butterfly lifecycle check to reject the previously observed egg-to-adult and nest-seeking errors. This narrow guard is not a general factuality guarantee.
4. Corrected the Modal story manifest version. Drawing analysis uses `sketch2life.modal.drawing-input.v1`; story generation uses the language worker's `sketch2life.modal.ai-request.v1`. The story adapter now maps known worker contract/output/fact-check failures and Modal `RemoteError` to terminal failures instead of reporting them as unknown. The original live call was not retried.
5. Added the Teacher Sketch Deck direct Modal candidate from a reviewed, synthetic plan. Its structured outline is a 16:9 draft, uses four progressive drawing steps, and references only the two approved activities. Added a local HTML preview. No Teacher HTTP endpoint or publication behavior was added.

## Live run and AI results

### Parent synthetic artwork flow

- Run: `c0ce11e9-cd7d-4743-9bf0-5f1dfc1fbb90`; image SHA-256 `c16930354d637199b97d744de16c62bfc4f0ee97c34a23751e27912d968c6949` (1,775,882 bytes).
- Parent workflow elapsed from 12:23:32 to 12:42:49 Asia/Saigon (19m17s, including bounded provider waits). Upload create/part/complete/readiness and image attachment succeeded. The drawing VLM took 47.262s at Modal and identified ?butterfly?; its confidence was `0.0` in the legacy DTO. The adult confirmation gate was used; the result was not auto-confirmed.
- Story revision API returned HTTP 202 / `STORY_OUTCOME_UNKNOWN` after 102.634s. The Modal worker rejected the manifest with `MODAL_SCHEMA_UNSUPPORTED` before model inference because the drawing manifest schema had been reused for story input. No story was generated; the revision and run remain `AWAITING_RECONCILIATION`.
- The local adapter now sends the expected language-worker schema and has unit coverage for schema and terminal-error mapping. It was not redeployed or live-retried under the one-call plan. A corrected live story result is therefore **not verified**.

### Teacher slide/deck POC

- Qwen2.5-7B-Instruct returned a structured 5-slide draft in 57.937s (`fc-01M6JGT64YRSBAF5BGHSV97A0N`): orientation, drawing guide (4 steps), subject exploration, and 2 approved-activity slides. Output was Vietnamese, 16:9, `DRAFT`, and `review_required=true`; the slide activity references exactly match the approved input fixture.
- FLUX visual call `fc-01M6JGVYR9G8DD2MD3HCRC4N54` waited 468.339s while Modal reported no L4 capacity. It produced no image and was not retried. The HTML preview is text-only, has no generated visual, is non-publishable, and does not demonstrate a complete visual slide.
- This is a direct worker POC, not an HTTP Teacher Deck API or a saved/presented school session.

### Timing summary

| Stage | Result | Duration |
|---|---|---:|
| Drawing VLM | Completed on synthetic artwork | 47.262s worker time |
| Parent story API/worker | Terminal worker contract failure, reported by pre-fix adapter as unknown | 102.634s request wait |
| Teacher deck text | Draft generated | 57.937s worker time |
| Teacher FLUX visual | No GPU capacity; no image | 468.339s wait |
| Parent end-to-end simulation | Stopped before video and post-video activities | 19m17s wall time |

## HTTP API verification

The StoryRun-lite harness recorded 28 HTTP requests. All 13 mounted operations were exercised at least once. Success/error codes below are actual results; `409` and `422` business-rule cases are expected unless explicitly marked otherwise.

| Method and route | Observed result | Assessment |
|---|---|---|
| `POST /v1/story-runs` | `201`; missing age/invalid profile `422`; existing active run `409 ACTIVE_RUN_EXISTS` | Working; validation and BR-02 behaved as designed |
| `GET /v1/story-runs/{run_ref}` | `200` | Working |
| `POST /v1/story-runs/{run_ref}/assets` | `202`; run later reached `SUBJECT_REVIEW` | Working; VLM completed |
| `POST /v1/story-runs/{run_ref}/subject-confirmation` | `202` | Working; adult confirmation required |
| `POST /v1/story-runs/{run_ref}/story-revisions` | `202 STORY_OUTCOME_UNKNOWN`; worker rejected schema; run remains held | **Not working end-to-end in the live build.** Local adapter fix is not live-retested. |
| `GET /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}` | `200` | Working; returns held revision |
| `POST /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation` | `409 STALE_REVISION` | Expected rejection because there was no valid `DRAFT`; successful confirmation path remains unverified |
| `POST /v1/story-runs/{run_ref}/cancel` | `202` | Working |
| `POST /v1/upload-sessions` | `201` | Working |
| `PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}` | `200` | Working |
| `POST /v1/upload-sessions/{upload_ref}/complete` | `202`; subsequent read reached `READY` | Working |
| `GET /v1/upload-sessions/{upload_ref}` | `200` | Working |
| `DELETE /v1/upload-sessions/{upload_ref}` | `202` | Working |

Additional boundary results:

- `GET /health` and `GET /openapi.json` returned `404` in the isolated StoryRun-lite harness; those routes are intentionally not mounted by this harness. This is not classified as a product API failure.
- The isolated StoryRun-lite router has no Teacher Deck HTTP endpoint and no integrated Parent post-video activity-list/selection endpoint. Deck work was called directly on Modal. The activity step was not reached because there was no playable video.
- A separate actor scope confirmed cancel and upload-abort operations without dispatching AI. The original Parent run was preserved when BR-02 returned `409` for a second unfinished run.

## Workload registry alignment

`deployment/modal/srs_v23/workloads.json` now records the observed outcomes for `drawing.analyze`, the combined `story.generate` / `storyboard.generate` path, `teacher.sketch-deck.generate`, and `lesson.visual.generate`. Every entry remains `enabled: false`. Parent Sketch Guide, drawing segmentation/SAM2, ASR/TTS, video, and lesson-plan suggestion were not invoked by this task and remain separately gated; the older Parent line-guide feasibility result remains a prior synthetic POC, not proof of this Teacher visual flow.

## Verification

- Focused Python 3.12 suite in a disposable container: **92 passed, 3 skipped**. The skipped cases require the verified task-owned PostgreSQL URL, which was not present in this test container.
- The live HTTP POC used the verified task-owned PostgreSQL database migrated through `20261104_story_revisions`; the disposable test container did not inherit its connection URL.
- Ruff on changed Python files: passed.
- `compileall` on story contracts and Modal story/deck/FLUX source: passed.
- `git diff --check`: passed (Git printed only existing CRLF-normalization notices).
- Live HTTP trace and worker outputs: `assets/ai_flow_srs_alignment_20261104/poc_run_trace.json`, `teacher_deck_output.json`, and `api_mutation_results.json`.

## Shutdown and remaining work

- Modal drawing VLM, language/audio, and FLUX dev apps are all `stopped` with `0` tasks. The prior duplicate language/audio app record is also stopped. Stop times are recorded by Modal on 2026-11-04.
- Both shared Modal Volumes remain present: job scratch and pinned model weights. No app or volume was deleted.
- Task-local ports 8002 and 5433 have no listeners. Existing shared Docker API/PostgreSQL/Redis/ClamAV containers remain untouched.
- Do not retry story or FLUX under this plan. A new approved live inference is required to verify the corrected story schema and to obtain a visual slide. The Parent positive script-confirmation path, post-video activity integration, and Teacher Deck HTTP/session API remain unverified or unimplemented in this slice.

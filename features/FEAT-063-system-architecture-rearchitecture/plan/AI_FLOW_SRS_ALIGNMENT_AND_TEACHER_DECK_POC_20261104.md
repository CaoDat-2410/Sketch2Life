# FEAT-063 AI flow SRS alignment and Teacher deck POC

**Status:** APPROVED / IN PROGRESS
**Date:** 2026-11-04
**Canonical product source:** `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft, §§4, 6.2, 6.2.1–6.2.2, 7.2, 7.4, 21, 31.4–31.5, BR-13–15, BR-47, BR-53–57, FR-PL-12–19, FR-AI-02/04/07, AC-50–55.
**Approver:** Product owner, by direct instruction in this conversation to detail and correct AI flows, fix story-generation/schema/business-rule errors, try the documented slide flow, test APIs, report failures, and stop the apps afterward.
**Approval timestamp:** 2026-11-04, Asia/Saigon.
**Plan approval SHA-256:** recorded in `approvals/TASK_APPROVAL.md` before implementation.

## Goal

Bring the executable synthetic Parent story-draft path closer to the current FEAT-063 SRS and demonstrate the separate Teacher AI Sketch Deck flow using synthetic, reviewed lesson data. Preserve existing source artwork and provider provenance. All generated stories/decks remain drafts; this task does not call video generation or publish content.

## Findings that define the work

- `deployment/modal/srs_v23/language_audio_app.py::generate_story_and_storyboard` accepts only `{topic, language, scene_count}`, hardcodes `bướm` and exactly five scenes, and returns a reduced schema that omits duration, image/video prompt, timing, and character anchors.
- The last synthetic butterfly output contained incorrect lifecycle facts (the adult butterfly appeared to hatch from the egg and seek a nest); no factual guard rejected it.
- The isolated StoryRun-lite Parent API confirms a subject but has no story-revision generation or script-review endpoint and no `story.story_revisions` / `story.story_scenes` persistence.
- `teacher.sketch-deck.generate` is registered as a candidate but has no Modal handler or Teacher HTTP endpoint. SRS §6.2.1 defines a 16:9 in-session web deck, not a PowerPoint export.

## Approved scope

1. Add strict, versioned story input/output contracts that carry only adult-confirmed subject, bounded visible drawing anchors, adult-confirmed idea/transcript when present, exact age in months, context/input hashes, and role-specific optional lesson direction. Parent requests must not carry pre-video activity selection or Teacher roster/occurrence data. Teacher input, if exercised, must pin a reviewed plan and only its approved activity data.
2. Replace the fixed-topic/fixed-five-scene worker behavior with bounded SRS story/storyboard generation: Vietnamese, 5–15 ordered scenes, 30–90 seconds total, scene action, visual prompt, narration, timing, and character anchors. Validate schema and invariants fail-closed. Keep a known-facts guard for the synthetic butterfly sample; outputs remain an adult-review draft and the model is not represented as a general factual validator.
3. Add an additive StoryRun-lite API/persistence slice for Parent story revisions and script confirmation, enforcing the confirmed subject/input revision, optimistic version, idempotency, one initial draft plus at most three AI rewrites, immutable revisions, and no hand-edited scene endpoint. Record schema/prompt/model revisions and lineage hashes. Do not add video admission or alter existing SRS product quotas in this slice.
4. Implement a private Modal Teacher Sketch Deck candidate from a synthetic approved plan: structured 16:9 slide outline, 3–5 progressive sketch steps, and concise explanation of each approved activity. Generate one synthetic FLUX line-art visual for the drawing guide and compose a local HTML preview for review. No roster, child profile, or child artwork is sent. Deck is marked DRAFT and is never published. Do not create a product Teacher endpoint in this POC; report that API gap explicitly.
5. Exercise the isolated Parent API workflow on the existing generated synthetic butterfly drawing through story draft and script confirmation. Exercise current relevant AI-related mounted API routes and negative business-rule cases. Direct Modal worker calls are identified separately from HTTP API success. Do not select/show Parent lesson activities because video is intentionally skipped and SRS places them after a playable video.
6. Capture exact API/worker statuses, timing, model revisions, prompt/schema versions, request/response hashes, output review, and limitations under FEAT-063 evidence. Stop task-owned local services and stop all Modal `dev` apps after evidence is saved; retain shared Volumes/model weights and do not delete apps or secrets.

## Acceptance criteria

- AC1: Story worker rejects missing, extra, wrong-version, unconfirmed-subject, role-inappropriate, and out-of-range inputs without dispatch or output persistence.
- AC2: A valid Parent input bound to the confirmed synthetic drawing produces a schema-valid Vietnamese draft with 5–15 sequential scenes and total duration 30–90 seconds; each scene has required action, visual prompt, narration, timing, and visual-anchor fields.
- AC3: Butterfly lifecycle guard blocks the previously observed egg-to-adult and nest-seeking errors. Guard failure is a safe draft-generation failure; no silent rewrite or retry.
- AC4: Parent story API persists immutable revisions and provenance; requires adult script confirmation before any downstream video-admission state; enforces maximum three rewrites and idempotent replay.
- AC5: Teacher deck candidate references only the synthetic approved plan/activity, has a 16:9 layout and 3–5 progressive steps, and does not invent/add activities. The HTML preview and FLUX image are evidence-only DRAFT assets.
- AC6: Current relevant HTTP API success/negative cases are run and recorded. Missing/unmounted operations, including the Teacher deck HTTP endpoint and any post-video activity endpoint in StoryRun-lite, are reported as gaps, not successful APIs.
- AC7: No video inference, real child data, real lesson document, publication, production model promotion, or product quota charge occurs.
- AC8: Task-owned local services and all deployed Modal `dev` apps are stopped and verified; shared Volumes and model weights remain intact.

## Planned file boundary

- `backend/src/sketch2life/contracts/schemas/ai_story.py` (new)
- `backend/src/sketch2life/application/ports/story_run_lite.py`
- `backend/src/sketch2life/application/services/story_run_lite.py`
- `backend/src/sketch2life/domain/story_run_lite.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/tables.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/repository.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/composition.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py`
- `backend/src/sketch2life/interfaces/http/story_run_lite_openapi.json`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json` (published local contract snapshot)
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/11-generate-story-revision.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/12-get-story-revision.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/13-confirm-story-revision.bru`
- `backend/alembic/versions/20261104_story_revisions.py` (new)
- `deployment/modal/srs_v23/contracts.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/flux_image_app.py`
- `deployment/modal/srs_v23/workloads.json`
- focused StoryRun-lite contract/unit/integration tests and Modal contract tests
- `features/FEAT-063-system-architecture-rearchitecture/evidence/AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md`
- task-local evidence scripts/assets under `evidence/scripts/` and `evidence/assets/ai_flow_srs_alignment_20261104/`
- additive FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, and `evidence/README.md`

No other files are in scope without a recorded plan amendment.

## Verification and stop rules

1. Read back the approved plan hash and preserve unrelated worktree changes.
2. Add focused schema, business-rule, migration, and HTTP contract checks; run those plus the task-owned StoryRun-lite PostgreSQL/API workflow.
3. Use one call per actual Modal AI workload in this plan: drawing if the prior generated fixture must be reinterpreted, story draft, Teacher deck text, and one FLUX guide visual. No automatic retry. Unknown call outcome remains unknown and is not repeated.
4. Deploy/redeploy only affected private `dev` app functions. Stop on missing model, unavailable GPU, unknown dispatch result, schema/factual guard failure, or unexpected billing/capacity behavior; preserve evidence and do not switch GPUs/providers.
5. Do not run video, SAM2, lesson-plan suggestion, TTS, Whisper, or unrelated AI workloads. Do not edit `.env`, secrets, SRS, or model-selection decision.
6. Run repository security validation before any future commit/push; this task does not authorize commit/push.

## Risks and limits

- FEAT-063 SRS v2.3 is a draft and age-band boundaries remain open. The synthetic story uses exact age months only and does not invent an age-band taxonomy.
- One known-facts guard is not proof of broad factual correctness; every generated script remains a draft requiring adult review.
- Modal L4 capacity/cold start may block calls. An unknown result is not retried.
- Teacher deck generation is a synthetic capability POC. It does not create a production Teacher endpoint, occurrence lifecycle, Core asset registration, or publication approval workflow.
- StoryRun-lite remains a local synthetic Parent pilot, not the full production Story/AI Job architecture.

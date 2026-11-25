# FEAT-084 — Port the new Parent AI screens of `codex/parent-modal-e2e-20261123` onto the current mobile line

- Implementation status: APPROVED_NOT_STARTED
- Owner: Project owner (Person 2, AI Understanding lane).
- Worktree: `.worktrees/aiport2` (branch `codex/aiport2-mobile-ai-20261123`), based on `origin/feature/fe-mobile-remediation` at `d8786b2b` (goal v4 Phase A Android Parent wiring).
- Source: `origin/codex/parent-modal-e2e-20261123` at `77635688` (CaoDat, 2026-11-23), `apps/ui-mobile` only.
- Backend contract: FEAT-083 (branch `codex/aiport1-backend-ai-20261123`, commit `283158a8`), read-only.
- Prepared: 2026-11-23.

## Authority

- Product requirements: only the FEAT-063 canonical working SRS (v2.7-draft) named in `docs/context/SRS_AUTHORITY.md` at the base commit. This plan does not change the SRS or any SRS authority pointer; SRS Rev70–Rev73 on the source branch is not adopted here.
- Decision (owner, 2026-11-23): the current mobile line is the base and Phase A wins. The new AI screens are brought in beneath the Phase A wiring (activities, selection, re-confirm, replay). The source branch's older mobile files are never taken wholesale.

## Goal

Add the topic, drawing-subject and sketch-guide screens of the source branch to the current Parent mobile app and wire them to the backend routes ported by FEAT-083.

## Backend contract to wire (field names and limits come from the FEAT-083 Pydantic models)

- `GET /api/parent/v1/topics/suggestions` → `ParentTopicSuggestionSetV1` (three topic cards per draft).
- `GET /api/parent/v1/topics/{topic_id}/drawing-subject-suggestions` → `ParentDrawingSubjectSuggestionSetV1` (three subject cards; `generation_source` `CURATED_CATALOG` or `QWEN_DRAFT`; `review_required` true). A 503 `PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED` shows the API's Vietnamese message and lets the adult choose a catalogue topic.
- `POST /api/parent/v1/topics/custom-subject-validation` → `ParentCustomSubjectValidationV1`; a 422 `PARENT_TOPIC_TEXT_NOT_ALLOWED` shows the API message.
- `POST /api/parent/v1/ai/sketch-guides` with the new `SvgTopicStrokeGuideRequestV1` body and `SvgTopicStrokeGuideSourceDraftV1` response; an unknown topic returns 404 `CURATED_SVG_GUIDE_NOT_FOUND` and the UI lets the adult continue without a guide. The old body `{topic, difficulty, step_count}` is replaced.

## Scope

1. Screens and components from `77635688`, adapted to the current navigation and gates: `DrawingSubjectScreen`, `SketchGuideScreen`, `LearningPathScreen` (only if it is a path/topic chooser that calls no out-of-scope route), `ParentAiLoadingState`, `ProgressiveSvgGuide`, `domain/svgGuide.ts`, `domain/topicMatching.ts`, and the topic and subject parts of `TopicScreen`.
2. Hand-merge the additive types and API calls into `domain/types.ts`, `application/ports/ParentPorts.ts`, `application/ports/ParentApplicationModule.ts`, `application/use-cases/*`, `infrastructure/http/ParentApi.ts`, `presentation/navigation/parentFlowV1.ts`, `useParentController.ts`, `workflowTypes.ts` and `ParentExpoApp.tsx`.
3. Tests of the ported pieces from the source branch (topic matching, SVG guide, topic and sketch-guide additions to the API contract test), plus new tests for the 404 `CURATED_SVG_GUIDE_NOT_FOUND` path and for the 422/503 topic messages.

## Out of scope

- `VideoCandidateScreen`, `videoCandidateProgress` and any video-candidate API wiring.
- Activity suggestion/selection calls on `/api/parent/v1/ai/story-runs/{id}/activity-*`; the Phase A wiring of `GET /v1/activities` and `POST /v1/story-runs/{id}/activity-selection` stays untouched.
- Registration completion, `ParentAuth.ts` provisioning, `config/rootEnv.js`, `app.config.js`, `tsconfig*`, Google sign-in changes.
- Story v3 input, Qwen3.8 story/activity, SRS edits, all source-branch evidence, `.pytest-*` directories and symlinks, any backend or Modal file.

## Constraints

- Phase A flow gates, run lifecycle and replay behaviour do not change.
- No real provider, Firebase or paid API call; no secrets, tokens, absolute machine paths, symlinks or model weights in Git. UI copy is Vietnamese and passes `scripts/validate-ui-copy.mjs`. Mobile holds no Modal, S3, Lightning or Runpod credentials or endpoints.
- `node_modules` may be linked temporarily by directory junction from `.worktrees/mobile` (read-only use) and the junctions are removed with a non-recursive `rmdir` before the run ends. No network install.
- Do not edit approval records or any other feature's records. Do not touch other worktrees. One finished task is one commit; no commit or push unless the owner asks.

## Acceptance criteria

1. `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, `python tools/validate_harness.py` and `git diff --check` pass in `.worktrees/aiport2`.
2. `vitest run tests` in `apps/ui-mobile`: every test that passes on `d8786b2b` still passes, except assertions of the one replaced `sketch-guides` request shape (listed by name in the evidence notes); new tests pass; `node scripts/validate-ui-copy.mjs` passes.
3. `tsc --noEmit -p tsconfig.typecheck.json`: no new error outside `packages/art-renderer` compared with a baseline run on `d8786b2b`.
4. The request and response shapes in `ParentApi.ts` match the FEAT-083 Pydantic models (the models checked are listed in the evidence notes).
5. The run log under `E:\AI_LOG\CODEX\AIPORT2-mobile-ai\` and `evidence/notes/FINAL_REPORT_20261123.md` list ported files, hand-merged files, edited existing tests, test numbers, anything NOT RUN, and open owner questions.

## Follow-ups (not part of this plan)

- Video-candidate screen and its backend, AI-generated activity set under Phase A, owner decision on SRS Rev70–Rev73.

# BE and AI lane handoff for an AI agent (open questions and constraints)

```yaml
record_type: AGENT_HANDOFF
audience: AI agent working the backend/AI lane in this repository (machine-oriented; not a message to a person)
author_lane: Person 2 coordinator (mobile + Parent flow integration)
date: 2026-11-13
branch_context: feature/feat063-m2-parent-teacher-foundation (code tip includes S1a-P2 and the dev Parent story flow, integration commit 9dfdd2d7)
status: OPEN_QUESTIONS
approval_record: NO
owner_modal_call_approved: NO
response_file: features/FEAT-063-system-architecture-rearchitecture/plan/BE_AI_HANDOFF_RESPONSE_<YYYYMMDD>.md
```

## 1. How to use this file

1. Read this file, then the evidence it cites. Verify every cited fact against the repository before relying on it.
2. Answer each question id below in the response file, using the response format in section 6. Mark every answer as `VERIFIED_BY_RUNTIME`, `VERIFIED_BY_CODE_READING`, or `NOT_VERIFIED`.
3. Fix only what falls inside your assigned allowlist and approvals. This file authorizes no code change, no approval entry, and no Modal call.

## 2. Hard constraints

- Do not edit `apps/ui-mobile` or any mobile file. The owner (Person 2) owns the mobile base. The BE/AI lane changes the AI side and backend only.
- Do not write or change `approvals/TASK_APPROVAL.md` or `DECISIONS.md`. The owner records approvals and decisions.
- Do not call Modal or any AI provider from automation. `OWNER_MODAL_CALL_APPROVED=NO`. A bounded Modal approval is required first (see BQ-4).
- Do not place credentials, tokens, database URLs, emails, or local absolute paths in any repository file.
- Documents in English. One finished task = one commit. Commit or push only when the owner explicitly asks.
- Treat repository records pinned by hash as read-only. If a hash mismatch appears, stop and report it; do not correct it.

## 3. Facts established on 2026-11-13 (verify before use)

| id | fact | source |
|---|---|---|
| F1 | A real-flow test ran on the scratch Docker stack (real PostgreSQL, real Firebase auth, Android emulator) with no Modal call. Login, Parent profile list/create/PATCH/DELETE, lesson seeding, StoryRun create and context confirmation worked. | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REAL_FLOW_NO_MODAL_TEST_LOG_20261113.md` |
| F2 | After context confirmation a run sits in `story.runs.run_state = INPUT_PROCESSING`. The mobile client resumes only `CONTEXT_PENDING`, so a relaunch shows the open run but cannot continue it. | same log, issue I-11 and steps 15-16 |
| F3 | The unique index `uq_story_run_active_parent` on `story.runs(active_owner_parent_account_id)` (partial, non-null) blocks a second active run per parent. Allowed `run_state` values come from `ck_story_run_state` after migration `20261112_parent_story_context.py`. | `backend/alembic/versions/` |
| F4 | Parent routers present: `/v1/parent/profiles`, `/v1/story-runs` (create, read, `active/current`, `context-confirmation`, `subject-confirmation`, `script-confirmation`), `/api/parent/v1/ai` (`sketch-guides`, `drawing-understandings`, `story-runs/{run_id}/story-revisions`). No audio-transcription or transcript-confirmation route was found in the Parent routers. | `backend/src/sketch2life/interfaces/http/routers/parent_*.py` |
| F5 | `POST /v1/story-runs/{run_id}/script-confirmation` (repository `parent_story_repository.py`, `confirm_story_revision`) records an adult CONFIRM only: story revision becomes `CONFIRMED`, `run_state` stays `SCRIPT_REVIEW`, `job_state` becomes `SUCCEEDED`, no video admission is started there. Request: `expected_revision` (1-4), `story_sha256` (64 lowercase hex), header `Idempotency-Key`. Stale revision returns 409 `PARENT_STORY_REVISION_STALE`. This is code reading only. | repository + router + schema |
| F6 | The mobile client calls `POST /api/parent/v1/story-runs/{id}/cancel`, `DELETE /api/parent/v1/story-runs/{id}`, `GET /api/parent/v1/story-runs`, `POST /api/parent/v1/story-runs/{id}/audio-transcriptions`, and a transcript confirmation. These paths were not found among the Parent routers. A different cancel route exists in the Lite router: `POST /v1/story-runs/{run_ref}/cancel` with `CancelRunRequest` and optional `If-Match`. | `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`; `routers/story_run_lite.py` |
| F7 | The mobile app now treats the open run as blocking and shows a banner. A reachable cancel/abandon path from Home is a planned mobile task that depends on BQ-2. | FEAT-081 CONTEXT/STATUS backlog proposals |

## 4. Open questions

### BQ-1 INPUT_PROCESSING after context confirmation (blocks: runtime acceptance of resume; not Wave 3 code)
- Question: Does `INPUT_PROCESSING` after context confirmation correspond to an active job or a queued/awaiting-provider state? Which of `job_state`, `retryable`, `error_code` and stage fields describes it?
- Needed: the legal transitions out of `INPUT_PROCESSING` (to `SUBJECT_REVIEW`, `FAILED`, others), which request triggers them (`drawing-understandings`?), and what the client can read or call while Modal is disabled.
- Needed: whether `GET /v1/story-runs/active/current` returns enough fields to distinguish "waiting for artwork upload", "analysis running", and "failed/retryable".

### BQ-2 Parent cancel/abandon contract (blocks: mobile Home cancel action)
- Question: What is the verified route, method, request/response contract, authorization, idempotency behavior, and state transition for cancelling an unfinished Parent StoryRun?
- Context: SRS target (per planning notes) says cancellation of an unfinished run enters `DELETE_PENDING`, releases the active-owner lock immediately, and starts the content purge lifecycle. Confirm or correct.
- Needed: whether the mobile paths in F6 are intended, or whether the client must call a different route. Do not leave the answer implicit.

### BQ-3 Audio transcription and transcript confirmation (does not block Wave 3; blocks the later audio task)
- Question: Is a Parent audio-transcription route and a transcript-confirmation route planned, and with what contract?
- Needed: availability status, request (multipart field names, size/type limits), response fields, idempotency, and whether a pre-run transcription path exists (the owner decision keeps the typed idea required until it does).

### BQ-4 AI fix scope and Modal approval boundary (blocks: any real AI acceptance)
- Question: What exactly is being fixed on the AI side (drawing-understandings, story-revisions, sketch-guides, or the worker)? Which contracts change (request, response, error codes such as `MODAL_MODEL_OUTPUT_INVALID`)?
- Needed: a contract diff (before and after) and an offline test that proves the change without calling Modal.
- Needed: the smallest bounded Modal approval that would validate the fix (workloads, number of calls, caller). The owner decides; propose the wording, do not assume it.
- Context: earlier Modal smoke tests were paused by the owner until this fix lands. No Modal call is authorized now.

### BQ-5 Script-confirmation side effects (confirmation request)
- Question: Confirm F5 by reading everything reachable from `confirm_story_revision` (including database triggers and background workers). Does anything start video admission or enqueue video work?
- Answer expected: `NO_SIDE_EFFECTS_FOUND` or a precise list.

### BQ-6 Seeding and local-stack practice (non-blocking; reduces setup friction)
- Question: What is the intended way to provide lesson-library data and role/identity rows for a local Parent flow? The scratch test used four hand-seeded lesson rows and a synthetic-profile flag.
- Question: Which Compose practices are intended? Issues met: MinIO image pull returned 401; Docker build required a `packages/art-renderer/dist-demo` directory; native PostgreSQL held host port 5432; the Alembic chain had multiple heads (`upgrade heads`).
- Answer expected: a documented command sequence or a statement that the repository already documents it, with the file path.

## 5. Mobile-side dependencies on the answers

| question | mobile task blocked | mobile lane action when answered |
|---|---|---|
| BQ-1 | state-aware resume of an active run | owner approves a separate task card |
| BQ-2 | reachable cancel/abandon action on Home | owner approves a separate FE/BE task card |
| BQ-3 | audio transcription flow | owner approves a later task |
| BQ-4 | real-AI acceptance of the pre-video flow | owner records a bounded Modal approval |

The FEAT-081 Wave 3 plan (P03-P06) is code-only with fake data and does not wait on these answers.

## 6. Response format

Write the response file named in the header. Use exactly one block per question:

```yaml
question_id: BQ-1
answer_status: VERIFIED_BY_RUNTIME | VERIFIED_BY_CODE_READING | NOT_VERIFIED
answer: <short factual statement>
evidence: <repo-relative paths and line numbers, or command + result>
contract: <route, method, request fields, response fields, error codes if applicable>
open_risks: <list or NONE>
needs_owner_decision: <list or NONE>
```

Add a final block `files_changed: []` listing any repository path you changed, with size and SHA-256 prefix, or `NONE`.

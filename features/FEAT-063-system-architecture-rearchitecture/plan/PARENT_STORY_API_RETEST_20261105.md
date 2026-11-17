# Parent StoryRun-lite API regression retest

**Plan revision:** 1  
**Status:** APPROVAL RECORDED / EXECUTION COMPLETE — PARTIAL RESULTS  
**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063  
**Worktree:** `codex/feat063-modal-backend-completion-20261103`

## Goal

Re-test the current Parent StoryRun-lite HTTP API after the Modal story parser fix. Record status, latency, contract alignment, and business-rule behavior for every mounted API operation, and verify one HTTP-triggered story draft through the real Modal Qwen worker.

## Basis and approval

The owner directly requested a fresh API retest with timings and a list of failures, contract drift, and business-rule mismatches. The retest is limited to the Parent StoryRun-lite API and the story-generation path relevant to the just-completed parser fix.

## Scope

1. Run the focused StoryRun-lite API, OpenAPI, application, domain, and worker-contract test suites. Record total elapsed time and pass/fail/skip counts.
2. Start one task-owned, disposable PostgreSQL 17 container on `127.0.0.1:5433`, without a persistent volume. Use only the isolated database `storyrun_lite_feat063_ai_20261104`, required by the existing synthetic API harness's database guard. Run `alembic upgrade head` against that database only; verify the connected database and owner before serving requests.
3. Run the current 13-operation StoryRun-lite route matrix through the local HTTP harness with synthetic fixtures and a deterministic fake vision adapter. This phase must dispatch zero AI calls. Include the existing expected 4xx/business-rule cases and retain per-request status and elapsed milliseconds.
4. Run one synthetic Parent HTTP story flow through `StoryRunLiteService` and the actual `ModalStoryFunctionClient`. Upload the generated butterfly fixture, use a deterministic synthetic butterfly understanding result, exercise explicit adult subject confirmation, create/fetch/confirm the story draft, and record per-request timings. Use the deployed FEAT-063 `dev` language/audio worker and Qwen2.5 story pin. Override the API adapter's wait to a hard maximum of 300 seconds for this one call. Persist a dispatch-intent record before the call; no retry after timeout, ambiguous outcome, or terminal failure.
5. Keep story output in memory only for schema/fact validation; redact story text, prompts, and child/profile details from all evidence. Record status codes, response field names, lengths/counts, hashes and elapsed times only.
6. Compare observed routes, schemas and state transitions with FEAT-063 SRS v2.3-draft, the pinned StoryRun-lite OpenAPI contract, `StoryRevisionDraftV1`, and the implemented business-rule guards. Separate expected negative responses from actual defects and unverified scope.
7. Stop the task-owned Modal language/audio app and the disposable PostgreSQL container; verify zero Modal tasks, stopped container, and unchanged shared Docker services/volumes. Preserve existing shared services and Modal model Volumes.

## Explicit exclusions

No backend/product code changes, migration edits, canonical SRS/OpenAPI edits, real child data, drawing VLM inference, Teacher/API flows, video, FLUX, SAM2, TTS, ASR, lesson suggestions, workload enablement, production configuration, `.env`/secret changes, shared DB access, shared container shutdown, Modal Volume deletion, commit, push, or merge. If the isolated DB cannot be identity-verified, do not start the API or migrate another target.

## Acceptance criteria

- Focused StoryRun-lite tests report exact counts and duration.
- All 13 mounted HTTP operations are exercised and reported individually with status and elapsed milliseconds; expected validation/business-rule 4xx cases are labeled expected.
- One actual HTTP story-generation call either returns a draft accepted by worker and backend schemas plus butterfly validation, or records a safe terminal/unknown failure within 300 seconds. No duplicate or retry.
- Adult confirmation is required before story generation, and story confirmation is required before the run enters the confirmed-script state; Parent activity preselection remains rejected. No video state or post-video activity is claimed as tested.
- No raw story, prompt, child/profile data, token, or credential is written to FEAT-063 evidence.
- Modal app is stopped with zero tasks. The task-owned PostgreSQL container is stopped, and shared services are left running.
- The report lists every failure, any contract drift, any business-rule mismatch, and limitations explicitly.

## Verification sequence

1. Verify this exact approved plan and inspect the pinned HTTP contract, fixture harness and current worktree.
2. Run the isolated contract/API suite; save timings and safe status summaries.
3. Re-create the same disposable DB for the HTTP story-flow phase, run Alembic head, verify database identity, then deploy the current language/audio app.
4. Persist story dispatch intent before invoking the HTTP route; execute exactly one actual story inference under the 300-second adapter cap.
5. Stop task-owned services, confirm cleanup, redact/inspect evidence, compare API results with SRS/OpenAPI/business rules, and update FEAT-063 records.

## Files in scope

- `features/FEAT-063-system-architecture-rearchitecture/plan/PARENT_STORY_API_RETEST_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/PARENT_STORY_API_RETEST_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/parent_story_api_retest_20261105/`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_parent_story_api_retest_20261105.py`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

Any necessary product-source or other path requires an amended plan before use.

## Amendment revision 2 — exercise every mounted Parent AI API

**Date:** 2026-11-05 (Asia/Saigon)  
**Status:** OWNER AUTHORIZED / IN PROGRESS  
**Reason:** The owner clarified: “chạy bằng cả các API gọi AI để test luôn”. This amendment supersedes the revision-1 exclusions for the Parent drawing-understanding VLM and exercises both AI-dispatching routes in the mounted StoryRun-lite Parent API.

### API inventory and revised scope

The mounted Parent StoryRun-lite API has 13 distinct operations. Two dispatch AI:

1. `POST /v1/story-runs/{run_ref}/assets` dispatches the drawing-understanding workload (`drawing.analyze`) after artwork admission.
2. `POST /v1/story-runs/{run_ref}/story-revisions` dispatches the combined story/storyboard worker (`story.generate`; `storyboard.generate` is not a separate HTTP call).

The retest will make at most one real Modal request for each workload, sequentially, with a 300-second client wait cap per request. No retry or duplicate dispatch is permitted after timeout, unknown outcome, or terminal failure. The story API call still requires adult subject confirmation. If the real drawing-understanding call fails, is unknown, or produces a candidate that cannot be safely used for the butterfly story fixture, do not retry it; use a separate synthetic actor/run and deterministic vision fixture only to exercise the independent story API once, and label that limitation prominently.

The remaining 11 distinct mounted operations will be exercised through HTTP with synthetic fixtures and zero additional AI dispatches. Record per-request status and elapsed milliseconds, including validation and business-rule cases.

The workload registry contains other AI capabilities without a mounted Parent HTTP API in this slice (Parent line-sketch guide, lesson visual generation, ASR/TTS as standalone workloads, SAM2 segmentation). Teacher Sketch Deck has no Teacher HTTP/session API. Record these as “no HTTP API in current slice”; do not call their private Modal handlers under this API retest. Video remains excluded as previously agreed.

### Revised acceptance criteria

- All 13 distinct StoryRun-lite HTTP operations are reported with status and elapsed milliseconds.
- Both mounted AI-dispatching routes are attempted at most once each through the HTTP API and use synthetic artwork only; report actual model, Modal call outcome and latency without persisting prompt or generated story text.
- Adult subject confirmation must precede story generation; adult script confirmation must precede the confirmed-script state; Parent activity preselection remains rejected.
- If drawing analysis fails, is unknown, or returns an unusable candidate, the report distinguishes the real VLM outcome from any separate fixture-backed story test. Never claim a single uninterrupted end-to-end AI success in that case.
- No raw story text, prompt, profile/child data, token, or credential is written to evidence.
- Deploy only the task-owned FEAT-063 dev drawing-VLM and language/audio Modal apps needed for these two calls; stop them afterward and verify zero tasks. Preserve shared Modal Volumes and Docker services.

### Revised execution sequence

1. Re-inventory the mounted StoryRun-lite operations and confirm the two AI routes above.
2. Run focused backend contracts and the no-AI route matrix against the already identity-verified disposable PostgreSQL database.
3. Deploy the dev drawing-VLM and language/audio apps; perform the synthetic Parent HTTP flow and make no more than one call per AI workload, each capped at 300 seconds.
4. If the VLM does not reach adult subject review, make no VLM retry; optionally continue only the independent story API test with a separate synthetic fixture/run as described above.
5. Stop both task-owned Modal apps and the disposable PostgreSQL container; verify shutdown, redact/inspect evidence, compare results to SRS/OpenAPI/business rules, and update FEAT-063 records.

## Execution closeout — 2026-11-05

- **Outcome:** All 13 mounted operations were covered by 22 no-AI matrix requests. The real drawing route ended unknown after 303.762 seconds; the separate fixture-backed story call returned 502 `STORY_OUTPUT_INVALID` after 59.266 seconds because the worker rejected the generated butterfly lifecycle as `EDUCATIONAL_FACT_INVALID`. No successful story draft, script confirmation, video, or post-video activity result is claimed.
- **Verification:** 154 focused backend tests passed in 12.52 seconds; Modal story-output/parser tests reported 45 passed, 1 skipped in 0.67 seconds. The no-AI matrix took 2.624 seconds. `alembic upgrade head` reported multiple independent heads; `alembic upgrade heads` applied all heads to the task database in 2.05 seconds.
- **Plan variance:** The first harness attempt used non-contract synthetic profile refs and received 422 before dispatch; evidence was preserved in `attempt_01_invalid_synthetic_run_request/`. The harness was corrected to the declared `synthetic-parent-demo` value. A runner exit-code gap was also corrected after the captured run; the observed story 502 is still reported as a failure, and no AI request was repeated.
- **Cleanup:** Both task-owned Modal apps stopped with zero tasks. The disposable PostgreSQL container was verified `exited`; shared Docker containers and Modal Volumes were preserved.
- **Detailed results:** `evidence/PARENT_STORY_API_RETEST_20261105.md` and `evidence/assets/parent_story_api_retest_20261105/attempt_02/`.

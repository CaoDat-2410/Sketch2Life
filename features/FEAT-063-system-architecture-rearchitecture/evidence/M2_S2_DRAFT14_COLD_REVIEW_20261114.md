# FEAT-063 M2 S2 Draft 14 Independent Cold Review

Review date: 2026-11-14

Target worktree: `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `b740f5033ec71baefd50b2b2ad250b663539f794`.

Reviewed plan: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT14_20261114.md`, 71,308 bytes, SHA-256 `0F74571746692D0E9A095F30216512253AEDF7237999D0AF17281B6348AA335E`.

This is an independent fresh-context review. I derived the findings from the target plan, decisions, SRS inputs, prior Draft 13 materials, and cited source files in this worktree; I did not rely on prior authoring rationale. This is a read-only plan review, not owner approval, Task Approval, implementation authorization, or launch authorization.

## Verdict

**CHANGES REQUIRED**

## Findings

### P2-1 — Late artwork-success acceptance expects a code the current guard does not return

Draft 14 AT-08 says a late artwork-analysis success after cancellation must return HTTP 409 `INVALID_STATE_TRANSITION` (plan line 125). The current guard in `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:572-574` raises HTTP 409 with code `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING` for every non-`INPUT_PROCESSING` state. `backend/src/sketch2life/interfaces/http/routers/parent_ai.py:378-387` forwards that code unchanged. D-201 at `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:528` says to reuse `INVALID_STATE_TRANSITION`.

The late result is rejected and the route surfaces 409 today, but the acceptance code and the current guard/D-201 trace do not agree. Specify that the `DELETE_PENDING` branch must return `INVALID_STATE_TRANSITION` and be mapped by the route, or reconcile the acceptance with the owner decision before approval.

## What I verified

- The target worktree, branch, and HEAD match the requested pin. The plan’s byte count and SHA-256 are as recorded above.
- D-194 through D-201 are consistent with the plan’s stated authority and phase boundaries: Rev60 remains the canonical unsigned working SRS; Rev67 is a conditional owner-selected input; the S1a-P2 known gap and S1b deferral remain; D-199 cancel/status scope and D-200’s HTTP 400 `INVALID_IDEMPOTENCY_KEY` choice remain; D-201 adds only the late-result guard and run-revision precondition. The plan does not grant approval or launch authority.
- The normal combined application mounts the existing Parent StoryRun router; the classroom profile does not. No Parent cancel route exists in the current router. Current active/current and by-ID GET responses expose `run_state`, `job_state`, `retryable`, and `error_code`, but not a run revision (`backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:88-113,200-240`; `backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-134`).
- The proposed `run_revision` path is accurate: the existing `story.runs.revision` is available to `get_run`, then must be added to `ParentStoryRunRecord`, `ParentStoryRunResponseV1`, and both response builders (`parent_story_runs.py:_response` and `parent_ai.py:_story_response`). Current source has one `ParentStoryRunRecord` constructor and two `ParentStoryRunResponseV1` builders. The existing table and migration define a non-null BigInteger `revision`, allow `DELETE_PENDING`, and allow `CANCEL_RUN` receipts; no new status or DDL is needed for the planned response field or guards.
- Independent search of backend Python source found the current Parent `story.runs` insert and all nine Parent `story.runs` update statements in `parent_story_repository.py`. The create insert initializes revision to 1. Every current state-changing update increments revision; the context replay/already-confirmed no-op does not update the run row. The inventory covers the Parent writers for state, job state, retryability, error code, result hash, active-owner lock, and revision. The separate StoryRun-lite demo repository is outside the Parent target adapter.
- Current guards reject `DELETE_PENDING` on context confirmation, artwork attach, artwork-analysis success, subject confirmation, story-generation start, and script confirmation. The artwork-analysis success guard is the code mismatch reported above. The current artwork-analysis failure/unknown writer and story-generation completion/failure/unknown writers have no `DELETE_PENDING` guard (`parent_story_repository.py:1088-1179,963-1078`).
- The plan accounts for the late Parent AI paths. Current artwork provider failure/unknown handlers suppress `ParentStoryRunError` before returning provider 502/504 (`parent_ai.py:307-338`); malformed-output paths call the failure writer at `342-369`; story failure/unknown and validation paths call it at `460-520`; completion calls it at `530-538`. Draft 14 explicitly requires the affected routes to surface the guard’s 409 (`plan:105,124-126`). These behaviors are not runtime-verified.
- The required `expected_revision` JSON body, stale 409 `STALE_REVISION`, and replay-before-precondition ordering agree with D-201. The current Parent validation handler maps a missing required body field on `/v1/story-runs...` to HTTP 400 `INVALID_REQUEST` with field errors (`backend/src/sketch2life/interfaces/http/app.py:531-590`). There is no current cancel model or route; the replay ordering for cancel remains future work.
- Draft 14 preserves the listed P2-1 and P3-1/P3-2 dispositions: D-200’s mismatch response remains separate from same-request replay; the BQ-1 context-confirmation row is code-reading only; and the crosswalk’s `/v1/jobs/{job_id}` entry is marked superseded by D-199. The cited repository and GET mappings support the stated `context_confirmed`, run-state, and job-state behavior.
- I verified all 62 Draft 14 input-pin rows and all 31 migration pins against their files. Historical DECISIONS digests were checked as byte-identical prefixes; all supplied sizes and hashes matched. This includes the Rev60 authority source, owner-selected Rev67, crosswalk, Draft 13, prior Draft 13 review, D-201 decisions file, and the listed D-201 source paths.
- At review start, status already contained a modified `DECISIONS.md`, untracked `BE_SESSION_CHECKPOINT_20261114.md`, Draft 10–13 reviews, and Draft 11–14 plans. These author-created paths were left untouched.

## What I could not verify

No tests, validators, backend, database, migration, Docker, network, provider, or Modal commands were run. Runtime route exposure, HTTP behavior, authentication/authorization, concurrency, cancellation, idempotency replay/mismatch, late-result persistence, migration applicability, task-database contents, worker behavior, and provider behavior remain unverified. The cancel endpoint and its request/response contract do not yet exist in source.

## Review boundary

Only the requested new review report was created by this reviewer. Existing worktree changes were preserved. This report records a plan review only and is not approval to implement or launch S2/S3.

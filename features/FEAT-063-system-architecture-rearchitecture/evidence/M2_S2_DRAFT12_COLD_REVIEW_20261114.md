# M2 S2 Draft 12 Cold Review — 2026-11-14

## Verdict

**CHANGES REQUIRED** — 0 P1, 1 P2, 2 P3.

Draft 12 carries forward both round-2 P2 fixes and the stale-K3 note. Its current route and ownership claims match the inspected worktree code, and it preserves the no-DDL, no-approval, and no-launch boundaries. Before it is used as an S2 approval candidate, reconcile the cancel idempotency response with the canonical SRS and tighten two traceability statements below.

**Reviewed plan:** `.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT12_20261114.md`.

**Review type:** Independent fresh-context, read-only plan review. The prior cold reviews were read as required inputs for checking the stated fix dispositions; their conclusions were not treated as substitutes for checking the cited records and code.

## Findings

### P2-1 — Cancel idempotency response conflicts with the canonical SRS

**Evidence:** Rev60 §21.4 says reuse of an idempotency key with a different payload returns `INVALID_IDEMPOTENCY_KEY` (`features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1670`). D-199 instead says reuse of the same key for another run or request returns HTTP 409 (`.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:526`), and Draft 12 makes that the future AT-08 assertion (`.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT12_20261114.md:77,193`). The existing Parent receipt helper compares the stored request fingerprint and raises HTTP 400 `INVALID_IDEMPOTENCY_KEY` on mismatch (`.worktrees/m2-s2/backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1348-1352`); the current router error adapter forwards that status and code (`.worktrees/m2-s2/backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:81-85`). The plan correctly recognizes that a future cancel path must map the helper mismatch to D-199’s 409, but it does not record the resulting deviation from Rev60.

**Impact:** The planned public contract differs from the current canonical SRS on a state-changing command. D-199 is explicit owner direction, so this is a contract-reconciliation gap rather than an invented plan requirement. The plan’s remaining-open-contract note does not identify this specific status/code conflict.

**Suggested fix:** Before S2 approval, record whether D-199 is an explicit cancel-specific exception to Rev60 §21.4 or whether cancel should retain `400 INVALID_IDEMPOTENCY_KEY` for a fingerprint mismatch. Make the AT-08 cases distinguish same-run/different-payload reuse from cross-run reuse and state the approved status/code for each. Reconcile the SRS/Parent contract as required; do not leave the 409 mapping implicit in implementation work.

### P3-1 — The BQ-1 table omits the context-confirmation transition it claims to answer

**Evidence:** The BE/AI handoff asks what happens after context confirmation, which transitions and requests follow, and whether the current read fields distinguish waiting, running, and failure (`features/FEAT-063-system-architecture-rearchitecture/plan/BE_AI_HANDOFF_FOR_AI_AGENT_20261113.md:44-52`; `tmp/be-ai-questions/BE_AI_QUESTIONS_20261113.md:45-51`). Draft 12 labels its table a BQ-1 transition table and says BQ-1 is answered by code reading (`.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT12_20261114.md:86-100,190`), but the rows omit context confirmation. In the repository, `confirm_context` updates the input confirmation fields and run revision without assigning `run_state` or `job_state` (`.worktrees/m2-s2/backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:325-400`). The response exposes `context_confirmed`, `job_state`, `retryable`, and `error_code` (`.worktrees/m2-s2/backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-133`). The table’s existing assignments otherwise match the cited repository code, including artwork accepted (`.worktrees/m2-s2/backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:530-544`), analysis success/failure/unknown (`.worktrees/m2-s2/backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:603-618,1154-1176`), and story generation (`.worktrees/m2-s2/backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:934-947,1021-1034,1080-1121`).

**Impact:** The transition rows are code-reading evidence, not runtime evidence, as Draft 12 correctly says. However, “BQ-1 is answered” overstates the table because it omits the specific post-context-confirmation state and does not state the observable status-field combination for that case.

**Suggested fix:** Add a context-confirmation row stating that the repository leaves `run_state` and `job_state` unchanged while marking `context_confirmed`; state what the current owner read exposes at that point. Keep request-trigger, dispatch, and provider behavior explicitly open/unverified wherever source code does not establish them.

### P3-2 — The crosswalk’s old `/jobs` route is not explicitly marked superseded

**Evidence:** The crosswalk’s “Current M2 disposition” still lists `GET /v1/jobs/{job_id}` as one of three S2 target operations (`.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md:26-30`). D-199 supersedes that route choice by directing S2 to use the existing Parent `active/current` and by-ID reads and not mount the AI Jobs candidate (`.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:526`). Draft 12 correctly says the candidate router is not in normal composition and excludes a separate `/jobs` route (`.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT12_20261114.md:47,57,80`), but its crosswalk note calls out the old basis-B statement without identifying the stale `/jobs` entry (`:37,182`).

**Impact:** A reader following the unchanged crosswalk’s “current” route list can encounter a direct contradiction with D-199’s current status disposition.

**Suggested fix:** Keep the crosswalk unchanged as historical evidence, and explicitly mark its `GET /v1/jobs/{job_id}` entry as superseded by D-199 in Draft 12’s crosswalk note.

## Verified OK

- **Authority and Rev67 boundary:** `docs/context/SRS_AUTHORITY.md:5-14` and D-195 (`DECISIONS.md:522`) keep unsigned Rev60 as the canonical working SRS. The crosswalk marks Rev61–Rev67 conditional or not affected; Draft 12 does not promote those changes (`M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md:14-22`; Draft 12 `:10,37,170-182`).
- **S1a-P2 close-out:** D-194 and the accepted addendum match Draft 12: `ACCEPTED WITH KNOWN GAP`, failed/consumed Gate P2, no retry or cleanup, three remaining synthetic rows, and production BE1 role-adapter coverage `NOT COVERED` (`DECISIONS.md:521`; `approvals/TASK_APPROVAL.md:2848-2862`; Draft 12 `:11,198`).
- **Round-2 P2-1:** AT-08 now specifies two distinct idempotency keys for competing creates and puts same-key replay in a separate case (Draft 12 `:74-75`). The route checks replay before create (`parent_story_runs.py:137-149`); the repository returns a matching replay or reports the active-run conflict (`parent_story_repository.py:68-90,169-215`).
- **Round-2 P2-2:** Draft 12 correctly places `current_input_revision` on `story.runs`; context and input metadata are on `story.run_inputs`; it also records asset nullability and size changes (Draft 12 `:164`). The migration confirms those table assignments and effects (`20261112_parent_story_context.py:48-76,105-159`).
- **Round-2 P3 stale-K3 note:** Draft 12 correctly says S3 Draft 5’s K3 clause is stale and must be reconciled before a future S3 approval, and identifies the foundation plan as older sequencing (`:201-202`). The cited S3 clause is at `M2_S3_TASK_APPROVAL_DRAFT5_20261110.md:102`; the foundation sequencing is at `M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md:571-575`; D-197/D-198 set the current S1b/K3 dispositions (`DECISIONS.md:524-525`).
- **Parent route ownership and job-status evidence:** The existing Parent router uses `/v1/story-runs`, has create, active/current, by-ID, and confirmation handlers, and has no cancel handler (`parent_story_runs.py:43,116-240,243-305`). Normal combined composition includes it by default when the demo flag is off; classroom composition does not include it (`router_composition.py:35-45,60-77`; `app.py:256-267,1003-1010`). The GET response maps and schema expose `run_state`, `job_state`, `retryable`, and `error_code` (`parent_story_runs.py:88-113,200-240`; `contracts/schemas/parent_story_runs.py:104-133`). `_owned_run` scopes reads by verified principal and returns 404 `RESOURCE_NOT_FOUND` when no owned row matches (`parent_story_repository.py:1290-1301`).
- **AI Jobs mounting:** The candidate router defines `/api/collaboration/v1/jobs/{job_id}` (`routers/ai_jobs.py:29,36-45`), but is not imported or mounted in `router_composition.py`; its separate fixture app does not make it part of the normal application. Draft 12 excludes it from S2 as D-199 requires.
- **Cancel source claims:** The current Parent receipt helper supports operation/scope-keyed receipts and stores response status/body; its mismatch response is the P2 finding above (`parent_story_repository.py:1303-1391`). The 20261112 receipt-operation check includes `CANCEL_RUN` (`20261112_parent_story_context.py:195-204`). StoryRun-lite is only a semantic reference: its cancel transaction locks/finds a receipt, checks stale revision first, rejects `DELETE_PENDING` and `FAILED` but does not explicitly reject `COMPLETED`, then sets `DELETE_PENDING`, clears the active-owner field, and finalizes a 202 receipt (`story_run_lite/repository.py:2575-2649,2671-2685,2749-2767`). Draft 12 accurately says a new Parent path must enforce D-199’s explicit `COMPLETED` guard (`:78,82`).
- **Active lock and no-additive-DDL evidence:** `active_owner_parent_account_id` exists and the partial unique index `uq_story_run_active_parent` applies to non-null values (`20261102_story_run_lite.py:355,388-395`). Parent create maps that uniqueness conflict to `ACTIVE_RUN_EXISTS` (`parent_story_repository.py:156-160`). The migration source adds the context fields and broadens the state/receipt checks, but Draft 12 distinguishes those source facts from task-database state (`20261112_parent_story_context.py:30-65,116-159,195-204`; Draft 12 `:164-166`).
- **Approval and launch boundaries:** Draft 12 is `DRAFT / NOT APPROVED / NOT LAUNCHED`; it grants no implementation, database/migration action, Task Approval, allowlist, command ceiling, gate launch, provider/Modal, network, stage, commit, or push authority (`:3,70,200,208-212`). D-194, D-196, D-198, and D-199 likewise grant no S2/S3 approval or launch (`DECISIONS.md:521,523,525-526`); the S1a-P2 addendum explicitly does not create an S2/S3 approval, allowlist, command ceiling, or gate approval (`approvals/TASK_APPROVAL.md:2860-2862`).

## Could not be verified

- The task database’s current schema, applied Alembic revisions, row counts, migration applicability, or rollback state. Draft 12 correctly marks these `NOT VERIFIED` (`:166`).
- Runtime route exposure, authentication/authorization behavior, Parent cancellation, concurrent writes, receipt replay/mismatch behavior, and any actual client-visible status transition. No Parent cancel route exists in the inspected code.
- Worker dispatch, provider behavior, purge scheduling/completion, or whether any external worker consumes `DELETE_PENDING`; the transition table is persistence code reading only.
- Gate A/B state, database inventories, and the owner-supplied CI run status. No database, backend, Docker, Modal, test, type-check, install, network, or validator command was run. I did not independently recompute every input pin in Draft 12 §9.

## Independence and review boundary

I performed this review in a fresh context, inspected the specified records and worktree code directly, and did not delegate. Previous cold-review reports were consulted only because the task required verifying their findings and dispositions.

This is a **read-only plan review, not an approval**. It authorizes no implementation, database or migration action, allowlist, command ceiling, gate, or launch. No plan or source file was edited; only this uncommitted review report was created.

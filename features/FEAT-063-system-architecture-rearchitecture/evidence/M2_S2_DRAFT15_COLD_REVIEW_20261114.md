# FEAT-063 M2 S2 Draft 15 Independent Cold Review

Review date: 2026-11-14

Target worktree: `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `b740f5033ec71baefd50b2b2ad250b663539f794`.

Reviewed plan: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT15_20261114.md`, 89,611 bytes, SHA-256 `FC880ADB618AE82AA246EAAD02ED03B107DD6213D5D01BFF56800274BFC5B436`.

This was an independent fresh-context review. I re-derived the findings from Draft 15, D-194 through D-202, the canonical SRS and crosswalk, pinned sources, and cited backend code. I read Draft 14 and its cold review for regression comparison, but did not use the prior review as a substitute for checking the claims against source. This is a read-only plan review, not an approval, Task Approval, implementation authorization, or launch authorization.

## Verdict

**CHANGES REQUIRED**

## Findings

### P2-1 — Parent AI error-code audit cites a formatter that does not handle those routes

Draft 15 expects a public top-level `code` for Parent AI guard errors and says the route should map `ParentStoryRunError` to `HTTPException(detail={"code": exc.code})`, after which `app.py:346-407` emits the top-level code (plan lines 115, 186, 198-205). AT-08 also requires that public shape for late story completion and late failure/unknown outcomes (plan lines 134, 136). The same assumption appears for current Parent AI errors: artwork attach, artwork-analysis success, and story-generation start (plan lines 198-201).

The Parent AI router prefix is `/api/parent/v1/ai` (`backend/src/sketch2life/interfaces/http/routers/parent_ai.py:64`). The artwork route is `/api/parent/v1/ai/drawing-understandings` (parent_ai.py:201-205). It does not match the `/v1/story-runs` check at `backend/src/sketch2life/interfaces/http/app.py:350` or `_legacy_parent_story_revision_path` at app.py:170-176, so it falls through to the generic `http_exception_handler` at app.py:490-491. Repository errors on that route are put in `HTTPException.detail` at parent_ai.py:303-305, 318-320, 336-338, and 386-387; the proposed late artwork guards would be mapped through the same route. Thus the claimed top-level public codes are unsupported for artwork attach, artwork-analysis success, and artwork-analysis failure/unknown (plan rows 198, 199, 203 and the artwork part of AT-08 line 136). By contrast, the story-generation route `/api/parent/v1/ai/story-runs/{run_id}/story-revisions` (parent_ai.py:408-412) is explicitly recognized by `_legacy_parent_story_revision_path` at app.py:170-176, so the top-level formatter does apply to story-generation start/completion/failure routes (plan rows 201, 204-205).

**Suggested fix:** Choose and document the intended Parent AI error envelope. To keep Draft 15's top-level-code expectations, plan an explicit handler/formatter for `/api/parent/v1/ai` that promotes the mapped code to the public top-level field, and cite it in the audit. If the existing framework error shape is intended, change the acceptance criteria and audit to assert that actual shape instead. The route mapping alone does not satisfy the current top-level assertion.

This is a static routing/formatter finding; I did not execute the app or claim runtime response evidence.

### P2-2 — AT-10 makes legacy-profile run eligibility mandatory while Rev60 leaves it open

AT-10 requires ages 121 and 155 from a trusted profile lookup to be refused with HTTP 422 `INVALID_REQUEST` and explicitly proposes a fixture for those legacy values (plan lines 178-180). Rev60 §31.10 row 16 says the target for new profiles is currently 36-120 months, but leaves the behavior of existing 121-155-month profiles—including whether they may create a run—OPEN-OWNER (`features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2728`). Rev67 Rev61's explicit “no new run above 120 months” rule is marked CONDITIONAL in the crosswalk (`features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md:16`); D-195 keeps Rev67-dependent S2/S3 impacts conditional and requires separate adoption (`features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:522`). Draft 15 also describes Rev67 as conditional (plan lines 28, 30, 182), but AT-10 still fixes this particular open behavior as an acceptance outcome.

The current service does reject values outside 36-120 with 422 `INVALID_REQUEST` (`backend/src/sketch2life/application/services/parent_story_runs.py:193-206`). That is implementation evidence, not an owner decision resolving the SRS's legacy-profile lifecycle question.

**Suggested fix:** Preserve the 121/155-month run question as OPEN-OWNER and make this outcome conditional or out of AT-10 until a separate owner decision resolves it. Alternatively, obtain and record that owner decision before treating refusal as a required product acceptance. Keep the Rev67 crosswalk conditional under D-195.

## What I verified

- Worktree branch and HEAD match the requested values. Draft 15 is exactly 89,611 bytes with the stated SHA-256.
- D-194 through D-202 align with the plan's stated scope. D-202 applies only to the late-result error-code split: existing artwork-analysis success remains HTTP 409 `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING`; the newly guarded artwork-failure/unknown and story-success/failure/unknown paths use HTTP 409 `INVALID_STATE_TRANSITION`. The other D-194 through D-201 decisions remain unchanged. Draft 15 correctly fixes Draft 14's artwork-success code mismatch (plan lines 20, 93-99, 135, 199).
- I re-derived the Parent adapter writer inventory from `parent_story_repository.py`: one `story.runs` insert (lines 108-123) and nine updates (lines 393, 531, 604, 731, 935, 1022, 1108, 1161, 1268). The create initializes revision to 1; each listed current update increments revision. The listed Parent writer groups and their current state guards match the source. The failure/unknown artwork writer and story completion/failure/unknown writers currently lack the D-201 `DELETE_PENDING` guard. The other backend run writers I found are in the distinct StoryRun-lite repository, which D-198 excludes from the selected Parent target adapter.
- The existing code/status assertions for Parent create, context confirmation, artwork attach and success, subject confirmation, story-generation start, and script confirmation match their raise sites and router mappings. Parent `/v1/story-runs` requests and the Parent AI story-revision path recognized by `_legacy_parent_story_revision_path` reach the top-level formatter. The drawing-understandings path does not, as described in P2-1. The cancel endpoint and new late-result guards remain future work; their planned status/code choices match D-199 through D-202, subject to that artwork-route envelope issue.
- AT-09 asserts only successful assistance results: submit HTTP 202, status HTTP 200, and accepted cancel HTTP 200. Their handlers/builders support those statuses. It asserts no assistance error code; the missing/non-owner `ASSISTANCE_REQUEST_NOT_FOUND` case is outside those success cases.
- AT-10's current source behavior is accurately described at the service boundary: accepted create returns HTTP 201; out-of-range trusted lookup values raise 422 `INVALID_REQUEST` before repository writes. The requirement-level status of legacy 121/155-month profiles remains open per P2-2.
- The plan does not claim new DDL or a new status value. `DELETE_PENDING`, `revision`, `version`, and `CANCEL_RUN` already exist in the pinned migrations (`20261102_story_run_lite.py:329-395`; `20261112_parent_story_context.py:57-65,195-203`). The plan also clearly withholds approval, implementation, allowlist, command-ceiling, gate, and launch authority (plan lines 3, 5, 50, 291, 301-303).
- The Changes from Draft 14 notes correctly identify the prior artwork-success mismatch and the need to map new guard errors (plan lines 16-24). The public-envelope correction is incomplete for the Parent AI prefix, as detailed in P2-1.

## Pins checked

- All 58 strict input rows in Draft 15 §9 were checked against the files in their stated root-checkout or S2-worktree locations; every size and full-file SHA-256 matched.
- All 31 migration rows were checked; every size and SHA-256 matched.
- The four historical DECISIONS entries were checked as byte-identical prefixes, and the after-D-202 full-file digest matched.
- All seven informational mobile-lane inputs exist and match their recorded last-observed size and SHA-256. I checked only their listed claims: the route-prefix mismatch, age-helper test cases, run-revision consumer/test surfaces, and the Rev67 copy's source-location identity. No input had changed since observation.

## What I could not verify

No tests, validators, backend execution, database or migration command, Docker, network, provider, or Modal command was run. Runtime route exposure and response bodies, authentication/authorization execution, concurrency, cancel/replay/mismatch behavior, late-result persistence, age-boundary runtime behavior, task-database contents, and Gate A/B remain unverified. No owner decision resolving the legacy-profile run question was present in the reviewed D-194 through D-202 record.

## Review boundary

This is a read-only plan review, not approval. Only the requested new report was created by this reviewer; existing worktree changes were preserved. No finding was repaired in Draft 15.
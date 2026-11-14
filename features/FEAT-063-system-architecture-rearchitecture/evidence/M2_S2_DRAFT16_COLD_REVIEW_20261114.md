# FEAT-063 M2 S2 Draft 16 Independent Cold Review

Review date: 2026-11-14

Target worktree: `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `b740f5033ec71baefd50b2b2ad250b663539f794`.

Reviewed plan: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT16_20261114.md`, 90,734 bytes, SHA-256 `3B76A6202E2D34D432891BBA1AE20A70361C0D4682D334D2C53AFAFF94DB10A9`.

This is a fresh-context independent review. I checked the plan against the canonical Rev60 SRS and authority boundary, D-194 through D-202, the current cited source, the source register, and Draft 15's independent cold review. Draft 15's report informed regression checks but did not substitute for re-deriving claims. The owner-selected Rev67 remains a conditional requirements input under D-195; Rev60 remains formally canonical. The mobile Rev67 row was treated only as a source-location pointer under the stated informational-input policy.

## Verdict

**READY WITH NOTES** — no actionable P1, P2, or P3 findings remain. Draft 16 resolves both findings from Draft 15. This verdict is about plan-review readiness only; the plan remains DRAFT and this review grants no approval or launch authorization.

## Findings

### P1

None.

### P2

None. The prior P2 findings and their Draft 16 dispositions are recorded below.

### P3

None.

No corrective edits are recommended. The remaining notes concern review limits and the plan's stated approval boundaries, not defects in the reviewed draft.

## What was verified

### Authority and decisions

- `docs/context/SRS_AUTHORITY.md:5-14,38-40` identifies the FEAT-063 v2.7-draft Rev60 file as the canonical working SRS, says it is unsigned, and keeps dated implementation evidence separate from target requirements. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md:43-49` corroborates the Rev60 baseline. Draft 16's authority statement at `plan/M2_S2_TASK_APPROVAL_DRAFT16_20261114.md:34-39` preserves that boundary and labels Rev67 as a conditional input rather than formal adoption.
- The target-worktree decision ledger rows `DECISIONS.md:521-529` preserve D-194 through D-202. Draft 16's summary at plan lines 36-39 agrees: D-194 keeps the S1a-P2 close-out accepted with its known gap; D-195 retains Rev60 authority; D-196 through D-200 set the S2 operation scope; D-201 adds the late-result guard and output-only `run_revision`/`expected_revision` contract; D-202 changes only the late-result error-code split.
- The canonical Rev60 SRS §31.10(16) at `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2728` sets the new-profile target at 36-120 months and leaves existing trusted profiles aged 121-155 months OPEN-OWNER. Its §9.8 error contract at lines 820-840 requires safe, stable error envelopes with `code`, `message`, `correlation_id`, and `retryable`, with optional retry timing and field errors. Rev60 §21.4 at lines 1668-1673 requires `INVALID_IDEMPOTENCY_KEY` for mismatched key reuse; §9.8 also lists that code under HTTP 400 at line 835. D-200's HTTP 400 choice is consistent with the SRS and current Parent helper; Draft 16's narrow statement that §21.4 itself leaves status open is accurate.

### Draft 15 P2-1: artwork error envelope

Draft 15 identified that its top-level error-code expectation was unsupported on the artwork route (`M2_S2_DRAFT15_COLD_REVIEW_20261114.md:17-25`). Draft 16 fixes this at plan lines 28-30, 123, 145, and 222-231: it plans a safe formatter/mapping only for the existing `POST /api/parent/v1/ai/drawing-understandings` route, asserts the Rev60 §9.8 public envelope and top-level domain code, and requires forwarding the guard before provider or validation handling. It does not claim runtime evidence.

The source confirms the gap and the proposed scope:

- The artwork router is mounted at `/api/parent/v1/ai` and defines the existing drawing-understandings path (`backend/src/sketch2life/interfaces/http/routers/parent_ai.py:64,201-205`).
- The current application formatter handles `/v1/story-runs` and the separately recognized legacy story-revision path (`backend/src/sketch2life/interfaces/http/app.py:170-176,346-407`). The artwork path matches neither; other unmatched Parent paths fall through to FastAPI's generic handler at `app.py:490-491`.
- The current artwork-success guard raises HTTP 409 `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING` in `parent_story_repository.py:572-575`, and the route maps it into `HTTPException.detail` at `parent_ai.py:378-387`. The current public top-level envelope is therefore not established for artwork, as Draft 16 states.
- The legacy story-revision path remains separately source-backed: its predicate is `app.py:170-176`, and Draft 16 audits it separately at plan lines 212-220. The artwork fix does not broaden handling to `/api/parent/v1/*` or replace that formatter.

The D-201/D-202 status-code split is preserved. The existing artwork-success guard keeps HTTP 409 `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING`; the newly required artwork failure/unknown and story-generation success/failure/unknown guards use HTTP 409 `INVALID_STATE_TRANSITION` (D-201/D-202 at `DECISIONS.md:528-529`; plan lines 142-145 and 227-231). Current failure/unknown route handlers can suppress `ParentStoryRunError` or replace it with provider/validation responses (`parent_ai.py:312-338,342-369,460-520`); the draft correctly requires the new guard to be mapped before those branches suppress or replace it. The repository writers also currently lack the new `DELETE_PENDING` guards (`parent_story_repository.py:963-1034,1080-1121,1154-1179`), matching the plan's static inventory at lines 101-106. These are planned changes, not implemented behavior.

### Draft 15 P2-2: trusted legacy-profile ages

Draft 15 identified that AT-10 had turned behavior for existing 121- and 155-month profiles into a required refusal (`M2_S2_DRAFT15_COLD_REVIEW_20261114.md:27-33`). Draft 16 resolves this at plan lines 31 and 185-189. AT-10 accepts only new creates at trusted ages 36 and 120 months; the service's current trusted-profile check is `application/services/parent_story_runs.py:193-207`, which accepts the inclusive 36-120 range. The draft makes no response, refusal, status, eligibility, or no-write assertion for existing profiles aged 121-155 months and explicitly preserves their read/edit/run/archive/delete and grandfather/migration policy as OPEN-OWNER under Rev60 §31.10(16). It selects no clamp, migration, or deletion behavior.

### Regression and scope checks

- The `run_revision` story-run revision remains source-backed and distinct from story revision numbering: Draft 16 uses the existing `story.runs.revision` for the additive response field and cancel precondition (plan lines 110-122; D-201 at `DECISIONS.md:528`). It adds no database column or revision status.
- The S2 route scope matches D-198/D-199: use the existing Parent StoryRun route family; only the Parent cancel route is added by the recorded owner decision; job status uses the existing owner-scoped reads, with no `/jobs` route or new `/api/parent/v1/*` story route (plan lines 54-60; D-198/D-199 at `DECISIONS.md:525-526`). No Story DDL is proposed (plan lines 58-60).
- No Task Approval, allowlist, command ceiling, owner-run gate, or launch is created. The plan says these remain absent and separate at lines 3 and 321-333. Its reference to a future separately approved route/persistence gate at line 129 is conditional future work, not a gate approval or launch. D-194's consumed Gate P2 approval is not reopened (plan line 37).
- The plan does not regress the earlier resolved findings: its change log at lines 28-32 accurately captures the exact-route envelope correction and the OPEN-OWNER legacy-age boundary.

### Input pins and informational mobile inputs

The target branch and HEAD match the requested values. Independently checked the Draft 16 section 9 hard/prefix table and static migration table:

- All 60 carried/current hard or prefix rows matched their listed byte counts and SHA-256 values. This includes the strict Draft 15 plan and review pins; the four historical DECISIONS rows matched their specified first-N-byte prefix hashes, and the current post-D-202 full ledger pin matched.
- All 31 migration source rows matched their listed byte counts and SHA-256 values. This verifies the pinned files only; it is not an Alembic or database-state check.
- The specified anchors matched: Draft 16 plan 90,734 bytes / `3B76A6202E2D34D432891BBA1AE20A70361C0D4682D334D2C53AFAFF94DB10A9`; Draft 15 review 9,502 bytes / `F6413E176111A1A67B0CB2C575BA78DAF18653973352D10EEF3E9A82A78DEF90`; target-worktree DECISIONS after D-202 204,122 bytes / `E70CCC2F7AB6F5C342BB1B836D6CEAB03EB905BF84244B08F01D78AB19A093AE`; SRS authority 4,054 bytes / `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F`; canonical SRS 553,948 bytes / `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`.
- All seven informational `.worktrees/mobile/` rows exist and still match their recorded last-observed sizes and hashes; none changed since observation. Within the permitted claim limits, the mobile client path is `/api/parent/v1/story-runs` (`apps/mobile/src/infrastructure/api/parentWorkflowApi.ts:156-172`) while the server router prefix is `/v1/story-runs` (`parent_story_runs.py:43`); the age-helper test covers 36/120 and 121/155 (`tests/parentFlowV1.test.ts:57-73`); and the listed mobile types, API clients, contract fixtures, and learning-flow fixtures are the documented `run_revision`-affected surfaces. No mobile behavior was treated as requirements authority.

## What could not be verified

No tests, validators, backend commands, database access, migration execution, Docker, network, provider, or Modal command was run. Runtime route exposure and response bodies, authorization execution, create/cancel/replay behavior, the new late-result no-write guards, runtime age boundaries, actual database migration state/applicability, Gate A/B, and the owner-supplied CI context are unverified. The review makes no runtime or deployment claim.

## Review boundary

This is a read-only plan review, not approval, Task Approval, implementation authorization, or launch authorization. Only this report was created; existing worktree changes were preserved. No source, plan, decision, approval, allowlist, command ceiling, gate, or launch state was modified.

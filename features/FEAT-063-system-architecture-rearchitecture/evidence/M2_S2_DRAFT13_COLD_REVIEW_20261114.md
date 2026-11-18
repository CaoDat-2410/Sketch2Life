# FEAT-063 M2 S2 Draft 13 Independent Cold Review

Review date: 2026-11-14

Target: worktree .worktrees/m2-s2, branch feature/feat063-m2-s2, HEAD b740f5033ec71baefd50b2b2ad250b663539f794.

Reviewed plan: features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT13_20261114.md, 51,026 bytes, SHA-256 5E87C70B34B87BE0D722A3D93166159DC000C960DB93A464858169761707ACC0.

## Verdict

**CLEAN** — no actionable findings.

This is an independent read-only plan review. It is not owner approval, a Task Approval, implementation authorization, or launch authorization.

## Review results

### Cancel idempotency and D-200

D-200 clearly supersedes D-199 only for a cancel Idempotency-Key reused with a different request fingerprint. The same key, run, and request still replays the stored HTTP 202 receipt. All other D-199 behavior remains in force. The decisions are recorded at DECISIONS.md:526-527, and Draft 13 preserves the same boundary at plan lines 10-12, 77-80, and 198.

Rev60 §21.4 (canonical SRS line 1670) and owner-selected Rev67 §21.4 (line 1696) both require INVALID_IDEMPOTENCY_KEY for a key reused with a different payload; neither specifies HTTP status. The existing Parent helper raises status 400 with that code on a stored-fingerprint mismatch (backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1327-1352), and the Parent router forwards the status and code as detail.code (backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:81-85). Thus HTTP 400 is supported by D-200 and current source behavior, while the SRS supports the error code but leaves status selection to the owner.

Draft 13 separates same-request replay, same-run/different-fingerprint reuse, and cross-run reuse at plan lines 77-79. The cross-run 400 is specifically an owner decision under D-200, not a status inferred from §21.4. The plan correctly requires a Parent-wide collection receipt scope and makes inability to detect cross-run reuse without additive DDL a stop condition. Existing receipt schema permits CANCEL_RUN and COLLECTION scope (backend/alembic/versions/20261112_parent_story_context.py:195-203; backend/alembic/versions/20261102_story_run_lite.py:484-527). No cancel route currently exists, so these remain future acceptance expectations, not observed runtime behavior.

### BQ-1 context confirmation

The added row at plan line 100 accurately describes the repository path: confirm_context allows INPUT_PROCESSING, SUBJECT_REVIEW, and PREPARATION_REVIEW; records context confirmation and updates revision metadata without assigning run_state or job_state (backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:345-400). The existing record/read mapping and Parent GET response expose context_confirmed, run_state, job_state, retryable, and error_code (parent_story_repository.py:269-271, 382-400, 422; backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:88-113, 228-240; backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-133).

The row and its follow-up at plan lines 100-105 label this as repository/code-reading evidence. They leave subsequent request, dispatch, worker, and provider behavior OPEN or NOT VERIFIED and do not claim runtime or task-database evidence.

### Crosswalk and Parent status reads

The pinned Rev67 crosswalk still has its historical GET /v1/jobs/{job_id} entry at line 28. Draft 13 explicitly marks that entry superseded by D-199 and says S2 uses only the existing Parent active/current and by-ID reads (plan lines 23, 37, 82, and 187). Those routes exist in the Parent router at lines 200-240 and expose the cited status fields. The AI Jobs candidate is defined separately and is not mounted by the normal router composition. The plan does not add a /jobs route.

### Authority, scope, and approval status

Draft 13 keeps Rev60 as the formally canonical, unsigned working SRS and uses owner-selected unsigned Rev67 only as a requirements input for this refinement (plan lines 10, 37, and 175-187; docs/context/SRS_AUTHORITY.md; D-195 at DECISIONS.md:522). Its treatment of D-194 through D-200 matches the decision record at DECISIONS.md:521-527, including the S1a-P2 known-gap status, S1b deferral, conditional Rev67 boundary, Parent StoryRun scope, D-199 cancel/status rules, and D-200 mismatch response.

The plan proposes no additive Story DDL, keeps unavailable database facts NOT VERIFIED, and stops if the existing receipt model cannot support the planned behavior (plan lines 29-37, 86, 169-171, and 213-217). Its header is DRAFT / NOT APPROVED / NOT LAUNCHED, and it grants no implementation, gate, allowlist, command, or launch authority (plan lines 3, 205, and 217). No S2 Task Approval entry was found in the pinned approval record.

## Pinned inputs verified

The worktree root, branch, and HEAD matched the supplied target. Each listed byte count and SHA-256 matched:

| Input | Bytes | SHA-256 |
|---|---:|---|
| Draft 13 | 51,026 | 5E87C70B34B87BE0D722A3D93166159DC000C960DB93A464858169761707ACC0 |
| DECISIONS.md after D-200 | 198,453 | 2A13CE8D79BCC34F2DD3E09119BA20BB80B8AE23A71B105D29EE25CCDEC471B7 |
| Draft 12 | 46,385 | AAC71A6E258585A6CF9B063E75A8FF1E4693C9E23E92065884B4C493B67E0917 |
| Draft 12 cold review | 12,619 | DA29C72DC9B9AC8F225E975AC3A2CACEC373088E72CD39936FCE7935980457F4 |
| SRS authority | 4,054 | 032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F |
| Canonical Rev60 | 553,948 | 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B |
| Owner-supplied Rev67 | 634,291 | B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |
| Parent story repository | 64,452 | 407D2843A93C31BD54202A1E504DE938FB085E67730C199FD4E9B9505E72B832 |
| Parent StoryRun router | 12,698 | 32C707515032FC7BEF08A12D0B1D8E6DD4271FF1B9C55891072BA76E150D6B60 |
| Parent StoryRun schema | 7,309 | C026A1566500EE7B7C2705DFCE6C4E0D0EC7B397E9FE93F11A237A416F768B19 |
| Rev67 crosswalk | 9,184 | 98C3E656B2CDA391C103C21D10E780DF3BB102286E2053360C1690D03FC11891 |

All 44 input-pin rows in Draft 13 §9 and all 31 migration pins in §5 were independently checked against their paths, byte counts, and SHA-256 values. The historical pre-D-199 and pre-D-200 DECISIONS pins were checked as the specified file prefixes. All matched.

## Checks performed and limits

- Read the repository AGENTS.md, root .claude/sketch2life-harness.md, root .codex/sketch2life-harness.md, SRS authority record, D-194 through D-200, relevant Rev60 and Rev67 §§21.2, 21.4, and 21.6 text, Draft 13, the prior Draft 12 cold review, the Rev67 crosswalk, and cited Parent router, repository, schema, composition, and migration source.
- Verified worktree identity and supplied pins; inspected the initial git status before review and preserved all pre-existing changes.
- No tests, validators, backend execution, database access, migration command, Docker, network, provider, or Modal command was run. Runtime route exposure, authentication, cancellation, receipt replay/mismatch, task-database state, and worker/provider behavior remain unverified, as the plan states.

At review start, git status already showed DECISIONS.md modified; untracked M2_S2_DRAFT10, DRAFT11, and DRAFT12 cold-review reports; and Draft 11, 12, and 13 plans. These pre-existing entries were left untouched. After report creation, status also showed an untracked BE_SESSION_CHECKPOINT_20261114.md that was absent from the initial snapshot. I did not create or edit it and left it untouched. This review created only this report.

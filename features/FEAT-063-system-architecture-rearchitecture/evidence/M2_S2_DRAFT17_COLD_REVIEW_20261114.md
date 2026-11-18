# FEAT-063 M2 S2 Draft 17 Independent Cold Review

Review date: 2026-11-14

Target worktree: .worktrees/m2-s2

Reviewed plan: features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT17_20261114.md

This is an independent, read-only plan review from the current worktree contents. The plan must remain DRAFT / NOT APPROVED / NOT LAUNCHED. This report is not approval, Task Approval, implementation authorization, or launch authorization.

## Verdict

**CHANGES REQUIRED** — one P2 finding leaves the planned artwork error-envelope acceptance short of an explicit Rev67 requirement. One P3 finding corrects a bounded informational statement about the FE-lane response type.

## Findings

### P1

None.

### P2

**P2-1 — AT-08 does not explicitly verify the localized message requirement.** Draft 17 line 158 says the planned artwork-route response must have a “safe string message,” while adopted Rev67 Section 9.8 line 853 requires the message to be safe and localized in Vietnamese. Because this is a newly planned route-specific formatter and AT-08 is presented as checking the public envelope, a safe English message could satisfy the written criterion while failing the SRS. Add an explicit Vietnamese-localization assertion to the planned acceptance (and keep the Section 6 alignment status conditional on that criterion).

Evidence: plan line 158; canonical SRS lines 848–857, especially line 853; plan line 329.

### P3

**P3-1 — The informational mobile type row overstates current field support.** Draft 17 line 455 says the FE-lane type and envelopes “consume” the additive run_revision response field. The inspected type at apps/ui-mobile/src/parent/domain/types.ts lines 360–382 defines ParentStoryRunV1 without a run_revision or runRevision property; lines 391–399 define envelopes using that type. The pinned file remains byte-identical to its last observation, so this is not a changed-since-observation or hard-pin failure. Reword the row to say that this current type/envelope is a future reconciliation surface and does not yet declare run_revision.

Evidence: plan lines 449–459, especially line 455; apps/ui-mobile/src/parent/domain/types.ts lines 360–382 and 391–399; plan line 132 already lists the FE files as surfaces to reconcile later.

## Verified review items

- D-203’s boundary is stated correctly in plan lines 5 and 48–54: it supersedes D-195 only for the canonical working SRS choice, leaves D-194 through D-202 in force, and does not approve or launch work. The current authority record and project context point to unsigned v2.7-draft Rev67. Older Rev60 references in historical change notes remain historical.
- The current Rev67 citations inspected in the plan match the cited content: Section 9.8 lines 846–861; Section 21.1 line 1634; Section 21.2 lines 1662–1674; Section 21.4 lines 1694–1696; Section 21.6 lines 1714–1721; the age requirements at FR-PL-25 lines 2470 and 2665, BR-57 lines 2536 and 2681, AC-66 line 2734, and Section 31.10 item 16 line 2756; and Sections 31.10.2, 31.15, 31.16, 31.17, and 31.18 at the cited line ranges.
- The Rev61–Rev67 alignment and deviation entries are substantively consistent with the adopted SRS and the unchanged S2 scope. The table identifies the required pre-story main-activity selection and recovery, context snapshot and lesson pin, image-first sequence, job-status route, cancel/purge/provider-job-cancellation lifecycle, run_revision and idempotency behavior, and safe error envelope. The related Parent flow requirements are recorded as aligned, deviations, or outside S2 scope rather than mislabeled as conformance. P2-1 above is the remaining acceptance detail for the error envelope.
- The prior P2-1 artwork finding is otherwise carried forward correctly: the plan keeps the narrow existing artwork route, preserves the D-202 success-guard code, distinguishes newly guarded late-result paths, and labels the formatter and acceptance as planned rather than implemented. The prior P2-2 age finding is resolved without regression: only new-run ages are accepted/refused in AT-10, and grandfathered completion, legacy-draft access, notices, edit/archive, and migration remain outside S2 acceptance.
- AT-10 is supported by the pinned service and router source. The profile lookup returns the stored current-revision age; service lines 193–207 reject ages outside the inclusive 36–120 range with 422 INVALID_REQUEST; the route invokes the service before repository create at lines 186–197; and the Parent application formatter preserves the status and code in a public error response at app.py lines 350–407. Thus the planned new-run refusal at trusted ages 121 and 155 precedes story, run-input, and CREATE_RUN receipt writes. The plan correctly excludes existing-profile lifecycle behavior.
- Plan lines 3, 48–54, 142, 163, 303, and 361–365 maintain the approval and launch boundaries: no source implementation, DDL, database action, provider or Modal call, Task Approval, allowlist, command ceiling, gate, or launch is authorized. The migration discussion is identified as static file evidence; it does not claim database state.

## Verified pins

The requested worktree identity and supplied anchors matched:

| Input | Verified value |
|---|---|
| Worktree branch and HEAD | feature/feat063-m2-s2; 26a6ff2eeb07b7e46f13a0d33c919169dc532821 |
| Draft 17 | 99,620 bytes; SHA-256 7CDCF2929F9B729490AF282D6AB52F31AB9CDED293504B5B2C33F4530771B63A |
| DECISIONS.md after D-203 | 205,834 bytes; SHA-256 88F182623103B1C3C2CEB5958501817731156D15789634CA225ED12ABA1A54A |
| Canonical Rev67 SRS | 634,291 bytes; SHA-256 B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |
| SRS_AUTHORITY.md | 4,054 bytes; SHA-256 E3783924BCDF0327CCCDA8806773FB4407ED311C7074289D74AB9B9124EAF662 |
| docs/context/SOURCE_REGISTER.md | 113,561 bytes; SHA-256 C22E2E443FF5C8C026914091EF385BBA46E638297D7DD985BA7CD31B765BD16D |
| docs/context/PROJECT_CONTEXT.md | 81,695 bytes; SHA-256 7B30D4B3C72C4774D8658AE389C1AC2D61E276D4199CAE4C7D9B1D931227550D |
| Draft 16 | 90,734 bytes; SHA-256 3B76A6202E2D34D432891BBA1AE20A70361C0D4682D334D2C53AFAFF94DB10A9 |
| Draft 16 cold review | 10,419 bytes; SHA-256 D33D770C42DE9D226B6379B3F6754E8962651C836C309128B128FE0D75794661 |
| Draft 15 cold review | 9,502 bytes; SHA-256 F6413E176111A1A67B0CB2C575BA78DAF18653973352D10EEF3E9A82A78DEF90 |
| Owner-selected Rev67 source copy | 634,291 bytes; SHA-256 B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |

All 72 strict or prefix input rows in Draft 17 Section 9 matched their byte counts and hashes, including five historical DECISIONS.md byte-prefix pins. All 31 migration file pins in Section 5 matched. All six FE-lane informational files exist and match their last-observed byte counts and hashes; none has a changed-since-observation note. The owner-selected Rev67 source copy also matches its separate strict exact-byte pin.

## Not verified

No tests, validators, Alembic CLI, database commands or connections, Docker, provider, Modal, install, or network activity was run. Runtime route exposure, response bodies, authorization, concurrency, cancellation, age-boundary execution, migration applicability, task-database state, and Gate A/B remain unverified. The migration graph remains static source evidence, not a database inventory. The owner-supplied CI status was not rechecked. BE_AI_QUESTIONS_RESPONSE_20261113.md was not read or cited.

## Review boundary

This is an independent read-only plan review, not approval or launch authorization. Only this report was created by this review. Draft 17, source code, SRS, decisions, approvals, and prior evidence were not edited. No fixes were made.

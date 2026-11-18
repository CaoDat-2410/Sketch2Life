# FEAT-066 API alignment roadmap Draft 3 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort set to high by the caller, read-only by instruction; started on the owner's instruction "Review Draft 3". Four scratch diff extracts were written under `tmp/feat066-roadmap-review-d3/` (repository-root scratch, git-ignored).
- **Pin reviewed:** `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT3_20261118.md`, 34,155 bytes, SHA-256 `B29AA77CF7DA443BF047C71DE5F8D1E8DBB6A4D83D6EA0BC4BD487D9E0ED4B86`. Pin check passed; Draft 1, Draft 2 and the Draft 2 review record also matched.
- **What the reviewer did not do (its statement):** no repository file modified, staged, committed, stashed or deleted; no fetch or network use; no test, validator, build, Docker or database use; the gate secret directory not read. Read, Grep, read-only Git, `sha256sum`, `wc` and `sed` only.
- **Verdict:** NOT READY (small corrections) — **P1=0, P2=1, P3=11**. No finding misstates a gate or implies an approval. The P1 and P2 count fell from 5 (Draft 2) to 1.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 finding

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| R3-01 | Whole draft; §4–§5; header | Draft 3 says it keeps every gate of Draft 2 but drops content the handoff still requires: the MGR-0..10 to workstream ID map (requirement A); the distinct-states list; the per-workstream status matrix with "ready-for-new-FE-integration = 0"; the MGR-10 deferral of feedback, inbox and notifications (requirement D). The MGR-2/3/6 review states are absent from §5.2–5.4, and the pin table refers to Draft 2 instead of listing pins. | Re-add a compact ID map, the states line, one status matrix with review pins, and one MGR-10 sentence. |

## P3 findings (summary)

R3-02 `backend/tests/unit/test_be1_bootstrap.py` does not exist on any branch checked; the bootstrap code files are real; other seed sources (`features/FEAT-048-be2-content-publication/src/bootstrap_local_pg.py`, the synthetic-pilot PostgreSQL fixtures) are not mentioned. R3-03 four clauses listed in §0 (§9.6, §9.7, §31.3, the §21.2 class-profiles row) are used nowhere else, so the F-13 disposition is partial. R3-04 the root checkout's 14 modified / 32 untracked are all dirty paths, not only FEAT-081 Bruno changes (about 13 modified and 5 untracked groups are Bruno-related; the rest include FEAT-063 `STATUS.md`, M2 plan drafts and `FEAT-066-brand-logo/`). R3-05 the mobile worktree's 22 dirty paths are 21 staged and 1 unmerged (`UU`) — relevant to O-9. R3-06 the "27-route baseline" is web-wide (three web roles), not a School Manager baseline. R3-07 existing Parent alignment work is not acknowledged (FEAT-081 Parent mobile read-route Bruno requests; `parentApiI2Contract.test.ts` and staged `ParentApi.ts` edits in the mobile worktree); `GET /v1/story-runs/active/current` is listed in the Parent first slice without its "[PROPOSAL]" caveat; the M2 closure says allowed operations still need their own task. R3-08 L5 says "every integrated operation" while the owner asked for Bruno tests for everything; say whether non-integrated and excluded routes get cases. R3-09 L2 plans video-quota read/admission and Billing contract drafts but leaves open whether the owner or the payment teammate builds the Billing ledger and ports; state that the drafts exclude quote, invoice, checkout, callbacks and top-up purchase, and that L2 covers the BE1-side port and read unless O-PAY decides otherwise. R3-10 the conventions slice is placed before every capability slice without noting that the MGR-7 approval excludes `app.py` error-envelope mapping, that the M2 closure's parity reading of `request_id` and `current_version` interacts with it, and that the 8 M2-allowed Parent operations might not need to wait. R3-11 "record the authorization in the scoped approval note" may exceed the authorized write (only the scoped verification-limit note); the seed rule names `be1_acceptance` as a seed database, which is the S-LL test database — reserve a separate name. R3-12 W-LESSON shares four files plus the catalog test with S-LL, not three.

## Verified as correct (reviewer)

All §1 identity facts and counts (BE untracked now 37), the M2 diff numbers, all record and file pins, the 145 Bruno request files and the 136-operation snapshot, the absence of Billing identifiers in `backend/src` and `backend/alembic`, every adopted-copy line citation, the Rev60 1622 to adopted 1649 mapping, the identity of §23.3 and §9.8 in both copies, the M2 facts (151 operations, 9 Parent targets, 8 allowed on the compared dimensions, cancel and assistance blocked), D-209, D-066-62 and D-066-63 quotations, and the location of the Rev69 addenda. F-01 to F-12 and F-14 dispositions are real; F-13 is partial (R3-03). Requirements: A partial, B met, C met, D partial, E met, F met. Payment is excluded and appears only as a dependency; all four roles are covered; no local absolute path was introduced; no approval is implied.

## Not verified (reviewer)

The owner's chat statements; the MGR-8 authorization and its result; whether the disclosed fetch ran as described; the real merge outcome between S-LL and the M2 branch; runtime, test, OpenAPI or database behavior; a full Rev60-to-adopted clause diff; whether the MGR-9 audit counts need refreshing against the reconciled FE base.

## Disposition by the coordinating session

Draft 3 is not edited. The findings are text corrections; whether to write a Draft 4 that addresses R3-01 to R3-12, and whether that draft is reviewed, is the owner's decision.

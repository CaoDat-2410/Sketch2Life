# FEAT-066 API alignment roadmap Draft 4 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort set to high by the caller, read-only by instruction; started on the owner's instruction "Review Draft 4". Two scratch files were written under `tmp/feat066-roadmap-review-d4/` (repository-root scratch, git-ignored): the Draft 3 to Draft 4 diff and an extract of the M2 contract freeze.
- **Pin reviewed:** `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, 42,628 bytes, SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`. Pin check passed; Draft 3, Drafts 1 and 2 and both earlier review records matched their cited pins.
- **What the reviewer did not do (its statement):** no repository file changed; no state-changing Git command; no fetch or network call; no test, validator, build, app or database; the gate secret directory not read. Read, Grep, Glob, read-only Git, `sha256sum` and `wc` only.
- **Verdict:** **READY WITH NOTES — P1=0, P2=0, P3=8.** No finding misstates a gate or an approval. All 12 R3 and all 14 F dispositions are real and correct; the Draft 4 edits introduced no material factual error. Handoff requirements A to F are all met; the owner's five lanes are represented; payment is excluded and appears only as the O-PAY dependency; four roles are covered; no approval is implied; no local absolute path is present.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P3 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| D4-01 | §3 Seed; §11 R3-02 | `features/FEAT-048-be2-content-publication/src/bootstrap_local_pg.py` creates a constrained PostgreSQL test role on a temporary cluster; it loads no data, so "related seed source" mislabels it. | Relabel as a database-role bootstrap, or drop it. |
| D4-02 | §6 L1 Goal against Rules | The goal says the seed serves "gate tests", while the rules require a separate `seed` database; existing PostgreSQL integration tests require a name containing `be1_acceptance` (`test_lesson_library_api.py:90-91`, `test_be1_age_provenance_postgres.py:39-40`, `test_be1_postgres_api.py:4`). | Drop "gate tests", or say those tests keep their own `be1_acceptance` database. |
| D4-03 | §7 DAG and critical path against §4 | §4 lets Phase A (audit, seed design) start now; the DAG draws the L3 audit downstream of the S-LL commit and O-0. | State that the audit's only dependency is the base used to re-count `dev` operations, or move it out of the chain. |
| D4-04 | §1 "Boundary deviation" | "No other network or Git operation was run for Drafts 2 and 3" does not cover Draft 4. | Extend to Draft 4, if true. |
| D4-05 | §3 Parent bullet; L4 Parent row | The M2 closure records that `GET /v1/story-runs/{run_id}` lacks the SRS §9.6 `StoryRunDetailV1` timeline (OPEN-OWNER, does not block integration); the Parent first slice lists "read" without that caveat. | Name it as an L3 register item. |
| D4-06 | §3 Web audit; L3; L4 | Rev52 and the MGR-9 plan are Rev60-based; §0 only names the five BE plans for re-mapping. | Add that Rev52 and MGR-9 are re-checked against the adopted copy in the L3 audit. |
| D4-07 | §4 Phase C; L4 Parent row | Phase C puts Parent after the conventions slice while O-CONV leaves that order to the owner; "starting from the existing staged `ParentApi.ts` work" can read as a settled baseline although that worktree has an unmerged path and O-9 is open. | Mark the order as the default pending O-CONV and O-9. |
| D4-08 | §1A matrix; §12 | The S-LL "AUTHORIZED" label has no qualifier there; §5.1 discloses that it is owner-reported with no repository record (confirmed: no match in CONTEXT, STATUS, TASK_APPROVAL or DECISIONS). | Append "(owner-reported, no repository record, §5.1)". |

## Not verified (reviewer)

The owner's chat statements (D-209 on the M2 branch independently supports the SRS selection); the MGR-8 authorization and its result; whether the disclosed fetch ran as described; the real merge outcome between S-LL and the M2 branch (hunks only confirmed adjacent); runtime, test, OpenAPI and database behavior; a full Rev60-to-adopted clause diff; the contents of the staged mobile edits.

## Disposition by the coordinating session

Draft 4 meets the review bar (zero P1, zero P2). It is not edited after the review; the eight P3 notes are carried as notes. Approval of the roadmap, any edit for the P3 notes, and the commit of the planning records are the owner's decisions.

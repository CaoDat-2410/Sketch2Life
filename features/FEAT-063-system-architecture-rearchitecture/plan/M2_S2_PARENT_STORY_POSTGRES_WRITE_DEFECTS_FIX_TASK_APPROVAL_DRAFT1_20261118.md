# FEAT-063 M2 — Parent story-run PostgreSQL write defects — fix Task Approval Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. It authorizes nothing: no source or test edit, no run, no database or container action, no commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2 (backend co-owned with CaoDat; the owner goes first). Not independently reviewed.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `2bfa1ac09dd91a030870e4afae250c6f4d2e2434` (one commit ahead of the remote; not pushed).
- **Why this task exists:** rehearsal 1 of the PostgreSQL gate G1 (`evidence/M2_S2_POSTGRES_GATE_G1_REHEARSAL_1_RESULT_20261118.md`, SHA-256 `5CDD5FA2F22DEA8EFF1718D10F99623A30449AE94D0C16C51B6BB576116C6D81`) showed that the Parent story-run create fails on PostgreSQL for every caller. The gate approvals forbid source changes, so the fix is a separate task. M2-S2 was closed on offline evidence; this task repairs defects in that closed work and is recorded as such.
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. The defects

All in `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` (69,489 bytes, SHA-256 `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` at HEAD).

| ID | Site | Defect | Evidence level |
|---|---|---|---|
| W1 | `create_run`, lines 103 and 135 | `lesson_pin_snapshot=None` is written to a `JSONB` column. SQLAlchemy binds an explicit `None` as the JSON value `null`, not SQL NULL. The check `ck_story_run_input_lesson_pin_snapshot` requires both lesson-pin columns to be SQL NULL or both set, so the insert is refused and the route answers 503 `PARENT_STORY_RUN_STORE_UNAVAILABLE`. Every create without a lesson version fails | **Confirmed by execution** (rehearsal 1: eighteen such constraint errors in the server log) |
| W2 | `attach_artwork`, lines 632 to 636 | The same explicit `None` for `lesson_pin_snapshot` when the previous input has no lesson pin | By reading; same mechanism as W1; not reached in rehearsal 1 |
| W3 | `_store_pending_idempotency_receipt`, line 1539 | `response_body=None` on a `JSONB` column. The check `ck_story_receipt_final_shape` requires `response_body IS NULL` for a PENDING receipt, so a JSON `null` is refused. The only caller is `reserve_story_revision` (line 1010): story generation could never reserve a revision on PostgreSQL | By reading; same mechanism as W1; **not covered by gate G1** |
| W4 | `attach_artwork`, lines 565 to 609 | Two asset-metadata objects are queued with `add_all`, then a Core insert into `core_asset_lineage` runs without a flush. The product session factory has `autoflush=False` and the lineage foreign keys are immediate, so the insert is refused and the call answers 409 `PARENT_STORY_ARTWORK_CONFLICT` | By reading (two independent cold reviews; library lines cited in `evidence/M2_S2_POSTGRES_GATE_G1_STAGE_B_COLD_REVIEW_R1_20261117.md`); not reached in rehearsal 1 |

No other site in this file passes an explicit `None` to a `JSONB` column, and `add_all` at line 565 is the only ORM add in the file (text search of the file at HEAD). Other modules were not surveyed for the same pattern; that is a recorded limit, not part of this task.

## 2. The change

One source file, four edits, no behaviour change other than the four repairs:

1. Import `null` from `sqlalchemy`.
2. W1, W2, W3: pass `null()` instead of `None` at the three sites, so the column receives SQL NULL. A non-`None` value is passed unchanged.
3. W4: call `self._session.flush()` after `add_all` and before the lineage insert, inside the existing `try` block, so an integrity error is still mapped to 409 by the existing handler.

Not changed: `infrastructure/story_run_lite/tables.py` (setting `none_as_null` on the column types would also work but touches metadata shared with the StoryRun-lite code); any migration; any constraint; any route, schema or error mapping; the session factory.

## 3. Allowlist and ceilings

Edited: `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`, only as section 2 describes.

New: `backend/tests/unit/test_parent_story_repository_postgres_nulls.py` — offline regression tests in the style of the existing `tests/unit/test_parent_story_run_cancel_repository.py` (a recording stand-in session, no database): for W1, W2 and W3 the captured insert statement, compiled for the PostgreSQL dialect, must carry SQL NULL and no bound parameter for the column when the value is absent, and must carry the value when present; for W4 the stand-in must see `add_all`, then `flush`, then the lineage insert, in that order.

Records (new or appended): the approval entry and later result entries in `approvals/TASK_APPROVAL.md`; one evidence report under `evidence/`. No other file.

Checks, with the task interpreter, caches under the repository-root `tmp/m2-s2-pg-defects/`, at most 20 runs each:

- Before any edit: Ruff and Mypy diagnostics located in the source file at HEAD are saved as the baseline.
- After the edit: Ruff and Mypy on the source file — **no diagnostic added** compared with the baseline; zero diagnostics in the new test file; byte-level LF check on both.
- pytest, offline, database variables unset: the new test file, plus the three existing files that exercise this repository (`tests/unit/test_parent_story_run_cancel_repository.py`, `tests/contract/test_parent_story_run_cancel_route.py`, `tests/contract/test_parent_story_run_request_contract.py`), plus `tests/contract/test_parent_ai_late_result_guards.py`. All must pass, none skipped.
- Repository validators and `git diff --check`.

No database, container, socket or provider is used by this task itself.

## 4. Verification on PostgreSQL

The offline tests show the statements are built correctly; they do not show PostgreSQL accepts them. That is shown by **rehearsal 2 of gate G1**, under the rehearsal approval already recorded (owner-run cards, rehearsal mode, a new index and container):

- W1: every item that failed in rehearsal 1 gets past its create.
- W2 and W4: case 08-03p reaches `PREPARATION_REVIEW` through `attach_artwork`.
- W3: not exercised by the gate. It stays "fixed by reading, unit-tested offline, not verified on PostgreSQL" until a test of story-revision reservation on PostgreSQL exists. Recorded as a limit.

The gate's test file, launcher and driver do not change, so their pins stand. The commit changes, so the cards take the new HEAD.

## 5. Sequence

1. Owner approves this draft (optionally after a cold review; Sonnet 5.5 high is enough for an artifact of this size; never Fable).
2. Session records the approval, takes the baseline, makes the edit, writes the unit test, runs the checks, writes the evidence report.
3. Owner instructs one commit (source file, test file, records, and the untracked rehearsal-1 record).
4. Owner removes the rehearsal-1 container with card C5 and runs rehearsal 2 with the new HEAD.
5. Session reads the outputs and reports. Further failures are reported as they are; a further product change needs a new decision.

## 6. Stop conditions

Stop and return to the owner if: the fix needs a change outside section 2; an existing test fails after the edit; a diagnostic is added that cannot be removed without widening the change; the unit test cannot observe the SQL NULL without a database.

## 7. What this task does not claim

- It does not re-open or re-close M2-S2. Whether the S2 closure record needs an addendum is the owner's decision; the facts are in the rehearsal-1 record.
- It does not survey other repositories for the same two patterns.
- It does not make any gate pass; rehearsal 2 may expose further defects in the sixteen items that never ran past their create.

## 8. Approval block (for the owner)

- [ ] Fix task approved as written in sections 2 to 6.
- [ ] A cold review of this draft is wanted first.

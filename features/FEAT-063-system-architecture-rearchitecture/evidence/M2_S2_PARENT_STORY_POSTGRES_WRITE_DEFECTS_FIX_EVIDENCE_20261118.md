# FEAT-063 M2 — Parent story-run PostgreSQL write defects — fix evidence — 2026-11-18

- **Status:** implementation done and checked offline; awaiting the owner. **Not verified on PostgreSQL** (that is rehearsal 2 of gate G1). Nothing committed or pushed.
- **Authority:** approval entry of 2026-11-18 in `approvals/TASK_APPROVAL.md` (owner: "Duyệt") on `plan/M2_S2_PARENT_STORY_POSTGRES_WRITE_DEFECTS_FIX_TASK_APPROVAL_DRAFT1_20261118.md`, SHA-256 `C722A0879885FC52AE6B8C2D3662DC2A2D375B9A2E13A92183F8668E2AC33B1E`. Approval record after that entry: 486,367 bytes, SHA-256 `A0791E2B5352D0F1937D09D17534E226B852B2E9D20B94570874CB05E9832AC9`.
- **Author:** coordinating Claude session (Fable 5.2). Not independently reviewed.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `2bfa1ac09dd91a030870e4afae250c6f4d2e2434`.

## 1. Files

| File | Before | After |
|---|---|---|
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 69,489 bytes, `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` | 69,989 bytes, `5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8` |
| `backend/tests/unit/test_parent_story_repository_postgres_nulls.py` | new | 7,605 bytes, `63C58CF2201966E4C912B6FF924DFD3BD712A5F84590FFBFDCC1DD9C7756A076` |

No other source, test, migration or configuration file was changed. The gate's test file and launcher are unchanged (`BC3FBE62...`, `00FED315...`).

## 2. The change (10 lines added, 4 removed in the source file)

| Defect | Change |
|---|---|
| W1 `create_run` | `lesson_pin_snapshot=lesson_pin if lesson_pin is not None else null()` |
| W2 `attach_artwork` | `null()` instead of `None` when the previous input has no lesson pin |
| W3 `_store_pending_idempotency_receipt` | `response_body=null()` |
| W4 `attach_artwork` | `self._session.flush()` after `add_all`, before the lineage insert, inside the existing `try` |
| Import | `null` added to the `sqlalchemy` import |

Three explanatory comments were added. No route, schema, error mapping, constraint, migration or session setting changed.

## 3. Checks (task interpreter: Python 3.12.10, Ruff 0.17.2, Mypy 1.20.2, pytest 8.4.2; all offline, database variables unset)

| Check | Runs | Result |
|---|---:|---|
| Ruff on the source file, before | 1 | 3 diagnostics (existing) |
| Ruff on the source file, after | 2 | 3 diagnostics; identical to the baseline after removing line numbers: **0 added** |
| Mypy on the source file, before | 1 | 3 diagnostics located in the file (existing) |
| Mypy on the source file, after | 2 | 3 diagnostics, identical to the baseline: **0 added** |
| Ruff on the new test file | 2 | 0 (run 1: one `E501`, fixed) |
| Mypy on the new test file | 2 | 0 (run 1: one `no-untyped-call`, fixed) |
| Byte-level check, both files | 1 | LF only, no trailing whitespace, single final newline |
| pytest: the new file and the four existing files named in the approval | 1 | exit 0, **44 passed**, none failed or skipped |
| `validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check` | 1 each | exit 0 each |

pytest was run with the repository's default options cleared and a per-test report (`-o addopts= -rA`), so every item's outcome is listed in the scratch output.

The new tests (six): create without a lesson pin binds no parameter for `lesson_pin_snapshot` (SQL NULL); create with a lesson pin binds the snapshot; `attach_artwork` asks the session for `add_all`, then `flush`, then the lineage insert, and flushes once; `attach_artwork` without a lesson pin binds SQL NULL; with one, it carries it; the pending receipt binds no parameter for `response_body`.

**Do the tests detect the old behaviour?** Shown for the binding rule, not by running the suite against the old source: an insert built with an explicit `None` for `lesson_pin_snapshot`, compiled for the PostgreSQL dialect, has a bound parameter for that column; with `null()` it has none. The tests assert the parameter is absent. The flush test asserts an event the old code never produced.

## 4. Limits

- Offline only. PostgreSQL acceptance of these statements is not shown here. W1, W2 and W4 are to be shown by rehearsal 2 of gate G1; W3 is not exercised by that gate and remains unverified on PostgreSQL.
- The unit tests use a recording stand-in for the session and replace repository helpers by attribute assignment; they check the statements built, not database behaviour.
- Other modules were not surveyed for the same two patterns.
- The three existing Ruff and three existing Mypy diagnostics in the source file are untouched debt.
- Not independently reviewed.

## 5. Next

One commit on the owner's instruction (source file, new test file, approval record, this report, the fix-task draft, the rehearsal-1 record). Then the owner removes the rehearsal-1 container (card C5) and runs rehearsal 2 with the new HEAD; the gate driver, test file and launcher keep their pins.

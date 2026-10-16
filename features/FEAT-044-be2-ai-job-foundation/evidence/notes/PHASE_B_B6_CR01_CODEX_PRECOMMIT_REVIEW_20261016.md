# B6-CR01 Codex pre-commit review — 2026-10-16

Latest focused re-review: **PASS_CODE_AND_R2_PACKAGE_PENDING_RUNTIME** on runner
`d42d697caec2a2d18e387e536ac140dd98101932feda17907b572d9467e92264` and B6 unit
`b1d3bced3111824cadb60a4ecb5bd676cf7ec103420b13a9ed76966f01dd9e5c`.
The parameter-variant finding below is resolved for these bytes; no further actionable issue
was found in this focused review. This is not runtime closure or commit authorization.
See the re-review addendum at the end. The original finding and its evidence are retained.

Historical verdict on 87f0961f/f07a1f4c: **NEEDS_REVISION**. One P2 remained inside
B6-CR01; no new business card or approval is created. This is a source review, not a commit
authorization or a replacement for the historical B6 closure on manifest `90724453`.

## Reviewed identity

- Branch: `feature/be2-01-ai-job-foundation`; real HEAD `993a26cae78c0a4fe983033f03881838c886b176`.
- Runner: `87f0961f92bb2228e7e7721f8de437f1c705476d6f472379cdbdd92ffb46f648`.
- B6 unit file: `f07a1f4c3c741b5e89ca480c69ee49886baec9b8878281da99c1649bc1f1c3f3`.
- These hashes stayed unchanged through the heldout probe. Claude was actively implementing
  CR01 during this review; later bytes and packages require their own verification.

## P2 — Missing parameter variants still satisfy the completeness gate

`src/run_durable_conformance.py:219-230` builds inventory from function names.
At line 311, `suite_gate` compares `(module, o.function)`, which removes the pytest parameter ID.
As a result, one executed variant represents every variant of the same function.

Heldout reproduction used actual pytest collection: 212 B2–B6 cases and 224 Phase A cases.
The diagnostic generated synthetic passing JUnit for those collected IDs, then omitted only
`test_migrations.py::test_contract_valid_opaque_ids_round_trip_all_five_columns[120]`, retaining
the `[81]` sibling. With only 211/212 B2–B6 cases present, the unmodified runner still reported
**G-01 PASS**, with “0 inventory tests not executed”. G-02/G-03/G-04 also passed.

This was a decision-logic probe, not PostgreSQL/Redis execution. Overall exit remained **2**
because services were absent. It does not invalidate the older full-suite Studio run protected
by its package wrapper. It does show that the new standalone completeness guarantee is not yet
met when a partial parametrized suite is supplied.

Correction: compare the complete expected collected testcase identity, including parameter IDs,
with the executed cases; missing variants must be NOT_RUN. Add a regression that removes one
variant while retaining its sibling. Retain failure/skip precedence and the no-service boundary.

## Direct local checks

- B6 unit tests: **16 passed**. Initial default temporary-directory access failed on Windows;
  rerunning with a fresh ignored workspace temporary directory passed all 16.
- Ruff and mypy on the two changed CR01 files: PASS.
- Harness, architecture, repository security and `git diff --check`: PASS.
- Fresh PostgreSQL/Redis runtime: **NOT_RUN locally**.
- Staged set empty; real HEAD/index unchanged. No code, package, approval or Git mutation by review.

Raw probe, collection, hashes and validation receipts:
`evidence/local/b6-precommit-review-20261016/` (ignored), especially
`gate/pg-gate-review-result.json` and `gate/pg-partial-parameter-actual-main-report.json`.

## Before publication

The old 46-file manifest `90724453` matches only 44 current files: runner and B6 unit tests have
changed. Its runtime PASS and COMMIT_PLAN_V2 dry-run proof apply to the old bytes. Finish the
bounded correction, review the new source, build its pinned package, obtain source-bound Studio
results, update the existing records and regenerate the publication dry run. Include this review
note in the selection and re-count paths. Same Phase B revision 3 scope, 14 cards / WIP 1;
BE2-01 remains IN_PROGRESS and B-12 HANDOFF.

## Focused re-review addendum —2026-10-16

Independent decision probes used actual pytest collection (217 B2–B6 and 224 Phase A cases)
and explicitly synthetic JUnit. Source hashes were identical before/after these probes:

- Omit PostgreSQL variant `[120]`, retain `[81]`: G-01 NOT_RUN.
- Omit one Phase A parameter variant: G-02/B-11 NOT_RUN.
- An unmapped failed case, alone or together with a missing variant: G-01 FAIL, exit 1.
- A real pytest collection error: empty inventory, gate FAIL.
- Complete passing evidence: G-01..G-04 PASS; overall exit 2 because services were absent.

Direct local rerun: 21 B6 unit tests passed; ruff and mypy on both current files passed.
Harness, architecture and repository security also passed. An earlier test invocation overlapped
author edits and is retained separately; it is not the final test result.

The immutable earlier ZIP d0b9f27b/source manifest a75841e0 passed an independent packaging
audit (pins, four ZIP members, two-file delta, scratch reconstruction, shell syntax and exit/skip
guards). Claude then changed the two source files again while completing the follow-up prompt.
That earlier package and its 21-commit dry run do not bind the latest reviewed bytes. Capture
the final bytes in a new package, verify it, obtain source-bound Studio results and regenerate
the publication dry run before real commits. Preserve the old package as history.

Raw re-review receipts: `evidence/local/b6-cr01-codex-rereview-20261016/`:
`gate/gate-rereview-result.json`, `b6-unit-current-junit.xml`, `ruff-current.txt`,
`mypy-current.txt`, and `package/package_and_plan_check.json`.
No PostgreSQL/Redis runtime, source changes, approval changes, staging or commits by this review.


## Codex R2 code/package pre-run review —2026-10-16

**Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME** on 46-file manifest cb527d7f and ZIP 3a9d6ef2. The reviewed source is runner d42d697c / B6 unit b1d3bced. Independent local21 B6 tests PASS; heldout missing B2-B6/Phase A parameter variants are NOT_RUN; unmapped failure with a missing variant yields FAIL/exit1; collection errors fail closed. R2 package audit PASS: 46/46 current hashes, ZIP4 members, two-file delta from90724453, scratch apply/reverse, shell syntax, source-state pins and exit/skip guards. No actionable finding remains in this focused pre-run scope. Studio runtime is NOT_RUN; CR01 remains FIXED_PENDING_RUNTIME_REVIEW, not closed. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md, latest R2 addendum. Next: run only b6cr01r2 on the approved synthetic Studio, review the source-bound results, then refresh publication documents and dry run. BE2-01 IN_PROGRESS, B-12 HANDOFF; approvals and source/packages unchanged by review. No staging/commit/push/merge/deploy.

R2 identities: manifest cb527d7f1739480a6312a0c497f65e1b6aca7ef5acdad28ce93f082e88cc1cca; ZIP 3a9d6ef263572f12083b7cbc8f606e0f7c678d4b3180586519d7b634b474b97c. Package receipt: evidence/local/b6-cr01-codex-rereview-20261016/r2-package/package_and_plan_check.json. At review time the proposed21-commit/124-path plan matched its source/document snapshot. These review-record updates change documentation; refresh the dry run after runtime and final recording.

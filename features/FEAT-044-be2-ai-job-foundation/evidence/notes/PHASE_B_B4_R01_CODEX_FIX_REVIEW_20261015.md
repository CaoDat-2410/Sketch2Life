# B4-R01 independent code and package review —2026-10-15

- Result: **PASS_CODE_AND_PACKAGE_REVIEW**, no additional actionable finding.
- B4-R01 remains **FIXED_PENDING_RUNTIME_REVIEW**; B4 is not closed, B5 NOT_STARTED.
- ACTIVE Q01/B4_FIXED_PENDING_RUNTIME_REVIEW. Existing PhaseBrev3B1–B6 approval applies,
  exactly14cards/WIP1/full-cardDONE0, parent BE2-01 IN_PROGRESS. No new approval/card.
- Codex primary and independent service/tests, SQL/ports/fakes and package reviewers inspected
  the exact six-file correction. Code/package are ready for the user's source-bound Studio run.
  Review changes documentation/evidence only; Claude's backend/package bytes are preserved.

## Reviewed source and scope

Base993a26cae78c0a4fe983033f03881838c886b176 plus dirty source. The previous Studio snapshot
is32-filemanifest444cfead; local corrected source is32-filemanifestf1c6834f. Only the six declared
backend/ports/fake/SQL/test files differ from the previous protected snapshot; other508protected
paths, including approved plans/approvals, remain unchanged. No schema/policy/RQ identity change.

`_sweep` now fixes `now` and page limit for an invocation and advances by the immutable last
row's `(sort time, unique id)` cursor. Every SQL query uses the same ORDER BY and strict row-value
`>` predicate, with LIMIT and no OFFSET. The fake implements the same comparison. Deferred rows
no longer stop traversal; changes removing already-processed rows cannot shift an offset past
later work. Each later invocation starts afresh. Existing handler locks/CAS/fences remain intact.
Positive approved timeout/backoff values keep newly created work outside the fixed sweep window.

The executor's reconstructed exact previous444cfead source ran the five new offline tests:
2failed/3passed; corrected source5passed. The two failures exercise deferred-page starvation and
all-deferred traversal. The other three are protective regressions, not before-failure proof.
This is **DIRECT_LOCAL_FAKE_SERVICE_RUN**, never PostgreSQL evidence.

## Independent verification

| Check | Actual result |
|---|---|
| B4 unit suite | **18passed**,exit0 |
| Additional service/fake probe | PASS: tied timestamps, multiple deferred pages before healthy work, restoring blocked scopes next invocation, all-deferred exact page multiple terminates |
| SQL offline probe | **4/4PASS**: actual three UoW queries compile using PostgreSQL dialect, cursor binding/tuple/ORDER BY/LIMIT and row mapping; tied-key fake traversal |
| Default fixture runner | **20PASS/0FAIL,215checks/0failed**,exit0; digest d17f58a3 unchanged; optional HTTP NOT_RUN1 |
| Source/package hashes | All32currenthashes match f1c6834f; five package digests match the executor record |
| Delta / ZIP | Exactly6deltafiles; reverse-check exit0; ZIP exactly4byte-identical operator members |
| Test collection | **104cases**:2+6+11+18+4+10+21+14+18 |
| Existing host proof |8cases PASS, consistent with runner/receipts; real scratch Git and Docker stub only; no inner runtime test |
| Runtime on corrected source | **NOT_RUN / REQUIRES_STUDIO_RUN**:64PG/Redis cases, including2newSQLregressions |

The executor additionally reported PhaseA223PASS/1localPillow skip and40offlineB2–B4PASS/64runtime
skips, lint/types/validators PASS. Raw PhaseA receipt identifies the skip as missing Pillow at
test_ai_job_polling.py:180; the executor's POSIX-only explanation was incorrect and is corrected
in the evidence note. Historical raw output is preserved. No package/source change is required.

Package/runner inspection confirms exact old-to-new transition or corrected verify-only retry,
refusal of foreign source/tampered delta, import pinned to the worktree, suite/log/skip error
propagation and Docker125 propagation. None of these host checks proves Redis/PG runtime.

## Exact package approved for the next test step

Ignored evidence/local/b4r01-studio-package-20261015/:

| Item | SHA-256 |
|---|---|
| Previous manifest |444cfeadd3d7d0d0e1f23663b576270f46692e870fe532071f6cf025ffd9ff01|
| b4r01_delta.patch |56af4fbd78a8dbcdaa4b9c8916fae8626324df775e396776c75dd55f5e28097b|
| b4r01_source.sha256 |f1c6834f41dc798fe4475509b7d4b9c8c578ebfd15f34ff07f72f2d4bf24aeb4|
| run_b4r01_on_studio.sh |c3ef682ff6ba9926951cdc9420e41cfd2c81b611acd17e09fde8ef3ff6d01813|
| be2-b4r01-studio-20261015.zip |a7afd57aec808458cf276c8187111ffa7321b0332af8ce7e3ea0764c22085b62|

## Next and handover correction

The user runs this ZIP on the existing synthetic Studio sketch2life-backend-test according to
ignored evidence/local/claude/prompts/B4_R01_STUDIO_RUN_20261015.md. No commit/push is needed.
Capture the source/hash header, new regression results,104B2–B4PASS/0skip,224PhaseAPASS/0skip,
fixture exit0 and every suite/log/outer/operator exit. Attribute supplied output USER_REPORTED_REMOTE.
Then perform focused closure review before B5. Previous97PASS belongs to444cfead, not this fix.

Updated handover top/table/latest§S, bootstrap, context/tracker/status/localINDEX to distinguish
localf1c6834f from last-reportedStudio444cfead and prevent reimplementation. Older§Q/§R remain
historical checkpoints. Operator prompts/handover stay Git-ignored. B2/B3/RT01 stay closed.
OwnerFence remains ASSUMED_CONTRACT; B5/B6/provider/realownerintegration remain deferred.

Local primary/peer receipts and protected520-path snapshot:
evidence/local/b4r01-codex-review-20261015/. Final harness/security/architecture/diff checks exit0;
all520protectedpaths and the real Git index remain unchanged, operator files and ZIP Git-ignored.
No backend/package/approval/approved-plan edits,
installs, service recreation, provider calls, staging, commit, push or deploy during review.

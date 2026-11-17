# FEAT-064 chain — GOAL A2 revision 3 plan

- Status: **DRAFT / AWAITING OWNER REVIEW**. This is a planning revision, not an implementation approval or launch prompt.
- Chain order: **A2 → independent review ACCEPTED → separate owner launch for B1 → independent review ACCEPTED → separate owner launch for B2**. Stop at each boundary. Approval of this plan does not authorize B1 or B2.
- Goal: reconcile and finish only the still-open A2 evidence for T2C (BE1 facts/source/admission and digest pin) and T7b (same-transaction owner fence), then stop at `A2 XONG-CHƯA REVIEW`.
- Authority: `OWNER_DECISIONS_G3G4_V4_20261101.md` §1 and §3 D4/D5; A2 REV2; the approved GA2 T2C/T7b plans and fake-owner addendum; current pause report and checkpoint. Their hashes are recorded below.

## 1. Current planning baseline (read-only)

| Item | Observed value |
|---|---|
| Branch | `feature/feat063-be-foundation` |
| HEAD | `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9` |
| Index | Clean |
| Merge in progress | No |
| Working-tree entries | 58; preserve every entry unless a later owner launch explicitly includes its exact path |
| Hash snapshot | `.claude/handoff/snapshots/FEAT064_CHAIN_BASE_20261103T165013/manifest.json`, SHA-256 `249C34A8E3FA6B1C98076AEC629E02F4158A5F19905378EBEBF6B81F4AEB4D7C` |
| Current A2 state | `TẠM DỪNG / XONG-CHƯA REVIEW`; no independent acceptance is recorded |

The snapshot records all 58 status entries, their working-tree hashes and byte lengths. It has no staged paths. Before an A2 launch, create a fresh A2 snapshot with byte copies of every dirty allowlisted file as V4 requires; do not rely on a hash-only snapshot for reconstructing diffs. Reconfirm the branch/HEAD and the exact current status then. If any unlisted path would need modification, stop and ask for a new scope.

### A2 working-tree comparison

Against `A2_PAUSED_20261102T164551/manifest.json`, 52 of the 54 current A2-relevant paths are byte-identical. Two A2-relevant files changed and their origin is not sufficiently established for this plan: `backend/tests/contract/test_openapi_contract_catalog.py` and `backend/tests/integration/test_be1_postgres_api.py`. Preserve both as outside-scope baseline; do not attribute their diffs to A2 or edit them. The first contains a pilot-profile lookup catalog addition; the second contains consent/rate-limit test changes. Across the full manifests, `docs/context/SOURCE_REGISTER.md` is a third changed path; it is outside A2 and must also remain byte-identical to the new launch snapshot. Three current entries absent from that A2 snapshot are outside A2: the two FEAT-063 StoryRun Lite handoff documents and `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/scripts/`. Preserve them.

The following last-recorded A2 results are historical evidence, not fresh results for this HEAD:

- Focused T2C unit modules: 34 passed.
- First full PostgreSQL module run: 68 passed, 4 failed because the four acceptance cases reached `AssistanceService.submit()` and the pilot SQL repository's `find_cache()` intentionally raises `NotImplementedError`.
- After the test helper used the real `_resolve_for()` and SQL UoW path, the focused acceptance assertions passed, but teardown raised a foreign-key violation while deleting an `ai_jobs.job` row still referenced by `ai_jobs.attempt`. Fixture cleanup rolled back. Possible prior synthetic rows were not inspected or manually removed.
- Ruff check passed; format check reported one pre-existing-to-that-reviewfix file needing formatting. Repository validators and `git diff --check` passed at the pause checkpoint. **Strict mypy and the pinned offline runner after review-fix were NOT RUN.**

Do not report these historical counts as current acceptance. In particular, do not weaken assertions, route the test through a fake cache, or clean database rows that the current test run did not create.

## 2. Work in this goal

### A2-R0 — launch reconciliation and safe DB gate

1. Recompute the V4, A2 REV2, prior A2 review-fix plan, T2C, fake-owner addendum, T7b, pause checkpoint, and current report hashes; compare them to the values in §6. A mismatch stops the goal before tests or edits.
2. Capture a fresh status/hash/byte-copy baseline for every dirty path in the proposed allowlist. Keep the two unattributed test diffs and all other paths byte-identical.
3. For any PostgreSQL case, use only a database explicitly provisioned as task-owned, disposable, and loopback-local in the separate launch. Verify host is loopback and the database identity/name matches the launch approval without printing the connection string. No database creation, reset, drop, truncate, broad cleanup, or cleanup of historical/leaked rows. If ownership or identity is unclear, mark PostgreSQL `NOT RUN / BLOCKED` and continue only independent offline checks.

### A2-R1 — reproduce the outstanding test-owned teardown failure

- First run the exact focused PostgreSQL acceptance test in the safe database gate above and record whether the job/attempt foreign-key teardown error still reproduces.
- If it reproduces, the only planned code change is in `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`: cleanup may delete only the exact `attempt_id` and `job_id` created by that test, deleting the referencing attempt before its job, in a transaction whose rollback/commit result is asserted. Never query-and-delete by organization, table-wide predicate, or an ID not captured by this test.
- Re-run the focused test after the change. If the test's own rows cannot be uniquely identified, if another row blocks cleanup, or if the failure has a different cause, stop without cleanup and report the measured blocker.
- If the failure does not reproduce, do not make a speculative cleanup change; record the fresh result and continue to the remaining verifications.

### A2-R2 — resolve, or explicitly block, the SQL acceptance path

- Run the current full `test_be1_synthetic_pilot_postgres.py` module after R1, plus the approved focused unit and caller-compatibility set.
- Do not reintroduce the historical `find_cache()` bypass. If the full module again reaches that unsupported method, stop that acceptance item as `BLOCKED`; diagnose from the trace and request a separate owner-approved plan if product code or another file would need changing. Do not alter `ai_jobs` source, repository ports, schema, or migration under this plan.
- Confirm the A2 contract still holds: scoped, single-statement/REPEATABLE READ facts; purpose equals session `configuration["purpose_ref"]`; synthetic evidence never becomes legal consent; T4 export and T5 receipt bind the source; digest pin and recomputed `ResolvedFacts` agree; old `members()` callers with no scope retain behavior; T7b checks the digest and epoch on the same connection, with bounded sorted `FOR SHARE` locks and the documented phantom-insert limitation.

### A2-R3 — finish static/offline evidence and stop

- Run the pinned offline GA2 runner copied byte-for-byte into a new writable snapshot directory, using its approved arguments/add-ons; never run it from a prior snapshot that it may overwrite.
- Run strict mypy for the exact A2 changed files and separate any already-recorded baseline error from new errors. Run Ruff with `backend/pyproject.toml`, the three repository validators, and `git diff --check`; record each actual exit status.
- Append a new A2 report and ledger checkpoint, and create a new `GA2_*` snapshot including the runner copy, exact command, output/exit code, hashes, and allowlist diff. Do not rewrite prior reports or approvals.
- End at `A2 XONG-CHƯA REVIEW` (or `A2 TẠM DỪNG/BLOCKED` if a gate fails). Do not start B1 until an independent reviewer records **ACCEPTED** and the owner sends a separate B1 launch prompt.

## 3. Exact proposed allowlist for A2-R1–R3

Implementation/test correction:

- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` — only the test-owned attempt/job teardown ordering described in A2-R1.

Read-only regressions (do not edit unless a separate exact approval is recorded):

- `backend/tests/unit/test_assistance_t2c_adapters.py`
- `backend/tests/unit/test_t2c_digest_pin.py`
- `backend/tests/unit/test_be1_owner_fence_t7b.py`
- `backend/tests/unit/test_sketch_generation_chain.py`
- The assistance/vision caller modules named by the pinned A2 REV2 and approved GA2 runner.

New task records after a separate A2 launch approval:

- This plan, one new A2 continuation report, append-only entries in `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` and `status/PILOT_GOAL_LEDGER_20261101.md`, and one new ignored `GA2_*` snapshot.

No other source/test path is authorized by this revision. In particular, no changes to either unattributed test diff in §1, `backend/src/sketch2life/services/ai_jobs.py`, AI Jobs ports/contracts/tables/repository, migrations/schema, router/composition, or any file outside this list. If the proven remaining defect requires one of those, stop and propose a separate plan.

## 4. Acceptance and stop conditions

| Check | Acceptance evidence |
|---|---|
| Teardown reproduction | Fresh focused result states reproduced/not reproduced; no cleanup before reproduction. |
| Test-owned cleanup (only if reproduced) | Exact test-created attempt deleted before exact test-created job; no foreign-key failure; assertions unchanged. |
| T2C/T7b | Focused tests and PostgreSQL integration tests pass on the approved task-owned loopback DB; if DB gate fails, mark DB acceptance NOT RUN/BLOCKED. |
| Compatibility | Named legacy no-scope `members()` callers and `test_sketch_generation_chain.py` run unchanged. |
| Static/offline | Strict mypy, pinned offline runner, Ruff, three validators, and diff check have real recorded outputs; no result is inherited from an earlier snapshot. |
| Scope | Final diff contains only the one approved test file change plus named new records; unattributed and unrelated baseline paths retain their launch hashes. |

Any out-of-allowlist change, unknown DB identity, test failure outside the reproduced cleanup issue, new product-code defect, ambiguous test-row ownership, or need to change an assertion is a stop. Preserve the worktree and record `NOT DONE/BLOCKED`; do not continue by broadening scope.

## 5. Approval required before implementation

Owner must review this plan, then issue a separate A2 launch that pins this file's SHA-256, current branch/HEAD, a fresh baseline snapshot, exact allowlist, test command set, and the task-owned loopback database identity (if PostgreSQL is to run). The launch must explicitly authorize any test-file edit. This plan does not modify historical A2 approvals and does not authorize implementation by itself.

## 6. Inputs and hashes checked while preparing this draft

| Input | SHA-256 |
|---|---|
| `OWNER_DECISIONS_G3G4_V4_20261101.md` | `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6` |
| `CODEX_GOAL_G3G4_A2_20261101_REV2.md` | `47CEA408AA9A4984C2EFD9E71A2EF0CDB2DF02C46E56FD7281086EBAE574AE10` |
| `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` | `A6DF8F6525A939E635EBFD4D2288BD8CBD7BCFB735EC1C45C042D2A37F40E69D` |
| `CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md` | `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C5063657` |
| `T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_GA2_20261102.md` | `1B1EB635FEA67D6EFCD19B3506F83538454D5A75012742F54B2CA0EA15086774` |
| `T2C_FAKE_OWNER_SCOPE_ADDENDUM_GA2_20261102.md` | `E04F41D3F765C24DDB1E59A36ED2E24A0287A40AD8CC5FF1215B054287E15857` |
| `T7B_OWNER_FENCE_UOW_PLAN_GA2_20261102.md` | `FDA943CE81C207F51616032A05AC1FB976934178A019BDCEF95DA73478A40C46` |
| `A2_REVIEW_FIX_PLAN_GA2_20261102.md` | `BAF5E76B5E11F05F19DD1863BD0F8BBCDE981729F76C59B392CFD386A9A5B450` |
| `A2_PAUSE_CHECKPOINT_GA2_20261102T164551.md` | `24A6CFEF58AD532330309C7129B8370145437E1E04A6645A232A0E719B3D50A7` |
| `A2_REVIEW_FIX_PAUSE_REPORT_GA2_20261102.md` | `3882D31C8E06B51A95E38B5C76D42853124D802AC2C85632F394E99B67786BDE` |

The old A2 REV2 and its implementation approvals remain historical. This revision does not claim their old HEAD pin is current.

# FR-C-08 Parent StoryRun lifecycle — implementation report (coordinator checks)

**Status: IMPLEMENTED IN THE WORKTREE / COORDINATOR CHECKS RUN / OWNER RUN 20261119-110418
PASSED (Docker, S3Mock deviation; §5b) / IMPLEMENTATION REVIEW R1 NEEDS REMEDIATION (0 P1, 2 P2,
9 P3), REMEDIATION APPLIED (§10) / AMENDMENT-1 OWNER RUN 20261119-130537 DONE, 0 FAILURES NEW
AGAINST BASE (§10.3) / REVIEW R2 ACCEPTABLE WITH NOTES (0 P1, 0 P2, 5 P3), FIXES APPLIED (§10.4) /
FINAL OWNER RERUN 20261119-134002 PASSED ON THE FINAL TREE (§10.5) / ACCEPTED BY THE OWNER ON
2026-11-19 WITH RECORDED DEBT (§10.6) / ONE TASK COMMIT ON THE OWNER'S WORD, NOT PUSHED.**
**Date:** 2026-11-19.
**Worktree and branch:** `.worktrees/frc08`, local branch `feature/feat063-frc08-lifecycle`,
base `03342207ab10379e6c53449274edaf4d9bcf60e4`, docs commit `d6bdfe3a`. Nothing is staged except
`git add -N` (intent to add) on the N paths; nothing is committed or pushed.

## 1. Authority

- Approval: `approvals/TASK_APPROVAL.md`, entries "FR-C-08 — Parent StoryRun lifecycle:
  implementation approved (Parent-only first slice)" and "... implementation LAUNCHED by the
  owner" (2026-11-19). The uncommitted launch append is kept unchanged.
- Allowlist Draft 13 (26,692 bytes, `82CB6E41…6E2B`), Contract Draft 11 (17,168 bytes,
  `A209D097…6737`), DTR Draft 6 (40,580 bytes, `E4B25542…B30C`), Core port design Draft 6
  (21,768 bytes, `C8EDD923…A86A`): all four re-hashed before the first edit and equal to the
  approval pins. FEAT-063 `DECISIONS.md` 260,722 bytes, `6F6DC329…E9AE0`, equal to the pin.
- Decisions D-214 to D-218. No decision beyond them was needed or taken.
- Amendment 1 (`approvals/TASK_APPROVAL.md`, last entry, "amendment 1 to the allowlist and the
  command ceiling", 2026-11-19; file 520,644 bytes, SHA-256 `F715721B…639A5A` when read): adds
  `backend/tests/unit/test_synthetic_eligibility.py` to E for one edit, adds the whole
  `tests/unit` + `tests/contract` comparison with the base to the coordinator ceiling, and adds
  three PostgreSQL suites to the owner-run ceiling (§10). It is the only widening of scope.

## 2. Pin check before the first edit

A local script (`tmp/frc08-impl/verify_pins.py`, git-ignored) parsed Allowlist Draft 13 §2-§4
and compared bytes and SHA-256 of every row with the worktree: **35 E and 30 H rows equal**, no
difference; **all 15 N paths absent**. HEAD~1 = `03342207…`, so no pin needed recomputing.

## 3. What was implemented (map to the documents)

| Area | Paths | Document rule |
|---|---|---|
| Cancel/delete command transaction: lock, replay, revision (cancel), state, then run `DELETE_PENDING` + lock released + revision/version +1, Parent aggregate upsert, outbox event (insert-if-absent, deterministic id), accepted audit (insert-if-absent), receipt whose body is the projection | `parent_story_repository.py`, `story_run_lifecycle.py` | DTR §6.1, rule 6; Contract §3.1-§3.2 error order |
| Eligible states: cancel = 13 SRS + 2 extensions; delete = COMPLETED, FAILED, ABANDONED | `story_run_lifecycle.py` | Contract §3.1-§3.2; D-214 item 1; D-216 item 4 |
| Projection before any input/profile access; GET union; replays of create/context/subject/script of a purged run without fingerprint check; cancel/delete replays keep it and return the stored body (pre-existing M2 cancel body → current projection) | repository, routers, schemas, port | DTR §6.5; Contract §3.3-§3.4; D-218 A-3 |
| Fence: `_live_run` predicate `run_state NOT IN ('DELETE_PENDING','DELETED')` on every Parent writer; the three S16 writers refuse both states and check the row count; `read_current_input` → 409; artwork route re-checks state before the first `put_object` | repository, `parent_ai.py` | DTR §7; port design §7 |
| `DELETE /v1/story-runs/{run_id}` (202, lifecycle envelope) in the existing router; cancel and delete read `Idempotency-Key` with `parse_idempotency_key` (optional header, no length constraint, 1-128) | `routers/parent_story_runs.py` | Contract §3.1-§3.2, §3.6; D-217 item 7 |
| Response schema: 20-state enum; `ParentStoryRunLifecycleEnvelopeV1` / `ParentStoryRunLifecycleProjectionV1`; cancel envelope replaced (alias kept) | `contracts/schemas/parent_story_runs.py` | Contract §3.4; D-218 A-3 |
| Schema delta and one migration on branch `frc08_lifecycle`, `depends_on` the Story head; downgrade guard; ORM NULL default for `owner_scope_ref` | `alembic/versions/20261119_frc08_lifecycle_scope.py`, `core_models.py`, `be1_models.py`, `story_run_lite/tables.py`, `ai_jobs/sql/tables.py`, `alembic/README.md` | DTR §5, §9, rule 1 |
| Core ports: optional organization + scope on Core records; additive scope-keyed reads; asset purge, upload close, outbox lease cycle, receipt store, audit writer, notice port | `core_foundation.py`, `core_store.py`, `outbox.py` | DTR §5.8; port design §5 |
| Core asset purge (closure across any scope, all or nothing, pre-check, sweep, locked row delete, verify, review report) and upload close | `core_lifecycle_store.py` | port design §5-§6 |
| Story lifecycle adapter: step-4 plan/purge (children, S10 NULLs, CANCEL_RUN body rewrite, fingerprint tombstones), `finalize_deleted`, cross-run asset answer, reconciliation query/insert | `story_lifecycle_store.py` | DTR §5.1 T2, §6.2 steps 4-5, §6.4 |
| BE1 consumer: steps 0-6, token rule T1-T7, `limit = 1`, 900 s lease with renewal before each step and between step-3 calls, 300 s step deadline, CAS on every receipt update (zero-row inside an effect raises), defer 30·2ⁿ capped 3600, bound 10 → exception (inserting a missing receipt), retained plan → exception with nothing deleted in Core; SQL receipt store and audit writer | `be1_lifecycle_consumer.py` | DTR §5.1, §6.2-§6.3, §8 |
| AI Jobs: `CancellationNotice` optional organization, scope, `story_run_ref`; Parent notice matches no job; insert-if-absent Parent notice store | `ports/ai_jobs.py`, `services/ai_jobs.py`, `sql/repository.py`, `fakes.py` | DTR §5.2 |
| Storage `list_keys` (all pages, fail closed) | `object_storage.py`, `s3_compatible.py`, lesson-library fake | port design §5.3 |
| Composition root and reconciliation tool, both refusing any target outside the §7 allow-list | `tools/run_be1_lifecycle_consumer.py`, `tools/frc08_reconcile_delete_pending.py` | Allowlist §3, §7 |
| OpenAPI: 201/200 descriptions of GET and the four replaying operations; cancel and delete stay uncatalogued | `openapi_contract.py`, catalog tests | Contract §3.7 |

## 4. Coordinator checks (Allowlist §7 items 1-4) — actual results

All run from `backend/` of the worktree (validators from the worktree root), PowerShell,
`PYTHONPATH=<worktree>\backend\src;<worktree>\backend`, the backend virtual-environment interpreter
(`<repo>\backend\.venv\Scripts\python.exe`); caches and outputs under `tmp/frc08-impl/`
(git-ignored). No database, storage, provider or network target was used. The table gives the
**final** results after the review-R1 and review-R2 fixes (§10.2, §10.4); the first-pass figures
are kept in §10.

| # | Command | Exit | Result |
|---|---|---:|---|
| 1 | `ruff check` on the 34 changed E Python paths (incl. the amendment-1 path), each compared with `git show HEAD:<path>` | 1 | **0 files with a changed count** (the findings are the pre-existing E501, I001, SIM105, UP035, UP012) |
| 1 | `ruff check` on the 14 N Python paths | 0 | All checks passed |
| 2 | `mypy` (MYPYPATH=src) on 25 changed src modules (21 E incl. `openapi_contract_amendments.py` unchanged + 4 N) | 1 | 32 errors in 8 files; baseline (21 E modules before any edit) 33 errors in 8 files. **0 new**: the two `run_state` errors of the routers are baseline errors whose message lists the wider enum; one baseline error (`ParentStoryRunCancelEnvelopeV1.request_id`) is gone |
| 3 | `pytest` on the 17 E/N unit and contract files (incl. `test_synthetic_eligibility.py`) and the 7 offline tests of `tests/integration/ai_jobs/test_migrations.py` (lines 116-259) | 1 | **488 tests: 487 passed, 1 failed, 0 skipped** (junit `tmp/frc08-impl/r2_junit.xml`, SHA-256 `4908E79D…2B0A76`, after the review R2 fixes). The failure is `test_openapi_schema_catalog_mapping.py::test_catalog_source_declares_every_key_exactly_once` (`ValueError: unsupported catalog item mutation`), which **fails identically at the base** (baseline run before any edit and review R1 row 4) |
| 3a | amendment 1: `pytest` on the whole `tests/unit` + `tests/contract` suites, worktree vs the read-only base export, compared by failing test id | 1 / 1 | see §10.2 and §10.4: **0 failures new against the base** (8,407 vs 8,205 tests, 83 vs 83 failing ids) |
| 4 | `tools/validate_harness.py` | 0 | HARNESS_VALID |
| 4 | `tools/validate_repository_security.py` | 0 | passed (a first run flagged `PARENT_COMPLETED_TOKEN_PATTERN = …` as a secret-like assignment; renamed to `PARENT_COMPLETED_RESULT_PATTERN`, then passed) |
| 4 | `tools/validate_architecture.py` | 0 | ARCHITECTURE_VALID |
| 4 | `tools/validate_skeleton.py` | 1 | SKELETON_INVALID: "active Android app must retain applicationId com.sketch2life.mobile". No file under `apps/` differs from HEAD (`git diff --stat HEAD -- apps` empty); not caused by this change |
| 4 | `git add -N` on the 14 code/test N paths (and on this report) | 0 | intent-to-add only |
| 4 | `git diff --check` | 0 | clean |

## 5. Owner-run items (Allowlist §7 items 5-7) — command files (results in §5a, §5b)

One PowerShell command file, `tmp/frc08-impl/OWNER_RUN_FRC08.txt` (git-ignored; 12,212 bytes,
SHA-256 `70BEDF3B…D9CE`, parse-checked with the PowerShell parser: 0 errors, not executed). It
creates a fresh PostgreSQL cluster (`initdb`, `listen_addresses=127.0.0.1`, port 55458, database
`sketch2life_frc08_lifecycle`) and a fresh MinIO (127.0.0.1:59458, throwaway generated
credentials, new bucket `frc08-lifecycle-<stamp>` checked empty), clears every variable that could
point elsewhere (`S1A_P_ALEMBIC_DATABASE_URL`, `PG*`, `AWS_*`), runs the tools' fail-closed guard on
the effective Alembic URL before each step, then runs item 5 (`upgrade heads`, `downgrade
frc08_lifecycle@base`, `upgrade heads`, with `alembic_version` printed after each), item 6 (the
integration test) and item 7 (one synthetic pre-existing `DELETE_PENDING` run, then the
reconciliation twice), and stops both servers. The owner fills the PostgreSQL bin folder and the
MinIO binary path.

Owner decision (same day): the run uses Docker instead. Second command file
`tmp/frc08-impl/OWNER_RUN_FRC08_DOCKER.txt` (13,797 bytes, SHA-256 `0BB88DAD…66A9`, parse-checked:
0 errors, not executed). It starts two new containers named `frc08-pg-<stamp>`
(`postgres:17-alpine`, 127.0.0.1:55458) and `frc08-minio-<stamp>` (127.0.0.1:59458/59459) with
per-run credentials passed by variable name, refuses if either name exists or a port is in use,
keeps the same guards and steps, stops at the first failing step, records exit codes and log
SHA-256, and never stops or removes any container (its own two are left for the owner). Its only
Docker calls are `version`, `ps -a --filter`, `image inspect` and the two `run` commands.

**Owner-approved deviation from Allowlist §7 (2026-11-19):** the MinIO images could no longer be
pulled, so the Docker command file was edited in place to use Adobe S3Mock (`adobe/s3mock:4.10.0`,
container `frc08-s3mock-<stamp>`, only `127.0.0.1:59458` → HTTP 9090, no volume, no credentials
passed; S3Mock ignores them and boto3 still gets throwaway values) as the local S3-compatible
store. The file now starts by removing only the leftover container `frc08-pg-20261119100546` of the
previous attempt (`docker rm -f -v`, that one name, checked against `^frc08-pg-[0-9]{14}$`). Its
Docker calls are `ps -a --filter`, `rm -f -v` (leftover only), `version`, `image ls -q` and the two
`run` commands. Version after the edit: 15,605 bytes, SHA-256 `6A3EF39A…CD66`, parse-checked
(0 errors), not executed. No code change was needed for path-style addressing: `build_s3_client`
already sets `addressing_style = "path"` whenever an endpoint URL is given, and the bucket step
sets it explicitly. The integration test's empty-bucket check now also looks at `Contents`
(S3Mock may omit `KeyCount`); the test file is now 17,708 bytes, SHA-256
`BF21E9F85AB61C4B618CCD2EC5DC01773833F65556D5215A3C46E3F91DD82ADF` (supersedes the §8 row).
S3Mock is a test double: its ListObjectsV2 paging, delete and error behaviour are not evidence of
MinIO or AWS S3 behaviour (port design §13 stays open for real S3/MinIO).

## 5a. Owner run 20261119-103216 (Docker, PostgreSQL 17 + S3Mock) — result and fix

Run folder `tmp/frc08-impl/owner-run/20261119-103216/` (git-ignored; `SUMMARY.txt` SHA-256
`433391BF…AC3B9A`, `item6_junit.xml` SHA-256 `0500AFD6…07D8CC`). Owner-run; the coordinator did not
connect to any database or storage and read only the log files.

| Step | Exit | Result |
|---|---:|---|
| 1a-1f containers, readiness, empty bucket, guard | 0 | all passed |
| 5a `upgrade heads` | 0 | `alembic_version` holds `20261119_frc08_lifecycle_scope` (and not `20261112_parent_story_context`) |
| 5b `downgrade frc08_lifecycle@base` | 0 | the row went back to `20261112_parent_story_context` |
| 5c `upgrade heads` again | 0 | as 5a |
| 6 integration test | 1 | **7 tests: 6 passed, 1 failed** (schema/CHECKs, cancel end to end with a completed token, delete without artwork, retained-asset exception, downgrade guard and receipt CAS passed) |
| 7 reconciliation | not run | the run stops at the first failing step |

These runtime results confirm DTR §13 item 4 (Alembic replaces the dependency row) on
PostgreSQL 17. The failure was
`test_reconciliation_inserts_one_event_per_pre_existing_run_and_nothing_on_a_rerun`:
`(seen, inserted) == (1, 0)` instead of `(1, 1)`.

**Diagnosis (read-only, by elimination; not verified at runtime).** `seen = 1` proves the
selection found the run in `DELETE_PENDING` with no outbox event for its aggregate. Inside
`insert_reconciliation_event` the locked re-read and the event-absence check repeat those same
facts, and the deterministic `event_id` cannot collide with another event. That leaves the last
line: the result was judged by `CursorResult.rowcount == 1` after
`INSERT … ON CONFLICT DO NOTHING`. SQLAlchemy only guarantees `rowcount` for UPDATE and DELETE, so
this check was unreliable. Neither the tool, the event-id rule, the aggregate upsert, test
ordering nor the fixture explains `(1, 0)`. Whether the row was in fact inserted in that run is
not known: no later step read it.

**Fix (allowlisted paths only).** `story_lifecycle_store.py`: the insert is built by
`reconciliation_event_statement(…)` with `RETURNING event_id`, and success means a returned id
(`scalar_one_or_none() is not None`), not `rowcount`. `test_story_lifecycle_store.py` gains five
offline tests: the statement renders `ON CONFLICT (event_id) DO NOTHING … RETURNING`, the method
reports exactly what RETURNING returned even when `rowcount` reads 0, and it skips runs that are
no longer `DELETE_PENDING` or already have an event. `test_frc08_lifecycle_postgres.py` now
first asserts that the event row exists (deterministic id, `pending`, `PARENT_ACCOUNT`) and only
then checks the counts. No other `rowcount` check is on an INSERT: the remaining checks are on
UPDATEs, and the run's cancel/consumer path, which uses them, completed.

**Coordinator checks after the fix:**
- ruff: N paths all passed; E paths have no changed per-file count.
- mypy: 0 new errors against the baseline; `story_lifecycle_store.py` alone reports no issues.
- pytest: **338 tests, 337 passed, 1 failed**. The failure is the same baseline catalog-source
  test as before (`rerun_junit.xml` SHA-256 `50B536FC…CB2571`).
- validators: harness, security and architecture valid; skeleton invalid with the same
  pre-existing Android message.
- `git diff --check`: clean.

New hashes: `story_lifecycle_store.py` 19,498 bytes `E9FB0002…07ED5F`;
`test_story_lifecycle_store.py` 12,714 bytes `49FA929A…56ACE3`;
`test_frc08_lifecycle_postgres.py` 18,112 bytes `A4DB0C86…D978DB`. These supersede the §8 rows.

The Docker command file now first removes only `frc08-pg-20261119103216` and
`frc08-s3mock-20261119103216`, guarded by `^frc08-(pg|s3mock)-20261119103216$`. File: 15,818 bytes,
SHA-256 `B23C716B…7BFA5B`, parse-checked with 0 errors, not executed.

## 5b. Owner run 20261119-110418 — PASSED (Allowlist §7 items 5-7)

Owner-run on Docker with the S3Mock deviation (§5): a new `postgres:17-alpine` container and a
new `adobe/s3mock:4.10.0` container, both published on loopback only (PostgreSQL 55458, S3 59458);
database `sketch2life_frc08_lifecycle`, a new bucket whose name contains `frc08`, credentials
generated for the run. Run folder `tmp/frc08-impl/owner-run/20261119-110418/` (git-ignored).
`SUMMARY.txt` SHA-256 `B01F7F99640E4F9BB85568F949B25A2ECD44A7E500F3B8989CF15A2870EAB2DD`;
`item6_junit.xml` SHA-256 `1A8183A3331C470099920F0119BDD24C183657871772141E25796DC8A1AB4785`.
The coordinator only read these files. Each log SHA-256 listed in `SUMMARY.txt` was recomputed
from the log file: **13 of 13 match**.

| Step | Exit | Log SHA-256 | Result |
|---|---:|---|---|
| 1a start PostgreSQL container | 0 | `0EE32A53758C2241FCD524F5128DB99F8D4A2E5B6044F8A7359C2A6869417341` | started |
| 1b start S3Mock container | 0 | `A369DF565D38FF916A1268A0932FDC6005E489534D97F455059372D562EDD012` | started |
| 1c wait for PostgreSQL | 0 | `8A361F77687F9953C5B81C87FFE4C8DBC9F31133F5338BE00446D7D28F2F636C` | ready |
| 1d wait for S3Mock | 0 | `5B65AFEDFE47907BA967DB82B60FD090CDB11D81826D07DF00764CC681D96B04` | ready (HTTP 200) |
| 1e create bucket, check empty | 0 | `9A7C7AF82993F4230593F4B0C75F011A29B02D83EC1459B0F673CFC8311DC471` | created, empty |
| 1f target guard | 0 | `E57E65E25FA45901401CF4FF3AB561DFB37F7D469797F191FE7563B7A73F5549` | `TARGETS_ALLOWED` |
| 5a `alembic upgrade heads` | 0 | `930E233AA3A2A1E20FD13AF3C84F78D4A2D28FB45243D0B10EE4CA9582FB6410` | 10 version rows incl. `20261119_frc08_lifecycle_scope` |
| 5b `downgrade frc08_lifecycle@base` | 0 | `8F022EA5D71D16904D78572AA4F7C10D964148E43C40189C16823386F1989AFD` | that row back to `20261112_parent_story_context` |
| 5c `upgrade heads` again | 0 | `B7615A16A13C74D862AC2EF064A44B8181E05194B5ABFD001405C74D164D5877` | as 5a |
| 6 integration test | 0 | `4F20F3ADAAB2326EB5E8241B03D10C8B3315F094DF286570F5F1B617765CD449` | **7 passed, 0 failed, 0 skipped** (6.32 s) |
| 7a seed one synthetic pre-existing `DELETE_PENDING` run | 0 | `3B24F9F154CD544128B71D0D1A2EC9668AD586247C1F3325D9F18BF1F956D523` | seeded |
| 7b reconciliation, run 1 | 0 | `EB2CE91ED9FA316C6FBEA65B55023BE88BB8E674F58506907EBBD90B9328BE73` | `eligible=1 inserted=1` |
| 7c reconciliation, run 2 | 0 | `3ECD874AF510B61FAB405754B35CDB23BCFC6DB2C0015DDFBA6F1C3AFB95C8A3` | `eligible=0 inserted=0` (no new event) |

The seven integration tests that passed:
- schema delta CHECKs and organization defaults;
- cancel purges everything and ends `DELETED` with a completed token;
- delete of a completed run without artwork ends with an empty asset entry;
- a retained asset ends in `exception` with nothing deleted in Core;
- reconciliation inserts one event per pre-existing run and nothing on a rerun;
- the downgrade guard refuses while lifecycle rows exist;
- a stale compare-and-set is refused by the receipt store.

Containers left running for the owner to remove later: `frc08-pg-20261119110418` and
`frc08-s3mock-20261119110418`.

**Earlier attempts (all owner-run, all stopped at their first failing step):**

| Run | Stopped at | Cause | Resolution |
|---|---|---|---|
| 20261119-093812 | 1b start MinIO, exit 125 | Docker Hub refused the pull of `minio/minio` (pull access denied) | MinIO replaced |
| 20261119-100546 | 1b start MinIO, exit 125 | the pinned quay.io MinIO tag returned 401 Unauthorized | owner-approved switch to S3Mock (§5) |
| 20261119-103216 | 6 integration test, exit 1 (6 passed, 1 failed) | the reconciliation judged its insert by `rowcount`, so it reported `inserted=0` | fixed with `RETURNING` (§5a); items 5a-5c had already passed |

**What this run settles (corrected after review R1, P2-2):** migration up/down/up, the CHECKs and
the downgrade guard on PostgreSQL 17 (Contract §8 condition 7, **first half** only), the
organization default of a new audit row, and the DTR §10 reconciliation check. The end-to-end
cancel, delete and retained-asset paths of the consumer also ran, against an S3-compatible double.
The downgrade-guard test of that run executed the whole guard once and was refused on its first
true clause; it has since been split per clause (§10, P3-4) and is not yet re-run.

**Not settled by this run:** organization-writer behaviour ("existing organization writers
behave as before", Contract §8 condition 7, **second half**). The later amendment-1 owner run
(§10.3) evidences it only in part, and the rest stays **OPEN** (review R2 wording):

> Owner run 20261119-130537 (PostgreSQL 17, disposable container, loopback; command file
> `23D6B910…`; log hashes verified):
> - `test_notice_coverage`: 8/8 passed.
> - `test_migrations`: 16 passed, 2 failed.
> - `test_be1_postgres_api`: 1 passed, 3 failed.
>
> The failing test ids and failing lines are exactly the same at the base tree (0 new).
>
> **Evidenced:**
> - the organization AI Jobs notice writer;
> - the BE1 HTTP writers (class, session, lobby, group, control, data request: audit count 7,
>   outbox ≥ 7, up to the pre-existing failure at the OpenAPI route count);
> - the retention worker;
> - `alembic upgrade heads` including the FR-C-08 revision on a fresh database, its rerun, and
>   the upgrade of an existing BE1 database.
>
> **Contract §8.7 second half stays OPEN for:**
> - the assertions after the pre-existing failure points: `test_be1_postgres_api.py` after lines
>   302, 557 and 750, and the head-set and downgrade assertions of `test_migrations.py`;
> - `test_m2_s2_g1_parent_story_postgres.py` (recorded debt, NOT RUN), including the edited
>   `_assert_no_side_effects` helper;
> - the runtime behaviour of the Parent confirmation and provider-result writers under the
>   `_live_run` predicate. Only `create_run`, `attach_artwork`, `cancel_run`, `delete_run` and
>   `get_run` ran on PostgreSQL, in `test_frc08_lifecycle_postgres.py`.

These open parts are to be accepted as recorded debt if the owner accepts the task (review R2 F-4).
Real MinIO/AWS S3 behaviour is also not covered, because S3Mock is a test double (port design §13).

**Coordinator checks at the time of this run** (the tree changed after it: review R1 and R2
remediation, §10; the final owner rerun of §10.4 re-runs item 6 and item 7 on the final tree):
- ruff: no new findings;
- mypy: 0 new errors;
- pytest: 338 tests, 337 passed, 1 failed (the baseline catalog-source test);
- validators: harness, security and architecture valid; skeleton invalid (pre-existing, Android);
- `git diff --check`: clean.

## 6. Verification map (static vs runtime)

**Static / offline evidence (this report):** Contract §8 conditions 1-3, 5, 6 and 8 at unit and
contract level; DTR §10 token, crash-point (each of the four steps × before entry / after entry /
after act / after flip, plus after objects, after sweep, after rows and a failing verification —
all rerun to the same four entries and `sha256`), sweep, retained-asset, step-6 late orphan,
CAS race, lease loss, retry bound, exception receipt insertion, replay and fence checks;
port design §12 checks over the production purge code with an in-memory reader
(`test_core_run_asset_purge.py`); `list_keys` error mapping.

**Runtime evidence from owner run 20261119-110418 (§5b):** migration up/down/up and the downgrade
guard on PostgreSQL 17; the CHECKs including the completed-token pattern; a new organization audit
row keeps a NULL scope ref; `FOR UPDATE`, `ON CONFLICT`, JSONB containment and
`IS NOT DISTINCT FROM` as used by the end-to-end cancel, delete, retained-asset exception and
reconciliation tests (`test_frc08_lifecycle_postgres.py`), against S3Mock.

**Runtime evidence from owner run 20261119-130537 (§10.3):** the organization writers listed in
§5b, on PostgreSQL 17, with 0 failures new against the base.

**Still open:**
- Contract §8 condition 7, second half: the parts listed in §5b (the assertions after the
  pre-existing failure points, the M2 gate suite as recorded debt, and the Parent confirmation and
  provider-result writers on PostgreSQL). To be accepted as recorded debt if the owner accepts the
  task.
- Files changed after owner run 20261119-110418:
  - `be1_lifecycle_consumer.py`: the review R1 scope defer, and the review R2 F-1 guard;
  - `routers/parent_story_runs.py`: the key parse moved;
  - `outbox.py`: docstring only;
  - `test_frc08_lifecycle_postgres.py`: the per-clause guard tests and the reconciliation
    pre-check.

  The integration suite has not run on them yet. The final owner rerun (§10.4,
  `OWNER_RUN_FRC08_FINAL.txt`) re-runs item 6 and items 7a-7c on the final tree.
- Real MinIO/AWS S3 listing and deletion (port design §13).

**DTR §10 bullets with no test (not mapped):** the re-open command (DTR §6.6) is out of scope
(Allowlist §6), so these command-level checks have no test and stay unmapped:
- "the re-open writes the receipt and the event in one transaction";
- "a rerun after a crash between them inserts only the event";
- "a re-open uses a fresh event id and a second `lifecycle.exception` gets a fresh `audit_id`" —
  the re-open half. The consumer half is covered: a new event id gets a new event-keyed audit id.

The consumer side of the re-open is covered offline. A `requested` receipt with verified `upload`,
`ai` and `story` entries and no `asset` entry runs to a completed token. The token matches
`COMPLETED_PATTERN`, and the asset entry lands at its fixed position (§10, P3-3).

Alembic 1.19.1 source (`runtime/migration.py`, `RevisionStep.update_version_num`) was read to
answer DTR §13 item 4: a revision with no `down_revision` and one `depends_on` UPDATEs the
dependency's row on upgrade and back on downgrade. This is a source reading, not a runtime result.

## 7. Judgment calls and deviations for the reviewer

1. Migration and report filenames carry `20261119_…` instead of the `20261120_…` written in
   Allowlist §3. The allowlist rows themselves say the date is set at approval: the migration row
   reads "(date set at approval)", and the report row reads "(date set at approval, as for the
   migration)". The implementation approval and the launch are both dated 2026-11-19. Revision id
   `20261119_frc08_lifecycle_scope`.
2. `organization_id` stays annotated `Mapped[str]` while the column becomes nullable on the five
   models, so that unchanged organization callers (many outside the allowlist) keep their types;
   Parent rows are written through Core statements with an explicit NULL.
3. `record_notice` writes the three new notice columns only for a Parent notice; organization
   notices keep the B2 statement, so the AI Jobs PG suites that pin `ai_jobs@head` keep working.
   `test_notice_coverage.py` reads notice rows through the B2 columns for the same reason, and a
   new PG-gated case checks that a Parent notice selects no job.
4. The AI Jobs notice port (`LifecycleNoticePort`) lives in `core_foundation.py` with the other
   consumer ports; its adapter `SqlParentLifecycleNoticeStore` is in the AI Jobs SQL repository.
5. `test_m2_s2_g1_parent_story_postgres.py` (owner-run M2 gate, not run here): besides
   `_EXPECTED_VERSION_ROWS` and the cancel/GET body assertions, `_assert_no_side_effects` now
   ignores the two lifecycle event types in `core_outbox_events`, because an accepted cancel writes
   one by design (DTR §6.1). This touches a helper, not only the named lines.
6. `tests/integration/ai_jobs/test_migrations.py` (H) was not edited. Its PG-gated
   `test_fresh_database_upgrade_heads…`, `test_rerun_of_heads…` and
   `test_migration_matches_tables_metadata` assert version-row sets or metadata at `heads`; the new
   revision and the new notice columns may change their outcome when the owner runs them (the
   first two already list only BE1/AI heads at the base). Reported, not changed.
7. The reconciliation step of the owner file seeds one synthetic `DELETE_PENDING` row so that
   item 7 shows "inserted=1" then "inserted=0".
8. The storage client keeps boto3's default timeouts; the database engine of the tools sets a
   30 s `statement_timeout`; the 300 s step deadline is enforced by the consumer.
9. Contract note (review R1 P3-6; the contract is not edited). On cancel and delete, request-shape
   errors (body and path validation) and `Idempotency-Key` errors (400 `INVALID_REQUEST`) come
   before the owner-scoped lookup (404). The key is now parsed after the Parent role check (403)
   and before the lookup. Contract §3.1 lists the lookup first and says nothing about key errors.
   The 400 does not depend on the run, so it reveals nothing about whether the run exists.
10. Follow-up (review R1 P3-8, not blocking): set an explicit storage client
    `Config(connect_timeout, read_timeout)` in the lifecycle composition, and cap the orphans
    deleted per `sweep_run_prefix` call. Today the call has no deadline check or lease renewal
    inside it.
11. Follow-up (review R1 P3-9, information): `PostgresOutbox.claim_ready(event_types=None)` still
    claims every type. Its docstring now warns that a future generic consumer must exclude
    `LIFECYCLE_EVENT_TYPES`.
12. Deviation from DTR §6.3 (review R1 P3-5, review R2 F-1). DTR §6.3 says a failed step sets the
    receipt to `awaiting_external_purge` by CAS and defers, and that the bound records `exception`.
    It does not foresee a receipt that belongs to another owner scope or another target. In
    `be1_lifecycle_consumer.py` such a receipt is never changed and gets no audit row:
    - below the bound, `_fail_attempt` only defers, with no CAS;
    - at the bound, the exception effect writes no CAS and no `lifecycle.exception` row, and the
      event is delivered without an effect (outcome `delivered`).

    The check `_foreign_receipt` compares `owner_scope_kind`, `owner_scope_ref` and
    `target_ref = story_run:<run_id>`. It is a deviation in the safe direction: it writes less than
    the DTR text says. A run id belongs to one owner scope, so only a forged or corrupt event can
    reach it.
13. Contract test scope (review R1 P3-5 third bullet, review R2 F-5).
    `tests/contract/test_parent_story_lifecycle_contract.py` has cases that set a canned 404 or 409
    on a fake service. They prove error rendering only. The decision itself is covered by the
    repository unit tests (`test_parent_story_run_cancel_repository.py`, fake session), and the SQL
    semantics by the owner runs. Accepted; no code change.

## 8. Changed and new files (bytes / SHA-256, final, after the review-R1 and review-R2 fixes)

| Path | Bytes | SHA-256 |
|---|---:|---|
| `backend/alembic/README.md` | 1755 | `A15C1AA600CC3308581895877CDCA7845232615D9E67B330F848BCA3DACABDD7` |
| `backend/alembic/versions/20261119_frc08_lifecycle_scope.py` | 8558 | `9D115AA6953F54748A9CFE639DCB7BFC88F5E3985DCDEEA8D2A182AA477A5F19` |
| `backend/src/sketch2life/application/ports/ai_jobs.py` | 21251 | `8C47E1D9B71793D8395D53492CEE0524F1DA49D7C860A971F4AF2BE224106590` |
| `backend/src/sketch2life/application/ports/core_foundation.py` | 14797 | `F4824D8F9957A89101CD245065E91835A25D98250CBF4F9249DB631A92CD45D4` |
| `backend/src/sketch2life/application/ports/object_storage.py` | 1308 | `3F297685BB5FA8857BC0F2F6F580FC172B6302DD232F7BB2F76C341E9F7ABC4F` |
| `backend/src/sketch2life/application/ports/parent_story_runs.py` | 8633 | `014EDA922B574A41A6B7E3F9FA869E851556152314D8F9C30E36B95318F2DA0E` |
| `backend/src/sketch2life/application/ports/story_run_lifecycle.py` | 6787 | `9D6CE35E9A78134C2A636C41F9407BEC47B70138E316AEA5732CEB62B5665988` |
| `backend/src/sketch2life/application/services/ai_jobs.py` | 73304 | `C0DF6C3C61FC0FD3A8165F445728D5E24B5223F67E65FF952D00F282405EE4CB` |
| `backend/src/sketch2life/application/services/parent_story_runs.py` | 8536 | `D74F2E4CCB70AD58C9C15218CE00053AE32856A9E40BB5122F5ED1C8F5E15517` |
| `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 9302 | `BDDFEBD54ACD90ABAB7A8429E6B276FAADF38C5C6CE0F0EEA27CCD2888D608A7` |
| `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py` | 33049 | `B643CF1AE80D2CA7BFDD00A23712735D918147A4CAF1B77DE55EC78D66AE3252` |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | 40493 | `37D134804B0B9BC690D24ED7A6283DAF221F165CAFF5A7E738D71102B077C437` |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | 13468 | `43FAAC94475F3116419713D5EF7C9019C19AC1D33557CC16D13B2FD5B253FD0A` |
| `backend/src/sketch2life/infrastructure/persistence/be1_lifecycle_consumer.py` | 35356 | `27051D448CDDEE5BB3C605F8AED2DEDCE8BBAA46B639FA0AC990DB7C3EC38E8F` |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | 29215 | `391F7E1A951931B69AADFAAEED11A796F8E5337F133D1A9FE0D363E82953FC47` |
| `backend/src/sketch2life/infrastructure/persistence/core_lifecycle_store.py` | 19057 | `5CFA95F2FD9CE33A809969B9066C1CA52AECAC3152A00BF799B962BAA0C73378` |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | 14133 | `891D87CC2B34A54DFEEF8DAB360AF4EF14BD8F8AF218170041A137318A4756EA` |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | 26520 | `6AF9CDA5BD6F9ACD8B81AFD044B12A40B9249DA94F228BB03C0CA1E738BE9184` |
| `backend/src/sketch2life/infrastructure/persistence/outbox.py` | 8807 | `0F4AB18A637E3BF510D3064D2F0104C894D54EE6365F633EF511626D9272DA2E` |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 81328 | `71A1306E3E9634A43ABC661ECA81DF36A9802B3883ECF7F88496189A46D5E7B4` |
| `backend/src/sketch2life/infrastructure/persistence/story_lifecycle_store.py` | 19498 | `E9FB000246D6276E19AC3C4983E12EFBD46C8D48A11339807714BDAF5B07ED5F` |
| `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` | 5264 | `02FEEB9C88FBF4E8F90A3703FCB3ECFCCA7426F8CC753BF727AC129CAA9A03DF` |
| `backend/src/sketch2life/infrastructure/story_run_lite/tables.py` | 27144 | `DD686156F3248ECF6DBE19113236110FC36045E986237AE23A8FD45238788AA0` |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1379399 | `A1F2E3F3F734A4CA458D8786DBED8587E107F89AB5E07825EA8D4A078AEAA3DD` |
| `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | 24425 | `DE481A26432DAFDCDB8D0AB0B8DDC59633577302495C082F2966D036DBC05D19` |
| `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 16297 | `349BC81503485563A55891F60447C32BDD9E9CFB5CB00FACA41D8CDD4F3C7116` |
| `backend/tests/contract/test_app_composition.py` | 13856 | `3EE6442A8C0E0E0FB5BE101C66B1DC6F64F9DF7877B5A13AAFCC2FDFF3A2482A` |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 26151 | `98C1A9052324A93968CC9942D4E17661BB45E1E53A137C25C14FECBD981E6A7C` |
| `backend/tests/contract/test_openapi_schema_catalog_mapping.py` | 12745 | `E3B02DD474652024D6429806E758FFC519E1AE6DB9AF61DED7796000993BFA98` |
| `backend/tests/contract/test_parent_ai_late_result_guards.py` | 5675 | `9E2F0E7D3A0FAEEFB11E1079CE9FB39AD1396FCBF9ED6D0B78C4263A7379DDDA` |
| `backend/tests/contract/test_parent_story_lifecycle_contract.py` | 13750 | `E01BEF8835E1684E6290B2DF5ABAFF88A4D363D4CD7AA3DEAED67A84FADB5108` |
| `backend/tests/contract/test_parent_story_run_cancel_route.py` | 5544 | `A6BD21825B42AC9353D5F29C20FEC1020A85904259CF998C5810234799329C3C` |
| `backend/tests/contract/test_parent_story_run_request_contract.py` | 14827 | `129146CAD7730CB2743EEAB62BAAAD664AF65E6CC9B68697C1F1FED93D6370B8` |
| `backend/tests/integration/ai_jobs/test_notice_coverage.py` | 11111 | `A42C7A486AD66F3E2619EED3476DBE660FC745E6652643E27FFBA148EAF74F1C` |
| `backend/tests/integration/lesson_library/test_lesson_library_api.py` | 51625 | `CE821C971577559AA1AC0C32B18007D4175B8B586A9DF09DB005380031B5D8BE` |
| `backend/tests/integration/test_frc08_lifecycle_postgres.py` | 22688 | `4CED1222C385F0C8E6EE711618AB93FAD5567D8A975EB3FCB73D7E562B1F7F92` |
| `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py` | 48542 | `7E36EE1078D51B257F9E5F67AF799FFF9322C31B9417ABB55420E0AC9F846C1E` |
| `backend/tests/unit/test_ai_job_application.py` | 25688 | `1272507EC1EBAEB49F2C861EA6F41914D5DA1FD64A12B3579A9213E23A7ADE7D` |
| `backend/tests/unit/test_ai_job_b5_effects.py` | 27605 | `D7281593C00E1E78C7EEF41DB92887E3AA904DAE5914EEB21CA058F1A47077F1` |
| `backend/tests/unit/test_be1_lifecycle_consumer.py` | 32345 | `2F98C96C0F9D93C479CF1C7BAA4BC8CF99CCFC2D1482DD68F8AC17AED72619BC` |
| `backend/tests/unit/test_core_run_asset_purge.py` | 14859 | `0CA8E90B1A3B2FC904203B3D0D77658EACC1CBEF9D62C162F61E7873EDA99ABB` |
| `backend/tests/unit/test_lifecycle_token_rule.py` | 9168 | `C4BC7A2F952EBA5C52C4447A255A65DD9C870D36BFE31C8BCC0E11B867989BE7` |
| `backend/tests/unit/test_parent_story_repository_postgres_nulls.py` | 9836 | `44EA31A731F2250311AEAF8C52461B91B88DC9924F885DACDD79AB34F5A6C04C` |
| `backend/tests/unit/test_parent_story_run_cancel_repository.py` | 20989 | `9FD80A878FA2777EB32DBD0D4F2407F1ED73DDBC28FFE12951A008EB3FC388C3` |
| `backend/tests/unit/test_s3_list_keys_error_mapping.py` | 3668 | `883FFC26E8128DD73B02DB3715677B354957182BA046B21649D02A88C4DDB853` |
| `backend/tests/unit/test_story_lifecycle_store.py` | 12714 | `49FA929AF759EC19F99202CD4ABCD4CC2A06A6B8CE3D3911F79FC397D956ACE3` |
| `backend/tests/unit/test_synthetic_eligibility.py` | 35584 | `96D27CB69E263BCFE0637DA5908936EE30605BD9C2DEB9497FB5030CCF0DEB47` |
| `backend/tools/frc08_reconcile_delete_pending.py` | 2413 | `85F803FFC7FD7360B0ED3777B701E307009D8CE3BEC9F8A0FB537A80A281EE2D` |
| `backend/tools/run_be1_lifecycle_consumer.py` | 8772 | `B2DB49B95928B7E31B7A0583E2231A02C0E172BDB19B53DD9E3810B413ECA2F4` |

E paths changed: 34 of the 35 of Allowlist Draft 13 (`openapi_contract_amendments.py` needed no
change) plus the one amendment-1 path `backend/tests/unit/test_synthetic_eligibility.py` (one edit).
N paths created: 15 of 15 (this report included; it is not in the table because it cannot hold
its own hash). No H path, SRS, `DECISIONS.md` or D path was edited. `TASK_APPROVAL.md` differs from
HEAD only by the owner's appended launch record and amendment 1; the coordinator did not edit it.
The table supersedes every earlier byte count or hash of these files in §5 and §5a.

## 10. Remediation after implementation review R1

Review: `tmp/frc08-impl-review/FR_C08_IMPLEMENTATION_REVIEW_R1_20261119.md` (git-ignored;
Sonnet 5.5, effort high; NEEDS REMEDIATION, 0 P1 / 2 P2 / 9 P3). The owner approved both P2
remedies (amendment 1, §1). No commit, push or stash was made. The coordinator ran no database,
Docker or storage command, and did not edit `TASK_APPROVAL.md` or `DECISIONS.md`.

### 10.1 Findings and fixes

| Finding | Fix | Paths |
|---|---|---|
| P2-1 the new revision breaks a count-pinned test | `31 → 32`, `(13, 10) → (14, 10)`, and a comment naming `20261119_frc08_lifecycle_scope`; nothing else in the file | `backend/tests/unit/test_synthetic_eligibility.py` (amendment 1) |
| P2-2 §5b overclaimed Contract §8.7 | §5b and §6 reworded: the run settles migration up/down/up, the CHECKs and the downgrade guard on PostgreSQL 17; organization-writer behaviour is NOT RUN; §8.7 second half stays OPEN | this report |
| P3-1 absolute local path | replaced with `<repo>\…` (§4) | this report |
| P3-2 stale report | status line, §4, §8 (regenerated from the files) and the next-gates section (§11, formerly §9) refreshed | this report |
| P3-3 re-open conditions not mapped | consumer test: a `requested` receipt with verified upload/ai/story entries and no asset entry runs to `completed`, matches `COMPLETED_PATTERN`, inserts the asset entry at its fixed position and never rewrites the verified entries; the command-level bullets are listed as unmapped in §6 | `tests/unit/test_be1_lifecycle_consumer.py` |
| P3-4 the downgrade-guard test proved one branch | parametrized per clause (9 cases: aggregate Parent, aggregate organization with a scope ref, outbox Parent, lifecycle request Parent, notice Parent, audit Parent, `DELETED` run, NULL `profile_ref`, `DELETE_RUN` receipt). Each case first checks that the guard passes on the clean database, then inserts its row and asserts that clause's message, inside a transaction that is rolled back. Placed first in the module | `tests/integration/test_frc08_lifecycle_postgres.py` (owner-run, not re-run yet) |
| P3-5 small test gaps | the vacuous `uploads == {}` assert now seeds an open upload and checks it is untouched; new tests for `_invalid_event` (organization scope, `story_run:` aggregate id, upper-case id, wrong event type, missing scope ref; deferred by 3600 s, then delivered with no effect at the bound), `RECEIPT_SCOPE_MISMATCH`, and `RECEIPT_TARGET_MISMATCH` / `SCOPE_INVALID` of the SQL receipt store. Code change: a receipt of another owner scope is now left unchanged (defer only, no CAS) | `tests/unit/test_be1_lifecycle_consumer.py`, `be1_lifecycle_consumer.py` |
| P3-6 key parse before the lookup | the key is parsed after `_require_parent`, still before the lookup; contract note in §7 item 9 (the contract is not edited) | `routers/parent_story_runs.py` |
| P3-7 date justification | §7 item 1 cites Allowlist §3 "date set at approval" | this report |
| P3-8 timeouts / sweep loop | recorded follow-up, §7 item 10 | this report |
| P3-9 unfiltered default claim | recorded follow-up, §7 item 11; docstring note on `claim_ready` | `outbox.py` |

### 10.2 Coordinator checks after the remediation

| Check | Result |
|---|---|
| ruff, 34 E Python paths vs `git show HEAD:<path>` | 0 files with a changed count |
| ruff, 14 N Python paths | all passed |
| mypy, 25 src modules | 32 errors in 8 files vs baseline 33; 0 new |
| pytest, targeted (17 E/N unit/contract files + 7 offline migration tests) | 484 tests: 483 passed, 1 failed (the base catalog-source test) |
| pytest, whole `tests/unit` + `tests/contract`, worktree (`--continue-on-collection-errors`) | **8,403 tests: 65 failed, 18 collection errors, 22 skipped** (junit SHA-256 `02D11A3F…CE3673`) |
| same at the read-only base export `tmp/frc08-impl-review/basefull` | **8,205 tests: 65 failed, 18 collection errors, 22 skipped** (junit SHA-256 `FEEE14CB…DB508C`); equal to review R1 row 5 |
| failing test ids compared (failures + errors) | **83 at base, 83 in the worktree, 0 new, 0 gone**; the worktree adds 198 passing tests |
| `validate_harness.py` | HARNESS_VALID |
| `validate_repository_security.py` | passed |
| `validate_architecture.py` | ARCHITECTURE_VALID |
| `validate_skeleton.py` | SKELETON_INVALID, the same pre-existing Android `applicationId` message; `apps/` unchanged |
| `git diff --check` | clean |

A first whole-suite worktree run was started before the P3 edits (65 failed, 18 errors at that
point, P2-1 already fixed). The table above is the second run, made after every code and test
edit.

### 10.3 Amendment-1 owner run (command file; run as 20261119-130537, below)

`tmp/frc08-impl/OWNER_RUN_FRC08_PG_SUITES.txt` (git-ignored; 12,704 bytes, SHA-256
`23D6B910…7A2AE7`, parse-checked with the PowerShell parser: 0 errors, not executed). It reuses
the running container `frc08-pg-20261119110418` and starts or removes no container. Before
anything runs, it checks the exact name, that the container is running, the image
`postgres:17-alpine`, and the binding `127.0.0.1:55458`. Ports 5432 and 5433 are refused.

The container's own throwaway credentials are read with `docker inspect` and never printed.
They are written to a password file under `tmp/frc08-impl/owner-run/<stamp>-pg-suites/`, which is
deleted at the end. The local secrets directory is never read. The file then runs:
- (a) `test_migrations.py` and `test_notice_coverage.py`, pointed at that container by the
  `BE2_TEST_PG_*` variables;
- (b) `CREATE DATABASE frc08_be1_acceptance` (refused if it exists), `alembic upgrade heads` on
  it after the fail-closed target guard, then `test_be1_postgres_api.py` with
  `BE1_TEST_DATABASE_URL`;
- (c) every worktree suite that fails is rerun from the base export, and the failing test ids
  are compared.

Each suite writes a junit file; logs, exit codes and log SHA-256 go to `SUMMARY.txt`.
`test_m2_s2_g1_parent_story_postgres.py` is recorded debt (NOT RUN).

**Result: owner run 20261119-130537** (folder `tmp/frc08-impl/owner-run/20261119-130537-pg-suites/`,
git-ignored). Container `frc08-pg-20261119110418`, host 127.0.0.1, port 55458. Databases: the
`be2_b2_*` databases (created and dropped by the suites) and `frc08_be1_acceptance`.
`SUMMARY.txt` SHA-256 `B51EC6A6C2C2173AD2C0096D57D8B29C18A3ABDF03D8D33ADF7FBFA7797384C6`.
The coordinator only read the files. The 8 log hashes in `SUMMARY.txt` were recomputed from the
logs: **8 of 8 match**. The password file is absent after the run, as designed.

| Step | Exit | Log SHA-256 | Result |
|---|---:|---|---|
| a1 `test_migrations.py`, worktree | 1 | `F4FA9416C079E108ACF70F9DCFB63F475243935AE0896A365D01114EF8D8A1D4` | 16 passed, 2 failed |
| a1 same at the base export | 1 | `61B788EF00DD3A9248C48DEF2F76C00EC81C73BF40FEE39628D0DF417061853A` | 16 passed, 2 failed |
| a2 `test_notice_coverage.py`, worktree | 0 | `9B0E1F2B0FB68C6AEA8BDCAA3E908836ED7B97C7C3E3BEF6D3A18DCAC036303E` | **8 passed** (base rerun not needed) |
| b0 `CREATE DATABASE frc08_be1_acceptance` | 0 | `D7B818BB2EE113BEAA8BB1F8F4E91783DC327907DA26B4A7012A68DC2A48A6B9` | created |
| b1 `alembic upgrade heads` on it | 0 | `0E98DD44E49606720075F91CA74A69CE80CA376F15F702F48B62D259050C1A4C` | migrated, incl. the FR-C-08 revision |
| b2 `test_be1_postgres_api.py`, worktree | 1 | `CA7B200FD5BEB6FF552CA2570C1831122B87ABF4282CE7374132B496A029EA54` | 1 passed, 3 failed |
| b2 same at the base export | 1 | `4CDAB9C881C7F2CC22F7175FD1E76DD12EEEB97DEA366B3B3977DAD29170B2C8` | 1 passed, 3 failed |
| c compare failing ids | 0 | `797C59DCEDC34508CE09FE374EA4FDE6A7DFC06F2B1C6C31E0A11F053DF16CAD` | a1 2 vs 2, b2 3 vs 3: **new_against_base=0** |

Junit SHA-256:
- `a1_test_migrations_junit.xml` `287EF528…335BCD` and `…_base_junit.xml` `55E683C2…F0612A`;
- `a2_test_notice_coverage_junit.xml` `18CAA5E5…A3A3B`;
- `b2_test_be1_postgres_api_junit.xml` `7E16DC33…E706EF` and `…_base_junit.xml` `A5DF0C3F…BA4316`.

The failing ids are the same at the base, and so are the failing lines (review R2 §7):
- `test_migrations.py`: `test_fresh_database_upgrade_heads_creates_both_module_branches`, at the
  version-set assertion (line 340), after `upgrade heads` succeeded. The second is
  `test_downgrade_removes_only_ai_jobs_on_disposable_database`, stopped by an older revision's own
  no-automatic-downgrade guard (Parent context), so it says nothing about the FR-C-08 downgrade.
- `test_be1_postgres_api.py`: three cases fail.
  - `…enforces_assignment_scope` fails at line 302, the OpenAPI route count. It ran after the
    organization writers and the audit and outbox count assertions.
  - `…room_code_start…` fails at line 557.
  - `…pending_consent…` fails at line 750.

The other 16 migration tests passed, including `test_rerun_of_heads_is_a_no_op`,
`test_existing_be1_database_gains_ai_jobs_without_changing_be1` and
`test_migration_matches_tables_metadata`. The retention-worker test of `test_be1_postgres_api.py`
passed in full. What this run evidences, and what stays open for Contract §8.7 second half, is in
§5b. `test_m2_s2_g1_parent_story_postgres.py`: recorded debt, NOT RUN.

### 10.4 Fixes after implementation review R2

Review: `tmp/frc08-impl-review-r2/FR_C08_IMPLEMENTATION_REVIEW_R2_20261119.md` (git-ignored;
22,895 bytes, SHA-256 `19553DFC…`; Sonnet 5.5, effort high; ACCEPTABLE WITH NOTES, 0 P1, 0 P2,
5 P3). The owner approved fixing all five, followed by one final owner rerun before acceptance.
No commit, stage or stash was made. The coordinator ran no database, Docker or storage command, and
did not touch `TASK_APPROVAL.md` or `DECISIONS.md`.

| Finding | Fix | Paths |
|---|---|---|
| F-1 the foreign-receipt protection ended at the bound, and the target was not checked | New `_foreign_receipt` (scope kind, scope ref, `target_ref`). It is used in `_purge` (raises `RECEIPT_SCOPE_MISMATCH` / `RECEIPT_TARGET_MISMATCH`), in `_fail_attempt` (no CAS) and in the `_exception` effect (no CAS, no audit; the event is delivered with outcome `delivered`). `LifecycleReceipt` gains `target_ref`, and the SQL receipt store reads it. New tests at `attempt_count = 9` and below the bound, for both the scope case and the target case. Recorded in §7 item 12 as a deviation from DTR §6.3 | `be1_lifecycle_consumer.py`, `core_foundation.py`, `tests/unit/test_be1_lifecycle_consumer.py` |
| F-2 the report predated owner run 130537 | the run is recorded in §10.3 (counts, 8/8 log hashes, the junit hashes, the same failing ids and lines at the base, 0 new, the M2 gate test NOT RUN); the status line, §5b, §6, §10.3 and §11 refreshed | this report |
| F-3 code and test changed after the last FR-C-08 PostgreSQL run | new command file for one final owner rerun of item 6 and items 7a-7c on the final tree (below); §6 lists the files changed after run 110418 | `tmp/frc08-impl/OWNER_RUN_FRC08_FINAL.txt` |
| F-4 Contract §8.7 second half only partly evidenced | the review R2 §7 wording is used in §5b; the listed parts stay OPEN, to be accepted as recorded debt if the owner accepts the task | this report |
| F-5 canned 404/409 contract cases | §7 item 13 states that they prove error rendering only, and that the decision is covered by the repository unit tests | this report |

**Final owner rerun (command file; NOT RUN yet).** `tmp/frc08-impl/OWNER_RUN_FRC08_FINAL.txt`
(git-ignored; 13,266 bytes, SHA-256 `CA2038B8…457018`, parse-checked with the PowerShell parser:
0 errors, not executed).
- It reuses the running containers `frc08-pg-20261119110418` (postgres:17-alpine,
  127.0.0.1:55458) and `frc08-s3mock-20261119110418` (adobe/s3mock:4.10.0, 127.0.0.1:59458).
  Before anything runs it checks their exact names, that they are running, their images and
  bindings. Ports 5432 and 5433 are refused.
- It creates a fresh database `sketch2life_frc08_final_<stamp>` (refused if it exists) and a
  fresh, empty bucket `frc08-final-<stamp>`.
- Steps, stopping at the first failure: `alembic upgrade heads` on the fresh database (the
  integration test needs heads), item 6 (`test_frc08_lifecycle_postgres.py`, 15 tests including
  the 9 per-clause guard cases), and items 7a-7c.
- The PostgreSQL credentials are the container's own throwaway values, read with `docker inspect`
  and never printed or written to a file. It deletes no file, container, database or volume.
- Logs, exit codes and log SHA-256 go to `tmp/frc08-impl/owner-run/<stamp>-final/SUMMARY.txt`.

**Coordinator checks after the R2 fixes:**

| Check | Result |
|---|---|
| ruff, 34 E Python paths vs `git show HEAD:<path>` | 0 files with a changed count |
| ruff, 14 N Python paths | all passed |
| mypy, 25 src modules | 32 errors in 8 files vs baseline 33; 0 new |
| pytest, targeted (17 E/N unit/contract files + 7 offline migration tests) | 488 tests: 487 passed, 1 failed, the base catalog-source test (junit SHA-256 `4908E79D…2B0A76`) |
| pytest, whole `tests/unit` + `tests/contract`, worktree | **8,407 tests: 65 failed, 18 collection errors, 22 skipped** (junit SHA-256 `9B656819…C3F895C`). A first attempt stopped at 78% with no result and was rerun |
| same at the base export (unchanged run of §10.2) | 8,205 tests: 65 failed, 18 errors, 22 skipped |
| failing test ids compared | **83 at the base, 83 in the worktree, 0 new, 0 gone** |
| validators | harness, security and architecture valid; skeleton invalid (the same pre-existing Android message; `apps/` unchanged) |
| `git diff --check` | clean |

### 10.5 Final owner rerun 20261119-134002 on the final tree

- **Command:** `tmp/frc08-impl/OWNER_RUN_FRC08_FINAL.txt` (13,266 bytes, SHA-256 `CA2038B8…`), owner-run.
- **Target:** the reused loopback containers `frc08-pg-20261119110418` (PostgreSQL 17, 127.0.0.1:55458) and
  `frc08-s3mock-20261119110418` (S3Mock, 127.0.0.1:59458); fresh database
  `sketch2life_frc08_final_20261119134002` and fresh empty bucket `frc08-final-20261119134002`.
- **Tree:** the last code and test edit was at 13:26 (`be1_lifecycle_consumer.py`,
  `test_be1_lifecycle_consumer.py`); the run started at 13:40, so it ran the final tree.
- **Result:** all 9 steps exit 0. Item 6 `test_frc08_lifecycle_postgres.py`: 15 passed, 0 failed, 0 errors,
  0 skipped (junit), including the 9 per-clause downgrade-guard cases. Reconciliation: run 1
  `eligible=1 inserted=1`, run 2 `eligible=0 inserted=0`.
- **Log hashes (SHA-256, recomputed by the coordinator from the files; equal to `SUMMARY.txt`):**

  | Step | SHA-256 |
  |---|---|
  | 1a_create_fresh_database | `2B33C79B1B28C3C22A15B2F300D3AA95BC23704CBBA4F0DD5220FB1D46857CA7` |
  | 1b_wait_s3mock | `5B65AFEDFE47907BA967DB82B60FD090CDB11D81826D07DF00764CC681D96B04` |
  | 1c_create_empty_bucket | `9A7C7AF82993F4230593F4B0C75F011A29B02D83EC1459B0F673CFC8311DC471` |
  | 1d_guard | `E57E65E25FA45901401CF4FF3AB561DFB37F7D469797F191FE7563B7A73F5549` |
  | 2_upgrade_heads | `A1A48664F53FE8B813B71E362323B7CB1FEEB4756D00A1040C9E8752E400ECEC` |
  | 6_integration_test | `A7F6398421039E0CCD7A101782D9BAD79D23384BD02ED0F045497729463A435B` |
  | 7a_seed_pre_existing_run | `3B24F9F154CD544128B71D0D1A2EC9668AD586247C1F3325D9F18BF1F956D523` |
  | 7b_reconcile_run1 | `EB2CE91ED9FA316C6FBEA65B55023BE88BB8E674F58506907EBBD90B9328BE73` |
  | 7c_reconcile_run2 | `3ECD874AF510B61FAB405754B35CDB23BCFC6DB2C0015DDFBA6F1C3AFB95C8A3` |

### 10.6 Owner acceptance and recorded debt

The owner accepted FR-C-08 on 2026-11-19 after review R2 (ACCEPTABLE WITH NOTES) and the final rerun. Recorded
debt and follow-ups:

- Contract §8 condition 7, second half (existing organization writers behave as before): partly evidenced
  (`ai_jobs/test_notice_coverage` 8/8; the BE1 HTTP test exercises the writers before its pre-existing
  route-count failure); the cut-off assertions stay OPEN as debt.
- `tests/integration/test_m2_s2_g1_parent_story_postgres.py`: NOT RUN (its guard accepts only the M2 gate
  databases, ports and role).
- Storage ran on S3Mock (owner-approved deviation); real MinIO or S3 paging and delete behaviour is not
  verified.
- Follow-ups: explicit storage timeouts and an orphan cap per sweep (R1 P3-8); a registered-consumer rule for
  the unfiltered default outbox claim (R1 P3-9); the SRS wording edit; the Parent client (FE) for cancel,
  DELETE and the lifecycle GET.

## 11. Next gates (owner)

1. Done: owner run 20261119-110418 of Allowlist §7 items 5-7 (§5b).
2. Done: independent implementation review R1 (Sonnet 5.5 high, NEEDS REMEDIATION); the
   remediation is §10.
3. Done: amendment-1 owner run 20261119-130537 (§10.3), with 0 failures new against the base.
4. Done: independent implementation review R2 (Sonnet 5.5 high, ACCEPTABLE WITH NOTES, 0 P1,
   0 P2, 5 P3); the fixes are in §10.4.
5. Done: final owner rerun 20261119-134002 on the final tree (§10.5).
6. Done: owner acceptance with recorded debt (§10.6).
7. Done with this report: one task commit (code, tests, evidence and the D rows). No push or merge;
   both need a separate owner word.

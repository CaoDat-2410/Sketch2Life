# FEAT-063 M2 — PostgreSQL acceptance gate G1 (reduced) — Task Approval Draft 2

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Until the owner approves it, this text authorizes nothing: no file under `backend/`, no container, database, migration, connection, process start, test run, network access, commit or push.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. This draft itself is not independently reviewed.
- **Predecessor, unchanged:** Draft 1, `plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT1_20261117.md`, SHA-256 `196A60F374FA41AB5501FD8B3915988133795EA898433F1E8644640DC618FA6C`; cold review R1 (Sonnet 5.5, high): READY WITH NOTES, 0 P1 / 3 P2 / 9 P3, `evidence/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R1_20261117.md`, SHA-256 `600ED9787772B7F1BD62794194E15056137D4F03F4E0598F3E69340FA3661A24`. Section 5.1 disposes of its findings G1 to G12. Draft 2 is self-contained with respect to Draft 1.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a` (equal to the remote-tracking ref; draft PR #29).
- **Plan carried:** `plan/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT4_20261117.md`, 26,537 bytes, SHA-256 `EBA29DEA0E30370916DEF964E227484F1E2820FA3F9E5ED47F15D21E3B1C880B`, as amended by sections 3 to 6 below. Where this text and Draft 4 differ, this text governs. No fifth plan draft is written (owner: "Làm P0"). Parts of Draft 4 that are superseded outright: its deviation table (section 3; replaced by section 3.1 here, where DV-6 and DV-8 have different content); its section 7 seeding table (replaced by section 4 here); guard 5's "ten heads" (replaced by the migration row of section 3 here); its section 9 sentence on acceptance of DV-1 to DV-12 and its "commit and clean status" pin (replaced by sections 3.1 and 6 here); its sections 10 and 11 (open items now decided; the review R2 map is historical).
- **Review carried:** `evidence/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT4_COLD_REVIEW_R3_20261117.md`, SHA-256 `68EFA21314321A357F915BA8340B724E723EFB73F318934EF9084D8783F0ABE5` (Sonnet 5.5, high; READY WITH NOTES, 0 P1 / 5 P2 / 11 P3 as that record states; it lists twelve P3 items, F6 to F17). Section 5 disposes of F1 to F17.
- `OWNER_MODAL_CALL_APPROVED=NO`. No provider, Modal or Firebase call at any stage.

## 1. What the owner is asked to approve

Two stages. **This draft asks for Stage A only.** Stage B is described so that Stage A is written to fit it; it needs its own approval entry after Stage A, when the files exist and can be pinned by hash.

| Stage | Content | Who | Touches a database or container |
|---|---|---|---|
| A | Write the two files of section 2; static checks; offline collection; case map. No source file is edited | Session | No |
| B (later approval) | Command cards; loopback probe; rehearsals on throwaway containers; the one-shot gate; evidence | Owner runs; session reads outputs | Yes |

## 2. Stage A allowlist and ceilings

New files, exactly these two, both in the repository (owner decision: "Ở lại repo"):

1. `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py` — the cases of Draft 4 section 6 as amended here. It does not use the `requires_postgres` marker, which is registered only for `tests/integration/ai_jobs/`; it skips with a stated reason when the gate variables of section 4 are absent; the Stage B gate card requires zero skipped tests.
2. `backend/tests/integration/m2_s2_g1_launcher.py` — test-only module (not collected: no `test_` prefix) that installs the socket guard **first**, then builds the real application with `create_app()`, assigns the synthetic token verifier to `app.state.be1_runtime.identity_verifier`, writes its own process identifier to a file under the output root, and serves on `127.0.0.1` at the approved API port.

Both are written with LF line endings.

New record files, exactly these two, in English, uncommitted until the owner asks:

3. `evidence/M2_S2_POSTGRES_GATE_G1_STAGE_A_REPORT_20261117.md` (date of writing in the name) — sizes and SHA-256 of the two code files; the table mapping every case to its test function; the exact seeding statements; the static-check commands, exit codes and outputs; what could not be established.
4. `plan/M2_S2_POSTGRES_GATE_G1_STAGE_B_TASK_APPROVAL_DRAFT1_20261117.md` (date of writing in the name) — the Stage B approval draft with the command cards.

Not allowed in Stage A: any edit to an existing file (source, test, configuration, `.gitattributes`, records, including `approvals/TASK_APPROVAL.md` except the entry that records this approval, which the session appends on the owner's approval); any new file outside the four above except scratch under the repository-root `tmp/m2-s2-pg-gate/`; dependency overrides; replacing the database session, runtime object, repository or service; rebinding names in an application module; any provider stand-in.

Static checks, with the task interpreter (`tmp/m2-s2-mapper-env/.venv`, Ruff 0.17.2, Mypy 1.20.2, pytest 8.4.2), each run from the worktree with `PYTHONPATH` and `MYPYPATH` pinned to this worktree's `backend/src`, every cache and base-temp directory under `tmp/m2-s2-pg-gate/cache/` (Ruff and Mypy cache directories set explicitly; pytest with `-p no:cacheprovider` and `--basetemp` there), repeatable up to 20 times each:

- syntax (`ast.parse`) and Ruff on the two code files only: zero diagnostics;
- Mypy: zero diagnostics **located in the two code files**; diagnostics located in existing package files are recorded debt and are not counted;
- a byte-level check of the two code files: LF only, no trailing whitespace, final newline (`git diff --check` does not examine untracked files);
- `pytest --collect-only` on the new test file with every database and libpq variable unset. Collection must not connect: neither file opens a connection, creates an engine or builds the application at import time; the test file builds nothing outside fixtures that first check the gate variables;
- the repository validators (`validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check`); constant names avoid the upper-case words the security validator flags, and the dummy storage key values do not have the shape of a real cloud key.

Stage A ends with the four files written and checked. It starts no process that listens, opens no socket and reads no credential.

Stop and return to the owner if, **by reading the code**, a case cannot be written without a source change or the launcher cannot build the application without one. Stage A runs no process, so whether the application actually builds and serves is first observed in the Stage B rehearsal; the same holds for finding G2 of review R1 (section 5.1).

## 3. Owner decisions fixed for this gate (2026-11-17)

Each was asked as a separate question; the owner's choice is quoted or named.

| Item | Decision |
|---|---|
| Migration target | "13 head ghim tên": the target is the 13 heads named in section 4. 31 revisions applied; exactly 10 `alembic_version` rows expected. Basis shown: SRS (SHA-256 beginning `B9B1F42D`, 701,157 bytes) lines 2038, 2109, 2169 ("từ source baseline") |
| Migration mechanism | "Một lệnh có kiểm" (given after review R1 finding G3: the Alembic command line takes one revision per invocation, and baseline section 5.3 item 4 says "tối đa một upgrade tới target revision đã pin"). **One** `alembic upgrade heads` per database, guarded: before it, the card stops unless all 31 migration files match their pinned SHA-256, `alembic heads` prints exactly the 13 pinned names, and the probe of Draft 4 guard 3 holds; after it, the card stops unless `alembic_version` holds exactly the 10 pinned rows. The pinned names, not the word `heads`, define the target; D-151 C1 ("không dùng upgrade heads làm đích M2 mặc định") is kept in that sense, and the owner's choice of the full set is explicit, not a default. Baseline section 5.3 item 2 (script and snapshot hashes): the 31 file hashes are the script pin; the "snapshot" is the empty-database probe plus the post-upgrade list of schemas, tables and version rows saved by the card |
| Port | Gate container `127.0.0.1:55440`; rehearsal container `127.0.0.1:55441`. Never 5432, 5433, 55432. API port (**proposed here, fixed by approving this draft**): `127.0.0.1:55450` for the gate, `127.0.0.1:55451` for rehearsals |
| Names | Databases `sketch2life_m2_s2_gate`, `sketch2life_m2_s2_rehearsal`; role `s2l_m2_gate`; containers and volumes `s2l-m2-s2-gate`, `s2l-m2-s2-rehearsal-N` |
| Repetition | Cases 08-01a and 08-01b: 10 executions each, every execution on a fresh Parent account; one failing execution fails the run |
| Test files | Stay in the repository |
| Image | `postgres:17-alpine`, repository digest `sha256:3540c0362c809df084ffac0ae69fe794515f9de92692f02178bcdce0ef0302ac` as read from the local Docker store by the session (read-only inspect). **The owner confirms this digest in the Stage B approval**; no pull is needed |

Earlier planning decisions that stand (Draft 4 section 4): PG-D1, PG-D2 (owner-run; the session holds no database credential), PG-D3, PG-D4 as replaced by "Restart thật", PG-D5, PG-D8, PG-D9, PG-D13, PG-D14, and the reduced gate ("ok v là rút gọn đi"). PG-D7 is unanswered and does not block this gate.

### 3.1 Deviations from the baseline, accepted item by item

Baseline: `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md` (D-151), rows M2-AT-08 (line 316), M2-AT-09 (line 317), M2-AT-10 (line 318) and section 5.3, read in full by the session before asking. Each deviation was put to the owner on 2026-11-17 as its own question, with the governing sentence quoted and two options; the Owner column gives the label of the option the owner selected. Those selections were made in the coordinating session and have no earlier repository record: **approving this draft is what records them**, and the owner may strike any row before approving. DV-13 to DV-18 come from review R3's list of missing deviations. The "baseline clause" of DV-10 is a paraphrase, not a quotation.

| ID | Baseline clause | What the gate does instead | Owner |
|---|---|---|---|
| DV-1 | "recovery không tạo duplicate" | Persistence across a real process stop and start only; the product has no start-up recovery code | "Chấp nhận" |
| DV-2 | "stale result không được accepted" (after restart) | Not shown after restart; shown before restart at repository level | "Chấp nhận" |
| DV-3 | "PostgreSQL integration qua route" for late results | Repository level on PostgreSQL only; HTTP mapping stays with the offline test `tests/contract/test_parent_ai_late_result_guards.py` | "Chấp nhận" |
| DV-4 | "Parent/Teacher" | Parent only; the routes admit only the Parent role | "Chấp nhận" |
| DV-5 | "không hơn một active run/job/receipt hoặc side effect" | Counts runs, inputs, receipts; asserts zero rows in `ai_jobs.job`, `ai_jobs.outbox`, `core_outbox_events` after create and cancel | "Chấp nhận" |
| DV-6 | "Given run qua PREPARATION_REVIEW" | The state is built from the test process with the product's own repository methods (`create_run` through the route, then `attach_artwork`, `record_understanding`, `confirm_subject`), not by raw SQL and not through provider routes; cancel goes through the route. The repository calls use a session from the product's own session factory, the one the routes use (`autoflush=False`), not a default session. See G2 in section 5.1 | "Chấp nhận" |
| DV-7 | "Test không giả định DB chặn 121" | Inverted: asserts PostgreSQL refuses a profile revision of 121 or 155 months and a run row with such an age (`ck_parent_profile_revisions_age_months_36_120`, `ck_story_run_child_age_months`); the service-level 422 stays offline evidence | "Chấp nhận" |
| DV-8 | "locale vi-VN", "serialize/persist/read profile revision", "metadata được giữ" | No locale (the Parent schema has none). Product persist and serialize of profile revisions are **not** exercised: profiles are seeded by SQL. The `profile_revision_ref` and `age_months` inside the create response's `context_snapshot` are compared with the seeded row | "Chấp nhận" |
| DV-9 | "composition/repository/wiring thật" | Synthetic token verifier replaces the Firebase verifier; the Parent-role check runs for real on seeded `be1_adult_identities` rows; the D-190 production role adapter is not exercised | "Chấp nhận" |
| DV-10 | Rows reached through product paths | Identities, profiles, COMPLETED and FAILED runs and the 08-01a holder row are seeded by direct SQL, listed in the evidence. Draft 2 uses **less** direct SQL than the owner accepted, see "Seeded runs" in section 4: only the 08-01a holder row is inserted by SQL; the COMPLETED run is a route-created run changed by one SQL update; the FAILED run uses a product method | "Chấp nhận" |
| DV-11 | "Không drop DB/cleanup mặc định" | A rehearsal container and its volume are removed by a named owner command before the next rehearsal; the gate container is kept | "Chấp nhận" |
| DV-12 | M2-AT-09 "Bắt buộc trước khi thoát S2" | Not covered by G1. This is not a deferral of M2-AT-09 | "Chấp nhận" |
| DV-13 | "không áp đặt loser status/error nếu contract chưa định nghĩa" | The loser is asserted as exactly 409 `ACTIVE_RUN_EXISTS`, which S2 Draft 18 (line 155, citing D-199) defines | "Chấp nhận" |
| DV-14 | "concurrent separate POST /v1/story-runs requests" | 08-01a is one request against a SQL-held uncommitted row (deterministic unique-index path); 08-01b is two real requests released together, overlap not guaranteed | "Chấp nhận" |
| DV-15 | Case 08-14 in S2 Draft 18 | Asserts 409 **and** code `INVALID_STATE_TRANSITION` ("409 + mã"), stronger than the approved case | "Chấp nhận" |
| DV-16 | "Replay/cancel lặp không tạo side effect trùng" | 08-02 asserts 201, the same `run_id` and unchanged row counts; it does not assert body equality, because create replay rebuilds the response from the current run | "Chấp nhận" |
| DV-17 | "không clamp" | Indirect only: at 36 and 120 the response age equals the seeded age; no out-of-range case reaches the service on PostgreSQL | "Chấp nhận" |
| DV-18 | "giữ result/assets/receipts và không coi là đã xóa" | Indirect: retention row sets unchanged, `DELETE_PENDING`, `purge_state` PENDING, owner read still returns the run | "Chấp nhận" |

**Claim rule.** A pass of this gate may be reported only as "gate G1 passed with deviations DV-1 to DV-18". It may not be reported as "M2-AT-08 ran and passed" or "M2-AT-10 ran and passed" without naming those deviations. Whether it is enough for the S3 ledger rows is the owner's decision at Stage B acceptance.

## 4. Technical facts fixed by the read-only preparation (P0)

Read from files at HEAD `7cc5cf74`; nothing was run except static parsing of the migration files and read-only Docker queries.

- **Migrations.** 31 revision files. **13 heads**: `20261015_ai_0001`, `20261017_lc_0001`, `20261018_ap_0009`, `20261018_kv_0001`, `20261018_vr_0001`, `20261019_ae_0001`, `20261019_pa_0001`, `20261019_vf_0001`, `20261101_be1_age_0001`, `20261102_pv_0001`, `20261109_m2_parent_profiles`, `20261110_ar_0001`, `20261112_parent_story_context`. Three of them (`20261015_ai_0001`, `20261101_be1_age_0001`, `20261102_pv_0001`) are named in another revision's `depends_on`, so the expected `alembic_version` content after the upgrade is the other **10**. (Reviews R1 to R3 said "ten heads"; that is the row count.) Whether Alembic agrees is first observed in rehearsal.
- The Stage B card pins all 31 migration files by SHA-256 and stops if one differs.
- `be1_adult_identities.account_role` is added by `20261110_ar_0001`; the Parent-role check reads it (`routers/parent_story_runs.py:75-84`).
- No migration file contains `CREATE EXTENSION`, `CREATE ROLE`, `GRANT` or `SUPERUSER` (text search). Migrations create schemas, a plpgsql function and a trigger, so the role owns the database.
- `20261112_parent_story_context` refuses to run if `story.runs` has a row and has no downgrade.
- **Application start-up.** Settings read `.env` one level above `backend/`; this worktree has none. The combined profile always constructs the S3-compatible storage client (`interfaces/http/app.py:1150-1159`); without keys in settings the client library walks its default credential chain (R3 F1).
- **Seeding columns.** `be1_adult_identities`: `subject`, `account_id`, `issuer`, `state='active'`, `account_role='parent'`, `role_revision`. `parent.child_profiles`: `parent_profile_id`, `owner_issuer`, `owner_subject`, `state='ACTIVE'`, `current_revision_no`, `data_origin='SYNTHETIC_DEV'` (deferred foreign key: insert profile and revision in one transaction). `parent.profile_revisions`: `profile_revision_id`, `parent_profile_id`, `revision_no`, `age_months`, `display_name`, `authored_by_issuer`, `authored_by_subject`, `revision_hash` (64 lower-case hex). Holder row for 08-01a in `story.runs`: `run_id`, `actor_scope_kind='PARENT_ACCOUNT'`, `actor_scope_ref` (SHA-256 of the canonical JSON of issuer and subject), `profile_ref`, `run_state`, `revision`, `version`, `active_owner_parent_account_id`.
  `account_id` and `role_revision` have only application-side defaults, so the SQL sets them.
- **Seeded runs** (review R1 G12). A run that the owner reads must have a current input row, so it is never a bare SQL insert:
  - FAILED run (08-14, and 08-16 for `job_state` and `error_code`): created through the route, then `fail_drawing_analysis(outcome_unknown=False)` called from the test process, which sets `FAILED`, job state `FAILED`, an error code, and clears the active owner (`parent_story_repository.py:1271-1298`).
  - COMPLETED run (08-14): created through the route, then one SQL update setting `run_state='COMPLETED'`, clearing `active_owner_parent_account_id` and advancing `revision` and `version`. No product method reaches COMPLETED without a provider.
  - The 08-01a holder row is the only run inserted by SQL. It has no input row; **the account that owns it is never read or used again**.
- Not yet read in full: `cancel_run`, `record_understanding`, `confirm_subject`. They are read in Stage A before the cases that use them are written.

**Gate variables** (names fixed here; values set only by Stage B cards):

- Core: `SKETCH2LIFE_ENV=test`; `SKETCH2LIFE_DATABASE_URL` (passwordless URL with the literal host `127.0.0.1`); `PGPASSFILE`; `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`.
- Start-up containment: `SKETCH2LIFE_BE1_ARTIFACT_ROOT` set to a directory under the output root (the local artifact store creates its folder at construction, and its default lies under `backend/`, which is not git-ignored); `SKETCH2LIFE_S3_ACCESS_KEY` and `SKETCH2LIFE_S3_SECRET_KEY` set **as a pair** to fixed dummy strings (one alone fails settings validation); `AWS_EC2_METADATA_DISABLED=true`; `AWS_SHARED_CREDENTIALS_FILE` and `AWS_CONFIG_FILE` pointing at non-existent paths under the output root.
- Gate identity: `M2_S2_G1_EXPECTED_DATABASE`; `M2_S2_G1_EXPECTED_PORT`; `M2_S2_G1_RUN_MARKER`; `M2_S2_G1_API_PORT`; `M2_S2_G1_OUTPUT_ROOT` (under the repository-root `tmp/m2-s2-pg-gate/`).

## 5. Disposition of review R3 (F1 to F17)

| ID | Disposition |
|---|---|
| F1 | Launcher and test environment set dummy values for the two S3 key settings (so the client is built with explicit credentials and the default chain is not walked), `AWS_EC2_METADATA_DISABLED=true`, and shared credential and configuration file variables pointing at non-existent paths under the output root. Values are fixed strings in the card, not secrets |
| F2 | Stated: the Python socket guard does not see connections the database driver opens in native code. PostgreSQL traffic is constrained by the literal-address URL, the probe, the cleared variables and (if usable) the egress block. Cards clear in addition `PGHOSTADDR`, `PGPASSWORD`, `PGSERVICEFILE`, `PGSYSCONFDIR`, `PGSSLMODE`, `PGSSLROOTCERT`, `PGSSLCERT`, `PGSSLKEY`, `PGCONNECT_TIMEOUT`, `PGAPPNAME`, `PGTARGETSESSIONATTRS` |
| F3 | Adopted (DV-8) |
| F4 | Adopted (DV-6). Retention row sets compared before and after cancel, by content: `story.run_inputs`, `story.understanding_revisions`, `story.review_decisions`, `story.command_receipts` (earlier receipts), `core_asset_metadata`, `core_asset_lineage` |
| F5 | Bootstrap password: a file generated by the card outside the repository, bind-mounted read-only and named by `POSTGRES_PASSWORD_FILE`. Role creation: `psql` inside the container reads the role password from a second mounted file through a `psql` variable, so it appears in no process argument and no inspection output. Client side: a `PGPASSFILE` in the client format, generated by the same card. Saved inspection output and every kept output are scanned for both passwords |
| F6 | 08-01a: lock-wait query `SELECT pid FROM pg_stat_activity WHERE <holder_pid> = ANY(pg_blocking_pids(pid))`, polled with a timeout; the holder is rolled back in a `finally`; the HTTP client timeout exceeds the wait timeout |
| F7 | Literal `127.0.0.1` everywhere; the socket guard also refuses name resolution of anything else |
| F8 | Seeded COMPLETED and FAILED runs have the active-owner column cleared; stated in the evidence. See DV-15 |
| F9 | Every card prints the imported `sketch2life` package path and stops unless it is under this worktree. "Exactly one URL" means `SKETCH2LIFE_DATABASE_URL` |
| F10 | The launcher writes its own process identifier; the test compares it with the identifier it recorded. Restart leg compares row contents, not only counts |
| F11 | Claim rule restated in section 3.1 |
| F12 | D-127 is cited as the cancel row (`DECISIONS.md` line 263) |
| F13 | DV-13 to DV-18 |
| F14 | Stated: the run marker detects mistakes, not tampering; the in-container socket uses trust authentication by image default, and only the card's commands use it |
| F15 | Test-file policy and output location are decided in section 3 and section 4; the labels PG-D10 and PG-D11 are retired |
| F16 | 08-16 uses a seeded run carrying a job state and an error code, read by the owner and refused (404) for a non-owner |
| F17 | Cards also clear the StoryRun-lite database URL variable, and set `STORYRUN_LITE_MAIN_DEMO_ENABLED=0` |

### 5.1 Disposition of review R1 of Draft 1 (G1 to G12)

| ID | Disposition |
|---|---|
| G1 (P2) | Section 2 now names four files: two code files and two record files (Stage A report; Stage B approval draft) |
| G2 (P2) | **Open product question, made a stop condition.** By reading, `attach_artwork` adds two asset-metadata objects and then inserts into `core_asset_lineage` with no flush in between, while the product's session factory has `autoflush=False` (`parent_story_repository.py:565-609`; `infrastructure/persistence/database.py:43`) and the lineage foreign keys are immediate. If that reading is right, the call fails with 409 `PARENT_STORY_ARTWORK_CONFLICT` under the product's own session, and the production artwork route would fail the same way. Nothing has been run. Rule: the test uses the product's session factory (DV-6). If `attach_artwork` fails in the first rehearsal, that is reported to the owner as a product defect; case 08-03p is then NOT RUN, not rebuilt with a default session or raw SQL, and the gate does not proceed until the owner decides. Stage A does not change the method |
| G3 (P2) | Owner decision "Một lệnh có kiểm": section 3, row "Migration mechanism" |
| G4 | Gate variables completed in section 4; API ports proposed in section 3 |
| G5 | Launcher installs the socket guard before `create_app()` (section 2) |
| G6 | LF required; byte-level check added (section 2) |
| G7 | Cache and base-temp paths, Mypy scope and a ceiling of 20 runs per check (section 2) |
| G8 | Owner column and its introduction rewritten (section 3.1): selections recorded by approving this draft |
| G9 | Section 6: the two code files are committed, on the owner's instruction, before Stage B; the gate pins that commit |
| G10 | Section 2: "by reading" in Stage A; by running in the Stage B rehearsal |
| G11 | Superseded parts of Draft 4 listed in the header; R3's P3 count and the DV-10 paraphrase noted |
| G12 | "Seeded runs" in section 4; the 08-01a account is never read again; DV-8 wording corrected |

## 6. Stage B outline (not requested now)

- Before Stage B the owner decides when the two code files are committed (one commit, on the owner's instruction, with the security validator rerun first). The gate pins that commit and requires no modified tracked file; untracked record files are listed in the evidence, not required to be absent.
- Cards, each with a throwaway rehearsal form before its one-shot form, each linted or dry-parsed before use.
- Loopback probe under the egress block for the three flows (test to API, test to PostgreSQL, API to PostgreSQL). If the block and loopback cannot be combined, stop and ask.
- Rehearsals on `s2l-m2-s2-rehearsal-N` at port 55441: the one guarded upgrade of section 3, then the full test file. Exit after at least three consecutive full passes; an intermittent result is a failure to be understood.
- Gate on `s2l-m2-s2-gate` at port 55440: ceiling 1. A failed gate leaves container, volume and outputs in place and consumes the ceiling.
- Guards, pins, stop conditions and the "does not show" list of Draft 4 sections 8 and 9 apply, with the changes of sections 3 to 5 here.

## 7. Not established

- Nothing was executed against a database; no container exists.
- Whether Alembic's head and version-row computation matches section 4 (review R1 agrees by reading Alembic 1.20.1's source; not run).
- Whether `attach_artwork` works under the product's session factory (G2).
- Whether the 15 migrations outside the story and Parent closure apply cleanly as a non-superuser database owner (text search only).
- Whether the application builds and serves from the launcher under `SKETCH2LIFE_ENV=test` without a source edit and without a network attempt.
- Whether the client library takes the password from `PGPASSFILE` with the URL forms Alembic and the application build.
- Whether an abruptly terminated launcher on Windows leaves a surviving child process.
- Whether Docker's published loopback port is reachable under the egress block.
- The PostgreSQL minor version inside the pinned image.
- Whether co-owner work on another branch already has PostgreSQL tests for these routes.

## 8. Approval block (for the owner)

- [ ] Stage A approved as written in sections 2 to 5.1, including the API ports proposed in section 3 and the recording of the DV-1 to DV-18 selections of section 3.1.
- [ ] A delta review of this draft is wanted before approval (Sonnet 5.5 high or Opus 5.5 high; never Fable).

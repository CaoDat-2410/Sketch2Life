# FEAT-063 M2 — PostgreSQL acceptance gate G1 (reduced) for M2-AT-08 and M2-AT-10 — plan Draft 4

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. It authorizes no code or test edit, no container, database, migration or connection, no process start, no test run, no network access, no commit or push.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. Not independently reviewed.
- **Predecessors, unchanged:** Draft 1 (`53B2A08E38AD2AFC1632D73A266CD831611C06236BB6CC0912D74FABF6501A62`; review R1, NOT READY), Draft 2 (`924F90D4CD61C7EA58EA0D70D0B6A18683F9273AAF93B58DC5A1953AA0BB01A5`; not reviewed), Draft 3 (`85672E6E50E164E08FAADA06C4229B98197320C4D5DF75A3E37316F131C679AC`; review R2, NOT READY, 1 P1 / 8 P2 / 8 P3, `evidence/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT3_COLD_REVIEW_R2_20261117.md`). Draft 4 is self-contained.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a` (pushed; draft PR #29).
- **Scope change in this draft:** on 2026-11-17, after review R2, the owner chose the reduced gate ("ok v là rút gọn đi"). The provider stand-in and the HTTP level of the late-result cases are removed. Gate G2 (M2-AT-09) is not planned here.
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Purpose, and what this gate is not

M2-S2 was closed by the owner on 2026-11-17 on offline evidence. The baseline the owner accepted under D-151 (`plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md`, SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1`) asks for PostgreSQL route evidence for M2-AT-08 before S2 exit. Nothing in the S2 work has ever run against PostgreSQL. This gate runs the database-dependent behaviour of the Parent story-run routes on a real PostgreSQL 17: concurrency, the active-owner lock, idempotency, revisions, cancellation, ownership.

It is **not** full conformance with the baseline rows. Review R2 established, and the session confirmed by reading the code, that several baseline clauses name behaviour the product does not have. Section 3 lists every deviation; each needs the owner's explicit acceptance in the approval text. Without those acceptances a pass of this gate may not be reported as "M2-AT-08 ran and passed" or "M2-AT-10 ran and passed".

The gate changes no source file. A product defect it exposes is reported to the owner (section 9).

## 2. The baseline text, quoted

**M2-AT-08** (Draft 10, line 316):

> Given synthetic Parent/Teacher cùng owner lock có quyền hợp lệ; when concurrent separate POST /v1/story-runs requests submit cùng active owner; then có không hơn một active run/job/receipt hoặc side effect; không áp đặt loser status/error nếu contract chưa định nghĩa. Given run qua PREPARATION_REVIEW; when POST /v1/story-runs/{id}/cancel; then áp dụng D-127: DELETE_PENDING, nhả active-owner trong transaction, giữ result/assets/receipts và không coi là đã xóa. Replay/cancel lặp không tạo side effect trùng. Sau đó dừng tiến trình hệ điều hành thật, khởi động process mới với app composition mới trên cùng DB; recovery không tạo duplicate và stale result không được accepted. Recreate object trong cùng process không tính là restart.
>
> PostgreSQL integration qua route, process stop/start thực, composition/repository/wiring thật.

**M2-AT-10** (Draft 10, line 318), method "Contract/unit và persistence integration":

> Given locale vi-VN, tuổi nguyên 36/120 và hàng cũ ngoài khoảng; when serialize/persist/read profile revision và thử tạo StoryRun; then metadata được giữ, hai biên hợp lệ; hàng cũ ngoài 36–120 không đủ điều kiện tạo StoryRun và bị từ chối rõ ràng, không clamp. Test không giả định DB chặn 121. Hành vi StoryRun với tuổi cũ 121–155 chưa được xác minh.

**Database rules of the baseline** (Draft 10, section 5.3):

> 4. DB task-owned: tối đa một upgrade tới target revision đã pin. ... Nhánh irreversible: upgrade disposable rồi dừng.
> 5. Không drop DB/cleanup mặc định. Chỉ xóa rows do test tạo, có owner rõ và FK order, trong approval.

D-151 condition C1 keeps the guardrail "không dùng upgrade heads làm đích M2 mặc định". Condition C4 limits "must run and pass" to cases approved in the relevant Task Approval. Condition C2 asks that the layer of M2-AT-10 be stated; this gate covers its persistence and route layer only as section 6 describes.

The concrete cases come from the S2 plan whose scope the owner approved: `plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md`, SHA-256 `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331`, section 4, marked "future evidence only; NOT RUN".

## 3. Deviations from the baseline, for the owner's explicit acceptance

| ID | Baseline clause | What this gate does instead | Why |
|---|---|---|---|
| DV-1 | "recovery không tạo duplicate" after restart | Shows persistence only: after a real process stop and start the same rows are read, a same-key cancel replay returns the stored response, the lock stays released, one new create succeeds, and row counts do not change across the restart | A text search of the application factory, both runtimes, the repository and the service found no start-up recovery or reconciliation code for Parent story runs |
| DV-2 | "stale result không được accepted" after restart | Not shown after restart. Shown before restart at repository level only (section 6, level R) | After a cancel the routes refuse before any provider call, with other codes; a late result can arrive only inside the request that spans the cancel, and a restart ends that request |
| DV-3 | Late-result behaviour through the route | Repository level only; no HTTP status or envelope evidence from PostgreSQL. The HTTP mapping stays covered by the existing offline test `tests/contract/test_parent_ai_late_result_guards.py` | Owner's choice of the reduced gate: the router constructs provider clients inline, so HTTP-level evidence would need a fake provider module, a cross-process pause channel and full staging of a run |
| DV-4 | "Parent/Teacher" actors | Parent only | The story-run routes admit only the Parent role |
| DV-5 | "không hơn một active run/job/receipt hoặc side effect" | Asserts runs, inputs and receipts, and that no AI-job or outbox row is created by create or cancel | Create and cancel create no job in the current code |
| DV-6 | "Given run qua PREPARATION_REVIEW" | The run is put into `PREPARATION_REVIEW` by direct SQL, with seeded understanding and asset rows, then cancelled through the route | Reaching that state through the routes needs a provider |
| DV-7 | M2-AT-10: "hàng cũ ngoài 36–120 ... bị từ chối rõ ràng" and "Test không giả định DB chặn 121" | Asserts that PostgreSQL refuses to store a profile revision of 121 or 155 months, and a run row with such an age. No run creation at those ages reaches PostgreSQL. The service-level 422 stays offline evidence. This inverts the baseline sentence | Both `parent.profile_revisions` and the run's stored age carry a 36-to-120 check; the wider range exists only in a BE1 table this path does not read (owner decision PG-D8) |
| DV-8 | M2-AT-10: "locale vi-VN", "metadata được giữ" | Locale not covered. Metadata: the stored profile revision is read back and compared for the two in-range cases | The Parent schema has no locale field |
| DV-9 | Real identity and role wiring | A synthetic token verifier replaces the Firebase verifier. The Parent-role check itself runs for real against seeded adult-identity rows. The production BE1 role adapter of D-190 is not exercised | External identity provider |
| DV-10 | Rows reached through product paths | Identities, profiles and several run states are seeded by direct SQL (section 7) | No provider; no route creates them without one or without the pilot composition |
| DV-11 | "Không drop DB/cleanup mặc định" | A rehearsal container and its volume are removed by a named owner command before the next rehearsal. The gate container is kept | A container is created for one rehearsal and holds nothing else |
| DV-12 | M2-AT-09 before S2 exit; the proposed S3 condition | Not covered. M2-AT-09 has no result after this gate | Separate gate G2, not yet planned |

## 4. Owner decisions taken (planning direction, not approvals)

The six proposals of Draft 1 that the owner accepted with the words "chấp nhận 6 đề xuất", as they stood then, and what has become of each:

| ID | Proposal as accepted | Now |
|---|---|---|
| PG-D1 | Test the S2 Draft 18 section 4 cases on PostgreSQL through the composed routes, late-result cases driven by synthetic results | Stands, narrowed by the reduced gate (DV-3) |
| PG-D2 | Rehearsal and gate are owner-run with prepared command cards; the session verifies outputs read-only and holds no database credential | Stands |
| PG-D3 | Keep the production BE1 Parent-role adapter not covered | Stands (DV-9) |
| PG-D4 | "Restart" as a new application instance and a new database connection reading the same state, without an operating-system process stop | **Withdrawn.** Given before the baseline sentence was shown. Replaced by "Restart thật": a real operating-system process stop and start |
| PG-D5 | Other baseline extras (job ownership, locale) recorded as not covered | Stands (DV-5, DV-8) |
| PG-D6 | A new database on the local PostgreSQL 17 service, port 5433 | **Superseded** by PG-D9 and PG-D14 |

Later decisions, each with the owner's words: PG-D8 "Kiểm DB từ chối" (DV-7). PG-D9 "Test lun DB trên Docker đi". PG-D14 "Container riêng": a dedicated container, not the repository's compose service. PG-D13 "Hai gate": G1 for M2-AT-08 and 10, G2 for M2-AT-09. PG-D12 "Cho bản giả" (a provider stand-in): **no longer used**, since the owner then chose the reduced gate, "ok v là rút gọn đi". PG-D7 (explicit confirmation of S3-D1, S3-D2 and S3-D4 of S3 Draft 7) is unanswered and does not block this gate. The identifiers PG-D10 and PG-D11 were used in Draft 2 for test-file policy and output location; they are proposals in section 10.

Owner-supplied fact: local PostgreSQL 17 listens on 5433 and PostgreSQL 18 on 5432, and Docker uses 5432. This gate uses neither port.

## 5. Database: one dedicated container per run

Proposals to be fixed in the approval text. Nothing here has been run; the Docker engine was not running when the session looked.

- **Image:** `postgres:17-alpine`, as named in the repository's `compose.yaml`, pinned by its repository digest (the manifest digest, not the local image identifier), which the owner reports. If absent the owner pulls it; that is the only network use and it is the owner's action. Alpine has no real system locales, so database collation behaves like C; no case orders text in SQL.
- **Container:** created by the owner from a card; own name and own named volume; PostgreSQL published only as `127.0.0.1:<port>:5432` on an approved port that is none of 5432, 5433 or 55432; password authentication, never trust; not part of the compose project. A failure to bind the port stops the run before anything else.
- **Role and database:** the bootstrap superuser is used once, inside the container, to create one login role that is not a superuser and one empty database owned by it. No migration needs a superuser (reviewer's reading of every migration: no extension, role or grant statements). Migration and tests connect only as that role and never run `CREATE DATABASE`, `DROP DATABASE`, `ALTER ROLE` or `GRANT`.
- **Run marker:** the card stores a random run identifier as a database-level custom setting and every later step reads it back with `current_setting` and compares it with the card's record. The server-side port is always 5432 inside a container and proves nothing.
- **Password:** generated by the card into a password file outside the repository. Alembic and the application read only a database URL setting, so the URL carries no password and the client library takes it from the password file; the variable naming that file is the one libpq variable the cards do not clear. Outputs are scanned for the password before they are kept.
- **Lifecycle:** rehearsal containers are removed as in DV-11. The gate container is stopped after the run and kept with its volume until the owner says otherwise.

## 6. Cases

**Through the route, on PostgreSQL:**

| # | Case | Expected |
|---|---|---|
| 08-01a | Unique-index path, deterministic. A second connection holds an uncommitted insert of an active run for the same account. The API create is sent; the test waits until the database reports that session waiting on a lock (with a timeout); the held transaction commits | Exactly 409 `ACTIVE_RUN_EXISTS`. Exercises the partial unique index and the driver's constraint-name mapping |
| 08-01b | Natural race: two creates released together, same Parent, same payload, distinct idempotency keys | One 201, one 409 `ACTIVE_RUN_EXISTS`; one run, one input row, one `CREATE_RUN` receipt; no AI-job or outbox row |
| 08-02 | Same-key create replay | The saved 201 |
| 08-03 | Cancel success | 202; `DELETE_PENDING`; active-owner column cleared; receipt body with `purge_state` PENDING; no AI-job or outbox row |
| 08-03p | Cancel of a run in `PREPARATION_REVIEW` (state and its understanding and asset rows seeded by SQL, DV-6) | As 08-03; every seeded input, understanding, asset and earlier receipt row is unchanged afterwards (D-127 retention) |
| 08-04 | Same-key cancel replay after the revision advanced | The recorded 202, before any revision comparison; nothing written |
| 08-05 | Same run, same key, different request | 400 `INVALID_IDEMPOTENCY_KEY` |
| 08-06 | `run_revision` | Equals `story.runs.revision`; +1 per committed state-changing command; unchanged by read, replay, no-op |
| 08-07 | Stale `expected_revision` | 409 `STALE_REVISION`; no write |
| 08-08 | Missing `expected_revision` | 400 `INVALID_REQUEST`; `field_errors` names `expected_revision`; no change |
| 08-09 | Cross-run reuse of a cancel key (create A, cancel A, create B, reuse A's key on B) | 400 `INVALID_IDEMPOTENCY_KEY` |
| 08-14 | Cancel in COMPLETED, FAILED, DELETE_PENDING, sending the correct current revision | 409 with code `INVALID_STATE_TRANSITION` each. COMPLETED and FAILED are seeded by SQL (DV-10) |
| 08-15 | Ownership and lock release | Non-owner cancel or read: 404 `RESOURCE_NOT_FOUND`; after cancel the run is not returned as active and the same Parent can create again |
| 08-16 | Job-status evidence through the two owner reads | `run_state`, `job_state`, `retryable`, `error_code` readable by the owner; 404 for a non-owner |

Numbering follows Draft 18's sixteen rows; rows 10 to 13 of Draft 18 (late results and the artwork-route envelope) are not route cases here (DV-3).

**Level R — late-result guards at repository level, on PostgreSQL** (Draft 18 rows 10 to 12): with a run in `DELETE_PENDING`, the four recording calls (story completion; artwork-analysis success; artwork failure or unknown; story failure or unknown) each raise the expected code (`INVALID_STATE_TRANSITION`; `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING` for artwork success) and change no row. The session is rolled back before a second connection asserts. This is a call into the repository from the test process, not route evidence.

**Restart leg** (DV-1, DV-2): the test starts the API as a child process, performs create and cancel through it, records its process identifier, terminates it abruptly at operating-system level, checks that the identifier is gone and the port refuses connections, starts a new process and records the new identifier. Through the new process: the owner read shows the same `DELETE_PENDING` state and revision; the active-run read returns none; a same-key cancel replay returns the recorded 202 and writes nothing; a new create by the same Parent succeeds exactly once. Row counts for runs, inputs and receipts are equal immediately before the stop and immediately after the start.

**M2-AT-10:**

| # | Case | Expected |
|---|---|---|
| 10-01, 10-02 | New run from a stored profile aged 36, and 120, months | 201; `INPUT_PROCESSING`; one run row, one input row, one `CREATE_RUN` receipt; no AI-job or outbox row; the stored profile revision read back equals what was seeded |
| 10-03, 10-04 | Inserting a profile revision of 121, and 155, months; and a run row carrying such an age | PostgreSQL refuses each insert with a check violation; nothing is stored (DV-7) |

**Repetition inside one run:** cases 08-01a and 08-01b are each executed a fixed number of times set in the approval text, every execution on a fresh Parent account, and every execution must pass. This is repetition of a deterministic expectation, not a retry: a single failing execution fails the gate.

## 7. Seeding and isolation

All seeding is done by the test, as the dedicated role, by direct SQL, and is listed in the evidence (DV-10):

| Seeded | For |
|---|---|
| Adult-identity rows with state active, role Parent, the synthetic issuer and an account identifier; one per test account, two where a non-owner is needed | Every route case; the real Parent-role check reads them |
| A Parent child profile of synthetic origin with a profile revision at 36 months, and one at 120 months | 10-01, 10-02, and every create |
| A run moved to `PREPARATION_REVIEW` with understanding and asset rows | 08-03p |
| Runs set to COMPLETED and FAILED | 08-14 |
| A held, uncommitted active run on a second connection | 08-01a |

Rules: every case uses its own Parent account, so no case depends on another's leftovers; the run committed by the holder in 08-01a belongs to an account no other case uses; the test deletes nothing. The table and column names are taken from the models when the test is written; this plan does not fix them.

## 8. Doubles, launcher, guards

**Doubles.** Allowed: assigning a synthetic token verifier to the runtime's verifier field after the application is created (the form the earlier Gate P2 test used); assigning a storage or scanner stand-in on the application state if start-up needs one. Not allowed: dependency overrides; replacing the database session, the runtime object, any repository or service; rebinding names in any application module; any provider stand-in.

**Launcher.** A test-only module that builds the real application in the test environment setting, assigns the synthetic verifier, installs the socket guard and serves on a loopback port. Its environment is fixed in the approval text: environment name `test`; the passwordless database URL and the password-file variable; the artifact root under the repository's git-ignored `tmp/m2-s2-pg-gate/`; the StoryRun-lite demo flag off; no provider setting; the synthetic-pilot flag off. With the pilot flag off, profiles cannot be created through the profile route, which is why they are seeded. If the application cannot be built and served this way without a source edit, that is a stop condition.

**Guards.**

1. Cards clear every database URL variable (`S1A_P_ALEMBIC_DATABASE_URL`, `SKETCH2LIFE_DATABASE_URL`, `S1A_P_TEST_DATABASE_URL`, `BE1_TEST_DATABASE_URL`) and the libpq variables for host, port, database, user, service and options, then set exactly one URL and the password-file variable. Review R1 confirmed that Alembic takes its URL from the first of those variables without any identity check.
2. The settings classes also read a `.env` file one level above the backend root of whichever checkout is imported. The card runs from this worktree, prints the imported package path in the probe, and stops if that path is not under this worktree or if a `.env` file exists at this worktree's root. (The main checkout has such a file; this worktree has none.)
3. Read-only probe before migration: URL host 127.0.0.1 and the approved port; run marker matches; allowlisted database name; the dedicated role with `rolsuper` false; major version 17; no tables in any non-system schema; no `alembic_version` table. Otherwise nothing runs.
4. Names: only the approved gate and rehearsal database names. `sketch2life_m2_s1a`, `sketch2life` and `postgres` are refused explicitly.
5. Migration target: a pinned list of revisions fixed in the approval text, not an unqualified "heads". (Two independent readings of the scripts count ten heads; Alembic was not run.)
6. Each test file repeats the probe, with "no rows in any migrated table" in place of "no tables", before any seeding; records table counts before and after; fails rather than skips when a guard does not hold.
7. A socket guard in the test process and in the launcher refuses any connection that is not to 127.0.0.1. The operating-system egress block is used as well if loopback works under it; probed in P0 for the three flows test to API, test to PostgreSQL, API to PostgreSQL.
8. Outputs and base temp under `tmp/m2-s2-pg-gate/`. Pytest with short tracebacks, no local-variable dump, no JUnit log capture, no cache provider.

## 9. Phases, pins, claim, stop conditions

| Phase | Content | Who |
|---|---|---|
| P0 | Read-only preparation: the pinned migration list; table and column names for seeding; image digest from the owner; loopback probe under the egress block. Independent review of this plan. Then the approval text with exact allowlist, cards, port, names, repetition count and ceilings, carrying section 3 for the owner's acceptance item by item | Session; owner; reviewer |
| P1 | Write the test file and the launcher. No source file is edited | Session |
| P2 | Static checks on the new files before anything runs: syntax, Ruff, Mypy. Constant names avoid the words the repository security validator flags | Session |
| P3 | Offline collection; a table mapping every case of section 6 to its tests | Session |
| P4 | Rehearsals, each on a new container. Exit after at least three consecutive full passes; any intermittent result is a failure to be understood | Owner-run |
| P5 | The gate: new container, guarded migration, one run | Owner-run; ceiling 1 |
| P6 | Evidence report stating section 3 and the limits below; independent review; owner acceptance | Session; reviewer; owner |

Pins at P5: commit and clean status; hashes of the test file and launcher; image digest; container name, port and run marker; migration list and resulting `alembic_version` rows; `pyproject.toml` and `uv.lock` hashes; interpreter and tool versions; role and database identity; table counts before and after; old and new process identifiers of the restart; exact commands and exit codes; output hashes.

**What a pass may be claimed to show:** the Draft 18 route cases 1 to 9 and 14 to 16 for M2-AT-08, the D-127 cancel from `PREPARATION_REVIEW` with retention, the late-result guards at repository level, persistence across a real process restart, and the M2-AT-10 cases above — on one PostgreSQL 17 container, through the composed routes, with a synthetic token verifier and SQL-seeded data. **What it does not show:** everything in section 3; behaviour with a real provider; HTTP-level late-result behaviour on PostgreSQL; anything about M2-AT-09. Whether that is enough for the M2-AT-08 and M2-AT-10 rows of the S3 ledger is decided by the owner's acceptance of DV-1 to DV-12, not by the pass.

Stop and return to the owner if: a case needs a source change; the application cannot be served by the launcher without one; a rehearsal failure is a product defect; the probe fails; the run marker differs; the imported package path is wrong or a `.env` is present; migrated revisions differ from the pinned list; a non-loopback connection is attempted; credential text appears in an output; a rehearsal is intermittent; a process cannot be terminated or the old one survives; the port cannot be bound; the egress block and loopback cannot be combined.

A failed gate leaves its container, volume and outputs in place and consumes the ceiling. Another attempt needs a new approval and a new container.

## 10. To be fixed in the approval text

- Loopback port; container, volume, role and database names (proposed database names: `sketch2life_m2_s2_gate`, `sketch2life_m2_s2_rehearsal`); repetition count for 08-01a and 08-01b.
- Test-file policy (proposal): new files under `backend/tests/integration/`, kept in the repository; they skip with a stated reason when the gate's variables are absent, and the gate card requires zero skipped tests. CI runs an explicit file list and is not affected.
- The owner's acceptance or refusal of each of DV-1 to DV-12.

## 11. Handling of review R2

N1: restart leg rewritten as persistence, late result after restart removed, claim narrowed (DV-1, DV-2, sections 6 and 9). N2: no provider stand-in (DV-3); level R only. N3: case 08-03p; DV-4, DV-5, DV-6. N4: password file with a passwordless URL (section 5). N5: guard 2. N6: abrupt termination with process-identifier evidence (section 6). N7: section 7. N8: section 4. N9: section 3 and section 9. N10: DV-7, with the run-table check added. N11: guards 3, 6 and 7. N12: repetition rule in section 6. N13: no message assertion remains in this gate. N14: lock-wait detection in 08-01a. N15: section 5. N16: no absolute path; P2 naming note; launcher environment in section 8.

## 12. Not established by this draft

- Nothing was executed; no container, database or port was contacted.
- Whether the image is present locally, and its digest.
- Whether the pinned migration list applies cleanly to an empty database as a non-superuser.
- Whether the application builds and serves from the launcher in the test environment setting without a source edit and without touching the network; the scanner and storage constructors were not read.
- Whether the client library takes the password from the password file with the URL forms Alembic and the application build.
- Whether an abruptly terminated launcher on Windows leaves a surviving child process.
- Whether Docker's published loopback port is reachable while the egress block is active.
- The exact tables and columns for seeding, including what an understanding or asset row needs.
- The reviewers' case-by-case readings of the code are readings, not runs.
- Whether co-owner work on another branch already has PostgreSQL tests for these routes.
- Size: one launcher and roughly twenty test cases. No estimate in days is offered.

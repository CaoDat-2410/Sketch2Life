# FEAT-063 M2 — PostgreSQL acceptance gates for M2-AT-08, 09 and 10 — plan Draft 3

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. It authorizes no code or test edit, no container, database, migration or connection, no process start, no test run, no network access, no commit or push.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. Not independently reviewed.
- **Predecessors, unchanged:** Draft 1 (SHA-256 `53B2A08E38AD2AFC1632D73A266CD831611C06236BB6CC0912D74FABF6501A62`; cold review R1 NOT READY, 2 P1 / 9 P2 / 6 P3, `evidence/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT1_COLD_REVIEW_R1_20261117.md`) and Draft 2 (24,380 bytes, SHA-256 `924F90D4CD61C7EA58EA0D70D0B6A18683F9273AAF93B58DC5A1953AA0BB01A5`; not reviewed; superseded on the database host). Draft 3 is self-contained: a reader needs neither predecessor.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a` (pushed; draft PR #29).
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Purpose and framing

M2-S2 was closed by the owner on 2026-11-17 on offline evidence, with recorded debt. That closure record stands. The M2 planning baseline the owner accepted under D-151 (`plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md`, SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1`) makes M2-AT-08 and M2-AT-09 a condition for leaving S2 and, as a proposed S3 condition, requires every M2-AT other than 05, 06 and 07 to run and pass. These gates produce that evidence late. They are a precondition for an honest M2 closure. They change no source file. A product defect they expose is reported to the owner (section 9).

Not resolved here, from D-151 itself: condition C4 limits "must run and pass" to acceptance cases approved in the relevant Task Approval; the baseline's S3 row is a condition the owner "must accept in the S3 Task Approval"; condition C5 (whether the five-route rule covers S2 route tests) was left open and the S2 Task Approval went ahead with these routes.

## 2. The baseline text, quoted

**M2-AT-08** (Draft 10, line 316):

> Given synthetic Parent/Teacher cùng owner lock có quyền hợp lệ; when concurrent separate POST /v1/story-runs requests submit cùng active owner; then có không hơn một active run/job/receipt hoặc side effect; không áp đặt loser status/error nếu contract chưa định nghĩa. Given run qua PREPARATION_REVIEW; when POST /v1/story-runs/{id}/cancel; then áp dụng D-127: DELETE_PENDING, nhả active-owner trong transaction, giữ result/assets/receipts và không coi là đã xóa. Replay/cancel lặp không tạo side effect trùng. Sau đó dừng tiến trình hệ điều hành thật, khởi động process mới với app composition mới trên cùng DB; recovery không tạo duplicate và stale result không được accepted. Recreate object trong cùng process không tính là restart.
>
> PostgreSQL integration qua route, process stop/start thực, composition/repository/wiring thật.

**M2-AT-09** (Draft 10, line 317):

> Given child request tổng hợp và actor/device hợp lệ; when POST /api/be1/v1/assistance-requests, GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status và POST /api/be1/v1/assistance-requests/{assistance_id}/cancel đi qua route thật; then auth, app composition, dependency wiring và PostgreSQL đều thật, không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Bao phủ các trạng thái: success chỉ được expose sau durable committed SUCCEEDED; timeout phải giữ durable request/job/receipt facts nhưng không có authoritative successful result, không tự định nghĩa transition; orphan theo FEAT-064 approval là analysis invocation SUCCEEDED trong khi job RUNNING, không có result ref hoặc authoritative receipt, nên API/status không expose accepted. Dừng process hệ điều hành thật, khởi động app process mới cùng DB và kiểm tra recovery/status không công bố stale/orphan result như accepted. Timeout/recovery/terminal semantics chưa có owner quyết định thì giữ gate mở, không bịa status/error. Bắt buộc trước khi thoát S2 và trước D9 hoặc frontend/client integration.
>
> PostgreSQL route integration qua real app composition/auth/dependency wiring và process restart.

**M2-AT-10** (Draft 10, line 318), method "Contract/unit và persistence integration":

> Given locale vi-VN, tuổi nguyên 36/120 và hàng cũ ngoài khoảng; when serialize/persist/read profile revision và thử tạo StoryRun; then metadata được giữ, hai biên hợp lệ; hàng cũ ngoài 36–120 không đủ điều kiện tạo StoryRun và bị từ chối rõ ràng, không clamp. Test không giả định DB chặn 121. Hành vi StoryRun với tuổi cũ 121–155 chưa được xác minh.

**Database rules of the baseline** (Draft 10, section 5.3):

> 4. DB task-owned: tối đa một upgrade tới target revision đã pin. ... Nhánh irreversible: upgrade disposable rồi dừng.
> 5. Không drop DB/cleanup mặc định. Chỉ xóa rows do test tạo, có owner rõ và FK order, trong approval.
> 6. backend/tests/integration/ai_jobs/test_migrations.py dùng maintenance connection để tạo/xóa DB; phần DB của test không chạy trên DB chính nếu chưa có thiết kế/approval riêng.

D-151 condition C1 adds that the guardrail "không dùng upgrade heads làm đích M2 mặc định" remains in force.

The S2 plan whose scope the owner approved (`plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md`, SHA-256 `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331`, section 4, marked "future evidence only; NOT RUN") refines these rows into concrete cases and defines loser status and codes the baseline left open. The gates test the Draft 18 cases and the baseline legs Draft 18 lacks (process restart; timeout and orphan for assistance).

## 3. Owner decisions taken (planning direction, not approvals)

| ID | Decision | Owner's words, 2026-11-17 |
|---|---|---|
| PG-D1 | Draft 18 section 4 cases, on PostgreSQL, through the composed routes | "chấp nhận 6 đề xuất" |
| PG-D2 | Rehearsals and gates are owner-run with prepared command cards; the session verifies outputs read-only and holds no database credential | same |
| PG-D3 | Production BE1 role adapter not in scope (section 6 notes what does run for real) | same |
| PG-D4 | Real operating-system process stop and start. An earlier answer for "new application instance", given on the session's recommendation before the baseline sentence was shown, is withdrawn | "Restart thật" |
| PG-D5 | Job ownership beyond case 08-16 and locale persistence are recorded as not covered | "chấp nhận 6 đề xuất" |
| PG-D6 | **Superseded.** Originally the local PostgreSQL 17 service on port 5433 | replaced by the next two rows |
| PG-D9 | The database test runs on Docker | "Test lun DB trên Docker đi" |
| PG-D14 | A dedicated container for the gate, not the `postgres` service of the repository's `compose.yaml` | "Container riêng" |
| PG-D8 | For 121 and 155 months: on PostgreSQL assert that the database refuses to store such a profile revision; the service-level 422 stays offline evidence; the two layers are reported separately | "Kiểm DB từ chối" |
| PG-D12 | A deterministic stand-in at the provider client boundary is allowed | "Cho bản giả" |
| PG-D13 | Two gates with separate approvals and separate one-shot runs: G1 for M2-AT-08 and M2-AT-10, G2 for M2-AT-09 | "Hai gate" |

Owner-supplied fact: on this machine PostgreSQL 17 listens on 5433 and PostgreSQL 18 on 5432, and Docker uses 5432. Neither port is used by these gates.

## 4. Database: a dedicated container per run

Everything in this section is a proposal to be fixed in each gate's approval text. Nothing here has been run; when the session looked on 2026-11-17 the Docker engine was not running, so local images and containers were not inspected.

- **Image:** `postgres:17-alpine`, the image the repository's `compose.yaml` already names. It is pinned by digest: the owner reports the digest of the local image and the approval text records it. If the image is not present the owner pulls it; that is the only network use in this plan and it is the owner's action.
- **One container per run**, created by the owner from a command card, named for its purpose (for example `s2l-m2s2-g1-rehearsal-1`, `s2l-m2s2-g1-gate`), with its own named volume, publishing PostgreSQL only as `127.0.0.1:<port>:5432` on a port fixed in the approval text that is none of 5432, 5433 or 55432. It is not part of the repository's compose project and shares no volume or network with it.
- **Role and database:** the container's bootstrap superuser is used once, by the card, to create one login role that is not a superuser and one empty database owned by it (`sketch2life_m2_s2_gate`, or `sketch2life_m2_s2_rehearsal` for rehearsals). Migrations and tests connect only as that role. Tests never run `CREATE DATABASE`, `DROP`, `ALTER ROLE` or `GRANT`.
- **Run marker:** the card stores a random run identifier in the database at creation (a database-level setting). Every later step first reads it back and compares it with the identifier in the card's own record. This proves the step is talking to this run's container. The server-side port is always 5432 inside a container, so the port alone proves nothing.
- **Why this is safer than the local service:** the accepted S1a database `sketch2life_m2_s1a` lives on the local PostgreSQL 17 service. A container on its own port cannot reach it. The risk that remains is a stale environment variable steering Alembic elsewhere (section 5).
- **Lifecycle:** a rehearsal container and its volume are removed by an explicit, named command in the next rehearsal's card, run by the owner; a gate container is stopped after the run and kept with its volume as evidence until the owner says otherwise. This is the gate's answer to the baseline's "no drop by default": the only thing ever removed is a container that was created for one rehearsal and named in the card.
- **Passwords:** generated by the card into files outside the repository; passed to Docker and to the tests by file, not on a command line and not inside a URL variable. Saved outputs are scanned for them before being kept.

## 5. Guards

Review finding P1-1, confirmed by the session: `backend/alembic/env.py` takes its URL from `S1A_P_ALEMBIC_DATABASE_URL` first, then from the core database setting, and connects with no identity check.

1. Migration runs only from a card that clears every database URL variable (`S1A_P_ALEMBIC_DATABASE_URL`, `SKETCH2LIFE_DATABASE_URL`, `S1A_P_TEST_DATABASE_URL`, `BE1_TEST_DATABASE_URL`) and the libpq routing variables, sets exactly one, and runs a read-only probe first.
2. The probe must show: host 127.0.0.1 and the approved port in the URL; the run marker; the allowlisted database name; the dedicated role with `rolsuper` false; major version 17; no user tables; no `alembic_version` table. Otherwise nothing runs.
3. Names: only the gate and rehearsal names are accepted. `sketch2life_m2_s1a`, `sketch2life` and `postgres` are refused explicitly.
4. The migration target is a pinned list of revisions, not an unqualified "heads". The list is produced in P0 by reading the migration scripts and is part of the approval text. (The reviewer counts ten heads by reading; not verified.)
5. Each test file repeats the probe before any fixture writes, requires an empty database at the start of a gate run, records table counts before and after, and fails rather than skips when a guard does not hold.
6. Outputs, base temp and artifact root are under `D:\GitHub\Sketch2Life\tmp\m2-s2-pg-gate\`. Pytest runs with short tracebacks, no local-variable dump and no JUnit log capture.
7. An in-process socket guard refuses every connection that is not to 127.0.0.1. The operating-system egress block is used as well if loopback traffic works under it; that is probed in P0. Three loopback flows are needed: test to API process, test to PostgreSQL, API process to PostgreSQL.

## 6. Test doubles and the launcher

Allowed, because they stand for external systems: a synthetic identity token verifier; a storage or scanner stand-in on the application state if start-up needs one; a deterministic stand-in at the provider client boundary (PG-D12).

Not allowed: overriding the database session, the runtime, device verification, the pilot runtime, the child-binding builder, or any repository or service object; monkeypatching any code under test.

Read from the code by the reviewer, not verified by a run: the story-run routes take the Parent role from the adult-identity table, so on a fully migrated database that check runs for real against seeded rows; the assistance device routes authenticate with a device grant and key and need no identity double.

Because the restart leg needs a separately started process, doubles cannot be injected by in-process overrides. A launcher module, test code only, builds the real application, installs the allowed doubles and serves it on a loopback port. The test starts it as a child process, stops it at operating-system level and starts a new one. The launcher is in the allowlist and among the pinned files. Whether the doubles can be installed from the launcher without editing any source file is not established; if they cannot, that is a stop condition.

## 7. Gate G1 — M2-AT-08 and M2-AT-10 (Parent story runs)

**Through the route on PostgreSQL:**

| # | Case | Expected |
|---|---|---|
| 08-01a | Unique-index path, deterministic: a second connection holds an uncommitted insert of an active run for the same account; the API create blocks on its insert; the held transaction commits | Exactly 409 `ACTIVE_RUN_EXISTS`; this exercises the index and the driver's constraint-name mapping |
| 08-01b | Natural race: two creates released together, same Parent, same payload, distinct idempotency keys | One 201, one 409 `ACTIVE_RUN_EXISTS`; one run, one `CREATE_RUN` receipt |
| 08-02 | Same-key create replay | The saved 201 |
| 08-03 | Cancel success | 202; `DELETE_PENDING`; active-owner column cleared in the same transaction; receipt body with `purge_state` PENDING |
| 08-04 | Same-key cancel replay after the revision advanced | The recorded 202, before any revision comparison |
| 08-05 | Same run, same key, different request | 400 `INVALID_IDEMPOTENCY_KEY` |
| 08-06 | `run_revision` | Equals `story.runs.revision`; +1 per committed state-changing command; unchanged by read, replay, no-op |
| 08-07 | Stale `expected_revision` | 409 `STALE_REVISION`; no write |
| 08-08 | Missing `expected_revision` | 400 `INVALID_REQUEST`; `field_errors` names `expected_revision`; no change |
| 08-09 | Cross-run reuse of a cancel key (create A, cancel A, create B, reuse A's key on B) | 400 `INVALID_IDEMPOTENCY_KEY` |
| 08-14 | Cancel in COMPLETED, FAILED, DELETE_PENDING, sending the correct current revision | 409 with code `INVALID_STATE_TRANSITION` each. COMPLETED and FAILED rows are seeded by direct SQL (stated limit) |
| 08-15 | Ownership and lock release | Non-owner cancel or read: 404 `RESOURCE_NOT_FOUND`; after cancel the run is not returned as active and the same Parent can create again |
| 08-16 | Job-status evidence through the two owner reads | `run_state`, `job_state`, `retryable`, `error_code` readable by the owner; 404 for a non-owner |

**Late results and the error envelope**, two evidence levels reported separately:

- Level R, repository on PostgreSQL: with the run in `DELETE_PENDING`, each late-result recording call (story completion; artwork success; artwork failure or unknown; story failure or unknown) raises its expected code (`INVALID_STATE_TRANSITION`, or `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING` for artwork success) and changes no row. The session is rolled back before a second connection asserts.
- Level H, HTTP through the route with the provider stand-in (08-10, 08-11, 08-12, 08-13): status 409, the same codes at top level, and the envelope: a message from the application's Vietnamese message set, a correlation id, `retryable` false, null retry-after and null field errors. The product wording of the message stays an open product decision; the test asserts membership, not a new wording.

**Restart leg**, after a committed cancel: the served API process is stopped at operating-system level and a new process started on the same database. Then: the owner read shows the same `DELETE_PENDING` state and revision; the active-run read returns none; a same-key cancel replay returns the recorded 202 and writes nothing; a late result is refused (level R, and level H through the new process); a new create by the same Parent succeeds exactly once; row counts for runs, inputs and receipts are unchanged across the restart itself.

**M2-AT-10:**

| # | Case | Expected |
|---|---|---|
| 10-01, 10-02 | New run from a trusted stored profile aged 36, and 120, months | 201; `INPUT_PROCESSING`; one run row, one input row, one `CREATE_RUN` receipt; no AI job or outbox row |
| 10-03, 10-04 | Storing a profile revision of 121, and 155, months (PG-D8) | The database refuses the row (check constraint `age_months BETWEEN 36 AND 120`); nothing is stored |

The service-level refusal (422 `INVALID_REQUEST` before any repository call) for 121 and 155 remains offline evidence from the existing unit tests. The report says plainly that no run-creation attempt at those ages reached PostgreSQL, because such a profile cannot exist there, and that the baseline sentence "Test không giả định DB chặn 121" predates the constraint.

## 8. Gate G2 — M2-AT-09 (assistance), outline only

G2 gets its own plan section and approval after a read-only survey of the seeding it needs (organisation, class, session, device, consent, pilot flags, AI-job rows). Cases: the three success operations of Draft 18 (submit 202 with receipt, device view and headers; status 200 with `submitted_to_teacher` only when an authoritative receipt exists; cancel 200, with the `If-Match` header the route reads stated in the test); timeout (durable request, job and receipt facts; no authoritative success; status does not report success); orphan (invocation SUCCEEDED while the job is RUNNING, no result reference or receipt; status `unknown`, not accepted); restart (process stop and start; status reads publish nothing stale or orphaned as accepted). The baseline says that where timeout, recovery or terminal semantics have no owner decision the gate stays open and nothing is invented: G2 asserts only what Draft 18 and the code already define and reports the rest as OPEN. States that cannot be produced through the route without a provider are seeded by direct SQL and listed.

G1 does not wait for G2. M2-AT-09 stays without a result until G2 has run.

## 9. Phases, pins, limits, stop conditions

| Phase | Content | Who |
|---|---|---|
| P0 | Read-only preparation: pinned migration list; image digest reported by the owner; loopback probe under the egress block; for G2 the seeding survey. Cold review of this plan. Then an approval text per gate with exact allowlist, cards, port, names and ceilings | Session; owner; reviewer |
| P1 | Write the test files and the launcher. No source file is edited | Session, under the allowlist |
| P2 | Static checks on the new files only, before anything runs: syntax, Ruff, Mypy | Session |
| P3 | Offline collection; a mapping table from every case to its tests | Session |
| P4 | Rehearsals, each on a new container. Exit only after at least three consecutive full passes with no retry inside the suite; any intermittent result is a failure to be understood | Owner-run |
| P5 | The gate: new container, guarded migration, one run, the concurrency tests repeated inside that run | Owner-run; ceiling 1 |
| P6 | Evidence report with the limits below; independent review; owner acceptance | Session; reviewer; owner |
| P7 | After G1 and G2: S3 Draft 8 | Session |

Pins recorded at P5: commit and clean status; hashes of every test file and the launcher; image digest; container name, port and run marker; the migration list and resulting `alembic_version` rows; `pyproject.toml` and `uv.lock` hashes; interpreter and tool versions; role and database identity; table counts before and after; exact commands and exit codes; output hashes.

A G1 pass shows the Draft 18 cases for M2-AT-08, the baseline restart leg and the M2-AT-10 cases above, on one PostgreSQL 17 container, through the composed routes, with a synthetic identity verifier and a provider stand-in. It does not show: the production BE1 Parent-role adapter path that D-190 names; behaviour with a real provider; anything about rows seeded by direct SQL beyond what the route does with them; run creation at 121 or 155 months on PostgreSQL; job ownership beyond 08-16; locale persistence; anything about M2-AT-09.

Stop and return to the owner if: a case needs a source change; the doubles cannot be installed without one; a rehearsal failure is a product defect; the probe fails or the database is not empty; the run marker does not match; migrated revisions differ from the pinned list; a non-loopback connection is attempted; credential text appears in an output; a rehearsal is intermittent; a process hangs or cannot be stopped cleanly; the egress block and loopback traffic cannot be combined; a baseline leg has no defined expected result.

A failed gate leaves its container, volume and outputs in place and consumes the ceiling. A further attempt needs a new approval and a new container.

## 10. Still to be fixed in the approval texts

- The loopback port, container and volume names, role name and database names.
- Test file policy (proposal): new files under `backend/tests/integration/`, kept in the repository; when the gate's variables are absent they skip with a stated reason, and the gate card requires zero skipped tests. CI runs an explicit file list and is not affected.
- Whether rehearsal containers are removed as proposed in section 4.
- PG-D7, carried over: explicit confirmation of S3-D1, S3-D2 and S3-D4 from S3 Draft 7. Not blocking.

## 11. Handling of review R1 of Draft 1

P1-1 (migration target unprotected): sections 4 and 5. P1-2 (restart): section 2 quotes the baseline; PG-D4; restart legs in sections 7 and 8. P2-3 (ages not storable): PG-D8, section 7. P2-4 (levels conflated): levels R and H, PG-D12. P2-5 ("disposable"): section 4 lifecycle. P2-6 (guards): section 5. P2-7 (doubles): section 6. P2-8 (message): section 7 level H. P2-9 (concurrency): cases 08-01a and 08-01b. P2-10 (governance): sections 1, 5 rule 4, 10. P2-11 (rehearsal exit, pins): section 9. P3 items: sections 4, 5, 7, 9.

## 12. Not established by this draft

- Nothing was executed; no container, database or port was contacted; the Docker engine was not running when queried.
- Whether the image is present locally and its digest.
- The count and names of migration heads, and whether the pinned list applies cleanly to an empty database.
- Whether a database-level setting is a workable run marker for a non-superuser role.
- Whether the application can be served by a launcher process, with the allowed doubles and start-up objects, without source changes and without touching the network.
- Whether Docker's published loopback port is reachable by the interpreter while the egress block is active.
- The seeding G2 needs.
- The reviewer's case-by-case reading of the code (no contradiction with Draft 18 found) is a reading, not a run.
- Whether co-owner work on another branch already contains PostgreSQL tests for these routes.
- Size: a process launcher, a provider stand-in and about twenty-five test cases for G1; G2 not sized. No estimate in days is offered.

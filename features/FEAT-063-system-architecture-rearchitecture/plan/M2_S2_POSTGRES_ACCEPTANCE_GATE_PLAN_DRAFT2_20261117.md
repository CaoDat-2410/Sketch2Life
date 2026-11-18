# FEAT-063 M2 — PostgreSQL acceptance gate for M2-AT-08, 09 and 10 — plan Draft 2

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. It authorizes no code or test edit, no database creation, migration or connection, no process start, no test run, no network access, no commit or push.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. Not independently reviewed.
- **Predecessor:** `plan/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT1_20261117.md`, 18,121 bytes, SHA-256 `53B2A08E38AD2AFC1632D73A266CD831611C06236BB6CC0912D74FABF6501A62`, unchanged. Cold review R1 of it: NOT READY, 2 P1 / 9 P2 / 6 P3 (`evidence/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT1_COLD_REVIEW_R1_20261117.md`). Section 10 lists how each finding is handled here.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a` (pushed; draft PR #29).
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Purpose and framing

M2-S2 was closed by the owner on 2026-11-17 on offline evidence, with recorded debt. That closure record stands. The M2 planning baseline the owner accepted under D-151 (`plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md`, SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1`) makes M2-AT-08 and M2-AT-09 a condition for leaving S2 and, in a proposed S3 condition, requires every M2-AT other than 05, 06 and 07 to run and pass. This gate produces the evidence the baseline asked for before S2 exit. It is therefore the late completion of an S2 exit criterion, and a precondition for an honest M2 closure. It changes no source file. A product defect it exposes is reported to the owner (section 8).

Two qualifications from D-151 itself, which this plan does not resolve: condition C4 limits "must run and pass" to acceptance cases approved in the relevant Task Approval, and the S3 row of the baseline is a condition "the owner must accept in the S3 Task Approval". Condition C5 (whether the five-route rule also covers S2 route tests) was left open by D-151; the S2 Task Approval went ahead with these routes.

## 2. The baseline text, quoted

These rows are quoted so that every decision below is taken against the words of the accepted baseline. Draft 11's rows for M2-AT-08 and 09 are reported by the reviewer as identical to Draft 10's.

**M2-AT-08** (Draft 10, line 316), expected behaviour and method:

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

The S2 plan whose scope the owner approved (`plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md`, section 4, marked "future evidence only; NOT RUN") refines these rows into concrete cases: 16 for M2-AT-08, three success operations for M2-AT-09, four ages for M2-AT-10. Draft 18 defines loser status and codes that the baseline left open. The gate tests the Draft 18 cases **and** the baseline legs Draft 18 does not have (process restart; timeout and orphan for assistance).

## 3. Owner decisions already taken (planning direction, not approvals)

| ID | Decision | Owner's words, 2026-11-17 |
|---|---|---|
| PG-D1 | Draft 18 section 4 cases, on PostgreSQL, through the composed routes | "chấp nhận 6 đề xuất" |
| PG-D2 | Rehearsal and gate are owner-run with prepared command cards; the session verifies outputs read-only | same |
| PG-D3 | Production BE1 role adapter not in scope (but see section 5: the story routes' own role check runs for real) | same |
| PG-D4 | **Real operating-system process stop and start.** The first answer, option (a) "new application instance", was given on the session's recommendation before the baseline sentence had been shown and is withdrawn. After the sentence was quoted the owner chose | "Restart thật" |
| PG-D5 | Other baseline extras recorded as not covered: now limited to job ownership beyond case 08-16 and locale persistence | "chấp nhận 6 đề xuất" |
| PG-D6 | New databases on the local PostgreSQL 17 service, loopback port 5433. Port 5432 (PostgreSQL 18) is not used; the owner states Docker uses it | "postgreSQL chạy 5433 ở 17 và 5432 ở 18 nhưng ko xài 5432 vì 5432 xài ở docker" |

Database names remain proposals not yet accepted: `sketch2life_m2_s2_gate`, `sketch2life_m2_s2_rehearsal`.

## 4. Case list

**M2-AT-08, through the route on PostgreSQL** — cases 08-01 to 08-09 and 08-14 to 08-16 as in Draft 1 section 3 (competing creates; create replay; cancel success; cancel replay; mismatched key; revision read and increment; stale revision; missing revision; cross-run key; wrong-state cancel; ownership and lock release; job-status reads), with these corrections from the review:

- 08-01 is two tests. Deterministic: a second connection holds an uncommitted insert of an active run for the same account, the API create blocks on the insert, the held transaction commits, and the response must be exactly 409 `ACTIVE_RUN_EXISTS`; this exercises the unique index and the driver's constraint-name mapping. Natural race: two threads released together; one 201, one 409, one run, one receipt.
- 08-08 asserts `field_errors` naming `expected_revision`.
- 08-09 setup: create A, cancel A, create B, reuse A's cancel key on B.
- 08-14 asserts the code `INVALID_STATE_TRANSITION` and sends the correct current revision, so that a stale-revision 409 cannot pass for the wrong reason. COMPLETED and FAILED rows are seeded by direct SQL; that is an evidence limit to state.
- 08-13 asserts a Vietnamese message (membership in the application's known message set), not merely a non-empty one. The product wording stays open as a product decision only.

**M2-AT-08, late results (08-10, 08-11, 08-12) and the error envelope (08-13)** — two evidence levels, kept apart in the report:

- Level R (repository on PostgreSQL): with the run in `DELETE_PENDING`, each late-result recording call raises the expected error code and changes no row. The test rolls the session back before asserting from a second connection.
- Level H (HTTP envelope): status 409, top-level code and envelope fields through the route. The route reaches these guards only after a provider client call, which this gate forbids. Level H therefore needs owner decision PG-D12.

**M2-AT-08, restart leg (new)** — after a cancel has been committed, the served API process is stopped at operating-system level and a new process is started on the same database. Then: the owner read shows the same `DELETE_PENDING` state and revision; the active-run read returns no run; a same-key cancel replay returns the recorded 202 and writes nothing; a late result is refused as in level R; a new create by the same Parent succeeds exactly once. "Recovery không tạo duplicate" is asserted as unchanged row counts for runs, inputs and receipts across the restart.

**M2-AT-09** — the three success operations of Draft 18 (09-01 submit, 09-02 status, 09-03 cancel, with the `If-Match` header the cancel route reads stated in the test), plus the baseline legs:

- 09-04 timeout: durable request, job and receipt facts exist; no authoritative success; the status read does not report success.
- 09-05 orphan: analysis invocation SUCCEEDED while the job is RUNNING, no result reference or authoritative receipt; the status read does not expose accepted (Draft 18: processing state `unknown`).
- 09-06 restart: process stop and start on the same database; status reads for the success, timeout and orphan rows publish nothing stale or orphaned as accepted.

The baseline says that where timeout, recovery or terminal semantics have no owner decision the gate stays open and no status or error is invented. Cases 09-04 to 09-06 assert only what Draft 18 and the code already define (non-terminal, not success, `unknown`); anything beyond that is reported as OPEN, not asserted. States that cannot be produced through the route without a provider (a SUCCEEDED job, an orphan) are seeded by direct SQL and listed as such.

**M2-AT-10** — 10-01 and 10-02 (trusted stored ages 36 and 120 create a run; one run row, one input row, one receipt; no AI job or outbox row) run on PostgreSQL. Cases 10-03 and 10-04 (121 and 155 months) cannot be driven from a stored profile: `parent.profile_revisions` has `CHECK age_months BETWEEN 36 AND 120` and an immutability trigger. The baseline sentence "Test không giả định DB chặn 121" was written before that constraint existed in this form. Owner decision PG-D8.

## 5. Test doubles: the line

Allowed, because they stand for external systems: replacing the identity token verifier with a synthetic one; a storage or scanner stand-in on the application state if start-up needs one; and, only if PG-D12 says so, a deterministic stand-in at the provider client boundary.

Not allowed: overriding the database session, the runtime, device verification, the pilot runtime, the child-binding builder, or any repository or service object; monkeypatching any of the code under test.

Consequences read from the code by the reviewer, not yet verified by a run: the story-run routes take the Parent role from the adult-identity table, so on a fully migrated database that check runs for real with seeded rows; the assistance device routes authenticate with a device grant and key and need no identity double.

Because the restart leg needs a separately started process, the doubles cannot be injected by in-process overrides. A small launcher module, test code only, builds the real application, installs the allowed doubles and serves it on a loopback port. The launcher is part of the allowlist to be approved and of the pinned files.

## 6. Database safety

Review finding P1-1, confirmed: `backend/alembic/env.py` takes its URL from `S1A_P_ALEMBIC_DATABASE_URL` first and then from the core database setting, and connects without any identity check. The accepted S1a database `sketch2life_m2_s1a` is on the same server. A stale variable would migrate it irreversibly.

Rules of this gate:

1. The owner creates, outside any test: one login role that is not a superuser and owns nothing else, and two empty databases owned by it. Tests and cards never run `CREATE DATABASE`, `DROP`, `ALTER ROLE` or `GRANT`.
2. Migration runs only from a command card that: clears every database URL variable (`S1A_P_ALEMBIC_DATABASE_URL`, `SKETCH2LIFE_DATABASE_URL`, `S1A_P_TEST_DATABASE_URL`, `BE1_TEST_DATABASE_URL`) and the libpq routing variables; sets exactly one; runs a read-only probe; and proceeds only if the probe shows the allowlisted database name, host 127.0.0.1, port 5433, major version 17, the dedicated role, `rolsuper` false, no user tables and no `alembic_version` table.
3. Allowlist of names: the gate and rehearsal names only. Explicit refusal of `sketch2life_m2_s1a`, `sketch2life` and `postgres`.
4. The migration target is a pinned list of revisions, not an unqualified "heads". The list is produced in P0 by reading the migration scripts (the reviewer counts ten heads by reading; not verified) and is part of the approval text.
5. The test files repeat the identity guard before any fixture writes, require an empty database at start for the gate, record table counts before and after, and fail rather than skip when a guard does not hold.
6. Nothing is dropped by default. A failed gate database is kept as evidence. Rehearsal databases are recreated by the owner for each rehearsal run. Any drop is a separate owner action.
7. The password is not typed on a command line and not placed in an environment variable that holds a URL. A password file outside the repository is used. Saved outputs are scanned for the password before they are kept; pytest runs with short tracebacks, no local-variable dump and no JUnit log capture.
8. Outputs, base temp and artifact root are under `D:\GitHub\Sketch2Life\tmp\m2-s2-pg-gate\`.
9. An in-process socket guard refuses any connection that is not loopback, in addition to the operating-system egress block if it can be combined with loopback traffic (to be probed in P0; three loopback flows are needed: test to API, test to PostgreSQL, API to PostgreSQL).

## 7. Phases

| Phase | Content | Who |
|---|---|---|
| P0 | Remaining owner decisions (section 9); read-only preparation: pinned migration list, seeding survey of the existing PostgreSQL tests, loopback probe under the egress block; cold review of this plan; approval of an exact allowlist | Owner; session; reviewer |
| P1 | Write test code and the launcher. No source file is edited | Session, under the allowlist |
| P2 | Static checks on the new files only: syntax, Ruff, Mypy, before anything runs | Session |
| P3 | Offline collection; mapping table from every case in section 4 to its tests | Session |
| P4 | Rehearsal on the rehearsal database, recreated fresh each time. Exit only after at least three consecutive full passes with no retry inside the suite; any intermittent result is treated as a failure to be understood | Owner-run |
| P5 | The gate: fresh gate database, guarded migration, one run, with the concurrency tests repeated inside that run | Owner-run; ceiling 1 |
| P6 | Evidence report with the limits of section 8; independent review; owner acceptance | Session; reviewer; owner |
| P7 | S3 Draft 8 | Session |

Pins recorded at P5: commit and clean status; hashes of every test file and the launcher; the migration list and the resulting `alembic_version` rows; `pyproject.toml` and `uv.lock` hashes; interpreter and tool versions; database identity and role; table counts before and after; exact commands and exit codes; hashes of the outputs.

## 8. What a pass will and will not show; stop conditions

A pass shows the Draft 18 cases and the baseline restart, timeout and orphan legs on one PostgreSQL 17 database through the composed routes, with a synthetic identity verifier. It does not show: the production BE1 Parent-role adapter path that D-190 names; behaviour with a real provider; anything about cases seeded by direct SQL beyond what the route does with those rows; HTTP-level late-result behaviour unless PG-D12 allows a provider stand-in; M2-AT-10 beyond what PG-D8 selects; job ownership and locale persistence (PG-D5).

Stop and return to the owner if: a case needs a source change; a rehearsal failure is a product defect; the database probe fails or the database is not empty; the migrated revisions differ from the pinned list; any non-loopback connection is attempted; credential text appears in an output; a rehearsal is intermittent; a process hangs or cannot be stopped cleanly; the egress block and loopback traffic cannot be combined; a baseline leg has no defined expected result.

A failed gate leaves its database and outputs in place and consumes the ceiling. A further attempt needs a new approval naming a new empty database.

## 9. Owner decisions still needed

- **PG-D8 — M2-AT-10 at 121 and 155 months.** (a) On PostgreSQL, assert that the database refuses to store a profile revision of 121 or 155 months (the check constraint), and keep the service-level 422 as offline evidence, stating that the two layers were shown separately (recommended: it tests the schema as it is and changes nothing); (b) drop the check in the gate database to insert such rows, which changes the schema under test; (c) a stand-in profile lookup returning 121 or 155, which is no longer a trusted stored profile; (d) record 10-03 and 10-04 as offline-only.
- **PG-D9 — database and role lifecycle.** Confirm rule 1 and rule 6 of section 6 (the owner creates the role and both databases; nothing is dropped without an owner action) and the two database names.
- **PG-D10 — test files.** New files under `backend/tests/integration/`, kept in the repository; when the gate's database variable is absent they skip with a stated reason, and the gate card requires zero skipped tests. (Earlier gate files fail when their variables are absent; CI runs an explicit file list and is not affected either way.)
- **PG-D12 — provider boundary.** For level H of the late-result cases: (a) allow a deterministic stand-in at the provider client boundary inside the launcher, returning synthetic results, so the real route code runs up to and after the call (recommended); (b) no stand-in: level H is reduced to one route-reachable 409 that checks the envelope shape, and the late-result behaviour is shown at level R only.
- **PG-D13 — one gate or two.** (a) Two gates with separate approvals and separate one-shot runs: G1 for M2-AT-08 and 10 (Parent story runs), G2 for M2-AT-09 (assistance, heavy seeding, timeout and orphan) (recommended: a problem in one does not consume the other's ceiling); (b) one gate.
- **PG-D7 — carried over.** Explicit confirmation of S3-D1, S3-D2 and S3-D4, recorded provisionally in S3 Draft 7. Not blocking.

### Owner answers to section 9, 2026-11-17 (planning direction only; not an approval)

Asked through a four-question form in the coordinating session, each question quoting the baseline sentence it concerns:

- **PG-D8:** answered "Kiểm DB từ chối". Option (a): on PostgreSQL assert that the database refuses to store a profile revision of 121 or 155 months; the service-level 422 stays offline evidence; the report states that the two layers were shown separately.
- **PG-D12:** answered "Cho bản giả". Option (a): a deterministic stand-in at the provider client boundary inside the launcher is allowed.
- **PG-D13:** answered "Hai gate". Two gates with separate approvals and separate one-shot runs: G1 for M2-AT-08 and M2-AT-10, G2 for M2-AT-09.
- **PG-D9:** the owner did not pick an option and wrote "Test lun DB trên Docker đi" (run the database test on Docker). This **replaces PG-D6**: the gate databases are to live in Docker, not on the local PostgreSQL 17 service at port 5433. Sections 3, 6 and 7 of this draft still describe port 5433 and are superseded on that point; a Draft 3 must rewrite them. The lifecycle question itself (who creates, who removes, nothing dropped by default) and the database names are still unanswered.

Open after this answer, to be settled before a Draft 3 (question PG-D14):

- Which Docker database. The repository's `compose.yaml` defines a `postgres` service (image `postgres:17-alpine`, database `sketch2life` by default, published as `5432:5432`); that is a development database, and `sketch2life` is on this plan's refusal list. The alternative is a dedicated container for the gate from the same image, on its own loopback-only port and its own volume, created per run.
- Read-only observation by the session on 2026-11-17: the Docker engine was not running when queried, so local images and existing containers were not inspected. Whether the image is already present, or would have to be pulled over the network by the owner, is not known.
- With a dedicated container most of finding P1-1 changes shape: the accepted database `sketch2life_m2_s1a` is on a different server and cannot be reached through the gate's port. The variable-clearing and probe rules of section 6 still apply, because Alembic would still follow a stale variable.

## 10. Handling of review R1

| Finding | Handling in Draft 2 |
|---|---|
| P1-1 migration target unprotected | Section 6 rules 1 to 5 |
| P1-2 restart contradicts the baseline | Baseline quoted in section 2; PG-D4 re-decided as a real process restart; restart, timeout and orphan legs added in section 4 |
| P2-3 ages 121 and 155 not storable | Stated in section 4; PG-D8 |
| P2-4 HTTP and repository levels conflated | Levels R and H in section 4; PG-D12 |
| P2-5 "disposable" undefined | Section 6 rules 1 and 6; PG-D9 |
| P2-6 guard content | Section 6 rules 2, 3 and 5 |
| P2-7 test-double boundary | Section 5 |
| P2-8 message assertion weakened | Section 4, case 08-13 |
| P2-9 concurrency coverage | Section 4, case 08-01 |
| P2-10 governance gaps | Sections 1, 6 rule 4, 9 |
| P2-11 rehearsal exit and pins | Section 7 |
| P3-12 to P3-17 | Section 6 rules 7 to 9; section 4 details; section 8 |

## 11. Not established by this draft

- Nothing was executed and no database was contacted. The session did not probe ports, roles or the firewall.
- The count and names of migration heads; whether the pinned list applies cleanly to an empty database.
- The seeding the assistance routes need and whether existing test helpers can be reused; this decides most of the size of G2.
- Whether the application can be served by a launcher process with the allowed doubles and start-up objects without touching the network.
- Whether a provider-boundary stand-in can be installed without changing source (if not, PG-D12 (a) fails its own stop condition).
- The reviewer's case-by-case reading of the code (no contradiction found with Draft 18) is a reading, not a run.
- Whether co-owner work on another branch already contains PostgreSQL tests for these routes.
- Size: larger than Draft 1 described. A process launcher, real seeding and about thirty cases. No estimate in days is offered.

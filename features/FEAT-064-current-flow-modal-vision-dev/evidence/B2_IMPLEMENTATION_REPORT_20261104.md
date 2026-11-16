# FEAT-064 Goal B2 implementation report — 2026-11-04

**Final status: `WAITING_FOR_OWNER_T12_RUN`**

This is an implementation handoff, not an independent review or acceptance. T9 and T13 were completed with offline/static verification. T12 remains owner-run because this session was explicitly not authorized to connect to PostgreSQL or apply migrations. No `READY_FOR_T13` or live-call authorization is claimed.

## Baseline and scope

- Checkout: `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index remained empty.
- Approved plan: `plan/CHAIN_B2_REV2_PLAN_20261103.md`, SHA-256 `DBE886D1BCCC1C14A54BA8FE2C499AAA29FA46A742D888E7882D0EE8F776C7DB`.
- Snapshot: `.claude/handoff/snapshots/GB2_BASE_20261104T212854/`; manifest SHA-256 `1BC57EA8E35AAF144549A7C52214D84C8126EE1BC4B382978F2AE2E237B03B2E`; baseline status had 114 entries / 115 expanded file paths, with an empty index.
- Changed paths against the snapshot: nine implementation paths plus this report. The snapshot comparison found no path outside plan §5. No approval, ledger, status, migration, schema, AI Jobs source, profile route, or OpenAPI contract source was changed.
- Authority pins remained: V4 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; B2 goal `DCC900204C53CFC1961BB00729B7A91821D878C548603BAD7C97C5511EDDD99A`; T12 procedure `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C5063657`.

The four pinned B1 source/test hashes still match:

| File | SHA-256 |
|---|---|
| `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py` | `2D4A99E15C3650A3E30538B9557251872CAFEE338E3F82FF7917A55D8284F004` |
| `backend/tests/unit/test_be1_pilot_artifact_fence.py` | `3D3683640B3876E1431E02294561AF9C90C616FA0FC5C32711F1D6311B84FA1D` |
| `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `0620AFDEBDB83584C2AA97BE9BCD6E1437CD99B84C912E4EF216BA4B1885440D` |
| `backend/tests/unit/test_pilot_queue_composition_b1.py` | `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4` |

## T9 — completed in this checkout

Added four assistance operations under `/api/be1/v1`: child request, child cancel, own-child status, and assigned teacher pending metadata. They reuse `build_assistance_requests_router(prefix)` and the existing classroom registration. The compatibility app keeps its existing no-assistance surface while the classroom profile and test acceptance profile expose the local/test-gated routes. The disabled gate returns 503. No approve/reject route or model call was added; `RequestStatus` remains unchanged and does not contain `UNKNOWN`.

Child status and teacher pending project only coarse processing metadata. P3 orphan coverage supplies an analysis-head fixture containing a private-output sentinel and a `SUCCEEDED` invocation while the job remains `RUNNING`, with no result refs, completion time, or authoritative completion receipt. The projection reads job lineage/completion evidence only; the analysis reader is an exploding fake and its read count stays zero. Both child and teacher remain in `processing`, and neither response contains the analysis id, intent, or private-output sentinel. The test runs for both active and paused sessions; the paused path has no current turn.

OpenAPI was measured with the local combined app and storage examples enabled, matching the catalog fixture. Before T9: **112 paths / 125 operations**, including **51 BE1 paths / 56 operations**. With pilot enabled after T9: **116 paths / 129 operations**, including **55 BE1 paths / 60 operations**. The pre-existing pilot-profile lookup is preserved and remains outside the four T9 additions.

## T13 — completed with loopback only

The script builds `create_classroom_app()` with local settings, injects the pilot runtime using `dataclasses.replace`, and does not read provider URL/token files. The full eight-step synthetic flow goes through HTTP loopback listeners: organization, class, session, synthetic proof, accepted stroke, assistance request, child status, and teacher pending. A fixed 0.15-second deadline against a 0.40-second loopback response returns `unknown`; the stub receives exactly one send. Manual run output: `PASS`, child and teacher state `unknown`, context revision `41`, provider token read `false`, provider stub requests `1`, external requests `0`, `OWNER_MODAL_CALL_APPROVED=NO`.

## Verification actually run

| Check | Result |
|---|---|
| Focused contract / T9 / T13 and existing compatibility checks | 11 passed |
| Copied pinned A4 offline runner, original B1 add-ons plus T9/T13 tests | 468 passed in 22.01s; the runner removed DB URL variables and blocked non-loopback sockets |
| Focused strict mypy (route/runtime/composition, new T9/T13 tests and T13 script) | 6 files, no issues |
| Ruff on changed Python with only `I001` ignored | passed |
| Plain Ruff | only three existing `I001` import-order findings in `router_composition.py`, `test_openapi_contract_catalog.py`, and the unrelated dirty import block in `test_be1_postgres_api.py`; those baseline blocks were preserved |
| `validate_harness.py` | `HARNESS_VALID` |
| `validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`, 6,423 publishable files scanned |
| `validate_architecture.py` | `ARCHITECTURE_VALID` |
| `git diff --check` | passed, no whitespace errors |

The existing `test_migrations.py` source expects BE1 head `20261101_be1_age_0001`, matching the current migration source statically. Its database-backed assertion was **not run**. Its PostgreSQL fixture creates and drops a separate database through a maintenance connection, which is outside this launch. This is not recorded as a migration-test pass.

## T12 — owner run required; NOT RUN here

No connection, preflight query, migration, or PostgreSQL test was run in this session. The authorized target is the owner-created empty PostgreSQL 17 database `s2l_b2_be1_acceptance_20261104` on `127.0.0.1:5433`, user `postgres`. The owner must set `BE1_TEST_DATABASE_URL` in the owner’s PowerShell process. This report contains no URL or credential.

Run only after the read-only preflight below passes exactly. Any mismatch, existing user table/schema, routing environment override, or unclear ownership means stop with T12 `NOT RUN / BLOCKED`; do not substitute another database. The preflight expects only the default empty `public` schema and zero user tables before migration.

```powershell
# From the repository root, in the owner's PowerShell window.
$repoRoot = (Get-Location).Path
$logBase = Join-Path $repoRoot '.claude\handoff\logs\GB2_T12_20261104'
$runTag = Get-Date -Format 'yyyyMMddTHHmmss'
$logDir = Join-Path $logBase $runTag
$tmpRoot = Join-Path $env:TEMP ('s2l_gb2_t12_' + $runTag)
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null
$python = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'
if (-not $env:BE1_TEST_DATABASE_URL) { throw 'Owner must set BE1_TEST_DATABASE_URL in this process.' }
$env:SKETCH2LIFE_DATABASE_URL = $env:BE1_TEST_DATABASE_URL

@'
import ipaddress
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

expected_db = "s2l_b2_be1_acceptance_20261104"
routing_keys = ("PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGUSER", "PGSERVICE", "PGSERVICEFILE")
if any(key in os.environ for key in routing_keys):
    print("PREFLIGHT_FAIL: libpq routing override is present; values suppressed")
    sys.exit(2)
try:
    url = make_url(os.environ["BE1_TEST_DATABASE_URL"])
except Exception:
    print("PREFLIGHT_FAIL: connection URL is absent or invalid; details suppressed")
    sys.exit(2)
if (
    url.drivername != "postgresql+psycopg"
    or url.host != "127.0.0.1"
    or url.port != 5433
    or url.username != "postgres"
    or url.database != expected_db
    or "service" in url.query
):
    print("PREFLIGHT_FAIL: URL identity differs from the approved task database")
    sys.exit(2)
for key in ("host", "hostaddr"):
    value = url.query.get(key)
    values = value if isinstance(value, tuple) else (() if value is None else (value,))
    if any(item not in {"localhost", "127.0.0.1", "::1"} for item in values):
        print("PREFLIGHT_FAIL: URL routing override is not loopback")
        sys.exit(2)

engine = None
try:
    engine = create_engine(url, hide_parameters=True, pool_pre_ping=True)
    with engine.connect() as connection:
        identity = connection.execute(text("""
            SELECT current_database(), inet_server_addr()::text, inet_server_port(),
                   current_user, current_setting('server_version'),
                   (SELECT r.rolname FROM pg_catalog.pg_database d
                    JOIN pg_catalog.pg_roles r ON r.oid = d.datdba
                    WHERE d.datname = current_database())
        """)).one()
        schemas = [row[0] for row in connection.execute(text("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
              AND schema_name NOT LIKE 'pg_%'
            ORDER BY schema_name
        """))]
        tables = [tuple(row) for row in connection.execute(text("""
            SELECT schemaname, tablename FROM pg_catalog.pg_tables
            WHERE schemaname NOT LIKE 'pg_%'
              AND schemaname <> 'information_schema'
            ORDER BY schemaname, tablename
        """))]
except Exception:
    print("PREFLIGHT_FAIL: connection or read-only inventory query failed; details suppressed")
    sys.exit(3)
finally:
    if engine is not None:
        engine.dispose()

print("identity:", identity)
print("pre_migration_schemas:", schemas)
print("pre_migration_user_tables:", tables)
server_address = ipaddress.ip_address(identity[1]) if identity[1] else None
if (
    identity[0] != expected_db
    or server_address is None
    or not server_address.is_loopback
    or identity[2] != 5433
    or identity[3] != "postgres"
    or identity[4].split(".", 1)[0] != "17"
    or identity[5] != "postgres"
    or schemas != ["public"]
    or tables
):
    print("PREFLIGHT_FAIL: live identity or empty inventory differs")
    sys.exit(3)
print("T12_READ_ONLY_PREFLIGHT=PASS_EMPTY_TASK_DATABASE")
'@ | & $python - 2>&1 | Tee-Object -FilePath (Join-Path $logDir '00-preflight.txt')
if ($LASTEXITCODE -ne 0) { throw 'Stop T12; do not run migrations or tests.' }
```

Migration bounds: the repository has multiple Alembic heads, so the single all-head upgrade pass is `upgrade heads` (plain `upgrade head` is ambiguous). The only downgrade is the single `pilot_vision` branch revision `20261102_pv_0001`, whose migration owns the `pilot_vision` schema. Do not run any other downgrade, reset, drop, truncate, or database provisioning command.

```powershell
# Still at repository root; one upgrade pass, then read-only current.
& $python -m alembic -c backend/alembic.ini upgrade heads 2>&1 | Tee-Object -FilePath (Join-Path $logDir '01-upgrade-heads.txt')
if ($LASTEXITCODE -ne 0) { throw 'Upgrade failed; stop and preserve the database for owner review.' }
& $python -m alembic -c backend/alembic.ini current --verbose 2>&1 | Tee-Object -FilePath (Join-Path $logDir '02-current-after-upgrade.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not record current revisions; stop.' }

# The owner runs each suite from backend; capture each result separately.
Set-Location .\backend
$python = '.\.venv\Scripts\python.exe'
$testFailures = [System.Collections.Generic.List[string]]::new()
& $python -m pytest -q -ra --tb=short --basetemp (Join-Path $tmpRoot 'be1-api') tests/integration/test_be1_postgres_api.py 2>&1 | Tee-Object -FilePath (Join-Path $logDir '03-test-be1-postgres-api.txt')
if ($LASTEXITCODE -ne 0) { $testFailures.Add('test_be1_postgres_api.py') }
& $python -m pytest -q -ra --tb=short --basetemp (Join-Path $tmpRoot 'synthetic-pilot') tests/integration/test_be1_synthetic_pilot_postgres.py 2>&1 | Tee-Object -FilePath (Join-Path $logDir '04-test-be1-synthetic-pilot-postgres.txt')
if ($LASTEXITCODE -ne 0) { $testFailures.Add('test_be1_synthetic_pilot_postgres.py') }
& $python -m pytest -q -ra --tb=short --basetemp (Join-Path $tmpRoot 'pilot-vision') tests/integration/test_pilot_vision_persistence_ga1_postgres.py 2>&1 | Tee-Object -FilePath (Join-Path $logDir '05-test-pilot-vision-persistence.txt')
if ($LASTEXITCODE -ne 0) { $testFailures.Add('test_pilot_vision_persistence_ga1_postgres.py') }
& $python -m pytest -q -ra --tb=short --basetemp (Join-Path $tmpRoot 'age-provenance') tests/integration/test_be1_age_provenance_postgres.py 2>&1 | Tee-Object -FilePath (Join-Path $logDir '06-test-be1-age-provenance.txt')
if ($LASTEXITCODE -ne 0) { $testFailures.Add('test_be1_age_provenance_postgres.py') }
Set-Location ..
$python = '.\backend\.venv\Scripts\python.exe'
if ($testFailures.Count -gt 0) {
    throw ('At least one PostgreSQL suite failed; preserve the database and do not downgrade: ' + ($testFailures -join ', '))
}

# Before the sole downgrade, read row counts for every pilot-owned table.
# If any count is nonzero, do not downgrade. Only clean IDs created by this run.
$inventoryProgram = @'
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
url = make_url(os.environ["BE1_TEST_DATABASE_URL"])
tables = ("request", "receipt", "event", "notice", "epoch", "analysis_head", "observation", "provider_result", "invocation")
engine = create_engine(url, hide_parameters=True)
try:
    with engine.connect() as connection:
        all_tables = [tuple(row) for row in connection.execute(text("""
            SELECT schemaname, tablename FROM pg_catalog.pg_tables
            WHERE schemaname NOT LIKE 'pg_%' AND schemaname <> 'information_schema'
            ORDER BY schemaname, tablename
        """))]
        schema_counts = [tuple(row) for row in connection.execute(text("""
            SELECT schemaname, count(*) FROM pg_catalog.pg_tables
            WHERE schemaname NOT LIKE 'pg_%' AND schemaname <> 'information_schema'
            GROUP BY schemaname ORDER BY schemaname
        """))]
        pilot_counts = {
            name: connection.execute(text(f'SELECT count(*) FROM pilot_vision."{name}"')).scalar_one()
            for name in tables
        }
finally:
    engine.dispose()
print("user_table_count:", len(all_tables))
print("schema_table_counts:", schema_counts)
print("user_tables:", all_tables)
print("pilot_vision_row_counts:", pilot_counts)
if any(pilot_counts.values()):
    raise SystemExit("PILOT_SCHEMA_NONEMPTY; stop before downgrade")
'@
$inventoryProgram | & $python - 2>&1 | Tee-Object -FilePath (Join-Path $logDir '07-pre-downgrade-inventory.txt')
if ($LASTEXITCODE -ne 0) { throw 'Stop before downgrade; do not delete rows outside this run.' }

# Exactly one pilot-branch downgrade, followed by the second and final all-head upgrade.
& $python -m alembic -c backend/alembic.ini downgrade pilot_vision@base 2>&1 | Tee-Object -FilePath (Join-Path $logDir '08-downgrade-pilot-vision.txt')
if ($LASTEXITCODE -ne 0) { throw 'Pilot branch downgrade failed; stop.' }
& $python -m alembic -c backend/alembic.ini current --verbose 2>&1 | Tee-Object -FilePath (Join-Path $logDir '09-current-after-downgrade.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not record revisions after downgrade; stop.' }
& $python -m alembic -c backend/alembic.ini upgrade heads 2>&1 | Tee-Object -FilePath (Join-Path $logDir '10-reupgrade-heads.txt')
if ($LASTEXITCODE -ne 0) { throw 'Round-trip re-upgrade failed; stop.' }
& $python -m alembic -c backend/alembic.ini current --verbose 2>&1 | Tee-Object -FilePath (Join-Path $logDir '11-current-after-roundtrip.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not record final revisions; stop.' }
$inventoryProgram | & $python - 2>&1 | Tee-Object -FilePath (Join-Path $logDir '12-postflight-inventory.txt')
if ($LASTEXITCODE -ne 0) { throw 'Final read-only inventory failed; stop and record the result.' }
```

Expected log names are under `.claude/handoff/logs/GB2_T12_20261104/<runTag>/`: `00-preflight.txt`, `01-upgrade-heads.txt`, `02-current-after-upgrade.txt`, four `03`–`06` per-suite pytest logs, `07-pre-downgrade-inventory.txt`, `08-downgrade-pilot-vision.txt`, `09-current-after-downgrade.txt`, `10-reupgrade-heads.txt`, `11-current-after-roundtrip.txt`, and `12-postflight-inventory.txt`. The inventory logs record table totals by schema and row counts for all nine pilot tables before the downgrade and after round-trip. Keep logs local/ignored; inspect them for accidental credential output before sharing any summary. If any test leaves rows, delete only IDs proven to belong to this run in FK-safe order; if ownership is unclear, leave them and stop before downgrade.

The `ai_jobs` PostgreSQL integration folder is intentionally not in these commands: its conftest uses a maintenance connection to create and drop a separate `be2_b2_<uuid>` database. That would violate this launch's no-maintenance/no-provisioning boundary. Do not set `BE2_TEST_PG_HOST`. `test_migrations.py` was not modified; its DB-backed assertion remains NOT RUN here. The owner must record the real `alembic current` heads and actual per-suite pass/fail/skip counts in the T12 handoff.

## Proposed records only (not written)

- Approval proposal: “B2 implementation is complete for T9/T13 offline scope; focused checks and pinned offline regression passed. T12 remains NOT RUN pending the owner-run task-owned PostgreSQL sequence. This record does not authorize D9 or a live provider call.”
- Ledger proposal: “Goal B2 status `WAITING_FOR_OWNER_T12_RUN`; T9/T13 implementation and offline/static verification recorded; owner T12 migration and PostgreSQL acceptance pending; no READY_FOR_T13/live-call claim. Independent B2 review and a separate owner decision remain required.”

No files were staged or committed. No Modal, GPU, provider, external network, database, migration, real child data, or live call was used. `OWNER_MODAL_CALL_APPROVED` was not changed and the dry-run reported `NO`.


## B2 T12 read-only reconciliation results — owner-run (2026-11-05)

- Provenance: owner-run; the coordinator read the owner-provided PowerShell transcript and seven log files under `.claude/handoff/logs/GB2_T12_RECON_20261105T141135/`. This is not an independent database connection. The owner transcript showed helper SHA-256 `5EE941FAAB2CB65FCE0DACB2689FC97B2D62235BB245E849CB1236F8A69A08A5` and runner SHA-256 `7466CB770F65F17477089A1C5962E4774E462059941F108017B67B2023DA70F2` matching the approved values; those hashes are not recorded inside the log artifacts.
- The one authorized read-only reconciliation retry completed inventory, Alembic heads/current, and offline metadata comparison. `RECON_EXIT inventory=0 heads=0 current=0 compare=0` records successful command exits, not a pass/fail verdict. No migration, test, database write, or further retry was performed in this reconciliation.
- Target identity in the owner-run inventory: read-only transaction on; database `s2l_b2_be1_acceptance_20261104`; server address `127.0.0.1/32`; port `5433`; PostgreSQL `17.11`; current user and database owner `postgres`.
- Inventory found 117 user tables versus 113 tables in repository metadata. Four database tables were not present in metadata: `public.be1_parent_group_members`, `public.be1_parent_groups`, `public.core_upload_parts`, and `public.core_upload_sessions`. No metadata table was missing from the database. Their presence is recorded as an observed difference; this report does not infer their origin or authorize cleanup.
- All nine `pilot_vision` tables had zero rows in the inventory. The database was not empty: 26 tables had rows. The empty pilot-owned tables meet only the stated pre-downgrade row-count condition at the time of this inventory; they do not authorize downgrade or round-trip.
- Alembic inventory found 9 rows in `public.alembic_version`. `alembic heads` and `alembic current --verbose` each reported 12 current/effective heads, and the latter matched the former. The three heads absent as stored rows were `20261015_ai_0001`, `20261101_be1_age_0001`, and `20261102_pv_0001`; the comparison correctly records that rows do not equal heads/current.
- Read-only source inspection shows `20261102_story_run_lite` depends on `20261102_pv_0001`, while `20261102_pv_0001` depends on `20261101_be1_age_0001` and `20261015_ai_0001`. This graph is a plausible explanation for why Alembic reports those three as effective heads without separate version rows. The reconciliation output alone does not confirm that interpretation against Alembic version-table semantics, so the evidence gap remains open pending technical review.
- T12 remains `PARTIAL` and B2 remains `NOT ACCEPTED`. Migration round-trip and database-backed `test_migrations.py` assertions were not run and still require a separate owner decision/approval. Preserve this database and its rows; do not downgrade, clean, or retry under the consumed one-retry addendum. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
- Log artifact SHA-256 values read by the coordinator:
  - `00-readonly-inventory.txt` — `66C5637611E72124903B697B312077D80A2F3A0415AA19768B5E400195B45451`
  - `01-alembic-heads.txt` — `2F71C9FF785A68DA7BE9AF01C2F3B7BDFF106CD4EC909EF965293D4C188A3ABD`
  - `02-alembic-current.txt` — `21C2DBF9FB874F82C73A25749E60EB2CF0F994C961FDAD80F14D182A24B7FE64`
  - `03-compare.txt` — `90A5239BF0B6136C54E4C73F3E471A137F786E67A4C6F597052D4C3B34696636`
  - `04-exit-codes.txt` — `CDF6D7D2D21166467F5630961E0E30DE02B856221E44D80C184FD7D50F4B904C`
  - `alembic-version-rows.txt` — `4421DDE6B55A282A4574D78E466209C6CF122EEB04BD13408F9AEECF2B6DEAD5`
  - `inventory-tables.tsv` — `07275BB93967EA03A9C4454760ACC509814305C4E840D61D6CB14E24B36CA2CD`

## B2 Revision 1 — report-only (2026-11-05)

Mục này thay thế trạng thái Final status ở dòng 3 của báo cáo gốc và là trạng thái hiện hành; 263 dòng gốc được giữ nguyên. Đây là cập nhật báo cáo, không phải kết luận review độc lập.

Final status: READY_FOR_INDEPENDENT_REREVIEW. T12 chỉ được coi là đóng khi review độc lập đóng T12. B2 NOT ACCEPTED. OWNER_MODAL_CALL_APPROVED=NO.

### Phản hồi finding NEEDS_REVISION

- P1 — bằng chứng T12: xem bảng đối chiếu theo hàng T12 của plan tại mục 3 và hai đính chính có dẫn dòng báo cáo gốc tại mục 4. Các dữ kiện DB là owner-run; phiên này chỉ đọc log và không kết nối DB độc lập.
- P3 — OpenAPI: hai route POST submit/cancel trong assistance_requests.py nhận Request, khai báo response_model=None, và chưa có schema request/response đầy đủ trong OpenAPI. Owner xác nhận hoãn finding này tới trước khi frontend/client tích hợp. Không sửa trong B2: router dùng chung nằm ngoài allowlist plan §5 và không đổi so với HEAD.
- P3 — T13: giới hạn claim được ghi nguyên văn ở mục 5.
- Điều kiện orphan B1: ranh giới riêng được giữ ở mục 6; B2 không xử lý hoặc coi điều kiện đó là kết quả được chấp nhận.

### 3. T12 đối chiếu từng ý trong hàng T12 của CHAIN_B2_REV2_PLAN_20261103.md

| Ý trong plan | Bằng chứng và nguồn log — owner-run | Giới hạn |
|---|---|---|
| Round-trip trên DB riêng | Owner-run trên DB mới; .claude/handoff/logs/GB2_T12_ROUNDTRIP_20261105T152148/roundtrip-log.txt cùng step-1-upgrade.txt, step-2-downgrade.txt, step-3-reupgrade.txt. Preflight ghi 0 bảng và 0 hàng alembic_version. Nâng pilot_vision@head: 48 bảng và hàng 20261102_pv_0001; hạ pilot_vision@base: 39 bảng và hai hàng 20261015_ai_0001, 20261101_be1_age_0001; nâng lại: 48 bảng và hàng 20261102_pv_0001. Chín bảng pilot rỗng sau mỗi lần nâng; không có bảng schema story. | Chỉ chứng minh round-trip nhánh pilot trong trạng thái trung gian với bảng pilot rỗng; giới hạn chi tiết ở mục 6. Log và các bước đều do owner chạy; không phải kết nối DB độc lập của phiên này. |
| Các suite tích hợp trong phạm vi | Lượt đầu: .claude/handoff/logs/GB2_T12_20261104/20261105T000535/03-test-be1-postgres-api.txt ghi assertion tại test_be1_postgres_api.py:305 không khớp hợp đồng OpenAPI đã công bố; đây là lỗi assertion, không phải lỗi runtime. Sau sửa test-only được ghi trong B2_T12_ASSERTION_FIX_REPORT_20261105.md, log rerun owner-run .claude/handoff/logs/GB2_T12_RERUN_20261105T013143/ ghi số pytest chính thức: 02-test-be1-postgres-api.txt — 4 passed; 03-test-be1-synthetic-pilot-postgres.txt — 118 passed; 04-test-pilot-vision-persistence.txt — 5 passed; 05-test-be1-age-provenance.txt — 1 passed. | Đây là số liệu của bốn suite trong lần rerun, không phải verdict cho T12/B2. Phần DB của assertion trong backend/tests/integration/ai_jobs/test_migrations.py vẫn NOT RUN; không gộp nó vào các suite này. |
| Số bảng và dữ liệu trên DB giữ lại | Inventory owner-run .claude/handoff/logs/GB2_T12_RECON_20261105T141135/00-readonly-inventory.txt và inventory-tables.tsv: 117 bảng; 26 bảng có dữ liệu; chín bảng pilot_vision đều có 0 hàng. Đối soát ngoại tuyến owner-run .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt sau khi nạp đủ module ghi 117 bảng metadata và 117 bảng DB, hai danh sách chênh lệch đều rỗng. | Đây là ảnh chụp inventory tại thời điểm owner chạy; không phải lời xác nhận về dữ liệu ở thời điểm khác. |
| Trạng thái assertion migration-head | Log owner-run .claude/handoff/logs/GB2_T12_RECON_20261105T141135/03-compare.txt, alembic-version-rows.txt và log ngoại tuyến GB2_T12_OFFLINE_20261105A/offline-check.txt: 9 hàng alembic_version bằng đúng 9 script head thật. DB assertion trong test_migrations.py là NOT RUN. | test_migrations.py tự tạo/xóa DB qua fixture; dòng 340 còn kỳ vọng đúng hai hàng cũ, không khớp chín head hiện tại. Không sửa test và không ghi assertion DB này là kết quả đạt. |

### 4. Đính chính hai đoạn của báo cáo gốc

1. Đính chính dòng 251: bốn bảng be1_parent_group_members, be1_parent_groups, core_upload_parts, core_upload_sessions không phải bảng DB-only. Chênh lệch đó phát sinh do thứ tự helper duyệt metadata trước khi import lesson_library.tables. Kiểm tra ngoại tuyến sau khi import đủ module ghi 117 bảng metadata, 117 bảng DB; in_database_not_in_metadata và in_metadata_not_in_database đều rỗng.
2. Đính chính dòng 253–254: chín hàng alembic_version bằng đúng chín head thật. Con số 12 trong alembic heads/alembic current là chín head thật cộng ba revision mang nhãn “effective head”: 20261015_ai_0001, 20261101_be1_age_0001, 20261102_pv_0001; ba revision này là tổ tiên qua depends_on, nên không cần hàng version riêng. Không còn chênh lệch cần giải thích. current_expansion_equals_heads: False trong kiểm tra ngoại tuyến chỉ so 12 revision mở rộng với 9 head thật.

### 5. Giới hạn claim T13

T13 chạy loopback với stub, pilot_job_repository=None và service giả; nó chỉ chứng minh helper hết thời gian trả unknown với đúng một lần gửi tới stub; nó KHÔNG chứng minh một job thật chuyển sang UNKNOWN; các test PostgreSQL của B1 phủ phần SQL UNKNOWN/HOLD thật.

### 6. Giới hạn T12 đã được owner chấp nhận và ranh giới orphan B1

Round-trip chỉ ở nhánh pilot_vision, trạng thái trung gian, bảng pilot rỗng; không chứng minh đảo ngược khi có dữ liệu, không chứng minh đảo ngược chuỗi story_run_lite (20261103_story_upload_compat cố ý không đảo ngược), không phải round-trip toàn đồ thị. Phần assertion DB của test_migrations.py là NOT RUN: fixture tự tạo/xóa DB; dòng 340 kỳ vọng đúng hai hàng, cũ so với chín head; không sửa test và không ghi là đạt.

Hàng analysis mồ côi có invocation SUCCEEDED trong khi job còn RUNNING là điều kiện RIÊNG phải xử lý trước khi dùng dữ liệu không synthetic hoặc provider. B2 không coi đó là kết quả được chấp nhận và không xử lý điều kiện này.

### 7. Trạng thái DB và provenance

DB giữ lại s2l_b2_be1_acceptance_20261104 nguyên vẹn. DB mới s2l_b2_be1_roundtrip_20261105 để nguyên sau lần nâng lại cuối, với 48 bảng. Giữ hay xóa các DB là quyết định riêng của owner. Mọi dữ kiện DB trong mục này đều là owner-run; phiên này chỉ đọc log, không kết nối DB độc lập.

## Revision 1 review-fix supplement (2026-11-05)

### P3 — Phân biệt dữ kiện log và suy luận về metadata

Mục này làm rõ cách diễn đạt ở mục 4 của Revision 1; dòng cũ được giữ nguyên byte. Log không trực tiếp ghi thứ tự import, nên chẩn đoán thứ tự helper dưới đây là suy luận từ source, không phải dữ kiện được quan sát trực tiếp trong log.

1. Dữ kiện trực tiếp trong .claude/handoff/logs/GB2_T12_RECON_20261105T141135/00-readonly-inventory.txt: metadata_expected_table_count là 113; in_database_not_in_metadata liệt kê đúng bốn bảng be1_parent_group_members, be1_parent_groups, core_upload_parts, core_upload_sessions; in_metadata_not_in_database rỗng.
2. Dữ kiện trực tiếp trong .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt: metadata_table_count_after_importing_all_modules là 117; observed_database_table_count là 117; in_database_not_in_metadata và in_metadata_not_in_database đều là danh sách rỗng. Các số 113, 117, bốn bảng và hai danh sách rỗng đều được xác nhận trong đúng các log nêu trên.
3. Suy luận từ source: backend/src/sketch2life/infrastructure/lesson_library/tables.py gắn bốn bảng vào CorePersistenceBase.metadata khi module được import; backend/alembic/env.py import module đó. Chẩn đoán là helper đối soát đã duyệt CorePersistenceBase.metadata trước khi import lesson_library.tables. Thứ tự này không được log ghi trực tiếp; đây là suy luận nhất quán với kết quả ngoại tuyến 117 bảng metadata khớp 117 bảng DB, không phải điều log chứng minh.

T12 PARTIAL; B2 NOT ACCEPTED; OWNER_MODAL_CALL_APPROVED=NO. Kết quả validator không phải verdict của T12 hay B2 và không tuyên bố finding đã được reviewer chấp nhận.

### P2 — Kết quả bốn kiểm tra

Các lệnh chạy từ gốc repository trước append và chạy lại sau append cho output cùng exit code. Các output dưới đây là lần chạy sau append; để tuân thủ quy định không ghi đường dẫn tuyệt đối cục bộ, dòng root được chuẩn hóa thành dấu chấm, mọi dòng còn lại giữ nguyên.

Lệnh: python tools/validate_harness.py
Output:
    HARNESS_VALID
    root=.
    approval_gate=enabled
    frontend_asset_gate=enabled
Exit code: 0

Lệnh: python tools/validate_repository_security.py
Output:
    REPOSITORY_SECURITY_VALID
    publishable_files_scanned=6424
    environment_files=excluded
    seed_accounts=excluded
    credentials_and_signing_keys=excluded
    external_reference_documents=excluded
    absolute_machine_paths=absent
Exit code: 0

Lệnh: python tools/validate_architecture.py
Output:
    ARCHITECTURE_VALID
    python_dependency_direction=valid
    mobile_feature_isolation=valid
    frontend_asset_gate=valid
    mobile_ai_boundary=valid
    firebase_data_products=absent
Exit code: 0

Lệnh: git diff --check
Output:
    warning: in the working copy of 'features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'features/FEAT-064-current-flow-modal-vision-dev/status/STATUS.md', CRLF will be replaced by LF the next time Git touches it
Exit code: 0; these are CRLF/LF warnings, not whitespace errors.

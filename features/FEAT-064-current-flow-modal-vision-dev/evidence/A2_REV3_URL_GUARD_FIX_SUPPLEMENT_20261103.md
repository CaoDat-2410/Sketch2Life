# A2 Rev3 — URL guard correction supplement

Date: 2026-11-03
Status: **XONG-CHƯA REVIEW** for this narrow correction. The independent A2 disposition remains **NEEDS_REVISION** until rereview.

## Why this supplement exists

The first correction report features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_URL_GUARD_FIX_20261103.md recorded 16 focused cases. Static inspection of SQLAlchemy's PostgreSQL psycopg dialect then showed that query parameters can override URL authority fields: query user, port and dbname values are forwarded to the driver. This supplement adds fail-closed checks for conflicting overrides and supersedes the earlier 16-case result. The earlier report and snapshot are retained as historical evidence.

Local, non-connecting SQLAlchemy dialect inspection showed:
- query user=other overrides the URL username;
- query port=5432 overrides the URL port;
- query dbname=other overrides the URL database name;
- query host is forwarded to the driver and remains covered by the existing host loopback check.

## Final guard behavior

For the exact database name sketch2life, the test guard now requires URL port 5433 and username postgres. If URL query overrides are present, every value must agree with the same approved target: port 5433, user postgres, dbname/database sketch2life. Existing PostgreSQL backend, loopback host, hostaddr and service checks remain. The be1_acceptance branch is unchanged.

The parameterized URL guard covers **20 cases**. It rejects alternate/default URL ports, alternate/missing usernames, and query overrides for port, user, dbname and database, in addition to the earlier remote-host, hostaddr, service and other-database cases.

## Pinned inputs and source hashes

| Input | SHA-256 |
|---|---|
| Independent review | BA6F5EB84FD0E7E3093DF52709DE052C1EEF98FE6B96BB0B9BF0A276DB545FDA |
| A2 Rev3 plan | 0F384549BE15D3BF38AF73287F9C6487D2D5B7AEAA1BFB08D71E18BE7CD2BA91 |
| Main-BE DB addendum | 4AFA521E50A91FB6B06D4BB33303AEC3A39021BECEB2A26907964B99EDF15BB7 |
| Sequential goal | D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A |
| Approval record | 5426AC3561DC68CDBE20251C52198E784E3B501A829C8BCAF25D96C390ADB495 |
| First correction report (superseded results) | 814BB51BA098FDA1AD75916D289D22427AE9EAA60D9FB4B8A438C6D6FD7F05C5 |
| First correction snapshot manifest | D077FF4FB646D1C2DB9735BA52BD3F90D9B566698EF133C8E99ECFE62342F932 |

Source SHA-256 at A2 final snapshot: BAF126219995DD2D894EC8BEFB674D02417E546565E7BCE3C43213BD5F6346CE
Intermediate source SHA-256 with URL port/user pin: 6DC62783B0C3E60043E419588C9D2F8E75F0129A2AB2FEAE506E5C84AB633D81
Final source SHA-256 with URL query-override checks: D3F37B9F05B952C51D7A6A36807AA3D4E429FE564DB9989D8C44475B7E0D949E

## Verification

Focused test command, run from the repository root after removing BE1_TEST_DATABASE_URL from the test process:

    backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml -o addopts= backend/tests/integration/test_be1_synthetic_pilot_postgres.py -k test_database_url_requires_loopback_and_approved_name -q

Result: **20 passed, 65 deselected**, exit code 0. The selected test has no database fixture and did not connect to PostgreSQL.

The no-cache Ruff check passed: all checks passed, exit code 0.
git diff --check for the test file was clean, exit code 0.

No PostgreSQL suite/database, migration, repository-wide validator, or mypy check was run. The previously reported 58 synthetic rows from the first failed teardown were not touched or rechecked. No approval/status/decision file was changed. No stage, commit, push, merge, B1/B2, Modal, GPU, provider or external network action occurred.

## Pre-existing local changes preserved

At the initial checkout for this correction, these three files already appeared modified; this task did not edit them. Their current hashes are captured in the final snapshot:
- FEAT-064 CONTEXT.md
- FEAT-064 PILOT_GOAL_LEDGER_20261101.md
- FEAT-064 STATUS.md

Existing unrelated local work remains untouched. Independent review is still required before A2 can be accepted.

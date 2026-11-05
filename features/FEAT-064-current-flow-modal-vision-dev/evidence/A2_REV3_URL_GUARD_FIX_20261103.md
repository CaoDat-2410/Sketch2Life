# A2 Rev3 — URL guard P2 correction

Date: 2026-11-03
Implementer stop: **XONG-CHƯA REVIEW**. The independent review disposition remains **NEEDS_REVISION** until the reviewer rechecks this correction.

## Scope and inputs

This correction addresses only the P2 finding in features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_MAIN_DB_INDEPENDENT_REVIEW_20261103.md. No runtime, migration, schema, behavioral assertion, or database change was made. No approval, status, or decision record was edited.

| Input | SHA-256 |
|---|---|
| Independent review | BA6F5EB84FD0E7E3093DF52709DE052C1EEF98FE6B96BB0B9BF0A276DB545FDA |
| A2 Rev3 plan | 0F384549BE15D3BF38AF73287F9C6487D2D5B7AEAA1BFB08D71E18BE7CD2BA91 |
| Main-BE DB addendum | 4AFA521E50A91FB6B06D4BB33303AEC3A39021BECEB2A26907964B99EDF15BB7 |
| Sequential goal | D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A |
| Approval record | 5426AC3561DC68CDBE20251C52198E784E3B501A829C8BCAF25D96C390ADB495 |

Checkout: feature/feat063-be-foundation, HEAD b6dbfa68e66718f3f40902c093e9ebd634b1ebb9; index empty at the pre-change check.

## Test guard change

In backend/tests/integration/test_be1_synthetic_pilot_postgres.py, the exact sketch2life database exception now additionally requires port 5433 and explicit username postgres. Existing PostgreSQL/loopback checks and the hostaddr and service rejection checks remain in place. The be1_acceptance branch is unchanged.

The parameterized guard now covers 16 cases, including:
- accepted exact sketch2life target shape;
- rejected alternate port 5432 and omitted/default port;
- rejected alternate and missing username;
- existing remote-host, non-loopback hostaddr, service, other-database and be1_acceptance cases.

Source SHA-256 before this correction (from the previous final A2 snapshot): BAF126219995DD2D894EC8BEFB674D02417E546565E7BCE3C43213BD5F6346CE
Source SHA-256 after this correction: 6DC62783B0C3E60043E419588C9D2F8E75F0129A2AB2FEAE506E5C84AB633D81

## Verification

Focused guard command was run from the repository root with BE1_TEST_DATABASE_URL removed from the test process:

    backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml -o addopts= backend/tests/integration/test_be1_synthetic_pilot_postgres.py -k test_database_url_requires_loopback_and_approved_name -q

Result: **16 passed, 65 deselected**, exit code 0. This selected test has no database fixture and did not connect to PostgreSQL.

Ruff's first cached invocation could not create a cache file because Windows denied access. The no-cache rerun passed:

    backend/.venv/Scripts/python.exe -m ruff check --no-cache --config backend/pyproject.toml backend/tests/integration/test_be1_synthetic_pilot_postgres.py

Result: **All checks passed**, exit code 0.

git diff --check -- backend/tests/integration/test_be1_synthetic_pilot_postgres.py: clean, exit code 0.

No PostgreSQL suite, database query, migration, repository-wide validator, or mypy check was run for this test-only correction. The previously reported 58 synthetic rows left by the first failed teardown were not touched or rechecked here.

## Boundary

No stage, commit, push, merge, B1/B2 work, Modal call, or provider call occurred. Existing unrelated working-tree changes were preserved. Independent review is still required before A2 can be accepted.

# C2 runtime test instructions — no GPU needed

Status: READY_FOR_OWNER_ENVIRONMENT, SQL tests NOT_RUN locally.
Use the committed BE2-12 checkpoint and a separate existing approved Python
environment, not the sender's pinned BE2-01 Studio checkout. No git pull into
that checkout. Record git branch/HEAD before running.

## Preconditions and effects

- Existing PostgreSQL 17 test server and existing approved Python 3.12
  environment with project dependencies. No install/start is authorized here.
- An authorized dedicated test role with CREATE DATABASE and access to drop its
  own disposable databases. No production DB or elevated-role changes.
- The fixture creates nine randomly named lc_48_<uuid> databases, one per case,
  applies only its module migration there, tests and drops each exact target.
  One test explicitly exercises downgrade only inside its disposable DB.
- Use your environment's actual host/port/user and private password-file path.
  Do not paste passwords/DSNs into chat, logs, Git or this document.
- Network interruption can leave an orphan disposable DB; report it for
  authorized cleanup, never run a wildcard database deletion.

## Bash/Lightning commands (values supplied by environment owner)

From repo root on the BE2-12 checkpoint:

    git branch --show-current
    git log -1 --oneline
    python -c "import sys; print(sys.executable)"

Configure only the existing authorized profile, replacing placeholders:

    export LC_TEST_PG_HOST="<approved-test-host>"
    export LC_TEST_PG_PORT="<approved-test-port>"
    export LC_TEST_PG_USER="<dedicated-test-role>"
    export LC_TEST_PG_PASSWORD_FILE="<existing-private-password-file>"
    export LC_TEST_ALLOW_CREATE=1
    python features/FEAT-048-be2-content-publication/src/run_c2_sql_checks.py

If no such environment exists, stop and report that; do not install packages,
start cloud/Docker or invent credentials. Existing BE2 runtime approval does
not automatically grant use of someone else's Studio/database.

## Expected result and files to return

- Runner prints PASS with a new .runtime/learning-content-c2/<timestamp> path.
- Exactly 9 PostgreSQL cases, zero failure/error/skip; runner exit 0.
- Missing profile returns NOT_RUN/exit 2; test/collection failures return 1.
- Return summary.json, junit.xml and pytest.log from that path, and
  collection.log if collection failed. Keep original failed receipts too.
- These results prove only C2; no whole-task, provider or production claim.

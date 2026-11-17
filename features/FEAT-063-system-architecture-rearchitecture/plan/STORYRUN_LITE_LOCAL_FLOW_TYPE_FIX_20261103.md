# StoryRun-lite local flow and new mypy error — 2026-11-03

Status: **APPROVED / IN_PROGRESS** by the owner's direct instruction in this thread.

## Scope and gates

- Fix types only in the newly introduced `ControlledDateTime.now` in `test_startup_recovery_expires_receiving_and_retries_staging_cleanup`, plus its necessary imports, in `backend/tests/integration/test_story_run_lite_postgres.py`. Construct the result as the datetime subclass required by the override while preserving the same instant and timezone behavior. Preserve runtime source, migrations and the 24 other baseline diagnostics.
- Run mypy with the same settings as the recorded baseline and report actual diagnostics, plus relevant lint and an appropriate focused test. PostgreSQL suite need not be repeated solely for this annotation.
- Locate the previously used real ClamAV locally; if available verify synthetic image CLEAN and EICAR INFECTED. Use the repo's V2 Vision stub in a temporary loopback launcher outside the repo, verify the worker and task DB gates, then run the local Parent Bruno 01–08 flow only after all prerequisites pass. If real ClamAV, the stub or another gate is unavailable, stop and record the actual results.
- Keep existing databases and local changes, do not reset or delete them. Do not call Modal, GPU or a provider, or stage, commit, push, merge or deploy. Stop only processes created for this task.

Append approval, feature evidence/status and an additive snapshot, keeping prior records intact.

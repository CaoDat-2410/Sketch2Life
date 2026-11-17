# FEAT-038 decisions

## 2026-10-09 — Lightning launcher and Python 3.12 compatibility

- Add a dedicated Bash launcher for the Lightning Vision V2 server. Preserve the Windows PowerShell local-backend launcher unchanged.
- Read `LIGHTNING_DEV_AUTH` from the caller's managed runtime environment and fail with a safe message when it is absent. Never embed or print credentials.
- Use the public `multiprocessing.connection.Connection` type for the runner endpoint annotation; do not import `PipeConnection`, which is unavailable in the reported Python 3.12 Linux runtime and is not needed by runtime behavior.
- Keep model loading lazy and do not call an AI provider/model during launcher startup.

## 2026-10-28 — Portability assessment only

- Record the owner's requested Modal feasibility review without expanding the approved launcher-fix scope or selecting a production provider.
- Recommend evaluating a custom Modal App ASGI endpoint to preserve current API contracts. A managed catalog Endpoint needs separate compatibility and adapter work.
- Treat combined GPU capacity, cold/warm timing, cost, model quality and runtime compatibility as unverified on Modal. Keep video migration separate from the Vision V2 service assessment.
- Evidence and the unapproved candidate follow-up plan are in `evidence/MODAL_PORTABILITY_REVIEW_20261028.md`.

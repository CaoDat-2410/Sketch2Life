# FEAT-038 decisions

## 2026-10-09 — Lightning launcher and Python 3.12 compatibility

- Add a dedicated Bash launcher for the Lightning Vision V2 server. Preserve the Windows PowerShell local-backend launcher unchanged.
- Read `LIGHTNING_DEV_AUTH` from the caller's managed runtime environment and fail with a safe message when it is absent. Never embed or print credentials.
- Use the public `multiprocessing.connection.Connection` type for the runner endpoint annotation; do not import `PipeConnection`, which is unavailable in the reported Python 3.12 Linux runtime and is not needed by runtime behavior.
- Keep model loading lazy and do not call an AI provider/model during launcher startup.

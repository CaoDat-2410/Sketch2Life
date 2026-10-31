# StoryRun-lite guarded Modal live smoke — 2026-11-03

Status: **APPROVED / IN_PROGRESS**, based on the owner's direct instruction in this thread. This is a new, narrow authorization; historical S1→S2 and local-loopback prohibitions remain unchanged as historical records.

## Scope and exact files

- `backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py`: retain loopback defaults; add an explicitly selected HTTPS Modal live mode, fixed server-side bearer header and a canonical UUID allowlisted run. Only that run may dispatch, through the existing A1 ledger/guard/transport and V2 adapter. Never print credentials. Reject ambiguous, malformed or non-Modal targets and missing configuration before any send.
- `backend/src/sketch2life/infrastructure/story_run_lite/composition.py`: select the existing loopback path by default; select live only through explicit configuration, with a Modal HTTPS base URL, a secret supplied in process environment, and the one run UUID. Reject conflicting mode/configuration; never silently fall back from live to fake/loopback.
- `backend/tests/unit/test_story_run_lite_photo_bridge.py` and, if necessary, `backend/tests/integration/test_story_run_lite_loopback.py`: offline configuration, fail-closed, bounded run selection, credential redaction, no extra dispatch and loopback regression. Use synthetic data and stubs; no live inference during tests.
- Feature plan, append-only approval, feature evidence/status and additive snapshots. Temporary scripts or fixtures belong in task-owned local directories outside source; no migration, server deployment, A2, FEAT-061/FEAT-064 or unrelated source edits.

## Safety and acceptance

1. Explicit live mode requires an HTTPS `*.modal.run` origin with no userinfo, non-root path, query, fragment or nonstandard port, a nonempty safe bearer token and the one run UUID. Default/unset remains loopback or unavailable; malformed, conflicting or incomplete live settings fail closed. No proxy bypass. Credentials never appear in logs, errors, Git or evidence.
2. Preserve `InvocationLedgerGuard` and `HttpJsonTransport` behavior: bounded total deadline, verified TLS, one POST `/v2/vision`, durable `SENT` before HTTP bytes, receipt committed before ledger completion, and no resend on `SENT` or `UNKNOWN`. Any post-SENT timeout, reset, redirect, invalid response or ambiguity terminates as UNKNOWN; no automatic retry. The run UUID is fixed before enabling live and only one synthetic run may send in this task.
3. Verify offline/unit/loopback behavior and no regressions before any live request. Verify a real ClamAV CLEAN for the exact synthetic input, a real EICAR INFECTED, isolated worker limits, and a new task-owned loopback PostgreSQL DB before any live inference. Obtain an active owner-operated Modal V2 origin and matching bearer via local secret input; never infer readiness from an old stopped app.
4. After gates pass, run one Parent flow and send at most one HTTP inference request to Modal. Record `SENT`/terminal ledger, run/result/confirmation, duration and any ambiguity, omitting sensitive bodies and credentials. One HTTP inference request is the scoped limit; remote server bounded repair, if enabled, can perform additional model generation and must not be represented as a measured single generation.
5. Stop task-owned temporary API/scanner processes afterwards. No existing DB reset/drop, no stage/commit/push/merge/deploy. Stop at a required out-of-scope change or unavailable endpoint; no placeholder proxy or live call.

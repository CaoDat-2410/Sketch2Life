# Evidence index

## EV-017-01 — Live adapter and route contract tests

- Date: 2026-09-05
- Scope: backend-only Lightning transport boundary, hash-checked synthetic fixture loader, typed ASR/VLM mapping, timeout/retry/rate-limit handling, malformed output rejection, and Gate A-preserving local route.
- Command: `backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_lightning_client.py backend/tests/unit/test_live_understanding_route.py backend/tests/unit/test_understanding_adapters.py backend/tests/unit/test_settings_security.py -q -p no:cacheprovider --basetemp=tmp/live-ai-tests`
- Result: 16 passed.
- Limitations: transport tests use an injected fake; no live provider request was made because the user has not supplied a configured endpoint/token file in this workspace.

## EV-017-02 — Mobile live-mode and full regression

- Date: 2026-09-05
- Mobile command: `pnpm --dir apps/mobile exec jest --runInBand`
- Mobile result: 2 suites, 7 tests passed; typecheck and lint passed.
- Cross-feature command: `$env:PYTHONPATH='features/FEAT-015-integration-readiness-review/src;features/FEAT-016-runtime-integration/src'; python -m pytest features/FEAT-015-integration-readiness-review/tests features/FEAT-016-runtime-integration/tests -q -p no:cacheprovider --basetemp=tmp/test-ui-regression-final`
- Cross-feature result: 32 passed.
- Governance/security: harness, architecture and repository security validators passed; absolute machine paths are absent.
- Bundle: Android Metro bundle composition passed after the pnpm workspace resolver update.

## EV-017-03 — Connection guide and notebook

- Artifacts: `LIVE_AI_GUIDE.md`, `notebooks/live_ai_smoke_test.ipynb`, and `tools/live_ai_smoke.py`.
- Behavior: verifies synthetic fixture hashes, starts against the local backend route, prints sanitized status/provenance/latency only, asserts Gate A and source provenance, and leaves fixture mode as rollback.
- Limitation: a real Lightning smoke result will be appended only after the owner configures the approved HTTPS endpoint and token file.
- Full backend regression: `backend/.venv/Scripts/python.exe -m pytest backend/tests -p no:cacheprovider --basetemp=tmp/backend-live-final-2` — 29 passed.
- Timeout transport hardening: socket timeouts now remain typed `TIMEOUT`; connection failures remain retryable `PROVIDER_ERROR`.
- Stale-session guard: live requests with `expected_session_version != 1` return `409 STALE_SESSION_VERSION`; provider job cancellation/stale completion and a real Lightning smoke result remain pending follow-up configuration/work.


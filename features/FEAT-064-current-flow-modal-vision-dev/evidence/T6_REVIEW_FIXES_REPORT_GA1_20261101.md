# T6 independent-review fixes — GOAL A1

**Status: XONG-CHƯA REVIEW**
**Plan SHA-256:** `30BB0D4778B3CFE81F9DB04E67DE1078483FE2A61E2A3BBC336E7AC0291D0160`
**Authority:** V4 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; Goal A1 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`; frozen T6 plan `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`.

## Scope

Implemented the three findings in `T6_INDEPENDENT_REVIEW_REPORT_GA1_20261101.md` under the separately approved review-fix plan. No old plan or approval content was edited. No ledger/schema/migration, service, worker, route, composition, or other source/test path was changed. No stage, commit, push, PostgreSQL/Alembic, Modal/GPU/provider, or external network operation was performed.

## Findings and changes

### Guard and transport identity

- `HttpJsonTransport.invocation_guard_identity` exposes the exact injected guard as a read-only property. `LegacyVisionV2Bridge.invocation_guard_identity` exposes that transport identity, also read-only.
- `InvocationGuardedVisionObservationPort` rejects an unguarded or differently guarded bridge during construction and rechecks identity immediately before each call. A runtime mismatch returns a no-send refusal without invoking the bridge.
- In guard state `NEW`, only a typed local `ObservationFailed(provider_invoked=False)` passes through. Success or `provider_invoked=True` raises an invariant error; neither is returned as success nor rewritten as not invoked. No SENT or terminal UNKNOWN is written from NEW.
- Tests cover different-guard and unguarded transports, identity drift before call, matched-guard success, and success/invoked failure presented while state remains NEW.

### DNS deadline and HTTPS verification

- Host resolution now runs on a daemon resolver thread and the caller waits only for the remaining monotonic deadline. The resolved socket connect and TLS handshake also receive the remaining time. The existing 160-second total deadline starts before resolution; `SENT` remains after DNS/TCP/TLS and before request bytes.
- HTTPS continues through `HTTPSConnection`'s default context. The implementation requires `CERT_REQUIRED` and hostname checking, passes the original URL hostname as `server_hostname`, and performs the handshake before marking SENT.
- A blocked injected resolver test proves the call returns within a short test deadline, makes no HTTP request, and leaves the durable claim consumed. A loopback-free TLS setup test verifies original-host SNI and certificate-validation settings without making a network call.

### Claim race and duplicate cases

- Two independent guards/transports now meet at a barrier inside the shared ledger's `claim` boundary. The test records one successful claim, one refused claim, and at most one HTTP send.
- An in-flight duplicate after SENT and the existing crash/restart-after-SENT test remain separate cases; both assert zero additional HTTP sends.

## Verification results

- Focused T6 module: **28 passed / 0 failed** (`pytest -o addopts= ... -q`, exit 0).
- Copied offline GA1 runner, same bytes as the prior snapshot runner (SHA-256 `766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76`), with T6 test module appended: **618 passed / 4 skipped / 0 failed** in 20.25 s, runner exit 0.
- The earlier T6 implementation report records 637 passed / 4 skipped. The current unchanged runner script produced 618 / 4 in the current working tree. No failure occurred; the runner output does not identify the 19-test count difference, so it is not attributed to a specific file or change here. Existing edits to other baseline tests were left untouched.
- Ruff check across the three changed source files plus the T6 test: `All checks passed!`. Ruff format check passed for `invocation_guard.py`, `transport.py`, and the T6 test. A whole-file format check of `legacy_v2.py` requested unrelated existing formatting changes outside the one-property authorization; those lines were not changed. An initial Ruff attempt could not create `.ruff_cache`; the successful run used `--no-cache`.
- Mypy: `Success: no issues found in 3 source files` using a temporary cache after an initial cache-related internal error.
- Validators before the final report/ledger recount: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (6,065 publishable files); `ARCHITECTURE_VALID`; `git diff --check` exit 0. Final post-document validator outputs are appended after rerun below.
- Focused and offline tests use the existing synthetic fixtures, a fake resolver, and loopback-only HTTP. No real child data or external network was used.

## Final post-document validator recount

After this report and the append-only ledger entry were present:

- `validate_harness.py`: `HARNESS_VALID`.
- `validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`, 6,066 publishable files scanned; absolute machine paths absent.
- `validate_architecture.py`: `ARCHITECTURE_VALID`.
- `git diff --check`: exit 0, no output.

## Snapshot

`.claude/handoff/snapshots/GA1_T6_REVIEWFIX_20261101T214519/`

No independent review is claimed. A1 remains `XONG-CHƯA REVIEW`; do not start A2 until review accepts the fixes.

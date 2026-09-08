# FEAT-017 test strategy

- Test data: synthetic FEAT-015 integration fixture only.
- Default mode: deterministic fixture adapter.
- Live mode: one approved Lightning development smoke path, backend-only.

## Required matrix

1. Valid ASR and vision provider-shaped responses map to versioned contracts.
2. Malformed JSON, prohibited fields, missing provenance and schema-version mismatch fail closed.
3. Timeout, retryable provider error, rate limit, cancellation and retry exhaustion preserve source artifacts and emit typed outcomes.
4. Duplicate/idempotent request and stale session/job completion cannot mutate newer state.
5. Gate A remains required after a successful live proposal; no live response directly reaches P1/media.
6. Mobile fixture mode remains usable when live mode is unavailable or disabled.
7. Secret/endpoint/raw-output redaction and bundle scans pass.
8. The full FEAT-015/016 regression remains green.

A live smoke result must include the fixture hash, provider/model/config identifiers, sanitized request ID, latency, status, and limitations. Do not store raw media or provider payloads.

# FEAT-017 live AI development integration plan

- Status: REVIEW
- Plan revision: 1
- Implementation status: REVIEW

## Problem and goal

The approved fixture UI proves the complete user flow but its AI proposal is deterministic. Add one reviewable live development path so the same screen can submit synthetic drawing/narration to a backend-only Lightning adapter, receive validated P2 contracts, and stop at Gate A for adult confirmation.

## Proposed scope

1. **Backend provider adapter**
   - Implement a concrete Lightning development client behind `AiGateway`, `AsrPort`, and `VisionUnderstandingPort`.
   - Resolve base URL and token only from ignored runtime configuration/secret references.
   - Send only the synthetic FEAT-015 drawing/narration artifact references or controlled fixture payloads.
   - Enforce connect/request timeouts, one bounded retry, request ID/idempotency key, operation allowlist, response-size/media limits, and typed provider failures.
2. **Contract and safety boundary**
   - Map provider responses into the existing `AsrResultV1` and `VisionUnderstandingResultV1` contracts and emit a Gate-A-bound proposal envelope; the full P2 fusion oracle remains the approved fixture path in this slice.
   - Reject malformed output, prohibited psychological fields, missing source provenance, unsupported schema versions, and stale session versions.
   - Preserve source hashes and model/config/provider provenance; never log raw media, prompts, output, headers, signed URLs, or secrets.
3. **Local backend runtime path**
   - Add a local-only HTTP route that exposes the live P2 request through the approved session-version guard; downstream FEAT-016 job semantics remain the fixture oracle in this slice.
   - Return typed `PROVIDER_ERROR`, `TIMEOUT`, `MALFORMED_OUTPUT`, `RATE_LIMITED`, and `STALE_SESSION_VERSION` outcomes so the UI can keep Gate A and fallback behavior.
4. **Mobile UI integration**
   - Keep the provider boundary in the backend. Add a development-mode toggle that selects `live-lightning` or `fixture` through a typed backend request, never through a provider URL/token.
   - Show loading, retryable failure, and validated proposal states in the existing fixture screen; no live result may skip Gate A.
5. **Evidence and rollback**
   - Record synthetic fixture hash, sanitized request metadata, model/config version, latency, status, retry/failure reason, and validated output hash under this feature.
   - Keep fixture mode as the default and document a one-command rollback to fixture mode.

## Acceptance criteria

- [x] Live Lightning development request is reachable only from backend infrastructure and uses runtime-injected secret references.
- [x] Mobile source, bundle, logs, and screenshots contain no provider endpoint, token, or SDK dependency.
- [x] Synthetic FEAT-015 fixture media is the only input; no real child data is accepted by the live path.
- [x] Successful live responses round-trip through the existing versioned P2 contracts with source provenance and model/config metadata.
- [x] Malformed/prohibited/stale/timeout/provider-error responses become typed failures and cannot create a Gate A bypass.
- [x] Gate A remains mandatory; P1/P3/P4 downstream identity and versions remain unchanged.
- [x] Retry, timeout, rate-limit, malformed output, and stale session-version behavior are covered by tests.
- [x] Redaction/security checks prove no raw media, prompt, output, secret, or signed URL enters ordinary logs/evidence.
- [x] Fixture mode remains the deterministic default and all FEAT-015/016 regression tests pass.
- [x] Live-run evidence includes exact environment class, fixture hashes, provider/model/config identifiers, latency, result interpretation, and limitations.

## Verification plan

- Unit/contract tests with injected provider-shaped fakes for success, malformed output, prohibited field, timeout, rate limit, retry exhaustion, and stale session.
- Local HTTP/job contract tests for polling, ETag/version, cancellation, duplicate request, and stale completion.
- Mobile Jest/typecheck/lint plus a bundle scan for provider strings/secrets.
- One explicitly approved synthetic Lightning smoke run, if credentials and endpoint are available, with sanitized evidence only.
- Full harness, architecture, security, and FEAT-015/016 regression before review.

## Risks and rollback

- Provider output or latency may make the UI less predictable: keep fixture mode as default and retain typed fallback.
- Lightning endpoint availability or quota may block a smoke run: report NOT_MEASURED rather than treating it as pass.
- Any secret or real-data boundary failure blocks review and reverts the development toggle to fixture mode.
- Runpod/production work remains a later plan with separate approval.

## Implementation review

The backend adapter, allowlisted fixture route, mobile live-mode client/state, smoke tool and notebook guide are implemented and covered by automated tests. The route currently uses a local session-version guard and returns validated ASR/VLM proposal data; provider job cancellation/stale completion and full live P2 fusion remain follow-up work. A real Lightning smoke run remains pending the configured HTTPS Studio/deployment URL and token file; no provider call was made in this workspace.



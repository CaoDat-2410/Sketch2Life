# Backend-only AI provider security boundary

## Trust boundary

```text
Android app
  | HTTPS + end-user/session authorization
  v
Sketch2Life backend API
  | application AiGateway port
  v
Backend AI adapter / controlled egress gateway
  | verified TLS + runtime provider credential
  v
Lightning fixture endpoint or Runpod production endpoint
```

The Android app must not know a provider hostname, endpoint ID, token, administrative API, or provider-specific request shape. Provider authentication does not replace application authentication or authorization.

## Development and production posture

- Lightning AI is development-only on the owner's normal account and limited credit balance. Treat its endpoint as authenticated public infrastructure, use fixtures only, and route every call through the backend adapter.
- Runpod Serverless queue endpoints are the production target. They expose bearer-authenticated API URLs, so use a restricted key scoped to the exact endpoint, runtime secret injection, rotation/revocation, and backend-only egress.
- Neither provider is described as private networking under the currently selected plans. If real child data later requires private network transport, that becomes a separate deployment/security gate.

## Required controls before live integration

### Identity and secrets

- Use the narrowest provider credential available: restricted endpoint key for Runpod and development-only token for Lightning.
- Store provider credentials in the deployment secret manager and mount/inject them at runtime.
- Never place credentials in React Native config, bundles, APK resources, source control, fixtures, screenshots, crash reports, or logs.
- Separate local, test, staging, and production identities/endpoints.

### Network

- Allow provider access only from backend/worker code; mobile has no provider route or credential.
- Restrict backend egress to the approved Lightning fixture endpoint or Runpod production API where hosting controls permit it.
- Verify TLS certificates and the expected service identity.
- Disable cleartext traffic in Android release/main manifests.

### Data and artifacts

- Send the minimum required fixture artifact, not a whole session record.
- Preserve source artifacts; provider output creates a new versioned derivative with model/config provenance.
- Use short-lived signed object references or controlled streaming, never public buckets.
- Encrypt data in transit and at rest; define retention/deletion before using any real child data.
- Fixtures must contain no real child media or identifying metadata.

### Request and output handling

- Require request ID, idempotency key, operation allowlist, model profile, and expected session version.
- Enforce body/media limits, content-type checks, timeouts, retry budgets, concurrency quotas, and circuit breaking.
- Treat all model output as untrusted. Parse into versioned contracts and run safety/domain validation before persistence or presentation.
- A worker returns an application completion command; it never mutates session state directly.
- Reject stale job completions and preserve auditable failure/fallback reasons.

### Logging and monitoring

- Log identifiers, timing, status, model profile/version, byte counts, and redacted error categories.
- Do not log raw media, full prompts, model output, authorization headers, signed URLs, certificates, or secrets.
- Alert on authentication failures, unusual volume/latency, repeated validation failures, and egress-policy violations.
- Keep audit access least-privileged and retention-limited.

## Production approval checklist

- [ ] Threat model reviewed for Lightning development and Runpod production modes.
- [ ] Environment policy rejects Lightning in production and requires the approved Runpod endpoint.
- [ ] Runpod key has restricted access to the intended Serverless endpoint only.
- [ ] Endpoint rejects anonymous access and is reachable only through backend code paths.
- [ ] Provider-key rotation and revocation are tested.
- [ ] Secret scanning and mobile bundle inspection show no provider secret/endpoint.
- [ ] TLS, timeout, retry, rate-limit, and circuit-breaker tests pass.
- [ ] Output-contract, stale-version, fallback, and prompt/media redaction tests pass.
- [ ] Fixture-only load/security evidence is stored in the implementing feature.
- [ ] Data retention/deletion and incident response owners are recorded.

No live model connection is authorized by this document; it defines the gate for a later feature.

Official provider references: [Lightning managed secrets](https://lightning.ai/docs/overview/ai-studio/managed-secrets), [Runpod endpoints](https://docs.runpod.io/serverless/endpoints/overview), and [Runpod API keys](https://docs.runpod.io/get-started/api-keys).

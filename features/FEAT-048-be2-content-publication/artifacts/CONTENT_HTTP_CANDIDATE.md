# CMD-48 content HTTP candidate — C4a

Contract version: 0.1-candidate. Status: component verified; NOT production
composition, NOT complete closed governance dispatcher. All eight content actions
are supported; preset/policy branches require owner schemas/delegates (CR-C4-01).

## Composition and identity

Factory: `build_content_commands_router(service, resolve_identity,
max_body_bytes=..., prefix="/api/collaboration/v1")`. The caller MUST provide a
transport body admission limit and a server-verified identity/scope resolver.
No header role/organization/principal is trusted. No default identity or live
boundary adapter is supplied. The existing default application is unchanged.

The resolver returns GovernanceIdentity(principal_id, organization_id) from
verified server context, or None (401). It does not replace current action
capability/source/review checks in the application owner guard. The service and
resolver run on the worker thread pool; request streaming stays async.

## Candidate path and request

POST `/api/collaboration/v1/governance/records`, application/json. This is the
only command route in the candidate router, not an alternate CMD-48 identifier.
No new eligibility/delivery HTTP route competes with BE1 CMD-59/60.

Body is exactly the existing strict learning_content ContentCommand action union.
Unknown fields/record kinds/actions are rejected; no dictionary passthrough or
fake successful owner mutation. Preset/policy currently return validation 422,
NOT the final typed delegate-unavailable behavior. Full dispatcher remains open.
OpenAPI documents the complete finite inline content DTO graph with no unresolved
references; body parsing is manual only to ensure safe non-echoing errors.

Create omits If-Match. Other actions require one strong quoted positive record
revision, e.g. `If-Match: "2"`; weak/wildcard/list/unquoted/zero/negative values
are rejected. Record revision is not target_version or expected_review_revision.
The client_request_id is in the body and binds full command and precondition;
retries use the same validated command and original If-Match.

Duplicate JSON keys, non-JSON numbers, invalid UTF-8/JSON and unknown/malformed
DTOs are rejected without echoing the raw body or validation input. Streaming
counts actual bytes against the injected admission bound, not only Content-Length.

## Response and errors

Success 200: `{correlation_id, data: ContentCommandResult}` with quoted current
record revision ETag, Cache-Control no-store and Vary Authorization. `data.record`
is the immutable recorded command-result metadata on retry; current_revision and
current_state are separately supplied. Neither is permission for new-session use.
record_review/request_changes return the shared DATA-24 review_record unchanged.
Optional incoming safe X-Correlation-ID is preserved; invalid values are replaced.

Errors use existing CollaborationErrorV1/0.1-candidate, including its contract
name/version, correlation_id and typed error {code,message,retryable}. Fixed
message only; no raw content, adapter exception, credential or DSN is exposed.

| Status | Meaning |
|---|---|
| 400 | malformed/forbidden create precondition |
| 401 | no verified server identity |
| 403 | current capability/separation/policy/source usage denied |
| 404 | scoped content target absent |
| 409 | stale record/review, hash/review/receipt/state conflict |
| 413 / 415 | body admission / media type rejected |
| 422 | invalid strict content command, JSON or required reason |
| 428 | non-create record If-Match missing |
| 503 | required authority/source/dependency unavailable; unknown safe-domain error hidden |
| 500 | unexpected adapter failure, hidden |

No automatic blind retry follows a 409. A 503 is retryable only with the same
idempotency key/body/precondition after dependency recovery; clients must never
treat retryable as permission to weaken a command or fabricate policy.

## Consumer sequence

1. Author creates with body/client_request_id, captures server ID/version/hash/revision.
2. Author submits exact target with record If-Match.
3. Independent matching reviewer records safety and pedagogical DATA-24 reviews,
   updating record If-Match and named expected_review_revision after each result.
4. Independent publisher publishes exact target and both returned review IDs plus
   pinned review policy version. A reviewer may publish only with separate capability.
5. BE1/P4 consumer resolves via ContentEligibility using its verified scope,
   requested age/purpose and optional explicit version/hash. Never infer current
   eligibility solely from cached publication metadata or receipt.
6. Recall targets exact version with current global record If-Match/reason. New
   resolution denies it; immutable provenance remains. Outbox notifications are
   intents requiring the owning idempotent delivery adapter, not proof of delivery.

Runnable synthetic consumer/action examples are the eight-action parametrized
test in backend/tests/contract/test_learning_content_http.py and the SQL lifecycle
test in backend/tests/integration/learning_content/test_commands_sql.py. They use
explicit assumed identity/authority adapters, never real child data or production
credentials. True consumer conformance/adoption remains an integration gate.

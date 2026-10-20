# C4c published-reference / lifecycle-notice conformance pack

Approved scope: P3 immutable published refs, exact new-session resolution,
retirement notice/outbox intent and H-CONTENT-PRESET consumer examples. Do not
implement BE1 sessions, a delivery gateway, provider hooks or active-copy policy.

Provide strict versioned metadata contracts matching existing owned SQL outbox
payload, a safe adapter for that payload and a typed query projection backed by
current ContentEligibility. Scope/identity are separate verified port arguments,
never client source-of-authority fields. Metadata refs/notices are not grants.

Define a candidate sink/ack protocol for consuming-owner adoption. Its fixture
demonstrates exact-version retirement, event idempotency/body conflict and pinned
history preservation. This is conformance evidence, NOT a delivered BE1 event,
durable consumer dedup, transport authentication or transactional outbox worker.
No owned SQL write/schema/migration change is needed for this metadata pack.

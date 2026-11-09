# FEAT-063 API and Event Contracts — Rev57 draft

- **Status:** logical contract proposal; not an approved API specification.
- **Baseline:** SRS/Data Table Register v2.7-draft Rev57, unsigned; source commit ae5707ca188d01d9719ed959b62d768ae927912d.
- **Label rule:** every route below is PROPOSED. A method/path proposal does not mean it is mounted. Existing mounted status is AS-BUILT only where the source composition is inspected.
- **Cross-owner rule:** AI Policy, Billing, Story/Lesson and AI Jobs each commit their own receipt/outbox. No transaction spans owners.

## 1. Contract inventory

Logical paths below are names for design review. Their exact public prefix, HTTP code and generated OpenAPI schema require API-owner review. Types are contract-level types, not SQL types.

| Operation | Method / path | Caller and authorization | Request fields / types | Response fields / types | Errors and recovery | Version / idempotency / owner |
|---|---|---|---|---|---|---|
| Select Teacher sample child | POST /v1/teacher/occurrences/{occurrenceRef}/sample-selection — PROPOSED | Authenticated Teacher assigned to occurrence class; server checks current tenant, grant/consent and Q-01 policy | occurrenceRef: opaque typed ref; expectedOccurrenceRevision: version; contractVersion; Idempotency-Key; policy inputs are server-owned, not caller supplied | one selectedChildRef: opaque typed ref; allowlisted display context: schema TBD; policyVersion: only if owner adopts versioned policy contract | Existing AUTH_REQUIRED / RESOURCE_NOT_FOUND / ACTION_NOT_ALLOWED semantics; no-eligible outcome and code TBD; stale revision returns conflict/reload behavior to approve; never return a list for Teacher choice | Proposed v1 contract; key scoped to principal + occurrence + command; Lesson/identity ports own reads |
| Confirm selected child/context | POST /v1/teacher/occurrences/{occurrenceRef}/sample-confirmation — PROPOSED | Assigned Teacher; repeat server-side scope/grant/consent checks at command time | occurrenceRef, selectedChildRef, expectedOccurrenceRevision, confirmedContextRevision, Idempotency-Key; confirmation payload allowlist TBD | accepted run reference/revision only after confirmation and run creation; otherwise semantic denial | Stale revision, grant revoked, no longer eligible or concurrent claim return a safe semantic error; exact code/attempt behavior OPEN Q-01 | Idempotent; Lesson/Story owners coordinate through versioned command, not shared SQL |
| Accept direct profile invitation | POST /v1/profile-share-invitations/{invitationRef}/accept — PROPOSED | Authenticated named Teacher recipient only | invitationRef, expectedGrantVersion if contract exposes it, Idempotency-Key | active grant reference/version and limited scope summary; response field set OPEN | Invalid/expired/revoked/scope mismatch denied without profile/media leak; school/class audience acceptance remains OPEN | Versioned command; grant owner unresolved; no name lookup |
| Revoke Parent share | POST /v1/profile-share-grants/{grantRef}/revoke — PROPOSED | Authenticated Parent grant owner | grantRef, expectedGrantVersion if used, Idempotency-Key, optional reason only if approved | revoke effective revision/time at contract level; detail OPEN | Repeated revoke idempotent; new reads/tokens and not-yet-accepted jobs blocked; accepted-job/history behavior OPEN | Parent retains revoke authority; no cross-owner transaction |
| Read post-video activities without preset | GET /v1/story-runs/{runRef}/activities — PROPOSED, conditional | Authenticated Parent/run owner; server checks current access and selected Q-13 policy | runRef; exact pinned lesson ref/hash if present; no child data in query parameters | For preset: activity entries tied to exact version/hash. For no preset: policy-selected no-call or catalog result; schema/cardinality TBD | Distinguish no catalog requested, zero eligible items, denied/revoked and unavailable; exact response shape/code OPEN; never block prior video generation | Read is after video; catalog lookup only if owner chooses query; learning_content owns data |
| Submit video admission | POST /v1/story-runs/{runRef}/video-admissions — PROPOSED | Current Parent/assigned Teacher; Story command authorization | runRef, expectedRunRevision, confirmedScriptRevision, exact context hash, optional LessonVersionRefV1 version/hash, Idempotency-Key, contractVersion | admission receipt refs/status at contract level; no provider detail; accepted run/job reference only after reconciliation-safe accept | policy/quota denial returns to SCRIPT_REVIEW as SRS says; unknown receipt stays pending for reconciliation; errors use existing common envelope where applicable | One request identity across owner-local receipts; AI Policy → Billing → Story; no distributed DB transaction |
| Provider completion callback | Internal adapter/event port — PROPOSED, not public route | Provider signature/auth validated by adapter; callback cannot choose target | provider event ref, job/attempt refs, target ref, safe disposition, output hash/asset ref, correlation; exact schema TBD | accepted/stale/rejected disposition from job owner; content not duplicated in job ledger | Duplicate callback idempotent; unknown outcome reconciled; stale result fenced; retries bounded | AI Jobs owns receipt/event; Story/Lesson owns result |

## 2. Shared request/response envelope

Proposed fields to review: authenticated principal context from verified token; tenant/class scope resolved server-side; contract version; correlation ID; owner-issued opaque target refs; expected aggregate revision/hash; Idempotency-Key for side-effecting command; safe response/error envelope. Do not accept role, permission, tenant or policy decision from client as authoritative. Do not return child media to School Manager/Platform Admin. Exact wire names and privacy allowlists need API and Privacy owner approval.

Use the established common meanings in SRS §21.6 for authentication, not-found/out-of-scope, forbidden action and active-run conflict. Do not invent a no-eligible error code, policy code, HTTP status mapping or retry header until contract review. A stale revision must be distinguishable from transient failure but code/name remains proposed.

## 3. Async video admission sequence

1. Story validates caller, run/script revision, grant and exact input/lesson pins; emits admission intent with idempotency and correlation.
2. AI Policy reserves compute under its owner transaction and returns/replays its receipt.
3. Billing independently validates Parent-account or occurrence-school scope, current included units then FIFO top-up; it records/replays usage receipt under its transaction.
4. Story accepts and records its outbox only after both owner receipts are resolved. Unknown outcome remains pending; reconciler queries by the same idempotency identity before any replay.
5. AI Jobs persists one job with exactly one of the eight approved target kinds and dispatches through its own outbox. Queue/worker/provider stage is asynchronous.
6. Provider callback is verified and recorded by AI Jobs; completion carries expected revision/input/context/lesson hashes to Story or Lesson.
7. Owning aggregate fences stale/duplicate completion, stores its result/asset lineage and publishes a versioned event. Video playback waits for technical and safety checks.

This order is a target contract, not an assertion of deployed integration. A rejected admission releases the AI Policy reservation per current model and consumes no product quota. Once accepted, product usage is not refunded for later provider/technical/safety failure. Plan-supersession cancellation, UI visibility, sample claim and other compensation remain OPEN; do not invent refund or retarget behavior.

## 4. Timeout, retry and reconciliation

- Accepted video job deadline is six hours from accepted_at, including queue and all stages, as already specified in SRS.
- Retry is bounded by the owning job/stage policy; a retry reuses the same target and pinned revisions.
- Unknown provider or cross-owner receipt outcome is reconciled before retry/dispatch that could double-charge or duplicate output.
- Cancel is a command/request, not proof that provider work stopped; late completion must pass target/revision fence.
- Grant revoke blocks new reads/tokens and jobs not yet accepted. Accepted in-flight handling remains owner decision where SRS marks it open.
- Event/outbox payloads carry only allowlisted metadata, owner/aggregate ref, contract version, revision, correlation and safe disposition; no prompt, child media or credentials.

## 5. AS-BUILT source verification boundary

At baseline ae5707ca188d01d9719ed959b62d768ae927912d, backend/src/sketch2life/interfaces/http/router_composition.py includes health, BE1, demo/story and Lesson Library routers. backend/src/sketch2life/interfaces/http/routers/ai_jobs.py exists, but the main composition does not include it. This is source inspection, not a live API/OpenAPI check. Route inventory and composition are recorded in SRS §32.7 and EV-063-62. The paths in this document remain PROPOSED until mount and auth/schema evidence is produced.

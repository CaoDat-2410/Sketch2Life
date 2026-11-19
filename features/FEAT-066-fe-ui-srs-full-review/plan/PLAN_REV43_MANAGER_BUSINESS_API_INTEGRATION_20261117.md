# FEAT-066 Plan Rev43 — School Manager business API integration

- Status: APPROVED_CONDITIONALLY; implementation starts only after Rev42 confirms a live Manager login through Firebase and both authorization reads.
- Owner request: “Cho account test lun sau đó login đồ ổn thì qua tiếp nối các api nghiệp vụ”.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`; `codex/fe-ui-web-remediation` at `b72f9e46`.
- Detailed route inventory: FEAT-066 Plan Rev40, SHA-256 `84E8779D7F169BEE9E5ECA8D02EABB571D23F66E11B167F782A04D04F261F070`.
- Product authority: FEAT-063 SRS v2.7-draft Rev60 via `docs/context/SRS_AUTHORITY.md`; unsigned.

## Static route disposition before implementation

Reuse the verified Manager auth/session. Rev40 listed ten operations, but source/guard inspection narrows the SRS-compatible FE target to five reads/commands:

| Operation | Disposition | Source/SRS basis |
|---|---|---|
| `GET /api/be1/v1/organizations/{organization_id}` | Connect | Requires an active organization assignment; returns only opaque ID and display name. |
| `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | Connect as minimal roster read | Requires matching class assignment and blocks when consent is not effective; response contains only child ID, class ID, display name, and age in months. No media/story fields. |
| `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | Connect as scoped status read | Requires active school_admin/Teacher assignment and returns only consent ID, opaque child ID, purpose, state, and effective flag. |
| `GET /api/lesson-library/v1/organizations/{organization_id}/parent-groups` | Connect | Requires an organization-wide `school_admin` assignment; cursor-paginated group metadata only. |
| `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups` | Connect with explicit submit and idempotency key | Manager-only, organization-scoped, audited, idempotent group creation; do not call live during tests. |

Do not expose the other five Rev40 operations under current contracts:

- Profile `POST` is restricted to a class-assigned Teacher and local synthetic-pilot mode; it cannot implement the SRS School Manager roster workflow or use real child data.
- Consent `POST` creates a pending, ineffective record on behalf of the current staff principal. The current SRS does not define Manager impersonation of Parent consent or a source-verified Parent evidence workflow. Consent `POST` and `revoke` stay unavailable pending a compatible consent actor contract/policy.
- Parent-group invitation `POST` accepts an opaque `parent_principal_ref`, but no scoped Parent discovery/read route exists. Do not ask the user to guess or manually enter an identity reference.
- Membership `DELETE` needs a membership ID and revision/ETag; the Manager parent-group list returns no membership collection and no Manager membership-read route exists. Keep revoke unavailable until a scoped membership read is exposed.

Audit the six already-connected Manager business routes but do not broaden them. In particular, the existing `POST /api/be1/v1/organizations/{organization_id}/classes` guard checks `school_admin` but does not enforce FR-T-03 class capacity. Do not issue live class-create mutations or represent capacity as enforced; keep this action visibly unavailable until the backend provides a capacity-checked contract. Preserve existing review revision gates; current lesson-detail only returns the current version, not an exact immutable-version read.

Exclude `POST /api/be1/v1/classes/{class_id}/assignments` until a tenant-scoped Teacher candidate read exists. Keep quota, billing, invoices, reconciliation, organization-feedback, and unsupported moderation screens unavailable because their APIs/policies are absent.

## Acceptance criteria

1. Every request uses the verified Firebase bearer token and configured organization; server authorization remains the security boundary.
2. Cross-organization, inactive-assignment, wrong-class, and malformed/stale revision cases fail closed; do not infer capability from client role alone.
3. Manager UI separates loading, error, empty, and server-confirmed success. Parent-group creation uses explicit submit/idempotency behavior; do not add unsafe profile, consent, invite, or membership mutations.
4. Expose only minimal SRS-permitted roster/consent fields. No child image, generated story, media URL/token, or unrelated profile fields are shown or logged.
5. Parent invitations/revocations require confirmation and show completion only after the server confirms.
6. Exercise read routes against the empty QA organization. Parent-group creation uses focused tests only; do not create groups, classes, children, parents, consent, or membership rows in live dev DB.
7. Record each of the ten routes' connectable/blocked status and the six existing routes' SRS gaps. Unsupported or unsafe routes remain clearly unavailable; no backend contract, schema, or authorization change.

## Work sequence and limits

1. Confirm Rev42 live Manager login passed before starting this implementation.
2. Reinspect each current route, response model, role guard, and SRS requirement before adding its UI/service call.
3. Connect the ten operations incrementally, preserve existing six integrations, and add focused FE tests for success, failure, tenant scope, loading, empty, and confirmation states.
4. Run focused tests, build, lint, and read-only authenticated GET smoke; do not issue live business mutations.
5. Update EV-050/EV-051, FEAT-066 context, decisions, status, plan/evidence indexes. Preserve unrelated dirty files. No commit or push.

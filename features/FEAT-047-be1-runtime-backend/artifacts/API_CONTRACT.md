# BE1 v1 API contract

- Status: implementation contract for FEAT-047, dated 2026-10-15.
- Base path: `/api/be1/v1`.
- Machine-readable contract: [`openapi-v1.json`](openapi-v1.json), OpenAPI 3.1.
- Implemented operations: 47 operations across 42 paths.
- Product boundary: this is a feature-scoped implementation contract. It does not adopt proposed SRS B22 routes as a product-wide contract.

## Runtime and security model

All BE1 routes use PostgreSQL as their source of truth. If the database is absent or unavailable, database-backed calls fail with `503`; no request falls back to process memory. Local artifact bytes use a persistent filesystem root. Filesystem artifact service is enabled only for `local` and `test`; production returns `503 ARTIFACT_PROVIDER_UNCONFIGURED` until an object-storage provider is selected.

Adult endpoints require `Authorization: Bearer <Firebase Authentication ID token>`. The server verifies the token, resolves the persisted adult identity and active organization/class assignment, and enforces the role and scope for each operation. Caller-supplied role fields never grant access. First organization provisioning is an operator bootstrap command that verifies a Firebase token interactively; no public endpoint creates an organization or seeds an account.

Device bootstrap uses `POST .../join` with a short-lived session join code and a device proof key. Canvas/reconnect calls use `X-Be1-Grant` and `X-Be1-Device-Key`; the database stores only a hash of the proof key. Grant refresh identifies the grant in the path and requires the current `X-Be1-Device-Key` proof, then rotates the key and returns the replacement once. Pending/revoked grants cannot call child routes.

Every BE1 response includes `X-Request-ID`. A caller may supply a 1–120 character ID matching `[A-Za-z0-9._:-]`; invalid or missing values are replaced with a server-generated ID. Error bodies repeat that ID. JSON request models reject unknown fields. Timestamps are UTC RFC 3339 values.

Consent verification and the purpose catalogue remain unapproved. The API can record or revoke a consent record, but it cannot mark one effective. As a result, profile enrollment and child-owned flows stay blocked with `409 CONSENT_NOT_EFFECTIVE` until a separate approved verification path exists. This gate is intentional and must not be bypassed by changing a request body or caller role.

## Common request rules

| Rule | Contract |
|---|---|
| JSON strictness | Unknown keys are rejected. IDs and display names are trimmed; empty values are invalid. |
| Revision checks | Session state commands take `expected_revision` (integer ≥ 1); stale values return `409 STALE_SESSION_REVISION`. Canvas commands also compare document revision and epoch. |
| Canvas idempotency | Append requires `Idempotency-Key` (1–256 chars). Same semantic request returns the durable receipt; reusing the key with a different payload conflicts. |
| Canvas sync | `after_revision` defaults to 0; `limit` defaults to 200 and is bounded to 1–500. Response includes `next_after_revision`. |
| Reconnect | `after_revision` defaults to 0. Response includes the latest readable checkpoint, current revision, epoch, and operations after the requested revision. |
| Configuration | Session `configuration` is an object with at most 64 entries and 8 KiB encoded size. `purpose_ref` and `join_code_sha256` are server-reserved keys. |
| Child age | `age_months` must be 36–155 completed months inclusive. |
| Join proof | `join_code` is 8–32 chars; `device_key` is 24–256 chars. The raw device key is never persisted. |
| Canvas operation | `operation_payload` is a JSON object up to 32 KiB. |
| Checkpoint | `snapshot` is a JSON object up to 2 MiB. |
| Artifact upload | Multipart image, max 12 MiB and 12 million pixels; accepted bytes must actually decode as PNG, JPEG, or WebP matching the declared media type. One to 40 explicit contributors are required. |
| Observation | `content` is a JSON object up to 8 KiB; `source_refs` has at most 20 entries. |
| Gallery contributors | One to 40 contributor IDs; audience is `class` or `school`. |

Exact required/optional properties, enum values, and bounds for request bodies and headers are defined in [`openapi-v1.json`](openapi-v1.json). The named request schemas are listed in the route table below.

## Route catalog

Paths below are relative to `/api/be1/v1`. “Adult” means Firebase-verified plus active assignment. An operation’s response always includes the `contract` name and fields listed here, except health and binary artifact downloads.

### Readiness, organization, classes, profiles, and consent

| Method and path | Caller / body | Success and response shape | Durable behavior / gate |
|---|---|---|---|
| `GET /health` | Public | `200`: `status`, `database`, `api` | Executes `SELECT 1`; only reports ready when PostgreSQL responds. |
| `GET /organizations/{organization_id}` | Adult | `200 Be1OrganizationV1`: `organization_id`, `display_name` | Requires an active assignment. |
| `GET /organizations/{organization_id}/me` | Adult | `200 Be1AdultAssignmentsV1`: verified `subject`, `organization_id`, `assignments[{role,class_id}]` | Returns only the caller’s active assignments. |
| `POST /organizations/{organization_id}/assignments` | `school_admin`; `CreateAssignmentRequest(subject, role, class_id?)` | `201 Be1AdultAssignmentV1`: `assignment_id`, `subject`, `role`, `class_id`, `active` | Persists identity mapping/assignment and writes audit + outbox. Cannot self-elevate without an existing admin assignment. |
| `DELETE /organizations/{organization_id}/assignments/{assignment_id}` | `school_admin` | `200 Be1AdultAssignmentV1`: `assignment_id`, `active=false` | Revokes future access and writes audit + outbox; history remains. |
| `GET /organizations/{organization_id}/classes` | Adult | `200 Be1ClassListV1`: `items[{class_id,display_name,state}]` | Class rows are filtered to the caller’s assigned classes unless the assignment is organization-wide. |
| `POST /organizations/{organization_id}/classes` | `school_admin`; `CreateClassRequest(display_name)` | `201 Be1ClassV1`: `class_id`, `display_name` | Persists class, audit, and outbox event. |
| `GET /organizations/{organization_id}/classes/{class_id}/profiles` | Adult assigned to class | `200 Be1ManagedProfileListV1`: `items[{child_id,class_id,display_name,age_months}]` | Denies the list if any active profile has no effective consent. No profile is currently creatable through the API while verification is pending. |
| `POST /organizations/{organization_id}/classes/{class_id}/profiles` | Admin/Teacher assigned to class; `CreateProfileRequest(child_id,class_id,consent_id,purpose_ref,display_name,age_months)` | `201 Be1ManagedProfileV1`: `child_id`, `class_id`, `display_name`, `age_months`, `consent_state` | Atomically creates profile + enrollment only with effective consent and valid age. Current policy gate returns `409 CONSENT_NOT_EFFECTIVE`. |
| `POST /organizations/{organization_id}/classes/{class_id}/consents` | Admin/Teacher assigned to class; `RecordConsentRequest(class_id,child_id,purpose_ref,evidence_ref?)` | `201 Be1ConsentV1`: `consent_id`, `child_id`, `purpose_ref`, `state="pending"`, `effective=false` | Creates a pending record only, then audits and publishes an outbox event. `evidence_ref` is metadata, not verified proof. |
| `GET /organizations/{organization_id}/classes/{class_id}/consents` | Admin/Teacher assigned to class | `200 Be1ConsentListV1`: `items[{consent_id,child_id,purpose_ref,state,effective}]` | Returns consent metadata in class scope. `effective` is always false under the current approved boundary. |
| `POST /organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` | Admin/Teacher assigned to class | `200 Be1ConsentV1`: `consent_id`, `state="revoked"`, `effective=false` | Revocation is idempotent and audited. It does not delete history. |

### Sessions, device admission, groups, and turns

| Method and path | Caller / body | Success and response shape | Durable behavior / gate |
|---|---|---|---|
| `POST /organizations/{organization_id}/sessions` | Admin/Teacher assigned to class; `CreateSessionRequest(class_id,purpose_ref,configuration={})` | `201 Be1SessionV1` fields plus one-time `join_code` | Stores only a hash of the join code; starts `configured`, revision 1; emits audit/outbox. The hash is never returned. |
| `GET /organizations/{organization_id}/sessions/{session_id}` | Adult assigned to session class | `200 Be1SessionV1`: `session_id`, `organization_id`, `class_id`, `state`, `revision`, `active_phase`, `configuration`, `started_at`, `ended_at`, `retain_until` | Returns the scoped session projection; never returns the join-code hash. |
| `POST /organizations/{organization_id}/sessions/{session_id}/lobby` | Admin/Teacher; `SessionTransitionRequest(expected_revision)` | `200 Be1SessionV1` | Moves configured session to lobby using compare-and-swap revision. |
| `POST /organizations/{organization_id}/sessions/{session_id}/start` | Admin/Teacher; `SessionTransitionRequest(expected_revision)` | `200 Be1SessionV1` | Requires admitted members and effective purpose consent. Pending consent is denied and audited. |
| `POST /organizations/{organization_id}/sessions/{session_id}/pause` | Admin/Teacher; `SessionTransitionRequest(expected_revision)` | `200 Be1SessionV1` | Durable state transition with revision, audit, and outbox. |
| `POST /organizations/{organization_id}/sessions/{session_id}/resume` | Admin/Teacher; `SessionTransitionRequest(expected_revision)` | `200 Be1SessionV1` | Durable state transition with revision, audit, and outbox. |
| `POST /organizations/{organization_id}/sessions/{session_id}/finish` | Admin/Teacher; `SessionTransitionRequest(expected_revision)` | `200 Be1SessionV1` | Sets `ended_at` and `retain_until = ended_at + 90 days`; closes active turns. |
| `POST /organizations/{organization_id}/sessions/{session_id}/join` | Device bootstrap; `JoinRequest(join_code,device_key)` | `202 Be1DeviceJoinV1`: `grant_id`, `state="pending"`, `session_revision` | Idempotent for the same session/device-key hash; stores key hash only. A replay returns the same response shape and grant. |
| `GET /organizations/{organization_id}/sessions/{session_id}/join-requests` | Admin/Teacher assigned to class | `200 Be1PendingJoinListV1`: `items[{grant_id,requested_at}]` | Lists pending grant IDs only; does not expose device proof or child identity. |
| `POST /organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/admit` | Admin/Teacher; `AdmitDeviceRequest(child_id)` | `200 Be1AdmissionV1`: `membership_id`, `state="admitted"`, `session_revision` | Requires an in-class profile and effective purpose consent. On re-admission, prior group/progress/help/turn binding is cleared. Pending consent blocks admission. |
| `POST /organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/revoke` | Admin/Teacher | `200 Be1DeviceGrantV1`: `grant_id`, `state="revoked"` | Revokes grant and active membership/turn authority; audits and emits an outbox event. |
| `POST /organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh` | Admitted device; current key in `X-Be1-Device-Key` | `200 Be1DeviceGrantRefreshV1`: `grant_id`, one-time replacement `device_key`, `state="admitted"` | Rotates the stored hash. Previous key stops working after commit. |
| `POST /organizations/{organization_id}/sessions/{session_id}/groups` | Admin/Teacher; `CreateGroupRequest(display_name)` | `201 Be1SessionGroupV1`: `group_id`, `display_name`, `state`, `session_revision` | Creates a manual group while the session is open. Automatic grouping (BE1-16) is excluded. |
| `PUT /organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/members/{child_id}` | Admin/Teacher; `AssignMemberRequest(child_id,expected_revision)` | `200 Be1GroupAssignmentV1`: `membership_id`, `group_id`, `session_revision` | Moves membership, closes the previous active turn, preserves accepted history, and requires effective consent. Same-group assignment is idempotent. |
| `POST /organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control` | Admin/Teacher; `GroupControlRequest(action=lock\|unlock,expected_revision)` | `200 Be1GroupControlV1`: `group_id`, `state`, `session_revision` | Lock closes active turns and blocks device canvas access. Unlock does not resume a prior turn. Repeating the current state is idempotent. |
| `POST /organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/progress` | Admin/Teacher/Guide; `ProgressRequest(progress)` | `200 Be1MemberProgressV1`: `membership_id`, `progress` | Progress values: `not_started`, `in_progress`, `ready`, `completed`; child-owned state is consent-gated. |
| `POST /organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/help` | Admin/Teacher/Guide | `200 Be1HelpRequestV1`: `membership_id`, `state="open"` | Opens a durable help request; consent-gated. |
| `POST /organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/leave` | Admin/Teacher | `200 Be1MembershipStateV1`: `membership_id`, `state="left"` | Revokes the membership’s device grant and closes its active turns; other device members remain intact. |
| `POST /organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/turns/{child_id}` | Admin/Teacher assigned to class | `200 Be1ActiveTurnV1`: `turn_id`, `child_id`, `group_id`, `state` | Starts one active attributed turn after session/group/member/consent checks; closes previous active turn in group. |

### Canvas synchronization and checkpoints

| Method and path | Caller / body | Success and response shape | Durable behavior / gate |
|---|---|---|---|
| `POST /organizations/{organization_id}/sessions/{session_id}/canvas/operations` | Active admitted device; `CanvasOperationRequest(operation_id,turn_id,document_epoch,expected_revision,operation_payload)` plus `Idempotency-Key` | `200 Be1CanvasOperationReceiptV1`: `status`, `canvas_id`, `resulting_revision`, `operation_id` | Appends immutable attributed operations and durable idempotency receipt; checks active grant, group, turn, consent, epoch, and revision. |
| `GET /organizations/{organization_id}/sessions/{session_id}/canvas/operations` | Active admitted device; query `after_revision?`, `limit?` | `200 Be1CanvasSyncV1`: `canvas_id`, `document_epoch`, `current_revision`, `operations[]`, `next_after_revision` | Returns only scoped operations after the requested revision, up to 500. |
| `POST /organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints` | Admin/Teacher; `CanvasCheckpointRequest(document_epoch,document_revision,snapshot)` | `200 Be1CanvasCheckpointV1`: `checkpoint_id`, `canvas_id`, `document_epoch`, `document_revision`, `checksum_sha256` | Writes checkpoint bytes to configured persistent local storage and metadata/audit in PostgreSQL; requires an accepted operation/revision and consent. |
| `GET /organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest` | Admin/Teacher/Guide | `200 Be1CanvasCheckpointV1`: checkpoint metadata plus `snapshot` | Verifies checksum and scope before returning snapshot; missing checkpoint is 404, unavailable/corrupt bytes are 410. |
| `POST /organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore` | Admin/Teacher; `CanvasRestoreRequest(checkpoint_id,expected_revision)` | `200 Be1CanvasRestoreV1`: `canvas_id`, new `document_epoch`, `document_revision`, `snapshot` | CAS increments canvas revision and epoch, retains prior operation history, updates active turns, and records audit/outbox. |
| `GET /organizations/{organization_id}/sessions/{session_id}/reconnect` | Active admitted device; query `after_revision?` | `200 Be1CanvasReconnectV1`: `canvas_id`, `document_epoch`, `current_revision`, `checkpoint?`, `operations[]` | Supplies a checkpoint and operations for reconnect; scope and consent checks apply. |

### Artifacts and learning records

| Method and path | Caller / body | Success and response shape | Durable behavior / gate |
|---|---|---|---|
| `POST /organizations/{organization_id}/sessions/{session_id}/artifacts` | Admin/Teacher; multipart `file`, repeated `contributor_ids` | `201 Be1ArtifactV1`: opaque `artifact_ref`, `version`, `sha256`, `media_type`, `byte_length` | Local/test only; stores bytes persistently and metadata/provenance/audit in PostgreSQL. Requires effective consent for every contributor. |
| `GET /organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref}` | Adult assigned to session class; query `version` (default 1) | `200` raw bytes with validated `Content-Type`, `ETag: "<sha256>"`, `Cache-Control: private, no-store` | Checks organization/session/source provenance and contributor consent; integrity failure is 410. |
| `POST /organizations/{organization_id}/gallery` | Admin/Teacher; `GalleryCreateRequest(session_id,artifact_ref,audience,contributor_ids,caption?)` | `201 Be1GallerySnapshotV1`: `gallery_id`, `state="draft"`, `audience`, `artifact_ref` | Snapshot records source artifact and contributors; requires effective consent for all contributors. |
| `GET /organizations/{organization_id}/gallery` | Adult assigned to the session; required query `session_id` | `200 Be1GalleryListV1`: `items[{gallery_id,artifact_ref,audience,contributors,caption,annotations,created_at}]` | Lists published snapshots only; rechecks contributor consent. |
| `POST /organizations/{organization_id}/gallery/{gallery_id}/publish` | Admin/Teacher assigned to the session | `200 Be1GallerySnapshotV1`: `gallery_id`, `state="published"` | Draft-only transition; rechecks contributor consent and records audit/outbox. |
| `POST /organizations/{organization_id}/gallery/{gallery_id}/annotations` | Admin/Teacher/Guide; `GalleryAnnotationRequest(text)` | `200 Be1GalleryAnnotationV1`: `annotation_id`, `gallery_id` | Published-only append; annotation author and timestamp are retained. |
| `POST /organizations/{organization_id}/classes/{class_id}/observations` | Admin/Teacher/Guide; `ObservationCreateRequest(session_id,child_id,kind,content,source_refs)` | `201 Be1ObservationV1`: `observation_id`, `child_id`, `kind` | Kinds: `observation`, `reflection`, `assessment`. Requires in-class profile, session/class match, and effective consent; source references are retained. |
| `GET /organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio` | Adult assigned to class | Would return a scoped portfolio projection after policy adoption; currently `409 CONSENT_NOT_EFFECTIVE` | Portfolio-purpose verification and retention policy are unresolved; no child projection is returned. |
| `POST /organizations/{organization_id}/data-requests` | `school_admin`; `DataRequestCreate(request_type=export\|delete,target_ref)` | `202 Be1DataRequestV1`: `request_id`, `state="requested"`, `completion_claimed=false` | Persists request, audit, and outbox. Creating a request does not verify authority or claim export/deletion completion. |
| `GET /organizations/{organization_id}/data-requests/{request_id}` | `school_admin` | `200 Be1DataRequestV1`: `request_id`, `request_type`, `target_ref`, `state`, `unresolved_items`, `completion_claimed` | Returns durable status. Worker leaves unresolved external/provider purge pending; it must not claim full completion without receipts. |

## Response and error format

JSON success bodies use the resource-specific `contract` name in the route catalog. Error responses use one stable envelope:

```json
{
  "code": "STALE_SESSION_REVISION",
  "message": "Session changed; reload before retrying",
  "request_id": "req-abc123"
}
```

| HTTP status | Meaning | Example codes |
|---|---|---|
| `401` | Missing/invalid adult token or device proof | `AUTHENTICATION_REQUIRED`, `INVALID_IDENTITY_TOKEN`, `DEVICE_AUTHENTICATION_REQUIRED`, `INVALID_DEVICE_CREDENTIAL` |
| `403` | Verified identity lacks active role or resource scope | `FORBIDDEN`, domain authorization code |
| `404` | Missing or intentionally concealed out-of-scope resource | `CLASS_NOT_FOUND`, `PROFILE_NOT_FOUND`, `JOIN_UNAVAILABLE`, `ARTIFACT_NOT_FOUND` |
| `409` | State, revision, idempotency, or policy gate conflict | `STALE_SESSION_REVISION`, `CONSENT_NOT_EFFECTIVE`, `SESSION_NOT_ACTIVE`, `RESOURCE_CONFLICT` |
| `410` | Stored bytes are unavailable or fail integrity validation | `CHECKPOINT_UNAVAILABLE`, `ARTIFACT_INTEGRITY_FAILED` |
| `413` | Request/image exceeds size or pixel bound | `UPLOAD_TOO_LARGE`, `IMAGE_DIMENSIONS_EXCEEDED`, `OBSERVATION_TOO_LARGE` |
| `415` | Media type is unsupported or disagrees with bytes | `UNSUPPORTED_MEDIA_TYPE`, `MEDIA_TYPE_MISMATCH` |
| `422` | Invalid body, query, header, or cross-field request | `REQUEST_VALIDATION_FAILED`, `CLASS_SCOPE_MISMATCH`, `IMAGE_INVALID` |
| `500` | Unexpected internal failure | `INTERNAL_SERVER_ERROR` |
| `503` | PostgreSQL, identity provider, or artifact provider unavailable | `DATABASE_NOT_CONFIGURED`, `DATABASE_UNAVAILABLE`, `IDENTITY_PROVIDER_UNAVAILABLE`, `ARTIFACT_PROVIDER_UNCONFIGURED` |

FastAPI validation errors intentionally omit submitted values. Every documented error uses the same `Be1Error` object (`code`, `message`, `request_id`) and `X-Request-ID` response header. The machine-readable OpenAPI file includes all BE1 status envelopes, including artifact/checkpoint `410` and upload `413`/`415`.

## Tested HTTP behavior

The Docker-backed integration suite exercises the routes against PostgreSQL through FastAPI `TestClient`; only the Firebase token verification boundary is replaced with a synthetic verified principal. It verifies class/session/group persistence, transition revisions, stale-command errors, same-device join deduplication, role denial, request-ID correlation, audit/outbox writes, data-request status persistence, pending-consent gates, hidden device-key storage, database health, and OpenAPI path/security/error declarations. These tests use synthetic IDs only in the dedicated `sketch2life_be1_acceptance` database.

Live response shapes and the read-only HTTP smoke results are captured in [API_CONTRACT_AND_SMOKE_20261015.md](../evidence/notes/API_CONTRACT_AND_SMOKE_20261015.md). The latest full-suite report is [pytest-junit-acceptance-20261015.xml](../evidence/raw/pytest-junit-acceptance-20261015.xml); the focused PostgreSQL report is [pytest-junit-be1-postgres-20261015.xml](../evidence/raw/pytest-junit-be1-postgres-20261015.xml).

## Current explicit gates

- Firebase project configuration and credentials are runtime-only; this repository does not contain Firebase secrets. A real Firebase token has not been used in local acceptance.
- Consent authority procedure and purpose catalogue remain pending; no operation can mark a consent effective. Therefore child profile/session admission, canvas, artifact, gallery, observation, and portfolio positive flows are intentionally unavailable.
- Production object storage and verified external-copy purge receipts remain unselected. Local filesystem persistence is not a production storage claim.
- Data-request creation/status and local retention scheduling exist; external authority review, export delivery, provider-copy discovery, and verified purge are not claimed complete.
- BE1-16 automatic grouping is Phase 2 and not part of this API.

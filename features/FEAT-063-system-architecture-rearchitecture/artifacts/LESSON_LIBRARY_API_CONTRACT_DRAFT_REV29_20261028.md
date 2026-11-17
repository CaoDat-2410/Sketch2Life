# Lesson Library API contract — draft Rev29

- Status: Rev29 is the historical design baseline. Its implementation reconciliation is recorded below under Rev31 and is approved by FEAT-063 Plan Rev31.
- Rev31 reconciliation: retain the Rev29 entity and authorization model, add upload-session status and abort operations, and make completion synchronous for deterministic malware scanning and extraction. Rev29 defined 28 operations; the implementation exposes 30. No AI, OCR, or asynchronous extraction job is introduced.
- Purpose: define the backend boundary for Teacher lesson CRUD/upload, Manager publication review, parent-group/named sharing, Parent read and Platform Admin moderation.
- Related plan: Plan Rev29. Product requirements remain in FEAT-063 SRS v2.3-draft; this contract does not sign off the full SRS.

## 1. Why this API exists

This API supports one reusable lesson lifecycle: a Teacher authors a structured lesson, optionally imports a document and confirms its extracted fields, a School Manager approves Public access, and authorized Parents read the resulting Public or shared lesson. It keeps the reusable library separate from an actual class occurrence and from child-specific Story/video runs.

## 2. Base path and naming rules

- **Base path:** `/api/lesson-library/v1`. This follows the repository's feature-scoped versioned base-path pattern (`/api/be1/v1`, `/api/collaboration/v1`) and the SRS `/v1/lessons` resource group.
- **Resource paths:** lower-case plural nouns (`lessons`, `versions`, `source-documents`, `access-grants`); IDs use `{lesson_id}`, `{version_id}`, etc. No `/create`, `/update` or role names are used as action verbs in resource paths.
- **Tenant scope:** staff authoring/review paths are nested under `/organizations/{organization_id}` as in BE1. The server checks the path organization against the verified assignment; a path ID never grants access. `/me` paths resolve the verified caller and do not accept principal IDs from the request body.
- **HTTP behavior:** `POST` creates a resource/command receipt, `GET` reads, `PATCH` changes mutable aggregate state, `PUT` writes an idempotent subresource such as an upload part, and `DELETE` performs a policy-defined soft archive/revoke. Lesson versions and uploaded source bytes are never physically overwritten.
- **JSON:** snake_case fields, strict unknown-field rejection, opaque IDs, UTC RFC 3339 timestamps. OpenAPI 3.1 is generated from the versioned request/response schemas.
- **Schema names:** `CreateLessonRequestV1`, `UpdateLessonRequestV1`, `LessonDetailV1`, `LessonPageV1`, `LessonVersionV1`, `LessonActivityV1`, etc. The `V1` schema name and `/v1` path identify the contract version; success responses include `contract: "<SchemaName>"`, following BE1 conventions.
- **Authentication:** `Authorization: Bearer <Firebase ID token>`. Principal, active role, organization and Parent/group membership come from verified server-side adapters. Client-supplied `principal_id`, role, `created_by` or owner scope is rejected/ignored as authority.
- **Request controls:** `X-Request-ID` is echoed; use strong `ETag`/`If-Match` for mutable aggregate revisions. Require `Idempotency-Key` on resource creation, upload completion, publication decisions, invitations and grants. List queries use `limit` (1–100) and opaque `cursor`.

## 3. Domain entities and persistence mapping

Domain names are singular PascalCase nouns. Domain objects do not carry `Entity`, `Model`, `ORM` or `DTO` suffixes. A persistence row is not automatically a domain entity; request/response DTOs live in `contracts` and end in `RequestV1` or `V1`.

| Domain object | Responsibility / lifecycle | Persistence owner and mapping |
|---|---|---|
| `Lesson` | Aggregate root for reusable lesson ownership, organization, current version, visibility and archive state. It is not a class occurrence. | Lesson: `lesson.library_items` |
| `LessonVersion` | Immutable authored content snapshot; edits create a new version. | Lesson: `lesson.library_versions` |
| `LessonActivity` | Ordered activity content owned by one exact LessonVersion; not the shared activity catalog entity. | Lesson: `lesson.version_activities` |
| `LessonSourceDocument` | Private original document reference and upload lifecycle owned by a reusable Lesson. | Lesson: `lesson.library_source_documents` |
| `LessonDocumentRevision` | Immutable deterministic extraction or Teacher-corrected revision, with parser/coverage/review provenance. | Lesson: `lesson.library_document_revisions` |
| `LessonAccessGrant` | One version-scoped access edge to a school, Parent group, Parent principal or Public audience; approval/expiry/revoke state is durable. A Public publication request is a `PUBLIC` grant in `PENDING_REVIEW`, not a second publication entity/table. | Lesson: `lesson.access_grants` |
| `ParentGroup`, `ParentGroupMembership` | School-owned Parent audience and invitation/acceptance/revoke lifecycle; `ParentGroupInvitationV1` is a DTO projection over an invited membership, not a duplicate entity/table. Lesson never writes these tables directly. | BE1: `be1.parent_groups`, `be1.parent_group_members`, through a versioned BE1 port |
| `UploadSession`, `Asset` | Resumable upload, bytes, checksums, media validation and storage lifecycle; Lesson stores opaque refs only. | Core owns `core.upload_sessions`, `core.upload_parts` and asset metadata/storage |
| `LessonOccurrence` | A real teaching slot that pins a LessonVersion. It is separate from Lesson and is out of this API's first backend scope. | Lesson: `lesson.occurrences` |

The Lesson owner also stores idempotency receipts in `lesson.command_receipts`. This is an infrastructure ledger, not a domain entity exposed by the API.

## 4. Shared payloads

### `LessonContentInputV1`

```json
{
  "locale": "vi-VN",
  "title": "Vòng đời của bướm",
  "topic": "Bướm",
  "target_age_band_ref": "age_band_ref",
  "target_age_band_version": 1,
  "objectives": ["Quan sát các giai đoạn phát triển"],
  "drawing_subject": "Con bướm",
  "drawing_steps_text": "Bắt đầu bằng thân và cánh...",
  "subject_learning_notes": "Bướm phát triển qua các giai đoạn...",
  "script_direction": null,
  "script_following_allowed": false,
  "activities": [
    {
      "title": "Tìm hình dạng trong vườn",
      "objective": "Quan sát đối xứng và màu sắc",
      "materials_text": "Giấy, bút chì",
      "preparation_text": "Chọn nơi quan sát an toàn",
      "instructions_text": "Quan sát rồi phác lại hình dạng",
      "observation_notes": "Để trẻ tự mô tả điều nhìn thấy",
      "safety_notes": "Có người lớn hướng dẫn ngoài trời",
      "activity_kind": "outdoor"
    }
  ]
}
```

The age-band reference resolves to a versioned catalog entry inside 36–120 months. Activity IDs/order and LessonVersion IDs are server-created. `activities` must contain at least one item for a version submitted for review. A draft may be incomplete only if the final approved SRS allows that state; the initial contract requires a valid activity list to save a version.

### `LessonDetailV1`

```json
{
  "contract": "LessonDetailV1",
  "lesson_id": "opaque_lesson_id",
  "organization_id": "opaque_organization_id",
  "owner_kind": "ORGANIZATION",
  "created_by": "opaque_principal_ref",
  "state": "ACTIVE",
  "visibility": "PRIVATE",
  "current_version": {
    "version_id": "opaque_version_id",
    "version_no": 1,
    "review_state": "DRAFT",
    "content": {}
  },
  "revision": 1,
  "created_at": "2026-10-28T00:00:00Z",
  "updated_at": "2026-10-28T00:00:00Z"
}
```

The `content` object conforms to `LessonContentInputV1`; Parent responses are a narrower `ParentLessonDetailV1` projection and never contain `organization_id` internals, author-only metadata, source documents or extracted full text.

## 5. Endpoint contract

Unless specified otherwise, JSON responses are direct versioned DTOs with a `contract` discriminator. Errors use the shared BE1-shaped envelope described in §6.

| Method and path | Caller / purpose | Request | Success |
|---|---|---|---|
| `POST /organizations/{organization_id}/lessons` | Teacher; create a school-owned reusable draft. | `CreateLessonRequestV1 {content: LessonContentInputV1, visibility?: PRIVATE\|SCHOOL}`. Organization and author are derived/verified, not body fields. | `201 LessonDetailV1`, `ETag: "1"`. |
| `GET /organizations/{organization_id}/lessons` | Teacher or Manager; list lessons visible to staff in that school. | Query: `state?`, `visibility?`, `limit?`, `cursor?`. Teacher results are author-scoped by default; Manager results are school-scoped. | `200 LessonPageV1 {items: LessonSummaryV1[], next_cursor}`. |
| `GET /organizations/{organization_id}/lessons/{lesson_id}` | Teacher/Manager; read an authorized school lesson and current version. | None. | `200 LessonDetailV1`, `ETag: "<revision>"`. |
| `PATCH /organizations/{organization_id}/lessons/{lesson_id}` | Teacher; edit draft content. This creates a new immutable LessonVersion. | `UpdateLessonRequestV1 {content: LessonContentInputV1}`; strong `If-Match` required. Visibility/publication is changed only through grant/review routes. | `200 LessonDetailV1`, new `ETag`. Stale revision: `409`. |
| `DELETE /organizations/{organization_id}/lessons/{lesson_id}` | Teacher owner or authorized Manager; archive without physical deletion. | Strong `If-Match`; optional reason is not accepted unless a contract field is approved. | `200 LessonDetailV1 {state: ARCHIVED}`; historical versions/grants remain auditable, access is revoked by policy. |
| `POST /organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | Teacher; start a private source-document upload for that Lesson. | `CreateLessonUploadSessionRequestV1 {file_name, media_type, byte_length, sha256}`. Purpose and target are server-bound to the route. | `201 UploadSessionV1 {upload_session_id, state, part_size_bytes, expected_parts, expires_at}`. No storage URL or credential. |
| `PUT /upload-sessions/{upload_session_id}/parts/{part_number}` | Upload-session owner; upload/retry one bounded chunk. | Raw bytes ≤4 MiB; `X-Part-SHA256` and `Content-Range`. | `200 UploadPartReceiptV1 {part_number, byte_length, sha256, accepted}`. |
| `GET /upload-sessions/{upload_session_id}` | Upload-session owner; resume after a client reconnect and inspect accepted chunks and expiry. | None. | `200 UploadSessionV1 {upload_session_id, state, accepted_part_numbers, expected_parts, expires_at}`. |
| `DELETE /upload-sessions/{upload_session_id}` | Upload-session owner; abort an open upload and delete its private chunks. Repeating an abort is safe. | None. | `200 UploadSessionV1 {state: ABORTED}`. |
| `POST /upload-sessions/{upload_session_id}/complete` | Upload-session owner; finalize, malware-scan, validate and deterministically extract the document synchronously. | Empty body; `Idempotency-Key` required. | `200 LessonSourceDocumentStatusV1 {source_document_id, state: READY_FOR_REVIEW}`. |
| `GET /organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}` | Authoring Teacher; inspect upload/extraction status. | None. | `200 LessonSourceDocumentStatusV1 {state, safe_file_name, file_extension, page_or_slide_count, warnings, parser_version}`. No raw bytes. |
| `GET /organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}` | Authoring Teacher; preview the deterministic structured extraction and correctable fields. | None. | `200 LessonDocumentRevisionPreviewV1 {revision_id, extracted_fields, warnings, page_coverage, review_state}`. |
| `POST /organizations/{organization_id}/lessons/{lesson_id}/versions` | Teacher; confirm/correct a document revision and save it as a new immutable LessonVersion. | `CreateLessonVersionRequestV1 {source_document_revision_id, content: LessonContentInputV1}`; `If-Match` required. | `201 LessonVersionV1`; new current-version ETag. Only allowlisted structured fields are saved. |
| `POST /organizations/{organization_id}/lessons/{lesson_id}/access-grants` | Teacher; request Public access for an exact version or create an eligible school/Parent share. This creates the canonical `LessonAccessGrant` entity. | `CreateLessonAccessGrantRequestV1 {version_id, audience_kind: PUBLIC\|ORGANIZATION\|PRINCIPAL\|PARENT_GROUP, audience_ref?, capability: VIEW\|DOWNLOAD\|REUSE, expires_at?}`; `Idempotency-Key` required. `PUBLIC` has no `audience_ref`; other targets require one. A Teacher Public grant starts `PENDING_REVIEW`; named/group grants require an approved version. | `201 LessonAccessGrantV1`. Public grant is not readable until Manager approval; named grants may start `INVITED` until the Parent accepts. |
| `GET /organizations/{organization_id}/access-grants` | Manager; review queue and school grant list. The review queue is a filtered LessonAccessGrant collection. | Query: `audience_kind?`, `state?=PENDING_REVIEW`, `lesson_id?`, `limit?`, `cursor?`. | `200 LessonAccessGrantPageV1 {items, next_cursor}`. |
| `POST /organizations/{organization_id}/access-grants/{access_grant_id}/decision` | Manager; approve or request changes for a pending Public grant. Cannot approve own authored content. | `DecideLessonAccessGrantRequestV1 {decision: APPROVE\|REQUEST_CHANGES, reason?}`; `If-Match` and `Idempotency-Key` required. | `200 LessonAccessGrantV1 {access_grant_id, state: ACTIVE\|CHANGES_REQUESTED, approved_by?, decided_at}`. The decision affects only the exact version/audience grant. |
| `DELETE /organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}` | Grant owner/Manager; revoke a share. | `If-Match` required. | `200 LessonAccessGrantV1 {state: REVOKED, revoked_at}`. Future Parent reads are denied. |
| `POST /organizations/{organization_id}/parent-groups` | Manager; create an audience group in their school. | `CreateParentGroupRequestV1 {display_name}`. | `201 ParentGroupV1 {parent_group_id, organization_id, display_name, state}`. |
| `GET /organizations/{organization_id}/parent-groups` | Manager; list groups in their school. | Query: `limit?`, `cursor?`. | `200 ParentGroupPageV1`. |
| `POST /organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` | Manager; invite a verified Parent principal to a school audience group. This creates a `ParentGroupMembership` in invited state. | `InviteParentToGroupRequestV1 {parent_principal_ref}`; `Idempotency-Key` required. | `201 ParentGroupInvitationV1 {membership_id, parent_group_id, state: INVITED, expires_at}`; emits an in-app notification event. |
| `GET /me/parent-group-invitations` | Parent; list pending group invitations for the verified principal. | Query: `limit?`, `cursor?`. | `200 ParentGroupInvitationPageV1` (items project `ParentGroupMembership`). |
| `POST /me/parent-group-invitations/{membership_id}/accept` | Invited Parent; accept group membership. | `Idempotency-Key` required. | `200 ParentGroupMembershipV1 {membership_id, parent_group_id, state: ACTIVE}`. |
| `DELETE /organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` | Manager revokes membership; Parent may leave their own group. | `If-Match` required. | `200 ParentGroupMembershipV1 {state: REVOKED}`; group-based lesson access ends immediately. |
| `GET /me/lesson-invitations` | Parent; list direct named-lesson invitations for the verified principal. | Query: `limit?`, `cursor?`. | `200 LessonInvitationPageV1` (items project invited `LessonAccessGrant` records). |
| `POST /me/lesson-invitations/{access_grant_id}/accept` | Named Parent; accept a lesson share. | `Idempotency-Key` required. | `200 LessonAccessGrantV1 {access_grant_id, state: ACTIVE}`. |
| `POST /me/lesson-invitations/{access_grant_id}/decline` | Named Parent; decline a lesson share. | `Idempotency-Key` required. | `200 LessonAccessGrantV1 {access_grant_id, state: DECLINED}`. |
| `GET /me/lessons` | Parent; browse the Public library and active direct/group shares. | Query: `source?=ALL\|PUBLIC\|SHARED`, `limit?`, `cursor?`. | `200 ParentLessonPageV1 {items: ParentLessonSummaryV1[], next_cursor}`. No child profile is required. |
| `GET /me/lessons/{lesson_id}` | Parent; read one currently authorized Public/shared version. | None. | `200 ParentLessonDetailV1` (approved structured content only); hidden, unshared or revoked lessons return safe `404`. |
| `GET /me/lessons/{lesson_id}/download` | Parent; download authorized structured lesson content. This is not the original Teacher source file. | None; requires effective `DOWNLOAD` capability. | `200 LessonExportV1` as `application/json` attachment with a safe filename. |
| `PATCH /platform/lessons/{lesson_id}/moderation` | Platform Admin; hide or restore library access with a reason. | `ModerateLessonRequestV1 {state: HIDDEN\|VISIBLE, reason}`; `If-Match` and `Idempotency-Key` required. | `200 LessonModerationV1`; action is audited and recalculates Public read access. |

The two upload-session lifecycle operations close the resumability and abort gap in the Rev29 chunk protocol. They are owner-scoped and expose no object-store coordinates. Completion is synchronous because malware scanning and bounded extraction run in-process; `READY_FOR_REVIEW` means a Teacher must still inspect or correct extracted fields before creating a LessonVersion.

### Response DTO field sets

- `LessonSummaryV1`: `lesson_id`, `title`, `topic`, `current_version_no`, `review_state`, `visibility`, `activity_count`, `updated_at`.
- `LessonPageV1` / `ParentLessonPageV1`: `contract`, `items`, `next_cursor`. `ParentLessonSummaryV1` contains only `lesson_id`, `version_id`, `title`, `topic`, target age-band reference/version, activity count and access source (`PUBLIC` or `SHARED`).
- `LessonVersionV1`: `lesson_id`, `version_id`, `version_no`, `review_state`, `structured_content_hash`, optional confirmed `source_document_revision_id`, authored principal ref and timestamp. Staff detail includes `LessonContentInputV1` for the current version.
- `LessonAccessGrantV1`: `access_grant_id`, `lesson_id`, `version_id`, `audience_kind`, optional `audience_ref`, one `capability`, state, grantor, reviewer/approval time when applicable, expiry and revoke time. Parent responses never include another Parent's audience ref.
- `UploadSessionV1`: `upload_session_id`, state, `part_size_bytes`, `expected_parts`, accepted part numbers and expiry. It never contains an object-store URL, bucket, credential or storage endpoint.
- `LessonSourceDocumentStatusV1`: source document ref, safe file name, extension, state, validated page/slide count, parser/version, coverage and safe warnings. `LessonDocumentRevisionPreviewV1` contains only allowlisted structured fields and Teacher-correctable warnings.
- `ParentLessonDetailV1`: authorized LessonVersion fields, activities and access source/expiry. `LessonExportV1` is the same permitted structured projection for download; it excludes the original upload and full extraction text.
- `ParentGroupV1`, `ParentGroupMembershipV1` and the invitation page expose group/member IDs, state and timestamps needed by that actor only. Invitation DTOs project a `ParentGroupMembership` or `LessonAccessGrant`; they are not independent persistence entities.
- `LessonModerationV1`: `lesson_id`, moderation state, reason, moderator ref and decision timestamp.

## 6. Headers, errors and authorization results

| Condition | HTTP | Stable code |
|---|---:|---|
| Missing/invalid Firebase token | 401 | `UNAUTHENTICATED` |
| Verified actor has wrong role or scope | 403 | `FORBIDDEN` |
| Unknown or inaccessible scoped resource | 404 | `LESSON_NOT_FOUND` / `RESOURCE_NOT_FOUND` (do not disclose cross-school existence) |
| Missing `If-Match` on a required mutation | 428 | `PRECONDITION_REQUIRED` |
| Stale version/revision or conflicting lifecycle state | 409 | `STALE_REVISION`, `INVALID_TRANSITION`, `PUBLICATION_REQUIRED`, `GRANT_REVOKED` |
| Invalid body/field/age band/activity list | 422 | `INVALID_REQUEST` |
| File/chunk exceeds bound | 413 | `REQUEST_TOO_LARGE` |
| Unsupported/encrypted/invalid-signature file | 415 or 422 | `UNSUPPORTED_MEDIA_TYPE`, `INVALID_SOURCE_DOCUMENT` |
| Rate limit | 429 | `RATE_LIMITED` with `Retry-After` |
| Database/storage/parser dependency unavailable | 503 | `DEPENDENCY_UNAVAILABLE` |

Error body follows BE1: `{"code":"...","message":"Safe explanation","request_id":"..."}`. Never return request bodies, raw extraction text, file paths, storage endpoints, credentials, provider diagnostics or SQL details in errors.

## 7. State and access contract

- `Lesson.state` is the library-item lifecycle (`ACTIVE` or `ARCHIVED`); `LessonVersion.review_state` is `DRAFT`, `PENDING_REVIEW`, `CHANGES_REQUESTED` or `APPROVED`; `LessonAccessGrant.state` is `PENDING_REVIEW`, `INVITED`, `ACTIVE`, `DECLINED`, `EXPIRED` or `REVOKED` as applicable. Do not overload one state enum across the three entities.
- Public review is represented by a `LessonAccessGrant` whose `audience_kind=PUBLIC` and state is `PENDING_REVIEW`, then `ACTIVE` only after a same-school Manager decision. It is not a separate `LessonPublication` entity/table. The Manager queue is `/access-grants?audience_kind=PUBLIC&state=PENDING_REVIEW`.
- Approval marks that exact version approved and activates the grant atomically. Editing after publication creates a new `DRAFT` version while the previously approved version remains available through its active, version-scoped grant until a new grant is approved or the old grant is revoked.
- Named/group grants are version-scoped and can be invited, accepted, active, declined, expired or revoked. Every Parent list/detail call resolves current Public state, active membership, grant state and version.
- `PRIVATE`: author only. `SCHOOL`: same organization staff under role policy. `SELECTED_AUDIENCE`: active target grant only. `PUBLIC`: published version across organizations. Raw documents and full extraction revisions remain authoring-school private for every visibility.
- Parent endpoints return only library content. They do not read child profiles, story runs, occurrences, feedback or video assets.

## 8. Explicit non-goals

No AI suggestions, AI parsing, OCR, line-sketch generation, image/slide generation, video pipeline, quota/billing, Parent/Teacher UI, lesson-to-StoryRun/occurrence wiring, child-profile sharing, delivery history or feedback endpoints are part of this API contract.

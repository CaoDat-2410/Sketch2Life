# Parent Android API contract — Rev67 implementation slice

- **Status:** Implementation contract for the Parent profile, consent, physical-artwork, and story-draft slice.
- **Requirements authority:** FEAT-063 canonical working SRS v2.7-draft, Rev60 (unsigned), plus its Data Table Register. This artifact records the bounded API implementation and does not replace or amend the SRS.
- **Authentication:** Firebase ID token in `Authorization: Bearer <id-token>`. Backend resolves the server-owned account and requires role `parent` for every endpoint below.
- **Base path:** `/api/parent/v1`.
- **Runtime:** AI routes require `SKETCH2LIFE_AI_PROVIDER=modal_dev` and local/test environment. No AI request is sent when the optional sketch guide is off.
- **Data boundary:** Firebase is Authentication-only. Profile, consent, StoryRun, and artwork metadata live in PostgreSQL; artwork bytes use the private S3-compatible adapter (MinIO locally). The mobile app never receives storage credentials or object URLs.

## Common behavior

- JSON requests use strict, versioned schemas and reject unknown fields.
- Successful responses include a generated `request_id`; Parent StoryRun commands return the saved server state.
- Profile writes use optimistic `expected_revision`. Creating a profile also records the adult's explicit acceptance of the currently configured policy.
- StoryRun creation checks that the submitted consent policy version equals the server's current version and that the selected profile revision and authorization are current.
- A single active Parent StoryRun per account is enforced by the database unique active-owner key. `GET /story-runs/active/current` recovers it after the app reopens.
- AI requests are not automatically retried. `AWAITING_RECONCILIATION` and `RUNNING` block another dispatch from the UI.
- Safe errors use FastAPI `detail.code`; when available they also carry a request ID. Common codes include `PARENT_ROLE_REQUIRED`, `PARENT_CONSENT_POLICY_UNAVAILABLE`, `PARENT_CONSENT_POLICY_CHANGED`, `PARENT_DATA_AUTHORIZATION_REQUIRED`, `PARENT_PROFILE_REVISION_STALE`, `PARENT_ACTIVE_STORY_RUN_EXISTS`, `PARENT_STORY_RUN_NOT_FOUND`, `DRAWING_IMAGE_INVALID`, `MALWARE_DETECTED`, `MODAL_OUTCOME_UNKNOWN`, and `STORY_OUTPUT_INVALID`.

## Profile and authorization endpoints

| Method and path | Purpose | Request | Success |
|---|---|---|---|
| `GET /consent-policy` | Read the current approved data-authorization text before an adult accepts it. | None | `200 {request_id, policy: {purpose_code, policy_version, consent_text, consent_text_sha256}}` |
| `GET /child-profiles` | List profiles owned by the authenticated Parent, including current revision and whether the authorization matches the current policy. | None | `200 {request_id, profiles: ParentProfile[]}` |
| `POST /child-profiles` | Create a profile and record explicit consent for its initial revision. | `{age_months, display_name, interests_summary, consent_accepted: true, consent_policy_version}` | `201 {request_id, profile: ParentProfile}`; `ETag` contains revision number. |
| `GET /child-profiles/{parent_profile_id}` | Read one owned profile. | None | `200 {request_id, profile: ParentProfile}` |
| `PATCH /child-profiles/{parent_profile_id}` | Create an immutable profile revision. Requires a current authorization. | `{age_months, display_name, interests_summary, expected_revision}` | `200 {request_id, profile: ParentProfile}`; `ETag` contains the new revision. |
| `POST /child-profiles/{parent_profile_id}/data-authorizations` | Record acceptance of the exact current policy version after a policy update or revoke. | `{consent_accepted: true, consent_policy_version}` | `200 {request_id, profile: ParentProfile}` |
| `DELETE /child-profiles/{parent_profile_id}/data-authorizations` | Revoke active authorization. New StoryRuns and AI dispatches for that profile are denied. | None | `200 {request_id, profile: ParentProfile}` |
| `DELETE /child-profiles/{parent_profile_id}` | Archive the owned profile and revoke its active authorization. This is a soft archive. | None | `200 {request_id, profile: ParentProfile}` with `state: ARCHIVED`. |

`ParentProfile` contains `parent_profile_id`, `state`, `current_revision` (`profile_revision_id`, `revision`, `age_months`, `display_name`, `interests_summary`, `revision_sha256`, `created_at`), authorization state/version/currentness, and timestamps. Age is 36–120 months. No exact date of birth or age band is stored. The display name is not included in AI worker input.

The consent policy is configured only in the repository-root `.env`:

```dotenv
SKETCH2LIFE_PARENT_CONSENT_POLICY_VERSION=
SKETCH2LIFE_PARENT_CONSENT_POLICY_TEXT=
```

Empty or invalid values fail closed with `503 PARENT_CONSENT_POLICY_UNAVAILABLE`. The repository does not supply legal copy or a production policy version.

## StoryRun endpoints

| Method and path | Purpose | Request | Success |
|---|---|---|---|
| `POST /story-runs` | Pin an owned profile revision and adult-confirmed context snapshot for one Parent run. | `{parent_profile_id, expected_profile_revision_id, consent_policy_version, topic, adult_confirmed_idea, context_confirmed: true}` | `201 {request_id, story_run: ParentStoryRun}` |
| `GET /story-runs/active/current` | Resume the authenticated account's active StoryRun. | None | `200 {request_id, story_run: ParentStoryRun | null}` |
| `GET /story-runs/{run_id}` | Read an owned run, its saved context, subject review, story draft, and current workflow state. | None | `200 {request_id, story_run: ParentStoryRun}` |
| `POST /story-runs/{run_id}/subject-confirmations` | Persist adult confirmation/correction of the interpreted drawing subject. | `{expected_understanding_revision, confirmed_subject}` | `200 {request_id, story_run_id, understanding_revision, decision: CONFIRMED}` |
| `POST /story-runs/{run_id}/story-revision-confirmations` | Persist adult confirmation of the exact current story revision. | `{expected_revision, story_sha256}` | `200 {request_id, story_run: ParentStoryRun}`; story revision status becomes `CONFIRMED`. |

`ParentStoryRun` returns opaque IDs, run state, pinned profile revision, bounded `context_snapshot`, its SHA-256, input/understanding/story revision references, candidate subject, safe workflow error state, and the rendered story. The rendered story deliberately omits `visual_prompt` and `character_anchors`.

The context snapshot is `sketch2life.parent-context.v1` and contains only profile revision reference, age in months, bounded interests summary, topic, adult typed idea, and consent policy version. The adult confirms this snapshot before `POST /story-runs`; reopening the app shows the same saved snapshot.

## AI endpoints

| Method and path | Purpose | Request | Success |
|---|---|---|---|
| `POST /ai/sketch-guides` | Optional topic-only Parent line-sketch. The screen calls it only after the adult enables the toggle and presses the action. | `{topic, difficulty: "beginner", step_count: 3}` | `200` with request/call reference, DRAFT/review marker, asset metadata, and transient `image_base64`. No profile, age, StoryRun, or child artwork is sent. |
| `POST /ai/drawing-understandings` | Save one physical-paper JPEG/PNG privately, scan/normalize it, and request VLM subject/features for adult review. | `{story_run_id, image_base64, media_type: "image/jpeg" | "image/png"}` | `200` with StoryRun/input/understanding revision references, candidate, confidence, and `review_required: true`. |
| `POST /ai/story-runs/{run_id}/story-revisions` | Generate the first story draft or ask AI to rewrite a draft from an adult instruction. | `{expected_understanding_revision, rewrite_instruction?}` | `200` with saved StoryRun, versioned story draft, hash, model reference, and `review_required: true`. Initial story plus at most three AI rewrites. |

Artwork request limits are enforced by the versioned schema and image pipeline: JPEG/PNG signature validation, malware scan, image decode/normalization, private storage, checksum/provenance, and a server-owned run/profile/consent check. The app previews the image before sending it. No raw media or prompt is written to device logs.

## Workflow state labels exposed by this slice

`INPUT_PROCESSING`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`, `SCRIPT_REVIEW`, `VIDEO_ADMISSION_PENDING`, `DELETE_PENDING`, `FAILED`, `COMPLETED`.

The UI treats both `RUNNING` and `AWAITING_RECONCILIATION` as non-retryable pending work and refreshes saved state rather than redispatching. A known terminal failure releases the active-owner slot; an unknown outcome keeps it reserved.

## Not implemented by Rev67

- Voice capture, Whisper transcription, transcript review, and audio retention.
- A second VLM inference when the adult corrects the suggested subject. The current implementation records the adult correction as a new understanding revision; that does not prove the SRS's separate-VLM-reinterpretation requirement.
- Video admission/generation/playback, video quality retries, or the outdoor activity list after video.
- Parent run history, cancel/delete lifecycle, and cleanup of retained run assets.
- Durable AI-job polling/reconciliation, a general idempotency-key contract, and manual recovery from an unknown Modal result.
- Parent Sketch Guide temporary-asset expiry/cleanup and full SRS output safety/line-art validation.

These omissions remain implementation gaps against the canonical SRS; this artifact does not mark the overall Parent workflow complete.

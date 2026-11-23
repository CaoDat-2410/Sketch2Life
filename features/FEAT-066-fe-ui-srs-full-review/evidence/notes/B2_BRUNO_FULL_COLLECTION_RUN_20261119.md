# B2 Bruno full-collection run against the local API — 2026-11-19

Status: run record for task B2 (BRU-0a and the follow-on full run). Counts and request paths only; no response bodies, headers or tokens are recorded. Result: **no real defect found; no request could pass an authenticated check, because the local API has no identity verifier and the collection holds no valid token.** Pass/Fail below is the classification of this note, not Bruno's own counter.

## Setup

- Application: this branch at `6f10ec24` (C4 `bb57486d`, C5 `e9c9a815`, M9-B `6f10ec24` included), started on 127.0.0.1:8010 against a fresh disposable database on the loopback `frc08` container (migrated with `alembic upgrade heads`, exit 0, not seeded).
- Bruno CLI 4.3.0: `bru run requests -r --env local --env-var baseUrl=http://127.0.0.1:8010 --reporter-skip-all-headers --reporter-skip-body`, from the collection root; the L5 guard in `collection.bru` was active for every request. 147 requests ran (146 tracked plus the L5 A02 request). `requests/firebase-auth-helper/` is not present in this worktree, so no Firebase request ran and nothing was written to Firebase.
- No token was created or faked. The collection keeps the placeholder bearer value. The API has no Firebase verifier configured here, so every bearer request answers 503 `IDENTITY_PROVIDER_UNAVAILABLE`. The Bruno counter ("143 passed, 4 failed") is not used. Only A02 and requests `137`–`140` (parent-mobile-read-routes) carry checks; 5 of the checks in `137`–`140` fail because the verifier is absent (503), which is BLOCKED-AUTH, and the other 142 requests have no checks, so Bruno counts them as passed whatever the status.

## Classification (147 requests)

| Class | Count | Meaning |
|---|---:|---|
| PASS | 4 | `health/002`, `health/090` (200), L5 A02 (200 and 3 of 3 checks), `local-story-video/116` (200, an unauthenticated list route; a placeholder id returns an empty list) |
| FAIL (real defect) | 0 | No 5xx other than the identity-provider 503, no wrong route, no missing header found |
| BLOCKED-AUTH | 95 | 86 answered 503 `IDENTITY_PROVIDER_UNAVAILABLE` (a bearer is sent, the verifier is absent: SD-5 is not built); 4 answered 401 `AUTHENTICATION_REQUIRED` (`storyrun-lite` 125, 127, 129, 130, which hit the Parent routes on the same paths because the demo flag is off) and 5 answered 401 `INVALID_DEVICE_CREDENTIAL` (no usable bearer or device credential) |
| BLOCKED-ENV | 46 | `storyrun-lite/126` (401: the demo-only readiness route is not mounted, the path falls into the Parent run route), placeholder path or body values (29 × 422, 3 × 400 (`storyrun-lite/135` is a 400 from a placeholder `Content-Length` header, not an unmounted route), 404 for unknown placeholder jobs, sessions or runs) and local-only features that are off (`local-storage-examples` ×3 and `storyrun-lite` 128, 131–134 are dev-only routes that are not mounted: 404) |
| STALE | 2 | `organizations-classes/004` and `005` answer 404 `RESOURCE_NOT_FOUND`: the routes were replaced (see below). Already labelled stale in `requests/l5/README.md` |

Totals: 4 + 0 + 95 + 46 + 2 = 147.

By folder (status counts): be1-registry 503×1; collaborative-canvas 401×3, 503×3; health 200×2; l5 200×1; lesson-library-upload-sessions 503×4; local-capture-understanding 422×4, 404×1; local-guided-session 422×18; local-renderer-assets 422×4; local-storage-examples 404×3; local-story-video 200×1, 422×3, 404×4; organizations-classes 503×11, 404×2; parent-group-membership 503×1; parent-lesson-library 503×8; parent-mobile-read-routes 503×4; platform-admin-accounts 503×3; platform-admin-moderation 503×1; portal-auth 503×1; records-gallery 503×8; school-manager-sharing 503×5; session-artifacts 503×2; sessions-devices 401×2, 503×23, 400×2; staff-lesson-library 503×4; storyrun-lite 401×5, 404×5, 400×1; teacher-lesson-authoring 503×7.

What this proves: the changed C4, C5 and M9-B requests (`072`, `074`, `076`, `079`–`080`, `086`–`089`, `142`–`146`) reach their routes (503 from the auth dependency, not 404). It does not prove their request shape; that needs real tokens and seed data, which is a later step.

## Route and request coverage (route table of the running app against the request files)

- Request changes made here: `145` (GET teacher candidates, M9-B) and `146` (POST class assignment with `If-Match` and `Idempotency-Key`, M9-B) added; `ROLE_GUIDE.md` corrected for C5 (it said `142`–`144` carry no key). The C4 header changes (`072`, `074`, `076`, `080`, `086`) and the C5 changes (`142`–`144`) were already in the tree and match the route signatures (script check of key and `If-Match` headers against the router functions: no mismatch for the Lesson Library and Teacher routes; the Admin routes `143` and `144` read the key through a helper, so the script flags them, and a manual read of the router confirms the key).
- Stale requests, kept and labelled: `004` and `005` (replaced by `146`; the old assignment routes no longer exist).
- Routes with **no request** (not added here; outside the C4, C5 and M9-B scope): `POST /v1/parent/profiles`, `PATCH` and `DELETE /v1/parent/profiles/{profile_id}`, `DELETE /v1/story-runs/{run_id}`, `POST /v1/story-runs/{run_id}/context-confirmation` and `/script-confirmation`, `POST /api/auth/v1/registrations`, `POST /api/parent/v1/ai/drawing-understandings`, `/sketch-guides`, `/story-runs/{run_id}/story-revisions`, and `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions`, `/lesson-visuals`, `/sketch-decks`. They are open items for a later Bruno task.
- Request `144` uses `{{platform_account_id}}`, which `environments/local.bru` does not define (before B2); the literal text was sent and the 503 masks it; the owner decides whether to add it. Dev-only requests whose routes are not mounted in a default local run: `local-storage-examples` (needs the local storage-example flag and S3 settings) and the `storyrun-lite` routes (need the StoryRun-lite demo flag).

## Not verified

Authenticated behaviour of any route; Bruno desktop behaviour; the app with no database; the dev-only routes with their flags on; request bodies against the routes' schemas (placeholders only).

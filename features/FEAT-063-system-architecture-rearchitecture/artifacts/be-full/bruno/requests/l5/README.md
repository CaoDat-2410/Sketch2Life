# L5 Bruno requests

## Current scope

BRU-0a adds one positive baseline request. The post-B2 follow-up adds 13 route requests, bringing this L5 scope to 14 requests total. The full collection contains 160 requests: 159 regular request files plus the separate L5 A02 request. The coordinating review session's follow-up run used 153 requests because sequences 153–159 were intentionally excluded; those seven local-test-only requests were not sent or parsed by the Bruno CLI (parsing is NOT VERIFIED). See `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/BRUNO_POST_B2_FOLLOWUP_RUN_20261119.md` for the run conditions, counts, and paths.

| Case | Request | File | Auth | Sequence |
|---|---|---|---|---:|
| A02 | GET {{baseUrl}}/health | shared/bru-0/001-health-get.bru | none | 1 |

## Post-B2 route coverage

These route requests use synthetic placeholders. Requests 147–152 target Parent lifecycle routes and may be sent only to the disposable local database/API with the placeholder bearer. Requests 153–159 are local-test-only and must never run against a configured environment. They were excluded from the coordinating session's run copy, so Bruno CLI parsing for them is NOT VERIFIED.

| Case | Request | File | Auth | Sequence |
|---|---|---|---|---:|
| Parent profile create | POST /v1/parent/profiles | parent-mobile-lifecycle/147-create-parent-profile-v1-post.bru | bearer | 147 |
| Parent profile update | PATCH /v1/parent/profiles/{profile_id} | parent-mobile-lifecycle/148-update-parent-profile-v1-patch.bru | bearer | 148 |
| Parent profile delete | DELETE /v1/parent/profiles/{profile_id} | parent-mobile-lifecycle/149-delete-parent-profile-v1-delete.bru | bearer | 149 |
| Parent StoryRun delete | DELETE /v1/story-runs/{run_id} | parent-mobile-lifecycle/150-delete-parent-story-run-v1-delete.bru | bearer | 150 |
| Parent context confirmation | POST /v1/story-runs/{run_id}/context-confirmation | parent-mobile-lifecycle/151-confirm-parent-story-context-v1-post.bru | bearer | 151 |
| Parent script confirmation | POST /v1/story-runs/{run_id}/script-confirmation | parent-mobile-lifecycle/152-confirm-parent-story-script-v1-post.bru | bearer | 152 |
| Parent registration | POST /api/auth/v1/registrations | portal-auth/153-register-parent-account-api-auth-v1-post.bru | none; local-test-only | 153 |
| Parent drawing analysis | POST /api/parent/v1/ai/drawing-understandings | parent-ai/154-analyze-parent-drawing-api-parent-ai-post.bru | bearer; local-test-only | 154 |
| Parent sketch guide | POST /api/parent/v1/ai/sketch-guides | parent-ai/155-generate-parent-sketch-guide-api-parent-ai-post.bru | bearer; local-test-only | 155 |
| Parent story revision | POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions | parent-ai/156-generate-parent-story-revision-api-parent-ai-post.bru | bearer; local-test-only | 156 |
| Teacher lesson-plan suggestion | POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions | teacher-ai/157-suggest-teacher-lesson-plan-api-teacher-ai-post.bru | bearer; local-test-only | 157 |
| Teacher lesson visual | POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals | teacher-ai/158-generate-teacher-lesson-visual-api-teacher-ai-post.bru | bearer; local-test-only | 158 |
| Teacher sketch deck | POST /api/teacher/v1/organizations/{organization_id}/ai/sketch-decks | teacher-ai/159-generate-teacher-sketch-deck-api-teacher-ai-post.bru | bearer; local-test-only | 159 |

A02 sends Accept: application/json. It sends no Authorization header and no X-Request-ID header. Its three named checks cover status 200, the exact health JSON body, and the non-empty response X-Request-ID header added by CONV-1. The route reads no database data; whether the app process starts without a database is NOT VERIFIED.

## Run instructions

Owner-run only, with @usebruno/cli 4.3.0. From the Bruno collection root, pass the request folder path explicitly:

bru run requests/l5/shared/bru-0 --env local --reporter-skip-all-headers --reporter-skip-body

Do not run the collection root without an explicit safe scope. Keep every report or output file under tmp/feat066-l5/. CLI report/output content is counts only; the hand-written run record also lists request paths and class counts, without response headers or bodies. The owner-run steps and required run record are in features/FEAT-066-fe-ui-srs-full-review/plan/L5_BRU0A_RUNBOOK_20261119.md.

The 2026-11-19 broad subset used a temporary collection copy at `tmp/bruno-next/coll`, with requests 153–159 removed. For a separately authorized rerun of that same subset, first verify those seven requests are absent and the target is the disposable loopback API, then run from the copy root:

```text
bru run requests -r --env local --env-var baseUrl=http://127.0.0.1:8010 --reporter-skip-all-headers --reporter-skip-body
```

Do not run `bru run` on the full collection root without a path. The loopback guard allows loopback destinations, so it does not stop requests 153–159 from reaching the local registration or AI routes. Those requests remain outside any run until separately authorized.

## Collection loopback guard — verified for Bruno CLI 4.3.0; desktop NOT VERIFIED

collection.bru contains a pre-request guard. It calls bru.interpolate(req.getUrl()), parses the result by hand with string methods (the Bruno 4.3.0 CLI sandbox has no URL global), rejects user-info, backslashes, control characters and malformed ports, and allows only the exact hostnames 127.0.0.1, localhost, and [::1]. An uninterpolated URL fails parsing and throws. The goal run of 2026-11-19 verified, with the Bruno CLI 4.3.0: interpolation works, the collection script runs for every request, the --env-var override applies, and the guard throws a script error naming the guard for the three negative controls. See the BRU-0a evidence note for the run record.

The collection-level candidate is intended to guard every request run from this collection by the CLI: all 160 request files and the local-only requests/firebase-auth-helper/ folder where it exists. This statement is for the CLI only. Bruno desktop behavior is NOT VERIFIED and is not claimed here.

The pre-request check covers the URL at that point only. Redirects and URL changes made later by a request script are not covered. A request script that rewrites the baseUrl variable (for example with bru.setVar) would also bypass the check. Do not add setUrl, sendRequest, or runRequest calls to the new L5 Bruno scripts. To deliberately run a non-loopback request, use another collection or the owner's own branch without this collection.bru file.

## Existing request labels

These labels are recorded here without editing the existing request files.

| Request | Label |
|---|---|
| organizations-classes/004-create-assignment-api-be1-v1-organizations-organization-id.bru | stale (replaced by 146) |
| organizations-classes/005-revoke-assignment-api-be1-v1-organizations-organization-id.bru | stale (route removed; 146 is the first-Teacher command) |
| storyrun-lite/128-attach-asset-v1-story-runs-run-ref-assets-post.bru | dev-only |
| storyrun-lite/131-create-upload-v1-upload-sessions-post.bru | dev-only |
| storyrun-lite/132-abort-upload-v1-upload-sessions-upload-ref-delete.bru | dev-only |
| storyrun-lite/133-get-upload-v1-upload-sessions-upload-ref-get.bru | dev-only |
| storyrun-lite/134-complete-upload-v1-upload-sessions-upload-ref-complete-pos.bru | dev-only |
| storyrun-lite/135-put-upload-part-v1-upload-sessions-upload-ref-parts-part-n.bru | dev-only |
| storyrun-lite/125, 126, 127, 129, 130 (create, readiness, get, cancel, subject confirmation) | dev-only; with the demo flag off the same paths reach the Parent story-run routes (401 without a verified token), and 126 has no route |

## Provisional role-variable names

These upper-snake-case names are PROVISIONAL until O-BRU-AUTH is decided. They are names only; no values are listed.

- Platform Admin: TOKEN_PLATFORM_ADMIN
- School Manager: TOKEN_MANAGER_ORG_A, TOKEN_MANAGER_ORG_B
- Teacher: TOKEN_TEACHER_ASSIGNED, TOKEN_TEACHER_UNASSIGNED, TOKEN_TEACHER_NO_ORG
- Parent: TOKEN_PARENT_P1, TOKEN_PARENT_P2, TOKEN_PARENT_P3

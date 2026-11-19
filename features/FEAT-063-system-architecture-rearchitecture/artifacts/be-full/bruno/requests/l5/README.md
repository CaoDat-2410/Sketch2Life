# L5 Bruno requests

## Current scope

BRU-0a adds one positive baseline request:

| Case | Request | File | Auth | Sequence |
|---|---|---|---|---:|
| A02 | GET {{baseUrl}}/health | shared/bru-0/001-health-get.bru | none | 1 |

A02 sends Accept: application/json. It sends no Authorization header and no X-Request-ID header. Its three named checks cover status 200, the exact health JSON body, and the non-empty response X-Request-ID header added by CONV-1. The route reads no database data; whether the app process starts without a database is NOT VERIFIED.

## Run instructions

Owner-run only, with @usebruno/cli 4.3.0. From the Bruno collection root, pass the request folder path explicitly:

bru run requests/l5/shared/bru-0 --env local --reporter-skip-all-headers --reporter-skip-body

Do not run the collection root without a path. Keep every report or output file under tmp/feat066-l5/. CLI report/output content is counts only; the hand-written run record also lists failure request paths and error classes, without response headers or bodies. The owner-run steps and required run record are in features/FEAT-066-fe-ui-srs-full-review/plan/L5_BRU0A_RUNBOOK_20261119.md.

## Collection loopback guard — verified for Bruno CLI 4.3.0; desktop NOT VERIFIED

collection.bru contains a pre-request guard. It calls bru.interpolate(req.getUrl()), parses the result by hand with string methods (the Bruno 4.3.0 CLI sandbox has no URL global), rejects user-info, backslashes, control characters and malformed ports, and allows only the exact hostnames 127.0.0.1, localhost, and [::1]. An uninterpolated URL fails parsing and throws. The goal run of 2026-11-19 verified, with the Bruno CLI 4.3.0: interpolation works, the collection script runs for every request, the --env-var override applies, and the guard throws a script error naming the guard for the three negative controls. See the BRU-0a evidence note for the run record.

The collection-level candidate is intended to guard every request run from this collection by the CLI: the 146 tracked request files and the local-only requests/firebase-auth-helper/ folder where it exists. This statement is for the CLI only. Bruno desktop behavior is NOT VERIFIED and is not claimed here.

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

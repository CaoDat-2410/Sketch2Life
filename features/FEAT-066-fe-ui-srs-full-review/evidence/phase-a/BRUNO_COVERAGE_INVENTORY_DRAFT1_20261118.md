# Bruno Coverage Inventory ? Draft 1

**Date:** 2026-11-18  
**Scope:** FEAT-066 Phase A, read-only inventory.  
**Source status:** the root checkout collection includes the owner?s uncommitted edits; no Bruno or repository source file was changed.

## Scope and method

- Runtime rows come from `features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/openapi-runtime-frozen.json` (151 operations). Classifications are copied row by row from `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_OPERATION_INVENTORY_AND_CONTRACT_FREEZE_20261118.md`.
- The collection contains 145 `.bru` request files. The supplied collection path has no `README.md`; `ROLE_GUIDE.md` and `bruno.json` are present.
- Matching requires the same HTTP method and path template. Query strings are ignored; dynamic path segments match template parameters.
- `Assertions/tests` is Yes when a matching request has a `script:post-response` or `assert {}` block. `Negative case` is Yes only when the file name marks a negative/refusal case or an assertion expects a failure status.
- Status is artifact coverage: `COVERED` = matching request plus assertion/script; `PARTIAL` = match with no assertion/script; `MISSING` = no matching request. `COVERED` does not mean the Draft 4 L5 full-case requirement is complete.
- The provided dev-router matching was performed statically in the prior pass. This report reuses those dispositions; it does not reread router files. No Bruno run, tests, app, database, Docker, network/fetch, or state-changing Git command was used.

## Environment files

| File | Placeholder assessment | Review variables |
| --- | --- | --- |
| `local.bru` | REVIEW ? not all values look like placeholders | `bearerToken` |

No environment value is reproduced. This row reuses the earlier value-free scan; no environment file was opened during report generation.

## Coverage summary

| Measure | Count |
| --- | ---: |
| Runtime operations | 151 |
| Operations with a matching Bruno request | 134 |
| COVERED | 4 |
| PARTIAL | 130 |
| MISSING | 17 |
| Operations with a recognized negative case | 0 |

### By M2 classification

| Primary row classification | Operations | COVERED | PARTIAL | MISSING |
| --- | ---: | ---: | ---: | ---: |
| T ? M2 target | 9 | 4 | 2 | 3 |
| PR ? proposal/conditional | 3 | 0 | 1 | 2 |
| PO ? pilot-only | 5 | 0 | 1 | 4 |
| LE ? local example | 3 | 0 | 3 | 0 |
| OO ? OPEN-OWNER | 11 | 0 | 4 | 7 |
| CB ? BE1 compatibility | 54 | 0 | 53 | 1 |
| CD ? demo-group compatibility | 35 | 0 | 35 | 0 |
| OS ? outside M2 scope | 31 | 0 | 31 | 0 |

Combined labels are preserved in the matrix: five rows are `PO + CB`; one is `T + PR`. The source prose tally says ?proposal 3? while the operation rows contain three `PR`-only rows plus the `T + PR` row. Counts above use the first class code for unique-row totals and preserve the secondary tag per row.

### By request folder

Folder counts are not additive across folders; an operation may be represented in more than one folder. ?Unmatched files? are outside the 151-operation table.

| Request folder | `.bru` files | Matched operations | COVERED operations | PARTIAL operations | Unmatched files |
| --- | ---: | ---: | ---: | ---: | ---: |
| `be1-registry` | 1 | 1 | 0 | 1 | 0 |
| `collaborative-canvas` | 6 | 6 | 0 | 6 | 0 |
| `firebase-auth-helper` | 1 | 0 | 0 | 0 | 1 |
| `health` | 2 | 2 | 0 | 2 | 0 |
| `lesson-library-upload-sessions` | 4 | 4 | 0 | 4 | 0 |
| `local-capture-understanding` | 5 | 5 | 0 | 5 | 0 |
| `local-guided-session` | 18 | 18 | 0 | 18 | 0 |
| `local-renderer-assets` | 4 | 4 | 0 | 4 | 0 |
| `local-storage-examples` | 3 | 3 | 0 | 3 | 0 |
| `local-story-video` | 8 | 8 | 0 | 8 | 0 |
| `organizations-classes` | 11 | 9 | 0 | 9 | 2 |
| `parent-group-membership` | 1 | 1 | 0 | 1 | 0 |
| `parent-lesson-library` | 8 | 8 | 0 | 8 | 0 |
| `parent-mobile-read-routes` | 4 | 4 | 4 | 0 | 0 |
| `platform-admin-accounts` | 3 | 3 | 0 | 3 | 0 |
| `platform-admin-moderation` | 1 | 1 | 0 | 1 | 0 |
| `portal-auth` | 1 | 1 | 0 | 1 | 0 |
| `records-gallery` | 8 | 8 | 0 | 8 | 0 |
| `school-manager-sharing` | 5 | 5 | 0 | 5 | 0 |
| `session-artifacts` | 2 | 2 | 0 | 2 | 0 |
| `sessions-devices` | 27 | 27 | 0 | 27 | 0 |
| `staff-lesson-library` | 4 | 4 | 0 | 4 | 0 |
| `storyrun-lite` | 11 | 4 | 1 | 3 | 6 |
| `teacher-lesson-authoring` | 7 | 7 | 0 | 7 | 0 |

## Draft 4 ?6 L5 lane gaps

Authority: `.worktrees/manager-api/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, ?6 ?L5 Bruno tests?. L5 covers every operation in the L3 audit scope: full positive and negative cases for integrated operations; auth-boundary and refusal cases for excluded or FE-disabled operations; status, envelope, and key-field assertions; negative cases for out-of-scope 404, same-key replay, same-key/different-payload 400, stale-revision 409, and pagination bounds. Payment endpoints belong to the payment teammate.

- **Parent first slice:** Draft 4 ?6 L4 names eight M2-allowed operations. Collection result: 8/8 requests, 4 COVERED, 1 PARTIAL, 3 MISSING. Missing: `POST /v1/parent/profiles`, `PATCH /v1/parent/profiles/{profile_id}`, and `DELETE /v1/parent/profiles/{profile_id}`. Four matched reads have positive response checks; no negative case was detected.
- **Parent cancel:** Draft 4 places cancel after client projection. The matching request is PARTIAL and has no assertion/refusal case; current per-operation L3 disposition remains **NOT VERIFIED**.
- **Web integration references:** Draft 4 ?6 L4 records 27 page-called templates across three web roles. `ROLE_GUIDE.md` explicitly maps 11 Manager and 3 Platform Admin operations, plus shared auth and health; 16/16 have matching requests and 0/16 have assertions. The remaining web-template-to-operation mapping is **NOT VERIFIED**.
- **FE-disabled route:** `POST /api/be1/v1/organizations/{organization_id}/classes` is marked disabled in `ROLE_GUIDE.md`; its request is PARTIAL and no auth-boundary/refusal case is detected.
- **Negative-case suite:** zero recognized negative cases across the collection. No asserted case was found for out-of-scope 404, same-key replay, same-key/different-payload 400, stale-revision 409, or pagination bounds.
- **Assertion depth:** four matched runtime operations have post-response checks; they cover positive responses/body/key properties. No failure-status assertion, error-envelope assertion, or `assert {}` block was detected.
- **Per-operation disposition:** the eight Parent first-slice operations, the explicitly mapped `ROLE_GUIDE.md` routes, the disabled Manager route, and Parent cancel are identified below. Other operation-level integrated/excluded assignments are **NOT VERIFIED** because the Phase A inputs do not provide the complete L3 role register.
- **Payment:** no payment/billing/invoice/checkout/webhook/subscription operation was identified in the supplied frozen 151-operation list; no payment row is included in this inventory.

## `.bru` files matching no frozen operation

| Disposition | Request file |
| --- | --- |
| External Firebase Auth helper; outside the local API operation list | `requests/firebase-auth-helper/001-parent-email-password-sign-in.bru` |
| NOT VERIFIED ? stale/path-drift candidate; no exact frozen or supplied dev-router match | `requests/organizations-classes/004-create-assignment-api-be1-v1-organizations-organization-id.bru` |
| NOT VERIFIED ? stale/path-drift candidate; no exact frozen or supplied dev-router match | `requests/organizations-classes/005-revoke-assignment-api-be1-v1-organizations-organization-id.bru` |
| Dev-router declaration; absent from the frozen operation list | `requests/storyrun-lite/128-attach-asset-v1-story-runs-run-ref-assets-post.bru` |
| Dev-router declaration; absent from the frozen operation list | `requests/storyrun-lite/131-create-upload-v1-upload-sessions-post.bru` |
| Dev-router declaration; absent from the frozen operation list | `requests/storyrun-lite/132-abort-upload-v1-upload-sessions-upload-ref-delete.bru` |
| Dev-router declaration; absent from the frozen operation list | `requests/storyrun-lite/133-get-upload-v1-upload-sessions-upload-ref-get.bru` |
| Dev-router declaration; absent from the frozen operation list | `requests/storyrun-lite/134-complete-upload-v1-upload-sessions-upload-ref-complete-pos.bru` |
| Dev-router declaration; absent from the frozen operation list | `requests/storyrun-lite/135-put-upload-part-v1-upload-sessions-upload-ref-parts-part-n.bru` |

Six unmatched request files correspond to route declarations found in the supplied manager-api dev router tree:

| Dev method/path | Router file | Bruno request file |
| --- | --- | --- |
| `POST /v1/story-runs/{run_ref}/assets` | `story_run_lite.py` | `requests/storyrun-lite/128-attach-asset-v1-story-runs-run-ref-assets-post.bru` |
| `POST /v1/upload-sessions` | `story_run_lite.py` | `requests/storyrun-lite/131-create-upload-v1-upload-sessions-post.bru` |
| `DELETE /v1/upload-sessions/{upload_ref}` | `story_run_lite.py` | `requests/storyrun-lite/132-abort-upload-v1-upload-sessions-upload-ref-delete.bru` |
| `GET /v1/upload-sessions/{upload_ref}` | `story_run_lite.py` | `requests/storyrun-lite/133-get-upload-v1-upload-sessions-upload-ref-get.bru` |
| `POST /v1/upload-sessions/{upload_ref}/complete` | `story_run_lite.py` | `requests/storyrun-lite/134-complete-upload-v1-upload-sessions-upload-ref-complete-pos.bru` |
| `PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}` | `story_run_lite.py` | `requests/storyrun-lite/135-put-upload-part-v1-upload-sessions-upload-ref-parts-part-n.bru` |

## Runtime operation matrix

| Method | Path | M2 classification | L5 disposition | Bruno request file(s) | Assertions/tests | Negative case | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GET | `/api/auth/v1/me` | `OO` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/portal-auth/141-current-account-role.bru` | No | No | **PARTIAL** |
| POST | `/api/auth/v1/registrations` | `OO` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/be1/v1/assistance-requests` | `PO + CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/be1/v1/assistance-requests/{assistance_id}/cancel` | `PO + CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/be1/v1/classes/{class_id}/assignments` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/be1/v1/device-grants/{grant_id}/join-status` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/001-read-join-status-api-be1-v1-device-grants-grant-id-join-st.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/health` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/health/002-be1-health-api-be1-v1-health-get.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}` | `CB` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/organizations-classes/003-read-organization-api-be1-v1-organizations-organization-id.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/classes` | `CB` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/organizations-classes/006-list-classes-api-be1-v1-organizations-organization-id-clas.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/classes` | `CB` | FE-disabled ? refusal/auth-boundary expected | `requests/organizations-classes/007-create-class-api-be1-v1-organizations-organization-id-clas.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | `CB` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/organizations-classes/008-list-consents-api-be1-v1-organizations-organization-id-cla.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/organizations-classes/009-record-consent-api-be1-v1-organizations-organization-id-cl.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/organizations-classes/010-revoke-consent-api-be1-v1-organizations-organization-id-cl.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/observations` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/011-create-observation-api-be1-v1-organizations-organization-i.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | `CB` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/organizations-classes/012-list-profiles-api-be1-v1-organizations-organization-id-cla.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/organizations-classes/013-create-profile-api-be1-v1-organizations-organization-id-cl.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/014-read-portfolio-api-be1-v1-organizations-organization-id-cl.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/data-requests` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/015-create-data-request-api-be1-v1-organizations-organization-.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/data-requests/{request_id}` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/016-read-data-request-api-be1-v1-organizations-organization-id.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/gallery` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/017-list-gallery-api-be1-v1-organizations-organization-id-gall.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/gallery` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/018-create-gallery-snapshot-api-be1-v1-organizations-organizat.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/annotations` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/019-annotate-gallery-api-be1-v1-organizations-organization-id-.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/publish` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/records-gallery/020-publish-gallery-api-be1-v1-organizations-organization-id-g.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/me` | `CB` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/organizations-classes/021-current-assignments-api-be1-v1-organizations-organization-.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/022-create-session-api-be1-v1-organizations-organization-id-se.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/023-read-session-api-be1-v1-organizations-organization-id-sess.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/session-artifacts/024-upload-session-artifact-api-be1-v1-organizations-organizat.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref}` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/session-artifacts/025-download-session-artifact-api-be1-v1-organizations-organiz.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status` | `PO + CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/collaborative-canvas/026-sync-canvas-operations-api-be1-v1-organizations-organizati.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/collaborative-canvas/027-append-canvas-operation-api-be1-v1-organizations-organizat.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/completion` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/028-complete-session-api-be1-v1-organizations-organization-id-.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/029-refresh-device-grant-api-be1-v1-organizations-organization.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/finish` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/030-finish-session-api-be1-v1-organizations-organization-id-se.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/031-create-group-api-be1-v1-organizations-organization-id-sess.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/collaborative-canvas/032-save-checkpoint-api-be1-v1-organizations-organization-id-s.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/collaborative-canvas/033-read-latest-checkpoint-api-be1-v1-organizations-organizati.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/034-control-group-api-be1-v1-organizations-organization-id-ses.bru` | No | No | **PARTIAL** |
| PUT | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/members/{child_id}` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/035-assign-member-to-group-api-be1-v1-organizations-organizati.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/collaborative-canvas/036-restore-checkpoint-api-be1-v1-organizations-organization-i.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/turns/{child_id}` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/037-start-child-turn-api-be1-v1-organizations-organization-id-.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/038-request-device-join-api-be1-v1-organizations-organization-.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/039-list-join-requests-api-be1-v1-organizations-organization-i.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/admit` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/040-admit-device-api-be1-v1-organizations-organization-id-sess.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/revoke` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/041-revoke-device-grant-api-be1-v1-organizations-organization-.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/042-read-learning-stage-api-be1-v1-organizations-organization-.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/043-advance-learning-stage-api-be1-v1-organizations-organizati.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/lobby` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/044-open-lobby-api-be1-v1-organizations-organization-id-sessio.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/help` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/045-request-help-api-be1-v1-organizations-organization-id-sess.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/leave` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/046-leave-session-api-be1-v1-organizations-organization-id-ses.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/progress` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/047-update-progress-api-be1-v1-organizations-organization-id-s.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/048-read-session-outcome-api-be1-v1-organizations-organization.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pause` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/049-pause-session-api-be1-v1-organizations-organization-id-ses.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles` | `PO + CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/be1-registry/050-list-pilot-profiles-api-be1-v1-organizations-organization-.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/collaborative-canvas/051-reconnect-canvas-api-be1-v1-organizations-organization-id-.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/resume` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/052-resume-session-api-be1-v1-organizations-organization-id-se.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/053-rotate-room-code-api-be1-v1-organizations-organization-id-.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/054-read-session-roster-api-be1-v1-organizations-organization-.bru` | No | No | **PARTIAL** |
| POST | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/start` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/055-start-session-api-be1-v1-organizations-organization-id-ses.bru` | No | No | **PARTIAL** |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending` | `PO + CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/be1/v1/room-code/join` | `CB` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/sessions-devices/056-request-room-code-join-api-be1-v1-room-code-join-post.bru` | No | No | **PARTIAL** |
| POST | `/api/dev/v1/storage-examples/lesson-source-documents` | `LE` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-storage-examples/057-upload-lesson-source-example-api-dev-v1-storage-examples-l.bru` | No | No | **PARTIAL** |
| DELETE | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | `LE` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-storage-examples/058-delete-lesson-source-example-api-dev-v1-storage-examples-l.bru` | No | No | **PARTIAL** |
| GET | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | `LE` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-storage-examples/059-download-lesson-source-example-api-dev-v1-storage-examples.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/me/lesson-invitations` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/060-list-lesson-invitations-api-lesson-library-v1-me-lesson-in.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/061-accept-lesson-invitation-api-lesson-library-v1-me-lesson-i.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/062-decline-lesson-invitation-api-lesson-library-v1-me-lesson-.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/me/lessons` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/063-list-parent-lessons-api-lesson-library-v1-me-lessons-get.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/me/lessons/{lesson_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/064-get-parent-lesson-api-lesson-library-v1-me-lessons-lesson-.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/me/lessons/{lesson_id}/download` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/065-download-parent-lesson-api-lesson-library-v1-me-lessons-le.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/me/parent-group-invitations` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/066-list-parent-group-invitations-api-lesson-library-v1-me-par.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-lesson-library/067-accept-parent-group-invitation-api-lesson-library-v1-me-pa.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/access-grants` | `OS` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/school-manager-sharing/068-list-access-grants-api-lesson-library-v1-organizations-org.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` | `OS` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/school-manager-sharing/069-decide-access-grant-api-lesson-library-v1-organizations-or.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/staff-lesson-library/070-list-lessons-api-lesson-library-v1-organizations-organizat.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/teacher-lesson-authoring/071-create-lesson-api-lesson-library-v1-organizations-organiza.bru` | No | No | **PARTIAL** |
| DELETE | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/staff-lesson-library/072-archive-lesson-api-lesson-library-v1-organizations-organiz.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `OS` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/staff-lesson-library/073-get-lesson-api-lesson-library-v1-organizations-organizatio.bru` | No | No | **PARTIAL** |
| PATCH | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/teacher-lesson-authoring/074-update-lesson-api-lesson-library-v1-organizations-organiza.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/teacher-lesson-authoring/075-create-access-grant-api-lesson-library-v1-organizations-or.bru` | No | No | **PARTIAL** |
| DELETE | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/staff-lesson-library/076-revoke-access-grant-api-lesson-library-v1-organizations-or.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/teacher-lesson-authoring/077-get-source-document-api-lesson-library-v1-organizations-or.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/teacher-lesson-authoring/078-get-document-revision-api-lesson-library-v1-organizations-.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/teacher-lesson-authoring/079-create-upload-session-api-lesson-library-v1-organizations-.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/teacher-lesson-authoring/080-create-lesson-version-api-lesson-library-v1-organizations-.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | `OS` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/school-manager-sharing/081-list-parent-groups-api-lesson-library-v1-organizations-org.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | `OS` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/school-manager-sharing/082-create-parent-group-api-lesson-library-v1-organizations-or.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/school-manager-sharing/083-invite-parent-to-group-api-lesson-library-v1-organizations.bru` | No | No | **PARTIAL** |
| DELETE | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/parent-group-membership/084-revoke-parent-group-membership-api-lesson-library-v1-organ.bru` | No | No | **PARTIAL** |
| PATCH | `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/platform-admin-moderation/085-moderate-lesson-api-lesson-library-v1-platform-lessons-les.bru` | No | No | **PARTIAL** |
| DELETE | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/lesson-library-upload-sessions/086-abort-upload-session-api-lesson-library-v1-upload-sessions.bru` | No | No | **PARTIAL** |
| GET | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/lesson-library-upload-sessions/087-get-upload-session-api-lesson-library-v1-upload-sessions-u.bru` | No | No | **PARTIAL** |
| POST | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/lesson-library-upload-sessions/088-complete-upload-api-lesson-library-v1-upload-sessions-uplo.bru` | No | No | **PARTIAL** |
| PUT | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/parts/{part_number}` | `OS` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/lesson-library-upload-sessions/089-upload-part-api-lesson-library-v1-upload-sessions-upload-s.bru` | No | No | **PARTIAL** |
| POST | `/api/parent/v1/ai/drawing-understandings` | `OO` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/parent/v1/ai/sketch-guides` | `OO` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/parent/v1/ai/story-runs/{run_id}/story-revisions` | `OO` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| GET | `/api/platform-admin/v1/accounts` | `OO` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/platform-admin-accounts/142-list-accounts.bru` | No | No | **PARTIAL** |
| POST | `/api/platform-admin/v1/accounts` | `OO` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/platform-admin-accounts/143-create-account.bru` | No | No | **PARTIAL** |
| PATCH | `/api/platform-admin/v1/accounts/{account_id}` | `OO` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/platform-admin-accounts/144-update-account.bru` | No | No | **PARTIAL** |
| POST | `/api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions` | `OO` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals` | `OO` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/api/teacher/v1/organizations/{organization_id}/ai/sketch-decks` | `OO` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| GET | `/health` | `OS` | Integrated / adapter-backed ? ROLE_GUIDE.md | `requests/health/090-health-health-get.bru` | No | No | **PARTIAL** |
| GET | `/v1/parent/profiles` | `T` | Integrated ? Parent first slice (Draft 4 ?6 L4) | `requests/parent-mobile-read-routes/137-list-parent-profiles-v1-get.bru` | Yes | No | **COVERED** |
| POST | `/v1/parent/profiles` | `T` | Integrated ? Parent first slice (Draft 4 ?6 L4) | ? | No | No | **MISSING** |
| DELETE | `/v1/parent/profiles/{profile_id}` | `T` | Integrated ? Parent first slice (Draft 4 ?6 L4) | ? | No | No | **MISSING** |
| GET | `/v1/parent/profiles/{profile_id}` | `T` | Integrated ? Parent first slice (Draft 4 ?6 L4) | `requests/parent-mobile-read-routes/138-read-parent-profile-by-id-v1-get.bru` | Yes | No | **COVERED** |
| PATCH | `/v1/parent/profiles/{profile_id}` | `T` | Integrated ? Parent first slice (Draft 4 ?6 L4) | ? | No | No | **MISSING** |
| POST | `/v1/profile/preferences/classify` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-capture-understanding/091-classify-preferences-v1-profile-preferences-classify-post.bru` | No | No | **PARTIAL** |
| GET | `/v1/renderer/pixi-asset` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-renderer-assets/092-read-renderer-pixi-asset-v1-renderer-pixi-asset-get.bru` | No | No | **PARTIAL** |
| GET | `/v1/renderer/rig-mask` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-renderer-assets/093-read-renderer-rig-mask-v1-renderer-rig-mask-get.bru` | No | No | **PARTIAL** |
| GET | `/v1/renderer/rig-package` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-renderer-assets/094-read-renderer-rig-package-v1-renderer-rig-package-get.bru` | No | No | **PARTIAL** |
| GET | `/v1/renderer/source` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-renderer-assets/095-read-renderer-source-v1-renderer-source-get.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/096-create-session-v1-sessions-post.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/097-get-session-v1-sessions-session-id-get.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/experience/prepare` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/098-prepare-experience-v1-sessions-session-id-experience-prepa.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/feedback` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/099-record-feedback-v1-sessions-session-id-feedback-post.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/gallery` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/100-read-gallery-v1-sessions-session-id-gallery-get.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/gate-a/confirm` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/101-confirm-gate-a-v1-sessions-session-id-gate-a-confirm-post.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/gate-b/approve` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/102-approve-gate-b-v1-sessions-session-id-gate-b-approve-post.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/handoff` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/103-complete-handoff-v1-sessions-session-id-handoff-post.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/media/audio` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-capture-understanding/104-upload-audio-v1-sessions-session-id-media-audio-post.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/media/image` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-capture-understanding/105-upload-image-v1-sessions-session-id-media-image-post.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/media/retake` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/106-request-retake-v1-sessions-session-id-media-retake-post.bru` | No | No | **PARTIAL** |
| PUT | `/v1/sessions/{session_id}/p1-context` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/107-set-p1-context-v1-sessions-session-id-p1-context-put.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/p1-filter` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/108-run-p1-filter-v1-sessions-session-id-p1-filter-post.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/p1/activity-suggestions` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/109-read-p1-activity-suggestions-v1-sessions-session-id-p1-act.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/p1/activity-suggestions/rank` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/110-rank-p1-activity-suggestions-v1-sessions-session-id-p1-act.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/p1/context-candidates` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/111-read-p1-context-candidates-v1-sessions-session-id-p1-conte.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/p1/context-options` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/112-read-p1-context-options-v1-sessions-session-id-p1-context-.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/p1/context-options` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/113-read-personalized-p1-context-options-v1-sessions-session-i.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/p1/context-options/finalize` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/114-finalize-p1-context-options-v1-sessions-session-id-p1-cont.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/renderer/launch` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-guided-session/115-prepare-renderer-v1-sessions-session-id-renderer-launch-po.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/story-video-jobs` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/116-list-story-video-jobs-v1-sessions-session-id-story-video-j.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/story-video-jobs` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/117-create-story-video-job-v1-sessions-session-id-story-video-.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/story-video/{job_id}` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/118-get-story-video-status-v1-sessions-session-id-story-video-.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/story-video/{job_id}/file` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/119-stream-story-video-v1-sessions-session-id-story-video-job-.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/understanding` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-capture-understanding/120-run-understanding-v1-sessions-session-id-understanding-pos.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/understanding/progress` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-capture-understanding/121-read-understanding-progress-v1-sessions-session-id-underst.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/whiteboard-video` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/122-get-whiteboard-video-status-v1-sessions-session-id-whitebo.bru` | No | No | **PARTIAL** |
| POST | `/v1/sessions/{session_id}/whiteboard-video-jobs` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/123-create-whiteboard-video-job-v1-sessions-session-id-whitebo.bru` | No | No | **PARTIAL** |
| GET | `/v1/sessions/{session_id}/whiteboard-video/file` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/124-stream-whiteboard-video-v1-sessions-session-id-whiteboard-.bru` | No | No | **PARTIAL** |
| POST | `/v1/story-runs` | `T` | Integrated ? Parent first slice (Draft 4 ?6 L4) | `requests/storyrun-lite/125-create-run-v1-story-runs-post.bru` | No | No | **PARTIAL** |
| GET | `/v1/story-runs/active/current` | `T + PR` | Integrated ? Parent first slice (Draft 4 ?6 L4) | `requests/parent-mobile-read-routes/139-read-active-parent-story-run-v1-get.bru` | Yes | No | **COVERED** |
| GET | `/v1/story-runs/{run_id}` | `T` | Integrated ? Parent first slice (Draft 4 ?6 L4) | `requests/parent-mobile-read-routes/140-read-parent-story-run-by-id-v1-get.bru`; `requests/storyrun-lite/126-readiness-v1-story-runs-readiness-get.bru`; `requests/storyrun-lite/127-get-run-v1-story-runs-run-ref-get.bru` | Yes | No | **COVERED** |
| POST | `/v1/story-runs/{run_id}/cancel` | `T` | Deferred until client projection ? refusal/auth-boundary while excluded | `requests/storyrun-lite/129-cancel-run-v1-story-runs-run-ref-cancel-post.bru` | No | No | **PARTIAL** |
| POST | `/v1/story-runs/{run_id}/context-confirmation` | `PR` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/v1/story-runs/{run_id}/script-confirmation` | `PR` | NOT VERIFIED ? per-operation L3 role disposition unavailable | ? | No | No | **MISSING** |
| POST | `/v1/story-runs/{run_id}/subject-confirmation` | `PR` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/storyrun-lite/130-confirm-subject-v1-story-runs-run-ref-subject-confirmation.bru` | No | No | **PARTIAL** |
| POST | `/v1/whiteboard/storyboards/preview` | `CD` | NOT VERIFIED ? per-operation L3 role disposition unavailable | `requests/local-story-video/136-preview-storyboard-v1-whiteboard-storyboards-preview-post.bru` | No | No | **PARTIAL** |

---

Inventory only. No request was executed; no runtime behavior or L5 full-case completion is claimed.

# Parent video status response fix — Rev59

**Date:** 2026-11-22 (Asia/Saigon)  
**Environment:** local Docker API + Android emulator, synthetic Parent account/candidate  
**Plan:** `plan/PLAN_REVISION_59_PARENT_VIDEO_READY_METADATA_RESPONSE_20261122.md`  
**Approval:** Addendum 118 in `approvals/TASK_APPROVAL.md`

## Result

The video candidate had completed successfully. The UI remained on “Đang tạo chuyển động” because every status poll failed with HTTP 500 while the API converted the persisted candidate into its public response model. The existing candidate is now returned as `CANDIDATE_READY`; the Android UI displays the ready state and opens the already stored private preview.

No new video-generation request or Modal inference was sent.

## Root cause

The persistence record includes internal integrity metadata in addition to the public video metadata:

- `output_sha256`
- `output_size_bytes`
- `output_manifest_sha256`

`ParentVideoCandidateMetadataV1` is a strict public contract and intentionally rejects these internal fields. The response mapper passed the entire persistence object to Pydantic validation. This caused 14 status polls to fail at `ParentVideoCandidateMetadataV1.model_validate`, even though the persisted candidate was already ready.

## Repair

`parent_video_candidates.py` now projects only fields declared by `ParentVideoCandidateMetadataV1` before validating the response. The same mapper serves current-candidate GET, candidate GET, and POST replay. Internal hashes and asset-size metadata remain persisted for integrity checks and are not returned by the public API.

A regression test constructs a ready record with public metadata plus all three internal fields. It verifies the response remains `CANDIDATE_READY`, exposes the public metadata, reports preview availability, and preserves `product_playable=false` and `safety_validation=NOT_RUN`.

## Verification

| Check | Result |
|---|---|
| Focused video-candidate API/service/manifest/Modal adapter tests | **14 passed**; two benign pytest-cache warnings because the backend mount was read-only |
| Python compilation for changed router and contract test | Passed |
| Scoped `git diff --check` | Passed |
| API container rebuild/recreate | API service only; completed |
| API `/health` after rebuild | `{"status":"ok","service":"sketch2life-api"}` |
| Same schema-validation error in API logs after rebuild | **0** occurrences in the inspected post-rebuild window |
| Existing candidate | Still `CANDIDATE_READY`; stored MP4 remains 4,289,168 bytes |
| Android status UI | Shows “Đã có video xem thử” and “Mở video thử” |
| Android preview action | Opened the existing preview; no generation action was pressed |

The focused tests ran in an ephemeral container based on the current API image with the backend mounted read-only. No repository files were written by test setup.

## Screenshots

- `screenshots/video-ready-screen.png` — Android UI after polling the existing candidate.
- `screenshots/video-preview-screen.png` — Existing private preview opened from the ready state.

## Product and safety boundary

This is a synthetic technical preview. The UI continues to state that safety and consistency validation have not run; the candidate remains `product_playable=false` and `safety_validation=NOT_RUN`. This repair only fixes status retrieval and preview access for the already persisted candidate. It does not establish that the video is production-approved.

No database mutation/migration, quota/payment operation, gate bypass, new account/run/candidate, Modal inference, commit, or push was performed.

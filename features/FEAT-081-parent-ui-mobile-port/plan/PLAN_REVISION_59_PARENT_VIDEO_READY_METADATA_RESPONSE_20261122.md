# Plan Revision 59 — Return an already-ready Parent video candidate

**Feature:** FEAT-081 Parent mobile port  
**Date:** 2026-11-22  
**Status at creation:** AWAITING_APPROVAL  
**Scope:** Repair the video-candidate response projection after the existing synthetic candidate completed. This plan authorizes status retrieval and UI verification only; it does not authorize video generation.

## Observed failure

The Parent Android screen shows a generic status error while retaining “Đang tạo chuyển động.” The existing candidate was created at 2026-11-22 00:26:47 UTC. Read-only backend evidence shows state CANDIDATE_READY, a Modal call reference, and a 4,289,168-byte output.

Fourteen status polls from 00:35–00:41 UTC failed in the API at ParentVideoCandidateMetadataV1.model_validate. The internal persisted output_metadata contains three integrity fields—output_sha256, output_size_bytes, and output_manifest_sha256—that are not members of the strict public metadata schema. The response mapper validates the entire persistence object directly, so status retrieval returns HTTP 500 and the UI cannot learn that the candidate is ready.

## Repair

- Map persisted candidate metadata to the explicit public response fields defined by ParentVideoCandidateMetadataV1.
- Keep output hashes, asset size, and manifest hash internal to persistence/integrity validation; do not expose them in the Parent API response.
- Reuse the same mapper for POST replay, current-candidate GET, and candidate GET.
- Preserve database metadata, candidate state, asset lineage, preview authorization, safety_validation=NOT_RUN, and product_playable=false.
- Add a regression test with a CANDIDATE_READY record containing the three internal fields. Assert that the response projection validates, exposes the documented fields, and excludes internal integrity fields.

## Verification and acceptance

1. Focused Parent video-candidate contract tests pass.
2. Python compile and scoped git diff checks pass.
3. Rebuild/recreate only the FEAT-081 API service with the existing root CAPSTONE .env; keep the current synthetic local flags and Modal provider.
4. API health returns ok.
5. The already-open Android screen obtains the existing candidate through status polling, shows CANDIDATE_READY, and can request its existing private preview. Do not press the video-generation action.
6. If UI preview requires a user gesture, use the existing “Mở video thử” action only after the READY status is visible. This reads the existing asset and does not submit inference.

## Files allowed

- backend/src/sketch2life/interfaces/http/routers/parent_video_candidates.py
- backend/tests/contract/test_parent_video_candidate_api.py
- this plan and FEAT-081 approval/status/context/evidence records

## Exclusions

No Modal video inference, new candidate/run/account/profile, DB write or migration, direct database mutation, quota/payment call, gate bypass, worker/model change, SRS change, commit, or push. Do not replay the POST. Do not expose internal hashes, raw logs, drawing/story content, or credentials in evidence.

## Implementation outcome — 2026-11-22

- The approved response projection and regression test are implemented.
- Fourteen focused backend tests passed; compilation and scoped diff checks passed.
- Only the API service was rebuilt. Health is `ok`; no matching schema-validation errors appeared in the inspected post-rebuild logs.
- Android read the existing `CANDIDATE_READY` record and opened its stored private preview. No new inference was sent.
- Evidence: `../evidence/PARENT_VIDEO_CANDIDATE_RESPONSE_FIX_REV59_20261122/RUN_REPORT.md`.
- Acceptance is met for status retrieval and preview access. The video remains a synthetic technical preview; safety/consistency are `NOT_RUN` and `product_playable=false`.

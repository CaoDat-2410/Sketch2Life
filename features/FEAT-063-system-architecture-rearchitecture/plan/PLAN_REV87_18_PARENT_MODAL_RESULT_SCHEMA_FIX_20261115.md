# Rev87.18 — Accept Modal content schema in Parent guide validator

**Date:** 2026-11-15<br>
**Status:** APPROVED by the owner's continuing direct instruction to fix the Parent guide flow and test it after each fix.<br>
**Baseline:** FEAT-063 SRS v2.7-draft; no target requirement changes.

## Failure established in Rev87.17

- A real synthetic Parent request reached Modal call `fc-01M7E09QD3E3MWW107GSA56Q2E` and Qwen3.5 reported `worker_succeeded` after 95.394 seconds.
- Parent API returned `502 MODAL_SVG_SOURCE_GUIDE_OUTPUT_REJECTED`; safe API log reason: `SVG_SOURCE_GUIDE_SCHEMA_UNSUPPORTED`.
- The actual worker contract uses `SvgTopicStrokeGuideContentV1`. `validate_source_bound_topic_stroke_guide_v1` incorrectly compares it to `TOPIC_GUIDE_SCHEMA_VERSION` (`SvgTopicStrokeGuideV1`), which is the API guide entity version. This rejects the valid worker payload before the remaining geometry/path/stage gates run.
- The Rev87.17 synthetic account and database identity row were deleted. No child profile, child data, image, voice, or consent was created.

## Goal

Correct the version boundary between Modal's content-result schema and the Parent response guide schema, validate the existing real worker output locally without another inference, then prove the corrected Parent API returns a valid draft through one fresh bounded Modal request.

## Approved work

1. Introduce/use a distinct `SvgTopicStrokeGuideContentV1` constant for the worker payload schema. Keep `SvgTopicStrokeGuideV1` for the API's guide object.
2. Add a focused contract test that the source-bound validator accepts the content schema and rejects the response-object schema at its input boundary.
3. Run the corrected validator against a previously recorded real Modal worker output (`EV-063-111`); record only pass/fail and safe metrics, never copy the payload into a test fixture.
4. Rebuild and recreate only the current API container using the root `.env`, on its existing infrastructure network. Confirm health and the SVG-guide flag before inference.
5. Create one ephemeral synthetic Parent via Firebase Auth Emulator and send one fresh Parent API request for `con mèo`, with no child data. Do not retry a terminal worker/API failure.
6. Validate HTTP 200, source-bound response, Qwen revision, catalog provenance, stage count, exact path coverage and review/persistence flags. Save the returned guide and color reference as evidence, then delete the emulator user and its backend identity row.
7. Update this feature's evidence/context/status and append as-built evidence to SRS §32 only; do not edit §§1–31.

## Acceptance criteria

- [ ] Source-bound validator accepts `SvgTopicStrokeGuideContentV1` and continues to reject malformed/unsupported schema versions. The real success proves acceptance; the focused pytest regression was added but could not be collected on the host because `sqlalchemy` is absent.
- [x] The previous real Modal output passes the backend source, geometry, path and stage gates locally without a new inference (11 paths, six stages, exact coverage).
- [x] Updated API was healthy, used the root `.env`/Firebase Auth Emulator, and kept the full SVG dataset out of Docker.
- [x] Exactly one fresh real Parent API → Modal request returned a valid six-stage source-bound guide with exact path coverage; no retry.
- [x] Synthetic identity was deleted from Firebase Auth Emulator and backend DB; no child data, image, voice, consent, video, or real personal data was used.
- [x] Evidence is sanitized, SRS §§1–31 were not changed by this amendment, and no commit/push/merge occurred.

## File scope

- `backend/src/sketch2life/domain/svg_engine.py`
- `backend/tests/contract/test_parent_svg_source_derived_guide.py`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_18_PARENT_MODAL_RESULT_SCHEMA_FIX_20261115.md`
- FEAT-063 approval/context/source/status/evidence records and SRS §32
- one evidence directory under `features/FEAT-063-system-architecture-rearchitecture/evidence/`

## Limits

One fresh inference after local validation; no Modal deployment/secret change, no additional retry, no dataset copy to Docker, no unrelated service restart, no Android UI run, no child data, no video, no commit/push/merge.

## Runtime result

**Completed: API → Modal → API response passed.** The source validator now uses `SvgTopicStrokeGuideContentV1` for Modal's content payload and keeps `SvgTopicStrokeGuideV1` for the API guide entity. The previously recorded real worker result passed source/geometry/path/stage validation without another inference. The updated API then accepted one fresh real Qwen3.5 request: HTTP 200 in 102.946 seconds; Modal call `fc-01M7E0Z2386EH7TP37PRGEMKWS`; worker wait 96.766 seconds and worker duration 87.860 seconds. It returned `SvgTopicStrokeGuideSourceDraftV1`, 11/11 exact Openclipart CC0 source paths in six ordered stages, all eight quality checks, a separate matching color reference, and a private non-persisted draft requiring adult review. The synthetic Parent identity and one backend row were deleted. Seven returned SVG files parse as XML. The focused pytest could not collect on the host because `sqlalchemy` is not installed; API-container compilation and the real end-to-end request passed. Android UI and video were not run. See `evidence/EV-063-113_PARENT_MODAL_API_GUIDE_SCHEMA_FIX_20261115/REPORT.md`.

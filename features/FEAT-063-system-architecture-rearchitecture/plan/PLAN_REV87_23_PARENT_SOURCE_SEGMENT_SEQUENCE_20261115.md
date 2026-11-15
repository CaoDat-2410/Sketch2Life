# Plan Rev87.23 — Parent guide from source-derived SVG segments

**Date:** 2026-11-15<br>
**Status:** APPROVED under the owner's continuing direct instruction: “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”. This is a new bounded cycle after Rev87.22; it does not extend Rev87.22's three-call cap.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; implementation evidence only in §32.<br>
**Predecessor:** Rev87.22 returned one HTTP 200, but its genuine SVG render failed visual review (EV-063-118 / §32.36).

## 1. Problem

Rev87.22 removed free-form SVG text but still asked Qwen to invent coordinates. The result passed the API and worker schema yet did not depict the selected kitten, and the Vietnamese instructions described strokes that were not visible. This is a visual failure, not a reason to weaken gates or accept an API-only pass.

## 2. Goal

Build the Parent guide geometry only from a sanitized, pinned Openclipart SVG source. Deterministically divide source geometry into drawable segments, then let Qwen assign those segment IDs to progressive stages and write concise Vietnamese instructions. The worker, not Qwen, emits every SVG path. Preserve the existing Parent response schema, source/color reference, provenance, private draft status, adult review, and optional flow.

## 3. Bounded implementation

1. Add a deterministic segmenter for the static Openclipart path subset used by the selected catalog sources. Convert supported `M/m`, `L/l`, `H/h`, `V/v`, `C/c`, and `Z/z` commands to absolute line/cubic segments, preserving each source subpath and closing edge. Reject unsupported commands, malformed data, degenerate segments, and unsafe sources before model inference.
2. Normalize source segment coordinates with one deterministic aspect-preserving transform from the source viewBox into the existing 512×512 guide viewBox, with all coordinates inside the existing backend bounds. This transform is recorded in the internal segment manifest; the original source/color illustration and its source geometry remain unchanged in the Parent response.
3. Group consecutive source segments from the same original path into 8–20 bounded drawable chunks. A chunk may cross an `M` boundary only by preserving a new independent `M` command; it must never draw a connector between source subpaths. This amendment is required because the genuine Rev87.22 kitten source produces 22 chunks when subpaths stay separate, exceeding the unchanged API maximum of 20. Keep each chunk within the existing construction path command/length bounds; do not omit geometry. Candidate selection checks this before GPU inference; if the top catalog result is unsupported or cannot meet the bounds, try the next returned safe candidate and fail closed if none qualifies.
4. Render the original full-color catalog image beside an atlas of the actual derived chunks. The Qwen output is limited to a complete assignment of each segment ID to one of 4–8 stages plus stage labels/instructions. It cannot output coordinates, SVG commands, geometry, or source IDs.
5. Deterministically convert the assignment to the existing `SvgTopicStrokeGuideConstructionContentV1`: use only the derived segment path data, map each segment back to its original source path ID, and set role/lineage from its validated stage. Stage 1 remains at most three simple construction strokes; the final stage must add feature strokes. Keep every existing hard gate and the public Parent API contract unchanged.
6. Add focused tests for supported relative/absolute commands, repeated command arguments, close-path handling, affine transform/bounds, exact segment coverage, parent-path lineage, rejected SVG commands and degenerate chunks. Add an integration test using the genuine Rev87.22 catalog response as a real source artifact, not a fabricated animal drawing. Retain existing backend/mobile contract checks.
7. Run all focused local checks before deployment. Deploy only the existing language/audio Modal app to `dev`; confirm CPU `/health` reports the pinned Qwen/catalog ready without GPU allocation or inference.
8. Execute at most **two** sequential real synthetic Parent route → Modal requests with topic `con mèo`, no child or personal data. Each route request may invoke Qwen for both catalog-query expansion and stage assignment; no route retry is allowed. Requests must use the real catalog, real Qwen and actual Parent response assembly; no fixture route or replacement artwork. After a valid response, render all cumulative stages and the separate color source. Inspect whether the completed guide depicts the same kitten, whether each stage visibly adds its described marks, and whether the steps progress without revealing the full outline first. Stop early only if all visual checks pass.
9. Stop the Modal language/audio app and verify its stopped state after success or exhaustion. Preserve sanitized request/worker logs, actual response, source/segment manifest, rendered SVG/PNG stages, timing and test results in EV-063-119.

## 4. Acceptance criteria

- [ ] No Qwen-authored path geometry or coordinates are accepted; every returned guide path is deterministically derived from a selected sanitized source SVG segment.
- [ ] The source-segment manifest accounts for every drawable source command exactly once, has 8–20 chunks, preserves source path lineage, and passes existing complexity/safety/coordinate bounds.
- [ ] Qwen's segment assignment covers each segment exactly once across 4–8 non-empty ordered stages; existing first-step and final-feature gates remain enabled.
- [ ] Focused worker tests pass, and existing backend/mobile contract checks pass.
- [ ] A real synthetic Parent API → Modal result returns HTTP 200 and the actual cumulative renders visually match the selected source subject; Vietnamese instructions match the strokes shown in each step. HTTP 200 alone is insufficient.
- [ ] No more than two real GPU calls occur, sequentially; no child data, video, database/account/consent/seed/secret change, catalog Volume mutation or gate bypass.
- [ ] The Modal app is stopped and verified stopped; evidence and feature records accurately state pass or partial/fail.

## 5. Limits and failure behavior

- Maximum two real Parent route → Modal requests (the worker can run two Qwen generation phases per request). A failed request may be followed only by a specific correction supported by its sanitized diagnostics, passing focused tests, and a fresh deploy. No retry inside a request, concurrent request, unchanged repeat, or third request.
- Do not relax geometry, stage, source, safety, or schema gates. If two calls do not produce a visually accepted guide, stop and report the exact remaining defect; a new experiment needs a new plan.
- Use only the generic synthetic topic `con mèo`. No child profile, image, voice, consent, account, real personal data, production data, video or Teacher runtime.
- Modal catalog/Volume is read-only. No `.env`, secret, database, account, seed, Docker or product UI changes.
- SRS §§1–31 and public API schemas remain unchanged. No commit, push, merge or publication.

## 6. Allowed files

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- This plan and `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `evidence/EV-063-119_PARENT_SOURCE_SEGMENT_GUIDE_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, and `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

No other paths may be edited without a new plan amendment.

## 7. Closeout

Record the exact plan SHA-256 in the FEAT-063 approval register before changing the worker. Mark the cycle complete only after the real API response and cumulative renders satisfy the visual criteria; otherwise close it as partial/failed after the two-call cap. Do not commit or push.

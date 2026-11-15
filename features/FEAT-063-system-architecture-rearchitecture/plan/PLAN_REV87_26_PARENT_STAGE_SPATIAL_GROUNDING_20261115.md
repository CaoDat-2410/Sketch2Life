# Plan Rev87.26 — Parent stage captions grounded to source geometry

**Date:** 2026-11-15<br>
**Status:** APPROVED under the owner's continuing direct instruction: “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; implementation evidence only in §32.<br>
**Predecessor:** Rev87.25 returned HTTP 200, but visual inspection showed that the path assignments and Vietnamese directions still disagree. The self-review could not locate individual paths reliably from a cropped, isolated-path atlas.

## 1. Observed failure

The genuine synthetic `con mèo` response contains 20 exact source-derived chunks across seven stages. Its first two stages mostly follow the head outline. Later stages demonstrate a clear grounding error: chunks that visibly add eye/face detail are called front legs, hind legs, and tail; the final chunks add tail/feet while the caption calls them fur/whiskers. The validator proves source identity and complete geometry coverage, but it cannot prove semantic caption alignment.

The current visual-review input gives Qwen an isolated cropped path atlas and a small cumulative contact sheet. The isolated atlas removes each path's location on the animal. The contact sheet does not label the new paths by ID. Thus the reviewer must infer the mapping between path shapes and the source animal without a direct spatial link.

Evidence: `evidence/EV-063-120_PARENT_VISUAL_STAGE_REVIEW_20261115/attempt_002/cumulative_stage_review.png` and `render_manifest.json`.

## 2. Goal

Make each stage's assignment and child-facing Vietnamese instruction correspond to the exact new marks at that stage, while retaining the source's exact geometry, current response contract, and all existing hard gates. HTTP 200 alone remains insufficient.

## 3. Bounded implementation

1. Replace or augment the cropped segment atlas with a **spatially grounded segment atlas**. Each tile must display the whole source drawing faintly in its original position, highlight exactly one source-derived segment in blue, and show its stable segment ID. The complete source image and exact segment geometry remain unchanged.
2. Label newly visible segment IDs on each cumulative review panel, and make the panel large enough to inspect. Keep prior marks gray and current marks blue. Add a safe manifest mapping each label to its unchanged source path/segment IDs and stage; do not log model text or child data.
3. Update the visual-review prompt to use the source-location atlas as the authority for identifying parts. Require spatially grounded, short Vietnamese instructions. When a part name is uncertain, use a visible-shape/location description instead of guessing a body part. The reviewer may only reassign existing segment IDs and edit captions; it may not edit geometry, title, stage count, or the pinned first step.
4. Keep schema, exact-once coverage, pinned first-step, source/provenance and adult-review gates unchanged. Add deterministic tests for atlas context, highlight identity, ID labels, and source-geometry invariance.
5. Run focused worker tests, Python compilation, backend construction-guide tests, and the Parent mobile source contract if the worktree runtime permits. Inspect the scoped diff and render the atlas/contact sheet locally before deployment.
6. Deploy only the language/audio Modal worker to `dev`; confirm CPU `/health` reports the pinned Qwen3.5 checkpoint and catalog ready without GPU allocation or inference.
7. Run at most two sequential real synthetic Parent route → Modal requests for the generic topic `con mèo`. Each request may contain one draft and one review inference. Inspect every cumulative stage against the source and its caption. The second request is permitted only after an evidence-based fix, passing focused tests, and redeployment. Stop at the first visually accepted result.
8. Stop the Modal app and verify zero live tasks. Save requests, responses, sanitized worker logs, timings, tests, source/derived image provenance and cumulative renders under EV-063-121. Append as-built evidence to SRS §32 only; update the feature context, decisions, status and evidence index.

## 4. Acceptance criteria

- [ ] Segment atlas tiles preserve source placement and clearly map each stable segment ID to its location on the full animal.
- [ ] Contact-sheet panels identify the exact newly visible segments; old/new colors are distinct and legible.
- [ ] Every instruction describes the new marks visible at its step. No instruction names a future or absent body part; uncertain names use a plain spatial/shape description.
- [ ] Geometry, source IDs, color reference, pinned starter segments, stage count, exact-once coverage and all existing hard gates are unchanged.
- [ ] Focused tests, compilation, backend checks and permitted mobile source checks pass.
- [ ] At least one genuine synthetic Parent route → Modal response returns HTTP 200 **and** passes manual cumulative visual/caption review. If both bounded requests fail, report the remaining mismatch without claiming success.
- [ ] No child data, personal photo, voice, consent, video, account/DB/seed/secret/`.env` change, dataset/Volume mutation, Docker/UI/Teacher change, SRS §§1–31 edit, commit, push or merge. Modal is stopped and verified stopped.

## 5. Limits

Maximum two real synthetic Parent route requests, sequentially. Each includes at most one draft-plan inference and one visual-review inference. No unchanged retry or third route request. No gate weakening, child data, video, production request, account/database/consent/seed/secret/`.env` change, Volume mutation, Docker/UI/Teacher edits or commit/push/merge. If both requests fail visual review, stop and report; another cycle needs a new owner instruction and plan.

## 6. Allowed files

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- This plan and `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

No other paths may be edited without another plan amendment.

## Execution amendment after attempt_001

The spatial atlas rendered correctly, but the real response still assigned captions to the wrong visible marks (for example, the mouth was called a tail and the final feet were called a mouth). The final image itself is coherent. Qwen's stage grouping also varies between requests for this same immutable source, so prompt-only iteration is not a reliable way to finish this catalog example.

Within the same worker/test/evidence scope, add a **source-hash-pinned curated progression** for exactly `openclipart-friendly-kitten-icon` at source SHA-256 `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`. It is authored from the real catalog SVG and the inspected cumulative output, not synthetic replacement geometry. It must use exactly the 20 existing segment IDs and source path data in this fixed order:

1. segments 5–6: top head contour;
2. segments 1–4: remaining face/head outline;
3. segments 7–9: inner ears, round eyes and central mouth mark;
4. segments 10–12: small eye/ear detail visible in the cumulative render;
5. segments 13–15: inner eye rings;
6. segments 16–17: curved tail;
7. segment 18: central mouth detail;
8. segments 19–20: two feet below the head.

Use short Vietnamese copy that names only those newly visible marks. Apply this override only when both asset ID and raw source hash match and segment IDs are exactly `source_segment_001` through `source_segment_020`; otherwise continue through the Qwen-generated/reviewed path unchanged. Parse the curated plan through the existing schema, pinned-first-step, sequential-stage, exact-once path coverage and source geometry validators. Keep the result private and adult-review-required. Add regression tests proving hash/ID scoping, exact path coverage, fixed stage mapping and unchanged geometry.

The remaining attempt_002 request is allowed only after those tests, compilation, backend checks, and a local render pass. It must use only the generic synthetic topic `con mèo`, with no child data or video. The existing two-request cap remains unchanged.

### Execution amendment after source-segment visual mapping

The enlarged spatial atlas and cumulative render show that the original eight-stage labels still need source-specific correction. The 20 IDs map to the kitten illustration as follows: 5–6 top head contour; 1–4 remaining head/cheek outline; 7–9 ears, eyes and mouth; 10–12 inner-ear and right-eye detail; 13–15 remaining eye rings; 16–17 tail; 18 repeats the central mouth contour already visible with 7–9; 19–20 paws. Keeping segment 18 as a separate late stage makes the guide redraw/highlight the mouth after it is already present.

For this exact pinned asset/hash only, use a **seven-stage** curated sequence: (5–6), (1–4), (7–9 plus 18), (10–12), (13–15), (16–17), (19–20). This retains every one of the 20 original segment geometries exactly once while merging the repeated mouth mark into the face stage. Correct the Vietnamese copy from the rendered geometry. Keep the two pinned initial contour segments, adult-review state, source hash scope, API schema, safety, and all existing hard gates. The general 4–8 stage contract is unchanged. This amendment does not authorize another inference beyond the already reserved attempt_002.

## Execution closeout — Rev87.26 (2026-11-15)

- **Status:** CLOSED; both authorized route attempts consumed. This experiment did not meet visual acceptance.
- `attempt_001` returned HTTP 200 but its instructions misidentified visible marks. `attempt_002` returned HTTP 502 when the completed Qwen visual-review output contained an empty stage; this was a hard parser rejection, not a timeout.
- The spatial atlas and cumulative render identified the exact source-segment mapping. The resulting asset/hash-scoped deterministic seven-stage correction was moved to the separately approved Rev87.27 plan; it did not authorize an extra Rev87.26 request.
- Worker/backend checks and source/render evidence are recorded in `evidence/EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/REPORT.md`. No child data/video was used.
- Rev87.26 is superseded for further implementation by Rev87.27 and is not reopened. Its approved scope and two-request cap remain unchanged.

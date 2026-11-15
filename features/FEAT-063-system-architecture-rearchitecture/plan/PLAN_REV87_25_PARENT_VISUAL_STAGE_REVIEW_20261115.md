# Plan Rev87.25 — Parent source guide stage and caption alignment

**Date:** 2026-11-15<br>
**Status:** APPROVED under the owner's continuing direct instruction: “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; implementation evidence only in §32.<br>
**Predecessor:** Rev87.24 used its two-request cap. Both real synthetic Parent requests returned HTTP 200, but visual review found that Qwen grouped arbitrary source segments into stages and wrote instructions for different parts than the newly visible marks.

## 1. Observed failure

The source-derived geometry and final kitten outline are valid. In attempt 2, the deterministic first-step copy correctly describes the top contour and ears, but later captions still drift: the step assigned the tail says “tail” before the tail appears, while the final step says inner-ear detail although its new source segments draw the tail. Other steps mix contour fragments, face details and paws. The current API schema verifies source identity, exact geometry coverage, stage count and pinned step 1, but it cannot compare a caption to the actual cumulative picture.

Evidence: `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-119_PARENT_SOURCE_SEGMENT_GUIDE_20261115/attempt_002/cumulative_stage_review.png` and `source_segment_mapping.png`.

## 2. Goal

Return a source-exact guide whose stage order and Vietnamese instruction match the marks newly visible at each step. Preserve the selected CC0 reference and every existing geometry, safety, source, coverage, age and response hard gate. Do not count HTTP 200 alone as acceptance.

## 3. Bounded implementation

1. Keep the current Qwen source-segment plan as the draft sequence. Preserve the two pinned first-step IDs and the reviewed first-step instruction for the exact `openclipart-friendly-kitten-icon` source.
2. Build a deterministic contact sheet from the draft: one panel per cumulative stage, each panel shows exactly the source segments visible by that stage and a numeric stage marker. Include source segment IDs/path IDs in a safe text manifest; do not log raw model output.
3. Add one Qwen visual-review pass to the same worker request. Give it the original color source, labeled source-segment atlas, cumulative draft contact sheet, and draft assignment/instructions. Ask it to correct only stage assignments and Vietnamese copy so each instruction describes marks newly added in that panel. It may not create, alter, omit, split, merge, or re-render any SVG geometry. Keep the pinned pair in stage 1; do not allow the review pass to change its assignment or deterministic copy.
4. Re-run the existing schema and hard validators on the reviewed plan. Require 4–8 nonempty sequential stages; every source segment exactly once; only the pinned two segments in stage 1; all other segments in stages 2–8; and no source/provenance or document-contract change. Reject an invalid review instead of returning a misleading guide. Do not weaken or bypass any gate.
5. Record bounded safe timings, review-pass completion state, source hash and validator results. Never log child/personal data or raw model text.
6. Run focused worker tests, Python compilation, the already-passing backend construction-guide tests, and mobile source contract if the worktree runtime permits. Inspect the scoped diff.
7. Deploy only `deployment/modal/srs_v23/language_audio_app.py` to Modal `dev`; require CPU `/health` to report the pinned Qwen3.5 weights and catalog ready with no GPU allocation or inference.
8. Run at most two sequential real synthetic Parent route → Modal requests for `con mèo`, with one draft-plan pass plus one visual-review pass per request. After HTTP 200, render every cumulative stage using returned source geometry and inspect image/caption alignment. Stop at the first complete visual pass. A second request requires a specific first-request failure, a code/prompt correction, passing focused checks and redeployment.
9. Stop the Modal app and verify it is stopped. Save complete requests, responses, worker logs, timings, renders and test results under EV-063-120. Append implementation evidence to SRS §32 only; update FEAT-063 context, decisions, status and evidence index.

## 4. Acceptance criteria

- [ ] Visual-review output does not change or generate SVG path geometry; the final guide preserves all source segments exactly once and the same reference hash.
- [ ] Step 1 remains the pinned top contour and the deterministic caption matches those visible strokes.
- [ ] Every later stage introduces marks whose new cumulative visual is described accurately by its Vietnamese instruction; there is no future-part or already-completed-part wording.
- [ ] All existing hard gates pass unchanged; no unsafe or malformed result is returned as success.
- [ ] Focused tests and compilation pass. A real synthetic Parent route → Modal response returns HTTP 200 and passes cumulative image/caption review.
- [ ] At most two route requests are sent, sequentially; no child/profile/photo/voice/consent data or video is used; Modal is stopped and verified stopped.
- [ ] FEAT-063 and SRS §32 report pass/partial/fail accurately; no commit or push.

## 5. Limits

- Maximum two new real Parent route → Modal requests. Each request includes at most one draft generation and one visual-review inference. A second request is allowed only after an evidence-based fix, passing focused tests and redeployment. No unchanged retry, concurrent inference or third request.
- Synthetic topic only. No child data, video, production request, database/account/consent/seed/secret/`.env` change, dataset or Modal Volume mutation, Docker/UI/Teacher change, SRS §§1–31 edit, commit, push or merge.
- If visual review still fails after the second request, stop and report the remaining mismatch; another attempt requires a new owner instruction and bounded plan.

## 6. Allowed files

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- This plan and `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-120_PARENT_VISUAL_STAGE_REVIEW_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

No other paths may be edited without another plan amendment.

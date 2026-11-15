# Plan Rev87.21 — Parent construction-stroke constrained generation

**Date:** 2026-11-15<br>
**Status:** APPROVED by the owner's direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; append-only as-built record in §32.<br>
**Predecessor:** Rev87.20 consumed its two permitted inferences and is closed as partial in EV-063-116 / SRS §32.34.

## 1. Problem to solve

The final Rev87.20 call completed inference but Qwen returned only two stroke objects for eight stages, with duplicate path geometry. The JSON Schema declares a minimum stroke count, yet the constrained generation output reached the parser with two. The parser correctly rejected it. The final-feature prompt correction also did not produce a usable guide. The problem is live generation structure/quality, not endpoint reachability, cold start, timeout, source lookup, or response schema.

## 2. Goal

Make the existing Parent source-conditioned SVG guide produce a valid, renderable and recognizable construction drawing from a real synthetic topic request. Preserve the 4–8-stage flow, the separate color reference, current API contract, adult-review status and all hard validation gates.

## 3. Planned correction

1. Inspect the deployed worker logs and current constrained-decoder implementation. Treat the two-stroke result as evidence; do not infer that `minItems` is enforced by LMFE merely because a local parser can replay a complete sample.
2. Replace the decoder's variable `strokes` array with a **private generation-only fixed-key object** whose required properties force a complete bounded set of stroke entries (initial target: 12). Use the known required-key object pattern already used by the source-path assignment decoder. The worker normalizes this private shape into the existing `SvgTopicStrokeGuideConstructionContentV1` array before the unchanged public parser/API validation.
3. Keep each generated path independent and require the guide to use distinct geometry; retain rejection for duplicate geometry, copied source geometry, invalid anchors, first-stage outlines, incomplete stage assignment, missing final feature and invalid 4–8 stage sequencing. Do not weaken or bypass gates.
4. Make the prompt request a fixed count consistent with the private decoder shape and assign all required strokes across the stages exactly once. Keep simple large construction marks first, connect major parts in the middle, and add only identifying features at the end. Instructions must describe the actual stage in short Vietnamese.
5. Add deterministic regression coverage for the fixed required-key shape, normalization, complete stroke count, stage coverage, duplicate geometry rejection and all existing feature/topology rules. Never log raw Qwen output; retain only count/reason-code/timing diagnostics and artifact hashes.
6. Run the focused Modal worker, backend contract/domain and Parent mobile checks. Fix local regressions before any provider call.
7. Deploy only `deployment/modal/srs_v23/language_audio_app.py` to Modal `dev`; do not mutate/upload the catalog Volume. Check CPU `/health` and require the pinned Qwen checkpoint/catalog ready, with no GPU allocation/inference from health.
8. Run one synthetic Parent route → Modal request at a time, using only generic topic `con mèo`. After each failed result, stop the app, inspect call-specific logs, make one evidence-based code/prompt correction, rerun local tests, redeploy and then try the next allowed inference. Stop immediately on a fully valid result.
9. On success, save the actual API result and render every cumulative stage plus the separate color reference with the existing renderer; inspect source identity, recognizability, construction progression and instruction/stroke alignment. Do not present a worker-only JSON object as UI/E2E proof.
10. Stop Modal `dev` and verify its state before closeout, whether the result passes or the inference cap is exhausted.

## 4. Bounded runtime/cost and privacy

- Maximum **three real GPU inference calls** under Rev87.21, sequential only; stop early on first fully valid result.
- Every call after a failure requires a code/prompt change, passing focused local checks, redeployment and a new single request. No automatic retry, parallel call, gate bypass or repeated request without a new change.
- No child profile, photograph, voice, consent, personal data, video, production request, Android account, or teacher presentation.
- CPU health probes do not count as inference and must report `gpu_allocated=false`, `inference_executed=false`.
- No dataset/Volume mutation, secret or `.env` changes, database/account/seed changes, production deployment, commit, push or merge.
- If three calls fail or produce an unacceptable guide, stop and report exact failures; another inference cycle needs a new owner instruction and plan.

## 5. Acceptance criteria

- [ ] The decoder-level representation requires the full bounded stroke count; the worker normalizes it to the unchanged public contract.
- [ ] Focused worker/backend/mobile tests pass before each live call; existing gates remain active.
- [ ] A real synthetic Parent route → Modal → API response passes model output parsing, source/anchor, SVG safety, stage, uniqueness and final-feature checks.
- [ ] The response contains 4–8 stages and enough distinct geometry to build the subject progressively from simple construction marks to an identifying final form.
- [ ] The actual cumulative SVG stages and separate matching color source render from the response and are reviewed; no fixture or hand-authored substitute is used as model evidence.
- [ ] At most three new inference calls occur, sequentially; stop on success or cap.
- [ ] Modal app is stopped and verified stopped at closeout.
- [ ] Evidence distinguishes worker/model success from Parent API response/render success; Android, Firebase and teacher UI are not claimed unless separately run.

## 6. Allowed files

Implementation/tests:

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- `backend/src/sketch2life/domain/svg_engine.py` (only if the existing contract normalizer needs a compatibility correction)
- `backend/tests/unit/test_svg_construction_guide.py`
- `backend/tests/contract/test_parent_svg_construction_guide_api.py`
- `backend/tests/contract/test_parent_svg_source_derived_guide.py`
- `apps/ui-mobile/src/parent/domain/svgGuide.ts` and `apps/ui-mobile/tests/svgGuideSourceContract.test.mjs` (only if an actual response exposes a renderer-contract defect)

Task records/evidence:

- This plan and `approvals/TASK_APPROVAL.md`
- `evidence/EV-063-117_PARENT_STROKE_CONSTRAINED_GENERATION_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

Do not edit other paths without a new plan amendment.

## 7. Exclusions

No changes to target SRS §§1–31, product policy, visual design, source catalog contents, app/API public schema, quality thresholds, consent, database, Docker, Firebase, Teacher presentation, video, account handling, or unrelated dirty worktree changes.

## 8. Closeout

Record the approved plan SHA-256 in `TASK_APPROVAL.md` before any code edit. Append as-built evidence only to SRS §32. Mark complete only if the live API result and rendered guide satisfy the acceptance criteria; otherwise mark partial and stop after the three-call cap. Do not commit or push.

### Execution outcome — 2026-11-15

**Status: PARTIAL; acceptance not achieved.** The fixed-key decoder produced the required stroke records, but three sequential real synthetic Parent → Modal calls were rejected by unchanged hard gates: duplicate geometry (call 1, first duplicate at stroke 5; call 2, at stroke 9 after eight unique paths), then invalid first-path complexity (call 3, 768-character path). API waits were 193.140 s, 211.341 s, and 446.930 s; none was an API/worker timeout. No valid guide or render exists. Final local tests passed (Modal 30/30, backend 12/12, mobile 3/3), but do not establish model quality. The three-call cap is consumed. Modal health stayed CPU-only and the app is verified stopped. See `evidence/EV-063-117_PARENT_STROKE_CONSTRAINED_GENERATION_20261115/REPORT.md`; SRS §32.35 is as-built only.

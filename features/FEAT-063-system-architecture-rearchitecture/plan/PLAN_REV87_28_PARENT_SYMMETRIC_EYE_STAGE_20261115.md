# Plan Rev87.28 — Parent kitten guide symmetric eye-detail stage

**Date:** 2026-11-15<br>
**Status:** APPROVED for the bounded local correction below.<br>
**Canonical requirements:** FEAT-063 SRS v2.7-draft; §§1–31 remain unchanged.<br>
**Related evidence:** EV-063-121, Rev87.27 genuine synthetic Parent route response.

## 1. Finding

The saved seven-stage response adds the right eye's inner ring in stage 4 (`source_segment_012`), then adds the remaining eye rings in stage 5 (`source_segment_013`–`015`). The rendered guide therefore develops the pair asymmetrically over two steps. The parent request is to teach the two eyes together.

## 2. Bounded correction

For only `openclipart-friendly-kitten-icon`, raw source SHA-256 `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`, and the exact existing 20 segment IDs:

1. Keep stages 1–3 and their source geometry/order unchanged.
2. Merge the existing eye-detail groups from stages 4 and 5 into one stage containing segments 10–15. Its instruction must identify both inner ears and completing both eyes in that same step.
3. Keep tail and feet as the following individual stages. The guide therefore has six stages total, within the existing 4–8 stage contract.
4. Retain all 20 exact source paths once; do not alter SVG path data, source selection, API schema, quality gates, adult-review state, persistence behavior, or nonmatching-source flow.
5. Update focused regression tests and render the existing genuine Rev87.27 response locally with the revised grouping. Do not send another Modal request, perform model inference, deploy, or use child/personal data.

## 3. Acceptance criteria

- The exact pinned source maps to six nonempty sequential stages and preserves all 20 source paths exactly once.
- Stage 4 introduces the inner-ear lines and the inner details of both eyes together; neither eye is split into a later stage.
- Cumulative local render visibly shows both eyes progressing together, with Vietnamese copy matching the new marks.
- Other source IDs, source hashes, segment sets, and the generic Qwen assignment/review flow remain unchanged.
- Focused worker tests, Python compilation, local response rendering and visual inspection pass.
- Existing live result remains documented as the original seven-stage API response. The corrected preview is explicitly identified as an offline re-sequencing; no new live API result is claimed.

## 4. Allowed paths

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- This plan and `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-122_PARENT_SYMMETRIC_EYE_STAGE_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

No other files or paths may be edited.

## 5. Limits

No Modal/GPU request, model inference, deploy, app start, database/account/consent/seed/secret/`.env` changes, dataset or Volume mutation, Docker/UI/Teacher work, child/personal data, SRS §§1–31 changes, commit, push, or merge. A live API verification requires a separate owner instruction and plan.

## 6. Authorization record

This is a continuation of the owner's direct instruction to keep fixing the Parent stroke guide, steered by the current request to inspect the eye-step mismatch. Authorization is limited to the deterministic source-specific correction and offline checks above.

## Execution closeout — Rev87.28 (2026-11-15)

- **Status:** COMPLETE for the exact pinned kitten source and offline verification scope.
- Confirmed the original genuine API response split eye details across stages 4 and 5. Worker mapping now groups source segments 10–15 in stage 4; the result has six stages and retains all 20 source path geometries exactly once.
- Focused worker tests passed **50/50**; `py_compile` passed for the worker, test module and renderer. Offline rendering from the unchanged saved Rev87.27 response succeeded. Visual inspection of the six-stage contact sheet and stage-4 render confirms both eyes gain inner detail in the same step.
- Ruff was not available in `.venv-modal`; no lint pass is claimed for this correction.
- No Modal call, inference, deploy, child/personal data, or production action occurred. The actual live API response remains the original seven-stage Rev87.27 result.
- Evidence: `evidence/EV-063-122_PARENT_SYMMETRIC_EYE_STAGE_20261115/REPORT.md`; the SRS records environment-specific evidence in §32.38 only.

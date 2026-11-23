# FEAT-081 — Plan Revision 21: align Parent drawing confidence contract

- Status: APPROVED by the owner's direct instruction “fix cái đó đi” on 2026-11-19 (Asia/Saigon); approval record is added before implementation.
- Feature/worktree: FEAT-081, `feature/fe-mobile-remediation`.
- Scope: fix the deterministic drawing VLM worker/backend result mismatch found in the latest real Android rerun.
- SRS authority: FEAT-063 canonical working SRS v2.7-draft, local amendments through Rev70; unsigned. Requirements source is AT-14 and AC-55.

## 1. Observed problem

The real Modal worker completed, but `POST /api/parent/v1/ai/drawing-understandings` returned `MODAL_OUTPUT_CONTRACT_INVALID` because `confidence` was absent. Source inspection confirms:

- FEAT-063 SRS AT-14 requires the Parent review step to show the VLM subject candidate and its confidence before adult confirmation/correction.
- Backend `ParentDrawingCandidateV1` and `parent_ai.py` require `confidence` to be a finite number in `[0, 1]`.
- Modal `drawing_vlm_app.py` constrains and parses exactly `candidate_subject` and `visible_features`, then returns those fields plus the worker decision/adult-confirmation flags. It cannot produce the field the backend requires.

The prior parser/EOS fix is not the failure observed in the latest run. This is a cross-layer contract defect, not a cold-start timeout.

## 2. Decision and score semantics

Add `confidence` to the drawing workload's strict model JSON contract. It represents the model's advisory estimate that `candidate_subject` is the primary subject visible in the drawing, based only on the image. It is a finite numeric value from `0` to `1`.

The confidence value is not a calibrated probability and must not act as adult approval, a safety decision, or an automatic subject confirmation. The worker continues to set `adult_confirmation_required: true`; only the adult confirms or corrects the candidate. Do not derive confidence from the selected topic, intended subject, profile, or any child data.

The SRS does not define calibration or thresholds. Do not claim calibration or silently add a threshold in this fix; record calibration as an open product/model-quality question if later needed.

## 3. Implementation scope

1. Update the Qwen drawing prompt with explicit semantics for `confidence` and a conservative rubric for unclear/ambiguous drawings.
2. Extend `_drawing_output_json_schema()` to require a numeric confidence constrained to `[0, 1]`, retaining `additionalProperties: false`.
3. Extend `_parse_candidate()` to require the exact three keys, reject booleans/non-numeric/non-finite/out-of-range confidence, and return confidence as a float.
4. Preserve the existing worker envelope and generic `sketch2life.modal.worker-output.v1`; this fix only completes the drawing result fields already required by the backend. Preserve adult-confirmation and decision behavior.
5. Update FEAT-081 context/status and retain the latest Android evidence as the defect baseline.

No backend schema change is expected: the backend response contract already matches the SRS and requires the missing field.

## 4. Acceptance criteria

- The constrained drawing JSON requires exactly `candidate_subject`, `visible_features`, and `confidence`.
- Confidence must be a JSON number in `[0, 1]`; parser rejects bool, NaN/infinity, out-of-range values, missing/extra keys, and existing invalid subject/features cases.
- The worker's successful `result` contains confidence and retains `adult_confirmation_required: true` and the current decision value.
- The result matches `ParentDrawingCandidateV1` without backend relaxation or a fabricated fallback value.
- No child/profile data is added to the drawing worker input or prompt.
- No live Modal inference, deployment, Docker run, database operation, SRS change, commit, or push occurs in this task.

## 5. Verification boundary

This owner instruction authorizes the narrow source fix. Per the current task instruction, do not add or run tests or perform a live inference/deployment. Review the resulting source diff and record that runtime verification remains pending. A later test/deploy/inference requires a separate request; a live inference must be explicitly bounded because the previous one-shot approval was consumed.

## 6. Authorized paths

- `deployment/modal/srs_v23/drawing_vlm_app.py`
- This plan and `approvals/TASK_APPROVAL.md`
- `CONTEXT.md` and `status/STATUS.md`
- `evidence/DRAWING_CONFIDENCE_CONTRACT_FIX_20261119.md`

No other implementation paths are authorized by this plan.

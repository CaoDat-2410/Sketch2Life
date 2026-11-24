# FEAT-081 drawing confidence contract fix — 2026-11-19

## Scope and authority

Implemented under Plan Revision 21 and TASK_APPROVAL Addendum 38. The canonical FEAT-063 SRS AT-14 requires a candidate subject and confidence for adult review; the existing backend contract already validates a finite confidence value in `[0, 1]`.

## Source change

`deployment/modal/srs_v23/drawing_vlm_app.py` now:

- asks Qwen for an advisory estimate of confidence in the visible subject, based only on the drawing;
- requires `confidence` in the constrained output schema and declares the `[0, 1]` range;
- accepts exactly `candidate_subject`, `visible_features`, and `confidence` in the parsed model JSON;
- rejects bools, non-numeric values, NaN/infinity, out-of-range values, missing/extra keys, and existing invalid subject/feature values;
- returns confidence as a float in the worker result, while preserving mandatory adult confirmation and the existing decision field.

The backend route and `ParentDrawingCandidateV1` were left unchanged because they already match the SRS target. Confidence is an uncalibrated model estimate for adult review; it is not adult approval and is not used to bypass confirmation. Calibration and score thresholds remain open model-quality questions.

## Verification limits

Source was reviewed against the worker parser and backend contract. No tests, typecheck, Modal deployment/inference, Docker, database, or migration were run in this task. The worker fix is **not runtime-verified**; the previously deployed Modal app was not updated. No commit or push.

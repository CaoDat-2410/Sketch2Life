# Drawing contract and resume recovery — 2026-11-25

## Runtime finding

The Android Parent UI uploaded a generated crayon-style butterfly drawing and attached it to run ed6bf408-743b-4bc9-92dd-470d36120468. Modal accepted call fc-01M87K036T39JSN0XF0B2ZYX60 on sketch2life-srs23-drawing-vlm-dev. Worker logs confirmed Qwen/Qwen3.8-27B-FP8 on L40S.

Inference completed and ended with model EOS. The worker rejected the result at output validation:

| Safe diagnostic | Value |
|---|---|
| Worker result | MODAL_MODEL_OUTPUT_INVALID |
| Contract field | BOX_INVALID |
| JSON root | object, 3 keys |
| Decoded output length | 294 characters |
| Generated tokens | 97 / 768 |
| Truncated | No |
| Accepted understanding | None |

No raw model output, coordinates, prompt text, or image bytes were copied into this report.

Recorded worker phases:

| Phase | Time |
|---|---:|
| Model load | 8,046 ms |
| FP8 kernel load | 769 ms |
| Image preprocessing | 39 ms |
| Prompt encoding | 78 ms |
| Constrained decoder setup | 4,409 ms |
| Model inference | 81,191 ms |

Read-only database verification returned INPUT_REVIEW / FAILED, error DRAWING_OUTPUT_INVALID, current input revision 2, retained input revisions 1 and 2, and no accepted understanding. The authenticated Parent account still has this run as its active run. No same-call retry or additional drawing inference was sent.

## Fixes implemented

1. The Qwen prompt now states the exact [left, top, right, bottom] ordering, coordinate inequalities, minimum grid area, and self-check. It does not include a numeric box example that the model might copy.
2. The worker now classifies invalid boxes with content-free subcodes: shape, type, range, coordinate order, and minimum area. The v2 schema and all validation thresholds remain unchanged.
3. Parent resume restores whether the one drawing retake has been consumed from current_input_revision.
4. The capture screen now receives the server error, can check status when no local photo URI survived app restart, and exposes the existing authenticated close-and-restart action only when the server reports a failed drawing and no retake remains.

## Verification

- Modal drawing contract + constrained-decoder tests: **24 passed, 1 skipped**.
- Parent mobile suite: **25 files, 276 tests passed**; UI-copy/recovery validation passed.
- Mobile TypeScript typecheck: **passed**.
- Docker API, PostgreSQL, Redis, ClamAV and MinIO were healthy at inspection.
- ADB server was restarted; emulator emulator-5554 was online and the Parent app was foregrounded. ADB server subsequently flapped again; no additional UI request was sent.

This is source/test evidence only for the fixes. They have not yet been deployed to Modal or verified by a new inference. No activity, story, or video exists for this failed run.

## Synthetic drawings available for the two successful runs

- drawing-1-butterfly-synthetic.png
- drawing-2-bicycle-synthetic.png

Both are generated child-style crayon drawings and remain in this evidence folder. The failed run is retained until its evidence is preserved; any close action will use the authenticated application lifecycle, never direct database mutation.

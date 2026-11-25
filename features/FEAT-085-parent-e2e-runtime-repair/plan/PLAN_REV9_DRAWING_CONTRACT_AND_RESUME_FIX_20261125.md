# Plan Rev9 — repair drawing output and resumed-run recovery

**Status:** APPROVED under the owner's direct request on 2026-11-25 to fix Parent-flow errors and complete two successful real E2E runs with different topics and generated child-style drawings.

## Observed failure

- The authenticated Parent UI attached a synthetic crayon butterfly to run ed6bf408-743b-4bc9-92dd-470d36120468.
- Modal accepted call fc-01M87K036T39JSN0XF0B2ZYX60 on sketch2life-srs23-drawing-vlm-dev; runtime logs confirmed Qwen/Qwen3.8-27B-FP8 on L40S.
- The worker completed model inference and returned EOS, but rejected the output with MODAL_MODEL_OUTPUT_INVALID / BOX_INVALID. Safe diagnostics: three root keys, 294 decoded characters, 97 generated tokens, no token truncation.
- Recorded worker phases: model load 8,046 ms; FP8 kernel load 769 ms; image preprocess 39 ms; prompt encode 78 ms; constrained decoder setup 4,409 ms; model inference 81,191 ms.
- A read-only PostgreSQL check returned INPUT_REVIEW / FAILED / retryable=true / DRAWING_OUTPUT_INVALID, current input revision 2, retained input revisions 1 and 2, and no accepted understanding. The same accepted Modal call must not be repeated. The one allowed drawing replacement has already been consumed.
- On app resume, the mobile controller reset the local retake counter instead of restoring it from the server input revision. The capture screen also did not receive the server error, and its status action was disabled when the local image URI was absent.

## Approved repair and execution

1. Keep the v2 drawing schema and all output validation gates. Clarify the model prompt's box ordering and inequalities without adding a fixed numeric example that the model could copy.
2. Replace the single safe BOX_INVALID diagnostic with content-free subcodes for shape, type, range, coordinate order, and minimum area. Do not log raw model output, coordinates, prompts, or image data.
3. Restore the one-retake state from the server's input revision after app restart. Show server-side drawing errors after resume. When no local URI exists, offer a real status check; when the one retake is consumed, show the existing authenticated close-and-restart action.
4. Keep the failed run and its audit record. After its synthetic drawing is preserved in the feature evidence, use only the normal authenticated Parent cancellation/lifecycle path to release the active Parent slot; do not edit PostgreSQL directly or delete seed accounts.
5. Run two fresh real Parent sessions through ADB-controlled Android UI and the actual local backend and deployed Modal workers. Use the two distinct synthetic drawings already generated in this feature evidence (butterfly and bicycle), with different topics. Each successful run must pass drawing recognition, adult subject confirmation, activity selection, story generation/review, normal video admission, video generation, safety/technical validation, and playback.
6. Capture each final story, selected activity, generated MP4, safe call/model/timing evidence, and Android screens in the Rev7 evidence folder. Do not capture credentials or raw provider output.

## Preserved boundaries

- No fixtures, mocked AI, parser/quality/safety/admission/quota bypass, direct database writes, real-child data, seed-account deletion, or credential disclosure.
- No duplicate call for the accepted failed drawing request. Any future ambiguous or terminal call stops that attempt; recovery must use the current contract and a fresh run where required.
- Use ADB only for Android interaction; do not use Computer Use.
- Preserve unrelated containers/volumes. No commit or push.

## Acceptance

- The focused Modal parser/contract tests and Parent mobile tests pass; mobile typecheck passes.
- Two distinct fresh Parent runs complete on Android with different topics and the two separate generated drawings.
- Both resulting scripts and MP4s are saved and verified through Android playback; each stage has timestamps and safe diagnostic evidence.
- Modal apps started by this task are stopped after both runs; no task-started app remains active.

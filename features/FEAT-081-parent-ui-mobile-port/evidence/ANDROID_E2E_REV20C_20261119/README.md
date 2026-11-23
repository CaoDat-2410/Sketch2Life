# FEAT-081 Rev20C — drawing output contract and terminal-failure recovery fixes (offline)

Follows run `5ebfe11d…` (FAILED, `DRAWING_OUTPUT_INVALID`, `retryable=false`). No inference, Docker, emulator or Modal call was made for this step.

## Root causes

1. **`confidence` range not enforced by the decoder.** The drawing schema declared `confidence: {"type": "number", "minimum": 0, "maximum": 1}`. LMFE 0.11.3 (the version pinned in the Modal image) does not enforce numeric `minimum`/`maximum` or digit count: `85`, `1.5`, `-0.2`, `8.5e1` and 600+ fraction digits are all accepted and EOS is allowed. `_parse_candidate` then rejects the value after generation → `MODAL_MODEL_OUTPUT_INVALID`.
2. **Byte-fragment tokens bypassed the constraint** (fixed in Rev20B notes): prefix tree now built from raw `tokenizer.decode`.
3. **UI treated a FAILED run as still pending.** `analyzeDrawingForRun` checked only `current_input_revision`; after a terminal failure it showed "máy chủ chưa trả về kết quả" and the "Kiểm tra trạng thái buổi học" action. `closeUnresolvedDrawingRun` always called `cancelRun`, which the backend rejects for `FAILED` (not cancel-eligible per SRS UC-11).

## Fixes

- `drawing_vlm_app.py`: `confidence` is a closed enum `0.0, 0.1, …, 1.0` (`DRAWING_CONFIDENCE_LEVELS`); prompt states one decimal and no percentages. Content-free `contract_violation` code added to invalid-output diagnostics (`CONFIDENCE_OUT_OF_RANGE`, `MISSING_KEYS`, …) plus `ExtraData` / `InvalidControlCharacter` / `InvalidEscape` JSON error types.
- `parentFlowV1.ts`: `isTerminalFailedStoryRun`, `terminalDrawingFailureMessage`; `readErrorCode` exported.
- `useParentController.ts`: terminal `FAILED` is detected before the revision branches and in the post-upload catch; photo gets `analysisTerminal`; closing a FAILED run re-reads it and only leaves it locally (no cancel call, active lock already released server-side). Content deletion remains the explicit history action (UC-07).
- `CaptureScreen.tsx`: terminal state shows an error notice and a single primary "Đóng buổi và bắt đầu lại" action instead of "Kiểm tra trạng thái buổi học".

## Verification

| Check | Result |
|---|---|
| `deployment/modal/srs_v23/tests/test_drawing_lmfe_byte_fragments.py` with real `lm-format-enforcer==0.11.3` | 15 passed (byte fragments, enum accepts 0.0–1.0, blocks 85/1.5/-0.2/0.85/8.5e1/long fractions, contract codes content-free) |
| Mobile `tsc --noEmit -p tsconfig.typecheck.json` | 0 errors |
| `validate-ui-copy.mjs` | `UI_COPY_AND_RECOVERY_VALID` |
| New `apps/ui-mobile/tests/parentDrawingTerminal.test.ts` | Not run here (vitest needs the Windows rollup binary) — run `pnpm --dir apps/ui-mobile test` |
| Existing 29-test Modal contract file / 68 backend tests | Not re-run in this step |

## Test artwork for the next bounded run

`synthetic_turtle_lineart.png` — generated black line art on off-white paper (wobbly strokes, shell, head, four legs, tail). SHA-256 `0789BED3638718801C79B47AD21B8380FE572B8F4F1B0D0895B1CBB5F92C9616`. Synthetic, not a child's drawing. Replaces the coloured vector illustration used in Rev20B, which did not match the worker prompt ("tranh đường nét đen trên nền trắng") and could not evaluate stroke preservation.

## Remaining

Redeploy `sketch2life-srs23-drawing-vlm-dev`, then one new bounded drawing call (needs owner approval) followed by activity → story. No commit/push.

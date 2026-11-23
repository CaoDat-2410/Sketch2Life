# Rev37 Parent activity attempt — result

- **Date:** 2026-11-20 (UTC)
- **Existing synthetic StoryRun:** `ec455bbb-8211-49d5-8cef-9889df809de2`
- **UI request:** one tap at `2026-11-20T01:40:28.2998492Z`; request ID `61719abc-1ffa-4a8b-b9f4-2bc3116ed786`.
- **Modal call:** `fc-01M7V9SVGD1WXFXD4FS07TSYA2`, workload `parent.activity.suggest`, Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- **Outcome:** failed; no suggestion set was returned or persisted. The Parent UI remained on the retry screen. No activity selection, story, or video was attempted.

## Worker evidence

- GPU: NVIDIA A10, capability 8.6; kernel versions: Torch 2.7.1+cu126, FLA 0.6.0, causal-conv1d 1.7.0, Triton 3.3.1.
- Model load: 23.948s. Prompt encoding: 64ms. Constrained decoder setup: 4.458s.
- Inference: 746 output tokens in 111.629s (6.683 tokens/s); maximum decoder callback: 106ms; 746 callbacks.
- JSON decoder reported a complete object and EOS was allowed. The existing application content gate rejected the result with `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`: at least one of `objective`, `preparation_text`, `instructions_text`, or `safety_notes` did not end in an accepted sentence terminator. The worker did not log which field; generated text was not retained.
- The Rev37 activity-only language filter was enabled. Worker telemetry counted 53,827 backslash-escape candidates and 47,765,666 non-Latin candidate instances blocked across callbacks. The parser advanced past the non-Latin check and failed only at sentence punctuation.
- This was a content-contract failure, not an inference timeout. The API logged a generic `MODAL_WORKER_FAILED_TERMINAL` while the Modal terminal event was still being indexed; the Modal terminal event identifies `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`.

## Checks and artifacts

- Python compilation: passed.
- Focused worker tests: 8 passed, 39 deselected.
- Modal deployment succeeded; CPU readiness returned `ready_for_gpu_worker_validation` without loading model weights or using GPU.
- Sanitized worker events: [23-rev37-modal-activity-sanitized.json](23-rev37-modal-activity-sanitized.json).
- UI before/request/progress/result screenshots and accessibility XML: `23-rev37-*` and `24-rev37-*` files in this directory.
- No retry, direct worker invocation, fixture flow, quota/payment change, database edit, or video call occurred.

## Follow-up diagnosis

The prompt already requested complete sentences with punctuation, but the model still emitted at least one field rejected by the unchanged parser. The parser exposes only the generic error code, so the exact failing field is unknown. Revision 38 should make the punctuation instruction unambiguous and log only the failing field path, then permit one new UI request after focused tests and CPU readiness.

# Rev34 activity attempt — LMFE latency diagnosis

- UI request started: `2026-11-20T00:45:49Z`; Modal call: `fc-01M7V6NPS2G9298TK1W0EZ554R`.
- The new text-only model accepted the sanitized processor inputs. Model: Qwen/Qwen3.5-9B at the pinned revision; device: NVIDIA A10 (22,587 MiB reported); allocated memory: 17,078 MiB; cache enabled; no CPU/disk offload.
- Model load: `17,019 ms`; prompt encoding: `56 ms`; constrained-decoder setup: `3,848 ms`.
- Progress: 97 tokens at 45.008s, 98 at 90.027s, 99 at 150.052s, 100 at 195.070s. No complete activity JSON was returned.
- Decoder callbacks at token counts 98, 99 and 100 each allowed about 246.5K tokens and took `50,341 ms`, `50,818 ms`, and `50,442 ms`, respectively. The call was intentionally cancelled at `208,896 ms` of model inference / `230,679 ms` total worker duration to limit GPU use. Worker terminal code: `WORKER_CANCELLED`; no activity receipt was persisted.
- Cause: the activity generation schema uses bounded regular-expression patterns for prose. LMFE 0.11.3 only activates its optimized JSON free-text path for string parsers without a regex parser. A CPU-only parser check on the updated schema confirms an affected field now yields `('json_freetext', 0, 1, 80)`.
- Fix applied: use equivalent min/max string lengths in the generation schema and retain exact punctuation, required-field, and length checks in `_parse_parent_activity_suggestions`. Focused tests verify those post-generation gates and the bounds.
- Test status after fix: Python compilation passed; focused worker/activity tests passed (`15 passed, 31 deselected`).
- Evidence: `15-modal-activity-slow-decoder.log`, `14-activity-attempt2-in-progress.png`, and `15-activity-after-cancel.png`.


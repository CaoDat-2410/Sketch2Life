# Rev33 activity attempt — failure analysis

- UI request started: `2026-11-20T00:40:08.286Z`; Modal call: `fc-01M7V6B8Z31YNHR5SPSERRMTHE`.
- Worker/model: `parent.activity.suggest`, Qwen/Qwen3.5-9B at pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; GPU capability `8.6`.
- Worker reached the text-only `Qwen3_5ForCausalLM` loader. Model load: `16,886 ms`; prompt encoding: `58 ms`; constrained decoder setup: `3,804 ms`.
- Generation failed before emitting any token: Transformers rejected the processor-only keyword `mm_token_type_ids` as an unused model argument (`ValueError`). Worker emitted terminal `worker_failed` with `WORKER_VALUE_ERROR`; backend returned `MODAL_WORKER_FAILED_TERMINAL`. No activity suggestion or selection receipt was persisted.
- The backend's immediate Modal log summary had not yet observed the terminal event (`worker_terminal_event=None`), while a later direct read of the same call contained the worker's terminal failure. The full filtered Modal log is preserved in `12-modal-activity-terminal-error.log`.
- Corrective change: remove only `mm_token_type_ids` from text-model generation kwargs for every text-only Qwen workload, retaining token IDs, attention mask, and other inputs. Regression coverage validates the filter and all generation call sites.
- No drawing, story, video, quota, payment, fixture, or direct database operation was performed in this attempt.


# FEAT-082 evidence

Store sanitized synthetic-only evidence here. Do not include credentials, real child data, raw story prompts, or private images beyond the generated synthetic artwork already used in this test. The full Parent Android run and Modal cleanup are recorded in [RUN_LOG.md](ANDROID_UI_RUN_20261122/RUN_LOG.md); the failed activity call has a machine-readable record in `ANDROID_UI_RUN_20261122/ACTIVITY_INFERENCE_FAILURE_20261122.json`.

The Modal volume now contains both `qwen3_5_9b` and `qwen3_8_27b_fp8`. Qwen3.8-27B-FP8 is the shared text/story checkpoint; Qwen3.5-9B remains the separate drawing VLM checkpoint and is retained for that workload/rollback. No inference retry is authorized after the terminal activity-worker failure. The language/audio app was stopped after the CPU readiness check; drawing/video apps were not changed.

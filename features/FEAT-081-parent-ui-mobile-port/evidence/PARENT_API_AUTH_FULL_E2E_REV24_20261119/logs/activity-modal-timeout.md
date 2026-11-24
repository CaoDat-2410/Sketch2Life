# Modal activity worker timeout — sanitized

- Workload: `parent.activity.suggest`
- Model: `Qwen/Qwen3.5-9B`, pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Modal call: `fc-01M7TEYCN2MXMSY61WJN09TRRQ`
- API job / generation / attempt: `7d772621ac72ab90` / `7bda3e98b05bc804` / `beb518acc5726d88`
- Worker start: `2026-11-20 00:51:22 +07`
- Model loaded: `2026-11-20 00:51:39 +07` (`15,692 ms`)
- Prompt encoding: `56 ms`
- Constrained decoder setup: `3,684 ms`
- Inference start: `2026-11-20 00:51:43 +07`
- Backend wait limit: `1,800 s`; timeout logged `2026-11-20 01:21:11 +07`, elapsed `1,800,048 ms`
- HTTP result: `504 PARENT_ACTIVITY_OUTCOME_UNKNOWN`
- Last stage: `model_inference`; terminal worker event: none; output digest/size: none
- Worker log event count observed by backend: `20`
- Warning: missing `causal_conv1d` and `flash-linear-attention`; reference PyTorch fallback is slower. This may contribute to latency; logs do not prove it is the only cause.
- Cleanup: task language/audio app stopped at `01:22:15 +07`; container list then empty. No second inference sent.

No prompt text, child data, account identifiers, credentials, Firebase tokens, or environment values are included.

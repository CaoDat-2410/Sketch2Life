# Rev53 SAM 2.1 gate retest results

**Date:** 2026-11-06 (Asia/Saigon)

**Plan:** `../../plan/PLAN_REV53_SAM2_GATE_RETEST_20261106.md`
**Mode:** one synthetic dev call; no video, real child data, product API, or production dispatch.

## Outcome

- **Worker gate:** PASS. `drawing.segment` is accepted by the dedicated L4 worker envelope; the video execution group continues to reject it.
- **Checkpoint preflight:** PASS. The pinned checkpoint was already present and validated before GPU inference.
- **One GPU inference:** PASS at worker/output-contract level. The source hash and lineage were preserved, the result is a valid PNG, and the source fixture remained unchanged.
- **Visual mask quality:** PARTIAL/FAIL for whole-subject segmentation. The mask selects only the central butterfly body and misses the head, antennae and both wings. See `visual_review.md`.
- **Product gate:** remains CLOSED. `deployment/modal/srs_v23/workloads.json` has `drawing.segment.enabled: false`; OpenCV/Pillow remains the baseline.
- **Video:** not called.

## Root cause and code change

The previous attempt stopped before checkpoint or GPU work because `drawing_segment_app.py` parsed its input using `execution_group="l4"`, while `contracts.py::L4_WORKLOADS` omitted `drawing.segment`. This was a worker-envelope allowlist mismatch, not a GPU scheduling or checkpoint error. The change adds only `drawing.segment` to the L4 allowlist. A focused test confirms that the L4 parser accepts it, the video group rejects it, and the product registry remains disabled.

## Model, artifact and timings

| Stage | Result | Timing |
|---|---|---:|
| App deploy | Dedicated dev app deployed | 73.464 s |
| Checkpoint preflight | Already present; hash/size verified | caller 27.051 s; worker 0.734 s |
| SAM 2.1 worker call | One synthetic call; no retry | caller wait 31.896 s; worker 7.924 s |
| End-to-end retest window | 18:42:58–18:43:59 +07 | 61 s |

- Model: `facebookresearch/sam2.1-hiera-small`, repository revision `2b90b9f5ceec907a1c18123530e92e794ad901a4`.
- Checkpoint: 184,416,285 bytes; SHA-256 `6d1aa6f30de5c92224f8172114de081d104bbd23dd9dc5c58996f0cad5dc4d38`.
- Synthetic source: 1,775,882 bytes; SHA-256 `c16930354d637199b97d744de16c62bfc4f0ee97c34a23751e27912d968c6949`; unchanged after inference.
- Mask: 1254×1254 PNG, 2,797 bytes; SHA-256 `3154be67e848431f64db5c4a705aed0b1a5b209a7380c61b012e3b215f50283e`.
- Model score: 0.702293; mask area: 0.0334394; review required: true.
- Inference Modal call ID: `fc-01M6RAR0DZ9803WY2008ZJCYEJ`; checkpoint call ID: `fc-01M6RAQ5GGTVTXXS86MC6CMCMK`.

Caller elapsed time includes Modal dispatch/startup overhead; worker phase durations are separately available in `inference_result.json`. The checkpoint was cached, so no model download was needed. No retry or second inference was made.

## Verification and cleanup

- Final Modal v2.3 test suite: 100 passed in 0.82 s using an isolated pytest temp directory.
- Ruff targeted lint, `py_compile`, `git diff --check`, and `tools/validate_repository_security.py` passed. Security validation scanned 6,953 publishable files and reported `REPOSITORY_SECURITY_VALID`.
- Modal app `sketch2life-srs23-drawing-segment-dev` stopped at 2026-11-06 18:45:21 +07 and verified with 0 tasks. Other task Modal apps were already stopped. Shared model and scratch volumes were retained.
- No product workload was enabled and no video function was invoked.

Raw safe dispatch/worker evidence: `checkpoint_preflight_dispatch_intent.json`, `checkpoint_preflight_result.json`, `inference_dispatch_intent.json`, `inference_result.json`, `run_metadata.json`, and `summary.json`.

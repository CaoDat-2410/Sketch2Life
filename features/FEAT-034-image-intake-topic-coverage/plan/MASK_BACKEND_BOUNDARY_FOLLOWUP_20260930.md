# Backend mask boundary follow-up

Status: APPROVED under the owner's explicit “continue” instruction following the measured mask diagnosis and worker correction. Scope remains invalid-mask handling, not expanded segmentation/retry behavior.

## Plan and acceptance

1. Validate the source-derived subject PNG before part processing/cache admission: source identity, matching dimensions, static decoded PNG, bounded bytes/pixels, renderer-equivalent RGB-average × alpha foreground threshold (>8), area within 0.001–0.75. Preserve original and mask bytes unchanged.
2. Reject invalid subject masks without issuing their read capabilities or promoting their parts. Keep the supervised session usable and record a specific safe failure code in the existing job contract/log; do not add an automatic provider retry or V1 animation fallback.
3. Replace fake 1×1 handoff fixtures with valid matching synthetic sources/masks; regress oversized, empty, alpha-transparent, corrupt and dimension-mismatched masks, plus exact 75% acceptance.
4. Restart only the local backend after focused service/runtime/contract tests pass. Keep local logs; warn that in-memory sessions reset. External Lightning deployment is still pending and is not implied by a local restart.

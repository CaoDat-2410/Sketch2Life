# Adaptive original-art and topic-scene plan review — 2026-10-08

## Owner decisions received

- Attempt both subject-background extraction and independent body-part separation; prefer part animation when validated masks support it.
- If parts cannot be separated reliably, retain a verified source-derived subject cutout and compose it into a Pixi scene matching the child's chosen topic.
- Allow AI to select among supported rendering strategies.
- Reuse the existing single post-Gate-B planner request rather than adding a second call.

## Repository review findings

- `backend/src/sketch2life/application/services/auto_rig/part_masks.py` proposes only image-evidenced connected-color regions inside the accepted parent mask; uniform silhouettes return no parts.
- `backend/src/sketch2life/application/services/auto_rig/service.py` permits full auto-rig only when validated part masks are available; unsupported cases stay at a source-cutout tier.
- `backend/src/sketch2life/contracts/schemas/pixi_show.py` and `backend/src/sketch2life/infrastructure/ai/lightning_pixi_show_planner.py` define the existing bounded planner request and intent. There is no explicit render-strategy/theme result, and scene candidates are text descriptors rather than visual previews.
- The current FEAT-030 revision-4 approval forbids automatic retry/substitute shows. The owner's new cutout-in-topic-scene fallback changes that approved boundary, so an additive plan and exact-hash approval are required before implementation.

## Disposition

Drafted `plan/PIXI_ADAPTIVE_ART_AND_TOPIC_SCENE_20261008.md` as an additive plan. The owner approved the exact pre-approval hash `FC634C8899AB4B4FC618AF8311BDBD9C7391CC0C952C2F24AF60EC33D12428EF` at 2026-10-08 22:20 Asia/Saigon. Implementation is now authorized within that scope. No source code, provider settings, live model calls, or assets had been changed during the review/approval step.

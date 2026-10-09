# Renderer V6 launch dispatch fix

- Feature: FEAT-030 Original-derived Pixi auto-rig
- Date: 2026-10-09 (Asia/Saigon)
- Status: APPROVED_BY_DIRECT_OWNER_FIX_REQUEST

## Problem

The mobile client builds `RendererLoadCommandV6` from the approved Pixi show envelope. The WebView receive path recognizes V6 and queues it, but `loadLaunch` only parses V1–V5. The V6 launch is therefore silently ignored after the initial zero-duration `READY` acknowledgment, leaving the mobile preparation watchdog to expire.

## Scope

- Accept V6 in the renderer launch parser and select it before V5, while preserving the existing V1–V5 compatibility paths.
- Keep the V6 schema, existing sprite-cycle handling, backend contract, model/provider behavior, source image, orientation, and topic-scene policy unchanged.

## Acceptance criteria

1. A valid V6 command passes the renderer launch parser and reaches the existing V6 preparation path.
2. V1–V5 commands retain their existing parsing and dispatch behavior.
3. Existing V6 sprite-cycle status and optional cycle handling remains reachable after dispatch.
4. Static type/build checks and `git diff --check` pass. Automated tests and live Android/Lightning inference remain outside this follow-up.

## Approval evidence

The project owner reported the Pixi launch failure repeatedly and supplied the current screenshot showing the preparation-timeout state after the preceding fixes. This follow-up is limited to correcting the V6 renderer dispatch defect identified from that evidence.

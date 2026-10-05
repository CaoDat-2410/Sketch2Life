# Mobile image, animation and Pixi runtime recovery

- Status: APPROVED
- Revision: 4
- Owner authorization: direct request to fix all reported errors and push; emulator smoke exposed Android 15 edge-to-edge status-bar overlap and continuous idle Home redraws.
- Scope: reproduce native asset resolution, repair image delivery without changing artwork; stop decorative animation work at unmount; bound renderer bridge updates and GPU work; restore the already approved FEAT-030 local sprite preview and prove it with synthetic inputs; keep app-screen content below the Android system status-bar inset; remove nonfunctional perpetual Home-only decoration that causes continuous redraws.
- Dependencies: approved FEAT-035 revision 1 and FEAT-030 `SPRITE_CYCLE_LOCAL_RUNTIME_ACTIVATION_20261002.md`; preserve the existing two-cycle preview allowlist and production gates.

## Acceptance criteria

1. Existing robot/onboarding/home artwork resolves to nonempty image bytes and is visibly present on Android; originals stay unchanged.
2. Decorative loops and timers have cancellation on unmount. Playback progress is bounded while pause, seek, completion and phase transitions remain immediate.
3. Pixi native host props remain stable across progress renders; renderer resolution/frame rate are bounded for mobile and sprite clock stays deterministic.
4. A QA-passed local cycle is decoded and visibly played through backend frame capabilities, with pause/replay/teardown checks. No production rights state or unsupported class is silently enabled.
5. Relevant mobile/renderer/backend tests, TypeScript, build, harness and security checks pass; remaining full taxonomy coverage is reported accurately.
6. The approved walker preview is visually grouped beside the source subject (outside its protected bounds), and inherits the same root/show translation so their vertical movement cannot drift apart.
7. Android 15 screens do not render their first row under the system status bar; retain the current desktop-web frame and older Android behavior.
8. Home does not continuously redraw for nonfunctional looping particles or CTA pulsing; story/Pixi motion remains intact.

## Verification

Record asset URL/decode findings, synthetic cycle checks and Android screenshots inside this feature's evidence tree. Test offline; do not invoke live inference as part of reproduction.

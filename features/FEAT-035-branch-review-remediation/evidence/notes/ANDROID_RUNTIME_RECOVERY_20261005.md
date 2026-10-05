# Android runtime recovery evidence — 2026-10-05

## Build and launch

- Built and installed the local Android debug preview for `com.sketch2life.mobile` on the
  `Pixel_10_2` AVD (`emulator-5554`). The native build completed successfully; local SDK overrides
  used compile/target 35 and x86_64 because this machine has Android 37 artifacts while the
  Expo/Gradle configuration requests 37.
- The APK launched to the React Native app. Smoke navigation reached onboarding, Home, Story
  Preview, then the expected adult next-step gate. No `AndroidRuntime`, `FATAL EXCEPTION`, or
  React Native JS error was found in the recent emulator logcat sample.
- The flow stops at the adult confirmation/profile gate. Native Android WebView behavior for the
  sprite-motion fixture was not verified in this pass; sprite cohesion was checked in the local
  browser renderer fixture at 0s and 1s instead.

## Visual/runtime observations

- `emulator-bundled-home-safearea-20261005.png` and
  `emulator-bundled-onboarding-safearea-20261005.png` show app content below the Android 15+
  status bar. `emulator-bundled-onboarding-before-safearea-20261005.png` preserves the before
  image demonstrating the previous overlap.
- `emulator-bundled-home-static-20261005.png` shows Home after nonfunctional floating particles
  and CTA pulsing were removed; greeting, illustrations, and navigation remain.
- With Home idle for eight seconds, `dumpsys gfxinfo` reported `Total frames rendered: 0`,
  `Janky frames: 0`, and `Number Missed Vsync: 0`. This is an idle-no-redraw observation, not a
  claim about frame time during active story/Pixi playback.
- `emulator-bundled-story-20261005.png` confirms the source drawing remains present in Story
  Preview; `emulator-bundled-flow-20261005.png` records the adult next-step gate.

## Scope and boundaries

- Offline/local only. No Lightning AI, Qwen, SAM, Whisper, or other live provider call was made.
- Existing artwork bytes were bundled/visible; originals and production asset eligibility were
  not changed. No release signing, asset promotion, or deployment was performed.

# Decisions

## D-066-01 — Use `tablist` for Parent tab-group wrappers

- Status: Implemented and runtime-verified on the supplied Pixel_6 emulator.
- Decision: Replace the unsupported Android runtime value `tabbar` with `tablist` on the Parent bottom-navigation and lesson-filter group wrappers.
- Rationale: Each contained control already exposes role `tab`; the existing `ChildProfilesScreen` uses the same `tablist` group pattern. The change preserves interaction and improves the chance that platform accessibility services identify the group correctly.
- Scope boundary: No other role, label, selected state, screen structure, or visual style changes.

## D-066-02 — Record the web/native Parent UI implementation split

- Status: Observed during post-run comparison; no product or implementation decision made.
- Finding: `UI_Project/parent-ui` is a React/Vite Android-sized browser prototype, while `UI_Project/parent-android/apps/mobile` is the separately implemented React Native Android target. Their Parent home screens use independent component trees and styling.
- Consequence: The visual mismatch is expected with the current source layout. Porting the browser design into the native app is separate work and was excluded from the approved FEAT-066 plan.

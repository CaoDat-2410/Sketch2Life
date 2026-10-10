# FEAT-036 decisions

## D-036-01 — Review only; no implementation approval

The owner requested an audit, prioritized findings, and a fix task while explicitly saying not to
implement. This feature records that review and its proposed work only. Product changes remain
`AWAITING_APPROVAL`; this request does not approve implementation.

## D-036-02 — Use the current owner-approved requirements as the UI target

Use the master SRS B21 and B30–B33 plus ADR-0012/0013 to evaluate UI. The stale
`apps/parent-web/README.md` statement that the web split is inactive does not override the newer SRS
scope closure. Reconcile the duplicated project-context statements before any web implementation.

## D-036-03 — Keep cross-feature work separately gated

Missing Parent Web, Guide Console, and illustrated-video runtime are recorded as product-surface
gaps. They need separately scoped/approved work and an explicit owner/allocation; this audit does not
assign them to a person or silently expand the mobile UI implementation scope.

## D-036-04 — Keep runtime captures distinct from design mockups

The screenshot album contains native emulator captures; existing screen PNGs under
`apps/ui-mobile/assets/images/` remain design assets and cannot stand in for runtime screenshots.
The source includes a 15-screen Web developer switcher (`?dev=true`) and direct screen selection
(`?screen=<id>`), but Expo Web stays blank with an empty root on local hostnames. `index.ts`
registers the app with `AppRegistry` without Expo's web root bootstrap, which appears to block this
capture route. The Android `Pixel 10` emulator now runs the app and exposes the standard React Native
Dev Menu (Bridge), but that menu has no app-route selector. Five of the 15 active screens have
runtime evidence; ten remain uncaptured. Current runtime evidence does not reproduce the earlier
Home inset overlap or solid-color story thumbnails, while the default Story Preview looks washed
out and needs a fully selected-drawing comparison. Product implementation remains
`AWAITING_APPROVAL`.

## D-036-05 — Keep runtime debug tools separate from app screen selection

The Android emulator's React Native Dev Menu is a real native debug menu (Reload, Open DevTools,
Change Bundle Location, Inspector, and related tools). It is not the app's 15-screen quick switch.
That quick switch and direct `?screen=<id>` route are Web-only. Keep the remaining screen coverage
open until a capture path is approved and available; do not treat the native Dev Menu as evidence
that all routes were reviewed.

## D-036-06 — Reclassify Home visual issues after current-runtime capture

The preserved Home screenshot suggested system-inset overlap and blank-colored story thumbnails.
Current Pixel 10 runtime evidence does not reproduce either issue: Home content respects visible
status/gesture areas and both story illustrations render. Do not schedule those fixes from the stale
capture. Keep safe-area verification in the device matrix and reopen image handling only if another
current device reproduces it. Story Preview's default placeholder remains a contrast check, not a
confirmed defect.

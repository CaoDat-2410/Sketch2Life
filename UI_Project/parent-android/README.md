# Parent Android and mobile UI sources

This workspace preserves both mobile clients present in the local project checkout, plus their shared renderer:

- `apps/mobile`: Android-only React Native 0.87 app boundary and native Android project.
- `apps/ui-mobile`: Expo/React Native mobile UX with its own screens and visual assets.
- `packages/art-renderer`: local PixiJS/GSAP renderer package referenced by both mobile workspace manifests.

The two apps are separate source workspaces and are kept side by side; neither has been merged into the other. This bundle was copied from the local working tree of checkout `Sketch2Life-be-dev-2026-11-07`, branch `dev`, HEAD `1431ef81`, including local uncommitted UI source. It is not verified as the latest GitHub revision. Dependency caches, generated build/Gradle/CMake outputs, signing materials, and machine-specific Android SDK settings are excluded.

## Install

Use Node.js 22.13+ and pnpm 11.19+. From this folder:

```powershell
pnpm install
```

## Start

For the React Native Android app:

```powershell
pnpm start
```

Then in a second terminal with an Android SDK/emulator configured:

```powershell
pnpm android
```

For the Expo mobile UI:

```powershell
pnpm start:ui-mobile
```

Both app manifests and the workspace lock/config are included. API/backend behavior is not added by this source bundle.


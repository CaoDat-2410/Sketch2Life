# FEAT-079 Decisions

## D1 — Expo becomes the active app framework

Use stable Expo SDK 58 with its compatible React Native 0.88 and React 19.3 versions for apps/mobile. React Native remains the UI framework underneath Expo. Use Expo CLI and a development client for local development and emulator builds.

## D2 — Preserve the current native Android project

Retain and integrate apps/mobile/android in place. Preserve the application ID and SDK floor/targets. Do not run clean prebuild or delete native sources as part of this migration.

## D3 — Preserve product and app boundaries

Keep Android-only support, the existing Parent demo flow, the local demo adapter and no-backend boundary. Keep apps/ui-mobile as the legacy Expo SDK 52 behavior reference without upgrading or merging it.

## D4 — Record a scoped ADR

ADR-0023 records Expo for the active apps/mobile app and supersedes the older bare React Native CLI workflow choice only for this application. The canonical product SRS remains unchanged and unsigned.

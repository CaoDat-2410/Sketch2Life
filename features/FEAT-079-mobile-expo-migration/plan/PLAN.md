# FEAT-079 Plan Rev1 — Expo migration for the active mobile app

- Status: APPROVED
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date: 2026-11-10
- Worktree: owner-designated fe-ui-full-remediation worktree.
- Requirement authority: FEAT-063 System Architecture SRS v2.7-draft Rev57, unsigned working baseline, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5.
- Target: apps/mobile, the active Parent Android app.

## Goal

Move the active Parent Android app to the Expo framework and Expo CLI while retaining its React Native TypeScript screens, local demo workflow, Android-only product boundary, and current application identity.

## Scope

1. Adopt the current stable Expo SDK 58 pairing (React Native 0.88 and React 19.3 as of 2026-11-10), Expo CLI, and a development client. React Native remains the UI runtime; Expo becomes the app framework and development/build toolchain.
2. Configure the Expo entry point, app config, Babel, Metro, Jest, package scripts, dependency alignment, and pnpm lockfile for the existing workspace and shared art-renderer package.
3. Integrate Expo modules and Expo CLI with apps/mobile/android while preserving the Android project and its app ID, minSdk 29, targetSdk 36, and compileSdk 37. Do not run prebuild --clean or discard native project files in this task.
4. Keep the app Android-only. Keep its current demo-only Parent flow, local in-memory state, and no-API behavior unchanged.
5. Keep apps/ui-mobile as the separate legacy Expo SDK 52 behavior reference; do not merge, upgrade, or delete it.
6. Record the scoped technology choice in ADR-0023. Add a dated supersession note to the older bare-RN workflow answer and update active mobile setup documentation. Do not rewrite the canonical SRS or historical ADRs.
7. Update feature context, decisions, status, and evidence.

## Acceptance criteria

- AC1: apps/mobile has an Expo app configuration and Expo entry point, and its development/start and Android scripts use Expo CLI rather than React Native CLI.
- AC2: Expo SDK, React Native, React, and Expo-native dependencies resolve to a compatible stable SDK 58 set; package-manager lock state represents the workspace resolution.
- AC3: Metro resolves apps/mobile and packages/art-renderer in the pnpm monorepo without borrowing the legacy Expo SDK 52 Metro graph.
- AC4: Android remains the only configured app platform; application ID remains com.sketch2life.mobile, minSdk remains 29, targetSdk remains 36, and compileSdk remains 37.
- AC5: The existing Parent demo workflow, profile, quota, settings, review gates, fixture lab, and local-only data boundary remain intact.
- AC6: Expo module initialization is present in the retained Android native project; no clean prebuild removes or overwrites native project files.
- AC7: Active mobile instructions and the feature evidence identify the Expo commands and state any local Android SDK/emulator limitation accurately.
- AC8: The changes stay in the owner-designated worktree, preserve all pre-existing edits, and do not alter apps/ui-mobile, web apps, backend, API contracts, SRS requirements, or product policies.

## Implementation steps

1. Record the decision and user-approved scope before code changes.
2. Align package dependencies and scripts with Expo SDK 58; update the workspace lockfile without changing the legacy Expo package.
3. Configure Expo app metadata, registration, Babel/Metro and test preset.
4. Integrate Expo modules with the existing Android project and preserve its Android identity and SDK constraints.
5. Update mobile setup and architecture records; capture feature-local evidence and status.

## Verification plan

- Inspect the resolved public Expo config and verify Android package/platform/SDK settings.
- Run the mobile TypeScript check and existing focused mobile tests when available.
- Run Expo dependency diagnostics for SDK alignment.
- Build and launch the Android development client on an emulator if Android SDK, JDK, and emulator are available; otherwise record the exact blocker and the commands for the owner to run after setup.
- Review the diff and run git diff --check. Do not run security validation unless preparing a commit or push.

## Risks and mitigations

- Expo SDK targets a specific React Native version. Use the published stable SDK 58 pairing instead of mixing SDK 52, RN 0.87, or canary versions.
- The native Android project is already present and contains the required application identity and SDK values. Integrate Expo incrementally and avoid destructive clean prebuild.
- A legacy Expo SDK 52 app shares the pnpm workspace. Preserve its package graph and lockfile importer while isolating the active app's SDK 58 Metro dependencies.
- Android build execution may be unavailable because this machine has no configured Android SDK or emulator. Keep config/type checks separate from device-build claims.

## Evidence plan

Record dependency/config resolution, source changes, command outputs, environment limitations, and the final worktree state under this feature's evidence directory. No screenshots or generated visual assets are required.

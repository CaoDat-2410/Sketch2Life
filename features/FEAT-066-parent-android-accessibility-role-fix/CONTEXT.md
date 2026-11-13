# Feature context

- Status: COMPLETE
- Owner: Project owner/requester
- Goal: Run the new Parent native Android UI on the existing emulator without a React Native red screen.
- Scope: Correct the two invalid accessibility group roles in `UI_Project/parent-android/apps/mobile`, build and install the debug APK, and verify the Parent preview and lesson library on the connected emulator.
- Non-goals: Delete the legacy Child Expo source, change the old `apps/ui-mobile` workspace, alter authentication or product behavior, change visual design, modify backend/API/data, commit, or push.
- Dependencies: Android emulator `emulator-5554` (Pixel_6, API 37), Android SDK/JDK already configured, Parent Metro server on localhost.
- Risks: A role accepted by TypeScript may still be rejected by the Android runtime; runtime verification on the supplied emulator passed for both the Parent home navigation and lesson-library filter group.

## Context snapshot

The requester wants the Parent mobile UI running as a native app on the provided Android emulator and supplied a screenshot of the runtime error `Invalid accessibility role value: tabbar`. The error is reproduced when entering the Parent preview flow. Both the Parent bottom navigation and lesson category filters use this invalid wrapper role; their child controls already use `accessibilityRole="tab"`.

Current product requirements are routed through `docs/context/SRS_AUTHORITY.md` to FEAT-063 SRS v2.5-draft. NFR-20 identifies Android platform accessibility as a target; this scoped implementation changes no product requirements and does not claim full accessibility conformance. The SRS remains an unsigned draft.

The Child Expo preview server was stopped as requested; its source is preserved. The target native app is `UI_Project/parent-android/apps/mobile`, package `com.sketch2life.mobile`, on branch `FE_UI_Project_Ver2` at commit `5c8b9e54` when the task began.

The Parent debug APK was built and installed on Pixel_6 emulator `emulator-5554` (Android 17/API 37). The preview home is left open on the emulator. The user selected the “Công khai” lesson-library filter without a RedBox. The debug app loads JavaScript from the local Metro server; authentication and preview data remain unconnected to backend services.

## Visual comparison finding

The browser design shown by the requester is `UI_Project/parent-ui`, a React/Vite Android-sized interaction prototype. The emulator runs `UI_Project/parent-android/apps/mobile`, a separate React Native app with its own `ParentHomeScreen`. The two implementations do not share screen components or styles, so starting the native app does not reproduce the browser prototype's home layout. The approved FEAT-066 scope fixed the native crash and explicitly excluded visual redesign; matching the browser screens in the native app requires a separately planned and approved UI port.

## Source references

- `docs/context/SRS_AUTHORITY.md` — canonical working SRS routing and approval boundary.
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §14.1 / NFR-20 — Android accessibility target.
- `UI_Project/parent-android/apps/mobile/src/shared/ui/ParentBottomNavigation.tsx` — invalid bottom-navigation wrapper role.
- `UI_Project/parent-android/apps/mobile/src/features/lesson/ParentLessonLibraryScreen.tsx` — invalid category-filter wrapper role.
- `UI_Project/parent-android/apps/mobile/src/features/profile/ChildProfilesScreen.tsx` — existing `tablist` grouping pattern in this app.

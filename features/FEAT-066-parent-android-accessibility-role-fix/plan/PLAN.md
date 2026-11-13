# Parent Android preview accessibility-role fix

- Status: APPROVED
- Plan revision: 1
- Implementation status: COMPLETE (scope unchanged from the approved hash; lifecycle status updated after authorization)

## Goal

Make the Parent native Android app render its preview flow on the requester's running emulator by removing the invalid `tabbar` wrapper role that currently triggers a React Native red screen.

## Scope

- In the active native Parent app only, change the wrapper grouping role in `ParentBottomNavigation` and the lesson-library category filters to the valid `tablist` role.
- Preserve each child control's existing `tab` role, selected state, labels, navigation actions, layout, and styling.
- Build and install the debug APK, then verify the Parent preview and lesson-library screens on `emulator-5554`.
- Record device screenshots and command/log evidence in this feature's `evidence/` directory.

## Steps

1. Confirm React Native 0.87.0 supports `tablist` and identify the two failing wrapper usages.
2. Apply the two-line semantic role correction without changing app flow or design.
3. Build the debug APK with the configured Android SDK/JDK and install it over the existing package.
4. Open the app, enter “Xem bản trải nghiệm”, and confirm the Parent home renders without a red screen.
5. Open the lesson library and confirm its category tab group renders and remains selectable.
6. Save visual/runtime evidence, update feature status/context, and inspect the final diff.

## Acceptance criteria

- AC1: The debug APK builds successfully and installs on `emulator-5554` as `com.sketch2life.mobile`.
- AC2: Tapping “Xem bản trải nghiệm” opens the Parent preview/home UI with the bottom navigation visible and no `Invalid accessibility role value` red screen.
- AC3: The lesson-library screen opens without the same red screen; its category controls retain their tab semantics and selection interaction.
- AC4: Screenshots, build/install/runtime details, and limitations are stored under this feature's `evidence/` directory.
- AC5: No Child Expo or legacy workspace source, backend/API behavior, authentication behavior, design, or product requirements are changed; no commit or push is performed.

## Risks and mitigations

- The TypeScript role union alone does not prove Android runtime acceptance; AC2 and AC3 require on-device verification.
- Keep the individual controls as `tab` and change only their group wrapper to `tablist`, matching the existing app pattern in `ChildProfilesScreen`.
- If another runtime failure appears, record it as a separate finding and do not broaden this fix without revising the plan.

## Verification plan

- Inspect the installed React Native 0.87.0 role definitions and the existing in-app `tablist` pattern.
- Run the Android debug Gradle build.
- Use ADB to install, launch, navigate, inspect logcat, and capture emulator screenshots.
- Review `git diff --check` and the final changed-path list. No automated test suite is added or run for this UI runtime correction.

## Evidence plan

- `evidence/README.md`: evidence index and result summary.
- `evidence/screenshots/parent-preview-home.png`: Parent home after entering preview.
- `evidence/screenshots/parent-lesson-library.png`: lesson library and filters.
- `evidence/notes/EXECUTION.md`: exact build/install/navigation commands, device/runtime details, result and limitations.

Implementation is permitted only with the matching `approvals/TASK_APPROVAL.md` record marked `APPROVED`.

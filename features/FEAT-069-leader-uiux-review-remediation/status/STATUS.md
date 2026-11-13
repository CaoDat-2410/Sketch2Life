# Status

- **Feature:** FEAT-069 — Leader review UI/UX remediation.
- **State:** IN_PROGRESS under the approved Rev4 UI-only plan. Parent, Teacher, School Manager, and Platform Admin UI work is updated and verified; publication is the remaining step.
- **Active plan:** `plan/PLAN_REV4_UI_ONLY.md`, SHA-256 `EE85CB380638985969419A38646B1D72383C74CC390027C903D1950C387FF4C3`.
- **Branch:** `FE_UI_Project_Ver2`.
- **Current scope:** APIs are used only as business-flow reference. The four role workspaces do not invoke `backendApi`, an auth bridge, `fetch`, or a backend request; their data remains visibly labeled as preview/demo data.
- **Parent UI:** Settings is only available from the Family Profile page. Unsupported gender controls and the pre-video activity-selection step are removed. Lesson activities are reached from a story after its video preview. Story/video generation remains an honest unavailable preview.
- **Teacher UI:** Existing high-contrast workspace, single top-bar notification entry, centered details, and navigable class → lesson → session → slide/Sketch → interaction → separate sample preview remain in place.
- **Other web roles:** School Manager and Platform Admin remain role-specific workspaces with preview data and no server-action claims.
- **Verification:** `npm run build` passed all five UI workspaces. Parent Android typecheck passed. Debug APK packaging passed after setting the process SDK path to the existing local Android SDK. CUA visually reviewed Parent home/profile/settings/story activity and all three web role workspaces. No automated tests were run.
- **APK:** `UI_Project/parent-android/apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`. Packaging passed; emulator installation was not repeated in Rev4. Earlier install and package lookup attempts stalled at Android Package Manager; no wipe/reset was performed.
- **Historical Rev3:** commit `be8aa646` and its API crosswalk remain as historical records. Rev4 reverted the UI-level API wiring; see `evidence/notes/EXECUTION.md` and `evidence/notes/OPEN_QUESTIONS.md`.
- **Publication:** Rev4 commit and normal fast-forward push to the previously authorized `origin/FE_UI_Project_Ver2` are pending closeout.

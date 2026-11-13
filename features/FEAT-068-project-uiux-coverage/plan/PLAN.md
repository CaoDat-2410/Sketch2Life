# Complete UI/UX coverage for Parent and web roles

- Status: APPROVED
- Plan revision: 1
- Implementation status: IN_PROGRESS

## Goal

Make the Parent Android UI and the Teacher, School Manager, and Platform Admin web UIs coherent, easy to review, and aligned with current product flow and actual API capability so the owner can hand off the project UI/UX on `FE_UI_Project_Ver2`.

## Scope

- Redesign the Parent home, navigation, profile/settings, lesson library/detail, and end-to-end story creation/review/generation/playback/history surfaces in `UI_Project/parent-ui`; keep mobile-first behavior and the existing packaged Android WebView target.
- Complete the Teacher web surfaces for dashboard, class/roster, lesson library/authoring/document review, occurrence preparation, optional Sketch Deck, sample story flow, and presentation confirmation.
- Complete the School Manager surfaces for organization/classes/assignments and version-specific lesson publication review.
- Complete the Platform Admin surfaces for content moderation and a truthful platform-operations overview.
- Establish shared, accessible design tokens and reusable UI states for navigation, buttons, forms, dialogs, tables/cards, notification surfaces, loading/empty/error/disabled states, and confirmations. Use the current Parent visual identity as the brand anchor; reduce glare and improve contrast in adult web workspaces.
- Map each business screen/action to a mounted API operation, an SRS target without a mounted endpoint, or local preview data. Do not add backend/API/schema/auth behavior.
- Preserve the existing role workspace commands, Parent Android packaging, and the three web role entry points. Add or revise concise run guidance only where required for the UI handoff.
- Record implementation and verification evidence inside this feature; update the source register, context, decisions, and status after meaningful milestones.
- After successful review/security validation, commit and push normally to `origin/FE_UI_Project_Ver2`, consistent with the owner’s earlier handoff instruction.

## Product and flow decisions

- Parent flow follows FEAT-063 SRS v2.5-draft: optional generic line-sketch while the child draws → capture → idea and optional confirmed transcript → subject review/correction → adult context snapshot confirmation → story/script review → video generation/status → private playback → lesson outdoor activities after the video.
- Parent context is reviewed and confirmed; the UI does not ask whether to ignore selected child context. Parent does not select outdoor activities before the video.
- Do not invent a persisted child-gender field or the unsupported “lesson priority versus child drawing” mismatch modal. Keep the SRS subject correction and optional lesson script-direction behavior.
- Teacher’s optional Sketch Deck remains separate from the child-specific sample-video run. Keep video readiness/safety state distinct from Teacher’s explicit presentation confirmation.
- Rev38 mockups and component boards are layout/content references only. Do not copy their visual tokens wholesale or reference their unapproved generated PNGs in runtime code.
- When no mounted API is available, show a clearly labelled local preview or unavailable state; never report mock local state as persisted or as a successful AI/backend result.

## Explicit boundaries

- No backend, API contract, database, authentication provider, provider/model, SRS, deployment, or real child-data changes.
- No removal or source changes to the legacy Child Expo workspace.
- No generated bitmap artwork or promotion of the Rev38 image drafts. Use code-native UI and existing approved/applied assets only.
- No release signing, force push, history rewrite, or work on another branch.
- The scope is the four stated adult roles; Child Expo is excluded based on the owner’s earlier direction that it is an obsolete UI target.

## Steps

1. Inventory the current four-role UI, current Parent APK packaging path, and API mount/client mapping against the canonical SRS; keep the findings in feature evidence.
2. Implement shared visual tokens and accessible primitives, then revise Parent mobile screens and navigation.
3. Implement the Teacher, School Manager, and Platform Admin page flows using reusable role-specific layouts and truthful API/preview states.
4. Build the Parent web bundle into the Android package, install/launch it on the supplied emulator, and inspect key Parent flows. Build and open the three web workspaces in browser viewports.
5. Resolve visual/functional defects found during inspection; store reproducible build and screenshot evidence under FEAT-068.
6. Update role run guidance and feature/source status. Run `git diff --check` and `python tools/validate_repository_security.py`, stage only the approved feature/UI files, commit normally, and push to `origin/FE_UI_Project_Ver2` if the branch remains a fast-forwardable authorized target.

## Acceptance criteria

- AC1: The Parent Android app opens the redesigned mobile-first Parent UI without needing the Vite server; the screen hierarchy, gestures, bottom navigation, and primary story entry work on the supplied emulator.
- AC2: Parent screens cover the SRS-relevant profile, lesson, story creation/review, progress, playback, history, quota, settings, and feedback surfaces; Parent activity ordering and context confirmation follow the decisions above.
- AC3: Teacher web presents the SRS flow with distinct lesson authoring/import/review, class/roster, optional Sketch Deck, sample story, and presentation-confirmation states.
- AC4: School Manager and Platform Admin each have complete, role-specific navigation and review/management surfaces without exposing child story/media data outside authorized scope.
- AC5: Web role dashboards and common components use a consistent higher-contrast visual system with keyboard/focus support, semantic labels, usable dialogs, and mobile/tablet overflow handling.
- AC6: Every backend-bound action is mapped to an existing mounted API and uses its actual request/response state; missing routes remain visibly preview-only or unavailable, with no false success, fake ETA/progress, or hidden mock persistence.
- AC7: Parent remains the Android target and the Teacher, School Manager, and Platform Admin web workspaces continue building and opening from their documented commands; the legacy Child Expo workspace is not selected by the launch/run guidance.
- AC8: Parent Android and all web workspaces build successfully; emulator/browser visual evidence is stored in FEAT-068, and the project security validator passes before commit/push.
- AC9: Feature context, decisions, evidence, status, root source register, and publication evidence accurately reflect the implemented scope and any remaining API limitations.

## Risks and mitigations

- Missing auth and story/video/occurrence endpoints can make real workflows impossible; represent only supported calls as connected and label other behavior as preview-only.
- The review notes predate the current SRS; follow the decision record and list any remaining product question rather than inventing a new contract.
- The Parent UI is HTML/CSS inside an Android WebView; verify on the emulator at actual device dimensions and safe-area/navigation-bar conditions.
- The requested scope spans four roles; implement shared primitives first and keep role workflows visibly distinct to avoid one oversized generic dashboard.

## Verification plan

- Build all UI_Project web workspaces and typecheck/build the Parent Android host using the versions documented in their manifests.
- Install and manually inspect the Parent app on the supplied emulator, including home, navigation, profile, lesson detail, capture/story review states, and playback/activity order.
- Open Teacher, School Manager, and Platform Admin web workspaces and manually inspect dashboard, primary workflow, dialogs, keyboard/focus, and a narrow viewport.
- Check each API call site against source route registration; do not send write requests to a shared backend. Run automated tests only where explicitly required by existing workflow or requested by the owner; this plan does not add tests.
- Run `git diff --check` and `python tools/validate_repository_security.py` before any commit/push.

## Evidence plan

- `evidence/README.md`: AC-to-evidence map and scope.
- `evidence/notes/API_UI_CROSSWALK.md`: route/client/preview-state crosswalk and any unimplemented backend target.
- `evidence/notes/EXECUTION.md`: build, emulator/browser inspection commands, results, and limitations.
- `evidence/screenshots/`: Parent emulator and role web screens captured during review.
- `evidence/notes/PUBLICATION.md`: security validation, staged paths, commit, and push result.

Implementation is permitted only while this plan revision is recorded as `APPROVED` in `approvals/TASK_APPROVAL.md`.

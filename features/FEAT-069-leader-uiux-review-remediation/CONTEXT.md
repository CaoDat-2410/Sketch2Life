# FEAT-069 — Leader review UI/UX remediation

- **State:** IN_PROGRESS under the exact approved Plan Rev2 scope. Rev1 is published; Rev2 completes the remaining leader-review UI items as review prototypes while preserving the canonical SRS/API boundary.
- **Branch:** `FE_UI_Project_Ver2`.
- **Goal:** Close the leader-review UI gaps that can be implemented without changing current product requirements or inventing backend behavior.
- **Authority:** `docs/context/SRS_AUTHORITY.md`; canonical working requirements are FEAT-063 SRS v2.5-draft, still awaiting owner sign-off.
- **Review input:** owner-provided local Codex attachment containing the leader transcript. The source stays local and is treated as feedback to reconcile, not as a replacement for current SRS/API contracts.
- **Baseline:** FEAT-068 is complete and published on this branch. The current UI source is preview-first: Parent business state is local; web role business data is local; an auth bridge and main-app identity endpoint are absent.
- **UI source selection:** The user confirmed `UI_Project/` is the primary UI/UX to update and that top-level `apps/` contains legacy UI outside this handoff. Rev2 implementation and run instructions target only `UI_Project/` workspaces.
- **Parent mobile entry:** `UI_Project/parent-android/apps/mobile` is the Android APK host; `ParentWebPreview` loads the bundled `UI_Project/parent-ui` page. The separate `parent-android/apps/ui-mobile` workspace is not the target for this review task.
- **Latest API comparison:** A read-only audit of the permitted newer backend source `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e` found Parent profile/story routers that are absent from `FE_UI_Project_Ver2@2518dc07`. Treat those newer routes as future source context only; the deliverable must label them unavailable unless mounted in the branch teammates clone.

## Approved scope

- Make Parent lesson selection visible in the story setup flow, clearly distinguish public system lessons from school/teacher-shared lessons, and retain in-place details.
- Improve the optional pre-capture line-sketch preview into a topic-aware, step-by-step guide while clearly identifying it as static until the approved AI route is mounted.
- Keep lesson story direction after capture/subject review; simplify audio-related copy while preserving editable adult review and accurately disclosing that speech recognition is not connected.
- Replace the full-screen context-selection presentation with a compact confirmation dialog while retaining the adult context review required by FR-P-06.
- Reduce Parent home height and keep the center create action immediately visible; retain global settings and existing bottom navigation.
- Improve Teacher web contrast and clarify the class → lesson → session presentation flow. Keep the sample-video workflow distinct from the class occurrence.
- Update feature evidence, decisions, status, and the root source register. Build/visually inspect affected outputs, run the required repository security validator, and publish a normal commit to the previously authorized `origin/FE_UI_Project_Ver2` target if it remains fast-forwardable.

## Out of scope / open product decisions

- Do not move Parent outdoor activities before playable video; FR-P-05 and FR-PL-16 expressly put them after video.
- Do not add a persisted child gender field absent from current SRS and API data models.
- Do not add the leader-described mismatch-direction modal unless an owner-approved SRS/API decision defines the analysis state and behavior. Preserve the existing post-capture lesson-direction choice.
- Do not claim live speech-to-text, AI line sketch, teacher dashboard data, or generated “Show Slide” output when the corresponding mounted authenticated API and runtime identity context are unavailable.
- Do not change backend/API/schema/auth/provider/SRS, run AI/provider requests, send writes to a shared backend, or modify the legacy Child Expo workspace.
- No generated bitmap assets are in scope. Use existing approved assets and code-native layout/illustration only.

## Current progress

Rev1 implementation and publication are complete. The user has now explicitly authorized the full leader-review UI scope under Plan Rev2. Rev2 follows the leader's requested presentation order as a local UI prototype where it differs from the unsigned canonical SRS, and does not modify that SRS or make backend/schema/API changes. Implementation has not started until this Rev2 approval record was completed.

The Rev1 builds passed and its screenshots are in `evidence/`. The supplied emulator could not install the rebuilt APK because Android's Package Manager returned `Failure calling service package: Broken pipe (32)` and the emulator log showed system-server/GMS death; no emulator data was wiped. Rev2 will rebuild and visually inspect the final output and record the emulator limitation if it persists.

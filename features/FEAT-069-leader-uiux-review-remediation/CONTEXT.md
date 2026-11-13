# FEAT-069 — Leader review UI/UX remediation

- **State:** IN_PROGRESS under the exact approved Plan Rev3 scope. Rev1 and Rev2 are published; Rev3 adds limited API-backed read states to the existing review UI while preserving the canonical SRS/API boundary.
- **Branch:** `FE_UI_Project_Ver2`.
- **Goal:** Close the leader-review UI gaps that can be implemented without changing current product requirements or inventing backend behavior.
- **Authority:** `docs/context/SRS_AUTHORITY.md`; canonical working requirements are FEAT-063 SRS v2.5-draft, still awaiting owner sign-off.
- **Review input:** owner-provided local Codex attachment containing the leader transcript. The source stays local and is treated as feedback to reconcile, not as a replacement for current SRS/API contracts.
- **Baseline:** FEAT-068 and FEAT-069 Rev2 are complete and published on this branch. Parent business state remains local preview. Web workspaces now have conditional read wiring for Teacher lessons/assignments and Manager classes, but the delivery checkout still lacks the expected auth bridge and `/api/auth/v1/me` handler for ordinary authenticated role resolution.
- **UI source selection:** The user confirmed `UI_Project/` is the primary UI/UX to update and that top-level `apps/` contains legacy UI outside this handoff. Rev2 implementation and run instructions target only `UI_Project/` workspaces.
- **Parent mobile entry:** `UI_Project/parent-android/apps/mobile` is the Android APK host; `ParentWebPreview` loads the bundled `UI_Project/parent-ui` page. The separate `parent-android/apps/ui-mobile` workspace is not the target for this review task.
- **Latest API comparison:** A read-only audit of the permitted newer backend source `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e86826447d975ef2757aa1fefdc876c8c` found Parent profile/story and AI routes absent from the delivery baseline `FE_UI_Project_Ver2@ae2a8c8165aa1d11b62a7005a9e28d8c0ea8c046`. Treat those newer routes as future source context only; the deliverable labels them unavailable unless mounted in the branch teammates clone.

## Rev3 current scope and implementation status

Plan Rev3 is the active approved plan and supersedes Rev2 for current work; its approved Parent Library addendum is recorded separately. In `UI_Project/shared/webWorkspace.tsx`, authenticated mode conditionally reads Teacher Lesson Library lessons plus BE1 assignments, or School Manager BE1 classes, when the runtime supplies both the Firebase token bridge and organization ID. In `UI_Project/parent-ui`, authenticated mode conditionally reads Parent public/shared lessons, invitations and selected lesson details, and submits invitation accept/decline only after an explicit user action. Teacher/Manager dashboards derive supported summary values from their API responses. API failure/unavailable states do not fall back to fixture rows. Without an auth bridge, screens remain explicitly labeled preview mode. Platform Admin remains preview-only because this delivery branch has no moderation queue-list API. Parent profile/story/photo/ASR/AI/video/playback state remains preview-only because those route families are not mounted in this delivery composition.

This frontend wiring does not establish that the team can log in end-to-end: the client references `GET /api/auth/v1/me`, but the handler and bridge are not present in this checkout. No API calls or writes were made during implementation or review. The exact route, branch and screen mapping is recorded in `evidence/notes/API_UI_CROSSWALK_REV3.md`.

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

Rev1 and Rev2 implementation/publication are complete. The user has explicitly authorized the API-aligned frontend work under Plan Rev3. Rev3 preserves the leader-review prototype behaviors from Rev2 where already approved, adds limited conditional API-backed read views for current mounted routes, and does not modify the unsigned canonical SRS or backend/schema/auth/API contracts. Any Rev2 behavior that conflicts with the SRS or lacks a mounted API remains visibly preview-only and is tracked as an open decision.

The Rev1 builds passed and its screenshots are in `evidence/`. The supplied emulator could not install the rebuilt APK because Android's Package Manager returned `Failure calling service package: Broken pipe (32)` and the emulator log showed system-server/GMS death; no emulator data was wiped. Rev2 will rebuild and visually inspect the final output and record the emulator limitation if it persists.

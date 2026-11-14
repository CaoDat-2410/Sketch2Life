# FEAT-069 — Leader review UI/UX remediation

## Current approved work — Rev8 full audit and visual polish

The owner approved a full audit of the five primary `UI_Project/` workspaces against both leader Rev38 folders, the leader review action items, current source/API evidence, and FEAT-063 SRS v2.5-draft. Rev8 keeps all flows as local fixtures, corrects Parent to the canonical SRS order (idea/transcript before subject/context review), defers lesson-vs-drawing choice until the post-image review, removes the sample-drawing action, and softens the colors across Parent and web. See `plan/PLAN_REV8_FULL_UI_AUDIT_AND_POLISH.md` and `evidence/notes/REV8_FULL_AUDIT_AND_EXECUTION_20261114.md`.

The review confirms every Rev38 ID P01–P12, T01–T07, M01–M02, A01–A02 and UI01–UI09 has a reachable mockup or a documented local-only state. This is not 100% formal leader/API sign-off: activity timing conflicts with the leader review, gender has no canonical contract, and full Parent story/AI plus some role APIs are not available in the delivery branch. Parent remains the Android WebView experience; staff roles and the unified portal remain web. Settings remains only on Family Profile and the Parent Home child card remains absent.

## Prior implementation baseline — Rev7 complete mockup pass

The owner approved a whole-project UI mockup completion pass for `UI_Project/` using the Rev38 leader folders as the visual/flow reference. Parent is the mobile Android WebView experience; Teacher, School Manager, Platform Admin and the unified role portal are web workspaces. Rev7 adds local-only sample transitions across P01–P12, T01–T07, M01–M02, A01–A02 and shared UI01–UI09, plus responsive spacing for the Parent profile actions and narrow web workflow rails. No API/auth/backend/persistence behavior is connected. See `plan/PLAN_REV7_ALL_UI_MOCKUP_FLOWS.md`, `evidence/notes/EXECUTION.md` and `status/STATUS.md`.

The prototype follows the owner-requested Rev38 Parent order (capture → subject check → idea/context → script) even though FEAT-063 SRS v2.5-draft §5.1 has a different order. This is a visual mockup choice, not a signed product requirement; the SRS stays unchanged and the conflict remains open. Gender, AI/transcription/job/playback/quota/payment values remain fixture states. APK packaging is verified; no Android device is currently attached to ADB for runtime installation.

- **Current review:** Rev38 screen/component references were compared with current `UI_Project/` source and canonical FEAT-063 SRS v2.5-draft. The review result is **partial alignment, not full flow parity**; see `evidence/notes/REV38_FLOW_ALIGNMENT_20261114.md`. Rev38 is generated visual proposal material, not an approved contract.
- **Rev6 home adjustment:** The redundant “Đang dùng hồ sơ” summary was removed from Parent home. Child selection remains in the story-start flow and Family Profile. The five-workspace build passed; the local Parent preview was reopened and confirmed the card is absent while “Bắt đầu kể” and primary navigation remain. See `plan/PLAN_REV6_PARENT_HOME.md` and `evidence/notes/EXECUTION.md`.

- **State:** COMPLETE under approved Plan Rev4 UI-only clarification. Rev1–Rev3 are historical publications. Rev4 removes conditional API/auth calls added in Rev3 and aligns UI behavior with the leader disposition; published as `11294211911506a7dae73a5ab78aee0bb51311f0` to `origin/FE_UI_Project_Ver2`.
- **Branch:** `FE_UI_Project_Ver2`.
- **Goal:** Close the leader-review UI gaps that can be implemented without changing current product requirements or inventing backend behavior.
- **Authority:** `docs/context/SRS_AUTHORITY.md`; canonical working requirements are FEAT-063 SRS v2.5-draft, still awaiting owner sign-off.
- **Review input:** owner-provided local Codex attachment containing the leader transcript. The source stays local and is treated as feedback to reconcile, not as a replacement for current SRS/API contracts.
- **Current implementation:** API/source records are used only to understand business concepts and role boundaries. Parent, Teacher, School Manager, and Platform Admin remain labeled UI previews; none of these UI workspaces invokes the backend client or auth bridge.
- **UI source selection:** The user confirmed `UI_Project/` is the primary UI/UX to update and that top-level `apps/` contains legacy UI outside this handoff. Rev2 implementation and run instructions target only `UI_Project/` workspaces.
- **Parent mobile entry:** `UI_Project/parent-android/apps/mobile` is the Android APK host; `ParentWebPreview` loads the bundled `UI_Project/parent-ui` page. The separate `parent-android/apps/ui-mobile` workspace is not the target for this review task.
- **Latest API comparison:** A read-only audit of the permitted newer backend source `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e86826447d975ef2757aa1fefdc876c8c` found Parent profile/story and AI routes absent from the delivery baseline `FE_UI_Project_Ver2@ae2a8c8165aa1d11b62a7005a9e28d8c0ea8c046`. Treat those newer routes as future source context only; the deliverable labels them unavailable unless mounted in the branch teammates clone.

## Rev5 preview completion — current scope

The owner approved `plan/PLAN_REV5_PREVIEW_COMPLETION.md` (SHA-256 `F49F00D71E5E0D84B2EA695A1BB63010DA2E82E8A8FAC356542BDA145279262A`). Continue to treat APIs as business-flow references only. Parent now demonstrates the post-capture lesson-mismatch choice, editable offline transcript fixture, generic topic/difficulty drawing guide, and the user-requested gender field in profile and child selection. Teacher Dashboard counts are derived only from local lesson-summary and assignment fixture rows shaped after the reviewed source contracts; no analytics endpoint is claimed.

The gender field is explicitly UI-only and session-local because canonical FEAT-063 SRS v2.5-draft and the reviewed API contracts do not define it. Mismatch analysis, speech transcription, drawing-guide content and all Teacher Dashboard values remain fixtures. No API, auth, AI, ASR, schema, backend, or SRS behavior is changed. `UI_Project/parent-android/apps/mobile` continues to package the canonical `UI_Project/parent-ui` WebView.

## Rev4 current UI-only scope — historical

The owner clarified that the deliverable is the leader-requested UI/UX and that API details are business-flow reference only. The exact approved plan and hash are in `plan/PLAN_REV4_UI_ONLY.md` and both approval registers. Rev4 shows Parent Settings only on the Family Profile page, removes the unsupported gender field, and makes lesson activities available after the story preview instead of during story setup. Parent video generation remains a clearly labeled preview state. Teacher, School Manager, and Platform Admin remain role-specific web previews with local demonstration data and no API/auth calls.

## Rev3 historical implementation (superseded by Rev4)

Plan Rev3 and its Parent Library addendum were approved and published historically; Rev4 supersedes their API-wiring behavior for the current deliverable. Rev3 briefly added conditional Parent Lesson Library/invitation reads and Teacher/Manager reads when an auth bridge was injected. Rev4 removes those calls at the owner's clarification that API/source details are business-flow reference only. The Rev3 source-to-route record remains in `evidence/notes/API_UI_CROSSWALK_REV3.md` for historical traceability, not as current runtime behavior.

This frontend wiring does not establish that the team can log in end-to-end: the client references `GET /api/auth/v1/me`, but the handler and bridge are not present in this checkout. No API calls or writes were made during implementation or review. The exact route, branch and screen mapping is recorded in `evidence/notes/API_UI_CROSSWALK_REV3.md`.

## Prior approved scope (historical Rev2)

- Make Parent lesson selection visible in the story setup flow, clearly distinguish public system lessons from school/teacher-shared lessons, and retain in-place details.
- Improve the optional pre-capture line-sketch preview into a topic-aware, step-by-step guide while clearly identifying it as static until the approved AI route is mounted.
- Keep lesson story direction after capture/subject review; simplify audio-related copy while preserving editable adult review and accurately disclosing that speech recognition is not connected.
- Replace the full-screen context-selection presentation with a compact confirmation dialog while retaining the adult context review required by FR-P-06.
- Reduce Parent home height and keep the center create action immediately visible; retain global settings and existing bottom navigation.
- Improve Teacher web contrast and clarify the class → lesson → session presentation flow. Keep the sample-video workflow distinct from the class occurrence.
- Update feature evidence, decisions, status, and the root source register. Build/visually inspect affected outputs, run the required repository security validator, and publish a normal commit to the previously authorized `origin/FE_UI_Project_Ver2` target if it remains fast-forwardable.

## Out of scope / open product decisions

- Do not move Parent outdoor activities before playable video; FR-P-05 and FR-PL-16 expressly put them after video.
- Do not persist the UI-only gender field or represent it as a canonical product/API field unless FEAT-063 SRS/data contracts are formally reconciled.
- Do not represent the mismatch modal or transcript sample as live image analysis/ASR. Their preview fixture behavior is authorized only for UI review.
- Do not claim live speech-to-text, AI line sketch, teacher dashboard data, or generated “Show Slide” output when the corresponding mounted authenticated API and runtime identity context are unavailable.
- Do not change backend/API/schema/auth/provider/SRS, run AI/provider requests, send writes to a shared backend, or modify the legacy Child Expo workspace.
- No generated bitmap assets are in scope. Use existing approved assets and code-native layout/illustration only.

## Prior progress record (historical Rev1–Rev3)

Rev1 and Rev2 implementation/publication are complete. The user has explicitly authorized the API-aligned frontend work under Plan Rev3. Rev3 preserves the leader-review prototype behaviors from Rev2 where already approved, adds limited conditional API-backed read views for current mounted routes, and does not modify the unsigned canonical SRS or backend/schema/auth/API contracts. Any Rev2 behavior that conflicts with the SRS or lacks a mounted API remains visibly preview-only and is tracked as an open decision.

The Rev1 builds passed and its screenshots are in `evidence/`. The supplied emulator could not install the rebuilt APK because Android's Package Manager returned `Failure calling service package: Broken pipe (32)` and the emulator log showed system-server/GMS death; no emulator data was wiped. Rev2 will rebuild and visually inspect the final output and record the emulator limitation if it persists.

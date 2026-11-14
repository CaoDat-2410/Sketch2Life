# Feature decisions

## D-069-20 — Workflow actions must show named local outcomes

Under Plan Rev9, a primary preview action must either open its named next screen, produce a visible local result with a return/continuation route, or explain why it is read-only/blocked and how to return. Generic “next step” dialogs are not used for unknown action types. Teacher draft editing updates only that Teacher preview row; Teacher-to-Manager submission remains explicitly disconnected because the role previews have independent fixture state. This adds no API, auth, persistence, or product contract behavior.

## D-069-18 — Rev8 follows canonical Parent order and stays fixture-only

Under Plan Rev8, FEAT-063 SRS v2.5-draft §5.1 is the working authority over the generated Rev38 sequence. Parent now captures → accepts idea/voice input → confirms the suggested subject → reviews minimum context and selects lesson-vs-drawing direction → confirms script. The mismatch choice only appears after the captured-image mock result. This supersedes D-069-16's Rev38 Parent order for the current prototype, without changing the unsigned SRS. All UI workspaces remain local previews; API contracts inform the screen shape, but no API/auth/network call or persistent data action is added.

## D-069-19 — Rev38 color direction is a calm UI proposal

Apply a dark readable blue primary, muted yellow accent and mint support colors with softer neutral surfaces and visible keyboard focus across Parent and staff web previews. Rev38 tokens guide this UI pass only; they are not approved production design tokens. Preserve existing role/workflow structure and reserve danger colors for danger/error states.

## D-069-16 — Whole-project Rev38 mockup pass stays fixture-only

The owner asked for complete UI mockup flows across the project, with sample values that can later be replaced by approved API data without redesigning screens. Implement Parent P01–P12 as the Android WebView UI and the three staff roles plus the shared sign-in portal as web previews. Use Rev38 for the prototype's visual flow, but keep FEAT-063 SRS v2.5-draft authoritative and unsigned; the Parent subject/idea ordering conflict is documented rather than changing the SRS. No API/auth/network, upload, payment, AI, or persistent data behavior is in scope.

## D-069-17 — Small-screen workflow clarity

Role workflow steps and preview boundary notes must stay readable in a narrow viewport. At widths up to 560px, show the step rail as a compact two-column grid and stack explanatory notes, avoiding a clipped sideways step rail. The wide web workspaces keep their existing layout.

## D-069-14 — Parent home selected-profile summary

The owner requested removing the “Đang dùng hồ sơ” summary from Parent home because the child is selected when starting a story. Remove only that duplicate home card; preserve child selection in story setup and Family Profile. Do not add a global home profile card back while reviewing Rev38. Rev6 implementation and browser check are recorded in `evidence/notes/EXECUTION.md`.

## D-069-15 — Rev38 references are proposals; audit gaps stay explicit

Use the leader-provided Rev38 screen/component folders as visual and flow review references, not as approved product/API contracts. Current product target remains FEAT-063 SRS v2.5-draft, unsigned. The read-only comparison found partial alignment, including a Parent idea/subject ordering conflict that must remain open; do not silently copy Rev38 or describe fixture states as connected capabilities. See `evidence/notes/REV38_FLOW_ALIGNMENT_20261114.md`.

## D-069-01 — Canonical product requirements

Use FEAT-063 SRS v2.5-draft as the working target. Leader transcript items that conflict with it remain open owner questions; do not silently change activity order, child-profile data, or AI flow contracts.

## D-069-02 — Parent transcript and AI guide truthfulness

Keep adult transcript editing/review while removing redundant instruction copy. Do not imply ASR or line-sketch AI is connected. A code-native static guide may be topic-aware but must not use child profile/media.

## D-069-03 — Context confirmation

Use a compact confirmation dialog in place of a separate context-selection page. The adult still reviews and confirms the allowed context snapshot before story generation, as required by FR-P-06.

## D-069-04 — API data boundary

Teacher role screens remain preview-only until an authenticated principal and organization context can be resolved through a supported bridge and mounted endpoint. Do not seed tenant IDs or claim fixture counts came from backend.

## D-069-05 — Rev2 leader review prototype scope

The user explicitly approved completing all remaining leader-review UI items under Plan Rev2. For reviewability, the Parent pre-video activity sequence and local gender control may be shown in preview UI even though they differ from or are absent from the canonical SRS/API. Keep FEAT-063 SRS v2.5-draft unchanged, label simulated AI/data states honestly, preserve the required adult context confirmation, and record these product decisions as unresolved pending formal owner/SRS sign-off.

## D-069-06 — UI source boundary and current-branch API availability

The user confirmed that `UI_Project/` is the project's primary UI/UX and that the top-level `apps/` tree is legacy UI that must not be used for this handoff. Keep the approved Parent Android/WebView and three-role web workspaces under `UI_Project/` as the implementation and run targets. Do not copy, launch, or register top-level `apps/` UI workspaces as part of this feature. A read-only comparison against the permitted newer backend source `origin/feature/feat063-m2-parent-teacher-foundation` at `5c07c94e` showed Parent profile/story routers there that are absent from the delivery branch `FE_UI_Project_Ver2` at `2518dc07`; only routes mounted in the delivery branch may be described as available to a teammate cloning this branch. Keep other Parent operations preview-only until their routes are present and authenticated in the delivery branch.

## D-069-07 — Parent APK presentation target

The Parent UI shown in the browser is the bundle rendered inside `UI_Project/parent-android/apps/mobile` by `ParentWebPreview`. Keep `UI_Project/parent-ui` as the canonical Parent UI implementation and ensure the Android debug APK packages that same bundle. The separate `UI_Project/parent-android/apps/ui-mobile` workspace is not the target of this leader-review task.

## D-069-08 — Rev3 conditional API reads and truth states

The approved Rev3 scope connects only current, mounted read contracts that can be safely scoped by an injected Firebase token bridge and organization ID: Teacher Lesson Library lessons, Teacher BE1 assignments, and School Manager BE1 classes. Teacher/Manager dashboard measures are derived from those returned rows, not from a dedicated analytics endpoint. Without auth/config, retain labeled preview data; with auth/config but missing organization context or failed reads, show unavailable/error states and do not replace API results with fixtures. Keep Teacher/Manager writes, Parent operations, Platform Admin queue, and all routes present only on the read-only comparison branch preview-only. Do not claim a full live workflow or connected login until the delivery branch has a supported identity bridge/handler and missing contracts.

## D-069-09 — Rev4 UI-only scope supersedes API wiring

The owner clarified that APIs are reference material for understanding business flow and are not to be joined to the UI. Rev4 removes the conditional API/auth calls added in Rev3; all four role workspaces remain visibly labeled previews with local demonstration data. Follow the leader disposition for Parent: show activities after the story/video preview, omit unsupported child gender, and show the Settings entry only on the Family Profile page. Do not modify backend/API/auth/schema/SRS or send requests to a service.

## D-069-10 — Rev5 post-capture mismatch preview

The owner directly requested a Parent flow for the leader's drawing-versus-lesson mismatch feedback. Show the choice modal when the local post-capture fixture reports a mismatch, and carry the chosen direction into story review. This is a deterministic UI fixture, not image analysis or an API decision; FEAT-063 SRS remains unchanged.

## D-069-11 — Rev5 gender display is session-local UI only

The owner directly requested gender in the Parent profile and child picker. Include an optional local field for UI review and mark the values as sample/session-only. The current canonical SRS/API does not define this attribute; do not persist it or treat it as an approved product data model.

## D-069-12 — Rev5 voice and drawing-guide fixtures

Keep the Parent audio workflow editable and reviewable, with a plainly labeled offline transcript sample and recoverable empty/error states. The three-step drawing guide may vary only by generic topic and selected difficulty. Do not request microphone permission during visual review or call ASR, AI or other services.

## D-069-13 — Rev5 Teacher Dashboard contract-shaped preview

Use local fixture rows matching the concepts in the reviewed lesson summary and active assignment contracts. Dashboard counts must be traceable to those rows; do not show topic analytics or imply a live connection. Empty/unavailable UI may be shown as a fallback, but the present in-repo sample is ready-state only.

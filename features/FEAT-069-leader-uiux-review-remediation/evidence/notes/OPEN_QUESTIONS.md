# FEAT-069 remaining UI/product questions

## Rev8 current disposition — full flow audit, 2026-11-14

- Current working SRS v2.5-draft §5.1 now governs the Parent mockup sequence: capture → idea/transcript → subject review → minimum context and post-image direction choice → script. The prior Rev7 prototype followed the generated Rev38 subject-before-idea order; Rev8 supersedes that visual choice without changing the SRS.
- The leader review's request to select outdoor activity before video conflicts with SRS §5.1, which places configured activities after playable video. Current UI keeps the SRS order pending owner/leader resolution; do not claim full leader sign-off.
- Parent image analysis/transcription/job/video, profile CRUD/gender, quotas and all role mutations/metrics remain fixtures or unavailable states. Current contracts support parts of Lesson Library, import/review, access grants, moderation updates and BE1 organization/class operations, but do not establish the entire workflow as durable API behavior.
- Gender remains a local-only value because no canonical data/API contract was found. Parent Settings remains only under Family Profile. No sample drawing button is present.
- The visual review covers browser previews; APK debug packaging passes, but ADB could not start its daemon in this environment, so emulator runtime was not verified.
- Formal leader acceptance and SRS v2.5 owner sign-off remain outstanding. See `REV8_FULL_AUDIT_AND_EXECUTION_20261114.md` for the screen/API crosswalk and build evidence.

## Rev7 current disposition — mockup completion, 2026-11-14

- The UI-only prototype now follows the owner-requested Rev38 Parent order: prepare/optional guide → capture → adult subject review → idea/transcript and context confirmation → script review → local job stages → sample video → activities after the preview is marked finished. This differs from FEAT-063 SRS v2.5-draft §5.1. The order is implemented only for the mockup; product ownership still needs to resolve/sign off the SRS conflict before the flow is treated as canonical.
- Rev38 Parent Library now has a child-profile switcher; the duplicate selected-child card remains absent from Home per the owner's request. Settings remains reachable only in Family Profile. Gender shows in profile and child selection as session-only fixture data, not as an approved data/API field.
- Teacher document import now shows upload → editable extraction fields → adult confirmation using local sample values. The selected file is not parsed or uploaded. Teacher lesson/session/sample-video paths, Manager publication/organization decisions, and Admin moderation/operations transitions are local previews.
- Quota counts and MoMo/VNPAY choices are display-only; they do not launch a payment flow. Job stages and video playback are illustrative. No AI/ASR/image-analysis, auth, persistence, external URL, or API call is made.
- Rev38 tokens/role navigation and generated screens remain visual proposals. Formal leader acceptance and SRS v2.5-draft owner sign-off remain outside this implementation; record remaining feedback separately instead of claiming approval.

## Rev38 comparison questions — 2026-11-14

- Parent sequence in the current preview shows subject review before idea/transcript/context. Canonical FEAT-063 v2.5-draft §5.1 orders capture → idea/transcript → subject review → context confirmation, while Rev38 P04/P05 visually proposes the former order. This is an unresolved flow conflict; retain the canonical SRS sequence as the working target until the owner formally resolves/signs off the requirement.
- Rev38 P01 places a child-selection entry in Lesson Library. The owner's latest request removes the duplicate selected-child card from home, while current selection is available at story start and Family Profile. Decide separately whether Library also needs a child switcher; do not restore the home card as a workaround.
- Rev38 P03 combines guide and active drawing; current guide is a separate static pre-capture screen. Confirm interaction placement before changing the story-start workflow.
- Rev38 P07/P08 show resumable job stages and playable video; current UI honestly presents unavailable preview states. These cannot be made operational by UI-only work without approved contracts/runtime.
- Rev38 T03/M01 propose extraction-field review and checklist-gated publication. Current UI does not fully represent those steps. Future implementation should first scope the fixture-only visual states and verify them against current SRS; no API connection is implied.
- Rev38 design tokens, gender/profile semantics, quota/payment figures, role navigation scope, and Admin operational controls remain proposal/open questions. The v2.5-draft SRS stays authoritative and unsigned.

## Rev5 current disposition

- Parent now includes an optional gender control and shows its value in the child picker because the owner explicitly requested it. FEAT-063 SRS v2.5-draft and the reviewed API contracts do not define gender. It is a local UI preview field only; product ownership must reconcile it before persistence or handoff as a canonical profile attribute.
- Parent mismatch review uses a fixed local fixture that reports a mismatch after capture. The modal allows lesson-led or drawing-led story direction. It does not run image analysis; the actual analysis contract/state remains unspecified in the target SRS/API.
- The voice-to-text screen uses a clearly labeled sample transcript to preview transcription and adult editing. No real ASR/Whisper request was made. Actual transcription error/retry behavior is not validated against a service.
- The drawing guide is a static three-step generic-topic preview with topic and difficulty controls. It does not use a child's profile/artwork or call a guide-generation API.
- Teacher Dashboard uses local lesson-summary and active-assignment fixtures shaped after read-only source contracts. The five workspaces remain disconnected from API/auth; dashboard metrics are list-derived counts, not live backend/analytics data.
- The user-requested Settings visibility boundary remains: Parent Settings is reachable only from the Family Profile page.
- FEAT-063 SRS v2.5-draft is still unsigned. Rev5 approves these preview surfaces only and does not amend SRS, API, or data models.

## Current Rev4 disposition

- Parent lesson activities appear after the story/video preview, following the leader review disposition and FEAT-063 SRS. The earlier Rev2 pre-video prototype is superseded.
- The unsupported child gender field has been removed from Parent profile UI.
- Parent Settings is available only on the Family Profile page.
- The four role workspaces are UI previews. Story/video generation, ASR, image analysis, lesson persistence, role writes, and operational metrics remain sample/unavailable states. Rev4 intentionally makes no API/auth connection, per the owner's clarification.
- FEAT-063 SRS v2.5-draft remains unsigned. Any future change to product behavior requires the owner to resolve/sign off the requirement separately.
- The final debug APK packages successfully. Installation/runtime on the supplied emulator was not repeated in Rev4; earlier attempts stalled at Android Package Manager. No emulator wipe/reset was performed.

## Historical Rev3 API wiring

Commit `be8aa646` briefly added conditional Parent Lesson Library, Teacher lesson/assignment, and Manager class reads. The owner clarified that API/source details are reference material only. Rev4 reverted those UI calls; the Rev3 API crosswalk and publication note remain historical evidence and do not describe current UI behavior.

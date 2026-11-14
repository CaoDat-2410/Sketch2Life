# FEAT-069 remaining UI/product questions

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

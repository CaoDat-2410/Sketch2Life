# FEAT-069 remaining UI/product questions

## Current Rev4 disposition

- Parent lesson activities appear after the story/video preview, following the leader review disposition and FEAT-063 SRS. The earlier Rev2 pre-video prototype is superseded.
- The unsupported child gender field has been removed from Parent profile UI.
- Parent Settings is available only on the Family Profile page.
- The four role workspaces are UI previews. Story/video generation, ASR, image analysis, lesson persistence, role writes, and operational metrics remain sample/unavailable states. Rev4 intentionally makes no API/auth connection, per the owner's clarification.
- FEAT-063 SRS v2.5-draft remains unsigned. Any future change to product behavior requires the owner to resolve/sign off the requirement separately.
- The final debug APK packages successfully. Installation/runtime on the supplied emulator was not repeated in Rev4; earlier attempts stalled at Android Package Manager. No emulator wipe/reset was performed.

## Historical Rev3 API wiring

Commit `be8aa646` briefly added conditional Parent Lesson Library, Teacher lesson/assignment, and Manager class reads. The owner clarified that API/source details are reference material only. Rev4 reverted those UI calls; the Rev3 API crosswalk and publication note remain historical evidence and do not describe current UI behavior.

# FEAT-034 status

- Status: IN_PROGRESS
- Plan revision: 1
- Implementation status: IN_PROGRESS
- Current milestone: Core implementation and automated verification complete; native-device verification and qualified catalog review remain.
- Implemented: bounded mobile image preflight/normalization with preserved source/derivative provenance; strict backend image content/MIME/animation/admission checks and typed diagnostics; deterministic giraffe aliases; corrected animal-family topic ownership; complete-list-first async top-three AI ranking; explicit empty-result diagnostics; all 300 recommendation cards now parse/render; feature-local full catalog report.
- Verification: FEAT-034 focused backend suite passed (54 tests); full backend suite passed with an isolated pytest temp directory; mobile TypeScript, UI-copy validation, and web export passed; Ruff passed; repository security validator passed. The host's default pytest cache location still emits an Access Denied warning, but does not fail the isolated test run.
- Catalog gate: 300/300 cards render; automated report records 77 mapping corrections and 223 `NEEDS_REVIEW` rows requiring qualified Montessori review. `ANIMAL_GENERIC` currently has four cards for age 3–6; no activity was invented to fill the measured gap.
- Device gate: Android debug APK rebuilt with Java 21, including the new native image module; installation and startup on `Pixel_10_2` passed. Native Metro entry returns 200 and app displays onboarding without observed startup errors. Backend health is 200 and ADB reverse is active on 8081/8000. Native picker-to-recommendation flow remains untested; WebP/HEIC/HEIF are not yet runtime-certified. See `evidence/notes/RUNTIME_STARTUP_20260930.md` for the correction to the earlier Metro diagnosis.
- Publication: The owner explicitly requested commit and push on 2026-09-30. Publish only FEAT-034 implementation, source references, and feature records; preserve unrelated worktree changes.
- Next gate: capture the Android synthetic-fixture flow and obtain qualified Montessori review for unresolved catalog mappings/content gaps before claiming all plan acceptance criteria complete.
# Follow-up — 2026-09-30

Publication authorized by the owner's explicit “commit and pussh” instruction. Publish only the preview/mask fixes, their tests and FEAT-034 records; leave unrelated SRS/story/report edits uncommitted. External Lightning update/restart is not performed by Git publication.

Backend early mask admission added under explicit “continue”; 65 focused tests, Ruff and repository security passed. Backend restarted and health returned 200; in-memory sessions reset. Emulator/Metro remain connected; app reload not performed because tool policy blocked the restart attempt. External worker deployment and fresh user-flow validation remain pending; no new commit/push. Evidence: `../evidence/notes/MASK_BACKEND_BOUNDARY_20260930.md`.

Three-card preview with “Xem thêm” implemented and mobile types/copy verified. SAM/Pixi area ceiling mismatch corrected; six SAM runtime tests and Ruff passed. External Lightning worker update/restart and fresh-session end-to-end segmentation are pending, not claimed complete. Evidence: `../evidence/notes/THREE_CARD_PREVIEW_MASK_LIMIT_20260930.md`.

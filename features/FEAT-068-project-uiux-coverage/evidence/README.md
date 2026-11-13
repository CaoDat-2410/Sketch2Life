# FEAT-068 evidence index

Verification captured for the approved scope in `plan/PLAN.md`. The UI is a handoff-ready preview where the current source does not expose the authenticated product API; this evidence does not imply backend persistence or AI/video completion.

| Evidence | Acceptance criteria | What it establishes | Limitation |
|---|---|---|---|
| `notes/API_UI_CROSSWALK.md` | AC2–AC6 | Source-mounted routes, client methods, UI call sites, and truthful preview/unavailable states | Static source review; no backend writes or live authentication attempted |
| `notes/LEADER_REVIEW_DISPOSITION.md` | AC2–AC5, AC9 | Disposition of the leader review against current SRS/API authority | DOCX itself remains local and is not published |
| `notes/EXECUTION.md` | AC1, AC3–AC8 | Commands, successful build/typecheck/APK results, emulator flow, screenshots and known review limits | Web screenshots cover role dashboards; no full browser walkthrough of every web dialog or narrow viewport is claimed |
| `screenshots/parent-android-home-final.png` | AC1, AC2 | Final Parent home on the Android emulator | Synthetic preview content |
| `screenshots/parent-android-auth-preview.png` | AC2, AC6 | Parent sign-in preview with the unconnected-auth notice | Authentication itself is unavailable in the current app/API composition |
| `screenshots/parent-android-story-entry-final.png` | AC1, AC2 | Story entry and the two-profile count | Synthetic profiles |
| `screenshots/parent-android-capture-empty-final.png`, `parent-android-after-picker-done.png` | AC1, AC2 | Empty capture state and selected-file preview state | Test image was a repository UI screenshot, not child media; selection was local to this emulator session |
| `screenshots/parent-android-subject-review.png`, `parent-android-context-review.png`, `parent-android-script-preview.png`, `parent-android-video-unavailable.png` | AC1, AC2, AC6 | The ordered review flow and honest unavailable-video endpoint | AI, persistence and playback are not connected |
| `screenshots/teacher-web-dashboard.png`, `school-manager-web-dashboard.png`, `platform-admin-web-dashboard.png` | AC3–AC5, AC7 | Distinct web-role dashboards rendered from the current workspaces | Dashboard-only captures; full route interactions are additionally assessed from source, not claimed as end-to-end API behavior |
| `status/STATUS.md`, `CONTEXT.md`, `DECISIONS.md`, `docs/context/SOURCE_REGISTER.md` | AC9 | Scope, decisions, source authority and milestone state | Publication fields are updated after push |
| `notes/PUBLICATION.md` | AC8–AC9 | Security validation and final branch/commit/push record | Publication fields are updated after the normal push |

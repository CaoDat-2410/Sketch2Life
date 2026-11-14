# FEAT-069 Plan Rev13 — Full Leader Review Completion & UI/UX Pro Max Polish

## Objective

Complete every remaining actionable item from the Leader's UI/UX review and meeting transcript inside `UI_Project/` (`parent-ui`, `parent-android` WebView assets note, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`, and `shared/`), and apply the persona-tailored `ui-ux-pro-max-skill` visual/interaction quality standards while preserving the approved forest-green/sage and warm-storybook-paper palette from Rev11–Rev12 and keeping all UI-only local fixture boundaries honest.

## Scope

In scope (`UI_Project/` + `features/FEAT-069-leader-uiux-review-remediation/` governance records):
1. **Parent UI (`UI_Project/parent-ui/`):**
   - **Global Settings Access:** Make the Discord-style Settings gear accessible across Home (in top-right header beside notifications), all `PageHeader` subpages (`history`, `library`, `profile`, `child-detail`, `lesson-detail`, `delivery-detail`, `run-detail`, `notifications`, etc.), and in-flow top header without overlapping titles.
   - **Remove Redundant Context Confirmation Blocker:** Remove the manual `Rà soát ngữ cảnh` checkbox gate (`contextConfirmed`) from the `review` step and footer Next button; automatically inherit the selected child profile (`selectedChild`) and show only compact automatic context info + post-capture Story Direction choice (`scriptFollowing` / mismatch modal) when a lesson is selected.
   - **Pre-Video Outdoor Activity Selection:** Bring Lesson Outdoor Activities ("Hoạt động cùng bé") BEFORE video generation inside `script` (`Duyệt kịch bản & hoạt động`), letting parents select/switch the attached outdoor activity before generating the video preview and reflecting that selection inside the script and post-video `ready` view without locking activities behind `videoPreviewFinished`.
   - **Audio / Voice Step Cleanup:** Remove verbose helper banners (`audio-transcription-state` confirmation walls and cluttered audio-limit prose before errors occur), keeping voice transcript flowing directly into the story idea textarea for immediate parent review/editing, with validation errors surfaced concisely via modal.
   - **UX Pro Max Mobile Craft:** Unify leftover Rev7 blue tokens (`#3479bd`) in Parent styles into the calm forest-green/sage/gold family, raise undersized micro-text (`9px–10px`) to comfortable mobile reading sizes, enforce `>= 44px` touch targets, unify `Escape` key dismissal across modals/sheets, and respect `prefers-reduced-motion`.
2. **Web Workspaces (`UI_Project/shared/`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`):**
   - **Contrast & Visual Comfort ("Chống mờ chữ / mỏi mắt"):** Audit and lift low-contrast muted/secondary text, placeholders, captions, and breadcrumbs to WCAG AA `>= 4.5:1` on cream/sage surfaces.
   - **UX Pro Max Persona Polish (`shared/rev13ProMax.css` + clean TSX refinements if needed):** Raise micro-labels to legible desktop sizes, calm overly repetitive warning boxes into clean scannable pills/notes while retaining honest fixture boundaries, refine spacing/hierarchy on Teacher Dashboard, Lesson Detail Modal, Classroom Presentation Session (`TeacherSessionWorkspace`), School Manager Publication & Class Consoles, Platform Admin Catalog/Moderation/Billing Workbenches, and the Unified Web Entry Portal.
3. **Verification & Documentation:**
   - Run `npm --prefix UI_Project run build` across all 5 workspaces cleanly.
   - Run `npm --prefix UI_Project run dev` briefly and inspect real rendered views across desktop (~1280px) and mobile (`375x812`) with zero layout breakage or console errors.
   - Run `git diff --check` and `python tools/validate_repository_security.py`.
   - Update `FEAT-069` `CONTEXT.md`, `DECISIONS.md`, `OPEN_QUESTIONS.md`, `status/STATUS.md`, and `evidence/notes/REV13_LEADER_UX_PRO_MAX_20261114.md`.

## Exclusions

- No edits to legacy `apps/`, `child-experience/`, backend services, database schemas, or API contracts.
- No network/API integration, real authentication, payment calls, AI/ASR provider calls, or real child data.
- No edits to `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (`v2.5-draft` remains canonical working SRS; explicit Leader overrides are documented as open items in `FEAT-069`).
- No generated bitmap assets or git history rewrites / unrequested force-pushes.

## Acceptance Criteria

- **AC1:** Parent UI exposes Settings modal from Home, Library, History, Profile, subpages, and story flow header via a crisp `>= 44px` gear button without text overlap.
- **AC2:** Parent UI `review` step has no blocking `contextConfirmed` checkbox or manual context confirmation gate; child profile context applies automatically.
- **AC3:** When a lesson is chosen in Parent UI, Outdoor Activities ("Hoạt động cùng bé") are selectable in `script` step BEFORE triggering Video generation (`generating`), reflected in the script preview, and accessible un-locked in `ready`.
- **AC4:** Parent UI `idea` audio step displays transcript directly inside `#story-idea` without cluttered post-transcript confirmation banners or verbose upload limit instructions, while preserving modal error dialogs.
- **AC5:** Parent UI removes leftover Rev7 blue tokens in `library-quota-meter`, `history-range-filter`, and `parent-job-timeline`, keeping full Rev11–Rev12 green + warm paper + gold harmony.
- **AC6:** Parent UI & Web Workspaces satisfy `ui-ux-pro-max` checks: WCAG AA muted-text contrast (`>= 4.5:1`), bumped micro-copy legibility, visible `3px` keyboard focus rings, `Escape` dismissal for modals, responsive 375px/1280px layouts with zero horizontal overflow, and `prefers-reduced-motion` safety.
- **AC7:** All 5 workspaces build cleanly (`npm --prefix UI_Project run build`), rendered browser checks pass with evidence screenshots, `git diff --check` is clean, and `python tools/validate_repository_security.py` exits `0`.
- **AC8:** Explicit governance decisions & SRS `v2.5-draft` vs Leader conflict notes (pre-video outdoor activity ordering, child gender field, omitted context tick, Settings scope) are updated in `FEAT-069` docs without claiming backend readiness or formal SRS sign-off.

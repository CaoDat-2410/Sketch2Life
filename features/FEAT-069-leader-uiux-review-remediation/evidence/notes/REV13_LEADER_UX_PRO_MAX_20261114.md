# Rev13 — Full Leader UI/UX Remediation & UX Pro Max Polish

Date: 2026-11-14 (Asia/Saigon). Approved plan: `plan/PLAN_REV13_LEADER_FULL_UX_PRO_MAX.md`, SHA-256 `EF94D11CE9A4FA038E2ABEB42DAD6119E9A920E6D39AF0EA2B75F5F0E6C4B53A`.

## Scope and files modified

Only active UI workspaces under `UI_Project/` were modified:
- `UI_Project/parent-ui/src/App.tsx`
- `UI_Project/parent-ui/src/main.tsx`
- `UI_Project/parent-ui/src/rev13ProMax.css`
- `UI_Project/shared/rev13ProMax.css`
- `UI_Project/shared/webWorkspace.tsx`
- `UI_Project/teacher-ui/src/main.tsx`
- `UI_Project/school-manager-ui/src/main.tsx`
- `UI_Project/platform-admin-ui/src/main.tsx`
- `UI_Project/web-ui/src/main.tsx`

Legacy `apps/`, backend APIs, authentication, database schemas, and canonical FEAT-063 SRS `v2.5-draft` remain untouched.

## Implemented changes

1. **Parent flow & navigation (`UI_Project/parent-ui/`)**:
   - Replaced the blocking `contextConfirmed` review checkbox with a non-blocking `.auto-context-pill` (`Tự động theo hồ sơ <name>`) while keeping post-capture Lesson Direction choice (`scriptFollowing`) and mismatch modal.
   - Positioned outdoor activities before video generation inside `script` via `.prevideo-activity-panel` (radio selector + link to kid-view), weaving the chosen activity into scene `05`, and removed the `videoPreviewFinished` lock from post-video review/completion.
   - Exposed Discord-style global Settings via `SettingsContext` across Home header, `PageHeader` subpages (including Family Profile top-right gear), and `.flow-header__actions`, with `Escape` key closing, and removed the redundant inline Settings button inside Family Profile so the profile page focuses solely on selecting/adding child profiles.
   - Removed cluttered upload/confirmation boilerplate in the audio/voice step and streamed fixture transcription directly into `#story-idea` with compact live/error status (`audio-live-status`).
   - Replaced remaining `#3479bd` Rev7 blue tokens (`library-quota-meter`, `history-range-filter`, `parent-job-timeline`, `.pill--blue`) with coordinated `#3f7559` / `#28543e` green + `#e7f0e6` sage surfaces.
   - Fixed the center `+` bottom-navigation `"Tạo mới"` label color (`#264d3b`) so it no longer inherited white-on-cream, enforced `>=44px` touch targets, `>=11.5px` helper copy at `>=4.5:1` contrast, `prefers-reduced-motion`, and unified `<select>` single-chevron rendering (`::picker-icon` suppressed + centered alignment).
2. **Web roles & shared portal (`UI_Project/shared/` + role entrypoints)**:
   - Added `UI_Project/shared/rev13ProMax.css` after `rev8ColorSystem.css` across Teacher, School Manager, Platform Admin, and Unified Web Portal to deepen secondary/muted green ink (`--muted: #4a6054`, placeholder `#5b7165`, nav `#3a5247`), refine card boundaries (`#cedad0`), calm `.feedback-preview-note` / `.dashboard-contract-note` banners, improve Teacher Session slide-deck readability (`20px` stage titles, `44px` controls), and remove duplicate Chromium `<select>` native `▼` triangles (`::picker-icon` suppressed).
   - Updated `DetailPanel` eyebrow localization in `UI_Project/shared/webWorkspace.tsx` (`lessons` -> `CHI TIẾT GIÁO ÁN`, `classes` -> `CHI TIẾT LỚP HỌC`, `teachers` -> `CHI TIẾT GIÁO VIÊN`, `organizations` -> `CHI TIẾT TỔ CHỨC`).

## Verification

- **Production build (`npm --prefix UI_Project run build`)**: Exited `0` after final source edits (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui` built cleanly via Vite v5.4.21).
- **Repository security & diff hygiene**: `git diff --check` exited `0`; `python tools/validate_repository_security.py` returned `REPOSITORY_SECURITY_VALID` (`publishable_files_scanned=7601`, `absolute_machine_paths=absent`).
- **Live browser verification (Rev13 initial + post-polish reloads)** across all five local Vite dev servers (`http://localhost:5196/` `web-ui`, `http://localhost:5197/` `teacher-ui`, `http://localhost:5198/` `platform-admin-ui`, `http://localhost:5199/` `school-manager-ui`, `http://localhost:5200/` `parent-ui`):
  - Mobile (`375x812`): `scrollWidth === 375`, `0` uncaught console/page errors; Home & subpage Settings gear + `Escape` modal; 2-tab lesson library + `Chi tiết` modal; no sample-drawing button on Capture; post-capture mismatch choice + auto-context pill (no blocking context tick); pre-video outdoor activity selection; Profile `Giới tính` field; crisp `"Tạo mới"` dark-green FAB label and single-chevron `<select>` controls verified visually on Home, `Giáo án`, and `Sửa hồ sơ trẻ`.
  - Desktop (`1440x900`): `scrollWidth === 1440`, `0` uncaught console/page errors across `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, and `web-ui`; centered Teacher `CHI TIẾT GIÁO ÁN` modal, clean Dashboard without lower duplicate notification panel, 16:9 `Slide / Sketch` Session stage, and single-chevron `<select>` controls verified on Teacher `Buổi dạy & plan` and Web Portal role login.
- **Standalone `tsc --noEmit` note:** Raw `tsc --noEmit` is not configured with `@types/react` / CSS module declarations in the five Vite apps; Vite production builds (`npm --prefix UI_Project run build`) handle TypeScript/JSX compilation for all five workspaces.

## Open product conflicts and boundaries

- Pre-video outdoor activity timing (`script`) follows leader review feedback and still conflicts with canonical FEAT-063 SRS `v2.5-draft` §5.1 (post-video activities); the SRS stays unchanged and open for owner resolution.
- Omitting the blocking context confirmation tick and keeping the session-local UI `Giới tính` attribute also remain open against canonical `v2.5-draft` / API schemas.
- All flows remain offline preview fixtures without backend API calls, live ASR/VLM/video generation, Android APK emulator install, or automated UI tests.

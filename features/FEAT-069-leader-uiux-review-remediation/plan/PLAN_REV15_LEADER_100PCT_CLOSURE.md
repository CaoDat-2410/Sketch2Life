# FEAT-069 Plan Rev15 — 100% Leader UI/UX Checklist Closure in `UI_Project/` (UI-Only, No API)

- **Feature:** `FEAT-069-leader-uiux-review-remediation`
- **Revision:** 15
- **Date:** 2026-11-14 (Asia/Saigon)
- **Status:** Drafted under explicit owner instruction (*"giờ làm sao để thành mức đạt hết là được, nhưng nói trước là không cần nối API nhé, vì nối API là nhiệm vụ của leader sau khi check UIUX của tôi xong á, giờ bạn giúp hoàn thành 100% đi"*).

## Goal

Close every remaining UI/UX gap identified in the forensic audit of `UI_Project/` against the Leader review checklist, `origin/dev` (`c87d8008`) workflows, and `v2.5-draft` SRS so all role interfaces (`Parent`, `Teacher`, `School Manager`, `Platform Admin`, and `Unified Web Portal`) achieve complete visual consistency, cohesive step-by-step interactive preview flows, and accurate UX documentation — strictly without connecting backend APIs.

## Scope & Work Packages

1. **Parent UI (`UI_Project/parent-ui/src/App.tsx`, `UI_Project/parent-ui/src/rev13ProMax.css`):**
   - **Topic-specific Line-Sketch Guide (`case 'guide'`):** Replace the garden-only CSS primitive stage with distinct, crisp, step-reactive vector SVG illustrations for all four dropdown topics (`Khu vườn`, `Bầu trời`, `Đại dương`, `Vũ trụ`) and all three progressive drawing steps (`1/3`, `2/3`, `3/3`) and difficulty levels (`Nhẹ nhàng` / `Thêm chi tiết`). Remove dead unreachable `renderSketchGuide` screen branch (`'sketch-guide'`).
   - **Natural Mismatch / Alignment Flow (`case 'review'` & modal):** Remove exposed developer-testing toggles (`Thử trạng thái khớp`, `Thử trạng thái lệch`, `Mở hộp thoại chọn`) from the main UI card. Derive alignment/divergence cleanly from selected lesson + confirmed drawing subject (while keeping the modal trigger automatic when a selected lesson diverges from the detected drawing subject, and allowing clean one-tap switching between `'Ưu tiên mục tiêu giáo án'` and `'Ưu tiên tranh của bé'` right in the card or modal, with transparent preview-mode wording).
   - **Stale Context Copy & Residual Blue Tokens:** Update outdated manual-context wording in `renderChildDetail` and `renderPrivacy` so they accurately describe automatic profile context per current Rev13+ UX; override remaining blue classes (`.child-avatar--lavender`, `.ai-dot`, `.status-spinner`, `.guide-toggle__icon`, `.soft-card--blue`) cleanly inside `parent-ui/src/rev13ProMax.css` using the approved forest-sage-gold palette.

2. **Web Workspaces & Teacher End-to-End Session Flow (`UI_Project/shared/roleFlows.tsx`, `UI_Project/shared/webWorkspace.tsx`, `UI_Project/shared/roleFlows.css`, `UI_Project/shared/rev13ProMax.css`):**
   - **Complete Seamless Teacher Session Cockpit (`TeacherSessionWorkspace`):**
     - Align Cô Mai's assigned class scope cleanly (`Lớp Lá 1`, consistent with `TeacherDashboard`, `CollectionPage`, and updated `config.teacher.metrics` `'01 Lớp phụ trách'`).
     - Unlock all approved/assigned Teacher lessons (`Bầu trời kỳ diệu · v2.0`, `Khám phá khu vườn · v1.4`, `Hành trình của hạt mầm · v1.0`), each paired with lesson-specific activities and 3-step custom SVG line-sketch slides (`16:9` classroom stage + `Tạo lại nét bước này · preview`, `Bỏ qua slide`).
     - Render a complete 4-stage interactive session flow directly inside `#session` (`01 · Vào tiết & Show Slide / Sketch` -> `02 · Hoạt động tương tác` -> `03 · Video mẫu riêng (Chụp tranh, Ghi ý tưởng, Duyệt kịch bản & Xem trước video)` -> `04 · Chiếu & Hoàn tất`), including sample child eligibility/consent fixture confirmation (respecting SRS §5.2 no manual student picking), live temporary drawing upload preview, voice/text idea & subject confirmation, script approval, 4-stage AI progress preview, interactive video preview player with CC & Play/Pause toggle, and class playback confirmation — while retaining optional navigation links to `#occurrences` and standalone `#sample`.
   - **Zero Leftover Blue/Purple Styling:** Replace `.catalog-status--draft` pastel blue (`#eaf1ff`/`#4b6ea6`) in `UI_Project/shared/roleFlows.css` with forest-sage stone (`#ebf3ec`/`#345b43`), and convert `HeroArt` Platform Admin check-card in `UI_Project/shared/webWorkspace.tsx` from purple (`#e9e5f3`/`#d4caec`/`#69559a`) to forest-sage tokens (`#e5efd7`/`#cbe0cf`/`#2e6b53`).

3. **Design System Documentation Sync (`UI_Project/DESIGN.md`):**
   - Update `UI_Project/DESIGN.md` to reflect the approved warm forest-green/cream-gold design system, Parent 5-slot bottom bar + central `+` FAB, global Settings gear access, removed manual Context gate, pre-video outdoor activity selection, Web 3-role green palette, consolidated sidebar hubs, and honest documentation of remaining UI-vs-SRS open questions.

## Exclusions

- No backend, database, Firebase, S3, Runpod, API, schema, or authentication endpoint edits.
- No edits to `apps/` (legacy), `features/FEAT-063-.../SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (`v2.5-draft`), or `UI_Project/child-experience/`.
- No synthetic live ASR, VLM, billing, or external API calls; all flows use explicit preview fixtures inside the browser session.

## Acceptance Criteria

1. Switching Parent `Gợi ý vẽ` topics between `Khu vườn`, `Bầu trời`, `Đại dương`, and `Vũ trụ` shows distinct, step-by-step vector line sketches across all 3 steps; dead `renderSketchGuide` branch is removed.
2. Parent `review` screen shows zero raw test-toggle pills (`Thử trạng thái khớp`, `Thử trạng thái lệch`, `Mở hộp thoại chọn`), automatically triggers the direction-choice modal on subject-lesson divergence, and cleanly displays direction choices without blue color leaks.
3. Teacher `Buổi dạy` lets Cô Mai start with `Lớp Lá 1` (`01 Lớp phụ trách` matching dashboard), pick any of the 3 enabled lessons, view lesson-specific line-sketch slides, run the interactive classroom activity, and step all the way through inline sample-child eligibility confirm -> drawing upload preview -> idea/subject/script approval -> sample video preview & class playback confirm without forced exit away from `#session`.
4. Built CSS bundles under `UI_Project/*/dist/assets/*.css` and active JSX SVGs contain zero leftover `#eaf1ff`, `#4b6ea6`, `#e9e5f3`, `#d4caec`, `#69559a`, `#4e8ee2`, `#3068c1`, `#3152c4` mismatches in active UI surfaces.
5. `npm --prefix UI_Project run build` succeeds across all 5 packages (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`), live browser inspection passes on desktop (`1440x900`) and mobile (`375x812`) viewports with 0 console/page errors and 0 horizontal overflow, and `python tools/validate_repository_security.py` exits cleanly.

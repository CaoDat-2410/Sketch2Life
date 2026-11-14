# Sketch2Life UI Design System (`UI_Project/`)

Design token and interaction specification for the official `UI_Project/` frontend prototypes (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`). All views in `UI_Project/` are UI/UX prototypes with browser-local fixtures (backend APIs are not connected here).

## 1. Color Tokens (Warm Forest-Sage Storybook Palette)

| Token / Role | Parent Mobile (`parent-ui`) | Web Roles (`teacher`, `manager`, `admin`, `web-ui`) |
| --- | --- | --- |
| Primary Brand / Action | `#3f7559` -> `#28543e` (`--brand-primary`) | `#2e6b53` / `#28543e` |
| Ink / Body Text | `#1f3930` (`--ink`), `#475f53` (`--ink-soft`) | `#1b342c` (`--ink`), `#4a6054` (`--muted`) |
| Canvas / Surface | `#fbf7ea` cream, `#fffefa` card | `#eef2ee` canvas, `#fffefa` card |
| Soft Tint / Badges | `#e7f0e6` sage wash, `#eff6ef` soft banner | `#ebf3ec` draft/info wash, `#dfe8dd` borders |
| Warm Storybook Accent | `#f5d279` / `#f4c84e` gold, `#d99a58` terracotta | `#f7cb70` gold highlights |
| Error / Alert | `#964133` coral text, `#fff4ef` soft surface | `#964133` / `#fde9e5` |

High-contrast text (`WCAG AA >= 4.5:1`) and minimum `44px` touch targets are enforced across interactive buttons, nav items, filters, and modal controls (`rev13ProMax.css`).

## 2. Typography

- **Display / Headings:** `'Baloo 2'`, `'Varela Round'`, `'Fredoka'`, `'DM Sans'`, sans-serif.
- **UI Body & Controls:** `'Be Vietnam Pro'`, `'Nunito Sans'`, sans-serif (full Vietnamese diacritic legibility, tabular numbers on metrics/step indicators).

## 3. Parent Mobile App (`UI_Project/parent-ui/`)

- **Minimal Homepage:** Hero storytelling card + quick start/resume CTA; omits dynamic recent-story carousels on Home to keep mobile scrolling light and avoid extra backend loads.
- **Bottom Navigation Bar:** 5 balanced slots — `Trang chủ`, `Lịch sử`, central circular `+ Tạo mới` FAB, `Giáo án` (split into *Giáo án công khai trên hệ thống* & *Giáo án trường / giáo viên gửi*), and `Hồ sơ`.
- **Profile & Global Settings Separation:** Profile screen manages child profiles (including `Giới tính`, `Độ tuổi`, `Ghi chú`), while account, sharing, invitations, quota, privacy, and password live in the global top-right gear `Cài đặt` drawer.
- **Story Creation Workflow:**
  1. `prepare`: Select Child Profile + optional Lesson selector with in-place `"Chi tiết"` modal + optional `"Thêm gợi ý vẽ trước khi chụp"` toggle.
  2. `guide` (optional): Interactive 3-step progressive vector line-sketch illustrations tailored per topic (`Khu vườn`, `Bầu trời`, `Đại dương`, `Vũ trụ`) and detail level (`Nhẹ nhàng` / `Thêm chi tiết`).
  3. `capture`: Camera/Gallery upload preview (no developer `"Dùng ảnh mẫu"` button in UI).
  4. `idea`: Direct voice-to-text into the story idea box + clean audio upload & modal error reporting without verbose helper text.
  5. `review`: Automatic profile context pill (no redundant pre-story context screen), subject confirmation/editing chips, and automatic divergence dialog prompting `"Ưu tiên mục tiêu giáo án"` vs `"Ưu tiên tranh của bé"` whenever detected subject diverges from the selected lesson.
  6. `script`: Pre-video Activity selection (`Hoạt động cùng bé`) embedded before video generation, plus rewrite requests & script review.
  7. `generating` -> `ready`: Multi-stage job progress + Story Player (CC & fullscreen) + unlocked activity playback & quick family feedback.

## 4. Web Portals (`teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`)

- **Unified Forest-Green Palette:** Shared brand marks, active sidebar tabs, KPI charts, modals, and `HeroArt` illustrations use the cohesive forest-sage system (`#2e6b53` / `#cbe0cf` / `#fffefa`).
- **Consolidated Task Hubs:** Overlapping sidebar views are grouped into multi-tab workspaces (`Teacher: 8 items`, `School Manager: 8 items`, `Platform Admin: 9 items`) with URL hash aliases and a topbar Bell notification/inbox shortcut.
- **Teacher End-to-End Session (`Buổi dạy`):** Supports assigned class scope (`Lớp Lá 1`), approved lessons (`Bầu trời kỳ diệu`, `Khám phá khu vườn`, `Hành trình của hạt mầm`), optional 16:9 SVG line-sketch slides, interactive classroom activity, and inline sample flow (`3A` eligibility/consent confirmation -> `3B` temporary drawing upload, subject & idea -> `3C` script review -> `3D` preview video playback & class presentation confirmation) without leaving `#session`.

## 5. Open UI-vs-SRS Alignment Notes

Pending formal owner/product resolution in `FEAT-069` & SRS `v2.5-draft`:
- Automatic profile context application vs explicit pre-story manual context confirmation gate (SRS §5.1).
- Public lesson browsing/copying vs invitation/assignment-only parent lesson discovery (SRS §5.1 / §31).
- Teacher inline session sample execution vs separated `sample` endpoint permissions/consent verification rules (SRS §5.2).

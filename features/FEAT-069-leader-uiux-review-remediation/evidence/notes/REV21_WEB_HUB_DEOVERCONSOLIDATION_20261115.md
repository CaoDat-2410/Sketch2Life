# Rev21 — Web Role Navigation & Hub Balance Refinement (`2026-11-15`)

## 1. Scope & Approved Baseline

Executed under approved `plan/PLAN_REV21_WEB_HUB_DEOVERCONSOLIDATION.md` (SHA-256 `86AB3BF5670F79DA7E27F9CDAAC8F043B8F09948C408C8F12AC6AAF6C104EDB8`) strictly inside `UI_Project/shared/webWorkspace.tsx` with zero edits to `UI_Project/parent-ui/`, backend APIs, `apps/`, CI workflows, or canonical `FEAT-063` SRS `v2.5-draft`.

## 2. Web Navigation & Hub Adjustments Implemented

1. **AC21.1 — Teacher `Buổi dạy` de-duplication (`UI_Project/shared/webWorkspace.tsx`):**
   - Replaced the 6-tab horizontal bar in `workspaceHubs.teacher.session` (`Không gian buổi dạy`, `Chuẩn bị Plan`, `Sketch Deck`, `Video mẫu`, `Trình chiếu`, `Kết thúc run`) with 2 distinct stages: `Lên lớp trực tiếp` (`session`) and `Chuẩn bị Plan` (`occurrences`).
   - Added `hiddenRoutes?: Record<string, string>` on `HubSpec` and populated `deck`, `sample`, `presentation`, `run-control` inside `session.hiddenRoutes` so `resolveRoute` and breadcrumb rendering (`activeRouteLabel`) continue resolving direct hash/shortcut links (`#deck`, `#sample`, `#presentation`, `#run-control`) under `Buổi dạy` without cluttering `.web-hub-tabs`.
2. **AC21.2 — School Manager `Hồ sơ trẻ & chuyển lớp` vs `Nhóm gia đình` separation (`webWorkspace.tsx`):**
   - Split `"Gia đình & Roster"` in `config.manager.nav` into two explicit top-level items: `Hồ sơ trẻ & chuyển lớp` (`roster`, icon `'file'`) and `Nhóm gia đình` (`groups`, icon `'layer'`).
   - Removed the redundant single-tab `groups` entry from `workspaceHubs.manager` so both routes render directly without a 1-tab `.web-hub-bar`.
3. **AC21.3 — Platform Admin top-level `Nhật ký vận hành` (`webWorkspace.tsx`):**
   - Promoted `Nhật ký vận hành` (`audit`, icon `'file'`) out of `workspaceHubs.admin.health.tabs` into a standalone sidebar item under `VẬN HÀNH & HỆ THỐNG`.
   - Left `workspaceHubs.admin.health` focused on technical telemetry (`Sức khỏe nền tảng` and `Tác vụ AI (Queue)`).
4. **Concise `Cài đặt` sidebar label (`webWorkspace.tsx`):**
   - Shortened `'Cài đặt & thông báo'` to `'Cài đặt'` across `teacher`, `manager`, and `admin` while keeping both tabs (`Tài khoản...` + notification inbox/ops tabs) and the Topbar bell popover accessible.

## 3. Verification Evidence

- **AC21.4 — 5-Workspace Build (`npm --prefix UI_Project run build`):** Exited `0` across all 5 workspaces (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`).
- **Live Browser Verification (`Rev21 Web Nav & Hub Verifier`):**
  - Host-verified via `BROWSER_HOST_FACTS`: `visited_origins: http://localhost:5172, http://localhost:5173, http://localhost:5174`, `blocked_origins: none`, inspected `final_step_76.png` (`http://localhost:5174/#audit` at `1440x900`).
  - **Teacher (`http://localhost:5172`):** Verified `'Cài đặt'` sidebar label, exactly 2 `.web-hub-tabs` (`Lên lớp trực tiếp`, `Chuẩn bị Plan`) under `Buổi dạy`, `#sample` & `#deck` resolving cleanly under `Buổi dạy` breadcrumbs and returning to `Lên lớp trực tiếp`, plus both Settings tabs (`Tài khoản & Web Push`, `Hộp thư thông báo`).
  - **School Manager (`http://localhost:5173`):** Verified separated `'Hồ sơ trẻ & chuyển lớp'` and `'Nhóm gia đình'` sidebar items without single-tab `.web-hub-bar`, plus `'Cài đặt'` label.
  - **Platform Admin (`http://localhost:5174`):** Verified top-level `'Nhật ký vận hành'` sidebar item + `'Sketch2Life > Nhật ký vận hành'` breadcrumb, and `Giám sát AI & hệ thống` containing only `'Sức khỏe nền tảng'` and `'Tác vụ AI (Queue)'`.
  - **Stability & Responsive:** Confirmed `0` console/page errors and `scrollWidth <= clientWidth` across Desktop (`1440x900`) and Mobile (`390x844`).

## 4. Open Boundaries

- Browser-local UI prototype only (no backend/API/auth/payment wiring); Unified Web Portal (`5175`) shares `UI_Project/shared/webWorkspace.tsx` via the same Vite build check (`EXIT=0`).
- Canonical `FEAT-063` SRS `v2.5-draft` remains unsigned and untouched.

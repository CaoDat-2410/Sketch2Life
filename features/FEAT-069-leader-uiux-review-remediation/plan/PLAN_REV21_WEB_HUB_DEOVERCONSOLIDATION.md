# Plan Rev21 — Web Role Navigation & Hub Balance Refinement (`UI_Project/shared/`)

- **Feature:** `FEAT-069-leader-uiux-review-remediation`
- **Status:** READY FOR OWNER APPROVAL (`DRAFT` -> `APPROVED`)
- **Date:** 2026-11-15 (Asia/Saigon)
- **Trigger:** Project owner reviewed the earlier Rev14 web sidebar consolidation screenshot (`"tôi thấy bạn gộp lại như cái phần trên mà bạn làm á, thì nó có bị làm gộp quá không vậy..."`) and approved implementing the proposed de-overcrowding refinements (`"ok làm đi"`).

## Scope & Strict Boundaries

1. **Teacher `Buổi dạy` (`UI_Project/shared/webWorkspace.tsx`):**
   - Simplify `workspaceHubs.teacher.session.tabs` from 6 overlapping tabs down to 2 clean, distinct stages:
     - `Lên lớp trực tiếp` (`session` — `TeacherSessionWorkspace` integrated flow)
     - `Chuẩn bị Plan` (`occurrences` — pre-class plan setup)
   - Keep `hiddenRoutes: ['deck', 'sample', 'presentation', 'run-control']` in `workspaceHubs.teacher.session` (and breadcrumb fallback labels) so deep links, dashboard shortcuts (`go('deck')`), and inline fallback links (`#sample`, `#presentation`, `#run-control`) remain functional inside the `Buổi dạy` section without cluttering the horizontal tab bar with redundant forms.
2. **School Manager Clarity (`UI_Project/shared/webWorkspace.tsx`):**
   - Separate child enrollment/transfer out of `"Gia đình & Roster"` into two unambiguous sidebar items under `NHÀ TRƯỜNG & NHÂN SỰ`:
     - `Hồ sơ trẻ & chuyển lớp` (`roster`, icon `'users'`)
     - `Nhóm gia đình` (`groups`, icon `'layer'`)
   - Remove the redundant single-item `groups` hub entry so both pages render directly without a 1-tab hub bar, while preserving all `#roster` and `#groups` routing (`roleFlows.tsx:509`).
3. **Platform Admin Audit Visibility (`UI_Project/shared/webWorkspace.tsx`):**
   - Promote `Nhật ký vận hành` (`audit`, icon `'file'`) from the 3rd tab inside `Giám sát AI & hệ thống` (`health`) to a top-level sidebar item under `VẬN HÀNH & HỆ THỐNG`.
   - Keep `workspaceHubs.admin.health` focused on technical telemetry (`Sức khỏe nền tảng`, `Tác vụ AI (Queue)`).
4. **Concise Settings Label Across All 3 Web Roles (`UI_Project/shared/webWorkspace.tsx`):**
   - Shorten sidebar item label `'Cài đặt & thông báo'` to `'Cài đặt'` across `teacher`, `manager`, and `admin` while keeping both tabs (`Tài khoản...` + `Hộp thư thông báo` / `Thông báo...`) and the Topbar bell shortcut intact.
5. **Exclusions:**
   - Strictly UI-only navigation refinement inside `UI_Project/shared/` (`webWorkspace.tsx`). Zero changes to `UI_Project/parent-ui/`, `backend/`, API/auth wiring, `apps/`, CI workflows, or canonical `FEAT-063` SRS `v2.5-draft`.

## Acceptance Criteria

- **AC21.1:** Teacher `Buổi dạy` displays only `Lên lớp trực tiếp` and `Chuẩn bị Plan` in `.web-hub-tabs`, while `#deck`, `#sample`, `#presentation`, and `#run-control` routes still render cleanly under `Buổi dạy`.
- **AC21.2:** School Manager sidebar explicitly exposes `Hồ sơ trẻ & chuyển lớp` (`roster`) and `Nhóm gia đình` (`groups`) as standalone items.
- **AC21.3:** Platform Admin sidebar explicitly exposes `Nhật ký vận hành` (`audit`), leaving `Giám sát AI & hệ thống` with `Sức khỏe nền tảng` and `Tác vụ AI (Queue)`.
- **AC21.4:** `npm --prefix UI_Project run build` passes across all 5 workspaces, live browser inspection (`1440x900` & `390x844`) confirms all 3 web portals (`5172`, `5173`, `5174`) have zero console errors and zero horizontal overflow, and all 5 `tools/validate_*.py` checks pass before committing & verifying `5/5` CI on GitHub.

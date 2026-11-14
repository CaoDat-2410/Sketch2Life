# Rev14 Evidence Note: Web Sidebar Consolidation & Multi-Tab Workbenches (2026-11-14)

- **Plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN_REV14_WEB_SIDEBAR_CONSOLIDATION.md`
- **Plan SHA-256:** `3BAC2BB69B509AAF376E5F76424355E1261B6C44BE6406C66038C8D6E0D5F9EB`
- **Baseline:** Canonical working SRS remains `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (`2.5-draft`, unsigned). No SRS, backend, API, auth, schema, legacy `apps/`, or `child-experience/` files were modified.

## 1. Summary of Changes (`UI_Project/shared/`)

1. **`UI_Project/shared/webWorkspace.tsx`:**
   - Consolidated sidebar navigation lists:
     - **Teacher (`18 -> 8` links):** `Tổng quan` (`home`), `GIẢNG DẠY` (`Lớp học & học sinh`, `Giáo án`, `Buổi dạy`, `Lịch sử buổi dạy`), and `GIA ĐÌNH & HỆ THỐNG` (`Phản hồi gia đình`, `Lượt tạo của trường`, `Cài đặt & thông báo`).
     - **School Manager (`15 -> 8` links):** `Tổng quan` (`home`), `NHÀ TRƯỜNG & NHÂN SỰ` (`Lớp học & sức chứa`, `Giáo viên & phân công`, `Gia đình & Roster`), and `GIÁO ÁN & VẬN HÀNH` (`Duyệt công khai`, `Phản hồi giáo án`, `Gói dịch vụ & Quota`, `Cài đặt & thông báo`).
     - **Platform Admin (`12 -> 9` links):** `Tổng quan` (`home`), `TỔ CHỨC & NỘI DUNG` (`Tổ chức`, `Tài khoản & vai trò`, `Kiểm duyệt thư viện`, `Danh mục hoạt động`), and `VẬN HÀNH & HỆ THỐNG` (`Đối soát thanh toán`, `Giám sát AI & hệ thống`, `Hỗ trợ & phản hồi`, `Cài đặt & thông báo`) — also eliminating prior single-item orphan groups and removing Feedback/Notifications/Settings from the `NHẬT KÝ` group.
   - Added `workspaceHubs` and `resolveRoute(role, rawId)` so legacy/deep-link hash IDs (`import`, `sharing`, `children`, `teacher-scope`, `occurrences`, `deck`, `sample`, `presentation`, `run-control`, `inbox`, `class-lifecycle`, `capacity`, `assignment`, `transfers`, `roster`, `quota`, `notifications`, `jobs`, `audit`), Dashboard metric cards, `DetailPanel` transitions, and `flowContinuations` resolve directly to their unified sidebar hub and active sub-tab without dead-ending.
   - Added `.web-hub-bar` (`role="tablist"`, `aria-selected`) inside `<main>`, breadcrumb sub-tab indicator, secondary `"Nhập từ tài liệu"` header CTA inside Teacher `Giáo án`, `"Mở hộp thư thông báo"` action in the topbar Bell popover, and `saveImportDraft(...)` to append confirmed preview import drafts into Teacher's local library list.
2. **`UI_Project/shared/roleFlows.tsx`:**
   - Passed `onNavigate` into `TeacherSessionWorkspace` so internal links (`#occurrences`, `#sample`) switch hub tabs directly without page jumps.
   - Added optional `onSaveImportDraft` support on `WizardPage` (`isImport`) and `RoleFlowPage`, allowing Teacher to save a local `Bản nháp` preview record back to `Giáo án -> Thư viện & soạn mới` after completing the SRS extraction review & confirmation step.
3. **`UI_Project/shared/rev13ProMax.css`:**
   - Added responsive styling for `.web-hub-bar`, `.web-hub-tabs`, `.web-hub-tab`, `.web-head-actions`, `.web-popover-actions`, and `.web-breadcrumb small` aligned to the Rev12/Rev13 forest-green/sage Pro Max palette with 44px touch targets and mobile wrap behavior.

## 2. Build & Browser Verification

- **Production build:** `npm --prefix UI_Project run build` exited `0` across all 5 workspaces (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`).
- **Live browser verification (`1440x900` desktop & `390x844` mobile on local dev servers `5196`–`5199`):**
  - Verified exact DOM navigation lists and hub `[role="tab"]` lists on **Teacher** (`http://localhost:5198/#lessons`), **School Manager** (`http://localhost:5196/#classes`), **Platform Admin** (`http://localhost:5197/#health`), and shared **Web Portal** (`http://localhost:5199/`).
  - Exercised Teacher's 3-step `Nhập từ tài liệu` flow (file select -> sample extraction populate -> confirmation checkbox -> `"Lưu bản nháp vào thư viện"`), verified return to `Thư viện & soạn mới` with the new draft row, verified `Buổi dạy` internal switch to `Chuẩn bị Plan`, verified Dashboard KPI routing (`Đang chia sẻ` -> `Giáo án / Chia sẻ giáo án`, `Tác vụ AI` -> `Giám sát AI & hệ thống / Tác vụ AI (Queue)`), verified topbar Bell popover -> `Hộp thư thông báo`, and confirmed `0` console/page errors and `0` horizontal overflow (`scrollWidth <= innerWidth` at `390x844` and `1440x900`).

## 3. Limitations

- UI-only preview using local fixture data; no real file parser/OCR, AI jobs, notifications backend, or persistence.
- SRS `v2.5-draft` remains unsigned and untouched.

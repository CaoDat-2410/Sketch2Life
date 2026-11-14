# Plan Rev14: Web Sidebar Consolidation & Unified Task Workbenches (`UI_Project/shared/`)

- **Feature:** FEAT-069 — Leader review UI/UX remediation and Pro Max polish
- **Plan revision:** 14
- **Status:** APPROVED for implementation (UI-only scope in `UI_Project/`)
- **Target surface:** `UI_Project/shared/webWorkspace.tsx`, `UI_Project/shared/roleFlows.tsx`, `UI_Project/shared/rev13ProMax.css`
- **Canonical SRS baseline:** `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (`2.5-draft`, unsigned working draft)

## 1. Objective

Streamline redundant and fragmented sidebar navigation items across the three authenticated web portals (**Teacher**, **School Manager**, and **Platform Admin**) by consolidating related steps/screens into unified tabbed workspaces—starting with merging **`Nhập & rà soát tài liệu`** inside **`Giáo án của tôi`**—while preserving every SRS `v2.5-draft` workflow gate, provenance note, and permission boundary, plus backward-compatible route/hash resolution so zero dashboard or modal links break.

## 2. Sidebar Consolidation Architecture (Before → After)

### A. Teacher (`18 → 8` sidebar items; 2 balanced sections + Tổng quan)
- **`Tổng quan` (`home`)** — Dashboard overview (all quick links updated/preserved via alias routing).
- **Section `GIẢNG DẠY`:**
  1. **`Lớp học & học sinh` (`classes`)** *(merges `classes`, `children`, `teacher-scope`)*:
     - Tab `classes`: Lớp được phân công (list + detail modal + Next flow -> Buổi dạy).
     - Tab `children`: Hồ sơ trẻ trong lớp (2-step preview form).
     - Tab `teacher-scope`: Phạm vi tổ chức & quyền lớp.
  2. **`Giáo án` (`lessons`)** *(merges `lessons`, `import`, `sharing`)*:
     - Tab `list`: Thư viện & soạn giáo án (collection list, filter/search, edit draft, `+ Soạn giáo án` modal + shortcut button `"Nhập từ tài liệu"`).
     - Tab `import`: Nhập từ tài liệu PDF/PPTX/DOCX (`FR-T-06` / `FR-T-07` 3-step extraction & mandatory Teacher field inspection/confirmation before creating a preview draft).
     - Tab `sharing`: Chia sẻ giáo án (revision-pinned invites & grant tracking).
  3. **`Buổi dạy` (`session`)** *(merges `session`, `occurrences`, `deck`, `sample`, `presentation`, `run-control` into one chronological teaching cockpit)*:
     - Tab `session`: Trình bày buổi dạy (`TeacherSessionWorkspace`: Class -> Lesson -> Activity -> Show Slide/Sketch -> Interaction -> Gate).
     - Tab `occurrences`: Chuẩn bị Plan & Occurrence (`WizardPage` 4-step pin).
     - Tab `deck`: Sketch Deck (Tùy chọn).
     - Tab `sample`: Video mẫu cho buổi dạy (eligibility confirmation + drawing + transcript/subject + script + jobs + playback).
     - Tab `presentation`: Xác nhận trình chiếu trong lớp.
     - Tab `run-control`: Hoàn tất / hủy run.
  4. **`Lịch sử buổi dạy` (`history`)** — Historical occurrences & runs.
- **Section `KẾT NỐI & HỆ THỐNG`:**
  5. **`Phản hồi gia đình` (`feedback`)** — Family lesson feedback thread.
  6. **`Lượt tạo của trường` (`quota`)** — School video quota rules & status.
  7. **`Cài đặt & thông báo` (`settings`)** *(merges `settings`, `inbox` + linked from Topbar Bell)*:
     - Tab `general`: Tài khoản & Web Push enrollment.
     - Tab `inbox`: Hộp thư thông báo chuẩn.

### B. School Manager (`15 → 8` sidebar items; 2 balanced sections + Tổng quan)
- **`Tổng quan` (`home`)**
- **Section `NHÀ TRƯỜNG & NHÂN SỰ`:**
  1. **`Lớp học & sức chứa` (`classes`)** *(merges `classes`, `class-lifecycle`, `capacity`)*:
     - Tab `list`: Danh sách lớp học (`+ Thêm lớp`).
     - Tab `lifecycle`: Vòng đời lớp học (`ManagerClassConsole mode="lifecycle"`).
     - Tab `capacity`: Sức chứa & điều kiện tạo lớp (`ManagerClassConsole mode="capacity"`).
  2. **`Giáo viên & phân công` (`teachers`)** *(merges `teachers`, `assignment`, `transfers`)*:
     - Tab `directory`: Giáo viên & lời mời (`ManagerTeacherProvisioning`).
     - Tab `assignment`: Phân công giáo viên theo lớp (`assignment` wizard).
     - Tab `transfers`: Đổi người phụ trách & xử lý run (`ManagerTransferWorkbench` — preserves `ACTIVE_RUN_CONFLICT` + separate emergency force-close audit boundary).
  3. **`Gia đình & Roster` (`groups`)** *(merges `groups`, `roster`)*:
     - Tab `groups`: Nhóm gia đình & lời mời (`ParentGroupsConsole`).
     - Tab `roster`: Roster & chuyển lớp (`roster` enrollment wizard).
- **Section `GIÁO ÁN & VẬN HÀNH`:**
  4. **`Duyệt công khai` (`review`)** — Publication 4-gate approval queue.
  5. **`Phản hồi giáo án` (`feedback`)** — Teacher review discussion inbox.
  6. **`Gói dịch vụ & Quota` (`billing`)** *(merges `billing`, `quota`)*:
     - Tab `billing`: Gói dịch vụ & hóa đơn (`ManagerBillingConsole`).
     - Tab `quota`: Quota video toàn trường (`OperationsPage` quota).
  7. **`Cài đặt & thông báo` (`settings`)** *(merges `settings`, `notifications` + linked from Topbar Bell)*:
     - Tab `general`: Cài đặt cổng trường.
     - Tab `notifications`: Thông báo tổ chức.

### C. Platform Admin (`12 → 9` sidebar items; fixes broken sidebar grouping & merges operator consoles)
- **`Tổng quan` (`home`)**
- **Section `TỔ CHỨC & NỘI DUNG`:**
  1. **`Tổ chức` (`organizations`)**
  2. **`Tài khoản & vai trò` (`accounts`)**
  3. **`Kiểm duyệt thư viện` (`moderation`)**
  4. **`Danh mục hoạt động` (`catalog`)**
- **Section `VẬN HÀNH & HỆ THỐNG`:**
  5. **`Đối soát thanh toán` (`billing-ops`)**
  6. **`Giám sát AI & hệ thống` (`health`)** *(merges `health`, `jobs`, `audit`)*:
     - Tab `health`: Sức khỏe nền tảng.
     - Tab `jobs`: Tác vụ AI (Queue & retryable states).
     - Tab `audit`: Nhật ký vận hành (redacted audit log).
  7. **`Hỗ trợ & phản hồi` (`feedback`)**
  8. **`Cài đặt & thông báo` (`settings`)** *(merges `settings`, `notifications` + fixes `settings`/`feedback`/`notifications` previously misplaced inside `NHẬT KÝ`, plus linked from Topbar Bell)*:
     - Tab `general`: Cài đặt hệ thống.
     - Tab `notifications`: Thông báo vận hành.

## 3. Acceptance Criteria

- **AC14.1:** Route alias & sub-tab state resolver in `UI_Project/shared/webWorkspace.tsx` maps every legacy route/hash ID (`import`, `sharing`, `children`, `teacher-scope`, `occurrences`, `deck`, `sample`, `presentation`, `run-control`, `inbox`, `class-lifecycle`, `capacity`, `assignment`, `transfers`, `roster`, `quota`, `notifications`, `jobs`, `audit`) to its canonical consolidated page + active sub-tab; `go()`, `onNavigate()`, hash links (`#occurrences`, `#sample`), `DetailPanel`, and `Dashboard` cards never dead-end.
- **AC14.2:** Topbar notification Bell popover retains existing preview notice and includes a direct action opening the role's consolidated notification tab (`inbox` or `notifications`).
- **AC14.3:** In Teacher `Giáo án`, switching to `Nhập từ tài liệu` preserves SRS `FR-T-06`/`FR-T-07` raw-file provenance warning, 25 MB limit, and editable field review; completing import review allows optionally saving the extracted preview draft into `Thư viện giáo án`.
- **AC14.4:** Consolidated tabs render cleanly with accessible `role="tablist"` / `aria-selected`, minimum 44px touch targets, clear visual hierarchy matching Rev12/Rev13 sage/forest-green palette, and zero horizontal overflow on desktop (`1440x900`) and narrow/mobile widths (`<=560px`).
- **AC14.5:** `npm --prefix UI_Project run build`, `git diff --check`, and `python tools/validate_repository_security.py` pass cleanly with no edits to SRS files, backend/API code, legacy `apps/`, or `child-experience/`.

## 4. Non-Goals & Exclusions

- No changes to `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, backend APIs, auth/database schemas, legacy `apps/`, or `child-experience/`.
- No real file parsing/OCR, live AI inference, live notifications/billing calls, or persisted child data.
- Keep running `npm --prefix UI_Project run dev` server active for owner inspection.

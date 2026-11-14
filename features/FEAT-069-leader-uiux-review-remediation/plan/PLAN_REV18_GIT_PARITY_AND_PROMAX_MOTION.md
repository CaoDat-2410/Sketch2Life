# Plan Rev18 — Git Parity Alignment, Clean Copy Closure & ui-ux-pro-max Motion (`UI_Project/`)

- **Feature:** `FEAT-069` — Leader review UI/UX remediation & project workflow parity
- **Revision:** 18
- **Date:** 2026-11-14 (Asia/Saigon)
- **Author:** Antigravity UI/UX Engineering

## 1. Objective

Close the final discrepancies surfaced by auditing `UI_Project/` against the latest upstream Git branches (`origin/dev` backend/web routers + `origin/feature/fe-mobile-remediation` Parent screens), the 100% Leader UI/UX checklist, and `nextlevelbuilder/ui-ux-pro-max-skill` interaction/motion craft standards — strictly **UI-only inside `UI_Project/`**, with zero backend/API wiring and zero edits to canonical `FEAT-063` SRS `v2.5-draft`.

## 2. Verified Gaps Being Closed

1. **Leftover Dev/Simulation/Unconnected Strings in `UI_Project/`:**
   - `UI_Project/parent-ui/src/App.tsx`:
     - Story history summary (`renderHistory`) still shows `{count} câu chuyện mẫu` and `Playback thật chưa được kết nối`.
     - Child detail (`renderChildDetail`) shows `Xóa hồ sơ mẫu`; Lesson detail (`renderLessonDetail`) shows `Trạng thái mẫu`.
     - Profile sharing (`renderSharing` / `renderShareForm`) shows `Đã chấp nhận · mẫu`, `Đang chờ · mẫu`, `Thu hồi quyền mẫu`, `Giáo viên mẫu`, and `Danh sách ở đây là mẫu; lời mời chưa gửi thật...`.
     - Quota action (`renderQuota`) shows `Lịch sử gói và hóa đơn chỉ hiển thị sau khi có dữ liệu thật.`
     - Generating step (`case 'generating'`) exposes `Mô phỏng bước tiếp theo`, `Xem trạng thái lỗi mẫu`, and `Xem tình huống an toàn chặn`.
     - Login preview (`submitAuthPreview`) shows `Đăng nhập chưa được kết nối. Thông tin bạn nhập không được gửi đi.` instead of entering `home` smoothly on valid submit.
   - `UI_Project/shared/UnifiedWebApp.tsx`: Invitation activation still labels the quick-fill helper `Điền lời mời mẫu`.
   - `UI_Project/shared/roleFlows.tsx`: Teacher flow/session labels use `run mẫu`, `MÃ MẪU:`, and `Buổi dạy mẫu đã hoàn tất.` where class/session wording belongs (while keeping pedagogical `video mẫu` / `tranh mẫu` accurate to classroom sample-video mode).
2. **Teacher Dashboard Alignment to `origin/dev` Backend APIs (`UI_Project/shared/webWorkspace.tsx`):**
   - `TeacherDashboard` currently displays fabricated `nextSession` (`'10:30 · hôm nay'`) and a duplicate `PHẢN HỒI GIÁO ÁN` dashboard summary card, neither of which has an `origin/dev` dashboard summary endpoint (backend exposes `/api/lesson-library/v1/organizations/{org_id}/lessons`, `/api/be1/v1/organizations/{org_id}/classes`, `/api/be1/v1/organizations/{org_id}/sessions`, and `/api/teacher/v1/organizations/{org_id}/ai/*`; feedback already lives in Notification Bell + `Phản hồi gia đình`).
   - Replace `teacher-next-session-grid` with an API-faithful **Sẵn sàng buổi dạy theo lớp phân công** panel built strictly from Teacher's active class assignment (`Lớp Lá 1`) + approved library lesson (`Bầu trời kỳ diệu`), providing one-click launch into `#session` or `#lessons`.
3. **`ui-ux-pro-max-skill` Motion & Tactile Interaction Craft (`parent-ui` & `shared`):**
   - Current `rev13ProMax.css` layers contain zero `@keyframes` choreographies and no key-driven view/step entrance animations.
   - Add crisp, GPU-only (`transform`, `opacity`) `150–360ms` easing (`cubic-bezier(0.22, 1, 0.36, 1)`) choreography:
     - Key-driven view/step transitions (`App.tsx` flow step, home/subpage views, Teacher session stage/substeps, unified web tab panes).
     - Drawing guide SVG reveal & step-progress indicator transitions; tactile mic pulse halo during voice recording & streaming indicator.
     - Scrim fade + sheet/dialog entrance scaling across Parent & Web modals.
     - Consistent button active press (`scale(0.97)`) and `@media (prefers-reduced-motion: reduce)` override suppressing motion cleanly.

## 3. Target Files (`UI_Project/` only)

- `UI_Project/parent-ui/src/App.tsx`
- `UI_Project/parent-ui/src/rev13ProMax.css`
- `UI_Project/shared/webWorkspace.tsx`
- `UI_Project/shared/roleFlows.tsx`
- `UI_Project/shared/UnifiedWebApp.tsx`
- `UI_Project/shared/rev13ProMax.css`

## 4. Explicit Exclusions

- No backend (`backend/`), `apps/`, `mobile/`, database, authentication, payment, AI, or `FEAT-063` SRS (`v2.5-draft`) changes.
- Known open conflicts between canonical `FEAT-063` SRS `v2.5-draft`, Leader UI review, and `origin/dev` backend schemas (`child.gender` absent in `CreateParentProfileRequest` `extra="forbid"`, omitted manual `context-confirmation` gate, pre-video vs post-video outdoor activity timing) are reported transparently in `OPEN_QUESTIONS.md` and final response; SRS is not altered.
- No force push or git history rewrite.

## 5. Acceptance Criteria

1. Zero user-visible `"chưa được kết nối"`, `"không được gửi đi"`, `"Playback thật"`, `"mô phỏng"` buttons, `"câu chuyện mẫu"`, `"Giáo viên mẫu"`, `"Xóa hồ sơ mẫu"`, `"Trạng thái mẫu"`, or `"lời mời mẫu"` strings anywhere in active `UI_Project/` screens.
2. `TeacherDashboard` shows only data grounded in `origin/dev` Teacher endpoints (lessons, review/sharing state, assigned classes, session launcher) with zero fake `10:30` schedule or duplicate dashboard inbox widget.
3. GPU-only (`transform`, `opacity`) motion choreography (`<=380ms`) active across Parent & Web step/tab/modal/guide/mic interactions with complete `@media (prefers-reduced-motion: reduce)` coverage.
4. `npm --prefix UI_Project run build` exits `0` across all 5 packages (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`).
5. Live browser verification confirms visual layout, animations, zero console/page errors, and zero horizontal overflow (`375x812` & `1440x900`).
6. `git diff --check` and all 5 `tools/validate_*.py` scripts exit `0`.

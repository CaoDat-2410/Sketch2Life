# Evidence Note — FEAT-069 Rev17 Remove Preview/API Warning Banners (2026-11-14)

- **Feature:** `FEAT-069-leader-uiux-review-remediation`
- **Plan:** `plan/PLAN_REV17_REMOVE_PREVIEW_WARNING_BANNERS.md` (SHA-256 `ED0E1D90E681F4EC2B08BA2EDB2DD4ADACD60C4ACE99F264DBBCC6B35CF39261`)
- **Mode:** UI-only visual/copy cleanup inside `UI_Project/` without modifying backend, APIs, auth, database schemas, legacy `apps/`, `UI_Project/child-experience/`, or canonical FEAT-063 SRS `v2.5-draft`.

## Implemented Changes

1. **Inline API/Preview Warning Removal across Web Role Flows (`UI_Project/shared/roleFlows.tsx`):**
   - Removed all 13 `.feedback-preview-note` banners (`Chưa kết nối ... API`, `Quyết định chỉ nằm trong fixture`, `Bề mặt dành cho quyền vận hành kỹ thuật`) across `TeacherSessionWorkspace`, `ManagerTransferWorkbench`, `OperationsPage`, `FeedbackInboxPage`, `ManagerTeacherProvisioning`, `ParentGroupsConsole`, `TeacherSharingConsole`, `AccountsConsole`, `ManagerClassConsole`, `CatalogWorkbench`, `ModerationWorkbench`, `ManagerBillingConsole`, and `ManagerPublicationReview`.
   - Removed `<div className="flow-boundary">`, `<p className="teacher-session-boundary">`, `<p className="feedback-boundary">`, `<p className="preview-boundary-note">`, `<small className="sample-selection-boundary">`, `<p className="flow-note">{spec.boundary}</p>` inside `FlowDetailDialog`, and the `<FlowRecoveryDisclosure />` + `recoveryCasesFor()` disclosure widgets.
   - Removed `· BẢN XEM TRƯỚC`, `· PREVIEW`, `· preview`, `· fixture`, `· minh họa`, `Chờ Billing API`, `TRÌNH PHÁT VIDEO · MẪU` -> `TRÌNH PHÁT VIDEO`, and `Tạo lời mời preview` / `Xem kết quả đối soát · preview` labels while keeping full interactive form/modal state transitions, safety reminders, and Manager's 4 mandatory publication review gates intact.

2. **Web Dashboards, Modals, Layout & Portal Login Cleanup (`UI_Project/shared/webWorkspace.tsx`, `rev13ProMax.css`, `backendApi.tsx`, `UnifiedWebApp.tsx`, `RoleHelp.tsx`, `WebPortalLoginPage.tsx`):**
   - Removed `.dashboard-contract-note`, `.dash-panel-note`, `.web-detail-boundary`, `Nguồn: Dữ liệu minh họa cho UI`, `.web-modal-note` in both authoring/action modals, `.push-preview-boundary`, `.web-preview-chip` in the topbar, and `<aside className="web-panel web-feature-side">` (`RANH GIỚI TÍCH HỢP`).
   - Added `.web-app .web-feature-grid.web-feature-grid--single { grid-template-columns: minmax(0, 1fr); }` in `UI_Project/shared/rev13ProMax.css` so single-panel routes render cleanly at full width without an empty right column.
   - Updated `BackendModeNotice` in `UI_Project/shared/backendApi.tsx` to return `null` when `isLocalPreview()`, and cleaned non-preview fallback copy (`ApiUnavailableView`).
   - Removed `Bản xem trước`, `· fixture`, and `minh họa` disclaimer copy in `UnifiedWebApp.tsx` and `RoleHelp.tsx` while keeping role cards, activation tabs, and login forms functional.
   - Removed `{portalRole === "ADMIN" && !preview && <div className="tw-item is-amber" role="note">` and `"Xem thử cục bộ"` / `"Vào bản xem thử"` labels in `WebPortalLoginPage.tsx`.

3. **Parent Mobile Prototype/Preview Note Removal (`UI_Project/parent-ui/src/App.tsx`):**
   - Removed `<em className="android-preview-badge">BẢN THỬ</em>` from the status bar next to `9:41`.
   - Removed all 8 `.preview-inline-note` callouts (`Home`, `LessonDetail`, `Notifications`, `Sharing`, `Quota`, `Feedback`, `ChildForm`), all 10 `.prototype-note` disclaimer boxes (`Profile`, `ChildDetail`, `Privacy`, `GroupInvitations`, `Activities`, `DeliveryDetail`, `Library`, `RunDetail`, `LessonPreview`, `Recovery`), `<p className="auth-preview-note">Bản xem trước chưa kết nối xác thực.</p>`, and `<div className="inline-note">...Ảnh chỉ lưu tạm trong phiên xem trước này.</div>`.
   - Cleaned remaining toast/CTA preview copy (`· xem thử`, `trong bản xem trước`, `XEM TRƯỚC`, `Gỡ quyền mẫu?` -> `Thu hồi quyền chia sẻ?`, `Để sau trong phiên này` -> `Để sau`) while preserving all product forms, safety rules, privacy banners, and post-capture lesson mismatch modal.

## Verification

- **Source & Diff Hygiene:** Python regex scans (`scan_note_classes.py`, `scan_phrases_context.py`) confirmed zero remaining disclaimer banner classes or visible preview/API-unconnected warning text across active `UI_Project/` TS/TSX files (only SVG `aria-label="Minh họa ..."` accessibility tags, non-local Firebase auth error guards, and unrendered `boundary` metadata strings remain). Trailing whitespace-only lines introduced during tag removal were stripped cleanly (`git diff --check` exited `0`).
- **Production build:** `npm --prefix UI_Project run build` passed across all 5 packages (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`).
- **Live Browser Verification (`browser` subagent):** Inspected all 5 running apps across host-verified origins `http://localhost:5196` (School Manager), `http://localhost:5197` (Platform Admin), `http://localhost:5198` (Teacher), `http://localhost:5199` (Unified Web Portal), and `http://localhost:5200` (Parent mobile) with `blocked_origins: none`, confirming `0` forbidden warning selectors, `0` preview/fixture disclaimer strings, clean single-column `#import` layout, clean `#sharing` / `#billing` / Parent story flow screens, `0` console errors, and `0` horizontal overflow.
- **Repository Policy Validators:** Executed all 5 scripts under `tools/validate_*.py` (`validate_harness.py`, `validate_skeleton.py`, `validate_architecture.py`, `validate_team_allocation.py`, `validate_repository_security.py`), all passing cleanly.

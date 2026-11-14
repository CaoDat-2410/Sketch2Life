# FEAT-069 Plan Rev17 — Remove Preview/API-Unconnected Warning Banners (`UI_Project/`)

- **Feature:** `FEAT-069-leader-uiux-review-remediation`
- **Plan revision:** 17 (follow-up UI polish pass on active branch `FE_UI_Project_Ver2`)
- **Requested scope:** Project owner supplied a screenshot of `<div className="feedback-preview-note" role="note">` (`"Chưa kết nối Lesson Grant API · Preview không gửi email, cấp quyền đọc hoặc xác nhận lời mời thật."`) and explicitly instructed removing all such inline dev/preview/API-unconnected warning banners and visually similar disclaimers across `UI_Project/`: *"mấy cái cảnh bảo như này bạn bỏ hết cho tôi được không, mấy cái giống như cái trên bỏ hết giúp tôi"*.
- **Target paths (UI-only):**
  - `UI_Project/shared/roleFlows.tsx`
  - `UI_Project/shared/webWorkspace.tsx`
  - `UI_Project/shared/webWorkspace.css`
  - `UI_Project/shared/backendApi.tsx`
  - `UI_Project/shared/UnifiedWebApp.tsx`
  - `UI_Project/shared/RoleHelp.tsx`
  - `UI_Project/parent-ui/src/App.tsx`

## Exclusions & Invariants

- **UI-only:** No backend, API, auth, database, schema, provider, or billing changes. Do not connect real endpoints or send real requests.
- **Authority & security intact:** Do not modify `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, legacy `apps/`, or `UI_Project/child-experience/`. Keep `.gitignore` / credential / privacy protections untouched.
- **Keep real product controls & UX:**
  - Preserve all genuine validation/error states (empty required fields, password mismatch, audio error sheet, mismatch direction choice modal), functional controls, Manager's 4 mandatory publication review gate checkboxes (`managerReviewGates`), real safety instructions (`activity.safety`, material safety inputs), and real product `.privacy-banner` disclosures on Parent screens (cleaning only "bản xem trước / dữ liệu mẫu" dev disclaimers from inside them).

## Planned Edits & Acceptance Criteria

- **AC1 — Remove all web inline API/preview warning banners (`UI_Project/shared/roleFlows.tsx`):**
  - Remove all 13 `<div className="feedback-preview-note" role="note">` banners across `TeacherSessionWorkspace`, `ManagerTransferWorkbench`, `OperationsPage`, `FeedbackInboxPage`, `ManagerTeacherProvisioning`, `ParentGroupsConsole`, `TeacherSharingConsole`, `AccountsConsole`, `ManagerClassConsole`, `CatalogWorkbench`, `ModerationWorkbench`, `ManagerBillingConsole`, and `ManagerPublicationReview`.
  - Remove `<div className="flow-boundary">`, `<p className="teacher-session-boundary">`, `<p className="feedback-boundary">`, `<p className="preview-boundary-note">`, `<small className="sample-selection-boundary">`, `<FlowRecoveryDisclosure .../>`, and `<p className="flow-note">{spec.boundary}</p>` inside `FlowDetailDialog`. Clean `<p className="groups-scope-note">` dev disclaimers (`chưa quyết định`, `cần API`, `duyệt preview`).
  - Remove `· BẢN XEM TRƯỚC`, `· PREVIEW`, `· preview`, `· fixture`, `· minh họa`, and `"Chờ Billing API"` dev warning clutter from headings, eyebrow badges, list footers, buttons, status pills, and notices while preserving full interactive UI workflows.

- **AC2 — Clean web workspace & dashboards (`UI_Project/shared/webWorkspace.tsx`, `webWorkspace.css`, `backendApi.tsx`, `UnifiedWebApp.tsx`, `RoleHelp.tsx`):**
  - Remove `.dashboard-contract-note`, `.dash-panel-note`, `.web-detail-boundary`, `<div><dt>Nguồn</dt><dd>Dữ liệu minh họa cho UI</dd></div>`, `<div className="web-modal-note">` (in `LessonAuthoringDialog` & `ActionDialog`), `<aside className="web-panel web-feature-side">` (`RANH GIỚI TÍCH HỢP · Dữ liệu minh họa` — and switch `FeaturePage` container to `web-feature-grid--single` single-column CSS rule), `<p className="push-preview-boundary">`, `<span className="web-preview-chip">`, and `"Bản xem trước"` / `"Dữ liệu minh họa"` subtitles, badges, table footers, and footer disclaimers.
  - Make `BackendModeNotice` return `null` during local UI-only runs so `"Xem thử · Dữ liệu minh họa, không lưu"` no longer renders.
  - Clean `"Bản xem trước · không dùng tài khoản thật"` / `"· fixture"` / `"minh họa"` dev disclaimers in `UnifiedWebApp.tsx` and `RoleHelp.tsx` while keeping Portal role selection & activation flows working.

- **AC3 — Remove all Parent mobile warning boxes & prototype notes (`UI_Project/parent-ui/src/App.tsx`):**
  - Remove all 8 `<div className="preview-inline-note" role="note">` callout boxes (`Home`, `LessonDetail`, `Notifications`, `Sharing`, `Quota`, `Feedback`, `ChildForm` gender/session notes).
  - Remove all 10 `.prototype-note` disclaimer boxes (`Profile`, `ChildDetail`, `Privacy`, `GroupInvitations`, `Activities`, `DeliveryDetail`, `Library`, `RunDetail`, `LessonPreview` modal) and `.auth-preview-note` `"Bản xem trước chưa kết nối xác thực."` (`Auth`).
  - Remove `<div className="inline-note">...Ảnh chỉ lưu tạm trong phiên xem trước này.</div>` (`Capture`) and `.preview-capability-list` (`Generating`) plus `· XEM TRƯỚC` / `· CHƯA TẠO AI` / `Dữ liệu minh họa` / `Gỡ quyền mẫu?` dev-fixture text across `App.tsx`, while keeping all genuine SRS privacy banners and story/safety guidance intact.

- **AC4 — Verification & Clean Delivery:**
  - Verify `npm --prefix UI_Project run build` succeeds cleanly across all 5 workspaces (`EXIT=0`).
  - Verify live rendered screens via `browser` subagent across Parent Mobile (`parent-ui`), Portal/Teacher (`#lessons`, `#sharing`, `#session`, `#feedback`, modal dialogs), School Manager (`#classes`, `#teachers`, `#review`, `#billing`), and Platform Admin (`#catalog`, `#moderation`, `#accounts`, `#health`) — confirming zero amber/inline API-warning boxes remain and no single-column blank grid gaps exist.
  - Update `FEAT-069` context/decisions/status/evidence records, pass all 5 `tools/validate_*.py` policy validators cleanly, and sync git working state cleanly per project rules.

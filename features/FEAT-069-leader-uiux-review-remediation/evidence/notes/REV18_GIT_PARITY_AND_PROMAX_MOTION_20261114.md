# Rev18 — Git Source Parity Audit, Dashboard Cleanup & UI/UX Pro Max GPU Motion (`2026-11-14`)

## 1. Scope & Approved Baseline

Executed under approved Plan Rev18 (`plan/PLAN_REV18_GIT_PARITY_AND_PROMAX_MOTION.md`, SHA-256 `6E363D2923898FBF119FDE162C20EC9B785718AE7470BD628A3F2CD5205830A3`) strictly inside `UI_Project/` without modifying backend code, auth, live network calls, or canonical `FEAT-063` SRS `v2.5-draft`.

## 2. Git Source Workflow & Role Parity Verification

Audited `origin/dev` backend routers and `origin/feature/fe-mobile-remediation` mobile UI screens against `UI_Project/` and `FEAT-063` SRS `v2.5-draft`:

| Area | `origin/dev` / `origin/feature/fe-mobile-remediation` | `UI_Project/` Implementation | Status / Conflict Disposition |
|---|---|---|---|
| Parent Story Run Lifecycle | `/v1/story-runs`: `POST /`, `GET /active/current`, `GET /{run_id}`, `POST /{run_id}/context-confirmation`, `POST /{run_id}/subject-confirmation`, `POST /{run_id}/script-confirmation` (`parent_story_runs.py`); AI routes `/api/parent/v1/ai/{sketch-guides,drawing-understandings,story-runs/{run_id}/story-revisions}` (`parent_ai.py`) | `UI_Project/parent-ui/src/App.tsx` covers profile setup, optional line sketch guide, photo capture, drawing understanding + mismatch choice, voice/text idea rewrite, script confirmation, progress & history | Aligned on core stages; open conflicts preserved cleanly below |
| Parent Child Profile Schema | `CreateParentProfileRequest` (`parent_profiles.py`) has `display_name`, `age_months`, `interests_summary` (`extra="forbid"`, NO `gender`) | `parent-ui` renders optional UI-local `gender` per Leader review | Open product conflict preserved; UI-only local state, no backend/SRS edit |
| Parent Manual Context Screen | `parent_story_runs.py` exposes `context-confirmation`; `fe-mobile-remediation` renders `ContextScreen.tsx` | `parent-ui` omits manual tick gate and displays `.auto-context-pill` on `review` per Leader review | Open product conflict preserved |
| Parent Outdoor Activity Timing | `fe-mobile-remediation:ActivityScreen.tsx` places outdoor activity selection pre-video; `FEAT-063` SRS `v2.5-draft` §5.1 places outdoor activities post-video | `parent-ui` keeps outdoor activity selection pre-video (`case 'script'`) per Leader review and quick-view after video (`case 'ready'`) | Open product conflict preserved |
| Teacher Dashboard & Classroom Session | `teacher_ai.py` (`/lesson-plan-suggestions`, `/sketch-decks`, `/lesson-visuals`), `lesson_library.py`, `be1_registry.py`, `be1_sessions.py` (`/lobby`, `/start`, `/learning-stage/advance`, `/pause`, `/resume`, `/finish`, `/completion`, `/join-requests`, `/roster`, `/outcome`); no dashboard next-session schedule or separate feedback-summary endpoint | Removed fabricated `nextSession` (`10:30 · hôm nay`) and duplicate `PHẢN HỒI GIÁO ÁN` summary panel from `TeacherDashboard` (`webWorkspace.tsx`); replaced with `.teacher-session-launcher` derived from `assignedClasses` + `approvedLessons`; Teacher `#session` uses `MÃ LỚP:` + 3-step SVG slides + 3A–3D sample video stages | Cleanly grounded in `origin/dev` endpoints |
| School Manager, Platform Admin & Web Portal | Consolidated role routes via `webWorkspace.tsx` (`resolveRoute`) and `roleFlows.tsx` | All Manager review gates, transfer/roster/capacity/quota tabs, Admin moderation/catalog/billing/audit/health, and Unified Web Portal role switch/activation verified | Cleanly aligned |

## 3. Copy & Visual Motion Updates Implemented

1. **Removed remaining dev/placeholder copy in active Vite workspaces:**
   - `UI_Project/shared/UnifiedWebApp.tsx`: renamed `'Điền lời mời mẫu'` -> `'Điền thông tin gợi ý'`.
   - `UI_Project/shared/roleFlows.tsx`: renamed `'run mẫu'` -> `'phiên chạy'`/`'lượt chạy'`, `'occurrence'` -> `'buổi dạy'`, `'MÃ MẪU:'` -> `'MÃ LỚP:'`, `'Buổi dạy mẫu đã hoàn tất.'` -> `'Buổi dạy đã hoàn tất.'`, `'luồng kiểm thử'` -> `'quy trình'`.
   - `UI_Project/parent-ui/src/App.tsx`: renamed `'Xóa hồ sơ mẫu'` -> `'Xóa hồ sơ'`, `'Trạng thái mẫu'` -> `{selectedLessonDetail.visibility}`, sharing grant `'· mẫu'`/`'Thu hồi quyền mẫu'`/`'Giáo viên mẫu'` & disclaimer text, quota history toast, `'Mô phỏng bước tiếp theo'` -> `'Tiếp tục tiến trình'`, grouped recovery test triggers inside `.job-recovery-disclosure`, updated `renderHistory` copy (`'câu chuyện mẫu'`/`'Playback thật chưa được kết nối'` -> `'câu chuyện'`/`'Lưu trữ riêng tư của gia đình'`), and transitioned valid `submitAuthPreview` submissions directly to `'home'` with `'Đăng nhập thành công.'`.
2. **UI/UX Pro Max GPU-only Motion & Accessibility:**
   - `UI_Project/parent-ui/src/App.tsx` + `rev13ProMax.css`: key-driven `.screen-stage` (`display: flex; flex-direction: column; flex: 1 1 auto; min-height: 0;`), `.flow-content` step transition, 3-step SVG sketch stroke animation (`.guide-sketch-stage-wrap .sketch-preview-svg`), `.scrim` fade + spring sheets, `.toast-message` slide-up, `.record-button.is-recording` pulse, `.transcription-spinner`, active press feedback (`scale(0.97)`), and `animation-iteration-count: 1` inside `@media (prefers-reduced-motion: reduce)`.
   - `UI_Project/shared/webWorkspace.tsx` + `roleFlows.tsx` + `rev13ProMax.css`: key-driven `.web-stage-enter`, `.teacher-session-stage-body`, `.teacher-session-deck-stage` SVG reveal, `.teacher-session-launcher` layout & responsive stacking, button press feedback, and full `prefers-reduced-motion: reduce` support.

## 4. Verification Evidence

- **Production build (`npm --prefix UI_Project run build`):** Exited `0` across all 5 workspaces (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`).
- **Residual copy scan (`UI_Project/{parent-ui,shared}`):** `0` dev/mock/placeholder disclaimer hits remaining across `parent-ui/` and `shared/` (pedagogical `câu chuyện mẫu` in `webWorkspace.tsx:38` and `'video mẫu'` in Classroom Mode intentionally preserved as SRS domain terminology).
- **Live Browser Verification (`Rev18 Final Live Visual Verifier`):**
  - Host-verified visited origins (`BROWSER_HOST_FACTS`): `http://localhost:5171`, `http://localhost:5172`, `http://localhost:5173`, `http://localhost:5174`, `http://localhost:5175` (`blocked_origins: none`).
  - Inspected `final_step_145.png`: verified Unified Web Portal sign-in view rendered crisply in the forest-green/cream palette with zero warning banners or clipping.
  - Subagent reported `0` console errors, `0` page errors, `0` overlapping/clipped elements, and `scrollWidth <= innerWidth` across desktop (`1440x900`) and mobile (`375x812`, `390x844`).

# Rev20 — Parent UX Friction & Copy Polish (`2026-11-14`)

## 1. Scope & Approved Baseline

Executed under approved `plan/PLAN_REV20_PARENT_UX_POLISH.md` (SHA-256 `485DF1D4E64538014453BE93CA4DEFBEF26B676D534B0AC060671B901BE9B8E2`) strictly inside `UI_Project/parent-ui/` (`App.tsx`, `rev13ProMax.css`) with zero changes to backend code, API/auth wiring, `apps/`, CI workflows, or canonical `FEAT-063` SRS `v2.5-draft`.

## 2. Parent UX & Copy Improvements Implemented

1. **AC20.1 — Residual & technical copy elimination (`UI_Project/parent-ui/src/App.tsx`):**
   - `sendShareInvite`: updated toast from `'Đã thêm lời mời mẫu. Chưa gửi tới giáo viên hay cấp quyền truy cập.'` to `'Đã gửi lời mời chia sẻ hồ sơ tới giáo viên.'`.
   - `case 'prepare'` & `renderLibrary`: replaced `'preset'` wording with `'Giáo án gợi ý sẵn có thể dùng ngay cho câu chuyện của bé.'`.
   - `renderChangePassword`: changed primary submit button from `'Kiểm tra thông tin đổi mật khẩu'` to `'Cập nhật mật khẩu'`.
   - `case 'generating'`: changed fast-forward action from `'Tiếp tục tiến trình'` to `'Tiếp tục ngay'`.
2. **AC20.2 — Smooth auto-advancing `generating` job progress (`App.tsx`, `rev13ProMax.css`):**
   - Added deterministic `useEffect` (`screen === 'flow' && step === 'generating' && previewJobState === 'processing'`) stepping `previewJobStage` (`0 -> 1 -> 2` at `850ms` each, `3 -> ready` at `700ms`).
   - Added `.job-recovery-disclosure__actions` styling (`rev13ProMax.css`) so expanding `<details>` (`Tình huống xử lý khác`) and choosing failure/safety inspection cleanly pauses auto-advance while leaving recovery buttons accessible.
3. **AC20.3 — Visible Homepage preset indicator (`renderHome`, `rev13ProMax.css`):**
   - Added `.home-preset-pill` inside `.home-start` when `!activeRun && presetForNextRun` matches an available lesson, showing `"Giáo án đã chọn: <title>"` and a 1-tap `Bỏ chọn giáo án sẵn` button so navigating back from `Thư viện giáo án` keeps user context clear.
4. **AC20.4 (partial, mic fallback) & Step 1 mobile layout ergonomics (`App.tsx`, `rev13ProMax.css`):**
   - Updated `toggleRecording` to set `transcriptionStatus('error')` consistently for unsupported media / denied permission branches with concise modal copy.
   - Reordered `case 'prepare'` so `.guide-option` (`Thêm gợi ý vẽ trước khi chụp`) renders right beneath child selection before `.prepare-lesson`, paired with `.flow-content--prepare` compact vertical rhythm in `rev13ProMax.css`.

## 3. Verification Evidence

- **Residual copy scan (`UI_Project/parent-ui/src`, `UI_Project/shared`):** Python regex audit confirmed `0` matches for `'lời mời mẫu'`, `'Kiểm tra thông tin đổi mật khẩu'`, `'Tiếp tục tiến trình'`, and `0` user-visible occurrences of `'preset'` (only internal JS/CSS symbols `presetForNextRun`, `presetLesson`, `.home-preset-pill`).
- **5-Workspace Production Build (`npm --prefix UI_Project run build`):** Exited `0` across `parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, and `web-ui`.
- **Live Browser Verification (`Rev20 Parent UX Verifier`, `http://localhost:5171`, `375x812`):**
  - Host-verified via `BROWSER_HOST_FACTS`: `visited_origins: http://localhost:5171`, `blocked_origins: none`, inspected `final_step_110.png`.
  - Confirmed `0` console/page errors and `0` horizontal overflow (`375x812` `body` & `#root`).
  - Confirmed `.home-preset-pill` (`"Giáo án đã chọn: Bầu trời kỳ diệu"`) + clear button from Library (`"Giáo án gợi ý sẵn có thể dùng ngay cho câu chuyện của bé."`).
  - Confirmed Step 1 visual order: `.guide-option` (`y = 143.0`) rendered cleanly above `.prepare-lesson` (`y = 262.4`).
  - Confirmed auto-advance from `generating` stage 0 through 3 into `ready` (`Video sẵn sàng`) in ~3.5s without clicks, and verified `'Tiếp tục ngay'` + pause via `<details>` -> `'Xem trạng thái tạm gián đoạn'`.
  - Confirmed `Cài đặt -> Chia sẻ hồ sơ -> Mời giáo viên` toast (`'Đã gửi lời mời chia sẻ hồ sơ tới giáo viên.'`) and `Đổi mật khẩu` button (`'Cập nhật mật khẩu'`). (Unsupported-mic `transcriptionStatus('error')` branch verified by code inspection & build; headless browser exercised the simulated mic-recording path into `#story-idea`.)

## 4. Open Boundaries

- Browser-local UI prototype only (no live backend/API/auth/ASR/VLM/payment wiring).
- Open `FEAT-063` SRS `v2.5-draft` conflicts (`gender`, auto context, pre-video activity timing) remain unchanged for owner/leader sign-off.

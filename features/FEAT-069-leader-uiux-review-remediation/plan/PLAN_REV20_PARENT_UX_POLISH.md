# Plan Rev20 — Parent UX Friction & Copy Polish (`UI_Project/parent-ui/`)

- **Feature:** `FEAT-069-leader-uiux-review-remediation`
- **Status:** READY FOR OWNER APPROVAL (`DRAFT` -> `APPROVED`)
- **Date:** 2026-11-14 (Asia/Saigon)
- **Trigger:** Project owner asked for an honest senior UX check ahead of strict Leader inspection (`"nhưng bạn có thấy rằng UI đẹp và UX thì tiện ích phù hợp với người sử dụng không..."`) and approved implementing all remaining UX refinements (`"ok, làm giúp tôi đi"`).

## Scope & Strict Boundaries

1. **Eliminate remaining residual/technical phrasing (`UI_Project/parent-ui/src/App.tsx`):**
   - `sendShareInvite`: `'Đã thêm lời mời mẫu. Chưa gửi tới giáo viên hay cấp quyền truy cập.'` -> `'Đã gửi lời mời chia sẻ hồ sơ tới giáo viên.'`.
   - Library & Prepare group copy: replace `'preset'` with warm natural Vietnamese (`'Giáo án gợi ý sẵn có thể dùng ngay cho câu chuyện của bé.'`).
   - Password button: `'Kiểm tra thông tin đổi mật khẩu'` -> `'Cập nhật mật khẩu'`.
2. **Smooth Auto-Advancing Story Generation (`case 'generating'`):**
   - Add deterministic `useEffect` in `App.tsx` that automatically advances `previewJobStage` (`0 -> 1 -> 2 -> 3 -> ready`) while `screen === 'flow' && step === 'generating' && previewJobState === 'processing'`, removing the awkward 4-click manual progression while pausing cleanly whenever the user inspects failure/safety states inside `.job-recovery-disclosure` and allowing instant quick skip.
3. **Homepage Preset Lesson Indicator (`renderHome`):**
   - Render a compact `.home-preset-pill` inside `.home-start` whenever `presetForNextRun` is set (`!activeRun`), displaying the chosen lesson name plus a 1-tap `×` clear button so navigating from `Thư viện giáo án` never feels lost.
4. **Consistent Mic Fallback Clarity (`toggleRecording`):**
   - Set `transcriptionStatus('error')` consistently across unsupported-media and denied-permission branches and make the `recordingError` modal instructions concise without any dev wording.
5. **Step 1 `Chuẩn bị` Mobile Ergonomics (`375x812`):**
   - Place `.guide-option` (`Thêm gợi ý vẽ trước khi chụp`) right beneath `Chọn hồ sơ trẻ` before the long expandable lesson directory and tighten vertical rhythm in `UI_Project/parent-ui/src/rev13ProMax.css` alongside `.home-preset-pill` styling.
6. **Governance & Exclusions:**
   - Strictly UI-only inside `UI_Project/parent-ui/`; zero backend, API, auth, `apps/`, CI, or `FEAT-063` SRS edits.

## Acceptance Criteria

- **AC20.1:** Zero leftover `'lời mời mẫu'` / `'preset'` / `'Kiểm tra thông tin đổi mật khẩu'` strings across `UI_Project/parent-ui/`.
- **AC20.2:** Entering `'generating'` progresses smoothly to `'ready'` automatically unless paused by error/safety inspection.
- **AC20.3:** Selecting `'Dùng giáo án cho câu chuyện'` from Library displays `.home-preset-pill` cleanly on Homepage with a functional clear control.
- **AC20.4:** `npm --prefix UI_Project run build` passes across all 5 workspaces, live headless browser verification confirms smooth behavior with `0` console/page errors and `0` horizontal overflow (`375x812`), and all 5 `tools/validate_*.py` checks pass before committing & verifying `5/5` CI on GitHub.

# EV-078-01 — Parent account and security page UX review

- Date: 2026-11-10
- Target worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation
- Preview: http://127.0.0.1:5171/p13-settings
- Product authority: FEAT-063 SRS v2.7-draft Rev57 (unsigned), per active AGENTS.md.

## Screens reviewed

- Parent web account subview at 360×780, 390×844, and 768×1024.
- Parent web security subview at 360×780, 390×844, and 768×1024.
- Security page after scrolling to the password form at 360×780 and 390×844.

## Results

- Account fields and save action are one section; notification, subtitle, and landscape preferences are a separately headed list.
- The last account preference row is above the floating create control at 360px; no horizontal overflow was measured at 360px or 390px.
- Security content is grouped into AI/privacy, profile access, and password sections.
- At 360px and 390px, the first password field remains above the floating create action. Scrolling exposes all password fields and the save button.
- After scrolling to the bottom at 360px, the password save button ended at y=666 and the floating action began at y=694; the controls did not overlap.
- The password form has three labeled fields. Submitting it empty displayed “Vui lòng nhập đầy đủ mật khẩu hiện tại và mật khẩu mới.”
- Submitting the account form displayed “Đã cập nhật thông tin tài khoản phụ huynh.”
- Preference switches changed and restored their state during review; each settings switch measured 44px high and retained its accessible label.
- Parent UI pnpm exec tsc --noEmit: PASS.
- Local preview returned HTTP 200. Browser screenshots were visually inspected at all three viewports.

## Evidence files

- P13-account-phone-360.png
- P13-account-phone-390.png
- P13-account-tablet-768.png
- P13-security-phone-360.png
- P13-security-bottom-phone-360.png
- P13-security-phone-390.png
- P13-security-bottom-phone-390.png
- P13-security-tablet-768.png

## Limits

- No automated test suite was run.
- No product policy or backend behavior was changed.
- The selected directory contained no .git metadata, so Git status/diff checks could not be captured.
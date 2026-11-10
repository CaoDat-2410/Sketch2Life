# FEAT-074 Plan Rev1 — Parent settings grouped into two categories

- Revision: 1
- Status: APPROVED by the owner's direct request in this conversation; approval ledger entry will record this exact plan hash before implementation.
- Prepared: 2026-11-10
- Active worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`.
- Product authority: FEAT-063 SRS v2.7-draft, updated 2026-11-07, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; still awaiting formal owner sign-off.

## Owner request

“Cái này gom hết vào 2 cái là đầu tiên là tài khoản cài đặt và cuối cùng là bảo mật đc k ? phân đều ra á”

## Goal

Replace the three separate P13 account/security navigation rows with two clear, balanced groups while keeping every current setting available.

## Product/SRS boundary

- The canonical SRS v2.7-draft remains the current product authority. Its account ownership, privacy, password/authentication, and notification constraints remain unchanged.
- This is a navigation and presentation change only. It does not add product requirements or change account, privacy, AI, notification, password, or security behavior.
- Do not change SRS, API/backend, persistence, authentication, or account data.

## Existing behavior to preserve

- “Tài khoản & Tùy chọn” opens parent name/email, notification, Vietnamese subtitle, and auto-landscape preferences.
- “Quyền riêng tư & Dữ liệu AI” shows the privacy and profile-access information.
- “Đổi mật khẩu” opens the existing password form and its validation/toast behavior.
- Child profiles, theme selection, logout, route behavior, and local preview state remain unchanged.

## Planned grouping

1. **Tài khoản & cài đặt** — parent details and preferences (notifications, captions, auto-landscape).
2. **Bảo mật** — privacy/AI-data and profile-access information, plus the existing change-password form.

The P13 main page will expose only these two category rows. The Security category will present both privacy information and password change together in its destination view.

## Acceptance criteria

1. The P13 “Tài khoản & Bảo mật” section contains exactly two top-level options: “Tài khoản & cài đặt” and “Bảo mật”.
2. The first option opens all existing account and preference controls with their prior state and interactions.
3. The second option presents privacy/AI-data and profile-access information together with the existing password-change form.
4. Back navigation from either category returns to P13 settings; password validation and feedback still work.
5. The two options have balanced row sizing, clear subtitles, touch-friendly targets, and visible keyboard focus on the existing design system.
6. P13 remains readable at phone widths without horizontal overflow; existing child-profile, theme, and logout sections remain available.
7. No API, backend, authentication, persistence, SRS, or product-policy behavior changes are made.

## Implementation steps

1. Replace the three main settings rows with the two planned categories and concise descriptions.
2. Merge the existing privacy content and password form into the Security destination without changing their logic.
3. Keep the Account & Settings destination intact and update its title to match the new category name.
4. Review the settings UI at the active local preview and record feature-local screenshots/findings.

## Verification boundary

No automated tests or builds are in scope. Do not commit, push, deploy, or publish. Store review evidence in this feature's `evidence/` directory.

# FEAT-074 — Parent settings grouped into two categories

- Status: COMPLETE; owner request and exact plan approval are recorded in the worktree root and feature-local approval ledgers.
- Active worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`.
- Runtime target: Parent UI settings at `http://127.0.0.1:5171/p13-settings`.
- Product authority: FEAT-063 SRS v2.7-draft (2026-11-07), SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; awaiting formal owner sign-off.
- Current request: replace the three account/security rows with two balanced categories: account settings first, security last.
- Scope: P13 navigation and grouping only; preserve the existing account settings, privacy information, password form, child profile, theme, and logout behavior.
- SRS boundary: no new product requirement or data contract is inferred. Account ownership, privacy, authentication, and notification rules remain unchanged.

## Baseline

P13 shows three separate navigation rows: account preferences, privacy/AI data, and password. The first opens parent identity and preference controls; the other two open separate privacy and password views.

## Implementation and review record

- P13 now exposes exactly two category rows: “Tài khoản & cài đặt” and “Bảo mật”. Both have equal minimum height and retain the existing visible-focus styling.
- The account destination still contains parent name/email, push notification, Vietnamese subtitle, and auto-landscape controls.
- The security destination combines the existing privacy/AI-data and profile-access information with the existing password form. Password validation code and feedback remain unchanged; the screen stays in Security after a successful local demo submission.
- Child profiles, theme, logout, route, and backend behavior were left unchanged.
- Isolated Edge 157 preview review: checked category count and destinations at 390×844 and 768×1024; back navigation returns to the two-row main view. No horizontal overflow or browser runtime exceptions were observed.
- No automated tests/builds, commit, push, or deployment were performed.

## SRS boundary

This change reorganizes existing settings only. It does not create new account, privacy, password, notification, or security requirements and does not change API/backend or persistence behavior.

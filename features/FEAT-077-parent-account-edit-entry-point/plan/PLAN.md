# FEAT-077 Plan Rev1 — Parent account edit entry point

- State: PLANNED pending hash-specific approval record.
- Date: 2026-11-10.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Requirement authority: FEAT-063 system architecture SRS v2.7-draft Rev57, unsigned working baseline. This is a presentation/navigation refinement of existing account settings, not a new product requirement.
- Targets: apps/parent-ui and apps/mobile (React Native demo).

## Owner request

“và ở ngoài là bao gồm cài đặt và bảo mật còn cái tài khoản thêm 1 icon cài đặt chỉnh sửa ở kế bên này cho tôi là được dùng skill mà làm”

## Goal

Keep the outer settings page organized into exactly two groups, “Tài khoản & cài đặt” and “Bảo mật”, and add an obvious, accessible edit action beside the parent account summary card.

## Scope

1. Preserve the two top-level category rows and their current account/security destinations in Parent web.
2. Add a 44px+ edit icon button beside the parent avatar/name/email/role card. In web it opens the existing account form.
3. Mirror the parent account summary and edit action in the React Native settings screen. The native edit form updates only the in-memory demo snapshot.
4. Preserve current profile, privacy, password, notification, and navigation behavior; do not add API or persistence.
5. Review the account card and two category rows at phone and tablet widths when the local preview is available. Record evidence within this feature.

## Acceptance criteria

- AC1: The outer settings page still exposes exactly “Tài khoản & cài đặt” and “Bảo mật”.
- AC2: The account summary shows parent identity and role, with a clear edit affordance aligned beside it.
- AC3: Activating edit opens the existing account settings form in web; native opens an editable local demo form and saving updates the app snapshot.
- AC4: The edit control has an accessible name, visible focus/pressed feedback, and at least a 44×44 touch target.
- AC5: Phone and tablet layouts keep the identity text readable and the icon from overlapping the role badge.
- AC6: Existing security, child-profile and settings-category destinations remain available; no API/backend/auth/persistence/SRS behavior changes.
- AC7: Update feature context, decisions, evidence, status and approval records before closing the task.

## Exclusions

- No changes to category wording or security policy unless required to preserve the supplied reference.
- No new authentication, account verification, backend/API, database, persistence, or payment behavior.
- No generated/external images or new icon package; use the established web SVG icon and native controls already available.
- No commit, push, deploy or publication.
- Do not alter other worktree changes or copy changes to the main checkout.

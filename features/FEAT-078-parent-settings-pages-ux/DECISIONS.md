# FEAT-078 Decisions

## D1 — Keep the scope on the two supplied Parent web pages

Reorganize the Parent web account and security subviews shown in the owner screenshots. The distinct React Native settings modal and unrelated routes are outside this change.

## D2 — Preserve behavior and policy copy

Keep the account form, preference switches, privacy statements, profile-access statement, password validation, success/error feedback, and back navigation. Change their visual grouping and hierarchy only.

## D3 — Use the current product SRS

Follow FEAT-063 SRS v2.7-draft Rev57 per active AGENTS.md. The selected worktree’s v2.5 SRS copy is stale and was not used for current requirements. No product requirement changed.

## D4 — Separate security topics into readable sections

Keep AI/privacy statements together, place profile access in its own section, and group all password fields and feedback under the password form.

## D5 — Give short phones enough space around the fixed create action

Use tighter spacing on the 360px breakpoint and 44px switch hit targets. Keep the account preference rows and password action from sitting underneath the floating navigation control.
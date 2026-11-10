# FEAT-077 Decisions

## D1 — Keep two outer categories

The Parent settings page exposes exactly “Tài khoản & cài đặt” and “Bảo mật”. Existing destinations and their content remain intact.

## D2 — Put edit beside the account summary

The account card action is a direct, labeled edit entry point. On web it reuses the existing account form. On React Native it opens a local demo editor for parent display name and email.

## D3 — Preserve the demo boundary

Native saves only to ParentWorkflowSnapshot in the in-memory demo adapter. No account API, auth provider, or persistence is added.

## D4 — Reuse current visual language

Use the existing web SVG edit icon and native pressable/icon treatment; do not add generated images or a dependency for one control.

## D5 — Reflow the identity card on phone

Keep the avatar, full name/email, role badge, and edit action readable at narrow widths by placing the role badge below identity text. Keep the desktop/tablet card on one row.
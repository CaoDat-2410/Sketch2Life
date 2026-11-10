# FEAT-078 Context — Parent settings page UX

- Owner request: reorganize the two supplied Parent web screens, account settings and security, because their layout is confusing.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, per the active repository AGENTS.md. The selected worktree contains an older v2.5 SRS snapshot; it was not used as current product authority.
- Account page: the parent form and save action remain grouped; video preferences have a clear heading and consistent rows with 44px switch targets. Short-phone spacing keeps the rows clear of the floating create action.
- Security page: privacy statements, profile access, and password form are separated into clear cards. Short-phone spacing keeps the first password field clear of the floating navigation; the full form remains reachable by scrolling.
- Behavior: existing account save feedback, switch state, privacy wording, password validation/error feedback, and back navigation are preserved.
- Boundary: this is presentation-only. No backend/API/authentication/persistence or product policy change was introduced.
- Validation: Parent UI TypeScript check passed; browser preview reviewed at 360×780, 390×844, and 768×1024. Save, switch, and empty-password error states were exercised. See evidence/EV-078-01-PAGE-UX-REVIEW.md.
- Repository metadata: the selected directory has no .git entry, so Git status/diff checks were unavailable.
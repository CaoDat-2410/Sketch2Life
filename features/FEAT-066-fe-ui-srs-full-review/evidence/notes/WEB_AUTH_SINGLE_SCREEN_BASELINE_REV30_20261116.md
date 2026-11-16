# Revision 30 baseline — shared role login

- Date: 2026-11-16.
- Branch: codex/fe-ui-web-remediation.
- Baseline commit: df07438e690cabf93ec9feacedcc5b6e3ca2709d.
- Worktree was clean before Rev30 planning began; no pre-existing dirty source paths need preservation.
- Current behavior observed before implementation: /login shows role cards; /teacher/sign-in shows the split login layout with role links; /school/login renders a separate BE1 login layout. The Teacher role link to School Manager is the route hop being removed.
- Source baseline and auth ownership were reviewed in WebPortalLoginPage, the app router, School Manager's LoginPage/uthService, AdminAccessGate, and PortalSessionContext.
- No credentials, sign-in submission, or product API call was made while capturing this baseline.
- Plan: eatures/FEAT-066-fe-ui-srs-full-review/plan/PLAN.md, Rev30 SHA-256 $hash.

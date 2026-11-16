# Rev30 — shared role login browser review

- Plan: Rev30, SHA-256 8D167E39A75B3A13E68FBBB1C4672C018E9282920CC4478D9DFA4B16B1DAD12F; direct owner approval is in both task approval registers.
- Requirement trace: FEAT-063 v2.7-draft FR-C-01 and §§2.1/10.1 require Firebase to prove identity, the backend to resolve application role/scope, and the client not to grant or change a role. UI role selection only chooses which authentication path to request.
- /login now renders the sign-in screen directly, defaulting to Teacher. The old role-card chooser and duplicate School Manager login view are removed.
- Role buttons update the role query on the same /login route and retain the same layout. Selecting a role clears the previous password and role-specific error while keeping the email.
- Compatibility routes resolve to the shared login view: /teacher/login and /teacher/sign-in to Teacher; /school/login to School Manager; /platform/login to Platform Admin; retired /school/preview/login to the Manager login tab.
- Authentication adapters remain distinct and real: Teacher calls the existing Firebase identity plus backend assignment-role resolver; School Manager calls the existing BE1/Firebase authService.login and the authenticated /school route still checks the school_admin assignment; Platform Admin continues to fail closed because role/capability discovery is unavailable. No mock session or role grant was added.
- Browser evidence: screenshots/web-auth-rev30-20261116/ contains three desktop role captures, Teacher/Manager mobile captures, and observations.json.
- At 1440×900, Teacher and Manager share the same 980×582 login card. On role switch the pathname stays /login; only the role query and selected panel change. Platform Admin retains its visible backend-unavailable notice.
- At 390×844, all role screens have documentElement.scrollWidth ≤ 390px; Teacher and Manager cards fit the viewport. Platform Admin's longer notice needs vertical scroll, with no horizontal overflow.
- Five legacy URL checks reached the correct selected role. A keyboard Tab + Space role change keeps focus on the active Manager button with a 3px solid focus outline.
- Browser reported zero runtime exceptions, zero console errors, and zero external requests. No credentials were entered, no sign-in was submitted, and no product API was called.
- npm run build: passed. npm run lint: exit 0; remaining warnings are in pre-existing backend API, shell, and role-page files, not the revised login component. git diff --check: passed.
- Application tests were not run under the approved boundary. Repository harness/security/architecture results are recorded in the final status after the pre-commit checks.

## Final repository validation

- Repository security validator: REPOSITORY_SECURITY_VALID; 6,879 publishable files scanned; no environment files, seed accounts, credentials, signing keys, external reference documents, or absolute machine paths found.
- Architecture validator: ARCHITECTURE_VALID; Python dependency direction, mobile feature isolation, frontend asset gate, mobile AI boundary, and Firebase data-product exclusion passed.
- Harness validator: HARNESS_INVALID for the existing missing apps/mobile/package.json and unrelated FEAT-070 evidence directories (raw, screenshots, metrics, notes). Those mobile/FEAT-070 paths were left untouched.
- git diff --check: exit 0; Git emitted only CRLF-to-LF normalization warnings.
- Skeleton validator was not run because Rev30 changes login code and evidence only; no repository structure change.

Git closeout: the single approved local commit was amended after validation; branch codex/fe-ui-web-remediation remains one commit ahead of origin; nothing was pushed.

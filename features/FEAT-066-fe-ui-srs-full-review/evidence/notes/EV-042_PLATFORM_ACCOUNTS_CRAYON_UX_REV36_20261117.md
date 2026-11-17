# FEAT-066-EV-042 — Platform Accounts crayon UX rebuild

- Date: 2026-11-17 (Asia/Bangkok).
- Plan: PLAN_REV36_PLATFORM_ADMIN_ACCOUNTS_CRAYON_REBUILD_20261117.md; SHA-256 6AE92FAEB7ED005B463E05176A58539A6927323E9C61ED3350F9CA243446E0D9.
- Approval: FEAT-066 Rev36 in approvals/TASK_APPROVAL.md before application edits.
- Task SRS: owner-supplied v2.7-draft dated 2026-11-13, amendments through Rev69; SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5. The repo authority remains Rev60; it was not changed. Neither source is signed off by this task.
- Visual input: screenshot attached to the owner request. No generated/remote asset was used.

## Findings against supplied SRS
- Screenshot shows backend/auth failure while also presenting “no matching account” and 0/0 pagination. This falsely represents a failed request as a successful empty result.
- Search was not a form, so Enter did not submit. School Manager role assignment used blocking window.prompt for organization ID.
- Current typed account service exposes role and active/disabled operations. Content Admin is a scoped Platform Admin permission, not a product role; Platform Admin has no default child profile/media access. The current account API exposes no capability grant/read endpoint.
- Current list uses offset pagination, page size 50. Supplied SRS §21.1 specifies opaque cursor pagination, default 25, maximum 100. The existing API contract is preserved; cursor pagination remains an API/backend gap.

## Implementation and evidence
- Rebuilt only Platform Accounts page and its scoped stylesheet using the existing warm paper/ink/blue crayon palette. Improved hierarchy, responsive filters/list, role/state controls, status feedback and scope explanation.
- Added distinct loading, auth/permission/network error, successful-empty, filtered-no-results and populated states. Errors clear rows/count and cannot appear as successful empty data.
- Filters submit by Enter or button. Page size is 25; existing offset request shape remains. Account create/role/state actions continue using existing authenticated APIs. School Manager organization ID is inline. No capability UI or child-data access was added.
- Four headless Chrome captures at 1440x900, 1024x768, 768x1024 and 390x844: no horizontal overflow or runtime exceptions. Each showed the expected missing-Firebase-session state, no successful-empty claim, no account table, and a disabled create button. The 1024px capture exposed a wrapping filter action and CSS specificity issue; both were corrected and the captures rerun. Primary action text is now white-on-blue in light mode; keyboard focus and reduced motion remain styled.
- For browser rendering only, isolated sessionStorage was set to enter the role shell. No Firebase ID token, credential or fabricated account data was present; authenticated list/mutation states were not runtime-verified.
- Evidence screenshots: screenshots/rev36-platform-accounts/rev36-accounts-1440x900.png, rev36-accounts-1024x768.png, rev36-accounts-768x1024.png, rev36-accounts-390x844.png.
- npm run build: PASS. Focused local oxlint on UsersPage.tsx: PASS. git diff --check: PASS (Git reports CRLF normalization notices for earlier dirty files).
- No app tests, account mutations, commit or push.

## Remaining gaps
- Offset/cursor API mismatch needs backend contract work.
- No capability grant/read API; no visible audit-event viewer surfaced on this account page.
- Successful account read, create, role update and lock/unlock were not exercised in this visual pass.

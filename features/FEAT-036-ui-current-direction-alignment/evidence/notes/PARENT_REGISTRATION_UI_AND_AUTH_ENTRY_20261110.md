# Parent registration UI and sign-in entry — 2026-11-10

## Scope and approval

- Approved plan: FEAT-036 plan revision 13, PLAN_REV13_PARENT_REGISTRATION_UI_AND_AUTH_LINK.md.
- Plan SHA-256: 0832F08952DA8B48342EE61FA257EAB2BD46DBC4EDBF101D8C593D77DDC951D5.
- Approval: owner explicitly requested the missing registration UI and registration link in the auth UI; recorded in approvals/TASK_APPROVAL.md.
- Product baseline: FEAT-063 SRS v2.7-draft. Parent registration UX remains open; this work adds only the requested visual surface and navigation.

## Implementation

- Added “Chưa có tài khoản? Đăng ký” beside the existing forgot-password link on Parent sign-in.
- Added /p15-parent-registration with the approved auth background and panel, email/password/confirmation fields, show/hide controls, an unavailable-state message, and return-to-sign-in navigation.
- The email value is carried through route state. Passwords are not passed through navigation.
- Submitting performs no auth or backend operation and reports that no account was created. No email or verification code is sent and no success state is shown.
- Updated the unauthenticated route guard and mobile auth shell so registration is treated as an auth route.
- Reused existing assets and dependencies. No SRS or backend changes were made.

## Rendered review

The local Vite preview was reviewed in hidden Edge using mobile CSS viewports. The test data was synthetic and the session used the local preview logout to reach sign-in.

| View | Viewport | Document width | Panel bounds | Result |
|---|---:|---:|---:|---|
| Sign-in with registration link | 375×812 | 375 px | x=16, y=309, 343×487 px | Link and preview card visible; no horizontal overflow |
| Sign-in with registration link | 320×568 | 320 px | x=16, y=77, 288×475 px | Link and preview card visible; no horizontal overflow |
| Registration | 375×812 | 375 px | x=16, y=145, 343×520 px | Full form and action visible |
| Registration | 320×568 | 320 px | x=16, y=31, 288×503 px | Full form and action visible; no horizontal overflow |

The registration link navigated to /p15-parent-registration. Vite returned HTTP 200 for that route, ParentScreens.tsx, and App.tsx.

## Screenshot evidence

The PNGs are local-only because FEAT-036 screenshots are ignored by the repository. SHA-256:

- login-375x812.png — ACC84D8135854A40D136AAD3F93C4190FDB68C6478695566E7D4C3B6D5F8191E
- login-320x568.png — 112E43ACB97EBB510B8443C0D9FBD614CA02BCFCBF8683BC9F66F35B48B4DCDE
- registration-375x812.png — 6D79425AE2DD2D4F1B779019813938DF8D0E4231BCE0E4DC24512C714480C5C2
- registration-320x568-top.png — B77720834E1F31DBA1450E9F466FA8634A6D1271D94120B9A7DF4AF52495B4EC
- registration-320x568-bottom.png — F870BC353B4A7B469A65BB9BC769894CEF5362A4E7FF091D282C94BCB074869D

## Verification limits

- No automated tests or production build were run.
- This review is a rendered local preview, not a physical-device check or authenticated production registration.
- The canonical SRS still leaves Parent registration/account-recovery UX and Parent Web target scope open. This task does not close those questions.

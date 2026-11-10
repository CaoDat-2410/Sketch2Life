# Parent auth refresh guard — 2026-11-10

## Reported behavior

The owner reported that refreshing the local Parent demo at /p01-lesson-library with no backend session left the app on the lesson menu. Expected behavior: return to /p11-authentication whenever no session exists.

## Root cause

ParentContext initialized isAuthenticated with isLocalPreview(). On localhost without an auth bridge, isLocalPreview() is true. This treated demo availability as an authenticated session on every hard reload, so the protected-route guard allowed the lesson library.

## Change

- Parent authentication now starts as signed out.
- Local preview is entered only after the user chooses its explicit action from the sign-in screen. Its session remains in memory and clears on page reload.
- If the existing auth bridge is configured, startup calls getIdToken() and backendApi.parentLessons(), matching the existing Parent sign-in role check. Both must succeed to preserve the session; missing token or rejected access resolves signed out.
- Protected routes redirect with history replacement to /p11-authentication when signed out. Sign-in, recovery, and registration routes remain public.
- Firebase configuration, backend authentication enforcement, role checks, and API behavior were not changed.

## Manual verification

The local Vite server at 127.0.0.1:5171 returned HTTP 200 for /p01-lesson-library and the transformed ParentContext module. A fresh headless Edge session opened /p01-lesson-library without a Firebase bridge/session; the rendered DOM contained the Parent login scene and did not contain lesson-library content. This confirms the signed-out route rendered authentication instead of the library.

git diff --check passed; Git emitted only CRLF-to-LF normalization warnings for existing Markdown. No automated tests or production build were run.

## Limits

No live Firebase bridge or signed-in Firebase account was configured in this local preview. The token-restoration branch was reviewed in source but not exercised against a live session. No backend or real user data was accessed.
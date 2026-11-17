# Task approval

- Status: APPROVED
- Approver: project owner, direct fix request in the current task.
- Approved scope: Expo Android dev-client Metro connectivity scripts, LAN/ADB-reverse local launch
  guidance, and feature-local verification evidence only.
- Plan revision: 3
- Approved at: 2026-09-28 Asia/Saigon
- Acceptance basis: `plan/PLAN.md`.
- Explicit exclusions: release networking, production API changes, provider credentials, Android
  signing, live AI calls, and product UI changes.

## Follow-up approval — native debug launch

- Status: APPROVED
- Approver: project owner, direct bug-fix request in the current task.
- Approved scope: add the `android:dev` debug build/Metro launch entrypoint and document the
  existing debug-vs-release JavaScript loading boundary.
- Plan revision: 2
- Approved at: 2026-09-28 Asia/Saigon
- Explicit exclusions: no change to React Native runtime semantics, release signing, provider
  connectivity, or product UI.

## Follow-up approval — stale localhost override

- Status: APPROVED
- Approver: project owner, direct bug-fix continuation in the current task.
- Approved scope: make the local launcher pass a detected private LAN address to Expo and retain
  explicit ADB reverse behavior for localhost mode.
- Plan revision: 3
- Approved at: 2026-09-28 Asia/Saigon
- Explicit exclusions: no release/runtime contract changes, credentials, or product UI changes.

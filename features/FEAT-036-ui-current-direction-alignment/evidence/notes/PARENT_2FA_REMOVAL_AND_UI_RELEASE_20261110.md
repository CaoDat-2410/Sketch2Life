# Parent 2FA removal and FEAT-036 UI release — 2026-11-10

## Approved scope

Plan revision 11, approved in `approvals/TASK_APPROVAL.md`, removes the unsupported simulated Parent
2FA interface. It also authorizes consolidation and publication of the owner-approved FEAT-036 UI
work present in this worktree as one commit.

## Parent Settings correction

- Removed the “Bảo mật 2 lớp (2FA)” Settings row and local detail screen.
- Removed the default-enabled local toggle, fake Authenticator/Email OTP selector, hard-coded
  backup codes, and local “generate new codes” success toast.
- Removed now-unused backup-code CSS and 2FA wording from the settings API-unavailable explanation.
- Kept password change and the other account/settings surfaces unchanged.
- The canonical FEAT-063 SRS requires MFA for organization and billing administrators. It does not
  establish Parent-account 2FA or supported factors; this UI change leaves that product question
  open and does not alter the administrator requirement.

## Consolidated UI batch

This worktree's approved Parent FEAT-036 batch contains the seven prioritized UX fixes; the ZIP
login composition and splash-to-login transition; public password recovery and removal of the fake
OTP recovery UI; responsive status-bar/safe-area handling; the centered camera create-story shortcut;
and associated plans, approval records, asset provenance, screenshots, and implementation evidence.
No unrelated portals, credentials, backend contracts, tests, builds, or deployment changes are in
scope.

## Verification

- The Parent Settings source no longer contains a `twofa` subview, `twoFaEnabled`, factor selector,
  or placeholder recovery codes.
- `python tools/validate_harness.py`: `HARNESS_VALID`.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`; 6,747 publishable
  files scanned, with no machine paths or credentials detected. The first run caught a local
  user-profile path in the recovery evidence note; that path was replaced with the supplied image
  filename and hash, and the validator passed on rerun.
- `python tools/validate_architecture.py`: `ARCHITECTURE_VALID`.
- `git diff --check` exited 0. Git reported only existing CRLF-to-LF notices for FEAT-036 context
  and decision files.
- Vite returned HTTP 200 for `/p13-settings`, `ParentScreens.tsx`, `App.tsx`, and `MobileLayout.tsx`;
  the transformed Parent screen module had no Vite internal-server-error response.
- Automated tests/builds are not authorized by plan revision 11 and were not run.

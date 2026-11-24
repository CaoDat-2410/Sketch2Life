# FEAT-084 Plan Rev2 — Android UI screenshots addendum

**Date:** 2026-11-23
**Status:** APPROVED by the project owner's direct request (2026-11-23 03:46:24 UTC).
**Parent:** Plan Rev1 — Parent mobile UI review and polish.

## Scope

- Launch the real Expo Parent app from worktree `<LOCAL_ROOT>\.codex-worktrees\fe` on an Android emulator.
- Capture screenshots of the four affected flow screens (topic, drawing subject, capture, activity) and other Parent screens reachable through the real app without fabricating data.
- Save screenshots and a screen-by-screen index under `evidence/screenshots/android/` in FEAT-084.
- Use only a pre-existing authenticated session and synthetic data if already present. Do not create accounts/profiles/consents, seed or edit backend data, submit AI inference, or use a preview harness/fixture.
- If an affected route cannot be reached without a new persistent record or AI call, capture the accessible app state and record the exact blocker; do not bypass auth, consent, or workflow gates.

## Verification limits

- This is visual UI execution and evidence capture, not a behavioral/API test.
- Do not run tests/typecheck, create backend data, call AI/Modal, change code, commit, or push under this addendum.
- Redact or avoid any real child/account personal information; screenshots must contain only synthetic or empty-state data.

## Acceptance

1. The Expo Parent UI is launched on an Android emulator from the approved worktree.
2. Screenshots are raw emulator captures, stored inside FEAT-084 evidence, with screen name, device, route and reachability noted.
3. The report distinguishes captured screens from screens blocked by unavailable account/session/data and makes no claim of end-to-end behavior.

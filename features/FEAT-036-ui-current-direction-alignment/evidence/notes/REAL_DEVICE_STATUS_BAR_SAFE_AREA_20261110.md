# Real-device status bar and safe area — 2026-11-10

## Owner concern and approval

The owner flagged the static `9:41`/signal/Wi-Fi/battery strip shown in the supplied image as a
problem when the UI runs on a physical mobile device. Revision 9 records the bounded responsive fix;
its plan hash and authorization are in `approvals/TASK_APPROVAL.md`.

## Implementation

- Kept the simulated status strip for the desktop phone-frame preview.
- Hid it for narrow viewports and touch-first devices, including mobile landscape.
- Set `viewport-fit=cover` so supported hosts expose system safe-area insets.
- Added a `data-safe-area` mode to `MobileLayout`: ordinary pages reserve the top system inset at the
  shell; login and recovery pages manage it internally so it is not applied twice.
- Kept bottom tab navigation's existing safe-area padding. No native status-bar code changed.

## Verification and limits

- Vite returned HTTP 200 for `/p14-password-recovery`, transformed `MobileLayout.tsx`, and the shared
  Parent stylesheet. The CSS response contains the touch/mobile media query and top inset rule.
- `git diff --check` passed. Git emitted existing CRLF-to-LF notices for FEAT-036 context/decision
  files; no whitespace errors were reported.
- No automated tests/builds were run, per the approved plan.
- Physical-device verification was not available in this session. The current viewport rules prevent
  the mock system row from rendering on mobile/touch layouts; the operating system supplies its own
  status bar when run in a host that exposes one.

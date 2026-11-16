# Parent create-story navigation shortcut — 2026-11-10

## Approval

Plan revision 10 is approved in `approvals/TASK_APPROVAL.md`; its SHA-256 is recorded there.

## Implementation

- Added a dedicated center slot in the bottom navbar with a raised blue camera action, “Tạo” label,
  and accessible name “Tạo câu chuyện mới bằng cách chụp tranh”.
- Sized the action above 44 CSS pixels and added visible keyboard focus, hover/press feedback, dark
  theme styling, and reduced-motion handling.
- The grid inserts the action between the existing tabs, so it remains centered for both local
  preview (four destinations) and product-nav (two destinations).
- The action reuses the Home CTA's capture-first `/p04-capture-subject-confirmation` route, optional
  setup skip state, and no-quota warning. No backend or flow-page behavior changed.

## Verification and limits

- Vite returned HTTP 200 for the transformed `MobileLayout.tsx` module and shared Parent stylesheet.
- `git diff --check` passed. Git emitted existing CRLF-to-LF notices for FEAT-036 context/decision
  files; no whitespace errors were reported.
- No automated tests/builds were run, per the approved plan.
- A rendered screenshot was not captured in this pass; visual inspection is still pending.

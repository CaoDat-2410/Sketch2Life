# FEAT-036 plan revision 8 — Password recovery visual refinement

- Revision: 8
- Status: `APPROVED`
- Prepared: 2026-11-09
- Type: Parent password-recovery UI refinement
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by
  `docs/context/SRS_AUTHORITY.md`
- Parent target-surface scope remains an open SRS question; this is a bounded change to the existing
  local Parent UI only.

## Objective

Make the dedicated Parent forgot-password page polished, clear, and visually consistent with the
current blue/cream UI palette, while preserving its route and honestly communicating that email
recovery is not connected.

## Scope

1. Refine only `/p14-password-recovery` layout, hierarchy, responsive styling, and decorative UI.
2. Use existing semantic color tokens and a code-native email/security illustration; add no external
   assets or new dependencies.
3. Keep the entered-email prefill and return-to-login actions.
4. Keep the unavailable notice and no-send/no-OTP/no-success behavior. Do not add backend or
   identity-provider calls.
5. Preserve dark theme support, visible keyboard focus, accessible labels/status, and reduced-motion
   behavior.
6. Record the implementation and Vite/source verification in FEAT-036 evidence and status.

## Acceptance criteria

1. The recovery page has a stronger visual hierarchy, a polished security/mail hero, a clear email
   field, an unmistakable unavailable state, and one clear return-to-login action.
2. The page remains usable at the existing mobile preview size and smaller widths without horizontal
   overflow.
3. Light/dark themes, keyboard focus, email prefill, and accessible form semantics remain intact.
4. No email is sent or false success/OTP is shown.
5. The Vite route/module/styles resolve and `git diff --check` passes. No automated tests/builds are
   authorized by this plan.

## Out of scope

- Login or Settings behavior, authentication contracts, recovery APIs/providers, other portals,
  deployment, publishing, commit, or push.

## Authorization

The project owner explicitly requested: “Dựng lại UI forgot password cho tôi đẹp đi nào”. This is
the recorded task approval for the bounded implementation described above.

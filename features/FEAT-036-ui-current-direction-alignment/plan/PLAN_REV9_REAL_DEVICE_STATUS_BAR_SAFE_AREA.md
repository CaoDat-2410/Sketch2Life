# FEAT-036 plan revision 9 — Real-device status bar and safe area

- Revision: 9
- Status: `APPROVED`
- Prepared: 2026-11-09
- Type: Parent mobile viewport and system-inset adaptation
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by
  `docs/context/SRS_AUTHORITY.md`
- Parent target-surface scope remains an open SRS question; this is a bounded responsive UI fix.

## Objective

Prevent the desktop phone preview's simulated `9:41`/signal/Wi-Fi/battery row from appearing on a
real mobile viewport alongside the operating system status bar, and keep app content clear of
system safe areas.

## Scope

1. Retain the simulated status bar in the desktop phone-frame preview.
2. Hide the simulated status bar on narrow viewports and touch-first devices, including mobile
   landscape layouts.
3. Enable `viewport-fit=cover` and apply the top safe-area inset to the mobile app shell for routes
   whose page does not already handle it. Keep login and recovery pages from receiving the inset
   twice.
4. Preserve the existing full-screen mobile layout and bottom navigation safe-area padding.
5. Record the source and Vite verification in FEAT-036.

## Acceptance criteria

1. Desktop phone-preview mode still displays the simulated status bar.
2. At mobile widths and on touch-first devices, the fixed `9:41` and simulated system icons are
   hidden.
3. The real system status bar remains native; web content starts within the top safe area when the
   host exposes inset values. Login/recovery retain their own safe-area padding without duplication.
4. No unrelated UI, authentication, or backend behavior changes.
5. Vite route/module/style responses succeed and `git diff --check` passes. No automated tests/builds
   are authorized by this plan.

## Out of scope

- Native Android/iOS status-bar configuration, native app code, system-bar colors, deployment,
  publishing, commit, or push.

## Authorization

The project owner flagged the fixed simulated status bar shown in the supplied screenshot as a
problem when the UI runs on a real mobile device. This plan records the bounded responsive fix for
that concern.

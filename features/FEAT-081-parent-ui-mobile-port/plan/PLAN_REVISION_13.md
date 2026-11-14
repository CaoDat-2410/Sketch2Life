# FEAT-081 Plan Revision 13 — Parent Mobile Logo and App Icon

## Status and authority

This plan records the owner's direct 2026-11-15 request to use the supplied transparent logo in the active Parent mobile UI and Expo app icon. The supplied image is the approved visual reference; preserve it without redrawing or cropping. The canonical product source remains the unsigned FEAT-063 v2.7-draft Rev60 SRS; this change does not alter a product contract.

## Goal

Replace the `S` mark in the active Parent mobile screen header with the owner-supplied logo and point the Expo launcher icon and web favicon to the same applied asset.

## Authorized files

| Kind | Path | Incoming bytes | Incoming SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/presentation/components/ui.tsx` | 23,875 | `0BB724D1934F0A96F694F67AE5B5AFE8833DCCAF131C560BD486B49F62D07D61` |
| E | `apps/ui-mobile/app.json` | 1,560 | `9489E92A02306F6F0C1F575F3FF1C1FB9331BCB58ED2FD52E49880781F2D0651` |
| E | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 57,711 | `FB8BB036EEC5EEE72256030D120103EDDF5DB44CD9F22B6334A77460E620DE91` |
| E | Owner attachment `codex-clipboard-c198b23f-1b29-42d6-8f85-d450e80ca81e.png` | 1,191,659 | `E5910593FDD6AAF42B38A208A2B32A1F94B769670A37BC9BCA553E976822399A` |
| N | `features/FEAT-081-parent-ui-mobile-port/assets/generated/sketch2life-logo.png` | — | — |
| N | `features/FEAT-081-parent-ui-mobile-port/assets/sketch2life-logo.asset.json` | — | — |
| N | `features/FEAT-081-parent-ui-mobile-port/assets/REVIEW.md` | — | — |
| N | `features/FEAT-081-parent-ui-mobile-port/assets/approved/sketch2life-logo.png` | — | — |
| N | `apps/ui-mobile/assets/applied/sketch2life-logo.png` | — | — |
| N | `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_13.md` | — | — |
| E | `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | record pre-append pin in Addendum 28 | — |

The image asset lifecycle follows `docs/governance/FRONTEND_ASSET_GATE.md` and D-007: record the user-provided source and exact hash in the generated asset manifest, record the owner's direct visual approval in `assets/REVIEW.md`, then copy the unchanged image to approved and applied locations. Runtime code must reference only the applied copy.

## Implementation rules

1. Use the exact 1254×1254 transparent PNG supplied by the owner; do not redraw, crop, recolor, or overwrite the existing butterfly asset.
2. Replace only the active Parent `ScreenFrame` header's `S` mark with the applied logo, preserving the header layout and accessibility semantics.
3. Point Expo `icon` and `web.favicon` to `./assets/applied/sketch2life-logo.png`. Keep the existing splash artwork and legacy demo screens unchanged.
4. Update only an existing source assertion; add no test case. Do not run tests, typecheck, validators, install, network, backend, Android build/prebuild, emulator, or Modal commands. Do not stage, commit, or push.
5. The committed Expo configuration is the source for future native icon generation. Existing generated native Android launcher images and the installed app are not rebuilt by this task.

## Acceptance criteria

- The active Parent mobile header displays the supplied logo instead of the `S` mark.
- Expo app icon and web favicon point to the applied logo asset; the old butterfly source and splash artwork remain unchanged.
- Asset provenance and owner visual approval are recorded, and runtime references point only to the applied copy.
- No product flow, API, backend, route, domain, dependency, or legacy demo behavior changes.

## Relationship to prior scope

This plan extends FEAT-081 only for the Parent header logo and Expo icon configuration. It does not alter Plans 10–12 or Addenda 25–27, and does not authorize edits to `CONTEXT.md` or `DECISIONS.md`.

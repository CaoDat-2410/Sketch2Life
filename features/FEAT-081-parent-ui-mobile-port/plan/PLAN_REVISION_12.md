# FEAT-081 Plan Revision 12 — Home Empty-Profile Card Alignment

## Status and authority

This plan records the owner's 2026-11-15 direction to fix any visible mismatch found while reviewing the supplied Home screenshot, including the disconnected visual preview. It extends Plan Revision 11 only for the Home empty-profile card copy below. The canonical product source remains the unsigned FEAT-063 v2.7-draft Rev60 SRS; this change does not alter a product contract.

## Goal

Match the supplied Home reference when no child profile is selected by keeping the selection state and `Quản lý hồ sơ` action without an extra profile-count/creation sentence. The same `HomeScreen` is rendered in the connected app and the offline preview, so both remain aligned.

## Authorized files

| Kind | Path | Incoming bytes | Incoming SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 5,971 | `0986358D257FC55438412A9DC721A945A31F04E8F492F8A27666463E3DBC958D` |
| E | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 57,374 | `725595B2AAB2ED545868F41E5A6A6BC42A5738E571CAB44025D3B7C2B00D6825` |
| N | `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_12.md` | — | — |
| E | `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | record pre-append pin in Addendum 27 | — |

`CONTEXT.md` and `DECISIONS.md` remain excluded. No preview harness edit is needed because the offline tabs render the same `HomeScreen` component. No controller, API, backend, route, domain, product flow, asset, or dependency file is in scope.

## Implementation rules

1. Remove the redundant profile-count/creation helper sentence from the Home selected-profile card; retain the `Hồ sơ đang chọn` heading, no-selection message, and `Quản lý hồ sơ` action.
2. Preserve the Home active-run badge, label, disabled condition, and existing `onResumeRun`/`onStart` callbacks.
3. Update only the existing source assertion block; add no test case.
4. The offline preview remains inert and uses the shared screen source; make no API/controller/network changes.
5. Static review only. Do not run tests, typecheck, validators, diff-check, install, network, backend, Android, emulator, or Modal commands. Do not stage, commit, or push.

## Acceptance criteria

- With no selected profile, Home shows the selection message and management button without an additional count/creation sentence.
- With a selected profile, its existing badge remains unchanged.
- Active-run continuation behavior and callbacks remain unchanged.
- The connected app and offline preview use this same presentation; no harness behavior or API boundary changes.

## Relationship to prior scope

This plan extends Plan Revision 11 only to simplify the Home no-selection card copy so it matches the supplied reference. All other Wave M, Addendum 25, and Addendum 26 constraints remain in effect.

# FEAT-081 Plan Revision 16 — Offline Bottom-Bar Preview Props

## Status and authority

This plan records the owner's 2026-11-15 request for the center Start action and the necessary integration discovered during static review: the offline preview also renders `ParentBottomBar` and must provide the new action props.

## Goal

Keep the existing bottom-bar preview functional and inert after the component gains its center Start action.

## Authorized files

| Kind | Path | Incoming bytes | Incoming SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx` | 25,500 | `898BBC7CE510CEAC43A8B43D971A7375BB100D021D8A8B7BABE494FC57741B6B` |
| E | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 58,364 | `3037FD3AEE2B0881F57A07AEBEE424FDCE6BE7511E4271AB216679317817A339` |
| N | `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_16.md` | — | — |
| E | `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | record pre-append pin in Addendum 31 | — |

## Implementation rules

1. Pass `ignoreAction` to the preview's Start callback and label it `Bắt đầu`.
2. Update only the existing bottom-bar preview assertion; add no test case.
3. Preserve the preview's offline boundary and all no-test/no-install/no-network restrictions in Addendum 30.

## Acceptance criteria

- The offline `bottom-bar` preview renders the updated four destination tabs and raised center action.
- Preview actions remain inert and make no API/controller/network calls.

## Relationship to prior scope

This plan extends Plan Revision 15 only for the existing `ParentBottomBar` preview call and its source assertion. All other FEAT-081 constraints remain unchanged.

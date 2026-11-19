# FEAT-081 Plan Revision 11 — No-Profile Family Actions and Offline Preview

## Status and authority

This plan records the owner's 2026-11-15 direction to address the no-selected-profile family-menu behavior and show the same state in the API-disconnected visual preview. It extends Plan Revision 10 only for the bounded UI and harness changes below. The current product source remains the canonical unsigned FEAT-063 v2.7-draft Rev60 SRS; no product contract is changed.

## Goal

Make profile-dependent family actions truthful when no child profile is selected and provide an offline preview of both the Home open-run/no-selected-profile state and the Family unselected-profile state.

## Authorized files

| Kind | Path | Incoming bytes | Incoming SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx` | 10,748 | `1563E0F020E59C0C795F22D1195565D726C6C0801E5E5A0DFEF75834BC7BA610` |
| E | `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx` | 24,232 | `FA0A77FEDF790EE349B9D6AB42D95C9C938867AC75EB904D01210C9F85DAD481` |
| E | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 56,685 | `36EA2F9723BD674809A1718DF5148C0A6CE03C0B69D4A793ABB1F23CF97B456A` |
| N | `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_11.md` | — | — |
| E | `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | 74,970 | `F7FF23F4B80FED201E1C57D5DE5BCB604526F920BDD0AB8419BEA063ED197C5B` |

`CONTEXT.md` and `DECISIONS.md` remain excluded under the owner's earlier instruction. No controller, API, route, backend, domain, asset, dependency, or product-flow file is in scope.

## Implementation rules

1. In the Family hub, disable `Chia sẻ hồ sơ với giáo viên` and `Bài giáo viên đã dạy` when no profile is selected. Show a concise hint explaining that a profile must be selected first. Keep both rows visible and retain their existing callbacks for the selected-profile state.
2. Keep Home continuation independent of the selected-profile selector: an active run remains resumable from Home when no profile is selected.
3. In `ParentVisualPreviewHarness`, retain inert callbacks and no API/network calls. Add a deterministic Family preview with a profile listed but not selected, and make the Home preview show no selected profile with an active run. Preserve a separate Home preview for a new run and the existing selected-profile Family preview.
4. Rename the preview tab for the family hub to `Gia đình`. Update only the existing source assertion block to cover the disabled rows and offline states; add no test case.
5. Do not run tests, typecheck, validators, diff-check, install, network, backend, Android, emulator, or Modal commands. Do not stage, commit, or push.

## Acceptance criteria

- The two profile-dependent family actions are visibly and accessibly disabled with no selected profile, with a clear hint nearby.
- Both actions remain enabled and retain their existing callbacks when a profile is selected.
- Home still shows `Tiếp tục buổi đang mở` and binds it to the existing resume callback even when no profile is selected.
- The API-disconnected preview can display: Home with an open run and no selected profile; Home for a new run; Family with a selected profile; and Family with no selected profile.
- Preview controls remain inert; the harness imports/invokes no API, controller, or network code.
- No product behavior, API contract, backend, route, or asset changes are made. Static review only; no tests are run.

## Relationship to prior scope

This plan extends Plan Revision 10 only to gate profile-dependent family rows and add deterministic offline preview states. All other FEAT-081, Wave M, and Addendum 25 constraints remain unchanged.

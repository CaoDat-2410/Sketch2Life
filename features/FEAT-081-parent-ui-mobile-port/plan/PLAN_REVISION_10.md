# FEAT-081 Plan Revision 10 — Family Tab and Home Resume Placement

## Status and authority

This plan records the owner-directed FE mobile layout revision based on the screenshots supplied on 2026-11-15 and the owner's approval to create Plan Revision 10 and Addendum 25. The source scope is authorized by Addendum 25 in `approvals/TASK_APPROVAL.md`.

The current product source remains the canonical FEAT-063 v2.7-draft Rev60 SRS, which is unsigned. This task changes navigation grouping and presentation only; it does not change product contracts or behavior.

## Goal

Make the fourth bottom tab the family hub, move the complete existing family-space menu from Home to that tab, and show active-run continuation on Home only. Keep child-profile selection, profile CRUD, consent status, and all existing destinations and callbacks intact.

## Authorized files

| Kind | Path | Incoming bytes | Incoming SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` | 17,825 | `7478B20697F5975EA098DCE4B12BA9A25EED282EFEDC4D9E8996C09355AC62ED` |
| E | `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 6,963 | `A502E72387370A9EDEAE5A836941D64B05F777E81D65DFDBE33C16113C8454A4` |
| E | `apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx` | 8,070 | `50507C3E8F7D56B48DD6D73544B835C32C15666A758F890C73C4B9D957448554` |
| E | `apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx` | 3,204 | `E023F8FE108A8EABDAFACD3993D80CE931D0AC2FAC50B13791452255EBFEA11B` |
| E | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 55,756 | `08D1C0BF4AC260E5E4FD26602A92E66CCDE2ECC387F29A36FE33AA0B4778A7D2` |
| N | `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_10.md` | — | — |
| E | `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | 72,812 | `AF5B092841F0A648F38E8FF3A447D29267D39206EFD73DEB71A99812F299DC5C` |

`CONTEXT.md` and `DECISIONS.md` are deliberately excluded and remain untouched under the owner's earlier instruction. No assets, controllers, domain files, routes, API contracts, or backend files are in scope.

## Implementation rules

1. Change only the fourth tab's visible label from `Hồ sơ` to `Gia đình`; retain its internal tab ID and existing navigation callback.
2. Keep Home's active-run card and existing `onResumeRun` callback. Remove the family-space menu and sign-out action from Home.
3. Make the existing profile tab content the family hub. Keep profile list/selection, data-processing status, pending-deletion reconciliation, profile create/edit/delete, and the existing new-run profile continuation when no active run exists.
4. Remove the active-run warning and `Tiếp tục buổi đang mở` action from the family/profile screen. Do not add cancellation or another resume path.
5. Place every existing family-space destination in the family hub and route each to its existing handler: `Tài khoản và bảo mật`, `Cài đặt`, `Thông báo`, `Lượt tạo video`, `Lịch sử hoạt động`, `Bài giáo viên đã dạy`, and `Chia sẻ hồ sơ với giáo viên`. Place `Đăng xuất` there as well.
6. Management sub-screens entered from the family hub return to the family tab and keep it selected in the bottom bar. Preserve all existing service calls, guards, unavailable states, and error behavior.
7. Update only the existing source assertion block to reflect the new placement; add no new test case. Do not run tests, typecheck, validators, diff-check, emulator, or other commands prohibited by the owner.
8. Do not stage, commit, or push.

## Acceptance criteria

- Home retains the active-run badge and `Tiếp tục buổi đang mở` action bound to the existing resume callback.
- Home no longer renders the family-space menu or sign-out action.
- The fourth tab is labeled `Gia đình` and opens the family hub.
- The family hub keeps child profiles and all current management/profile states, and includes all seven original destinations plus sign-out.
- The family hub does not render an active-run resume CTA; it does not create a duplicate active run.
- Each family destination invokes the same existing callback as before; returning from its child screen lands on the family hub.
- No controller, domain, backend, route, payload, API, or new asset changes are made.
- Static source review confirms only the authorized paths changed. No tests or validators are run.

## Relationship to prior scope

This plan supersedes only the Plan Revision 9 presentation constraints that kept the fourth tab labeled `Hồ sơ`, placed the family-space menu on Home, and retained the active-run resume CTA on the profile screen. All other FEAT-081 decisions and Wave M work remain unchanged.

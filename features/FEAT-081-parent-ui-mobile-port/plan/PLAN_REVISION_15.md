# FEAT-081 Plan Revision 15 — Center Start Action and Activity Tab

## Status and authority

This plan records the owner's direct 2026-11-15 request to make Start a prominent center action and replace the redundant Start bottom-navigation destination. The canonical FEAT-063 v2.7-draft Rev60 SRS does not specify exact bottom-tab labels. The existing Parent history screen is the available destination for an `Hoạt động` tab.

## Goal

Keep four navigation destinations—`Trang chủ`, `Bài giảng`, `Hoạt động`, and `Gia đình`—and place the existing start/resume action as a larger, raised center button between `Bài giảng` and `Hoạt động`.

## Authorized files

| Kind | Path | Incoming bytes | Incoming SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx` | 3,206 | `B700A2A63D3ED4C1F807A5CD6C33C0F0E6C0065E413641A1CBCF36244398B10F` |
| E | `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` | 17,757 | `542CE4B1EB489E8D8E73DEAF055B212F14D5BDFE637EAE58B566B3334984E5D4` |
| E | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 57,857 | `5253F18D4B3FA8074157F6AE7541D3FA049D25489CAA0B63A5FA1AEC931128FD` |
| N | `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_15.md` | — | — |
| E | `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | record pre-append pin in Addendum 30 | — |

## Implementation rules

1. Replace the `start` navigation tab with an `activity` tab labeled `Hoạt động` using the existing history route and `loadRuns` behavior.
2. Add a large raised center `Bắt đầu` action outside the tab list. Preserve its existing behavior: resume an open run; otherwise continue with the selected profile or open family profiles when none is selected. When an open run exists, use a truthful `Tiếp tục` label.
3. Keep the Family menu's existing history entry and return behavior. A history view opened from the center tab returns to Home; one opened from Family returns to Family.
4. Update only the existing source assertion block; add no test case. Do not change API, controller, backend, domain, route contracts, cancellation behavior, or product steps.
5. Run the requested UI checks and repository pre-commit checks. After they pass and the staged file list is reviewed, create exactly one commit for the current uncommitted feature changes. Preserve the two existing unpushed commits without rewriting them; push the branch so all three commits reach `origin/feature/fe-mobile-remediation`.

## Acceptance criteria

- The bottom navigation has four destination tabs plus a visibly prominent raised center action.
- The center action retains existing start/resume/profile-gating behavior and labels an open run as `Tiếp tục`.
- `Hoạt động` opens the existing `Lịch sử buổi học` screen without adding an API or domain flow.
- The two existing unpushed commits remain unchanged; all current intended FEAT-081 changes are represented in one new commit and pushed.

## Relationship to prior scope

This plan extends FEAT-081 only for the bottom-navigation composition, existing history routing, verification, and the owner-requested commit/push. It does not alter Plans 10–14 or authorize edits to `CONTEXT.md` or `DECISIONS.md` beyond preserving their already-present worktree diffs for the requested consolidation.

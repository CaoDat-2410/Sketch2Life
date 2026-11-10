# FEAT-071 Plan revision 1 — Parent profile one-tap switching

- Status: APPROVED
- Prepared: 2026-11-10
- Approved: 2026-11-10 by direct owner instruction after plan review.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; pending formal owner sign-off.
- Runtime target: `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`, local preview on port 5171.

## User request

The owner asks why the P13 child-profile list does not switch profiles like a social app and says navigating through `Chọn mặc định` feels awkward.

## Diagnosis

- P13 and P10 render each profile as a button whose click navigates to `/p10-child-profiles/:childId`.
- Only the detail page calls `setSelectedProfileId`, through `Chọn mặc định`.
- P01 already switches the same selected profile with one-tap child pills.
- The settings row shows `Đang dùng` and a chevron, so it looks like a current-profile selector but behaves as a details link.
- The selection is held only in React state and resets to `child-minh` after a full reload.

## Goal

Let a Parent switch the active child directly from the P13 profile list, with a clear separate path to edit or inspect a profile. Apply the same behavior to the duplicate P10 list so the two lists do not disagree.

## SRS mapping and constraints

- SRS §5.1 / Parent use case: the Parent chooses a child profile before creating a story.
- SRS overview: each story run is associated with exactly one child.
- BR-15 requires the profile context to be confirmed at the relevant prerequisite step; FR-PL-18 requires each generation to use the selected child's drawing and profile context.
- The SRS does not prescribe a Facebook-style switcher, its location, or persistence across sessions. The v2.7-draft remains unsigned, and Parent Web target-client status remains open.
- This is a local FE usability change only. Do not add account switching, API/auth changes, local-storage persistence, or an SRS decision.

## Proposed interaction

1. Tapping an active, non-archived profile selects it immediately; the list stays open and the `Đang dùng` state moves to that profile.
2. A distinct, accessible details action opens the existing profile detail page, preserving edit/archive/consent workflows.
3. Archived profiles cannot be selected; their details and restore flow remain available.
4. P01's existing one-tap selector continues to use the same current-profile state.
5. Selection applies to the current Parent UI session and subsequent story setup. Do not imply that it persists after reload; keep `Mặc định` language out of the switch action.

## Scope

- `apps/parent-ui/src/pages/ParentScreens.tsx`: P13 and P10 profile rows and the detail-page selection copy.
- `apps/parent-ui/src/styles/tokens.css` only if the separate select/details controls need a small responsive layout adjustment.
- FEAT-071 context, decision, approval, status, and evidence records.
- Preserve the existing local P11/P14/P15 authentication diff in `ParentScreens.tsx` and all other in-flight FEAT-036/067/068/069 work.
- Manual review on the active local preview at mobile and desktop/tablet widths, including P13 selection, P10 consistency, P01 selected-profile reflection, profile details, archived state, keyboard access, and P06 preflight child label before a new story.

## Acceptance criteria

1. On P13, tapping a different active profile updates `selectedProfileId` and the visible `Đang dùng` marker immediately without routing to profile details.
2. P10 offers the same select behavior; the separate details action still opens the correct profile.
3. The P01 child selector reflects the selection made on P13/P10 through the shared state.
4. P06 preflight for a new story identifies the selected child; selecting a profile does not change the Parent account or any already accepted video route.
5. Archived profiles cannot become selected, and their existing detail/restore actions remain reachable.
6. Selection and details actions have distinct accessible names, keyboard operation, visible focus, and touch targets of at least 44 CSS pixels where practical.
7. Reload behavior remains session-local for this feature; no storage, API, or billing path is added.
8. No runtime errors or mobile overflow are introduced in the manual local preview walkthrough.

## Approval boundary

No source implementation begins until the owner approves this plan and the approval is recorded in the worktree root `approvals/TASK_APPROVAL.md`. Do not edit the unrelated authentication changes currently present in `ParentScreens.tsx`. Automated tests/builds, commit, push, deployment, publishing, backend/API changes, auth/account switching, persistence, and SRS changes are outside this plan.

# FEAT-070 Plan revision 2 — Fix P06 admission on the served Parent UI

- Revision: 2
- Status: APPROVED
- Prepared and approved: 2026-11-10
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; pending formal owner sign-off.
- Supersedes Plan revision 1 for runtime implementation. Rev1 (hash 5CCF6FC2B5F130C98D6DE5743277FC50BAAAC8AEE10AB8F36504FCECC4FF26A2) was applied in codex/fe-ui-web-remediation, which is not the worktree serving port 5171.

## Goal

Correct the live local Parent UI path so an accepted final-quota request leaves story review and enters video progress. Recheck the full synthetic flow against the current SRS in the actual worktree serving the user's preview.

## Runtime diagnosis

- Port 5171 is served by Vite from F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation/apps/parent-ui.
- That served MobileLayout still had the old copy and called confirmScriptAndStartVideo() before separately checking quotaRemaining to navigate.
- On the active preview, a stable physical pointer click on “Tạo video ngay” with one remaining unit hit the enabled button. The sheet closed, P06 showed the exhausted-quota state, and the URL remained /p06-story-review.
- ParentRoutes has an explicit P07 route; the Sheet button is a native button in a Radix dialog, and the button hit-test passed. The defect is in the admission/navigation result handling.

## Scope

- apps/parent-ui/src/context/ParentContext.tsx
- apps/parent-ui/src/components/MobileLayout.tsx
- FEAT-070 records and append-only approval evidence in this worktree.
- Manual physical-pointer walkthrough against the existing local preview on port 5171, using an isolated browser profile and synthetic state.

## SRS mapping and constraints

- FR-P-08: an adult confirms the final script before video creation; show video after safety reaches VIDEO_READY.
- FR-PL-24 and §31.7 / AC-61: Parent quota belongs to the Parent account; accepted requests consume one unit; an exhausted request is rejected. Amounts remain open.
- FR-PL-16 / §31.5 / AC-52: show outdoor activity only after video.
- The canonical SRS is the v2.7-draft in the main checkout per docs/context/SRS_AUTHORITY.md. Do not use this worktree's stale v2.5 authority text as current requirements.
- Keep the local mock path. No API, auth, billing, provider, data model, or SRS changes.

## Implementation steps

1. Change the admission command to return false when rejected and true when accepted, after consuming exactly one synthetic unit.
2. Make the modal navigate to P07 only when that command returns true; remove the second quota-based navigation decision.
3. Make confirmation copy state the post-use quota, including zero after the last unit.
4. Review the P06 CTA, Sheet, router, P07 progression, and context lifetime for related route/state blockers; keep unrelated behavior unchanged.
5. Re-run on the actual port-5171 worktree using stable physical pointer input after sheet animation settles. Verify a one-unit request enters P07, progresses to READY, and reaches P08 and P08b; verify zero quota keeps the purchase action.
6. Store runtime and source evidence under FEAT-070/evidence.

## Acceptance criteria

1. With one synthetic unit remaining, confirmation shows zero remaining after the proposed use; a real pointer click is accepted, consumes exactly one unit, closes the sheet, and changes the route to /p07-video-job-status.
2. P07 progresses through the preview stages to READY and the flow reaches P08 video then P08b post-video activity.
3. With no quota before a new request, P06 blocks creation and offers the purchase path; the admission command rejects without a route change or quota consumption.
4. The visible server on port 5171 serves the patched source from this worktree.
5. Do not modify FEAT-036, FEAT-067, FEAT-068, FEAT-069, their existing in-progress changes, the canonical SRS, or unrelated files.

## Verification limits

- Manual browser walkthrough is authorized.
- Automated tests/builds, commit, push, deployment, and publication are excluded.
# FEAT-070 implementation and manual verification

- Date: 2026-11-10
- Approved plan: revision 2
- Result: implemented and manually verified on the active port-5171 preview
- Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`
- Runtime: Vite process PID 8124, `http://127.0.0.1:5171`
- Browser: isolated Edge profile, mobile viewport 430 × 932; interactions used pointer coordinates after layout and sheet animations settled.

## Confirmed cause

The active `ParentContext.tsx` called `isLocalPreview()` inside `showToast`, but the module import included only `backendApi` and `hasFirebaseAuthBridge`. A physical click on the enabled P06 confirmation button reached the admission function, consumed the last quota unit, closed the sheet, and then threw `ReferenceError: isLocalPreview is not defined` while displaying the success toast. Because the exception interrupted the function, the click handler never received an accepted result and never navigated to P07.

The failure also occurred when opening the local preview because that path displays a toast. The observed stack traced `showToast` from both `openPreview` and `confirmScriptAndStartVideo`.

## Implemented behavior

- Restored the `isLocalPreview` import in `ParentContext.tsx`.
- Made `confirmScriptAndStartVideo` report rejection (`false`) when the Parent quota is empty and acceptance (`true`) after the synthetic request state is updated.
- Made the confirmation action navigate to `/p07-video-job-status` only when the admission command returns `true`.
- Changed the confirmation message to show the quota remaining after the proposed use, clamped at zero.
- Removed all temporary runtime trace markers after diagnosis.

## Manual walkthrough

All steps used the existing local preview and synthetic data; no API, backend, billing, or video provider was called.

1. Opened `/p06-story-review`; the route guard sent the isolated profile to sign-in. Opened the local preview through its UI button, then followed P01 → P04 capture → P04 subject confirmation → P05 idea confirmation → P06 story review.
2. Used the P06 rewrite action once. The preview updated the scene and script to revision 2, decremented the rewrite allowance from 3 to 2, and displayed its local toast without a runtime error.
3. Opened the approval sheet and confirmed all four checks: drawing, main character, story idea, and five-scene script revision. With two quota units initially available, the post-use copy showed one remaining. Physical-pointer approval routed to P07 and consumed exactly one unit.
4. Waited for the synthetic P07 sequence to reach READY, opened P08 video, then P08b outdoor activities and P08c session feedback. Outdoor activities appeared only after the completed-video screen.
5. Returned home and repeated the capture → subject → idea → review path with one unit left. The P06 approval sheet showed zero remaining after the proposed use. Physical-pointer approval routed to P07 and consumed the last unit.
6. Returned from P07 to P06. The exhausted state showed the warning and `Mua thêm lượt tạo` action; the create-video CTA was absent. Selecting the purchase action opened P12. The purchase screen was inspected only; no payment simulation was submitted.
7. No runtime errors were recorded after the import fix. Both changed modules returned HTTP 200 from port 5171, and the served context module contained the restored import with no diagnostic trace code.

## Evidence files

- `p06-approval-confirmation.png`
- `p07-video-job-status.png`
- `p08-video-complete.png`
- `p08b-outdoor-activities.png`
- `p06-last-quota-confirmation.png`
- `p06-quota-exhausted.png`
- `p12-quota-topup.png`
- `repro-active-p06-modal.png` (initial runtime reproduction)

## Requirements and limits

The walkthrough was checked against FEAT-063 SRS v2.7-draft Rev57: FR-P-08 final adult script approval; FR-PL-24 / §31.7 / AC-61 Parent-account quota consumption and rejection when exhausted; and FR-PL-16 / §31.5 / AC-52 outdoor activities after video. The canonical SRS remains unsigned; Parent Web target-client status and quota amounts remain open. No requirement or quota amount was inferred from older SRS copies.

Automated tests and builds were not run because the approved plan excludes them. No commit, push, deployment, or publication was performed. Existing unrelated worktree changes were preserved.

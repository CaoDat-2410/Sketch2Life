# FEAT-070 Plan revision 1 — Parent Web video admission demo fix

- Revision: 1
- Status: APPROVED
- Prepared and approved: 2026-11-10
- Product authority: FEAT-063 SRS v2.7-draft Rev57, pending formal owner sign-off.

## Goal

Make the local Parent UI preview report and apply the video quota decision consistently. After an accepted script/video request, continue to the video progress screen even when that request uses the last synthetic quota unit.

## Scope

- apps/parent-ui/src/context/ParentContext.tsx
- apps/parent-ui/src/components/MobileLayout.tsx
- FEAT-070 records and append-only task approval evidence.
- One manual local-preview flow through story review, video progress, and post-video playback/activity.

## SRS mapping and constraints

- FR-P-08: adult confirmation of the final script precedes video creation; show video at VIDEO_READY after safety.
- FR-P-05 and AC-52: post-video activities appear after video.
- FR-PL-24 and §31.7: Parent video usage belongs to the Parent-account quota; reject a request when that scope is exhausted.
- AC-61: an accepted Parent request uses Parent-account quota.
- SRS quota amounts and Parent Web target-client status remain open. Synthetic preview values do not settle either question.
- Keep the existing mock adapter path. Do not add API, authentication, billing, provider, or persistence behavior.

## Implementation steps

1. Trace the story-review confirmation, quota mutation, and navigation callback.
2. Make the admission action return whether it accepted the request; use that result as the sole condition for navigating to video progress.
3. Make the confirmation copy state the remaining quota after the accepted use.
4. Preserve exhausted-quota rejection without consuming quota or navigating.
5. Run one complete synthetic Parent UI preview flow, inspect the quota boundary and P07-to-P08 transition, and record evidence.

## Acceptance criteria

1. With at least one synthetic unit, confirming the script accepts exactly one request, consumes exactly one unit, closes the confirmation sheet, and navigates to P07, including when the remaining count becomes zero.
2. The confirmation sheet accurately displays the remaining count after the proposed one-unit use.
3. With zero units before confirmation, admission is rejected, no quota is consumed, and the flow stays on story review with the purchase path available.
4. The existing local preview advances through video progress and then to the video/playback and post-video UI. No real API or provider call occurs.
5. Only the two listed app source files and FEAT-070 records change; FEAT-036 and other pre-existing work remain untouched.

## Verification

- Manually run one local Parent preview flow, using synthetic data.
- No automated tests, build, commit, push, or deployment are included.
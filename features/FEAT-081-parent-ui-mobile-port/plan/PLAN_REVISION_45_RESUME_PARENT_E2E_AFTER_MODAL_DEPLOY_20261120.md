# FEAT-081 — Plan Revision 45: resume Parent E2E after Modal app deployment

**Status:** APPROVED by the owner's active direct request to run the Parent workflow end to end without quota, and the follow-up instruction to deploy the missing Modal app.  
**Worktree:** `<local-machine-path>, branch `feature/fe-mobile-remediation`.  
**Product authority:** FEAT-063 canonical working SRS v2.7-draft / Rev67; unsigned.  
**Related run:** Plan Revision 43 / Addenda 70–73. The missing app is now deployed. The activity request failed before Modal accepted a call, so it performed no model inference.

## Goal

Continue the existing real Android Parent UI flow from the saved synthetic run and reach the farthest successful stage, including a silent technical video candidate if every upstream stage and human-review gate passes.

## Approved scope

1. Reuse the existing synthetic Parent, synthetic child profile, StoryRun, and generated synthetic turtle drawing from Rev43. Do not rerun drawing analysis or create duplicate account/profile/run data.
2. Use the real Expo UI and task API. Send exactly one fresh activity-suggestion request after the Modal app deployment; the prior 504 was `NotFoundError` before a Modal call ID, so no activity model inference occurred.
3. If activities return and persist, select one in the real UI and request exactly one story generation. Review the exact visible story and its server revision/hash as the adult test operator; do not confirm if malformed, unsafe, or mismatched to the drawing/activity.
4. If the adult review and server confirmation succeed, submit at most one silent LTX-2.5 technical candidate through the real Parent UI and the existing local/test synthetic no-quota candidate guard. Do not use product-ready or `VIDEO_READY` labels.
5. Capture sanitized timings, request/job/attempt/Modal IDs, UI screenshots, and candidate output if produced; update the Rev43 report plus FEAT-081 context/status.

## Limits

- Synthetic data only; no fixtures, prerecorded API results, direct business-row DB inserts, or scripted endpoint calls to skip the UI.
- No drawing re-inference, no activity retry after the single post-deployment request, no story retry, no video retry, no warm-up, no scene retry, and no other Modal function invocation.
- Do not read or mutate quota/billing records. The only no-quota path is the existing explicit local/test + `modal_dev` + synthetic candidate guard. If any guard rejects, stop before Modal video dispatch.
- Preserve consent, age, authorization, activity, story, hash, privacy, safety, and ownership gates. The video remains a private technical candidate; do not bypass safety or claim product playback/readiness.
- Do not deploy, stop, or modify other Modal apps; do not modify `.env`, secrets, Volumes, migrations, or unrelated services. Preserve all existing worktree changes. No commit/push.
- If the emulator/API state cannot safely resume the same run, or a stage fails, stop and record the exact safe failure. Do not silently create a replacement run that would repeat an already successful AI stage.

## Acceptance

- The real UI reaches activity selection and one story review with the saved run, or reports a correlated, specific blocking failure.
- If human and server gates pass, one technical video candidate is generated and shown in the authenticated private preview; otherwise no video request is sent.
- Every actual inference has a correlated API/Modal outcome and sanitized evidence. No fixture or quota-ledger mutation occurs.

## Evidence

Append to `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/`.

# FEAT-075 Plan Rev1 — Final Parent FE demo-flow SRS UI/UX review

- Revision: 1
- Status: APPROVED by the owner’s direct request in this conversation; exact plan hash will be recorded before implementation.
- Prepared: 2026-11-10
- Active worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned and awaiting formal owner sign-off.

## Owner request

“Sau đó check UI/UX theo luồng của SRS lần cuối cho tôi có lỗi thì sửa ko thì trả báo cáo đã check gì chạy luồng như nào cho tôi và đợi yêu cầu tiếp theo”.

This is the final SRS-aligned manual UI/UX review and complete local FE demo run. The user explicitly requires this work to happen in the fe-ui-full-remediation worktree, not the main checkout.

## Goal

Run and inspect the Parent story-to-video demo flow at the local preview, identify verified interaction, navigation, state, accessibility, and responsive UI defects, fix in-scope defects, and leave a feature-local record of the exact run and result.

## SRS scope

Use only FEAT-063 v2.7-draft Rev57 §§5.1, 6.2.2, 7.2, 7.4, UC-01/UC-02, and the applicable BR/FR/AC records as current requirements. Parent flow includes:

1. Parent preview sign-in and selection of exactly one child profile.
2. Optional lesson/line-sketch path or skip; capture one synthetic drawing.
3. Review/confirm one subject, entered idea/transcript, and minimum profile context.
4. Generate the initial story; allow at most three AI rewrite suggestions and require the adult to review the new revision.
5. Confirm the final script/storyboard and quota admission before starting video.
6. Show asynchronous video progress and recoverable failure/safety states; enable playback only at READY after automatic checks.
7. Show pinned lesson activities only after playable video; allow completion/feedback and inspect the resulting Parent history.

No-preset activity catalog behavior remains OPEN under §31.10(13); preserve the existing distinction and do not infer a new policy. The run uses synthetic fixture data only.

## Acceptance criteria

1. The manual flow reaches the intended screens in SRS order and keeps the selected single-child context visible and consistent.
2. Subject, transcript/idea, context, script revision, rewrite allowance, script confirmation, quota, job progress, READY playback, post-video activities, and history state have clear and accurate UI feedback.
3. The P06 “Duyệt kịch bản & Tạo video” sheet’s “Tạo video ngay” action visibly transitions to P07 after successful local admission, closes the sheet, and does not navigate on rejected quota admission.
4. A rewritten script is presented as a new revision and requires explicit adult confirmation before video admission. No direct scene editing is introduced.
5. Playback cannot be reached as ready before the job fixture reaches READY; post-video activity controls are available only after video readiness.
6. Critical phone and tablet screens are readable, touch/keyboard navigable, and have no horizontal overflow, inaccessible blocking overlay, or browser runtime exception during the reviewed flow.
7. Any code change is limited to verified Parent FE defects in this flow and uses existing demo state/contracts. Do not add API/backend/auth/persistence behavior or close SRS open questions.
8. Feature-local evidence documents the route/viewport/interaction sequence, findings, fixes, and verification boundaries.

## Review and implementation steps

1. Compare current Parent screens/state transitions against the cited SRS and reproduce the reported P06 create-video transition at the active local preview.
2. Execute the complete happy path at phone viewport; inspect the optional lesson/guide branch and relevant rewrite/quota/recoverable-status states where the preview allows.
3. Inspect relevant key screens at a tablet viewport and check keyboard focus, modal close/return behavior, and responsive overflow.
4. Fix only defects reproduced during review, preserving unrelated worktree changes.
5. Re-run the affected interaction(s) and the complete FE demo path; save screenshots and a concise evidence report under this feature.

## Boundaries

- FE-only local preview. No API/backend/provider job or real video is called; all identities, artwork, audio, story, quota, and playback are synthetic fixture data.
- Do not modify the canonical SRS, source register, API contracts, persistence, auth model, billing policy, or global product decisions. Preserve all OPEN-OWNER/OPEN-TECHNICAL questions.
- Keep all edits and evidence in the user-designated worktree. Do not copy work into F:/Github/Sketch2Life.
- Preserve pre-existing modified/untracked worktree files; do not reset, clean, or overwrite unrelated work.
- No automated tests/builds unless required to diagnose a reproduced defect; no commit, push, deploy, or publish.
- No external/generated visual assets. This is an interaction and usability audit of the established UI.

## Verification

Manual local Edge/browser interaction is required by the user’s request. Automated test/build commands, API integration and production behavior are outside this plan. Record browser/viewport, test path, exact routes, edge states, results, and limitations in feature-local evidence.

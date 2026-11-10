# EV-075-01 — Final Parent FE SRS flow review

- Review date: 2026-11-10
- Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`
- Preview: `http://127.0.0.1:5171`
- Browser: isolated Edge/Chromium session
- Main viewport: 390 × 844; responsive checks at 320 × 800 and 768 × 1024
- Requirement baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`
- Data boundary: local FE preview only. Profiles, artwork, transcript, story, quota, job progress and playback were synthetic; no API, microphone, video provider, or backend persistence was used.

## Review result

The reported P06 navigation failure did not reproduce in the active preview: on a newly admitted demo run, **Tạo video ngay** closed the preflight sheet and routed to P07. The review did find and fix two other issues in the same flow:

1. The seeded fixture showed a video job already running while its script was marked unconfirmed. Returning from P07 to P06 therefore offered another rewrite/admission and could consume quota for a second request on the same run. The seeded script now starts as accepted; a context-level in-flight guard rejects duplicate admission; P06 and the preflight sheet show/retain the accepted-job state. A new draft resets the script state and still has the normal review and admission path.
2. The shared accessible sheet trapped Tab and closed with Escape, but focus fell to the document body. `AccessibleDialog` now returns focus to the element that opened it when that element is still mounted.

## SRS trace

| SRS area | Manual check | Result |
|---|---|---|
| BR-02 — at most one unfinished run per adult | Home while a run is active; attempted new-run entry; returned to P06 from the active P07 job | New-run entry is blocked; accepted run offers **Tiếp tục câu chuyện** and cannot start a duplicate request. |
| FR-P-02/04/06, BR-14/15/19 — one child, subject and approved profile context | Selected Bé An; confirmed the detected subject; reviewed age band, interests, learning notes and pinned lesson direction on P05; checked the privacy exclusion note | P05 and P06 preflight show Bé An consistently. Continue/skip are blocked until subject and context are confirmed. Context remains separate from the idea transcript. |
| FR-P-03, BR-23 — adult transcript review | Used the local recording fixture, stopped it, and inspected the generated sample transcript | **Tiếp tục** and **Bỏ qua ý tưởng** remain disabled until the parent checks the transcript review control. The preview clearly states it did not use a real microphone. |
| FR-P-05, §31.10(13) — lesson activity catalog | Completed a run without a pinned lesson and a run pinned to “Vòng đời bướm” | No-preset run shows an empty-state explanation and does not inherit the default lesson activities. Pinned run shows only its lesson activities and safety notes. The catalog policy remains OPEN; this fixture behavior does not decide it. |
| FR-P-07, BR-13 — rewrite cap and revision review | Requested one rewrite | P06 advances from revision #1 to #2, updates the suggested scene, shows 2/3 remaining and requires a fresh explicit approval before admission. |
| FR-P-08, BR-11/38 — final script approval, accepted request and quota | Inspected the P06 preflight, then activated **Tạo video ngay** on a new draft | The sheet shows one child, subject, idea state, context approval, script revision and quota consequence. Successful admission closes the sheet and routes to P07. Accepted/in-flight requests cannot consume a second unit. |
| FR-P-08, BR-16 — playable only after READY | Followed P07’s synthetic progress to READY, entered P08, played, paused and replayed | P08 starts at `00:00`, shows scene 1/5, captions and private in-app playback copy. Playback advanced and stopped at 01:00. P08/P08b redirect to P07 if the job is not READY. |
| Parent completion and history | Completed P08b, submitted a five-star feedback fixture and opened P09 | P09 shows the completed “Vòng đời bướm” run under An, with five scenes and recorded feedback. The no-preset run also appeared in history with its own story title. |
| Shared dialog keyboard behavior | Used Tab and Escape on P06 preflight and the P08 suitability sheet | Tab stays inside the sheet; Escape closes it and returns focus to the opening button. Verified again after the focus-restoration fix. |

## Demo sequences executed

### Active seeded run and duplicate-admission retest

`P01 → P07 → P06 → P07 → P08 → P08b → P08c → P01 → P09`

- P01 showed the active run and blocked new-run entry.
- Before the fix, P06 incorrectly offered another admission even though the seeded job was already RUNNING. The preflight still offered a quota-consuming button.
- After the fix, P06 showed that the request was already accepted and offered only **Tiếp tục câu chuyện**. Returning to P07 continued the existing job.
- The seeded no-preset run reached READY, opened P08 at 00:00, showed no lesson activity fallback, completed, and appeared in P09.

### New lesson-pinned run

`P01 → optional lesson picker → P02 → P04 → P05 → P06 → preflight → P07 → READY → P08 → P08b → P08c → P01 → P09`

- Selected profile Bé An and pinned “Vòng đời bướm”; visited P02 and the optional P03 line-sketch guide, then used the allowed skip-to-capture action for the full run.
- Used the synthetic library image, confirmed “Con bướm,” entered an idea and approved the profile context.
- Checked the rewrite revision and P06 preflight; the new-run preflight remained enabled and the create action still routed to P07 after the duplicate guard was added.
- P07 reached READY; P08 opened at 00:00/Cảnh 1; P08b displayed the two pinned activities and their safety instructions.
- Submitted feedback and confirmed P09 listed the completed five-scene story under An.

### P06 and shared-sheet retest after focus fix

`P04 → P05 context approval → P06 → preflight → P07`

- Confirmed P05 actions were disabled before context approval.
- Opened the P06 sheet, verified Tab containment and Escape focus return, reopened it and activated **Tạo video ngay**.
- Confirmed the sheet closed, route changed to P07 and no Vite error overlay was present.

## Responsive and runtime observations

- At 320 × 800, 390 × 844 and 768 × 1024, the document/body width matched the viewport; no horizontal overflow was found on the reviewed routes.
- The 768px preview expands the app shell to 740px and keeps the bottom navigation visible; reviewed content remained readable and scrollable.
- No browser/Vite runtime error overlay appeared during the final rerun.
- Automated tests/builds were not run. Verification was the requested manual FE demonstration in the local preview.

## Evidence images

- `p01-active-run-gate-390.png` — active-run entry guard.
- `p04-subject-390.png` — synthetic subject selection.
- `p05-context-review-final-390.png` — profile snapshot, privacy note and unapproved state.
- `p06-active-request-accepted-390.png` — P06 state after an existing run is accepted.
- `p06-preflight-final-390.png` — final preflight fields, focus ring and quota consequence.
- `p07-ready-390.png` — READY state from the initial review run.
- `p08-player-postfix-390.png` — final phone player, beginning at 00:00.
- `p08-player-final-390.png` — playback at completion with captions.
- `p08b-no-preset-empty-390.png` — no-preset empty state.
- `p08b-pinned-activity-postfix-390.png` — pinned lesson activities and safety guidance.
- `p09-history-postfix-390.png` — completed run and feedback at phone width.
- `p09-history-320.png` — narrow phone layout.
- `p09-history-768.png` — tablet-width history layout.

## Limits retained

- This preview is synthetic and does not prove API admission, persistent quota accounting, real audio/video playback, moderation, or backend history persistence.
- Safety-blocked/service-error recovery fixtures were not selectable through the reviewed UI, so those branches were not exercised.
- FEAT-063 v2.7-draft remains unsigned. §31.10(13)’s no-preset activity catalog question remains open.

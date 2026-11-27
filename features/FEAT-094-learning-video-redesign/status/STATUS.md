# FEAT-094 status

**State:** APPROVED (Rev 2 option A and Amendment A, 2026-11-26). In progress.

| Phase | State | Evidence and notes |
|---|---|---|
| 0 | verified in the app | Activity step passed live on the first answer. Run history loads on first open. 16:9 video of 30 s in 9 min 26 s (`evidence/M3_app_run/RUN.md`). |
| 1 | done (E1-E3 and S0-S4) | `evidence/M1_experiments/`. One seed per variant; the owner has not judged the videos. E5, E6 not run. |
| 2 | done and verified outside the app | One L40S prepares and renders; 657 s with a cold Qwen, 395 s warm (`evidence/M4_two_containers/RUN.md`). Warm-up at story review (S6) not yet seen in the app. Qwen and video images now install from locks; Debian packages not pinned. S7 (early keyframes) not built. |
| 3 | waiting for the owner | Card rules, review tool, selection and model drafting are wired in. The 40 cards now name the pages they were compared with (141 facts supported, 81 partly, 19 not found: `evidence/M6_remaining/CARD_SOURCE_REVIEW.md`) and are **still DRAFT**: the owner approves them. |
| 4 | live outside the app | Learning script v2 as before; a setting may not name an animal; fast actions are rewritten. Lines are still 11 to 13 words where 14 to 18 are asked. Writing 25 to 27 s warm. ADR-0027 proposed. |
| 5 | live outside the app, one known defect | Zoomed background plates, edge measure, six-frame model check, first-frame check with repaint, contact shadow, part labels. Run 4: 623 s for 50 s of video; one scene pans (reported). Visual check stays in `report` mode. Not built: paper-gap removal inside the cut-out. (`evidence/M6_remaining/RUN.md`) |
| Amendment A screens | code done, offline tests only | As before, plus: a reload takes the existing activity suggestions. Not yet seen on a device (the emulator app waits for a new sign-in). |
| 6 | deferred by the owner (2026-11-27) | The 30-drawing evaluation. |

## Open

- The new screens and the learning flow through the app.
- Decision for the owner: scene length follows the voice (less silence, fewer frames) instead of a fixed 10 s.
- Decision for the owner: turn the visual check from `report` to `enforce` (render again up to twice, then fail).
- The false-positive rate of the checks on other drawings is unmeasured (fifteen scenes of one drawing).
- Early keyframes (S7) and E5, E6, S8 are not done (conditional or low value, see `evidence/M6_remaining/RUN.md`).

## Deviations from the plan text

- The backend filters activity drafts one by one but still offers exactly three (SRS section on activity suggestions).
- Plan 10 foresaw `story-revision.v2` and a migration; the stored contract stays v1 and the learning script sits inside
  the story content (Amendment A).
- Plan 8.2 part labels (D1) are shown without arrows: recognition gives no part positions.
- Plan 7.1 mask cleanup is not built: removing paper-coloured areas would punch holes into uncoloured subjects.

Note: another session moved the dev Modal runtime to workspace `siesta-6107` on 2026-11-26 (FEAT-095).

# FEAT-094 status

**State:** APPROVED (Rev 2, option A, 2026-11-26). In progress.

| Phase | State | Evidence and notes |
|---|---|---|
| 0 | code committed (`620e06a3`); app verification: first video **failed**, second attempt running | Activity step passed live on the first answer (262 s with a cold Qwen). Run history loads on first open. The first video failed on a 25 fps defect, fixed and deployed (`evidence/M2_normalize/FINDING.md`). Truncated confirm button not yet reproduced. |
| 1 | done (E1-E3 and S0-S4) | `evidence/M1_experiments/RESULTS_SPEED.md`, `RESULTS_QUALITY.md`. One seed per variant; the owner has not judged the videos. E5, E6 not run. Experiment MP4 files stay local. |
| 2 | partly done, video app deployed to dev, live result pending | fast profile with out-of-memory fall-back, prompt cache, decoder compile in the warm-up; backend sends all scene prompts after planning. ADR-0026 proposed. **Not done:** merge of scene preparation into the video app (two-container limit), warm-up at script review, early keyframes, pinned image dependencies. |
| 3 | partly done | card rules, repository, review tool, 40 cards **all DRAFT without sources**; AI drafting and wiring into the script not started |
| 4 | not started | |
| 5 | started, motion-only LTX prompt deployed to dev | Still open: end frame in the Parent pipeline, mask cleanup, output checks, regeneration |
| 6 | not started | |

## Findings of the 2026-11-26 app run

- Resuming a run after signing in shows "Chọn một hồ sơ để kiểm tra điều kiện bắt đầu" and goes back to the context
  review, because no profile is selected.
- A cold Qwen start makes the activity request outlast the app's wait. The reload then starts a second suggestion set
  instead of showing the stored one.

## Deviations from the plan text

- The backend filters activity drafts one by one but still offers exactly three (SRS section on activity suggestions)
  instead of a shorter list.
- The phase 0 verification videos run with scene preparation still in its own app, so up to three L40S containers can be
  active. Stopping the idle Qwen container during a run was refused by the permission check.

Note: another session moved the dev Modal runtime to workspace `siesta-6107` on 2026-11-26 (FEAT-095).

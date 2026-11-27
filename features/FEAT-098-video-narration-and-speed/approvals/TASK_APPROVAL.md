# Task approval

- Status: APPROVED, plan Rev 1 (`plan/PLAN_REV1.md`)
- Approver: project owner, in chat, 2026-11-27. Words: "Duyệt Rev 1".
- Covers: part A (narration), part B (speed: S1 to S3 switched on, S4 to S6 behind settings, off), part C (offline
  checks, one batched GPU session, one full video through the app) within up to 45 minutes of L40S plus the story model.
- Owner inputs on 2026-11-27 (chat, answers to questions before the plan was written): more narration and knowledge
  without a longer video; AI-generated motion for longer narration; try the pasted speed tips; run the video test after
  everything is finished.
- Not covered: switching on S4 to S6 (needs the owner's look at the clips), a second full video, commit, push, SRS
  change.

## After the measurement (2026-11-27, in-app question with the side-by-side clip delivered first)

- Speed options: the owner chose **"VAE + 960×576"** (S4 and S5 on; S6 stays off). The engineer had recommended the
  convolution VAE alone; the two options together were not measured, and S5 alone showed softer lines and a smeared
  head near the end of the test clip. The question said so.
- Amendment A, spoken-text filter: the owner chose **"Sửa luôn"** — compare with Vietnamese accents so that "súng" and
  "tự tử" stay refused while "sừng", "từ từ" and "bổ sung" are spoken. Text typed without accents is still compared
  without them.

## During the app run (2026-11-27)

- First-story path: the owner chose **"Sửa rồi chạy video"** after being told the app's first story never asked for the
  learning script. The question named the first story and the rewrite; only the first story was changed, because the
  app's rewrite is refused for another reason (see `evidence/README.md`).
- Cancelling the first test run (`04be37ea`, created in this session, synthetic drawing, no video): the owner chose
  **"Hủy và chạy tiếp"**; the question said its content is deleted for good.

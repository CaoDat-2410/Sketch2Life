# FEAT-087 task approval

## Design Rev1 — Subject roles and keyframe-conditioned LTX video

- **Status:** APPROVED_FOR_IMPLEMENTATION (2026-11-24)
- **Document:** `plan/DESIGN_REV1_SUBJECT_ROLES_KEYFRAME_VIDEO.md`
- **Owner choices recorded 2026-11-24:** approach 2 (SAM masks + composited start/end keyframes); direction B (main subject may move, keyframes keep original strokes); parent views and lightly edits main/secondary roles; live-inference package approved as a whole (§6.9) once the design is approved.
- **Approval:** Project owner, direct instruction in chat 2026-11-24 13:25 (UTC+7): "tiến hành cái plan này, có thể sử dụng skill của replicant mcp để test UI android" with Design Rev1 attached. This approves the design, M0–M7 and the one-shot live-inference package in §6.9 (deploy 3 dev Modal apps; M1 x4, M4 x3, M6 x2, M7 x3). Android UI testing through the replicant/adb-mcp tools is authorised for M3.
- **Implementation:** may start. Stop-and-report conditions stay as in the design: M0 failure, any live step failure (no retry/no bu), anything outside §6.9.
- **Delivery:** No commit or push.

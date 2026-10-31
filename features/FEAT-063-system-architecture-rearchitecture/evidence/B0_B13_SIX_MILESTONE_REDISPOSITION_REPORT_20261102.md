# B0–B13 redistribution to the six-milestone roadmap

- Date: 2026-11-02, Asia/Ho_Chi_Minh.
- Scope: documentation-only, authorized by the project owner in this thread.
- Approved plan SHA-256: `03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582`.

## Disposition recorded

- The B0–B13 backlog remains as historical traceability, but is no longer the active execution sequence.
- Milestone 1 is only the StoryRun-lite S1→S2 demo goal. No old B task is added to that milestone. Passing S1→S2 offline/loopback acceptance is not evidence of a live Modal call.
- B0a/B1/B2 are recorded as prior analysis/decision work; B0b stays unresolved but nonblocking. B3's old unsigned manifest is not an execution approval. B4a and B8 are marked as old-path work that is not repeated for the photo-based demo. B5 and B6/B7 remain conditional or require a new plan if their legacy requirements are retained.
- B9–B13 are redistributed across milestones 2–6: inputs to M3, story/script to M4, video to M5, foundation and identity/jobs to M2, and quota/lifecycle/billing/organization/integration acceptance to M6. B12 remains a test gate across M2–M6.
- The SRS and Data Table Register requirements were not deleted or amended by this task. Future implementation still requires its own reviewed plan and approval.

## Files updated

| File | SHA-256 after update |
|---|---|
| `plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md` | `03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582` |
| `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md` | `2CAB64B6F45F2B1851F0B3AFD11ADD623A3D6BFD125D70908EF9617E74B62118` |
| `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md` | `875E93C59085DA9C38923DB85EEE50D15945CBD38EC27EC0B6389B93B3ECB8D4` |
| `approvals/TASK_APPROVAL.md` | `DF15DEFE2846FB354C438A62BC2AD4CFDC817EAB1F90C61DF31B7803468BDE6B` |

## Verification and limits

- `git diff --check` on the changed tracked documentation returned no whitespace errors (exit 0). Git printed a CRLF-to-LF normalization warning for `approvals/TASK_APPROVAL.md`; no line-ending conversion was run by this task.
- No tests or validators were run because this change only updates planning documents.
- No implementation code, SRS, DTR, migration, database, Modal/provider/GPU, or runtime was touched.
- The separate StoryRun-lite S1→S2 goal remains active. This documentation update does not change its implementation status, authorization, or live-Modal boundary.

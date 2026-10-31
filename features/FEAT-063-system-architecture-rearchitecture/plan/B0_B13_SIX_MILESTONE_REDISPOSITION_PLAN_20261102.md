# B0–B13 → lộ trình sáu mốc: kế hoạch cập nhật hồ sơ

- Status: **APPROVED** for the documentation-only scope below by the project owner's direct instruction in this thread on 2026-11-02.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Date: 2026-11-02, Asia/Ho_Chi_Minh.
- Scope: documentation-only update to distinguish the active StoryRun-lite S1→S2 demo from the legacy B0–B13 backlog and map still-relevant work into milestones 2–6.
- No implementation, schema, migration, SRS requirement deletion, database, Modal/provider/GPU, deployment, commit, or push is included.

## 1. Sources to reconcile

- `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md` — historical B0–B13 planning backlog; it is DRAFT and does not authorize execution.
- `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md` — current six-milestone coordination roadmap.
- `plan/STORYRUN_LITE_S1_S2_MASTER_GOAL_20261102.md` — the active S1→S2 photo-based demo scope; it excludes live Modal and the old A2/B1/B2 canvas goals.
- Current FEAT-063 context, decisions, source register, approvals, and SRS/DTR as read-only project context.

## 2. Documentation changes

1. Preserve the historical B0–B13 task definitions. Add a dated disposition that the backlog is no longer the active execution sequence.
2. Update the six-milestone roadmap so milestone 1 is satisfied by the S1→S2 implementation and its offline/loopback acceptance only. Do not imply that this proves a live Modal call.
3. Map still-relevant work from B0–B13 into milestones 2–6. Mark completed, unresolved/nonblocking, conditional, and superseded items separately.
4. Explicitly disambiguate legacy Rev36 B6/B7 S1/S2 from the current StoryRun-lite S1→S2 goal.
5. Keep the SRS draft and requirements intact; this is a planning disposition, not a requirement deletion or implementation approval.
6. Add an evidence note listing the resulting disposition, changed-file hashes, and verification performed.

## 3. Acceptance criteria

- The roadmap says milestone 1's demo deliverable is the current S1→S2 scope; no B0–B13 implementation task is added to it.
- The roadmap maps B3–B13 that remain relevant to milestones 2–6 and marks B0–B2, B4a, and B8 according to their recorded status/legacy role rather than silently deleting them.
- B0b remains explicitly unresolved/nonblocking; B5 and B6/B7 are conditional/replanned rather than assumed accepted for the new flow; B9–B13 remain requirement buckets to be re-planned, not ready-to-run goals.
- The old backlog remains available as historical traceability and clearly points to the six-milestone roadmap as the current planning view.
- Only the plan, approval entry, backlog, roadmap, and evidence note are changed. No active S1→S2 code, migration, DB, provider, or test data is touched.
- `git diff --check` is clean for the documentation changes.

## 4. Explicit exclusions

- Do not change implementation code, tests, migrations, SRS requirements, or Data Table Register schema.
- Do not resume A2, old FEAT-064 B1/B2, old Rev36 implementation, or any B0–B13 goal.
- Do not call Modal, GPU, an external provider, or a network service; do not access databases.
- Do not stage, commit, push, merge, reset, stash, or clean.

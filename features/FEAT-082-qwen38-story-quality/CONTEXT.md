# FEAT-082 — Qwen3.8 FP8 story quality

## Goal

Use the pinned Qwen3.8-27B-FP8 checkpoint for shared development text workloads and improve Parent story quality without changing the drawing VLM. Amendment J extends verification through the real synthetic Parent Android UI and a silent LTX-2.5 video candidate.

## Authority and boundaries

- Current product authority is the unsigned FEAT-063 SRS v2.7-draft. This feature's development preview does not amend product requirements or establish production readiness.
- Shared Modal text workloads use pinned Qwen3.8-27B-FP8. Drawing understanding remains on Qwen3.5-9B. LTX-2.5 is a separate video workload.
- Parent AI inputs remain minimized: no raw drawing bytes, profile identity, Firebase identity, or unrestricted free-text interests are passed to the Qwen text worker.
- Activity selection is persisted from the actual UI before story generation; the backend pins and validates the selected activity.
- All live run data was synthetic. No fixture, direct worker call, database state mutation, quota bypass, or safety bypass was used.
- No commit or push is authorized by this task.

## Latest verification — 2026-11-23

The real Parent UI → API → Modal path passed drawing analysis, activity fallback, story generation, one adult-directed rewrite, adult confirmation, video generation, status polling, and full in-app playback to 0:30. The final video call used LTX-2.5 on L40S and completed five scenes; details and request/call IDs are in `evidence/ANDROID_UI_RUN_20261122/RUN_LOG.md` and `evidence/PARENT_E2E_FINAL_SUMMARY_20261123.json`.

Focused Modal contract tests passed (82). The final live activity/story/video passes had no terminal API/worker errors. Earlier distinct runtime failures and their fixes remain in the chronological run log.

## Open limitations

- The accessible published/shared lesson catalog returned no eligible activity for the test context; the AI fallback returned three valid suggestions and the adult's selection persisted.
- Story revision 1 added an unsupported water/raft event; one allowed UI rewrite corrected it, and the adult confirmed revision 2.
- The video preserved recognizable child-drawing colors and texture and kept both turtle and leaf visible, but review found a transient text-like artifact and relative-position drift/overlap in middle scenes.
- The UI labels the video “Bản thử nghiệm · Chưa kiểm tra an toàn.” It is not evidence that the SRS automatic video safety gate passed. This task's silent candidate also does not satisfy the canonical SRS narration/subtitle target.
- Treat this as a successful technical development E2E, not a production-quality or safety-cleared release.

## Runtime cleanup

Cleanup completed after evidence capture: stopped `emulator-5562`, the worktree Expo server, only the `s2l-feat081-rev23` containers, and the Modal drawing, language/audio, and video apps. Other Compose projects stayed running; Modal lists the three task apps as stopped with zero tasks. No containers/volumes were deleted and no persistent data was removed.

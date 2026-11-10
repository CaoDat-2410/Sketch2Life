# Parent Android demo flow — implementation note

- Date: 2026-11-10
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation
- Branch: feature/fe-ui-full-remediation
- Governing record: FEAT-069, approved plan revision 1; approved plan SHA-256 remains recorded in approvals/TASK_APPROVAL.md.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, pending formal owner sign-off.

## Implemented

- AppRoot opens the Parent Android demo by default and retains the previous fixture flow under a separate Fixture lab route.
- Parent screens depend on ParentWorkflowPort. The local ParentDemoWorkflowAdapter is selected in app composition and can be replaced when an approved API adapter is ready.
- Demo profiles, run/story data, default transcript/subject, context, guide, post-video activity, quota and reminder live in the demo infrastructure. ParentWorkflowSnapshot exposes screen content, so Parent screens do not import demo fixture data. Legacy fixture contracts are isolated separately.
- The demo covers sign-in, registration, recovery, profile selection/creation, one active run, drawing/idea, optional guide, upload interruption/resume, transcript/subject/context review, story rewrite, video status/retry/playback placeholder, post-video activity, history, delete, quota, reminder and sign-out/reset.
- Explicit review actions, stage-aware back navigation, transcript/subject change invalidation, three story rewrites, two replacement requests, quota accounting and recovery messaging are represented in the adapter.
- Layout switches at 760 px, limits tablet content width, stacks on phone widths, wraps tablet grids and keeps touch actions at least 44 px high.

## Acceptance coverage

- AC1–AC2: Parent default route, separate fixture lab, typed port and centralized replaceable demo content.
- AC3–AC5: Source flow implements the approved stages and limits; activities are reachable only after video readiness.
- AC6: Registration/recovery, auth, capture, audio, guide, upload, quota and video remain clearly demo-only; no API/provider/native capability is called.
- AC7: Responsive phone/tablet layout is implemented in source. No device visual review was performed.
- AC8: Changes for this task are confined to apps/mobile and FEAT-069 in the selected FE worktree. Existing FEAT-036/067/068 and Parent Web worktree changes were preserved.

## Verification and limitations

- git diff --check completed with no whitespace errors after the final cleanup.
- No tests or builds were run because the approved task explicitly excludes them.
- The app was not launched on an emulator/device. Native rendering, tablet orientation and Android package compilation remain unverified.
- All state is in memory and synthetic. A reload starts a fresh demo. Auth, API persistence, native camera/gallery/microphone, upload bytes, notifications, AI generation, quota billing and real video playback are not connected.
- The canonical SRS is still a draft awaiting formal owner sign-off.

## Follow-up UI correction — 2026-11-10

- Root cause: REQUEST_VIDEO changed readiness data but left the app snapshot on video-status, so the result appeared in the same UI and had no dedicated playback route.
- The adapter now enters video-playback after video creation. A distinct placeholder screen shows the result and an explicit action advances to post-video activities; back navigation returns to video status.
- Source inspection covered the ParentWorkflowPort screen/stage/command types, adapter routes and stage guards, and the Parent screen states. The playback still contains no real media.
- Tests, builds, and device QA were not run under the existing approval exclusions. Git status and diff checks remain unavailable because Git reports “this operation must be run in a work tree” in the designated worktree.

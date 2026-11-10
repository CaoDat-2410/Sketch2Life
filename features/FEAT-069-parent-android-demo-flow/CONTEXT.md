# FEAT-069 — Parent Android demo flow

- Status: IMPLEMENTED_SOURCE_REVIEWED
- Owner: Project owner
- Scope: `apps/mobile` only, in `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; draft pending formal owner sign-off.
- Related review: FEAT-066 `SRS-UI-01` confirms `apps/mobile/src/app/AppRoot.tsx` still mounts only `FixtureFlowScreen`.

## Goal

Provide a navigable Parent Android UI demo covering the SRS Parent journey while keeping all synthetic/demo data behind an adapter boundary so the adapter can later be replaced by approved API and native-media adapters without rewriting screens.

## Scope

- Parent demo entry, sign-in/recovery and a registration UI route requested earlier by the owner; registration remains demo-only and does not create a real account.
- Child profile selection/create, home/history/quota, one-child run, drawing and idea input, optional guide, transcript/subject/context review, story review/rewrite, video status/playback, post-video activities, complete/cancel/delete.
- Responsive phone and tablet layouts, Vietnamese labels, accessible actions and recoverable demo states.
- A `ParentWorkflowPort` plus demo implementation and one centralized fixture-data module. `AppRoot` selects the demo adapter; a separate route retains the existing fixture lab.

## Non-goals

- Backend/API implementation or live API wiring; Firebase adapter/configuration; provider calls; real account provisioning.
- Native camera, gallery, microphone, resumable network upload, notifications, or real video playback. Their UI boundaries and demo states are represented behind replaceable ports.
- Changes to `apps/parent-ui`, `apps/ui-mobile`, Teacher, Manager, Admin, backend, SRS, or open-owner decisions.
- Commit, push, deployment, new packages, or generated visual assets.

## Constraints and open questions

- Activities appear only after video. Parent no-preset activity-catalog behavior remains OPEN under SRS §31.10.
- Registration is included as an owner-requested demo UI affordance, not an SRS-derived account-creation policy.
- `apps/ui-mobile` is reference-only under FR-P-01; do not copy its activity-first flow.
- Demo screens must label synthetic data and must not claim that API, AI, capture, upload, or video operations are live.

## Follow-up — 2026-11-10

- Owner-reported issue: selecting “Tạo video demo” left the Parent flow on the video-status UI, with no distinct result screen.
- Corrected within approved plan revision 1: video creation now enters a separate video-playback stage, with an explicit next action to open the post-video activity.
- Generation and playback remain demo-only behind the existing workflow boundary; no product scope or SRS decision changed.

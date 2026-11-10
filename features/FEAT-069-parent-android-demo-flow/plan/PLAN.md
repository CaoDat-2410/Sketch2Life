# FEAT-069 — Parent Android demo flow

- Status: APPROVED
- Plan revision: 1
- Implementation status: IN_PROGRESS

## Goal

Build the complete Parent Android UI journey in `apps/mobile` as a local demo. Keep synthetic state and fixture records in one adapter/data boundary so a future approved API adapter can replace them without changing screen components.

## Scope and file boundaries

- Target app: `apps/mobile/src/app`, `apps/mobile/src/features/parent-flow`, `apps/mobile/src/infrastructure/demo`, and existing `apps/mobile/src/features/fixture` only where needed to centralize its fixture records or expose the lab route.
- New app flow: login/registration/recovery UI, profile selection/create, dashboard/history/quota, single-child run, capture/idea, optional guide, transcript/subject/context review, story/rewrite, video status/playback, post-video activities, and run lifecycle actions.
- Keep `FixtureFlowScreen` available as a separate fixture lab. The app's normal demo entry opens the Parent flow.
- Keep all mock child/profile/run/story/activity/video values in demo infrastructure; screens call a typed `ParentWorkflowPort` and do not import fixture records.
- Represent camera/gallery/audio/video provider behaviors with demo ports and honest demo states. Do not add packages or claim live device/backend behavior.

## SRS mapping

- FR-P-01: Parent Android composition root and `apps/ui-mobile` reference boundary.
- FR-P-02–04: child profile, single drawing, text/audio idea, transcript confirmation and subject revision.
- FR-P-05–09: post-video activity, minimal context, three story rewrites, script approval, video status and up to two quality regenerations.
- FR-P-10–11: recoverable Vietnamese stages/errors and optional private temporary guide behavior.
- §21.5–21.6 and AC-20: required screens, stage recovery, permission fallbacks and accessibility.
- FR-C-11/12: show demo lifecycle/reminder and resumable-upload states through adapter contracts only; do not claim server persistence.

## Steps

1. Define screen/state and command/query types for the Parent workflow; isolate all demo records in infrastructure.
2. Implement a demo adapter behind `ParentWorkflowPort`, including explicit loading, empty, recoverable-error and terminal states.
3. Build the Parent navigation and screens, keeping Adult confirmation gates explicit and using only adapter data.
4. Compose the Parent demo as the default app route and expose the existing fixture lab as a distinct route.
5. Update feature context, decisions, evidence index and status. Do not modify unrelated worktree changes.

## Acceptance criteria

- AC1: Normal app entry opens the Parent Android demo; the former fixture remains reachable in a separate fixture-lab route.
- AC2: Demo fixture values and state transitions are centralized behind the typed adapter; screen components contain no hard-coded child, run, story, activity, quota or video records.
- AC3: The UI can navigate through profile → drawing/idea → transcript → subject → context → story → video → post-video activity → complete, and can inspect history/quota and cancel/delete a run.
- AC4: Transcript, subject, context and script gates require explicit adult actions. Subject edits create a new local demo revision. Activity selection is never a pre-video gate.
- AC5: Demo enforces at most three story rewrites and two quality regenerations. A rejected video is hidden from playback after a replacement request is accepted.
- AC6: Registration, recovery, camera, gallery, audio, upload, guide, quota and video actions are marked or messaged as demo-only; no live API/provider/device operation is implied.
- AC7: Layout adapts to phone and tablet widths/orientations without horizontal overflow; labels and touch actions remain accessible.
- AC8: No changes occur outside the approved `apps/mobile` paths and this FEAT-069 record; preserve all pre-existing FEAT-036/067/068 working-tree changes.

## Risks and mitigations

- Backend and mobile API contracts are not connected. Use a stable application port and deterministic demo adapter; do not encode server schema in screen components.
- Registration and no-preset activity behavior are unresolved product questions. Keep registration UI demo-only and avoid inventing catalog policy.
- Native capture/audio dependencies are absent in the mobile package. Show honest demo selection/recording states through replaceable ports; do not add dependencies in this scope.
- Large single-screen state can become hard to replace. Split contract, adapter/data, navigation and screen rendering into feature-owned files.

## Verification/evidence plan

- No automated tests/builds are authorized in this task. Record a source-level implementation summary and limitations in `evidence/`; report that behavior remains demo-only until adapter replacement.

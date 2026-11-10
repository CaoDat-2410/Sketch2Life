# FEAT-069 decisions

## D-069-01 — Keep demo data behind a replaceable workflow port

Parent screens use `ParentWorkflowPort`; deterministic records and demo behavior live in `apps/mobile/src/infrastructure/demo`. Replacing the demo implementation with an approved API implementation should not require screen rewrites.

## D-069-02 — Preserve the existing fixture lab

Keep `FixtureFlowScreen` and its synthetic flow available on a separate route. It is not the default Parent experience and is not deleted as part of this task.

## D-069-03 — Demo actions are not live integrations

Registration, password recovery, camera/gallery selection, audio capture, upload, guide, quota and video are represented as demo states. No Firebase/API/provider/native media side effect is introduced.

## D-069-04 — Parent Android only

The implementation target is `apps/mobile`. Existing `apps/parent-ui` tablet and navbar work is preserved and out of scope; `apps/ui-mobile` remains reference-only.

## D-069-05 — Preserve open SRS decisions

Do not implement a pre-video activity choice. Keep no-preset activity catalog behavior and account-creation policy open beyond the owner's bounded demo-UI request.

## D-069-06 — Keep screen content behind the workflow snapshot

Demo profiles, run/story values, context, guide steps, activity, reminder and quota live in the demo infrastructure. ParentWorkflowSnapshot exposes the screen-ready content so UI screens do not import demo fixtures. The old fixture lab keeps its contracts in a separate fixture-data module.

## D-069-07 — Give video results a distinct demo screen

After REQUEST_VIDEO is accepted, the run enters a separate video-playback screen and stage. The playback remains a placeholder. CONTINUE_AFTER_VIDEO advances to the post-video activity only for a ready and visible video on an active run. PLAY_VIDEO can reopen the playback screen from video-status. This clarifies the approved video status/playback journey without adding a live video integration.

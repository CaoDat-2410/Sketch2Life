# FEAT-081 Parent UI Alignment Review — Owner-Supplied SRS Rev67

Date: 2026-11-15  
Review input: owner-supplied `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 634,291 bytes, SHA-256 `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`.  
Approval: Addendum 32; plan: `plan/PLAN_REVISION_17.md` (5,277 bytes, SHA-256 `1E166E3D6DE16F5D784626C03715E59F1C4B0281150755EF91F5446632B523D2`).

This is a source review against the SRS file selected by the owner for this task. It does not update the repository-wide SRS authority register, assert formal SRS sign-off, or certify visual parity on an emulator.

## SRS requirements reviewed

- §5.1 steps 1 and 9–14 (lines 298–313): effective parent consent; one main activity must be selected before story; generate and confirm the story only after that selection; provide video playback and lifecycle actions; show the selected activity and, when pinned, activities from the exact lesson version after video.
- FR-P-02, FR-P-05, FR-P-08, and FR-P-13 (lines 510–521): topic and lesson are optional, activity selection is required before story, and video/post-video behavior is part of the Parent flow.

## FE changes made

- `workflowTypes.ts`: the learning gate now permits only supported-age profiles with server-confirmed consent and a non-empty policy revision. Unknown, pending, unavailable, and revoked consent fail closed.
- `ActivityScreen.tsx` and `ParentExpoApp.tsx`: removed the direct “continue to story” bypass. The screen identifies main activity selection as required and unavailable; exact-pinned activities remain read-only. No selection, API call, or payload was invented.
- `StoryScreen.tsx`, `ParentExpoApp.tsx`, and `ParentVisualPreviewHarness.tsx`: added an explicit `mainActivityConfirmed` presentation input. The app and offline preview pass `false` because the current application has no confirmed activity-selection state. Generation, retry, rewrite input/action, and story confirmation remain disabled until that state can be supplied. If a previously confirmed story is displayed while activity selection is unverified, the UI reports that uncertainty instead of showing an unqualified success notice.
- Existing expectations in `parentFlowV1.test.ts` and `parentSrsBehavior.test.ts` were updated. No test cases were added; tests were not run.

## Remaining mismatches and limits

- Consent is represented by a fixed unavailable adapter (`route-not-in-be-handoff`), so Parent learning is now blocked until an effective consent response can be confirmed by a service.
- Activity selection is unavailable. The Activity screen therefore cannot advance to Story, and Story actions cannot be enabled. The current `ParentStoryRunV1` has no confirmed main-activity field. Selection API/contract and recovery behavior remain unverified.
- Rev67 makes topic and lesson optional. The current FE `canBeginContextStep` requires an exact lesson pin (`parentFlowV1.ts`), and the controller rejects a missing pin (`useParentController.ts`). This no-preset path was not changed under Addendum 32; backend acceptance of the optional lesson request remains unverified.
- Voice-to-text is explicitly unavailable in `TopicScreen.tsx` and `TranscriptReviewScreen.tsx`.
- Video generation/playback, post-video activity display, and run completion/cancellation/deletion/history depend on unavailable platform capabilities. The current UI does not satisfy those Rev67 requirements; no successful playback or lifecycle behavior is claimed.
- No emulator screenshot was reviewed in this task, so visual alignment remains unverified.

## Static review and execution boundary

Read-only review confirmed that no production `onSkip` route remains from Activity to Story, the story controls include the activity gate, the preview is inert and supplies the same false state, and the changed consent assertions now expect fail-closed behavior. This was source inspection only.

Not run: tests, typecheck, validators, diff-check, install, network, backend, Android build, emulator, or Modal. No files were staged, committed, or pushed.

## Final pins for changed FE source and existing assertions

| File | Bytes | SHA-256 |
|---|---:|---|
| `apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts` | 7,763 | `D5CEA3287C5BB0669B77A6B963FFD461475030760BC5BF18F7F767BA0D9EE069` |
| `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx` | 4,663 | `4E06D88311F50A7C483E6EEB657E591916C7A7042883545C577CB1A415ACC8A4` |
| `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx` | 8,106 | `7BDA28C78F2A5545805FF5F1B864CA8B342B0CE99F8BB600286BD754434BC5D5` |
| `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` | 18,172 | `B150747630FB0571533B582F24B80715B29051CCE24BDE67CB81AFC72D5D5117` |
| `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx` | 25,563 | `6C6C7DC71676DEC74E45FE2AB1D8E186E50979C4DFEC64B63279CA0CAB368B10` |
| `apps/ui-mobile/tests/parentFlowV1.test.ts` | 24,461 | `6E99C2421BB833D76C2AB3D3E3F288D110F9DD554549F2F7830B534F1C6E6164` |
| `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 59,558 | `2A7F24E47A66074C3850A77EA4CBE4161B7135EB0A231C6A4693D91CABCFDCEC` |

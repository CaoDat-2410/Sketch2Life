# FEAT-081 Wave 3: Native pre-video Parent flow — Plan Revision 4

Status: DRAFT for owner review. Not approved and not launched.
Date: 2026-11-13.
Target: apps/ui-mobile on feature/fe-mobile-remediation.
Owner: Person 2.
Source draft: tmp/fe081-wave3/WAVE3_NATIVE_PREVIDEO_PLAN_DRAFT_20261113.md.
Decision draft: tmp/fe081-wave3/D011_DRAFT.md.

This revision drafts a flow/data-only port of P03-P06 using the owner decisions in D011_DRAFT.md. It removes components/ui.tsx from editable paths and freezes it as H. No implementation, test run, runtime call, or approval is authorized by this draft. The canonical FE-063 v2.7-draft SRS remains unsigned.

## Goal and boundary

Port the native Parent flow through P06 while preserving the V1 profile, StoryRun, context, adult-review, and lesson-version pins. Implement flow and data behavior only; do no visual polish or sample-asset copying.

Wave 3 is limited to P03 DrawingGuide, P04 Capture and Understanding, P05 Topic/Context using the typed adult idea only, and P06 Story. The existing audio capture UI is untouched; audio transcription, transcript confirmation, and TranscriptReviewScreen are out of scope. It does not include P07, video, job status, playback, post-video activity, session feedback, account recovery, or registration. The pre-video activity chooser remains excluded; use the existing Activity skip path.

## Owner decisions incorporated

The owner decisions are copied in D011_DRAFT.md for Person 2 to record in DECISIONS.md. This plan follows the required order: topic and typed adult idea; optional P03 guide; V1 create and context confirmation; capture only after context confirmation. The typed adult idea is the only Wave 3 input path. Leave the existing audio capture UI untouched and do not connect it to run creation or transcription. Guide steps come only from explicit separators in the selected lesson version's drawing_steps_text; never infer boundaries. Missing guide content is an optional empty state with continue-to-capture. The whole-topic guide illustration stays separate. No visual restyling is in scope.

OWNER_MODAL_CALL_APPROVED=NO for all of Wave 3. Code and fake-data tests only. Stop before drawing-understandings and story-revisions calls. P04-P06 real-AI runtime acceptance is deferred until the AI fix and a bounded Modal approval. Stop before P07/video and do not start video admission.

## Proposed flow

1. Select the Parent profile and pinned lesson version; enter the topic and required typed adult idea.
2. Open optional P03. Parse only explicit step separators from that pinned lesson's drawing_steps_text. Show the approved empty state and allow continue-to-capture if guide data is missing or ambiguous; do not invent steps. Keep the whole-topic illustration out of this wave.
3. Create the V1 StoryRun and present the returned context. Require explicit adult context confirmation.
4. After context confirmation, continue to P04 capture. Do not create a replacement run from CaptureScreen. Handle an existing run only through a known supported state; the INPUT_PROCESSING job/stage question is listed below and must not be guessed. Leave the existing audio capture UI untouched and do not submit audio for this flow.
5. Require an adult to review/correct the returned drawing subject before subject confirmation. Use only returned candidate data; never import sample candidates or fabricate confidence. Do not make a transcript-confirmation step part of Wave 3.
6. Use the existing Activity skip. Generate/rewrite story only through fake-data tests in this wave; cap rewrites at three. Confirm only the exact displayed revision/hash if the V1 response supplies both. Stop at P06, before P07 or video admission.

## Per-screen scope and acceptance

### P03 — DrawingGuideScreen

Add a native screen backed only by the selected pinned lesson's drawing_steps_text. Normalize explicit separators deterministically, preserve order/wording, and return an explicit missing/ambiguous result. Never infer boundaries from prose, titles, or images. Keep the guide optional; the empty state can continue to capture. Do not move or call the whole-topic sketch.

### P04 — CaptureScreen and UnderstandingScreen

Reuse the existing camera/gallery picker and image validation. Capture is reachable only after V1 context confirmation. Show the selected drawing and safe localized states. Subject review uses only the returned candidate and requires an adult action; no candidate or unknown result is fabricated or silently confirmed. No live AI operation is run in this wave.

### P05 — TopicScreen and ContextScreen

Keep topic, required typed adult idea, and pinned lesson selection. Do not edit the existing audio capture UI or route recorded audio into Wave 3 run creation. Do not call audio-transcriptions or transcript-confirmations and do not edit TranscriptReviewScreen. Follow the owner order: topic/idea and P03 precede V1 run creation and context confirmation; capture follows confirmation. Context confirmation remains separate from Continue.

### P06 — StoryScreen

Use fake-data tests for loading, draft, rewrite-limit, and confirmation states. Permit at most three rewrites. Confirmation is allowed only when the current displayed story has the exact V1 revision and hash. If either is absent, stop and request an additive contract allowlist; do not guess or edit a shared contract. The screen ends at confirmed script and must not route to P07 or video admission.

## Offline acceptance criteria

- W3-AC1 — Guide data: deterministic parsing accepts only explicit separators in the pinned lesson's drawing_steps_text, preserves order and wording, and reports missing/ambiguous data without invented steps.
- W3-AC2 — Guide navigation: previous/next/current-index behavior clamps to valid bounds; skip/continue does not mutate the lesson pin or StoryRun.
- W3-AC3 — Flow gates: require profile, pinned lesson version/hash, topic, typed adult idea, and explicit context confirmation before capture; photo is not a prerequisite for creating the V1 context.
- W3-AC4 — Drawing and subject review: drawing analysis requires a selected photo and confirmed V1 context; subject confirmation requires a returned candidate/revision and an explicit adult action. Unknown outcomes do not trigger automatic retries or duplicate commands.
- W3-AC5 — Story safety: rewrites are limited to three and disabled after confirmation; confirmation requires exact current revision/hash; missing fields block confirmation.
- W3-AC6 — Excluded work: no activity chooser or activity-suggestions operation; retain the Activity skip; no guide illustration, P07, video, or live Modal/provider call.
- W3-AC7 — Compatibility: the existing Wave 2 behavior and offline tests remain intact; H pins remain byte-identical; the approved offline test and typecheck runs pass. Tests use synthetic inputs and fake ports only.

These criteria do not prove device layout, live route availability, endpoint response shapes, or real-AI behavior. Runtime/Android acceptance is owner-run. Real-AI acceptance for P04-P06 is deferred until the AI fix lands and the owner grants bounded Modal approval.

## Exact proposed allowlist

E means editable existing path. N means a new path. R means read-only reference. H means hash-only and must remain byte-identical. Every path below is explicit; there are no wildcard entries. E/H pins are copied from the source draft snapshot and must be rechecked before owner approval.

### E — editable existing paths

| Mode | Exact path | Snapshot bytes | Snapshot SHA-256 |
|---|---|---:|---|
| E | apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts | 759 | F153CBC4D96F8396016B83BFC8CA591240F8035DC5F396874365172CCE3F8354 |
| E | apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts | 31,132 | F3F0A76ABBEF26C901554129D947B04C51BAE3EF2C486EC3497E26928901CDE9 |
| E | apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts | 6,010 | 7D6BB96BCFC7FB47706A8A10B4DED73FD8D3BE313B0E3AD61253DEDC855012DB |
| E | apps/ui-mobile/tests/parentFlowV1.test.ts | 5,902 | 9BB4835948ECDF8A6C6BFCD637E902410AB64D2656A07CB78BC2EE19FCB8DF26 |
| E | apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 16,092 | 9A3CF7D23371323B33CB7ABAC806A354973C0CEDC4ED9567F16160168E046D77 |
| E | apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx | 4,251 | D94A292C6098E78C15C71D167CFEB05BE2EBAE67F318D9B8BDD8ED2AD2CACABD |
| E | apps/ui-mobile/src/parent/presentation/screens/UnderstandingScreen.tsx | 2,097 | 8F21667581CBB1F89C80309E0FCBD0CC71F7A9909AF10B4A18ED38DB03216D8E |
| E | apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx | 6,509 | EA17130D3CB1FF397446820B22AEA8A9E32841DE81820009FF5BD90AD3D7F183 |
| E | apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx | 2,765 | 94B1EE1C22BB4F51256A7BF297F4211279A3578D0D030368BF53481316394C38 |
| E | apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx | 3,779 | 3280B267B56C36BF1F0918B5B60F5EAFAF9378BCAC2EB763B8037A801697C847 |

### N — proposed new paths

| Mode | Exact path | Snapshot |
|---|---|---|
| N | apps/ui-mobile/src/parent/presentation/screens/DrawingGuideScreen.tsx | Absent at draft snapshot |
| N | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE3_20261113.md | Absent; requires explicit owner authorization |

### R — read-only references

| Mode | Exact path |
|---|---|
| R | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx |
| R | .worktrees/ui/apps/parent-ui/src/data/mockParentData.ts |
| R | .worktrees/ui/apps/parent-ui/src/components/Kit.tsx |
| R | .worktrees/ui/apps/parent-ui/src/components/MobileLayout.tsx |
| R | .worktrees/ui/apps/parent-ui/src/styles/tokens.css |
| R | .worktrees/ui/features/FEAT-036-ui-current-direction-alignment/evidence/notes/PARENT_UI_UX_REVIEW_20261109.md |
| R | tmp/ui-port-plan/SAMPLE_INVENTORY.md |
| R | tmp/ui-port-plan/PORT_MAP.md |
| R | apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx |
| R | apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx |
| R | apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx |
| R | apps/ui-mobile/src/parent/presentation/screens/TranscriptReviewScreen.tsx |
| R | apps/ui-mobile/src/parent/presentation/screens/HandoffScreen.tsx |
| R | docs/context/SRS_AUTHORITY.md |
| R | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md |

### H — hash-only paths, frozen byte-identically

| Mode | Exact path | Snapshot bytes | Snapshot SHA-256 |
|---|---|---:|---|
| H | apps/ui-mobile/src/parent/presentation/components/ui.tsx | 11,444 | 722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773 |
| H | apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts | 25,559 | 182EBB83A8A9A284444FAADE68740C5DD50CDD0F387393A4577A2C7AD626F7DE |
| H | apps/ui-mobile/src/parent/application/ports/ParentPorts.ts | 8,472 | 62CDC570BEEE074D1BD4558A5567E37CD2911DC7041D4689F231CC2884182551 |
| H | apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts | 2,164 | 0373643C8C92C9EA6D144C22F27202D8A09163FB03D369A786982E9413CBB9A3 |
| H | apps/ui-mobile/src/parent/application/ParentApplicationError.ts | 1,027 | 3087B87025511877F983BF0A9331E11DF110078F938354C87800E61CFF4BD2AF |
| H | apps/ui-mobile/src/parent/domain/types.ts | 10,152 | 990FA43EF6E04874FD72E9E62AC7CCAD9332F687BFE92A64586A87A7010A0240 |
| H | apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts | 2,994 | C3A88AB853C6EE96882ABF950EAC76032E68D97D6E52D7A42EF63C869E99CCC2 |
| H | apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts | 6,766 | 8812D4AB0DAB6DB7C35CDA9F14EEEB953201AC0157DDE1C4C2216A8FD40C43AE |
| H | apps/ui-mobile/package.json | 2,081 | AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF |
| H | pnpm-lock.yaml | 470,780 | 5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72 |
| H | apps/ui-mobile/tests/apiRetryIdentity.test.mjs | 3,188 | C0DC06450146667AC16C8108960E892F30B4D34AD0A1B0AD3EBB3EC19D5C6054 |
| H | apps/ui-mobile/tests/mainFlowSafety.test.mjs | 7,985 | 41B82F60E83B17DBB09F7195ACF122E3653046A49822D42D5416E39B53582D74 |
| H | apps/ui-mobile/tests/storyDraft.test.ts | 1,770 | 07C8BE23A875F2082CDC2626A23E4462A46CF61525BD487F9053CCD00CBCFC50 |
| H | apps/ui-mobile/tests/catalogViewModel.test.ts | 3,254 | 8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978 |
| H | apps/ui-mobile/tests/parentApiI2Contract.test.ts | 17,370 | C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075 |
| H | apps/ui-mobile/tests/parentLearningI2.test.ts | 5,841 | E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892 |
| H | apps/ui-mobile/scripts/validate-ui-copy.mjs | 21,206 | 5AD006820035DF1B4DF1489338CBC08A06B877B80B2B345C1A82806D729A0391 |

The shared components/ui.tsx entry is H, not E: it is frozen byte-identically and must not be edited. No wildcard or unlisted path is authorized. New report-path creation also requires explicit approval.

## Explicit non-scope

Wave 3 must not modify backend code, database/schema/migrations, approvals, DECISIONS.md, shared API/transport/domain contracts, package manifests or lockfiles, or visual assets. The E entry for workflowTypes.ts is limited to the native navigation step type; it does not authorize changes to shared API contracts. The H paths, including components/ui.tsx, must remain byte-identical. No visual polish, generated guide art, or whole-topic sketch work is included.

## BE questions this plan depends on

1. INPUT_PROCESSING after context confirmation — NON-BLOCKING for this Wave 3 code-only launch because active-run resume is outside P03-P06 and remains a separate follow-up. Before any resume/runtime acceptance, BE must state whether a job is active and provide the supported status/stage or reconciliation operation; mobile must not guess.
2. Verified cancellation route — NON-BLOCKING for Wave 3 because Home cancel/abandon is outside this allowlist and remains a separate FE/BE task. The History route /api/parent/v1/story-runs/{id}/cancel is unverified; BE must provide the exact route, method, contract, authorization, and idempotency before that task. Do not infer a replacement.
3. Audio transcription and transcript-confirmation — NON-BLOCKING for this code-only wave because D-011 decision 10 removes the P05 audio subpath from scope. Coordinator code reading of integration/dev-on-s1ap at 9dfdd2d7 found no audio-transcription or transcript-confirmation route under the Parent profile, V1 StoryRun, or Parent AI routers (profiles; /v1/story-runs/*; /api/parent/v1/ai/{sketch-guides,drawing-understandings,story-revisions}). The mobile ParentApi still calls /api/parent/v1/story-runs/{id}/audio-transcriptions. Record that mismatch as a BE follow-up; it does not block the typed-idea-only Wave 3. This is code reading, not a runtime result.
4. V1 script confirmation — ANSWERED by coordinator code reading, not runtime-verified; NON-BLOCKING for this code-only wave. In integration/dev-on-s1ap at 9dfdd2d7, backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1181-1288, POST /v1/story-runs/{run_id}/script-confirmation records adult CONFIRM, sets story revision status CONFIRMED, leaves run_state SCRIPT_REVIEW, sets job_state SUCCEEDED, and does not start video admission. The request requires expected_revision (1–4), story_sha256 (64 lowercase hex), and Idempotency-Key; stale revision returns 409 PARENT_STORY_REVISION_STALE. The response carries story_revision_no, story_sha256, story_revision_id, story_status, and story. The mobile route/body/header check is recorded here: ParentApi.ts calls POST /v1/story-runs/{run_id}/script-confirmation with expected_revision and story_sha256 and an Idempotency-Key header; no mismatch was found by source reading. None of this proves runtime behavior.

## Stop conditions

- No Modal or other live AI/provider calls. Stop before drawing-understandings and story-revisions; no code or acceptance run may make those calls.
- No network requests, service/database access, or dependency installation. Offline tests use synthetic fixtures and fake ports only. If a command would install or use network access, stop.
- No video, video admission, P07 navigation, or post-video work.
- Q1 and Q2 remain NON-BLOCKING; Q3 is NON-BLOCKING because the audio subpath is excluded; Q4 is answered by code reading only. Do not treat code reading as runtime verification. Do not launch until D-011, the plan, and exact allowlist have been owner-approved; stop if a new blocking BE contract issue is found.
- If V1 story response lacks the exact revision/hash required for the displayed script, stop and request an additive allowlist. Never invent fields or edit shared contracts.
- If guide separators are ambiguous, report the guide as missing/ambiguous; never infer step boundaries.

## Command ceilings and who runs them

These proposed Wave 3 budgets are separate from Wave 2 accounting. Codex runs none of these commands. Every invocation must remain offline and use synthetic/fake data.

| Command | Ceiling | Runner and use |
|---|---:|---|
| pnpm run test from apps/ui-mobile | 2 | Coordinator: one baseline before edits and one post-implementation run. |
| pnpm run typecheck from apps/ui-mobile | 2 | Coordinator: one baseline before edits and one post-implementation run. |
| python tools/validate_harness.py from repository root | 2 | Owner: one baseline and one final run. |
| python tools/validate_repository_security.py from repository root | 2 | Owner: one baseline and one final run. |
| python tools/validate_architecture.py from repository root | 2 | Owner: one baseline and one final run. |
| git diff --check from repository root | 2 | Owner: one baseline and one final run. |

The package test script runs Vitest with fake/synthetic data and the existing UI-copy validator. Runtime and Android acceptance are owner/coordinator-run. P04-P06 real-AI runtime acceptance is deferred until the AI fix lands and bounded Modal approval is recorded. No test, typecheck, validator, Android, network, install, or provider command is run by Codex under this plan.

## Evidence

The single proposed implementation evidence path is features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE3_20261113.md. It needs explicit owner authorization in the Wave 3 approval entry. Store offline test and typecheck results there; owner-run Android/runtime evidence belongs there when separately authorized. Do not create another evidence path under this draft.

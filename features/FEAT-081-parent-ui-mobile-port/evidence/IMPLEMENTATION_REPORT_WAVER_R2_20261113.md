# FEAT-081 Wave R2 implementation report

## Status

READY for coordinator post-run review under owner Addendum 1. R2 is complete without no-preset; an exact lesson version pin remains required. R3 and R4 had not started when this R2 report update was recorded.

## Pre-flight

- Worktree: .worktrees/mobile; branch feature/fe-mobile-remediation; HEAD f193d4abcf45e8b8e62a5c7d2d29d6978f4a342d.
- Approved plan: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes, SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- The 92-row E/H/R/N manifest was checked before R2. Hash cells were 64 hexadecimal characters, E rows matched their post-R1 pins, all 17 H rows matched, and R differences were limited to the append-only Task A record pins. The BE handoff note and no-Modal log pins were checked in the main checkout. R2 report path was absent at entry.
- All R2 files matched their post-R1 or R0 pre-pins recorded below. No route, plan, or worktree mismatch was found.
- No network, backend, provider, Modal, install, test, typecheck, validator, diff-check, emulator, Android, Gradle, or ADB operation was run.

## Initial stop evidence (superseded by owner Addendum 1)

Plan Revision 7 §3 says to stop if no-preset is blocked. The current helper at apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts:73-85 requires a profile, non-empty topic, non-empty adult idea, and a lesson pin containing lesson ID, version ID, and content hash. apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx:267-294 passes that result as TopicScreen.canContinue, and apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx:119 disables Continue when it is false. The controller repeats the same requirement at apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts:626-638. Clearing a lesson therefore cannot advance to the drawing-guide step. The router at ParentExpoApp.tsx:305 renders DrawingGuideScreen only when a lesson exists.

There is a second upstream gate: useParentController.ts:59 creates consent state as unavailable because the consent route is absent from the owner-authorized backend handoff; useParentController.ts:402-417 blocks profile learning without server-confirmed consent. This follows the D-015 boundary and must not be bypassed with a local success state.

The required navigation/gate resolution is outside the R2 allowlist: ParentExpoApp.tsx and parentFlowV1.ts are not R2 E paths. No R2 change was made to either file. Proceeding would widen the allowlist or claim the blocked behavior works, so work stopped before R3.

## Paths and pins

| Path | Before bytes | Before SHA-256 | After bytes | After SHA-256 |
| --- | ---: | --- | ---: | --- |
| apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx | 4,838 | A4A29FCA5B3EF090A22779214939A0DE6165F96276C9AEA58E0C2E6CD4632B9F | 5,012 | 05AB783965739E3520B6E30B38EBEF7AC457218DE8BD2032789C8AB8A46D7D46 |
| apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx | 9,876 | 35D75628DF9220FABA787010E5E40A895FA99AE3A3A34F325E7B752DDFB04003 | 11,581 | 96BED38BA596A182046716DFC1C3DB1C69024F3C07B24E13637778A5A09555DE |
| apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx | 1,595 | C43EC59DBA63C00E9C9489072BF014060AF33AE3C93198F29D8BAD78903782B0 | 1,676 | 61CE950D1129C45FA12910286EC8A7E4A4F26CC939EBBF91761D8FE757EB87C8 |
| apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx | 6,667 | 8A87F7C3769CD57DF9F97E21D85163FF448409B586E1C6CFADB9C16937B157D5 | 6,955 | E91EA21498CFC2C71AABBCDF9ECE01CE36CFBB258335FD6B71F221A649352815 |
| apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts | 36,772 | 52DC10A52C528ED527FDE762E8A89687BCE4F90965B083FC4ECC9BC1F916CA6C | 42,571 | 4A6931C4D39ADE035D97DEC11F3B4245E453B5F5F79926E833F4D396ABD4B6F0 |
| apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts | 5,716 | 63B4F280FB86FC24E07B047A38F25E61CB4C65242C000BAE0AC12357626CDF12 | 7,586 | 2DBEAB524E0C9286919837E1182D0C8538B4B2C783A6900CA93C2EA3C2A8C497 |
| apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts | 25,559 | 182EBB83A8A9A284444FAADE68740C5DD50CDD0F387393A4577A2C7AD626F7DE | 22,638 | 43212F92BB83371D2ED0ED6EC65426C81BDEA9B0DD5BD0AA51A8B2E9110EAB02 |
| apps/ui-mobile/tests/parentSrsBehavior.test.ts | 11,529 | C2D19DA754EA6B4442A0EB7CE062916505950E859C69CB3409DA2C98597000CA | 18,045 | B9D1E6198BB80D91510F72C76E57AC69F4528F633188C201611CC85135D927E0 |
| apps/ui-mobile/tests/parentFlowV1.test.ts | 16,654 | 51C92A5F0E7CA0D259FE8ACDA74A50199A81D15BA183D9F3A1FBF8C31B79E5A8 | 19,211 | D1F77D7A01CAB4F9635D5768050B3E6DF798C89020050F3563FA942352A87E17 |
| apps/ui-mobile/src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter.ts | 773 | 2E525046ED9F9A48A2491434EE68F6151A237A9E8C288009CB2A56AF94782DE6 | 838 | 59334ABC207EB27FCE48CE1FA95FC73A3A6C75005C55ABAF668DC4E6E964BF40 |
| features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R2_20261113.md | absent | absent | Recorded immediately in run state after writing | Recorded immediately in run state after writing |

The report cannot include its own content hash. Its final size and full hash are recorded in tmp/fe081-waveR2/run_state/RUN_STATE.md and the coordinator handoff.

## Initial source acceptance status (updated below by owner Addendum 1)

| Acceptance | Status | Source evidence and limitation |
| --- | --- | --- |
| WR-AC9 | NOT RUN | workflowTypes.ts validates exact authorized lesson/version/hash and expiry; LessonPickerScreen and TopicScreen show the version pin. The all-required-field gate prevents optional/no-preset progression. |
| WR-AC10 | IMPLEMENTED_BY_SOURCE | useParentController.ts:587-610 requires the active-run preflight, photo, and API availability; this R2 controller does not call StoryRun creation. Static tests assert no legacy createRunBeforeDrawingV1 or application.learning.suggestActivities call. No runtime test was run. |
| WR-AC11 | NOT RUN | The picker exposes a clear/no-lesson action, but the following gate and router block continuation without a lesson. |
| WR-AC12 | IMPLEMENTED_BY_SOURCE | useParentController.ts:174-213 checks the server active-run endpoint before profile continuation; the run-start gate blocks unavailable preflight and existing active runs. No runtime test was run. |
| WR-AC28 | NOT RUN | Catalog filtering and exact version/hash checks are present. Revocation/runtime authorization and private-copy lineage cannot be established by these local checks; no personal-copy route or lineage contract is in the owner route table. |
| WR-AC35 | NOT RUN | Invitation states are rendered from server lists and actions refresh the lists before any accepted/declined label can be shown. No backend runtime was exercised; group-invitation decline is not in the owner route table. |

## Initial copy changes (updated below by owner Addendum 1)

SRS reasons are optional topic/lesson setup and exact-version review under FR-P-02/06/13, FR-PL-03/04/05/06/13/23 and BR-08/09/49-51/58; safe permission recovery under §21.6; and showing only server-confirmed invitation state under FR-PL-06/23 and BR-58.

| Location | Before | After |
| --- | --- | --- |
| TopicScreen subtitle | Nhập chủ đề và gợi ý của người lớn trước khi xem hướng dẫn từng bước. | Chủ đề, ý tưởng và bài giảng đều là tùy chọn. Bạn có thể để trống để tiếp tục theo bức vẽ của con. |
| TopicScreen fields | Chủ đề; Ý tưởng của người lớn | Chủ đề (không bắt buộc); Ý tưởng của người lớn (không bắt buộc) |
| TopicScreen no-lesson state | Hãy chọn một bài học cho buổi học này. | Không chọn bài giảng cũng được. Bạn có thể tiếp tục mà không ghim bài giảng mẫu. |
| LessonPickerScreen action | Tiếp tục không dùng giáo án | Tiếp tục không dùng bài giảng |
| TopicScreen microphone failures | Used the native cause.message when available, otherwise “Không thể bắt đầu ghi âm.” or “Không thể hoàn tất bản ghi.” | Chưa thể dùng micro. Bạn vẫn có thể nhập ý tưởng bằng văn bản. / Chưa thể lưu bản ghi âm. Hãy thử lại hoặc nhập ý tưởng bằng văn bản. |
| LessonGalleryScreen invitation state | Displayed expiry text or a raw membership ID; only pending items were visible. | Lesson states: “Đang chờ phản hồi”, “Đã được chấp nhận”, “Đã từ chối”, “Đã thu hồi”, “Đã hết hạn”, or “Chưa xác định trạng thái”. Group states: “Đang chờ bạn chấp nhận”, “Đã tham gia”, “Đã thu hồi”, or “Đã hết hạn”. Displays “Trạng thái từ máy chủ: …”, hides membership IDs and expiry timestamps, and gates response buttons to actionable states. |
| Lesson/lesson-picker version detail | Displayed topic/activity count without exact version ID/hash. | Displays version ID in list rows and version ID plus SHA-256 for opened lesson detail. |
| Unavailable activity and identity errors | No typed unavailable activity message; capability-unavailable errors had no dedicated safe label. | “Chưa có tuyến dịch vụ được xác nhận để tải hoạt động. Chưa có yêu cầu nào được gửi.” and “Tính năng này chưa có tuyến dịch vụ được xác nhận.” |
| Invitation refresh failures | No post-action server reconciliation message. | “Chưa thể xác nhận trạng thái lời mời từ máy chủ. Hãy kiểm tra lại trước khi thử tiếp.” or “Máy chủ chưa xác nhận thay đổi lời mời. Trạng thái hiện tại vẫn theo máy chủ.” |

The changed optional-copy promise is currently contradicted by the navigation gate documented above. It is not accepted as implemented copy behavior until the blocker is resolved.

## Test changes

R2 added synthetic assertions for exact authorized lesson version/hash/expiry, active-run/photo/API gate states, typed local-unavailable ParentApi operations without fetch/auth, invitation/state rendering, and controller source guards against legacy run creation and activity suggestion. Existing test assertions were not deleted or rewritten in the R2 diff. These assertions were not executed; the coordinator owns the remaining test invocation.

## Owner emulator checklist

NOT RUN. After the gate is resolved, owner review should cover invitation empty/pending/accepted/declined/revoked states and lesson/version/unavailable states on the local emulator, including the 6.1-inch portrait layout. No emulator or Android tooling was run by Codex.

## Read-only command ledger

Ran Get-Content, Select-String, Get-Item, Get-FileHash, rg, Python UTF-8 source inspection, git status, and git diff for static review. Confirmed the active-run and lesson checks, unavailable error handling, and the no-legacy-run/no-suggestion controller source guards. No test or validation command was run.

## Initial stop status and open items (superseded by owner Addendum 1)

- NOT RUN: pnpm run test, pnpm run typecheck, all validators, git diff --check, network/backend/provider/Modal calls, Android/emulator/Gradle/ADB, and owner visual review.
- R2 is NOT READY because Plan Revision 7 §3's no-preset stop condition is met.
- Required owner/coordinator resolution: authorize an amended R2 allowlist for the gate and router paths and confirm the consent contract, or issue a plan revision that changes the blocked acceptance. Do not bypass consent or widen the R2 allowlist without that instruction.
- Personal-copy/source-lineage behavior remains unavailable without an approved route and schema. Parent-group decline remains unavailable because the owner-authorized route table has no decline operation.
- R3 and R4 remain unstarted.

## Owner Addendum 1 resolution and final R2 status

The owner resolved the R2 no-preset stop condition in Addendum 1 and D-016. The backend StoryRun create contract requires an exact lesson ID, version ID, and content hash. Parent no-preset remains unavailable until a backend contract exists; SRS 31.10 no-preset remains OPEN-OWNER. This R2 checkpoint is READY with that branch explicitly unavailable. No route, screen, or allowlist was added outside the approved plan.

WR-AC9 is limited to the supported pinned-lesson path; its no-preset branch is NOT AVAILABLE: backend contract absent. WR-AC11 is NOT AVAILABLE: backend contract absent. The client keeps the exact selected lesson version/hash and does not offer a no-lesson continuation. Personal-copy lineage under WR-AC28 and Parent-group invitation decline under WR-AC35 remain typed unavailable because those routes are absent; Addendum 1 accepts those unavailable states, so they are not checkpoint blockers. No fake success is shown.

### Copy and source-test corrections

| Location | Previous copy | Current copy | Reason |
| --- | --- | --- | --- |
| `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx` subtitle | Topic, idea, and lesson were described as optional. | Topic and idea may be added; a pinned lesson version is required to continue. | D-016; backend run creation requires the exact lesson pin. |
| `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx` empty lesson state | It said the adult could continue without pinning a sample lesson. | It asks the adult to select and pin a lesson version. | No-preset is NOT AVAILABLE under D-016; SRS 31.10 remains open. |
| `apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx` | The empty state and button offered continuing without a lesson. | The empty state explains that a pinned version is required; the no-lesson button is removed. | D-016 and the exact backend lesson-pin contract. |
| `apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx` picker state | The subtitle and button described lesson choice as optional. | The picker asks the adult to pin a lesson version; the no-lesson button is removed. | D-016 and the exact backend lesson-pin contract. |

`apps/ui-mobile/tests/parentSrsBehavior.test.ts` now checks that the picker requires a pinned lesson and that the old no-lesson continuation copy is absent from the picker, gallery, and topic screen. The prior source assertions that required the no-preset button/optional-lesson copy were intentionally changed for D-016; no behavioral test assertion was deleted. The lesson-version/hash and invitation-state source assertions remain.

### Updated paths and pins

| Path | Before bytes | Before SHA-256 | After bytes | After SHA-256 |
| --- | ---: | --- | ---: | --- |
| `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx` | 6,955 | `E91EA21498CFC2C71AABBCDF9ECE01CE36CFBB258335FD6B71F221A649352815` | 6,918 | `3F33560E469CA5DE34AC36E638A863C26637A27864EF8F9B61582F797364B0FA` |
| `apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx` | 1,676 | `61CE950D1129C45FA12910286EC8A7E4A4F26CC939EBBF91761D8FE757EB87C8` | 1,579 | `ADD6C6606C4FE10AF125D6D3FA90B4152B03C6A5B7A24A809A7D7D48A3B4EF41` |
| `apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx` | 11,581 | `96BED38BA596A182046716DFC1C3DB1C69024F3C07B24E13637778A5A09555DE` | 11,467 | `D71F0B14A5826701C7447A7677E59829AF2D1AFA628B9B4E10E2ECE1ED3B1847` |
| `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 18,045 | `B9D1E6198BB80D91510F72C76E57AC69F4528F633188C201611CC85135D927E0` | 18,408 | `B635CEF5289254ED695BDA2C0119C80F27BA8CFFA1ED1E822998CECAF2956451` |

R2 static review confirmed no no-lesson success promise remains in these three screens, the test source guard reflects the owner decision, and exact pinned-lesson selection remains required. The current R2 evidence report has been superseded in place with this resolution; its final size and full SHA-256 are recorded in `tmp/fe081-waveR2/run_state/RUN_STATE.md` after the report update.

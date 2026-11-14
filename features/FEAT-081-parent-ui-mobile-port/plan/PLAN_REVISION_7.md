# FEAT-081 Parent Mobile UI — Plan Revision 7 (DRAFT)

Status: DRAFT ONLY. No implementation or checkpoint is authorized by this draft. Rev60-based Plan Revision 6 and Wave R records were withdrawn before launch. This Rev67 revision needs separate owner plan approval and its own explicit launch instruction for EACH of R0, R1, R2, R3, and R4.

## 1. Authority and goal

Working source for this planning task: owner-supplied, unsigned v2.7-draft Rev67 at tmp/fe081-waveR2/srs_new/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_Rev67_owner_supplied.md (634,291 bytes; SHA-256 B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996). It supersedes the repository Rev60 copy for this planning exercise. docs/context/SRS_AUTHORITY.md still points to Rev60 and the repository copy has not been replaced; this remains an open governance item. In Rev67, §21.7 is the external-provider communication contract; the wireframe/UI contract paragraph is at line 1750 and OI-17 is listed at line 1228. Preserve this source numbering.

Wave V presentation-only alignment was cancelled before code change. D-013, Addendum 11, and Plan Revision 5 remain historical and unchanged. Prior Wave R Plan Revision 6 and associated records were withdrawn and never launched. This draft does not restore or append them.

Goal: rebuild the Parent mobile experience around Rev67 surfaces and flows using the owner’s restrained crayon visual direction. Crayon is an owner design decision outside the SRS. OI-17 sign-off is deferred until the owner reviews R0 emulator screenshots; the visual concept remains unapproved until then. Adult-operated only unless the owner separately changes scope.

Behavior, flow, copy, error recovery, and synthetic-data tests are in scope in each launched checkpoint. Absent backend operations use typed unavailable ports in the normal app; test fakes are permitted only in tests. Never show fake success. No real route wiring for operations absent from the BE handoff. OWNER_MODAL_CALL_APPROVED=NO. No new dependency, system fonts, code-only drawings, existing react-native-svg, expo-linear-gradient, @expo/vector-icons. No copied art.

Owner request, not a Rev67 requirement: add optional child gender to create/edit forms as a local draft with choices boy, girl, and prefer not to say. Do not send it to any model. Until SRS, profile schema, migration, revision hash, and BE contract are approved, exclude it from persistence payloads and identify it as unsaved; do not claim it was saved.

## 2. Required Rev67 flow and gates

1. Select an authorized profile and current consent state. The profile form may show the owner-requested optional gender draft, but its persistence remains explicitly unavailable.
2. Topic and lesson are optional. A selected lesson binds to its currently accessible exact version/hash.
3. Optional guide runs before photo capture. Use approved/licensed SVG catalog first and deterministic vector strokes; guide failure never blocks capture.
4. Capture one drawing photo. It is mandatory before StoryRun creation or VLM. Camera is primary; denied camera still permits gallery.
5. Match subject against the optional topic/lesson and show any mismatch. Offer topic change or one retake only; the retaken image supplies the subject and the lesson pin remains unchanged.
6. If audio is present, show the transcript for adult edit and exact-revision confirmation; mic denial leaves typed idea available. After transcript review (or its omission), the adult confirms/edits the current subject revision before context review.
7. Adult reviews/confirms allowed context snapshot and current revisions.
8. Activity preview follows subject/context confirmation. Catalog-first and access-filtered; exact pinned version if a lesson is selected. AI selects canonical candidate IDs and reasons. Exactly three quality-gated drafts only if no catalog candidate fits and capability gates are approved.
9. Adult chooses exactly one main activity. Unknown/error/unavailable/empty preview cannot bypass the gate. Replacements exclude shown/rejected choices.
10. Story generation/rewrite/review uses the selected activity. Confirm exact story/script revision hash before video admission.
11. Display typed job state/stage, never fabricated percentages. Playback only after technical and safety validation.
12. After playback: pinned lesson shows all activities from exact version with main marked; no lesson pin shows only the run-pinned main, with no catalog query or extra list.
13. Completion, cancel, regeneration, history, delete, quota, and purchase are server-backed only when an approved route exists. Pending/reconciling is not success.

API V2 must settle snapshot/run creation timing. The SRS step order still requires subject/context confirmation before activity preview and selection before script. Do not reuse legacy create-run-before-photo behavior while timing is unresolved.

## 3. Dependency-ordered checkpoints

Checkpoints are sequential. Each needs its own launch instruction. Before each launch, re-pin current E/H/R files and confirm N paths. For a path created in an earlier checkpoint, use the exact after-pin in its evidence as the next pre-pin. Do not widen the allowlist mid-checkpoint. Tests use synthetic profiles, topics, SVG strokes, activities, revisions, jobs and permission states only.

| Checkpoint | Surfaces and SRS IDs | Behavior, copy and state machine | Routes and ports | Exact path allowlist | Tests, acceptance and owner emulator review | Stop conditions | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0 — crayon foundation/primitives | ui.tsx primitives and ParentBottomBar only; GoogleSignInButton only if compatibility requires. NFR-20/29 and §21.5 accessibility. No screen file. | Restyle in place; preserve every export, prop/default, callback, copy string, busy/pressed/disabled/confirmation state, tab ID/order and safe-area behavior. Typed job stage has no percent; busy is not success. | No route changes. Create typed capability/operation states and unavailable adapter, not wired into product flow. | E: apps/ui-mobile/src/parent/presentation/components/ui.tsx; apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx; optional apps/ui-mobile/src/parent/presentation/components/GoogleSignInButton.tsx. N: apps/ui-mobile/src/parent/application/ports/ParentCapabilityPorts.ts; apps/ui-mobile/src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter.ts; apps/ui-mobile/tests/parentSrsBehavior.test.ts; R0 report. | Synthetic contrast test for every foreground/fill pair; text independent of color; no percent field; targets 44 dp minimum/48 preferred; optional prop defaults. WR-AC1–4. Owner checks 6.1-inch portrait, labels, scaling, focus, busy/disabled, safe area and touch; local screenshots. OI-17 remains pending. | Stop if any current screen call needs screen edits, copy or API compatibility changes, contrast fails, new dependency needed, or any unlisted path is needed. | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R0_20261113.md |
| R1 — account/auth/recovery/profile | AuthScreen, AccountScreen, SettingsScreen, ProfileScreen, ProfileFormScreen, ProfileSharingScreen and navigation/controller. FR-C-01/04/05/07/10; FR-P-01/02/06; FR-PL-07/08/25; BR-03/18–21/35/48/57; NFR-02/04/15/16/20/21/34/36/38. | Adult sign-in, re-auth, change/reset password, sign-out/session clear; profile list/create/edit with age bands and legacy read/delete; explicit consent capture/revoke states; named Teacher invite with scoped 90-day audited grant and pending/accepted/declined/revoked/expired states; immediate revoke; profile delete confirmation and DELETE_PENDING. Gender is optional form-only draft (boy/girl/prefer not to say), visibly unsaved and excluded from API/model payloads pending SRS+BE change. Calm Vietnamese recovery copy. | REAL only Firebase Authentication and exact handoff-listed /v1/parent/profiles list/create/PATCH/DELETE operations. Consent, share-grant lifecycle, gender persistence, delete receipt/status/purge are FAKE_PORT. No successful-state claim until exact operation confirms. | E: apps/ui-mobile/src/parent/presentation/screens/AuthScreen.tsx; AccountScreen.tsx; SettingsScreen.tsx; ProfileScreen.tsx; ProfileFormScreen.tsx; ProfileSharingScreen.tsx; ParentExpoApp.tsx; navigation/useParentController.ts; navigation/useParentPlatformController.ts; navigation/workflowTypes.ts; apps/ui-mobile/tests/parentSrsBehavior.test.ts; apps/ui-mobile/tests/parentFlowV1.test.ts. N: R1 report. The R0-created test path uses only its recorded R0 after-pin. | Synthetic auth expiry/one refresh; profile age-band and legacy states; consent capture/revoke; share pending/accepted/declined/90-day/expired/revoked with immediate access block; profile DELETE_PENDING; gender enum/no-model/no-payload/unsaved notice; safe draft retention. WR-AC5–8, 28, 31, 34, 36, 38, 39. Owner checks account/settings and profile/sharing/deletion states, labels/focus/scaling. | Stop if frozen auth/use-case/package paths must change; if gender is represented as saved; if absent consent/share/lifecycle route is treated as success; or if unresolved field scope/consent policy is silently chosen. No new auth provider/schema/migration. | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R1_20261113.md |
| R2 — home, lessons, optional setup, invitations and run-start entry | HomeScreen, LessonGalleryScreen, LessonPickerScreen, TopicScreen and related navigation/application paths. FR-P-02/06/13; FR-PL-03/04/05/06/13/23; BR-08/09/49–51/58; §5.1 steps 1–3; §19 UC-02; §21.5; §31.10 no-preset/A01/A02/S01/S02. | Optional topic/lesson and exact version pin; no-preset; published/currently authorized lesson discovery; only permitted private draft/personal-copy access, with source lineage and no source edit; lesson and Parent-group invitation inbox with pending/accept/decline/active/revoked states; safe unavailable response when an operation is absent. Home provides run-start preflight, but StoryRun creation waits for R3 photo/API V2. | Existing listed profile/run ops only. Lesson catalog/access/copy/invitation/group membership/active-run routes are ABSENT and FAKE_PORT. No accepted invite, copy, access, or run success without server confirmation. | E: apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx; LessonGalleryScreen.tsx; LessonPickerScreen.tsx; TopicScreen.tsx; navigation/useParentController.ts; navigation/workflowTypes.ts; application/use-cases/ParentLessonUseCases.ts; infrastructure/http/ParentApi.ts; domain/types.ts; apps/ui-mobile/tests/parentSrsBehavior.test.ts; apps/ui-mobile/tests/parentFlowV1.test.ts. N: R2 report. Extend only from the post-R1 test pins. | Synthetic optional-topic/lesson, exact pin/hash, stale re-review, published/authorized-only discovery, revoke/unpublish, lesson personal-copy source lineage/no source mutation, lesson/group invitation accept/decline/revoked, no-preset, active-run duplicate and no-StoryRun/VLM-before-photo tests. WR-AC9–12, 28, 35. Owner checks invitation empty/pending/accepted/declined/revoked and lesson/version/unavailable states. | Stop if no-preset is blocked, a copy/invitation is falsely accepted, legacy create-run still precedes photo, access cannot be checked, or new route/schema/screen file is needed. No purchase/preset/history policy choice. | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R2_20261113.md |
| R3 — story-creation flow | DrawingGuideScreen, CaptureScreen, TranscriptReviewScreen, UnderstandingScreen, ContextScreen, ActivityScreen, StoryScreen and flow contracts. FR-P-02–08/11–13; FR-PL-15–19; BR-01/08/13–15/18–21/23/42/44–46/54–57; §5.1; §19 UC-02; §21.5/21.6; §31.17–31.18. | Optional catalog-first guide with 4–8 progressive strokes; mandatory photo; camera/gallery; typed idea or optional audio capped at 2 minutes and 20 MB; reject over-limit input before transcription; transcript review/edit/explicit revision confirmation; subject match/revision and one retake; context review; activity preview; exactly one main choice; story/rewrite/review and exact-hash confirmation. Script requires current confirmations and selected activity. Interrupted upload resumes only when contract exists; unavailable remains explicit. | Photo/session/VLM order, transcription/transcript confirmation, resumable media session, SVG catalog/vector/draft, activity filtering/selection/drafts/replacements, snapshot revisions and activity-bound story absent/incompatible routes are FAKE_PORT. Existing story routes REAL only for listed legacy operations, never as unapproved API V2. Normal app has unavailable states; test fakes only. | E: apps/ui-mobile/src/parent/presentation/screens/DrawingGuideScreen.tsx; CaptureScreen.tsx; TranscriptReviewScreen.tsx; UnderstandingScreen.tsx; ContextScreen.tsx; ActivityScreen.tsx; StoryScreen.tsx; navigation/useParentController.ts; navigation/parentFlowV1.ts; application/use-cases/ParentLearningUseCases.ts; application/use-cases/ParentLessonUseCases.ts; application/ports/ParentPorts.ts; application/ports/ParentApplicationModule.ts; infrastructure/http/ParentApi.ts; domain/storyDraft.ts; domain/types.ts; apps/ui-mobile/tests/parentSrsBehavior.test.ts; apps/ui-mobile/tests/parentFlowV1.test.ts. N: R3 report. Extend tests only using post-R2 pin in launch instruction. | Synthetic audio boundary (2 minutes/20 MB, both caps, just-over-limit rejection/no transcription); typed fallback; transcript edit/hash/confirm; upload interruption/unavailable; 4–8 strokes/nonblocking failure; photo-before-run/VLM; permission alternatives; match/one retake; context revision; catalog-first/exactly-three-gated-drafts/exactly-one/no-bypass/replacement exclusion; no raw media/identity; story gate/rewrite/hash. WR-AC13–20, 33, 43. Owner checks permission/guide/mismatch/transcript/activity/story recovery; synthetic data only. | Stop if API V2/order, audio limits, quality/privacy gate or route is not approved; if over-limit audio reaches transcription; if there is fake transcript success, a second retake, or a story bypass. No live AI/provider calls. | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R3_20261113.md |
| R4 — job/video/post-video/lifecycle/history/quota | ActivityScreen, StoryScreen, HandoffScreen, StoryHistoryScreen, LessonHistoryScreen, QuotaScreen, NotificationsScreen and existing navigation only; implement new typed job/video/completion content within these listed E files and create no new UI file. FR-P-08–10; FR-PL-21/22/24; FR-C-08/11; BR-02/11/14/16/17/24–27/34/36/38–40/45/47/49/55/56/59/60; NFR-10/12/17/19/23/25/26/28/31/34/36; §5.1 steps 12–14; §21.5/21.6; §31.6–31.7; §31.10. | Typed job stage, never percent; playback only after technical+safety validation. Adult can mark a video unsuitable and return to script review; allow at most two quality regenerations after the initial accepted full request; each accepted full request consumes one run/quota unit even on later failure, scene retries consume none, and script hash must be reconfirmed. Hide rejected video immediately on accepted replacement request and keep hidden if replacement fails. Complete/cancel run, history, completed-run delete, DELETE_PENDING, quota, and notifications are server-confirmed states only. Lesson delivery history is 30 days from first delivery/open under active scope; run history has no inferred 30-day window. Lesson download only when permitted; feedback has no chat/completion toggle/drawing attachment. Inbox reminder is deduped at +144 h; push/email best effort; +168 h closeout is not resumable. No video download/export or guessed quota/purchase. | REAL only exact profile DELETE remains owned by R1. Parent job/status/video/safety/playback/regeneration/complete/cancel/run history/run delete/lifecycle receipts/quota/purchase/lesson history/download/feedback/inbox routes are ABSENT: FAKE_PORT. Normal app shows explicit unavailable/pending only; tests alone may use fakes. | E: apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx; StoryScreen.tsx; HandoffScreen.tsx; StoryHistoryScreen.tsx; LessonHistoryScreen.tsx; QuotaScreen.tsx; NotificationsScreen.tsx; navigation/useParentController.ts; navigation/useParentPlatformController.ts; navigation/parentFlowV1.ts; application/use-cases/ParentLearningUseCases.ts; application/use-cases/ParentPlatformUseCases.ts; application/ports/ParentPorts.ts; infrastructure/http/ParentApi.ts; domain/types.ts; ParentExpoApp.tsx; apps/ui-mobile/tests/parentSrsBehavior.test.ts; apps/ui-mobile/tests/parentFlowV1.test.ts. N: R4 report only. If a new UI file proves necessary, stop and revise the plan before launch; no wildcard. | Synthetic no-percent/busy-not-success, accepted request/quota accounting, two-regeneration ceiling, script reconfirmation, rejected-video immediate hide (including replacement failure), idempotency/reconciliation, quota exhausted, no fake video, post-video pin/no-pin, cancel/delete pending, 30-day lesson history vs separate run history, permitted content download, feedback restrictions, notification dedupe/144h/168h closeout, every §21.6 error group and exact retry rule. WR-AC21–30, 32, 37, 40–44. Owner checks labels/reconciliation/player gate/activities/pending lifecycle/history/inbox/quota/scaling; local synthetic screenshots only. | Stop if absent route would show success, rejected video reappears, accepted request accounting is misstated, unresolved Q193 leads to purchase, duplicate commands are possible, or package/backend/Modal/new UI file is needed. No payment or real player wiring. | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R4_20261113.md |

## 4. Checkpoint state machines

- R0 controls: idle/focused → pressed → busy → confirmed result or explicit error/unavailable. A busy state never transitions to success without a confirmed operation; primitive interaction callbacks remain unchanged.
- R1 account/profile: signed-out → authenticating → authenticated → profile-list → selected profile revision → consent current/pending/revoked → profile/context form → confirmed supported fields or typed unavailable. Gender stays an explicitly unsaved local draft. Token expiry permits one refresh/re-auth attempt. Share: named invite pending → accepted scoped 90-day grant → expired/revoked; decline is terminal. Profile deletion: confirmed request → DELETE_PENDING → confirmed/purged; block access while pending.
- R2 entry: home → profile selected → optional topic → optional exact lesson pin → lesson/group invitation pending → accepted or declined → current access/version review → preflight. Stale/revoked lesson returns to review. A personal copy remains a private draft with lineage only when its unavailable route later exists; no source mutation. Run-start waits for mandatory photo and never creates StoryRun here.
- R3 creation: optional guide or skip → mandatory photo → optional typed idea or bounded audio capture (≤2 minutes and ≤20 MB) → transcript unavailable or transcript review/edit/explicit confirm → subject match/review → confirmed subject, or mismatch choice (change topic / one retake) → context review/confirm → activity loading → canonical candidates or gated exactly-three drafts, otherwise blocking unavailable/no-fit → exactly-one main selected → story draft/rewrite (up to SRS limit) → exact revision review/confirm. Any stale revision returns to its review; no transition skips activity selection.
- R3 media-boundary test: synthetic photo at 20 MiB is accepted for the offline boundary model; an oversized photo is blocked before upload; interrupted transfer remains resumable only with an approved session/receipt contract, otherwise it is explicitly unavailable (WR-AC45).
- R4 delivery/lifecycle: exact script confirmation → admission unavailable or accepted → queued → running → reconciling or terminal job result. Only technical+safety-ready output enters private playback. Mark unsuitable → return to script review → up to two quality regens after initial request; accepted replacement immediately hides rejected video and it remains hidden if replacement fails. Reconfirm exact script; each accepted full request consumes one request/quota unit, scene retries none. Playback → complete or allowed regenerate. Lesson pin shows exact-version activities; no-pin shows only run-pinned main. Cancel/completed-run delete/profile lifecycle → pending → confirmed; inbox +144h and closeout +168h follow server state. Unknown state remains reconciling and blocks duplicates.

## 5. Offline acceptance criteria

- WR-AC1: every foreground/fill pair meets proposed 4.5:1 normal and 3:1 large-text contrast on real fills.
- WR-AC2: every state has text/accessibility semantics; color alone never indicates state.
- WR-AC3: targets at least 44 dp, prefer 48 dp; scaling never clips/overlaps.
- WR-AC4: R0 props/defaults/copy/callbacks/tabs/safe area/states remain compatible; job type has no percent field.
- WR-AC5: auth expiry allows at most one refresh/re-auth retry and preserves safe local draft.
- WR-AC6: selected profile context is single-profile/revision-bound; no cross-profile content.
- WR-AC7: missing/out-of-scope resources have safe response without revealing resource existence.
- WR-AC8: profile/consent loading, empty, stale, denied and confirmed states never falsely claim unavailable mutation success.
- WR-AC9: topic and lesson each may be omitted; selected lesson binds exact version/hash; stale requires adult review.
- WR-AC10: run-start cannot create StoryRun or call VLM before mandatory photo.
- WR-AC11: no-preset works and does not force lesson selection.
- WR-AC12: active run cannot be duplicated; absent resume/history returns typed unavailable.
- WR-AC13: guide uses 4–8 deterministic progressive strokes and failure does not block capture.
- WR-AC14: denied camera leaves gallery; denied mic leaves typed idea; synthetic permission tests cover both.
- WR-AC15: transcript requires adult review/confirmation; unavailable transcription is not fake.
- WR-AC16: mismatch allows topic change or one retake only; lesson pin unchanged.
- WR-AC17: subject/context confirmations bind current revisions; stale requires review.
- WR-AC18: one main activity is mandatory before script; unavailable/unknown preview cannot bypass.
- WR-AC19: catalog-first filtering and exact pin; exactly three gated drafts only if no fit; replacement excludes shown/rejected.
- WR-AC20: guide/activity requests exclude raw image/audio/identity/profile; script confirmation binds exact hash.
- WR-AC21: typed job stage has no percentage; busy/reconciling never means success.
- WR-AC22: video waits for technical/safety readiness; rejected output and regeneration limits follow SRS.
- WR-AC23: no-pin post-video shows only run-pinned main without catalog query; pinned state uses exact version.
- WR-AC24: cancel/delete stay pending until server confirmation; reconciliation avoids duplicate command.
- WR-AC25: quota/purchase is server-derived; unknown Q193 cannot show purchase success or fabricated values.
- WR-AC26: §21.6 errors recover safely without provider diagnostics or cross-profile leakage.

- WR-AC27: versioned age bands are enforced; legacy 121–155-month profiles cannot start a new run, and legacy draft actions follow the read/delete rule without inferred migration.
- WR-AC28: lesson/profile sharing is scoped and revocation/expiry blocks new reads; only published/currently authorized lessons appear, without cross-scope disclosure.
- WR-AC29: Parent feedback has no chat or image attachment and cannot show submitted/replied success when its port is unavailable.
- WR-AC30: lesson delivery history follows the resolved 30-day window and active-scope rule; Parent run history lists only owned/authorized lifecycle records. Do not infer that run history shares the lesson 30-day window; no revoked content is exposed.

- WR-AC31: optional gender uses only boy/girl/prefer not to say; remains an unsaved draft until approved SRS+BE schema/migration/revision hash; omitted from API and all model payloads, with no false save claim.
- WR-AC32: FR-P-09/BR-11 permit at most two quality regenerations after the initial accepted full request; each accepted full request consumes one run request slot and one quota unit even on failure, automatic scene retries consume neither, exact script is reconfirmed, and rejected playback hides immediately after replacement acceptance and remains hidden on replacement failure.
- WR-AC33: FR-P-03 audio is capped at 2 minutes and 20 MB; over-limit audio is rejected before transcription, typed idea remains available, transcript edits bind to a revision and require explicit adult confirmation.
- WR-AC34: FR-PL-07/08 named Teacher share is pending until accepted, scoped and 90 days, audit is metadata-only, revoke is immediate and blocks new read/token/unaccepted job; absent routes never show a successful grant.
- WR-AC35: lesson and Parent-group invitations support pending, accept, decline, active/revoked as specified; only accepted/current scope unlocks content, and unavailable routes do not alter membership.
- WR-AC36: profile delete immediately blocks new run/profile/playback access as required, stays DELETE_PENDING until lifecycle confirmation, and never claims purge complete early.
- WR-AC37: only completed runs can be deleted; unfinished runs use cancel; both remain pending until confirmed, preserve consumed quota metadata, and prevent duplicate commands.
- WR-AC38: consent capture/revoke is explicit and revisioned; absent consent state/write/revoke routes remain unavailable and consent is never inferred from profile existence.
- WR-AC39: settings/account change-password, reset/re-auth and sign-out use Firebase Authentication; sign-out clears local session and does not expose raw auth diagnostics.
- WR-AC40: Parent inbox is canonical, +144h reminder is deduped, push/email are best effort, +168h closeout follows server lifecycle, and delivery failure does not alter run state.
- WR-AC41: lesson history is 30 days from first delivery/open and respects active scope; run history lists authorized owned lifecycle records without inheriting an unsupported 30-day assumption.
- WR-AC42: permitted lesson content download and scoped feedback are distinct from forbidden video export; feedback has no chat, completion toggle, or drawing/image attachment.
- WR-AC43: every §21.6 error group maps to its exact review, safe response, retry/hold/poll rule, including all Teacher-only groups as no Parent route.
- WR-AC44: every route absent from the BE handoff has a typed unavailable normal-app result; fake responses appear only in synthetic tests and cannot produce fake success.
- WR-AC45: NFR-32 photo input is at most 20 MiB; over-limit input is blocked before upload, and interruption has an explicit resumable/unavailable state without a false upload-success claim.

## 6. Command ceilings per checkpoint

For EACH R0–R4:
- Codex runs zero test, typecheck, validator, diff-check, install, emulator, network, or Modal commands.
- Coordinator ceiling: at most two pnpm run test and two pnpm run typecheck executions per checkpoint, one baseline and one post-implementation.
- Owner ceiling: at most two runs each of validate_harness, validate_repository_security, validate_architecture, and git diff --check per checkpoint, plus one emulator review.
- These ceilings never widen the allowlist. No install, network, Modal/backend calls, or child data.

Owner may lower ceilings. Baseline does not replace post-run checks. Evidence reports use the exact N paths above; screenshots remain local and contain no secrets, account identifiers, or real child data.

## 7. §31.10 status and unresolved gates

Do not reinterpret every §31.10 row as OPEN because an earlier Rev60 answer kept rows 16–29 open. Preserve Rev67’s per-row statuses and ask before reopening resolved rows.

OPEN-OWNER items: §31.10 row 10/Q192; §21.5 purchase availability Q193; quota buyer/allocator/payment/exhaustion/terminal expiry in row 2; remaining owner-dependent teacher eligibility/consent (row 4), script-following defaults/overrides/pins (row 5), school quota payer/allocator (row 6), sharing fields/consent/renewal (row 8), visual asset review/publish (row 9), personal-copy schema/retention (row 12), role/resolver policy (row 14), legacy profile migration (row 16), audit policy details (row 17).

The separate owner-requested gender field is not in Rev67 and is not an answer to any OPEN-OWNER row. It stays pending a later SRS update and BE profile schema/migration/revision-hash change; this plan permits only an explicitly unsaved form draft.

OPEN-TECHNICAL items: §31.10 rows 13–15 API/snapshot/recovery/receipt/purge details; row 17 audit mapping; rows 18–23 SVG source classes, guide quality review/adjudication, authoring/revision, renderer/performance SLO, API/persistence alignment, and failure recovery. §31.17/31.18 also leave API V2, DTR/DDL, guide/activity rubric, performance, SVG readiness and recovery open.

Rev67-resolved examples include 30-day history (row 3), no-preset activity behavior (row 13), and supersession policy (row 15). Preserve other RESOLVED statuses too. Open items do not authorize product-policy choices; use typed unavailable states until decisions/gates are recorded.

## 8. Dependencies on backend routes not yet available — FAKE_PORT

The BE handoff at features/FEAT-063-system-architecture-rearchitecture/plan/BE_AI_HANDOFF_FOR_AI_AGENT_20261113.md identifies existing Parent profiles, selected StoryRun v1 operations, script confirmation, and legacy AI operations. This is read-only handoff evidence, not live verification. REAL applies only to the exact listed operation/contract; it does not prove the Rev67 API V2 flow.

ABSENT, therefore FAKE_PORT until approved and implemented: Rev67 photo/audio upload sessions and resumable receipts; transcription/transcript confirmation; SVG catalog/vector engine/approved guide draft; API V2 mismatch/retake and revision snapshot; activity filtering/hydration/exactly-three gated drafts/replacement exclusion/selection persistence; activity-bound story; profile consent/share-grant invite/accept/decline/revoke and lifecycle receipts; lesson/group invitations, catalog/access/personal-copy, delivery history/download/feedback; video admission/status/reconciliation/retrieval/safety/regeneration; completion, run history/cancel/delete, quota/purchase, DELETE_PENDING purge, and inbox/read/reminder state. Gender persistence also remains unavailable pending SRS+BE schema migration/revision hash. Do not wire real routes for these operations. Normal app displays explicit unavailable state; tests alone may supply fake responses.

## 9. What cannot be proven offline

- Rev67 formal sign-off; it remains unsigned.
- SRS_AUTHORITY and repository FEAT-063 SRS update.
- Approval/deployment of API V2, DTR/DDL, schemas, privacy, idempotency, quality, renderer/performance or lifecycle contracts.
- Existence of routes absent from the handoff; no network request was made.
- Real AI/VLM/audio/video quality or safety.
- Live quota, payment, purchase, retention, deletion/purge behavior; run-history retention cannot be inferred from the resolved lesson-history window.
- Gender persistence, migration, schema compatibility or whether the owner request is accepted into a later SRS.
- Real-device visual/accessibility before emulator review and OI-17.
- Android permission/gallery/lifecycle/screen reader/text scaling/video behavior without owner review.
- Passing tests, typecheck, validators, diff-check, or emulator review. None were run for this planning task.

## 10. Stop conditions and out of scope

Stop at first pin mismatch, unlisted file change, new route/dependency need, failed acceptance criterion, out-of-checkpoint screen edit, Rev67 conflict, inaccessible state, or evidence gap. Do not widen a checkpoint allowlist. Prepare a revised plan and obtain a new launch instruction.

Out of scope: implementation by this draft; backend/API/DTR/DDL; real AI/provider/video/payment calls; Modal; dependency/package/lock changes; copied/commissioned art; child-facing surfaces; gender SRS/schema/migration change (only a draft-only unsaved form request is planned); Teacher/Manager/Admin authoring, billing, moderation, class/occurrence and emergency controls; edits to D-013/Addendum 11/Plan Revision 5; authority/decision/approval/context/status records; deploy/stage/commit/push.

## 11. Exact baseline allowlist and pins

E paths are editable only where the checkpoint row lists them. N paths are absent at baseline and may be created only in the listed checkpoint. R is read-only; H is frozen. No wildcard paths. Sizes are bytes; each hash is full SHA-256.

| E | apps/ui-mobile/src/parent/application/ParentApplicationError.ts | 1027 | 3087B87025511877F983BF0A9331E11DF110078F938354C87800E61CFF4BD2AF |
| E | apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts | 2164 | 0373643C8C92C9EA6D144C22F27202D8A09163FB03D369A786982E9413CBB9A3 |
| E | apps/ui-mobile/src/parent/application/ports/ParentPorts.ts | 8472 | 62CDC570BEEE074D1BD4558A5567E37CD2911DC7041D4689F231CC2884182551 |
| E | apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts | 6766 | 8812D4AB0DAB6DB7C35CDA9F14EEEB953201AC0157DDE1C4C2216A8FD40C43AE |
| E | apps/ui-mobile/src/parent/application/use-cases/ParentLessonUseCases.ts | 711 | 0C46FF6814B06E6363CBE779C63A2AD0EB2F59C6DFCDD5206B7756C5748CB59C |
| E | apps/ui-mobile/src/parent/application/use-cases/ParentPlatformUseCases.ts | 2722 | 4E4FB4449451B036FA479D73DD5E4F1CE5A4D27169B5603578B6221486AB2A16 |
| E | apps/ui-mobile/src/parent/domain/storyDraft.ts | 2320 | E8D24ED55701511EB5F13A1E6C32CFE0DBACA459D444DD27F55248EAD4ED9C0C |
| E | apps/ui-mobile/src/parent/domain/types.ts | 10152 | 990FA43EF6E04874FD72E9E62AC7CCAD9332F687BFE92A64586A87A7010A0240 |
| E | apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts | 25559 | 182EBB83A8A9A284444FAADE68740C5DD50CDD0F387393A4577A2C7AD626F7DE |
| E | apps/ui-mobile/src/parent/ParentModule.ts | 1238 | B1E6A5236F57E0A6A4950150A245C29FE2098E75F95C55B2EB1787360806EA12 |
| E | apps/ui-mobile/src/parent/presentation/components/GoogleSignInButton.tsx | 2562 | 26F0BF8BAB3AC1BB47AEC341539ADDCC870AE49D2CE76DD58716053B791EF5C9 |
| E | apps/ui-mobile/src/parent/presentation/components/ui.tsx | 11444 | 722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773 |
| E | apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts | 13722 | 70872D3BE7316D88B2608B16C9D153F4F086F5654D007ABFC668A02CF5CBE242 |
| E | apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts | 34507 | 19EEEB022C9874622A682D9DD822BD2982CE05F4840BEEE6E23A617315CD7DCA |
| E | apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts | 7643 | BB91CC698A6C9512DB6ABEE7691D78214EC8309D772B014464DA16C999DCFDFA |
| E | apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts | 755 | 611A0C2207287963762295F42C02323AE297F20C4D5833F5304AD71B8371F29A |
| E | apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 16836 | 5861CED5A1D98A4D8E00251B278C9AAEC271E4F4D4292E59691A20901E21508C |
| E | apps/ui-mobile/src/parent/presentation/screens/AccountScreen.tsx | 3187 | 2A350B4BD4949DCABCA2287DC390581E69B917956A8CF811B2E92AC32205B3B0 |
| E | apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx | 3462 | 64CD3C7CDA5291C4EA69363A77EEF5872EAC26B02A2C908C1B9455EAC00A07A7 |
| E | apps/ui-mobile/src/parent/presentation/screens/AuthScreen.tsx | 4101 | DADAC33D4EA38F813C4549DE3959D3405FE2EA37C2ECE498DDD2CFDD25336DEC |
| E | apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx | 4266 | 49DD0029CF29075E042D09F6017DB8CC37449CE91E35095DB6A61196D942A102 |
| E | apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts | 1962 | 5BE1210C95C9F1CEBABADEE7DAD2169620B5B438BA85DE24941236DF018630F0 |
| E | apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx | 2851 | 79EAC93B95E8F02E927E80D3BDE34CAADE07C550F1B0B99D5373AE8B494CB68E |
| E | apps/ui-mobile/src/parent/presentation/screens/DrawingGuideScreen.tsx | 2814 | 45D6310ABB43B5C0ECD5AE854D6C906AB9919DB67E179510088BCB82B4235B9F |
| E | apps/ui-mobile/src/parent/presentation/screens/HandoffScreen.tsx | 1704 | 18C2DB25669A1020F1D593F532E4C38F1905F2EF296C02245C7D2DF2E925EA7C |
| E | apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx | 4838 | A4A29FCA5B3EF090A22779214939A0DE6165F96276C9AEA58E0C2E6CD4632B9F |
| E | apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx | 9876 | 35D75628DF9220FABA787010E5E40A895FA99AE3A3A34F325E7B752DDFB04003 |
| E | apps/ui-mobile/src/parent/presentation/screens/LessonHistoryScreen.tsx | 3421 | 6D9B1DB17245635F583BDBC2DE559549ABDC75FFAAED26A9D702F4FED7429ABB |
| E | apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx | 1595 | C43EC59DBA63C00E9C9489072BF014060AF33AE3C93198F29D8BAD78903782B0 |
| E | apps/ui-mobile/src/parent/presentation/screens/NotificationsScreen.tsx | 1798 | 5C9AC558A53CE96BC13771835D3B5A0FF3AC0FE21B18D96EE85C780AFD366E7E |
| E | apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx | 2054 | 4E8CB3F6B92AE8614DBE282E623A4E769CF16574EF0B14CAAC468B3A7C054358 |
| E | apps/ui-mobile/src/parent/presentation/screens/ProfileFormScreen.tsx | 3169 | C20BDE89B47BFF70F7389E9D8694952FE648B45B0A70ED36540D9B4CF5D6630F |
| E | apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx | 4019 | 66E39128D43B3D5E4F497785B4E986C82E23BFC4D1CC91771F6F43B8422D4CA4 |
| E | apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx | 3529 | A9EB79B7BC2C5E1EEFF8304299F37C251BF285DD5500F673194C67064773CA29 |
| E | apps/ui-mobile/src/parent/presentation/screens/QuotaScreen.tsx | 1480 | B6DD6051244288845178E195BFBD5BB69A4748897293BDC7AA37EAB5512FB93C |
| E | apps/ui-mobile/src/parent/presentation/screens/SettingsScreen.tsx | 2191 | FD1015ACF453F3C303392F4A005F60EDBBD3F791BDF365AD6996F4316C81A185 |
| E | apps/ui-mobile/src/parent/presentation/screens/StoryHistoryScreen.tsx | 3716 | AA1138C6AB64B9E7EC3D327AE01360DFE5D1512744410F07EB207C5BEE57A759 |
| E | apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx | 3891 | 51FF610C83D79002C248B3447DCFE7A7758E9EA7DE80975B872E1E9070301FB9 |
| E | apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx | 6667 | 8A87F7C3769CD57DF9F97E21D85163FF448409B586E1C6CFADB9C16937B157D5 |
| E | apps/ui-mobile/src/parent/presentation/screens/TranscriptReviewScreen.tsx | 2360 | 8834A9E90745BEBD3F83483A2A5C0A85F92231D2073A91E92BAFEBFE93944823 |
| E | apps/ui-mobile/src/parent/presentation/screens/UnderstandingScreen.tsx | 2097 | 8F21667581CBB1F89C80309E0FCBD0CC71F7A9909AF10B4A18ED38DB03216D8E |
| E | apps/ui-mobile/tests/parentApiI2Contract.test.ts | 17370 | C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075 |
| E | apps/ui-mobile/tests/parentFlowV1.test.ts | 13508 | 7F4623080EDE3980D96CD426242C161A630F198B1627685D6B4DB0C0F4A9FCD5 |
| N | apps/ui-mobile/src/parent/application/ports/ParentCapabilityPorts.ts | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| N | apps/ui-mobile/src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter.ts | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| N | apps/ui-mobile/tests/parentSrsBehavior.test.ts | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| N | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R0_20261113.md | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| N | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R1_20261113.md | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| N | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R2_20261113.md | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| N | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R3_20261113.md | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| N | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R4_20261113.md | 0 (absent) | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| R | AGENTS.md | 3406 | 89ACC84AA4D838730205A03917B40DEB37E9622AAF7092E982476D934EC29A61 |
| R | docs/context/SRS_AUTHORITY.md | 4054 | 032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F |
| R | docs/governance/APPROVAL_POLICY.md | 707 | F734FD4C6416A526EBF2C0031804069467F6361B3A9854E7B5DBCA0AEADE4216 |
| R | docs/governance/FRONTEND_ASSET_GATE.md | 831 | 28DD1E51B54206C7A85B8F3BA4E0DAA638D4CBCF4CAF23BA04A2CED4BC76DDC1 |
| R | docs/governance/WORKFLOW.md | 1240 | 23D8717F82A85DB8E66922C81460A16EC24022FFD766C63457D308491A8D98A3 |
| R | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md | 171609 | 7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2 |
| R | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | 553948 | 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B |
| R | features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REAL_FLOW_NO_MODAL_TEST_LOG_20261113.md | 9816 | F19BC575C411A389720C7AF7EC405BA6CCD8106FE3C7D3D6F1BD80AE08154E40 |
| R | features/FEAT-063-system-architecture-rearchitecture/plan/BE_AI_HANDOFF_FOR_AI_AGENT_20261113.md | 9206 | F746A7B3D425A2C6EF0541C28A8584CC8CEF0D6D0F140CD09A68F14F9FA091EA |
| R | features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md | 39015 | 2F5D9304F3555A9DC28B7A8EB87DB9958A890EA161F5E39486811DD755C8380C |
| R | features/FEAT-081-parent-ui-mobile-port/CONTEXT.md | 21613 | 58FC49D0F444512BB7D7513A348FB055698BCBEBC5242C70F99744A00050FBBB |
| R | features/FEAT-081-parent-ui-mobile-port/DECISIONS.md | 13613 | 4FC79E32E838C5A07E01CA601F28AED35B437334FE4D73493E84BB5DF4F94FB3 |
| R | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE3_20261113.md | 27257 | C3EB7AA66C45652F952B944A5DC1DE53440F10D383414558F934C8B1605F70AA |
| R | features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_4.md | 18717 | 6D3FEF1B2C24595EBC4F6499368330C485471AF59A4E9C974CF1F5C97BD71E0A |
| R | features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_5.md | 49834 | 73A706C2A241AC2CF4F8A48946672F1B9549FE44023DEA8FBC4A12E0E089FE67 |
| R | features/FEAT-081-parent-ui-mobile-port/status/STATUS.md | 16314 | BE3EEF0541B90A0105506C6B6371AB45B9A0C20C4E220B4804345AA633240C82 |
| R | tmp/fe081-waveR/CRAYON_DESIGN_LANGUAGE_PROPOSAL.md | 10409 | 36A00689D413EE6FDCFD1F93C58B4C383EFDC5264DD745D8791ED2C396E814FD |
| R | tmp/fe081-waveR/SRS_UX_REQUIREMENTS_MAP.md | 25993 | 5BF91D0882183C7CDBC008CE5A1A28550571118C6A338D7B777349146FB30ECF |
| R | tmp/fe081-waveR/WAVER_APPROVAL_ENTRY_DRAFT.md | 3388 | 1B87D2DF5E95633AA5B622C0A6DBBE673A782046D66B7609B9EB903D44638B91 |
| R | tmp/fe081-waveR/WAVER_D014_DRAFT.md | 3830 | 3EEA1DC3ACC5E885866A8A6A3FB7C23C3495FA041C6B0BC92A9FBCA02EBD9F91 |
| R | tmp/fe081-waveR/WAVER_OWNER_QUESTIONS.md | 9424 | BB565C3A263C2A4805F5D1095E2FE116483CA6542A781825879F1AE91BD93758 |
| R | tmp/fe081-waveR/WAVER_PLAN_DRAFT.md | 43952 | 39DE33EF4F54C4CA6A4358B907674EBAAFEC23AC9F3FD3A3463050DAF039156A |
| R | tmp/fe081-waveR/withdrawn/PLAN_REVISION_6.md | 43952 | 39DE33EF4F54C4CA6A4358B907674EBAAFEC23AC9F3FD3A3463050DAF039156A |
| R | tmp/fe081-waveR2/srs_new/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_Rev67_owner_supplied.md | 634291 | B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |
| H | apps/ui-mobile/package.json | 2081 | AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF |
| H | apps/ui-mobile/scripts/component-registry-check.md | 94 | 074D275BB80B32EBB84BFECC68048B1DA8AFEC4A0720CAC2BA41B798D39833D0 |
| H | apps/ui-mobile/scripts/start-android-dev.ps1 | 4507 | 3EF2CE8D9232CF483121794FB19B2577531686511C721D4D7EC2BA215850EB18 |
| H | apps/ui-mobile/scripts/ui-verification.md | 126 | AC355095C4FFC7D3930E7104031B40F73966ED0CAD06850811457B1B913AE3D9 |
| H | apps/ui-mobile/scripts/validate-ui-copy.mjs | 21206 | 5AD006820035DF1B4DF1489338CBC08A06B877B80B2B345C1A82806D729A0391 |
| H | apps/ui-mobile/src/parent/application/use-cases/ParentAccountUseCases.ts | 765 | 1EDA6FD349FA8E1E719C97C3A1551B90F7BDCFAB236C81F5E3FDD8BE39560635 |
| H | apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts | 2994 | C3A88AB853C6EE96882ABF950EAC76032E68D97D6E52D7A42EF63C869E99CCC2 |
| H | apps/ui-mobile/src/parent/domain/profileRules.ts | 356 | 25EA93AD268DC49704D64F87A2D1252983F745A530CB43D8D67AEFD3EE16C3EE |
| H | apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts | 10305 | BBFEEF77C3CABD2632AFE7EE96D6996509C809BB8521FBD80326223961DD6077 |
| H | apps/ui-mobile/src/parent/infrastructure/config.ts | 1049 | F0C1E0198460E9A432E81D9E8724BCC35CD030CA8C411F2050503F1C87C0FF07 |
| H | apps/ui-mobile/src/theme.ts | 2134 | 7114FB92B63855E2FE9E6B77D1111AAD8FB1F33555ABBF321B6D3DE1D8F16B46 |
| H | apps/ui-mobile/tests/apiRetryIdentity.test.mjs | 3188 | C0DC06450146667AC16C8108960E892F30B4D34AD0A1B0AD3EBB3EC19D5C6054 |
| H | apps/ui-mobile/tests/catalogViewModel.test.ts | 3254 | 8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978 |
| H | apps/ui-mobile/tests/mainFlowSafety.test.mjs | 7985 | 41B82F60E83B17DBB09F7195ACF122E3653046A49822D42D5416E39B53582D74 |
| H | apps/ui-mobile/tests/parentLearningI2.test.ts | 5841 | E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892 |
| H | apps/ui-mobile/tests/storyDraft.test.ts | 1770 | 07C8BE23A875F2082CDC2626A23E4462A46CF61525BD487F9053CCD00CBCFC50 |
| H | pnpm-lock.yaml | 470780 | 5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72 |

## 12. Former-H paths opened as E and rationale

The paths below were frozen H paths under the prior Wave V inventory and are proposed E in this baseline. They are editable only when the corresponding checkpoint row lists them. No H path is implicitly open.

| Former-H path now E | Rationale |
| --- | --- |
| apps/ui-mobile/src/parent/application/ParentApplicationError.ts | Map SRS recovery errors to safe user messages without raw diagnostics. |
| apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts | Compose typed unavailable capabilities; keep test fakes out of product success paths. |
| apps/ui-mobile/src/parent/application/ports/ParentPorts.ts | Define typed operation/result boundaries while preserving listed route contracts. |
| apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts | Enforce activity choice and avoid unsupported activity success paths. |
| apps/ui-mobile/src/parent/application/use-cases/ParentPlatformUseCases.ts | Represent absent lifecycle/history/quota operations as unavailable. |
| apps/ui-mobile/src/parent/domain/types.ts | Add explicit unavailable/pending/reconciliation/player states without weakening contracts. |
| apps/ui-mobile/src/parent/domain/storyDraft.ts | Preserve exact story revision and confirmation rules. |
| apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts | Prevent calls to absent routes; preserve only handoff-listed operations. |
| apps/ui-mobile/src/parent/ParentModule.ts | Compose normal app with unavailable adapters and no fake success. |
| apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | Expose/reorder screens as checkpoints launch. |
| apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts | Add pure gates and recovery for exact revisions and new state order. |
| apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts | Enforce photo, confirmation, selection and safe unknown-state gates. |
| apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts | Remove false success for unlisted lifecycle/history/quota calls. |
| apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts | Represent exhaustive flow states/transitions. |
| apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts | Distinguish empty from unavailable; avoid fabricated recommendation states. |
| apps/ui-mobile/tests/parentFlowV1.test.ts | Permit synthetic flow/recovery tests if R0 test file is insufficient. |
| apps/ui-mobile/tests/parentApiI2Contract.test.ts | Assert absent routes make no requests and listed route contracts stay unchanged. |
| apps/ui-mobile/src/parent/application/use-cases/ParentLessonUseCases.ts | Guard lesson operations against routes absent from the BE handoff and represent them as typed unavailable. |

The remaining H paths stay frozen because this draft does not depend on modifying them. This includes apps/ui-mobile/package.json and pnpm-lock.yaml. If a future checkpoint cannot meet its exact scope without changing a remaining H path, stop and prepare a separately approved allowlist revision.

## Coverage check against the SRS

This inventory was checked against the Rev67 requirement tables, not only the Parent screen catalog. It assigns every FR-C-01–12, FR-P-01–13, FR-PL-01–25, NFR-01–38, and BR-01–60 identifier to a checkpoint or gives a role/backend reason for deferral. A checkpoint assignment covers only Parent client behavior and synthetic offline tests. Backend-only clauses remain unproven and use FAKE_PORT where their routes are absent. Source line references below are Rev67 line numbers.

### Parent/common functional requirements

| Requirement | Rev67 section and line | Owner checkpoint | Client coverage and deferred portion |
| --- | --- | --- | --- |
| FR-C-01 | §6 table line 492; UC-01/13 | R1 | Firebase auth, safe setup denial and recovery; backend issuer/scope enforcement remains server-owned. |
| FR-C-02 | §6 line 493; §7.2 | R2/R3 | Exactly one selected child before run; backend request enforcement is not proven offline. |
| FR-C-03 | §6 line 494; §19/§21.6 | R2/R4 | No duplicate active run; retry only after terminal state. Database concurrency/lock is backend-only. |
| FR-C-04 | §6 line 495; §31.3 | R1 | Separate Parent/Teacher scope and generic denial; cross-scope server proof deferred. |
| FR-C-05 | §6 line 496; §7.2/§31.8 | R1 | Profile revision UI and stale review; immutable persistence/migration remains BE. |
| FR-C-06 | §6 line 497; §5.1 | R1/R3 | Distinguish app history from adult-entered external context; only reviewed minimal snapshot proceeds. |
| FR-C-07 | §6 line 498; BR-20 line 263/2498 | R1/R3 | Sensitive support need is excluded by default; no diagnosis or unsupported AI context. |
| FR-C-08 | §6 line 499; UC-07/11 | R4 | Cancel unfinished/delete completed, pending and quota-preservation states; lifecycle purge is FAKE_PORT. |
| FR-C-09 | §6 line 500; NFR-09/37 | R3/R4 boundary | Client retains source references and does not expose binaries/URLs; immutable storage lineage is BE-only. |
| FR-C-10 | §6 line 501; UC-09; §21.6 line 1735 | R1 | Profile delete and DELETE_PENDING UI; immediate revoke/purge receipt remains partly FAKE_PORT. |
| FR-C-11 | §6 line 502; UC-15; §21.5/21.6 | R4 | Inbox +144h reminder and +168h closeout states; scheduler, email/push delivery and server transitions are FAKE_PORT. |
| FR-C-12 | §6 line 503; NFR-32 line 656 | R3 | Photo/audio size, duration and interruption state; resumable chunk receipts and server validation deferred. |
| FR-P-01 | §7.2 line 509; §21.5 lines 1702–1703 | R1 | Login, re-auth, account settings and sign-out. |
| FR-P-02 | §7.2 line 510; §21.5 lines 1703–1705 | R1/R3 | Profile selection plus mandatory photo before run/VLM; camera denial keeps gallery; exact API V2 order remains open. |
| FR-P-03 | §7.2 line 511; BR-23 line 266; NFR-32 line 656 | R3 | Typed/audio idea, max 2 minutes/20 MB, transcript review/edit/confirm; transcription and upload routes FAKE_PORT. |
| FR-P-04 | §7.2 line 512; §21.5 line 1706 | R3 | Subject match, adult correction, revision and one-retake flow; target VLM route FAKE_PORT. |
| FR-P-05 | §7.2 line 513; §5.1/§31.17–31.18 | R3/R4 | Catalog-first preview, exactly one main pre-script, gated exactly-three drafts only if allowed, exact post-video pin; routes FAKE_PORT. |
| FR-P-06 | §7.2 line 514; §5.1/§21.6 line 1724 | R1/R3 | Consent-aware minimal context revision and adult confirmation; target snapshot/consent routes FAKE_PORT. |
| FR-P-07 | §7.2 line 515; BR-13 line 256/2491 | R3 | Initial story plus at most three rewrites; no direct scene edit; existing legacy routes do not prove target flow. |
| FR-P-08 | §7.2 line 516; §21.5 line 1708 | R3/R4 | Exact script hash confirmation, ready-only playback, complete/regenerate; video admission and lifecycle FAKE_PORT. |
| FR-P-09 | §7.2 line 517; BR-11 line 254/2489; §21.6 line 1727 | R4 | Unsuitable mark, max two accepted quality regens after initial, hide rejected output immediately on accepted replacement; exact accounting in WR-AC32. |
| FR-P-10 | §7.2 line 518; §21.6 lines 1729–1733 | R0–R4 | Vietnamese stage/error and exact retry/hold/poll rules; every error group also mapped in §21.6 surface matrix. |
| FR-P-11 | §7.2 line 519; BR-42/44/46 lines 285–289 | R3 | Optional progressive 4–8 step SVG guide; catalog-first; no child data; skip/failure nonblocking. Source/rubric/render gates remain open. |
| FR-P-12 | §7.2 line 520; §21.6 line 1723 | R3 | Topic compatibility, adult choice of topic change or one retake, retain exact lesson pin. |
| FR-P-13 | §7.2 line 521; BR-55 line 2534/2679 | R2/R3/R4 | Topic/lesson optional, image mandatory, guide/presentation optional, main activity before script, exact post-video list behavior. |

### Parent lesson/library requirements

| Requirement | Rev67 section and line | Owner checkpoint or disposition |
| --- | --- | --- |
| FR-PL-01 | §31.2 line 2641 | R1: scoped authorization/revoke UI; BE auth remains backend-owned. |
| FR-PL-02 | §31.2 line 2642 | R1/R2/R4: tenant-safe profile, lesson, invitation, feedback and quota surfaces; server isolation proof deferred. |
| FR-PL-03 | §31.2 line 2643; §31.10 row 12 | R2: only authorized private draft/personal-copy editing with lineage; no Parent AI suggestion; absent copy route FAKE_PORT. Editable fields/retention stay open. |
| FR-PL-04 | §31.2 line 2644 | R2: discover only allowed PUBLIC/current lessons and download only permitted content (download control in R4). |
| FR-PL-05 | §31.2 line 2645 | R2 consumer view only; publication moderation/hide/unpublish actions deferred to authorized Teacher/Manager/Admin. |
| FR-PL-06 | §31.2 line 2646 | R2: named/group lesson invite accept/decline and revocable access; API absent. |
| FR-PL-07 | §31.3 line 2647; §31.10 row 8 | R1: named Teacher invite, scoped 90-day grant, audit, immediate revoke; exact field scope/consent policy remains OPEN-OWNER. |
| FR-PL-08 | §31.3 line 2648 | R1: allowed-field display and immediate revoke; schema, tokens/jobs/cache behavior backend-owned. |
| FR-PL-09 | §31.4 line 2649 | Out of Parent scope: Teacher lesson authoring form. |
| FR-PL-10 | §31.4 line 2650 | Out of Parent scope: Teacher parser/filter. |
| FR-PL-11 | §31.4 line 2651 | Out of Parent scope: Teacher preview/correction/confirmation. |
| FR-PL-12 | §31.4 line 2652 | Out of Parent scope: Teacher/authorized publisher AI draft review. |
| FR-PL-13 | §31.2 line 2653 | R2/R3: display validated lesson/activity fields and optional script direction without mutating source. |
| FR-PL-14 | §31.4 line 2654 | Out of Parent scope: Teacher/Platform visual or slide authoring; Parent consumes only published authorized assets. |
| FR-PL-15 | §31.5 line 2655 | R3: optional guide creates no job when skipped; guide port absent. |
| FR-PL-16 | §31.5 line 2656 | R2/R3/R4: mandatory photo/order, one activity, and post-video behavior. |
| FR-PL-17 | §31.5 line 2657; §31.10 row 5 | R3: optional lesson direction and exact script reconfirm; defaults/override limits stay OPEN-OWNER. |
| FR-PL-18 | §31.5 line 2658 | R3/R4: child-specific run/video; no cross-child reuse; video route absent. |
| FR-PL-19 | §31.5 line 2659 | R3: mismatch/correction before re-suggest; no silent subject change. |
| FR-PL-20 | §31.5 line 2660 | Out of Parent scope: Teacher occurrence child selection; Parent uses its own profile-scoped flow. |
| FR-PL-21 | §31.6 line 2661; §31.10 row 3 | R4: lesson deliveries for 30 days from first delivery/open; run history uses separate lifecycle semantics. |
| FR-PL-22 | §31.6 line 2662 | R4: permitted lesson-content download and scoped feedback only; no chat, completion toggle, or drawing/image attachment. |
| FR-PL-23 | §31.3 line 2663 | R2: Parent-group and named lesson audiences/invitations; only accepted active membership grants access. |
| FR-PL-24 | §31.7 line 2664; §31.10 row 2 | R4: server-confirmed Parent quota only; Q193 payer/purchase/allocation/exhaustion remain OPEN-OWNER and no purchase is shown. |
| FR-PL-25 | §31.8 line 2665; §31.10 rows 1/16 | R1/R3: versioned month-age bands, no new run after legacy age cutoff, old draft read/delete; migration/edit rules remain technical/open. |

### Non-functional requirements

| ID | Rev67 section/line | Owner checkpoint or explicit deferral |
| --- | --- | --- |
| NFR-01 | §9 line 625 | R0–R4: preserve inward ports/adapters architecture. |
| NFR-02 | §9 line 626; NFR-34 line 2706 | R1–R4: deny-by-default scoped UI; server enforcement is unproven where FAKE_PORT. |
| NFR-03 | §9 line 627 | R0–R4: synthetic fixtures only; no child media/PII or diagnostic payload in UI. |
| NFR-04 | §9 line 628 | R1: Parent and Teacher owner separation. |
| NFR-05 | §9 line 629 | R2/R4: single-profile/active-run states; database constraints and saga remain backend-only. |
| NFR-06 | §9 line 630 | R3/R4: revision/hash stale protection and idempotent command states. |
| NFR-07 | §9 line 631 | Deferred to backend/operations: local Compose storage recovery is not a mobile UI acceptance claim. |
| NFR-08 | §9 line 632 | Deferred to backend/operations: latency and load benchmark are not proven by client work. |
| NFR-09 | §9 line 633 | R3: input size/type/error UI; media validation/AV and lineage remain backend gates. |
| NFR-10 | §9 line 634 | R4: private playback authorization state; route/token remains FAKE_PORT. |
| NFR-11 | §9 line 635 | Deferred to backend: redacted structured logging/trace/metrics. Client hides diagnostics. |
| NFR-12 | §9 line 636 | R3/R4: honor Retry-After and avoid request loops. |
| NFR-13 | §9 line 637 | R0–R4: understandable adult Vietnamese copy without skipped required review. |
| NFR-14 | §9 line 638 | R0–R4: typed states and thin adapters. |
| NFR-15 | §9 line 639 | R1: Firebase Authentication only; no secret/provider endpoints in client. |
| NFR-16 | §9 line 640 | R1 UI boundary; schema migration/backfill is deferred. Gender requires SRS+BE change and no migration here. |
| NFR-17 | §9 line 641 | R3/R4: typed provider unavailable/failure and no fallback model. |
| NFR-18 | §9 line 642 | Deferred to backend/operations: production backup policy and safety. |
| NFR-19 | §9 line 643 | R4: technical/safety-ready gate and adult unsuitable mark; evaluation effectiveness remains backend-only. |
| NFR-20 | §9 line 644 | R0–R4: semantic labels, text errors, permission alternatives, scaling/accessibility. |
| NFR-21 | §9 line 645 | R0–R4: adult labels, validation and safe errors in Vietnamese. |
| NFR-22 | §9 line 646 | Deferred to backend/operations: synthetic load/scheduler benchmark. |
| NFR-23 | §9 line 647 | R3/R4 state gates; server safety policy implementation remains deferred. |
| NFR-24 | §9 line 648 | Deferred to security/backend; client must not bypass auth, storage or provider boundaries. |
| NFR-25 | §9 line 649 | R4: represent cost/quota rejection; reservation/circuit breaker is backend-owned. |
| NFR-26 | §9 line 650 | R4: inbox canonical; push/email best-effort and deduped. |
| NFR-27 | §9 line 651 | Deferred to backend/operations: readiness, SLO, RPO/RTO measurement. |
| NFR-28 | §9 line 652 | R3/R4 UI limits and typed cap states; capacity calculation/benchmark is backend-owned. |
| NFR-29 | §9 line 653 | R0–R4: Android WCAG2ICT/platform review; no certification claim. |
| NFR-30 | §9 line 654 | R0–R4: Android API 29 floor and pinned SDK compatibility checked by owner. |
| NFR-31 | §9 line 655 | R4 deletion UI; real-data retention/backup deletion policy remains unresolved/backend-owned. |
| NFR-32 | §9 line 656 | R3: photo 20 MiB/audio 20 MB and 2 minutes; resumable chunk backend contract remains absent. |
| NFR-33 | §9 line 657 | Out of Parent scope: Teacher Web presentation/viewport/keyboard requirements. |
| NFR-34 | §31.9 line 2706 | R1/R2/R4: grants, tenant boundary and revoke UI; all server token/cache/job enforcement remains BE-owned. |
| NFR-35 | §31.9 line 2707 | Out of Parent scope: Teacher source-document filtering and provenance. |
| NFR-36 | §31.9 line 2708 | R1/R2/R4: cross-role profile grants and school-scoped feedback. |
| NFR-37 | §31.9 line 2709 | R2/R3: exact source/version references; immutable asset/lesson lineage is backend-owned. |
| NFR-38 | §31.9 line 2710 | R0–R4: adult-guided Vietnamese content for ages 3–10; child-operated surfaces remain out of scope. |

### Business-rule requirements

| ID | Rev67 section/line | Owner checkpoint or explicit deferral |
| --- | --- | --- |
| BR-01 | §8 lines 244/2479 | R3: one selected child per run. |
| BR-02 | §8 lines 245/2480 | R2/R4: active-run prevention and lifecycle terminal state; lock implementation backend-only. |
| BR-03 | §8 lines 246/2481 | R1: separate account/profile scope and invited grant. |
| BR-04 | §8 lines 247/2482 | Out of Parent scope: school capacity slots. |
| BR-05 | §8 lines 248/2483 | Out of Parent scope: School Manager class assignment. |
| BR-06 | §8 lines 249/2484 | Out of Parent scope: Teacher reassignment workflow. |
| BR-07 | §8 lines 250/2485 | Out of Parent scope: Teacher profile authoring. |
| BR-08 | §8 lines 251/2486 | R3: catalog-first main activity candidates; no raw media/identity. |
| BR-09 | §8 lines 252/2487 | R2: topic/lesson optional; exact authorized lesson version. |
| BR-10 | §8 lines 253/2488 | Out of Parent scope: Teacher occurrence sample slot. |
| BR-11 | §8 lines 254/2489 | R4: one initial accepted full request plus at most two quality regenerations; accounting and script reconfirmation as WR-AC32. |
| BR-12 | §8 lines 255/2490 | Out of Parent scope: Teacher sample uniqueness. |
| BR-13 | §8 lines 256/2491 | R3: at most three rewrites after initial story. |
| BR-14 | §8 lines 257/2492 | R3/R4: every story revision re-reviewed and confirmed. |
| BR-15 | §8 lines 258/2493 | R3: transcript, subject, lesson/context, activity and script confirmations. |
| BR-16 | §8 lines 259/2494 | R4: validated video display and immediate hiding of rejected output. |
| BR-17 | §8 lines 260/2495 | R4 state only; automatic technical scene retry is backend-owned and consumes no user request. |
| BR-18 | §8 lines 261/2496 | R1/R3: age bands and no name to models; gender owner request adds no model data. |
| BR-19 | §8 lines 262/2497 | R1/R3: revisioned personalization with distinct context sources. |
| BR-20 | §8 lines 263/2498 | R1/R3: support needs limited and excluded from AI by default. |
| BR-21 | §8 lines 264/2499 | R3: adult-confirmed minimal per-run snapshot. |
| BR-22 | §8 lines 265/2500 | Out of Parent scope: Teacher lesson-document upload. |
| BR-23 | §8 lines 266/2501 | R3: audio maximum two minutes/20 MB and transcript confirmation. |
| BR-24 | §8 lines 267/2502 | R4: display only validated format/duration/media state; backend output contract absent. |
| BR-25 | §8 lines 268/2503 | R4: no video download/export/public URL. |
| BR-26 | §8 lines 269/2504 | R4: completed-run delete/cancel lifecycle, no quota refund and pending purge. |
| BR-27 | §8 lines 270/2505 | R0–R4: synthetic-only data. |
| BR-28 | §8 lines 271/2506 | Out of Parent scope: payment adapters. |
| BR-29 | §8 lines 272/2507 | Out of Parent scope: purchased school capacity activation/proration. |
| BR-30 | §8 lines 273/2508 | Out of Parent scope: organization auto-renew/refund policy. |
| BR-31 | §8 lines 274/2509 | Out of Parent scope: school subscription grace/capacity restriction. |
| BR-32 | §8 lines 275/2510 | Out of Parent scope: School Manager capacity reduction. |
| BR-33 | §8 lines 276/2511 | Out of Parent scope: billing-admin notices; Parent run reminders are BR-39/R4. |
| BR-34 | §8 lines 277/2512 | R0–R4 client boundary; metadata-only audit is backend-owned and not claimed. |
| BR-35 | §8 lines 278/2513 | R1: profile deletion and immediate scope revoke; purge remains FAKE_PORT. |
| BR-36 | §8 lines 279/2514 | R3/R4: safe script/video state gates; actual server classifier/policy remains deferred. |
| BR-37 | §8 lines 280/2515 | Out of Parent scope: Teacher presentation confirmation for occurrence. |
| BR-38 | §8 lines 281/2516 | R4: server-derived Parent quota; no mutable/fabricated balance or purchase. |
| BR-39 | §8 lines 282/2517 | R4: +144h deduped inbox, best-effort delivery, +168h closeout. |
| BR-40 | §8 lines 283/2518 | R4: cancel/delete pending; used quota/sample claim is preserved as applicable. |
| BR-41 | §8 lines 284/2519 | Out of Parent scope: School Manager emergency force-close. |
| BR-42 | §8 lines 285/2520 | R2/R3: optional guide/topic/lesson and required photo/subject review order. |
| BR-43 | §8 lines 286/2521 | Out of Parent scope: Teacher presentation/deck control. |
| BR-44 | §8 lines 287/2522 | R3: guide cap/privacy; compute cap is backend-owned. |
| BR-45 | §8 lines 288/2523 | R3/R4 client pipeline gates; provider generation pipeline remains absent. |
| BR-46 | §8 lines 289/2524 | R3: optional progressive catalog-first SVG guide; no child input; skip/failure nonblocking. |
| BR-47 | §31.10 crosswalk lines 2526/2671 | R0–R4: keep Parent/Teacher baseline boundary while adding lesson platform; platform backend remains separate. |
| BR-48 | §31.10 crosswalk lines 2527/2672 | R1: named scoped revocable profile grants and consent. |
| BR-49 | §31.10 crosswalk lines 2528/2673 | R1/R2/R4: tenant-safe profile, lesson and feedback views. |
| BR-50 | §31.10 crosswalk lines 2529/2674 | R2: lesson version/personal-copy source lineage; no published source mutation. |
| BR-51 | §31.10 crosswalk lines 2530/2675 | R2 consumer view only; publication approval/moderation commands excluded. |
| BR-52 | §31.10 crosswalk lines 2531/2676 | Out of Parent scope: Teacher upload-field filtering. |
| BR-53 | §31.10 crosswalk lines 2532/2677 | Out of Parent scope: AI lesson draft review/publish. |
| BR-54 | §31.10 crosswalk lines 2533/2678 | R3: explicit adult guide request; skip creates no job. |
| BR-55 | §31.10 crosswalk lines 2534/2679 | R3/R4: one main activity and exact post-video pin behavior. |
| BR-56 | §31.10 crosswalk lines 2535/2680 | R3/R4: child-specific video and confirmed subject mismatch; script defaults remain open. |
| BR-57 | §31.10 crosswalk lines 2536/2681 | R1/R3: age-band/version admission and legacy profile/draft policy. |
| BR-58 | §31.10 crosswalk lines 2537/2682 | R2: group/named lesson invitation and revocable access. |
| BR-59 | §31.10 crosswalk lines 2538/2683 | R4: school-scoped lesson feedback, no chat/media. |
| BR-60 | §31.10 crosswalk lines 2539/2684 | R4: Parent quota scope; buyer/allocator/payment/exhaustion/top-up terms remain OPEN-OWNER. |

### Explicit out-of-scope and deferred boundary

No Parent action is planned for FR-PL-09/10/11/12/14/20; NFR-33/35; or BR-04/05/06/07/10/12/22/28–33/37/41/43/52/53, because these are Teacher, School Manager, Platform Admin, organization billing, authoring, moderation, or occurrence-sample functions. Parent consumption of their approved outputs remains in R2/R3/R4 as mapped above. NFR-07/08/11/18/22/24/27, backend parts of FR-C-03/09/10/11/12, all absent API V2/service operations, and server portions of every mapped NFR/BR are deferred to BE/operations; the client uses typed unavailable states and synthetic tests only. These deferrals do not mark the SRS requirements satisfied.

### Related Parent-facing AI and billing capability requirements

| SRS IDs | Rev67 line range | Parent checkpoint and boundary |
| --- | --- | --- |
| FR-AI-01–03 | 566–568 | R3/R4 client gates for typed jobs, schema-valid/stale responses and source lineage; all absent AI routes remain FAKE_PORT. |
| FR-AI-04–10 | 569–575 | R4 storyboard/video/playback/no-export states; generation and short-lived playback authorization are unavailable routes. |
| FR-AI-11 | 576 | Backend observability deferred; the app never displays raw diagnostic content. |
| FR-AI-12–13 | 577–578 | R3/R4 safety and generation states; server policy and provider pipeline are not implemented or proven by UI. |
| FR-AI-14–15 | 579–580 | R2/R3 consume only approved/versioned guide artifacts; Parent guide stays optional/nonblocking and its catalog/render/job routes are FAKE_PORT. Teacher authoring remains out of Parent scope. |
| FR-B-01–08 | 586–593 | Out of Parent scope: organization subscription pricing, payment, capacity lifecycle and billing-admin notification operations. |
| FR-B-09–14 | 594–599 | R4 inbox/quota boundary: canonical inbox and best-effort delivery; Parent quota summary/admission follows server scope; Q193 purchase stays OPEN-OWNER. All related Parent routes absent from handoff are FAKE_PORT. |
| FR-T-01–22 | 539–560 | Teacher-only workflow and presentation actions are out of Parent scope; Parent may consume only published, currently authorized lesson/guide outputs covered by R2/R3. |
| FR-O-01–10 | 605–614 | Platform operations/admin actions are out of Parent scope; Parent only sees safe lifecycle outcomes through R1/R4 states. |




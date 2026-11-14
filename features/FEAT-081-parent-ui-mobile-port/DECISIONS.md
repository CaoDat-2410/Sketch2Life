# FEAT-081 — Owner decisions

Owner: Person 2 (AnhKhoaa157).
Recorded: 2026-11-12.

| ID | Decision | Basis |
|---|---|---|
| D-001 | Target apps/ui-mobile, the Expo SDK 52 / React Native 0.76.9 / React 18.3.1 Parent app on dev. The web sample UI in sibling worktree .worktrees/ui, branch feature/fe-ui-full-remediation at commit 30c94342, mainly apps/parent-ui, is read-only reference material. | direct owner instruction 2026-11-12 |
| D-002 | CaoDat built the existing ui-mobile base. The owner will edit the Parent UI from here on; no per-file ownership reservation is required. Merge risk remains because CaoDat may later edit the same files on dev and must be stated in the plan. | direct owner instruction 2026-11-12 |
| D-003 | Use feature ID FEAT-081 and folder features/FEAT-081-parent-ui-mobile-port. A read-only check found no FEAT-081 folder on origin/dev, feature/fe-ui-full-remediation, or origin/codex/fe-ui-web-remediation, and no local or remote-tracking branch name containing FEAT-081. | direct owner instruction 2026-11-12 |
| D-004 | Use existing Vitest 3.2.4 through the package script test: vitest run tests && node scripts/validate-ui-copy.mjs. Do not add Jest or change package.json or pnpm-lock.yaml in this feature. | direct owner instruction 2026-11-12 |
| D-005 | Wave 1 is P01/P02 (home and lesson gallery) using the alternative allowlist in PORT_ORDER_AND_ALLOWLIST_DRAFT_R2.md. Do not edit shared components/ui.tsx. | direct owner instruction 2026-11-12 |
| D-006 | For the later, separately approved move to apps/mobile (plain React Native 0.87 / React 19.2), new screens use only React Native View, Text, Pressable, StyleSheet, and Animated primitives. Media picking, audio recording, and browser opening go through application ports, with Expo-only code in infrastructure adapters. Icons use react-native-svg components, not @expo/vector-icons. Add no Expo gradient or other Expo-only library in new screens and no new Expo-only dependency. Follow AGENTS.md dependency direction: interfaces/adapters -> application -> domain; infrastructure implements ports. | direct owner instruction 2026-11-12 |
| D-007 | Waves 2-5 are outline only and need separate approvals. Hold P08c, P14, and P15 until a product requirement is recorded. Do not copy any sample image, avatar, icon, or font until it is generated under assets/generated with provenance and visual approval, then passes the repository asset gate before application. | direct owner instruction 2026-11-12 |
| D-008 | Out of scope: the Android applicationId / validate_skeleton CI fix, the move to apps/mobile, and wiring the client to new backend routes. Those routes exist only on a private, unpushed integration branch. Wave 1 uses synthetic fixtures only and makes no API change. | direct owner instruction 2026-11-12 |

These decisions authorize this feature's recorded Wave 1 approval only. Implementation has not launched; later waves and the apps/mobile migration remain separate gates.
## D-009 — FEAT-081 implementation location

- Decision: Keep apps/ui-mobile as the implementation location for FEAT-081 Wave 1 and for any separately approved FEAT-081 Parent UI follow-on wave. Do not move or duplicate those FEAT-081 screens into apps/mobile.
- Scope and reconciliation: This is a feature-scoped implementation-location exception. It does not amend the canonical FEAT-063 v2.7-draft Rev60 SRS, change its broader apps/mobile Parent product target, or globally supersede ADR-0020 or ADR-0021. The older D-006/D-008 future-move wording is superseded only for FEAT-081 and its separately approved follow-on UI waves. Any product-wide or production-target change requires a separate owner decision and SRS/ADR revision.
- Reference: ADR-0023-feat081-mobile-ui-target.md.
- Basis: direct owner instruction 2026-11-12.
- Exact DECISIONS.md SHA-256 immediately before appending D-009: 35CC570FABE7144ECB8B9B3AE098E484A4E432D7FEDE5448FD6FACFCC3997CB9.
## D-010 - FEAT-081 Wave 2 API wiring plan approval (not launch)

- Decision: Approve Wave 2 API wiring for FEAT-081 under `plan/PLAN_REVISION_3.md`, an exact copy of the owner-pinned R2 draft. Wave 2 is APPROVED / NOT LAUNCHED. The plan's `DRAFT` header is superseded by Addendum 4; no implementation is launched by this decision.
- Owner product decisions:
  1. Tomorrow's StoryRun requires a lesson preset/version pin.
  2. `drawing-understandings` stays unchanged and receives no added `Idempotency-Key`.
  3. Consent and data-authorization calls stay removed; no consent-return path is designed here.
  4. `activity-suggestions` is not mounted; use the existing Activity screen skip action.
  5. Use synthetic profiles; restore existing profiles through the profile list route.
  6. `OWNER_MODAL_CALL_APPROVED=NO`; the owner-run flow stops before `drawing-understandings`.
- Launch gates: 2A and 2B are separate. 2A requires a separate explicit owner launch instruction. 2B requires its own instruction after 2A passes.
- S1a-P2 basis: The pending, not-yet-ACCEPTED list/delete/Parent-role-gate contract is accepted as the working basis for 2A and may change slightly. Any change after S1a-P2 acceptance is handled by a new addendum.
- Wave 2 baseline: Owner-run results at 2026-11-12 23:56 and 2026-11-13 00:15 on bytes identical to commit `3c75b10d` are the baselines: `pnpm run test` reported 4 files / 29 tests passed and `UI_COPY_AND_RECOVERY_VALID`; typecheck had no diagnostics; `validate_harness`, `validate_repository_security`, `validate_architecture`, and `git diff --check` all exited 0. These results consume the baseline invocation of each command in the approved ceilings.
- Command ceilings: `pnpm run test` 3 total; `pnpm run typecheck` 3 total; each of `validate_harness`, `validate_repository_security`, `validate_architecture`, and `git diff --check` 2 total. The baseline invocation is consumed.
- Pinned plan: `plan/PLAN_REVISION_3.md`, 34,224 bytes, SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`.
- Previous DECISIONS prefix pin: 3,950 bytes, SHA-256 `3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805`.
- Post-append DECISIONS.md byte length and SHA-256 are recorded in Addendum 4, status/context, and the command ledger after this append.
- Basis: direct owner approval dated 2026-11-13.

## D-011 - FEAT-081 Wave 3 native P03-P06 flow and boundaries (plan approval; not launch)

1. P03 step source: parse only explicit separators in drawing_steps_text; never invent step boundaries; a version-pinned structured steps array is a later BE question.
   Reason: Keeps each displayed instruction traceable to the selected lesson version and avoids fabricated steps.
2. Missing guide: approved optional empty state with a continue-to-capture action.
   Reason: A missing optional guide must not block the parent from continuing.
3. Flow order: topic and idea, then P03 guide, then V1 create and context confirmation, then capture after context confirmation.
   Reason: Preserves the committed V1 context-confirmation gate before capture.
4. Audio idea: the typed adult idea stays required until the BE provides a pre-run transcription path.
   Reason: The current V1 create path needs an adult idea before the run exists.
5. Modal: OWNER_MODAL_CALL_APPROVED=NO for all of Wave 3. Code and fake-data tests only. Stop before drawing-understandings and story-revisions calls. Runtime acceptance of P04-P06 real AI steps is deferred until the AI fix lands and a bounded Modal approval exists.
   Reason: Prevents an unapproved provider call and avoids claiming unverified real-AI acceptance.
6. P06 boundary: stop before P07 and video. Do not start video admission. The BE lane must confirm the V1 script-confirmation semantics before any launch.
   Reason: Keeps video outside this wave and avoids relying on an unverified endpoint effect.
7. Story V1 fields: if the response lacks the exact revision/hash fields needed to confirm the displayed version, stop and request an additive contract allowlist; never guess.
   Reason: Adult confirmation must apply to the exact displayed script version.
8. Guide illustration (whole-topic sketch): out of Wave 3, kept separate.
   Reason: The whole-topic sketch is not a per-step guide image and is outside the bounded flow port.
9. Ownership: apps/ui-mobile is the owner's UI base, built to follow the flow; the owner will later restyle layout and look. CaoDat changes only the AI side and does not edit mobile. There is no shared-file ownership risk in apps/ui-mobile. Wave 3 ports flow and data behavior only; no visual polish.
   Reason: Keeps Wave 3 limited to native flow/data behavior and avoids visual restyling work.
10. P05 audio/transcription: OUT OF WAVE 3. The typed adult idea remains the only input path; do not edit TranscriptReviewScreen.tsx or the existing audio capture UI.
    Reason: No Parent transcription or transcript-confirmation route was found; exclusion preserves Decision 4 and avoids relying on an unsupported contract.

### Wave 3 no-Modal boundary

OWNER_MODAL_CALL_APPROVED=NO for every Wave 3 activity. This permits code and fake-data tests only. No drawing-understandings or story-revisions call may be made, and real-AI runtime acceptance for P04-P06 remains deferred until the AI fix lands and the owner records bounded Modal approval.

- Basis: direct owner approval from Person 2 dated 2026-11-13.
- Pre-append DECISIONS.md pin: 6,312 bytes / SHA-256 prefix B1D74778.


## D-012 - FEAT-081 Wave 3 V1 story-revision read-model clarification (not a new launch)

- Clarification of D-011 decision 7; this is not a new launch.
- Coordinator code reading, not a runtime result: backend `ParentStoryRunResponseV1` / `_story_response` returns `story_revision_no`, `story_sha256`, `story_status`, `story`, and other run fields inside `story_run` on GET/POST `/v1/story-runs` and POST `/api/parent/v1/ai/story-runs/{run_id}/story-revisions`.
- The frozen mobile `ParentStoryRunV1` declaration in `apps/ui-mobile/src/parent/domain/types.ts` omits those story fields.
- Wave 3 may add a local, runtime-validated read model only in `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts`: `story_revision_no` must be an integer greater than or equal to 1 and `story_sha256` must match `^[0-9a-f]{64}$`. If either value is absent or invalid, confirmation is blocked and no confirmation request is sent.
- `types.ts`, `ParentApi.ts`, `ParentPorts.ts`, `ParentApplicationModule.ts`, and `ParentLearningUseCases.ts` remain frozen H paths and byte-identical; no H path is authorized for edit. Cleanup of declared types is deferred to a later route-wiring task.
- If a runtime response lacks either required story field, stop and request an additive allowlist under D-011 decision 7.
- Basis: direct owner decision from Person 2 dated 2026-11-13.
- Pre-append `DECISIONS.md` pin: 9,467 bytes / SHA-256 prefix `B589A16E`.

## D-013 - FEAT-081 Wave V native Parent UI visual alignment

1. Fidelity: token-level plus per-screen layout and hierarchy parity with the sample for the EXISTING Parent screens. No pixel perfection; the owner will have the look refined later by someone else.
2. Fonts: system fonts only; no font package; the sample font (Be Vietnam Pro) is a later optional decision.
3. Icons: no copied assets and no new dependency; keep the existing native Ionicons where current screens already use icons; use text and native shapes for any missing visual role.
4. Dark mode, landscape and tablet support: out of scope; 6.1-inch portrait only.
5. Checkpoints V0 to V4 exactly as proposed; each has its own launch instruction, its own test run set, its own evidence report and its own commit. ui.tsx is the only H path that opens (to E, in V0). All other H paths, package.json and pnpm-lock.yaml stay frozen.
6. V4 restyles the existing history, quota, notifications and sharing screens as presentation only. Preserve the current route availability and every state EXACTLY as the code is today; add or remove no route, no filter, no detail view and no behavior. (This replaces the earlier "routes stay unavailable" wording: the screens are mounted today and the backend routes behind them simply do not exist yet; that stays as is.)
7. Copy: no copy changes, except text that layout strictly requires with the owner's approval. Note that apps/ui-mobile/scripts/validate-ui-copy.mjs does not scan the Parent screens; no-copy-change is therefore verified by a before/after string comparison of every edited file at acceptance.
8. Visual acceptance is owner-run on the emulator per checkpoint; screenshots are not committed to the repository (the evidence report records references and the owner's result only).
9. No behavior change: flows, state machines, routes, contracts and the existing 59 tests stay unchanged.
10. (Plan question 9) Approved: the listed 22 current native screens plus shared ui.tsx and ParentBottomBar.tsx, and nothing else. P07-P09, P08c, P14 and P15 stay excluded.
11. (Plan question 10) Confirmed: system fonts, no copied sample art or assets, and no new dependency.

No-behavior-change boundary: Only presentation changes are authorized. Do not change flows, state machines, routes, route availability, contracts, existing screen behavior or tests. Do not add filters, detail views, dependencies, copied assets, routes or other behavior. Any text strictly required by layout needs the owner's approval and is checked by before/after string comparison.

- Basis: direct owner decision from Person 2 dated 2026-11-13.
- Pre-append DECISIONS.md pin: 10914 bytes / SHA-256 prefix 5AD97606.

## D-014 - FEAT-081 Wave V cancellation and Wave R Plan Revision 7 approval (plan only; not launch)

- Owner: Person 2.
- Date: 2026-11-13.
- Owner disposition: ACCEPT. The owner accepts all recommended defaults in tmp/fe081-waveR2/WAVER_OWNER_QUESTIONS_R67.md and approves Plan Revision 7 as pinned below. This approves the plan only; Wave R is NOT LAUNCHED.
- Approved plan: tmp/fe081-waveR2/WAVER_PLAN_DRAFT_R7.md, 70,512 bytes / SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9. The byte-identical approved copy is features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md.
- Checkpoint launch instruction: NONE. A separate explicit owner launch instruction is required for each of R0, R1, R2, R3 and R4.
- Pre-append DECISIONS.md pin: 13,613 bytes / SHA-256 4FC79E32E838C5A07E01CA601F28AED35B437334FE4D73493E84BB5DF4F94FB3. The post-append pin is recorded in Addendum 12 after this append.

### Supersession and authority

1. Wave V presentation-only alignment is cancelled before code change. D-013, Addendum 11, and features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_5.md remain unchanged historical records. This decision supersedes only their prospective Wave V execution direction. The Plan Revision 5 pin remains 49,834 bytes / SHA-256 73A706C2A241AC2CF4F8A48946672F1B9549FE44023DEA8FBC4A12E0E089FE67.
2. Wave R Plan Revision 6 was withdrawn before launch. Its copies remain under tmp/fe081-waveR/withdrawn/ and no checkpoint launched under Revision 6.
3. The owner-approved Wave R planning exercise used the owner-supplied, unsigned v2.7-draft Rev67 at tmp/fe081-waveR2/srs_new/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_Rev67_owner_supplied.md, 634,291 bytes / SHA-256 B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996. This records the source used for this plan; it does not update the repository SRS or adopt Rev67 as the repository's current canonical working SRS. The repository copy remains Rev60, docs/context/SRS_AUTHORITY.md remains unchanged, and reconciling/updating those sources is an open governance item. Rev67 remains unsigned.
4. Wave R's goal is to rebuild the adult-operated Parent mobile experience around the owner-supplied Rev67 flows and the owner's restrained-crayon Variant A direction, with typed unavailable production capabilities for routes absent from the BE handoff and synthetic test data only. No implementation is approved by this decision.

### Visual direction and concept decisions

- Primary direction: concept VARIANT A, restrained crayon, chosen by the owner without blending in Variant B. Variant B is comparison only. The concept is at tmp/fe081-waveR2/concept/index.html and was reviewed by the owner. This is not OI-17 design sign-off.
- Navigation has four tabs, in order: Trang chủ, Bài giảng, Bắt đầu, Hồ sơ.
- The optional drawing guide uses 4 to 8 steps supplied by the engine output. Guide failure or unavailability remains nonblocking to the mandatory photo.
- If camera access is denied, gallery remains equally visible and usable.
- A subject mismatch offers both changing the topic and one retake. The exact lesson pin remains unchanged.
- Main-activity choice is one-of-N. Show exactly three drafts only after a no-suitable-catalog result and only when the required gates are approved. Exclude every shown or rejected entry from replacements.
- Before script confirmation, the adult sees the readable story, revision id, and full lowercase hash. Every new story revision requires a fresh explicit confirmation of that exact revision.
- After video, a pinned lesson shows the activities from that exact pinned version and marks the chosen main activity. With no lesson pin, show only the run-pinned main activity.
- Completion and cancel have separate explicit confirmations. Show accepted or closed only from server-confirmed state.
- Quota shows only the server-confirmed summary. Do not show a purchase action while Q193 remains open and until the owner separately approves it.
- Error recovery follows SRS §21.6 grouped by user action. Do not show provider, SQL, or stack diagnostics. Check the same job before any retry. The remaining recovery groups receive dedicated screens ordered by ambiguity, within the exact Plan Revision 7 E-file boundary; if a new UI file is needed, stop and obtain a revised plan.
- Vietnamese copy is placeholder text until editorial and legal review.
- A Parent-group invitation grants no access before acceptance. After acceptance, the server validates current membership before access is granted.

### Owner-requested child-gender field

This is an OWNER REQUEST, not a requirement in Rev67 or the BE contract. The profile creation and editing forms may show an optional field, empty by default, with boy, girl, and prefer not to say. The consent basis must be stated in a future SRS and legal review; no consent policy is decided here. Do not use this field for story generation or as model input without separate approval; it is excluded from API and model payloads now. Do not persist it or claim it is saved until the SRS update and BE profile schema, migration, and revision-hash change are approved. Until then, visibly identify the value as an unsaved local draft.

### Owner answers to Plan Revision 7 questions

The owner accepts all recommended defaults for questions 1–35 in tmp/fe081-waveR2/WAVER_OWNER_QUESTIONS_R67.md, with these recorded dispositions:

1. Restrained paper-like, pastel crayon treatment, sparse stickers, adult-first legibility; use Variant A only as the primary direction.
2. OI-17 sign-off is deferred until the owner reviews R0 emulator screenshots.
3. Use system fonts; do not add expo-font.
4. Use code-only SVG or native art and existing icons; no copied or commissioned art.
5. Keep the surfaces adult-operated; child-facing flows are out of scope.
6. Use calm, plain Vietnamese copy as placeholder text pending editorial and legal review.
7. Keep emulator screenshots local, synthetic, and free of account identifiers and child data.
8. Use the five sequential checkpoints R0–R4 in the plan.
9. Require a separate explicit launch instruction for each checkpoint.
10. Use typed unavailable ports or states in the normal app; fakes are test-only; never show fake success.
11. Block story generation when required activity preview is unavailable; preserve inputs, permit only contract-approved retry, and provide a safe exit. Do not invent a manual candidate.
12. On mismatch, offer topic change or exactly one retake; keep the lesson pin unchanged.
13. Use an approved or licensed SVG catalog first; a structured draft is allowed only if all quality, privacy, and API gates are approved.
14. Keep the guide optional before photo; require the photo before StoryRun creation or VLM. Leave exact server create timing open pending API V2.
15. Do not wire API V2-dependent behavior to real routes before API V2, DTR and DDL, quality, and performance gates are approved.
16. Preserve Rev67's per-row RESOLVED, PARTIAL, OPEN-OWNER, and OPEN-TECHNICAL statuses; do not reopen resolved rows by inference.
17. Keep Q192 and its related §31.10 row OPEN-OWNER.
18. Keep Q193 OPEN-OWNER and purchase unavailable until separately decided and approved.
19. Preserve the resolved 30-day lesson-history rule; schema mapping remains technical.
20. With no lesson pin, select one main activity before story and show only that run-pinned main after video, with no catalog query or extra list.
21. With a lesson pin, show all activities from the exact pinned version after video and mark the selected main; never substitute a version.
22. If a required activity result is unavailable, block story, retain context, allow safe exit, and do not provide a manual fake result.
23. Keep the guide optional and nonblocking to mandatory photo.
24. Leave the remaining owner-dependent §31.10 portions open; do not decide them for this plan.
25. Preserve Rev67's supersession distinctions; command, receipt, reconciliation, and purge details remain technical.
26. Show only server-confirmed quota state; do not guess balance, price, or percentage and do not expose purchase while Q193 is open.
27. Send no profile, age, identity, photo, audio, or artwork input to drawing-guide operations.
28. Do not show a draft rejected by or lacking its quality gate as a candidate; retain a blocking unavailable or no-fit state and do not start story.
29. Do not display a VLM confidence percentage unless its meaning is defined by the SRS and verified by the backend.
30. Use synthetic data only; no real child content in tests or screenshots.
31. Require a separate launch after the previous checkpoint's evidence and pins are reviewed.
32. Keep OWNER_MODAL_CALL_APPROVED=NO; no Modal or provider call is authorized.
33. Open only the exact 18 former-H paths listed in Plan Revision 7 §12 as E; all other H paths remain frozen.
34. Plan approval launches nothing; each R0–R4 checkpoint needs its own explicit launch instruction.
35. Keep child gender an optional, empty-by-default form draft with boy, girl, or prefer not to say; state the consent basis in a future review, exclude it from story generation, model inputs, and API payloads, and do not persist or claim save pending the SRS and BE schema, migration, and revision-hash approvals.

### Former-H paths opened as E

Only these 18 paths are reclassified from H to E, with the Plan Revision 7 §12 rationales:

- apps/ui-mobile/src/parent/application/ParentApplicationError.ts — Map SRS recovery errors to safe user messages without raw diagnostics.
- apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts — Compose typed unavailable capabilities; keep test fakes out of product success paths.
- apps/ui-mobile/src/parent/application/ports/ParentPorts.ts — Define typed operation/result boundaries while preserving listed route contracts.
- apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts — Enforce activity choice and avoid unsupported activity success paths.
- apps/ui-mobile/src/parent/application/use-cases/ParentPlatformUseCases.ts — Represent absent lifecycle/history/quota operations as unavailable.
- apps/ui-mobile/src/parent/domain/types.ts — Add explicit unavailable/pending/reconciliation/player states without weakening contracts.
- apps/ui-mobile/src/parent/domain/storyDraft.ts — Preserve exact story revision and confirmation rules.
- apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts — Prevent calls to absent routes; preserve only handoff-listed operations.
- apps/ui-mobile/src/parent/ParentModule.ts — Compose normal app with unavailable adapters and no fake success.
- apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx — Expose/reorder screens as checkpoints launch.
- apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts — Add pure gates and recovery for exact revisions and new state order.
- apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts — Enforce photo, confirmation, selection and safe unknown-state gates.
- apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts — Remove false success for unlisted lifecycle/history/quota calls.
- apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts — Represent exhaustive flow states/transitions.
- apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts — Distinguish empty from unavailable; avoid fabricated recommendation states.
- apps/ui-mobile/tests/parentFlowV1.test.ts — Permit synthetic flow/recovery tests if R0 test file is insufficient.
- apps/ui-mobile/tests/parentApiI2Contract.test.ts — Assert absent routes make no requests and listed route contracts stay unchanged.
- apps/ui-mobile/src/parent/application/use-cases/ParentLessonUseCases.ts — Guard lesson operations against routes absent from the BE handoff and represent them as typed unavailable.

All other H paths remain frozen. The package manifest at apps/ui-mobile/package.json and the repository package lockfile remain frozen at their exact H pins in Plan Revision 7. OWNER_MODAL_CALL_APPROVED=NO. This decision approves Plan Revision 7 only; no checkpoint is launched, and no implementation, test, staging, commit, push, or provider or Modal call is authorized.

## D-015 - FEAT-081 Wave R backend route-boundary clarification

- Owner: Person 2.
- Date: 2026-11-13.
- Authority: Direct owner clarification in tmp/fe081-waveR2/GOAL_R1_R4_INSTRUCTIONS.md, 11,719 bytes / SHA-256 A79675D14ED07CED9F41BCC12AF10C72F4833033D6C452485CF7CF37C19CA180.
- Status: Plan Revision 7 remains APPROVED. The owner launched checkpoints R1, R2, R3 and R4 in this run. This clarification does not change the plan, scope, allowlist, pins, command ceilings or checkpoint sequence.
- Route boundary: The BE handoff lists backend operations coarsely. For all of Wave R, the table below is the authoritative REAL route set and nothing else.

### REAL route set

- Authentication:
  - POST /api/auth/v1/registrations.
  - GET /api/auth/v1/me.
- Profiles, prefix /v1/parent/profiles:
  - GET /v1/parent/profiles with cursor: runtime-verified.
  - POST /v1/parent/profiles: runtime-verified.
  - GET /v1/parent/profiles/{profile_id}: NOT VERIFIED BY RUNTIME; code-reading only, module backend.src.sketch2life.interfaces.http.routers.parent_profiles, function read_parent_profile.
  - PATCH /v1/parent/profiles/{profile_id}: runtime-verified.
  - DELETE /v1/parent/profiles/{profile_id}: runtime-verified.
- StoryRuns, prefix /v1/story-runs:
  - POST /v1/story-runs.
  - GET /v1/story-runs/active/current.
  - GET /v1/story-runs/{run_id}.
  - POST /v1/story-runs/{run_id}/context-confirmation.
  - POST /v1/story-runs/{run_id}/subject-confirmation.
  - POST /v1/story-runs/{run_id}/script-confirmation.
- Parent AI, prefix /api/parent/v1/ai:
  - POST /api/parent/v1/ai/sketch-guides.
  - POST /api/parent/v1/ai/drawing-understandings.
  - POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions.
  - These routes exist. The owner reports that the local backend returns 503 MODAL_AI_NOT_ENABLED when its AI provider is disabled. The UI must show truthful unavailability and never claim success. This is not successful provider verification. Automation makes no Modal or provider call.
- Lesson library, prefix /api/lesson-library/v1:
  - GET /api/lesson-library/v1/me/lessons.
  - GET /api/lesson-library/v1/me/lessons/{lesson_id}.
  - GET /api/lesson-library/v1/me/lessons/{lesson_id}/download.
  - GET /api/lesson-library/v1/me/lesson-invitations.
  - POST /api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept.
  - POST /api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline.
  - GET /api/lesson-library/v1/me/parent-group-invitations.
  - POST /api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept.

Only profile list, create, PATCH and DELETE are runtime-verified in this clarification. GET-by-ID is code-reading only. Every other listed route is NOT VERIFIED BY RUNTIME unless a specific result is stated above; route presence or code reading is not runtime verification.

### ABSENT routes and frozen-H rule

The following are ABSENT and must use a typed unavailable adapter in the normal app, test fakes only, and never fake success: run history list; run cancel and delete; profile sharing; consent grant and revoke; notifications; quota; lesson delivery and feedback; audio transcription and transcript confirmation; photo and audio upload sessions; video admission, status and playback; and every legacy /api/parent/v1/child-profiles, /api/parent/v1/story-runs, /api/notifications, /api/billing and /api/lesson-library/v1/me/deliveries route.

Frozen H files may contain methods for ABSENT routes, including grantAuthorization, revokeAuthorization, archive and getConsentPolicy in apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts, only if no product code path calls them. Controllers classified E must never invoke those methods. apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts, where it is E for a checkpoint, must return a typed unavailable result locally for each ABSENT route instead of issuing HTTP. The frozen stale-PATCH reconciliation in apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts that calls GET /v1/parent/profiles/{profile_id} is allowed. No frozen H path may be edited.

### Checkpoint and regression clarifications

- The three paths created in R0, apps/ui-mobile/src/parent/application/ports/ParentCapabilityPorts.ts, apps/ui-mobile/src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter.ts and apps/ui-mobile/tests/parentSrsBehavior.test.ts, are editable in R1 through R4 under Plan Revision 7 Section 3. Use the preceding checkpoint's exact after-pin as the next pre-pin.
- The frozen-H tests apps/ui-mobile/tests/parentLearningI2.test.ts, apps/ui-mobile/tests/catalogViewModel.test.ts, apps/ui-mobile/tests/storyDraft.test.ts and the demo-flow tests are regression guards for their E sources. Changes to apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts, apps/ui-mobile/src/parent/domain/storyDraft.ts and apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts must be additive, using new functions or optional fields, so every assertion in those frozen tests continues to pass.
- If an assertion in the E tests apps/ui-mobile/tests/parentFlowV1.test.ts or apps/ui-mobile/tests/parentApiI2Contract.test.ts must change because behavior intentionally changes, update it and list each changed assertion and its SRS reason in that checkpoint's evidence report. Never silently delete coverage.
- The BE handoff note and its pin remain unchanged. Plan Revision 7, its allowlist, pins, command ceilings and checkpoint sequence remain unchanged. Keep all SRS 31.10 OPEN-OWNER items open.

- Pre-append DECISIONS.md pin: 25,930 bytes / SHA-256 EAB5F1F30B08CCB50E3A081FE85C0D4F5E6A453BE68E320A78C6E17D2DBE43C8.
- Post-append DECISIONS.md pin: recorded in Addendum 13 after this append; the full resulting pin is cross-recorded there to avoid a self-referential hash.
## D-016 - FEAT-081 Wave R owner clarification: consent and no-preset

- Owner: Person 2.
- Date: 2026-11-13.
- Authority: Direct owner clarification in tmp/fe081-waveR2/GOAL_RESUME_ADDENDUM_1.md, 5,921 bytes / SHA-256 0E0718311AE711665E003F268B50357697970F3DF521B519E9FB8BA7CD94B8E5.
- Status: Plan Revision 7 remains APPROVED. This decision records the owner's consent and no-preset clarifications; it does not change scope, allowlist, pins, command ceilings, or checkpoint sequence.

### Consent behavior

Consent grant and revoke routes remain absent and typed unavailable. While consent is unavailable, show that state as informational and non-blocking. Do not invent or claim a consent confirmation or capture. A server-confirmed denial or revocation blocks learning; server-confirmed consent continues to permit learning when the profile is otherwise eligible. Delete-pending profiles and age-ineligible profiles remain blocked. Consent is never inferred from profile existence.

### No-preset behavior

The backend StoryRun creation contract requires an exact lesson pin containing lesson ID, version ID, and content hash. A topic-only run without a lesson is NOT AVAILABLE in the client until an approved backend contract supports it. Keep the lesson pin required and remove or avoid user-visible copy promising an optional lesson. Mark no-preset acceptance as NOT AVAILABLE because the backend contract is absent; this is not a checkpoint blocker. SRS 31.10 no-preset remains OPEN-OWNER.

### Other route boundaries

Personal-copy lineage and Parent-group invitation decline remain typed unavailable because no corresponding route is present in the D-015 owner-authorized route table. This is accepted and does not change the plan allowlist.

- Pre-append DECISIONS.md pin: 31,797 bytes / SHA-256 5FD6A07D52A29018D4FC841BBB59FE74329A88B0AC642B316D290A1B4C7A172E.
- Post-append DECISIONS.md pin: recorded in Addendum 14 after this append.

## D-017 - FEAT-081 Wave R owner clarification: R3 and R4 backend boundaries

- Owner: Person 2.
- Date: 2026-11-13.
- Authority: Direct owner clarification in tmp/fe081-waveR2/GOAL_RESUME_ADDENDUM_2.md, 7,336 bytes / SHA-256 0AD8DB3F69E420BE8444762E4D588D1896F55152FC1610C0414A70F171920A66.
- Status: Plan Revision 7 remains APPROVED. This decision records R3 and R4 backend-boundary behavior; it does not change scope, allowlist, pins, command ceilings, or checkpoint sequence.
- Pre-append DECISIONS.md pin: 33,745 bytes / SHA-256 B89A61951B304EE28AF41DBDF3348B57B9E54FB0E98638975B952205BBCF604F.

### Owner decisions

1. While no activity route exists, a Parent may generate a story without a chosen main activity. Show “Main activity: not available yet.” Do not block story generation and do not send an activity field in a story-revision request. This is an explicit deviation from SRS BR-15 and FR-P-05 due to the absent backend contract, not SRS conformance.
2. Never infer topic mismatch by comparing strings or keywords. Mismatch handling is NOT AVAILABLE until the backend returns a mismatch signal.
3. With no run-cancel route, the only run action is “Resume active run.” Show a typed cancel-unavailable state. Do not add fake cancel or fake start-over behavior.

### General backend-boundary rule

For any requirement that needs a route or request field absent from the D-015 owner-authorized route table, the normal app returns a typed unavailable state and shows a clear message. Tests may use fakes only. No fake success is allowed. Mark the behavior NOT AVAILABLE: backend contract absent; this is not a blocker. Stop only for an out-of-allowlist file, a frozen H edit, a fake-success requirement, or evidence that the D-015 route table is wrong.

### Acceptance record

- WR-AC13: guide is optional and nonblocking. Show 4–8 ordered steps only if the existing guide response schema supplies them; otherwise mark the deterministic stroke engine NOT AVAILABLE.
- WR-AC14: implement camera-denied/gallery-available and microphone-denied/typed-idea-available behavior with synthetic coverage.
- WR-AC15: typed idea remains available; audio transcription and transcript confirmation are NOT AVAILABLE, with no fake transcript.
- WR-AC16: topic-mismatch handling is NOT AVAILABLE. Keep adult subject correction through the existing subject-confirmation operation; keep the lesson pin unchanged and never change subject silently.
- WR-AC17: bind subject confirmation to expected_understanding_revision and context confirmation to expected_context_revision plus context_snapshot_sha256. A stale 409 returns to adult review and is never retried automatically.
- WR-AC18: show main activity as not available yet; story generation is not blocked by activity selection and no activity field is sent.
- WR-AC19: show pinned lesson activities as read-only information. Catalog filtering, selection, drafts, and replacement are NOT AVAILABLE.
- WR-AC20: guide and story requests exclude raw image/audio, identity, profile fields, and child gender. Script confirmation uses the exact story hash and expected revision.
- WR-AC45: accept a synthetic 20 MiB photo at the offline boundary and reject a larger photo before upload. Resumable upload is NOT AVAILABLE.

OWNER_MODAL_CALL_APPROVED=NO.
- Post-append DECISIONS.md pin: recorded in Addendum 15 after this append.

## D-018 - FEAT-081 Wave R post-emulator correction PE1: top bar background and double status-bar inset

- Owner: Person 2.
- Date: 2026-11-14.
- Authority: Direct owner task after emulator review. The Home screen showed a light-blue status-bar band above a cream empty band and the header.
- Status: Plan Revision 7 remains APPROVED. This decision records the owner-requested PE1 correction and its one-time verification authorization; it does not change the plan, allowlist, pins of other files, or checkpoint sequence.
- Pre-append DECISIONS.md pin: 37,125 bytes / SHA-256 D08056B7F07E07AB4D5DE8861126338E66E532094745B81CE214F0F6235EE833.

### Owner-requested correction

Render the JavaScript StatusBar with dark-content and the approved cream palette background for every app step. Remove the redundant StatusBar.currentHeight top padding from ScreenFrame because the app uses a non-translucent status bar and content is already laid out below it. Preserve all existing screen exports, props, callbacks, defaults, copy, and other layout. Do not edit Android native resources, app.json, package files, or any frozen H row.

### Scope and one-time verification authorization

PE1 code and test scope is limited to apps/ui-mobile/src/parent/presentation/components/ui.tsx, apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx, and apps/ui-mobile/tests/parentSrsBehavior.test.ts, all Plan Revision 7 E/N paths. The R0 evidence report and tmp/fe081-waveR2/run_state/RUN_STATE.md may be updated. The plan, allowlist, other file pins, and checkpoint sequence remain unchanged.

The owner authorizes exactly one additional coordinator pnpm run test run and one additional coordinator pnpm run typecheck run; exactly one additional owner run of validate_harness, validate_repository_security, validate_architecture, and git diff --check; and one owner emulator re-check limited to the top bar area and the Home, Lessons, Start, and Profiles tabs. Codex runs none of these commands or reviews.

OWNER_MODAL_CALL_APPROVED=NO.

## D-019 - FEAT-081 Wave R post-emulator correction PE2: age-band absence is non-blocking

- Owner: Person 2.
- Date: 2026-11-14.
- Authority: Direct owner task after emulator review. The real profile response has null age-band fields because the current backend does not compute an age band.
- Status: Plan Revision 7 remains APPROVED. This decision records the owner-authorized PE2 behavior and shared verification authorization; it does not change the plan, allowlist, pins of other files, or checkpoint sequence.
- Pre-append features/FEAT-081-parent-ui-mobile-port/DECISIONS.md pin: 39,150 bytes / SHA-256 A0CA10FDA558EF8024028E17507CCD1C87947F122E6E1C3045C05AAE52C7498D.

### Owner decision

For a profile with age_months from 36 through 120 inclusive, age eligibility is supported even when both age_band_ref and age_band_version are null. Display an age-band reference and version only when the server supplies both. When both are absent, show the informational state "age band not available yet" without blocking profile selection or learning and without inventing a band or version.

Profiles aged 121 through 155 months remain legacy-read-only: they may be viewed or deleted but cannot start a new run. Ages below 36 or above 155 remain unavailable. If exactly one age-band field is present, treat the server data as inconsistent and unavailable, using the existing safe message. No other behavior changes. D-016 consent rules remain unchanged.

This decision records the FEAT-081 client behavior for the current backend contract. It does not update the SRS, backend schema, or backend contract.

### Scope and shared verification authorization

PE2 is limited to apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts, apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts, apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx, apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx only if needed, apps/ui-mobile/tests/parentFlowV1.test.ts, and apps/ui-mobile/tests/parentSrsBehavior.test.ts, all Plan Revision 7 E/N paths, plus the R1 evidence report and tmp/fe081-waveR2/run_state/RUN_STATE.md. No H row, native file, package file, plan, or allowlist is changed.

PE2 adds no command runs. It shares the single additional coordinator test run, single additional coordinator typecheck run, single additional owner run of validate_harness, validate_repository_security, validate_architecture, and git diff --check, and single owner emulator re-check authorized by Addendum 16. That emulator re-check also covers the profile card and Start flow. Codex runs none of these commands or reviews.

OWNER_MODAL_CALL_APPROVED=NO.

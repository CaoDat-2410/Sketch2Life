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

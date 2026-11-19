# FEAT-081 Plan Revision 20 (draft) — C-P Parent per-role slice (FEAT-066 rows M02–M05, M08–M11) — Draft 3

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. It authorizes no code, merge, fetch, test, command, stage, commit or push.
- **Date:** 2026-11-19. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 2 (13,540 B, `4BEA9D32…`), round-2 review NOT READY 0 P1 / 4 P2 / 7 P3 (`evidence/CP_ADDENDUM_COLD_REVIEW_DRAFT2_20261118.md`); Draft 1 (9,945 B, `8A417387…`), round 1 NOT READY 0 / 8 / 8 (`evidence/CP_ADDENDUM_COLD_REVIEW_DRAFT1_20261118.md`). The owner granted round 3 on 2026-11-19. §10 maps the round-2 findings; §11 keeps the round-1 map.
- **Numbering:** on approval this becomes FEAT-081 **Plan Revision 20**; its Task Approval entries are **Addendum 35** (C-P0) and **Addendum 36** (C-P1); the settled answers of §6 are recorded as FEAT-081 **D-023**. Revision 19 and Addendum 34 were used by the superseded, never-committed `/api/parent/v1` plan (FEAT-081 STATUS, 2026-11-18 entry). Command ceilings come with each addendum.
- **Why here:** FEAT-066 D-066-70 D-D: C-P is carried by a FEAT-081 addendum referencing the FEAT-066 register rows M02–M05 and M08–M11.
- **Owner delegation:** package questions are settled from the SRS or the recommendation (owner instruction of 2026-11-18, recorded in FEAT-066 D-066-75); the owner can override any answer when approving.

## 1. Inputs (full pins)

| Input | Location | Bytes | SHA-256 |
|---|---|---:|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| FEAT-066 register Draft 4 (root checkout, git-ignored `tmp/`) | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` | 41,798 | `0F3F35FD0ABA730D0E1A62A46992D50F9D4DC2297B343452A9916144F99AF5F1` |
| M2 frozen client projection (`origin/dev` at `ba295f11`) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/openapi-client-projection-frozen.json` | 213,111 | `F23BF908A104667153F88D6438AE8E95BE9895A76DAB7099877EBE9EFC49589D` |
| M2 operation inventory and contract freeze (`origin/dev`) | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_OPERATION_INVENTORY_AND_CONTRACT_FREEZE_20261118.md` | 56,475 | `B72228CE918DE75A6531ED6A01C9E2A1C9643D26BC69442505D87591414AE351` |
| M2 limitation ledger, items O1–O4 (`origin/dev`) | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_LIMITATION_LEDGER_20261118.md` | 17,463 | `A82335ECBB3AE1BD600956FEFD75D0885CFE7EF095BA9BBD64303DBD91B5CF4A` |
| FEAT-081 mobile UI target | `docs/adr/ADR-0023-feat081-mobile-ui-target.md` (not `ADR-0023-single-web-role-app.md`) | — | — |
| FEAT-066 decisions | D-066-68 (C-D1, C-D2, C-D5, C-D7, C-D10), D-066-70, D-066-71 CV-1, D-066-75 | FEAT-066 `DECISIONS.md` (conv1 worktree, 68,171 B, `E615C3BF…`) | — |
| Mobile branch | `feature/fe-mobile-remediation` at `5aa9443a` (pushed); contains `origin/dev` `1c9148e8`, not `ba295f11` | — | — |

## 2. What is already true

Facts below were checked in the code by the coordinator and the round-1 and round-2 reviews.

- **Done by `65e0332e`** (pushed on the owner's word): the 11 projected Parent operations use the `/v1` paths, and the 7 state-changing ones send `Idempotency-Key`; profile create sends only the allowed fields and reads the profile back; the controller follows the profile `next_cursor` to the end (`loadAllProfiles`); patch sends `expected_revision` and re-reads on 409 `STALE_REVISION`; the delete-pending view is reconciled; `inspectActiveRun` calls the active-run route; every request sends `X-Request-ID`; `apiErrorFromResponse` reads `code`, `message`, `request_id`, `correlation_id`, `retryable`, `retry_after_seconds`, `current_version` and `field_errors`, with a fallback to `detail`.
- **Profile types match the projection.** The differences are all in the **story-run** types (§4 C-P1 table).
- **Error envelopes:** the projection documents two: `ParentErrorResponse` for profiles (required `code`, `message`, `correlation_id`, `retryable`, `request_id`; optional `current_version`, `field_errors`, `retry_after_seconds`) and `ParentStoryErrorEnvelopeV1` for story runs (no `request_id`, no `current_version`). C-D1 (D-066-68) applies the Parent envelope with `request_id` and `current_version` to every Parent route, and the `ba295f11` runtime already sends `request_id` (and `current_version` when known) on story-run errors; the projection under-documents them. The single tolerant parser stays; nothing is required that the projection does not require.
- **Request-id generator:** `parent-expo-<time>` collides when two requests start in the same millisecond (`loadAllProfiles` and `inspectActiveRun` run together).
- **Parent AI (CV-1):** the `ui-mobile` parser is already dual; the detail-only parser is in `apps/mobile` (`parentWorkflowApi.ts` line 268), outside FEAT-081 by ADR-0023; on `ba295f11` only `sketch-guides` lacks the top-level envelope, and it is blocked by O-ASSIST (ledger O1).
- **Merge facts:** since `1c9148e8`, the only path changed on both sides is `.gitattributes` (both append at the end; no `merge=union`). The M2 merge brings about 25 backend files, 175 FEAT-063 files and 93 FEAT-066 files, and nothing under `apps/` or `tools/`. The mobile line's own `backend/alembic/env.py` (+13/−1) and `compose.yaml` differences survive.
- **Naming gap:** the SRS names `SYNTHETIC_TEST`; the dev BE writes `SYNTHETIC_DEV`; the consent gate accepts both (`workflowTypes.ts` 163–167).
- **Open, non-blocking:** ledger O3 (active-run summary "[PROPOSAL]"); SRS §21.2 main-activity selection on run create, absent from the projection (FR-P-05); FEAT-081 STATUS line 122 still names `401ded3c` (fixed by the C-P1 status entry).

## 3. Gates (register §5 C-P row)

| Gate | Status |
|---|---|
| O-0 (M2 on `dev`) | **Met:** PR #30 merged, `ba295f11` |
| O-MOB2 | **Closed:** D-066-70 D-A and D-B, carried out on 2026-11-18 |
| FEBASE (mobile) | Part done (`1c9148e8`); **C-P0** brings in `ba295f11` |
| O-9 (mobile method) | D-066-70 D-C: side-branch merge, no force-push |
| C-D10 | Parent may be wired before CONV-1 |
| Independent review | After C-P1 implementation, before acceptance (Sonnet 5.5 high) |

## 4. Sub-slices — two tasks, each with its own Task Approval, owner word and single commit

### C-P0 — Bring M2 into the mobile line (Addendum 35; its commit is the merge commit)

1. HieuNewBie joins (D-066-70 D-C): he confirms the `env.py` and `compose.yaml` deviations are still wanted, and that nothing of his is unpushed.
2. Check that `origin/feature/fe-mobile-remediation` is still `5aa9443a` (a fetch needs the owner's word); if it moved, stop and re-plan the merge.
3. Local side branch from the mobile tip; `git merge ba295f11` (pinned by commit). Resolve `.gitattributes` by keeping both sides' appended lines.
4. Owner-run `pnpm` typecheck and vitest in `apps/ui-mobile`; repository validators `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py` and `validate_skeleton.py` (the merge changes repository structure); `git diff --check`.
5. Addendum 35 authorizes the merge commit's whole scope explicitly (the M2 backend, FEAT-063 and FEAT-066 files it brings) and no other edit.
6. On the owner's word: fast-forward `feature/fe-mobile-remediation`, push without force, delete the side branch. C-P0 is complete here; C-P1 starts as a separate task.

### C-P1 — Story-run type parity and request ids (Addendum 36; FE only, `apps/ui-mobile`)

**1. Story-run types — field by field against the projection:**

| FE type (`apps/ui-mobile/src/parent/domain/types.ts`) | Field | FE today | Projection | Change |
|---|---|---|---|---|
| `ParentStoryRunV1` | `run_revision`, `created_at`, `updated_at` | absent | required (integer; strings) | add, required |
| `ParentStoryRunV1` | `profile_revision_ref`, `context_confirmed`, `retryable` | optional | required | required |
| `ParentStoryRunV1` | `current_input_revision`, `understanding_revision`, `story_revision_no` | optional | required, `integer` or null | required, `number \| null` |
| `ParentStoryRunV1` | `subject_label`, `story_revision_id`, `story_sha256`, `error_code` | optional | required, `string` or null | required, `string \| null` |
| `ParentStoryRunV1` | `run_state` | `string` | required enum: `INPUT_PROCESSING`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`, `SCRIPT_REVIEW`, `VIDEO_ADMISSION_PENDING`, `DELETE_PENDING`, `FAILED`, `COMPLETED` | string-literal union |
| `ParentStoryRunV1` | `story_status` | optional `string` | required enum or null: `GENERATING`, `DRAFT`, `CONFIRMED`, `SUPERSEDED`, `FAILED`, `AWAITING_RECONCILIATION` | required union `\| null` |
| `ParentStoryRunV1` | `job_state` | optional `string` | required enum or null: `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `AWAITING_RECONCILIATION` | required union `\| null` |
| `ParentStoryRunV1` | `candidate` | optional `ParentCandidate` (`decision: string`) | required `ParentDrawingCandidateV1` or null; `decision` enum `REVIEW_REQUIRED`, `CONFIRMED_BY_ADULT`, `CORRECTED_BY_ADULT`; `candidate_subject` required (string or null) | new `ParentDrawingCandidateV1` type, required `\| null` |
| `ParentStoryRunV1` | `story` | optional `unknown` | required `ParentStoryDisplayV1` or null (`schema_version`, `language` = `vi`, `title`, `duration_ms`, `scenes`, `story`) | new `ParentStoryDisplayV1` type, required `\| null`; screens keep reading the same fields |
| `ParentStoryRunV1` | `lesson_pin_snapshot` | optional, all inner fields optional | optional (null allowed); when present 11 fields required (`activities`, `content_sha256`, `drawing_subject`, `lesson_id`, `schema_version`, `script_following_allowed`, `subject_learning_notes`, `title`, `topic`, `version_id`, `version_no`) | stays optional; inner required fields made required |
| `ParentStoryContextV1` (run `context_snapshot`) | `age_months`, `interests_summary` | optional | required (`interests_summary` a non-null string) | required |
| `ParentStoryContextV1` | `schema_version`, `profile_revision_ref` | absent | required (`sketch2life.parent-context.v1`; UUID) | add, required |
| `ParentStoryRunEnvelopeV1`, `ParentActiveStoryRunEnvelopeV1` | `request_id` | optional | required | required |
| Subject confirmation response | `request_id`, `decision` | `request_id?`, `decision: string` | required `request_id`; `decision` the constant `CONFIRMED`; `story_run_id`, `understanding_revision` | exact type |

**2. Stale values in screens and fixtures:**
- HomeScreen `terminalRunStates` (line 48): drop `ABANDONED` and `DELETED`, which the enum does not have.
- HomeScreen run-state map (line 501): **delete** the `CONTEXT_PENDING` entry; runs start as `INPUT_PROCESSING`, which the map already has. The copy "Đang chuẩn bị buổi vẽ" becomes unused and is removed with it.
- `CONTEXT_PENDING` fixtures: `tests/parentApiI2Contract.test.ts` line 52, `tests/parentFlowV1.test.ts` lines 252 and 260, `tests/parentLearningI2.test.ts` line 9 → `INPUT_PROCESSING`.
- `ParentVisualPreviewHarness.tsx` (line 200) builds a run literal with `run_state: 'ACTIVE'` and none of the new fields → a valid enum value and the required fields.

**3. Request ids:** `X-Request-ID` matches 1 to 120 characters from `A-Z`, `a-z`, `0-9`, `.`, `_`, `:` and `-`; each attempt gets a new id `parent-<time base36>-<12 random base36 characters>`, using the same `Math.random` source as the existing `createIdempotencyKey` (correlation only; no security property is claimed). The `Idempotency-Key` stays the value that is stable across a retry (SRS §21.1 line 1635). The per-attempt id follows the convention already used by the Demo client (`apiRetryIdentity.test.mjs`).

**4. Contract test (new, vitest):**
- Reads the frozen projection with `readFileSync(new URL('../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/openapi-client-projection-frozen.json', import.meta.url))` (present after C-P0; the file is `-text` in `.gitattributes`), following the existing pattern of `tests/parentSrsBehavior.test.ts`.
- **Runtime part:** stubs `fetch`, calls each of the 11 `ParentApi` methods, and checks method, path template and header names against the projection's path, operation and header parameters.
- **Type part:** fixtures for the run, the two envelopes, the context snapshot, the candidate, the story display and the subject-confirmation response are built from the projection's `required` lists and written with `satisfies` the FE types, so `pnpm` typecheck fails on drift; a runtime assertion checks each fixture's keys against the JSON `required` list.

**5. Other tests:** a request-id uniqueness test (many ids in one millisecond stay distinct and match the pattern); the existing 93 tests stay green after the fixture updates; the UI-copy validator stays valid.

**Allowlist (exact paths in Addendum 36):** `apps/ui-mobile/src/parent/domain/types.ts`; `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` (request-id helper and envelope types); `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx`; `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx`; `apps/ui-mobile/tests/parentApiI2Contract.test.ts`, `parentFlowV1.test.ts`, `parentLearningI2.test.ts`; the new contract test and request-id test under `apps/ui-mobile/tests/`; any other file that typecheck shows reading a tightened field, listed in the Task Approval before it is edited; the C-P1 evidence note; FEAT-081 `status/STATUS.md` (append). No backend, Bruno or `apps/mobile` file.

**Checks (owner-run):** `pnpm` typecheck and vitest; UI-copy validator; repository validators; `git diff --check`.

**Acceptance:** the contract test passes for all 11 operations; typecheck passes with the tightened types; request ids are unique and match the pattern; cursor loop, stale re-read, delete-pending and active-run behaviour unchanged; independent review passed.

### Moved out of C-P

- **Bruno requests for M04, M05, M08** → FEAT-066 L5 (collection `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/`; numbers after C-P0; runner decision O-BRU open). The FEAT-066 register and L5 plan wording that still lists them under C-P are aligned in the next FEAT-066 record update.
- **Parent AI envelope:** approving this plan closes the C-P half of CV-1 (D-066-71) — `ui-mobile` is already dual. `sketch-guides` waits for O-ASSIST and ledger O1; the `apps/mobile` detail-only parser stays outside FEAT-081 (ADR-0023) and is listed as unowned in the FEAT-066 record update.

## 5. Order

C-P0 (Addendum 35, its own owner word, commit and push) → C-P1 (Addendum 36, its own owner word) → independent review → owner acceptance → C-P1's single commit and, on the owner's word, push. C-P needs no FEAT-066 BE slice.

## 6. Settled answers (per the SRS or the recommendation; owner delegation recorded in D-066-75)

| ID | Point | Settled answer | Basis |
|---|---|---|---|
| CP-1 | Contract source | The M2 frozen client projection (`F23BF908…`) | M2 contract freeze (`B72228CE…`); C-D10 |
| CP-2 | The 3 confirmations | Already wired by `65e0332e`; C-P1 only corrects their types; their product exposure and M2 class (PR) stay under O-PROJ | They are in the frozen projection; no new UI |
| CP-3 | How M2 enters the mobile line | Side-branch merge pinned to `ba295f11`, fast-forward, no force-push, as its own task | D-066-70 D-C; one task, one commit |
| CP-4 | Error bodies | One tolerant parser; nothing required beyond the projection; `request_id` and `current_version` read when present | Frozen projection; C-D1; runtime on `ba295f11` |
| CP-5 | Request ids | New collision-free id per attempt, pattern 1 to 120 characters from `A-Z`, `a-z`, `0-9`, `.`, `_`, `:` and `-`; the idempotency key is the retry-stable value | SRS §21.1 line 1635; Demo client convention |
| CP-6 | Parent AI envelope | Nothing left in FEAT-081; closes the C-P half of CV-1; `sketch-guides` waits for O-ASSIST | `ui-mobile` parser already dual; ADR-0023 |
| CP-7 | Consent routes and real-data consent | Out | No route on `dev`/M2; OI-05 open |
| CP-8 | Cancel, Parent Lesson Library reads, main-activity selection | Out | O-PROJ (ledger O2); FR-P-05 open |
| CP-9 | Who runs `pnpm` | The owner | The Codex sandbox fails `pnpm` |
| CP-10 | Bruno requests | FEAT-066 L5, after C-P0 | Collection outside `apps/ui-mobile`; O-BRU open |
| CP-11 | `story`, `candidate`, `lesson_pin_snapshot` | Tightened to the projection types (see the table) | The frozen projection is the contract (CP-1) |

## 7. Not verified

- Live remote state (step 2 of C-P0 checks it).
- The real merge result beyond the facts in §2.
- Whether the BE honours a reused `X-Request-ID` on an idempotent replay (not relied on).
- Which further screens typecheck will flag after tightening (handled by the Task Approval rule in the allowlist).
- No command was run for this draft beyond read-only checks.

## 8. Limits

No backend, Bruno, `apps/mobile` or web file. No new route or screen. Consent, cancel, the Parent Lesson Library and the MG gaps stay out.

## 9. Recording

On approval: Plan Revision 20 (this text), Addenda 35 and 36 in FEAT-081 `approvals/TASK_APPROVAL.md`, D-023 in FEAT-081 `DECISIONS.md`, a STATUS entry; all append-only, decisions only, no owner chat wording.

## 10. Round-2 findings and their fixes

| Finding | Fixed in |
|---|---|
| CP-R2-01 (P2) | §4 C-P1 step 1 field-by-field table (14 fields, 3 enums, context snapshot, envelopes, subject confirmation, `story`, `candidate`, `lesson_pin_snapshot`); CP-11 |
| CP-R2-02 (P2) | §4 step 2 and allowlist: preview harness, the three test files, `terminalRunStates` |
| CP-R2-03 (P2) | §4 step 4: JSON path, runtime fetch-stub part, `satisfies` fixtures plus a runtime key check |
| CP-R2-04 (P2) | §4 heading, C-P0 step 6 and §5: two tasks, each with its own addendum, owner word and commit |
| CP-R2-05 | §2 envelopes paragraph and CP-4 |
| CP-R2-06 | §1 ledger pin and the full ADR file name |
| CP-R2-07 | §4 step 3 and CP-5: pattern, randomness source, Demo-client convention |
| CP-R2-08 | C-P0 steps 1, 2, 4, 5: HieuNewBie joins, remote-tip check, `validate_skeleton.py`, merge scope in Addendum 35 |
| CP-R2-09 | §4 "Moved out": register and L5 alignment; CV-1 C-P half closed; `apps/mobile` parser listed unowned |
| CP-R2-10 | §4 step 2 deletes `CONTEXT_PENDING`; "type the envelopes" dropped |
| CP-R2-11 | §2 attribution and "7 state-changing operations" |

## 11. Round-1 findings (Draft 1)

All sixteen were fixed in Draft 2 (see Draft 2 §9); CP-R1-09, 11 and 13 were completed by CP-R2-06, 01 and 03 above.

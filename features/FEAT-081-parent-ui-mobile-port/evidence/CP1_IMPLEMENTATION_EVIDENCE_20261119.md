# FEAT-081 C-P1 Implementation Evidence — 2026-11-19

## Authority and pins

- Task: FEAT-081 C-P1, Parent story-run type parity and request IDs; Addendum 36, `APPROVED_FOR_IMPLEMENTATION`; decision D-023.
- Approved plan: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_20.md`, 22,981 bytes, SHA-256 `95C9E51ABAF997B0A5164A3EBB713E7060BBAC0A0E3BF05694DA192DC38EA55E`.
- Contract source: `features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/openapi-client-projection-frozen.json`, 213,111 bytes, SHA-256 `F23BF908A104667153F88D6438AE8E95BE9895A76DAB7099877EBE9EFC49589D`.
- Worktree branch snapshot: `feature/fe-mobile-remediation` at `700717fbe9befa01a1152dc7138540a1548a8083`; local origin ref matched. C-P0 ancestry check for `ba295f11` succeeded.
- The owner's pre-existing changes to `DECISIONS.md`, `approvals/TASK_APPROVAL.md`, the four addendum draft files, three cold-review drafts, and `PLAN_REVISION_20.md` were left untouched.

## Files changed

Counts are `git diff --numstat` against HEAD for tracked files; untracked test files count as all-added. The evidence note is excluded from its own table; its final size and SHA-256 are reported by the coordinator after this update.

| Path | Added lines | Removed lines | Current bytes | Current SHA-256 |
|---|---:|---:|---:|---|
| `apps/ui-mobile/src/parent/domain/types.ts` | 90 | 29 | 12,546 | `07137968A22330922B9C8E5F994A9E9E924B922014DA571202E2375183B2169B` |
| `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` | 6 | 1 | 22,573 | `DB3B024EB2743059101CD49DC194DBCE0DF385A93C88799439D4B95772335092` |
| `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 1 | 2 | 37,706 | `EC605E36546CE0D8D62604F278881CBF779230A15231C5D92B397C6433DB54C7` |
| `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx` | 21 | 5 | 28,145 | `96BFF8F542B6C3D0819EDAE39A8A3DC2F00FB23A29B317C148E427B644A52864` |
| `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts` | 10 | 6 | 23,923 | `1DAC2BC378F5855290051DEA4D0C9BB01199CD6D69A41DA46E37793DF41EECA8` |
| `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts` | 2 | 2 | 65,623 | `2E0E92C7E36B8A5D2679B2D8693198249DE550AF978BFC8CD7CB42654F3805F3` |
| `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts` (Addendum 36 amendment 1; one request-id line) | 1 | 1 | 7,828 | `89007F64E826690C13C15B56FB26361BBCDA22E61D19F53DA90F1474F5C01FAC` |
| `apps/ui-mobile/tests/parentApiI2Contract.test.ts` | 1 | 1 | 17,371 | `30E4878CE7D99FDBC93900208F255E572FE5529BD4006076B19502F296D8E20D` |
| `apps/ui-mobile/tests/parentFlowV1.test.ts` | 9 | 3 | 25,843 | `E849BFC943D6481D167101B1D3B98A86D7425428753B06F10057DFC1D4EBB9D3` |
| `apps/ui-mobile/tests/parentLearningI2.test.ts` | 39 | 3 | 7,601 | `9343CDF2364F15DAD1329AAAA0AA2DFAA16924E048464564F4BC9B860509F8B1` |
| `apps/ui-mobile/tests/parentStoryRunProjectionContract.test.ts` | 375 | 0 | 14,043 | `C0D532CF79C88F61F6A9B7A262B0A202AECAD47AF6523C86C9AB75C80658F21E` |
| `apps/ui-mobile/tests/parentRequestId.test.ts` | 24 | 0 | 825 | `4A12D81D91999A058BF52AB535AC6F773F4CF7E415C4A59AF6643D9B4B6F0587` |
| `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md` | 17 | 0 | 24,166 | `153EE04B18BDADB69E6BABFA41C020E476D2DD6943D5C0FF805DC6943318AF1C` |

## Plan section 4, step 1 disposition

| Projection row | Disposition |
|---|---|
| `ParentStoryRunV1`: `run_revision`, `created_at`, `updated_at` | Added as required fields (`number` for the revision and `string` timestamps). |
| `profile_revision_ref`, `context_confirmed`, `retryable` | Changed from optional to required. |
| `current_input_revision`, `understanding_revision`, `story_revision_no` | Changed to required `number \| null` fields. |
| `subject_label`, `story_revision_id`, `story_sha256`, `error_code` | Changed to required `string \| null` fields. |
| `run_state` | Replaced `string` with the exact 10-value projection union. |
| `story_status` | Changed to a required six-value union or `null`. |
| `job_state` | Changed to a required five-value union or `null`. |
| `candidate` | Changed to required `ParentDrawingCandidateV1 \| null`; the candidate has the projected required fields and three-value decision union. |
| `story` | Changed to required `ParentStoryDisplayV1 \| null` with projected schema version, language, story sections, duration and scenes. |
| `lesson_pin_snapshot` | Remains optional and nullable. Its eight previously optional projected fields are required when present; the three already-required pin fields stay required. Optional age-band and script-direction fields remain optional. `Activity` retains its eight required fields. |
| `ParentStoryContextV1` | `age_months` and non-null `interests_summary` are required; added required schema version and profile revision reference. |
| Run envelopes | Both `ParentStoryRunEnvelopeV1` and `ParentActiveStoryRunEnvelopeV1` now require `request_id`; their `story_run` fields remain required. |
| Subject-confirmation response | `request_id`, `story_run_id`, and `understanding_revision` are required; `decision` is the literal `CONFIRMED`. |

The hand-listed required-key arrays, compile-time `RequiredKeys<T>` checks, two-way enum equality checks, and runtime projection comparisons cover the listed rows. The runtime API contract test checks method, path template, and projection-required headers for all 11 Parent API methods; an extra `X-Request-ID` is allowed.

## Other implementation notes

- Removed `ABANDONED` and `DELETED` from Home's terminal run set and removed its `CONTEXT_PENDING` progress entry. Updated the in-scope stale fixtures to `INPUT_PROCESSING`.
- The preview harness uses a valid projected run state, required run/context/pin fields, and candidate decision `REVIEW_REQUIRED`.
- `readDrawingCandidate` returns `ParentDrawingCandidateV1`; unrecognized string decisions fall back to `REVIEW_REQUIRED`. Removed the legacy `CONFIRMED` candidate branch while retaining `CONFIRMED_BY_ADULT` and `CORRECTED_BY_ADULT` behavior.
- `createRequestId` creates a fresh `parent-<base36 time>-<12 base36 characters>` value per request attempt using `Math.random`. The provided `Idempotency-Key` is unchanged and remains the retry-stable action identity. No security property is claimed.
- The `loadAllProfiles` cursor loop, stale-revision re-read, delete-pending reconciliation, active-run inspection, and tolerant error parser were not changed.
- The historical `401ded3c` status statement was corrected by appending a C-P1 checkpoint; the historical entry itself was not rewritten.

## Verification

| Command | Exit code | Output |
|---|---:|---|
| `python tools/validate_harness.py` | 0 | `HARNESS_VALID`; approval and frontend asset gates enabled. |
| `python tools/validate_repository_security.py` | 0 | `REPOSITORY_SECURITY_VALID`; 7,694 publishable files scanned; restricted data classes excluded; no absolute machine paths found. |
| `python tools/validate_architecture.py` | 0 | `ARCHITECTURE_VALID`; dependency direction, mobile isolation, asset gate, AI boundary and Firebase data-product checks valid. |
| `git diff --check` | 0 | No output; clean. |

The validators and `git diff --check` were run again after the evidence and status append. Their final outputs matched the results above.

Not verified by this session: `pnpm run typecheck`, Vitest, the UI-copy validator, and device/runtime behavior. The owner must run the requested typecheck and test command before acceptance. No independent review was started here.

## Owner-reported syntax correction — 2026-11-19

- The owner reported that `pnpm run test` failed to load the new projection contract suite and `pnpm run typecheck` reported syntax errors at the two Parent StoryRun envelope required-key declarations. This session did not rerun either command.
- Moved each `satisfies readonly (keyof ...)[]` clause onto the same line as `as const` in `parentStoryRunEnvelopeRequiredKeys` and `parentActiveStoryRunEnvelopeRequiredKeys` in `apps/ui-mobile/tests/parentStoryRunProjectionContract.test.ts`.
- The test file changed from 14,047 bytes / `7A283240471FBB7168C2FEE95E176564A7DED526359E449993F4000041DE57D9` to 14,043 bytes / `C0D532CF79C88F61F6A9B7A262B0A202AECAD47AF6523C86C9AB75C80658F21E`.
- A whole-file scan for lines beginning with `satisfies` returned no matches.
- After the fix, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check` were rerun; all exited 0. The security validator scanned 7,694 publishable files.
- `pnpm run typecheck`, `pnpm run test`, UI-copy validation, and device/runtime behavior remain unverified. No other file was edited in this correction task; no staging or commit occurred.

## Owner-reported typecheck follow-up and Addendum 36 amendment — 2026-11-19

- The owner reported `pnpm run test` passed with 10 files, 96 tests, and UI-copy validation passing. The owner-run `pnpm run typecheck` log (`tmp/bru0-cp1/cp1_typecheck2.log`) reported two TS2322 errors; this session did not run pnpm or node.
- The first error was in `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts` at the active-run envelope reconstruction: the conditional spread made `request_id` optional. Source inspection confirmed `ParentActiveStoryRunEnvelopeV1.request_id` and `ParentStoryRunEnvelopeV1.request_id` are both required `string`. The only code change in that file is the unconditional `request_id: active.request_id,` at the returned envelope.
- The second error was in `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx`: `previewProfile.interests_summary` is `string | null`, while the projected context requires `string`. The only code change in that file is `interests_summary: previewProfile.interests_summary ?? '',`.
- Owner amendment 1 was appended at the end of Addendum 36 in `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`. It adds only `ParentLearningUseCases.ts`, lines 58-61, to the allowlist for the exact fix above. The remainder of Addendum 36 is unchanged; `OWNER_MODAL_CALL_APPROVED=NO` remains.
- Final file pins after the correction: `ParentLearningUseCases.ts` — 7,828 bytes, SHA-256 `89007F64E826690C13C15B56FB26361BBCDA22E61D19F53DA90F1474F5C01FAC`; `ParentVisualPreviewHarness.tsx` — 28,145 bytes, SHA-256 `96BFF8F542B6C3D0819EDAE39A8A3DC2F00FB23A29B317C148E427B644A52864`; `TASK_APPROVAL.md` — 93,294 bytes, SHA-256 `4C382AE28D8E19F885C28C5F765C0B0628A077A3B6A965FA63B9086EB8183C9D`.
- After the code and approval amendment, the four authorized checks were run: harness, repository security, architecture, and `git diff --check`; all exited 0. The security validator scanned 7,694 publishable files. No pnpm/node, stage, or commit was run by this session.

## Owner-run results and independent review — 2026-11-19

- Owner-run, 2026-11-19: `pnpm run typecheck` completed with no TypeScript errors.
- Owner-run, 2026-11-19: `pnpm run test` passed 10 files / 96 tests. This includes 2 tests in `parentStoryRunProjectionContract.test.ts` and 1 test in `parentRequestId.test.ts`.
- Owner-run, 2026-11-19: UI-copy validator returned `UI_COPY_AND_RECOVERY_VALID`.
- Independent review CP1-R1 = READY WITH NOTES, 0 P1 / 0 P2 / 5 P3, reviewer Sonnet 5.5 high.
- Addendum 36 and amendment 1 remain as approved. `TASK_APPROVAL.md` is 93,294 bytes / SHA-256 `4C382AE28D8E19F885C28C5F765C0B0628A077A3B6A965FA63B9086EB8183C9D`.
- Not committed, not pushed.

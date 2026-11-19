# FEAT-081 Plan Revision 20 (draft) — C-P Parent per-role slice (FEAT-066 rows M02–M05, M08–M11) — Draft 2

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. It authorizes no code, merge, fetch, test, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 1 (9,945 B, `8A417387…`). Its round-1 review was NOT READY with 0 P1, 8 P2 and 8 P3 (`evidence/CP_ADDENDUM_COLD_REVIEW_DRAFT1_20261118.md`). §9 maps each finding to its fix.
- **Numbering:** when approved, this becomes FEAT-081 **Plan Revision 20** and its Task Approval **Addendum 35**. Revision 19 and Addendum 34 were used by the superseded, never-committed `/api/parent/v1` plan (FEAT-081 STATUS, 2026-11-18 entry), so their numbers are not reused. The settled answers of §6 are recorded as FEAT-081 **D-023** on approval. Command ceilings come with Addendum 35.
- **Why here:** FEAT-066 D-066-70 D-D: the Parent slice C-P is carried by a FEAT-081 addendum referencing the FEAT-066 register rows M02–M05 and M08–M11.
- **Owner delegation:** package questions are settled from the SRS or the recommendation (the owner's instruction of 2026-11-18, recorded in FEAT-066 D-066-75); the owner can override any answer when approving.

## 1. Inputs (full pins)

| Input | Location | Bytes | SHA-256 |
|---|---|---:|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| FEAT-066 register Draft 4 (root checkout, git-ignored `tmp/`) | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` | 41,798 | `0F3F35FD0ABA730D0E1A62A46992D50F9D4DC2297B343452A9916144F99AF5F1` |
| M2 frozen client projection (on `origin/dev`, merge `ba295f11`) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/openapi-client-projection-frozen.json` | 213,111 | `F23BF908A104667153F88D6438AE8E95BE9895A76DAB7099877EBE9EFC49589D` |
| M2 operation inventory and contract freeze (on `origin/dev`) | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_OPERATION_INVENTORY_AND_CONTRACT_FREEZE_20261118.md` | 56,475 | `B72228CE918DE75A6531ED6A01C9E2A1C9643D26BC69442505D87591414AE351` |
| FEAT-066 decisions | D-066-68 (C-D1 envelope, C-D2 `X-Request-ID`, C-D5 key, C-D7 Parent `expected_revision`, C-D10 Parent before CONV-1), D-066-70, D-066-71 CV-1, D-066-75 | FEAT-066 `DECISIONS.md` (conv1 worktree) | — |
| Mobile branch | `feature/fe-mobile-remediation` at `5aa9443a` (pushed); contains `origin/dev` `1c9148e8`, not `ba295f11` | — | — |

## 2. What is already true (verified by the round-1 review)

- **Done by `65e0332e`** (owner-approved, pushed): all 11 projected Parent operations use the `/v1` paths with `Idempotency-Key`; profile create sends only the allowed fields and reads the profile back; the controller follows the profile `next_cursor` to the end (`loadAllProfiles`); patch sends `expected_revision` and, on 409 `STALE_REVISION`, re-reads the profile; the delete-pending view is reconciled; `inspectActiveRun` calls the active-run route; every request sends `X-Request-ID`; `apiErrorFromResponse` reads `code`, `message`, `request_id`, `correlation_id`, `retryable`, `retry_after_seconds`, `current_version` and `field_errors`, with a fallback to `detail`; `parentApiI2Contract.test.ts` covers the cursor, delete-pending, the stale 409 and the error cases.
- **Parity against the frozen projection:** the 5 profile operations and subject confirmation match. Story-run create, active, read, context confirmation and script confirmation differ **only in the story-run response type** (`ParentStoryRunV1`): `run_revision`, `created_at`, `updated_at` absent; `profile_revision_ref`, `context_confirmed`, `retryable`, `error_code` and `job_state` optional where the projection requires them; `run_state` typed as a free string instead of the 10-value enum; `context_snapshot` lacking `schema_version` and `profile_revision_ref`; a test fixture and the HomeScreen map using `CONTEXT_PENDING`, which is not in the enum.
- **Two error envelopes** in the projection: profiles use `ParentErrorResponse` (required `code`, `message`, `correlation_id`, `retryable`, `request_id`; optional `current_version`); story runs use `ParentStoryErrorEnvelopeV1` (no `request_id`, no `current_version`). `X-Request-ID` is declared on the profile operations only. M2 ledger O4 (the extra fields) is confirmed by C-D1 for the profile envelope only.
- **Request-id generator:** `parent-expo-<time>` collides when two requests start in the same millisecond (`loadAllProfiles` and `inspectActiveRun` run together).
- **Parent AI (CV-1):** the `ui-mobile` parser is already dual (top-level §9.8 fields and `detail`). The detail-only parser is in `apps/mobile`, which ADR-0023 keeps outside FEAT-081. On `ba295f11` only `sketch-guides` still lacks the top-level envelope, and it is M23, blocked by O-ASSIST (M2 ledger O1, OPEN-OWNER).
- **Merge preview:** a read-only `git merge-tree` of `5aa9443a` with `ba295f11` predicts **one conflict, `.gitattributes`** (both sides append). The M2 merge brings about 25 backend files (Parent story runs, Parent AI, the cancel route, `run_revision` in responses) and the FEAT-063/066 records; it touches no `backend/alembic` or `compose.yaml` path. The mobile line's own differences from `dev` in `backend/alembic/env.py` (+13 lines widening the version table) and `compose.yaml` survive the merge.
- **Naming gap:** the SRS names `SYNTHETIC_TEST`; the dev BE writes `SYNTHETIC_DEV`. The consent gate (`9ae5696e`) accepts both.
- **Open items, non-blocking for C-P:** M2 ledger O3 (the active-run summary is still "[PROPOSAL]"); SRS §21.2 asks for a main-activity selection in the create-run request, which the projection does not have (FR-P-05, FEAT-081 open item); FEAT-081 STATUS line 122 still names `401ded3c` as the branch tip (fixed in the C-P1 status entry).

## 3. Gates (register §5 C-P row)

| Gate | Status |
|---|---|
| O-0 (M2 on `dev`) | **Met:** PR #30 merged, `ba295f11` |
| O-MOB2 (mobile reconciliation) | **Closed:** D-066-70 D-A and D-B, carried out on 2026-11-18 |
| FEBASE (mobile) | Part done (`1c9148e8` merged, `5aa9443a`); **C-P0** brings in `ba295f11` |
| O-9 (FE base reconciliation method) | Mobile part decided by D-066-70 D-C (side-branch merge, no force-push); C-P0 uses the same method |
| C-D10 | Parent may be wired before CONV-1 |
| Independent review | After C-P1 implementation, before the slice is accepted (Sonnet 5.5 high) |

## 4. Sub-slices

### C-P0 — Bring M2 into the mobile line (git, each step on the owner's word)

1. Tell HieuNewBie first: the merge brings the M2 backend into the branch he commits to, and the branch keeps its own `env.py` and `compose.yaml` deviations, which he confirms are still wanted.
2. Local side branch from the mobile tip; `git merge ba295f11` (pinned by commit, not by the moving `origin/dev` ref; a new fetch needs the owner's word). Resolve `.gitattributes` by keeping both sides' lines.
3. Owner-run `pnpm` typecheck and vitest in `apps/ui-mobile` (the Codex sandbox cannot run `pnpm`); the repository validators (`validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, `git diff --check`).
4. Fast-forward `feature/fe-mobile-remediation` to the side branch and push without force; delete the side branch.

### C-P1 — Story-run type parity and request ids (FE only, `apps/ui-mobile`)

1. **Story-run type:** bring `ParentStoryRunV1` and its envelopes to the projection: add `run_revision`, `created_at`, `updated_at`; make the projection-required fields required; type `run_state` as the 10-value enum; complete `context_snapshot` (`schema_version`, `profile_revision_ref`); replace `CONTEXT_PENDING` in the fixture and the HomeScreen map with the enum value the BE returns. The run screens carry `run_revision` but use no new route.
2. **Error envelopes:** keep the one parser; type the two envelopes separately; read story-run `current_version` only as a tolerance (top level or `detail`), never require it.
3. **Request ids:** a collision-free `X-Request-ID` per request (a random suffix inside the 1–120 character pattern), new on every attempt; the `Idempotency-Key` stays the one that is stable across a retry (SRS §21.1 line 1635; the existing `apiRetryIdentity.test.mjs` convention). `X-Request-ID` continues to be sent on every request; the projection declares it on the profile operations.
4. **Tests:** a contract test that reads the frozen projection JSON (in the tree after C-P0) and checks each Parent operation's path, method, headers and required response fields against `ParentApi.ts` types; updated story-run fixtures; a request-id uniqueness test; the existing 93 tests stay green; the UI-copy validator stays valid.

**Proposed allowlist (exact paths in Addendum 35):** `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`, the Parent type files, the HomeScreen run-state map, the request-id helper, the Parent test files and fixtures, the new contract test; the C-P1 evidence note; FEAT-081 `status/STATUS.md` (append). No backend file, no Bruno file.

**Checks (owner-run):** `pnpm` typecheck, vitest, UI-copy validator; repository validators.

**Acceptance:** the contract test passes for all 11 projected Parent operations; story-run types match the projection; request ids never collide; the existing behaviour (cursor loop, stale re-read, delete-pending, active run) is unchanged.

### Moved out of C-P

- **Bruno requests for M04, M05 and M08** → FEAT-066 L5 (BRU-0 and the per-slice Bruno work): the collection lives under `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/`, needs a live BE with seed data and the open runner decision O-BRU, and its numbers are assigned after C-P0 so they do not collide.
- **Parent AI envelope (former C-P2):** nothing left in FEAT-081 (`ui-mobile` is already dual). The remaining BE item, `sketch-guides`, waits for O-ASSIST and M2 ledger O1. The `apps/mobile` detail-only parser is outside FEAT-081 (ADR-0023) and needs its own scope decision if that app is kept.

## 5. Order

C-P0 → C-P1 → independent review → owner acceptance → one commit and, on the owner's word, a push. C-P needs no FEAT-066 BE slice.

## 6. Settled answers (per the SRS or the recommendation; owner delegation recorded in D-066-75)

| ID | Point | Settled answer | Basis |
|---|---|---|---|
| CP-1 | Contract source | The M2 frozen client projection (`F23BF908…`) | M2 operation inventory and contract freeze (`B72228CE…`); C-D10 |
| CP-2 | The 3 confirmations | Already wired by `65e0332e`; C-P1 only corrects their response types. Their product exposure and any change to their M2 class (PR) stay under O-PROJ | They are in the frozen projection; no new UI is added |
| CP-3 | How M2 enters the mobile line | Side-branch merge pinned to `ba295f11`, fast-forward, no force-push | D-066-70 D-C method |
| CP-4 | Error bodies | Two envelopes: profile (§9.8 plus `request_id`, optional `current_version`) and story run (§9.8 only); one tolerant parser | Frozen projection; C-D1 |
| CP-5 | Request ids | New collision-free `X-Request-ID` per attempt; the idempotency key is the retry-stable value | SRS §21.1 line 1635; C-D2 names only the header |
| CP-6 | Parent AI envelope | Nothing left in FEAT-081; `sketch-guides` waits for O-ASSIST | `ui-mobile` parser already dual; ADR-0023 |
| CP-7 | Consent routes and real-data consent | Out of C-P | No route on `dev`/M2; OI-05 open |
| CP-8 | Cancel, the Parent Lesson Library reads, main-activity selection | Out of C-P | O-PROJ (M2 ledger O2); FR-P-05 open |
| CP-9 | Who runs `pnpm` | The owner | The Codex sandbox fails `pnpm` |
| CP-10 | Bruno requests | FEAT-066 L5, after C-P0 | Collection outside `apps/ui-mobile`; O-BRU open |

## 7. Not verified

- Whether the BE honours a reused `X-Request-ID` on an idempotent replay (C-P1 does not rely on it).
- Merge results beyond the `merge-tree` prediction (HieuNewBie may push before C-P0).
- No command was run for this draft beyond read-only checks.

## 8. Limits

No backend, Bruno, `apps/mobile` or web file. No new route or screen. Consent, cancel, the Parent Lesson Library and the MG gaps stay out.

## 9. Round-1 findings and their fixes

| Finding | Fixed in |
|---|---|
| CP-R1-01 | §2 lists what `65e0332e` already did; C-P1 reduced to the story-run type and request ids; "load more" dropped |
| CP-R1-02 | §2 and CP-4: two envelopes, `correlation_id` named |
| CP-R1-03 | C-P1 step 3 and CP-5: per-attempt collision-free id; key is the retry-stable value |
| CP-R1-04 | §2 merge preview and C-P0: `.gitattributes` only; `env.py` and `compose.yaml` confirmed with HieuNewBie; pinned to `ba295f11`; validators |
| CP-R1-05 | §4 "Moved out" and CP-6 |
| CP-R1-06 | §3 gate table; independent review in §3 and §5 |
| CP-R1-07 | Bruno moved to FEAT-066 L5 (CP-10) |
| CP-R1-08 | CP-2 names O-PROJ |
| CP-R1-09 | §1 full pins, projection hash, freeze document |
| CP-R1-10 | Header numbering (Revision 20, Addendum 35, D-023) |
| CP-R1-11 | §2 and C-P1 step 1 full list |
| CP-R1-12 | §2 open items |
| CP-R1-13 | C-P1 step 4 contract test reads the frozen JSON |
| CP-R1-14 | Former C-P2 removed |
| CP-R1-15 | Header cites D-066-75; §2 naming gap |
| CP-R1-16 | §2: STATUS fixed in the C-P1 status entry |

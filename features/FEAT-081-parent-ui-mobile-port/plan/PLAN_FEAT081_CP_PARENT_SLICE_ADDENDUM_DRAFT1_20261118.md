# FEAT-081 addendum — C-P Parent per-role slice (FEAT-066 register rows M02–M05, M08–M11) — Draft 1

- **Status:** DRAFT / NOT REVIEWED / NOT APPROVED / NOT LAUNCHED. It authorizes no code, merge, test, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Why here:** FEAT-066 D-066-70 D-D says the Parent slice C-P is carried by a FEAT-081 addendum that references the FEAT-066 register rows M02–M05 and M08–M11.
- **Trigger:** PR #30 (the M2 Parent/Teacher foundation) was merged into `dev` on 2026-11-18 (merge commit `ba295f11`). `dev` now carries the frozen M2 Parent routes.
- **Owner delegation:** package questions are settled from the SRS or the recommendation (§6); the owner can override any of them when approving.

## 1. Inputs

| Input | Location (relative to the repository root) | Pin |
|---|---|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 B, `B9B1F42D…` |
| FEAT-066 register Draft 4 | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` (git-ignored, root checkout) | 41,798 B, `0F3F35FD…` |
| M2 frozen client projection | `features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/openapi-client-projection-frozen.json` on `origin/dev` | 213,111 B (hash to pin in the C-P1 Task Approval) |
| FEAT-066 decisions | D-066-68 (C-D1 envelope with `request_id` and `current_version`; C-D2 `X-Request-ID`; C-D5 key; C-D7 Parent revision in the body, `expected_revision`; C-D10 Parent may go before CONV-1), D-066-70 (mobile reconciliation), D-066-71 CV-1 (`/api/parent/v1/ai` envelope moved to C-P) | FEAT-066 `DECISIONS.md` |
| Mobile branch | `feature/fe-mobile-remediation` at `5aa9443a` (pushed) | contains `origin/dev` `1c9148e8`, **not** `ba295f11` |

## 2. What is already true

| Fact | Effect |
|---|---|
| The mobile Parent API layer was moved to the dev `/v1` family on 2026-11-18 (`65e0332e`): profiles list/read/create/patch/delete and story-run create/active/read/context/subject/script confirmations, with `Idempotency-Key` on every command and `expected_revision` on patch and script confirmation | Most register defects of M02–M05 and M08–M11 (legacy paths, missing keys) are already fixed against the pre-M2 `dev` |
| Owner-run checks on `5aa9443a`'s parent commit `2e61b369`: typecheck clean, vitest 93/93, UI-copy validator pass | Baseline for C-P |
| The synthetic consent gate follows SRS 832 and 1095 (`9ae5696e`) | Real-data consent stays open (OI-05) |
| The mobile branch does **not** yet contain the M2 merge `ba295f11` | C-P0 brings it in |
| The frozen client projection lists 11 Parent operations: the 5 profile operations and 6 story-run operations (create, active, read, context, subject, script confirmation). The 8 M2-allowed operations of the roadmap are the 5 profile operations plus create, active and read | C-P1 checks the 8; the 3 confirmations are already called and are checked too (§4) |
| Cancel (`POST /v1/story-runs/{run_id}/cancel`) is an M2 target but not in the client projection (M2 ledger O2) | Out of C-P (O-PROJ) |

## 3. Row map

| Row | Operation (M2) | Remaining work after `65e0332e` | Sub-slice |
|---|---|---|---|
| M02 | GET `/v1/parent/profiles` | UI cursor continuation ("load more"); response and error parity with the projection | C-P1 |
| M03 | GET `/v1/parent/profiles/{profile_id}` | flat view and the delete-pending view handled; parity | C-P1 |
| M04 | POST `/v1/parent/profiles` | parity of the 201 reference and the read-back; Bruno request (MISSING) | C-P1 |
| M05 | PATCH `/v1/parent/profiles/{profile_id}` | `STALE_REVISION` 409 handling with `current_version`; Bruno request (MISSING) | C-P1 |
| M08 | DELETE `/v1/parent/profiles/{profile_id}` | 202 delete-pending view; Bruno request (MISSING) | C-P1 |
| M09 | GET `/v1/story-runs/active/current` | `run_revision` in the FE type; the route summary is still "[PROPOSAL]" (M2 ledger O3) | C-P1 |
| M10 | GET `/v1/story-runs/{run_id}` | `run_revision` in the FE type | C-P1 |
| M11 | POST `/v1/story-runs` | body parity (no extra fields), `run_revision`, an active caller | C-P1 |
| Confirmations | context, subject, script confirmation | already called; parity check only, no new UI | C-P1 |
| Parent AI | `/api/parent/v1/ai/...` | §9.8 envelope on the BE and an envelope-aware mobile parser (CV-1) | C-P2 |
| M01, M06, M07 | consent policy and data authorizations | no route on `dev`/M2; open (O-PCONSENT, OI-05) | out |
| M12, M13 | legacy confirmation paths | superseded by the `/v1` confirmations above | closed by `65e0332e` |
| M15, M16, M19, M21 | Parent Lesson Library `/me` reads | proposed separate slice; needs O-PROJ | out |
| MG01–MG15 | Parent capability gaps (StoryRun assets, idea, jobs, video, quota, notifications, history, sharing, purchase) | BE gaps; separate slices | out |

## 4. Sub-slices

### C-P0 — Bring M2 into the mobile line (git step, owner word)

Merge `origin/dev` (`ba295f11`) into `feature/fe-mobile-remediation` the way D-066-70 D-C was done on 2026-11-18: a local side branch from the mobile tip, the merge there, owner-run `pnpm` typecheck and vitest, then a fast-forward of `feature/fe-mobile-remediation` and a push without force, each step on the owner's word. HieuNewBie is told before the merge, because the M2 merge brings backend and Alembic changes into a branch he commits to. Expected conflict areas: `backend/alembic`, `compose.yaml`, FEAT-081 records.

### C-P1 — Contract parity of the Parent operations (FE only, mobile)

1. **Parity audit** of the 11 projected Parent operations against `openapi-client-projection-frozen.json`: request bodies, headers (`Idempotency-Key`, `X-Request-ID`), status codes (201, 202 on delete, 409 `STALE_REVISION`), response shapes (flat profile view, delete-pending view, `run_revision`), and the error body (§9.8 fields plus `request_id` and `current_version`, C-D1).
2. **Fixes in `apps/ui-mobile`** for every difference: `ParentApi.ts` types and parsing; the profile list "load more" with `next_cursor` (M02); the patch conflict path shows the current version and lets the Parent retry (M05; C-D7); the delete screen shows the pending deletion (M08); `run_revision` carried on the run types (M09–M11); one `X-Request-ID` per request, reused on the retry of the same command (C-D2).
3. **Tests:** contract tests next to `parentApiI2Contract.test.ts` and `parentFlowV1.test.ts` for each operation and each error shape; the existing 93 tests stay green; the UI-copy validator stays valid.
4. **Bruno (L5):** requests for M04, M05 and M08 (missing today) with status and envelope assertions.

**Proposed allowlist (exact paths in the C-P1 Task Approval):** `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` and its type files; the Parent profile and story-run screens and hooks under `apps/ui-mobile/src/parent/`; the four Parent test files and new contract tests; the three Bruno requests; the FEAT-081 evidence note. No backend file.

**Checks (owner-run, because the Codex sandbox cannot run `pnpm`):** typecheck, vitest, the UI-copy validator; repository validators.

**Acceptance:** every projected Parent operation matches the frozen projection in path, headers, status codes and shapes; the FE shows stale, pending-deletion and envelope errors without inventing retry semantics; tests green.

### C-P2 — Parent AI envelope (CV-1)

- **BE part (FEAT-066 BE queue):** add `/api/parent/v1/ai` to the CONV-1 envelope (the family CV-1 left out because the mobile parser reads only `payload.detail`), with its OpenAPI error rows.
- **FE part (mobile):** the Parent AI parser reads the §9.8 envelope (`code`, `message`, `retryable`, `retry_after_seconds`, `request_id`) and stops reading `detail`.
- The FE part ships **first or together**, so the mobile app never meets an envelope it cannot read (the parser accepts both shapes during the window).

## 5. Order

1. C-P0 (owner word for each git step), then C-P1 FE. C-P1 needs no BE change and is outside the FEAT-066 BE queue; it is the only role slice that can be wired now.
2. C-P2 FE (dual parser) after C-P1; C-P2 BE joins the FEAT-066 BE queue after C-T1 BE unless the owner moves it.
3. Cancel, the Parent Lesson Library reads and the MG gaps wait for their own decisions (O-PROJ, OI-05) and slices.

## 6. Settled answers (per the SRS or the recommendation; owner delegation of 2026-11-18)

| ID | Point | Settled answer | Basis |
|---|---|---|---|
| CP-1 | Contract source for C-P1 | The M2 frozen client projection on `dev` | M2 freeze (D-171 item 7); C-D10 lets Parent go before CONV-1 |
| CP-2 | Scope of the parity check | The 8 M2-allowed operations plus the 3 confirmations already called | They are all in the frozen projection and already wired; no new UI for the confirmations |
| CP-3 | How M2 enters the mobile line | Side-branch merge and fast-forward, as D-066-70 D-C | Same method that worked on 2026-11-18; no force-push |
| CP-4 | Error body | Parse §9.8 fields plus `request_id` and `current_version` | C-D1; M2 ledger O4 confirmed by C-D1 |
| CP-5 | Correlation header | Send `X-Request-ID`; reuse it on a retry of the same command | C-D2 |
| CP-6 | Parent AI envelope | C-P2: dual parser first, then the BE envelope | CV-1 (D-066-71) |
| CP-7 | Consent routes (M01, M06, M07) and real-data consent | Out of C-P | No route on `dev`/M2; OI-05 open |
| CP-8 | Cancel and the Parent Lesson Library reads | Out of C-P | O-PROJ (M2 ledger O2) |
| CP-9 | Who runs `pnpm` | The owner | The Codex sandbox fails `pnpm` with EPERM |

## 7. Not verified

- The exact differences between the mobile types and the frozen projection (C-P1 step 1 finds them).
- Merge conflicts of C-P0 (depends on HieuNewBie's commits since `5aa9443a`).
- No command was run for this draft beyond read-only searches.

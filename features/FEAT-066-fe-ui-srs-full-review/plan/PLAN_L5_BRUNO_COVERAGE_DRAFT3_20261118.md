# FEAT-066 L5 — Bruno coverage plan (A-5) — Draft 3

- **Status:** DRAFT / NOT APPROVED / NOT RE-REVIEWED. This is a plan only. It authorizes no change to any Bruno file, and no Bruno run, test or runtime.
- **Date:** 2026-11-18.
- **Author:** coordinating Claude session (Opus 5.5).
- **Owner:** Person 2. L5 is the owner's own lane (D-066-65).
- **Predecessors, unchanged:** Draft 2 (14,900 bytes, `1BE8D3EC6D807F68320DA79769FF9A13236F634337EBD74F4977DC97D658EDE9`); Draft 1 (10,625 bytes, `06750F9A8F324FB282E688A03B73066FD070307697F0BF1C5B5664ABB4E9545B`).
- **Draft 2 review:** Sonnet 5.5 (told high), round 2, NOT READY (0 P1 / 2 P2 / 9 P3). Record: `evidence/notes/L5_BRUNO_COVERAGE_DRAFT2_COLD_REVIEW_20261118.md`. Draft 3 fixes B2-01 to B2-09 (§10) and is not re-reviewed.
- **Draft 1 review:** Sonnet 5.5 (told high), round 1, NOT READY (0 P1 / 7 P2 / 4 P3). Record: `evidence/notes/L5_BRUNO_COVERAGE_DRAFT1_COLD_REVIEW_20261118.md`, 6,828 bytes, `637A26B69412BFBB…`. §10 disposes of B1-01 to B1-11.
- **Inputs:**
  - P4 inventory: `tmp/feat066-phase-a/bruno-inventory/BRUNO_COVERAGE_INVENTORY_DRAFT1_20261118.md`, 48,221 bytes, `50BACD27…`.
  - A-1 register Draft 4: `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md`, 41,798 bytes, `0F3F35FD…`.
  - Roadmap Draft 4, L5 card.
  - Seed design Draft 6: `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT6_20261118.md`, 28,192 bytes, `CABC4BCA…`.
  - Decisions D-066-64 to D-066-70, especially D-066-68 and D-066-69.
  - The SRS of D-066-64.
- **Collection:** `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/` in the root checkout. It holds 145 request files, `bruno.json`, the untracked `ROLE_GUIDE.md` and the tracked `environments/local.bru`, plus the owner's uncommitted edits.

## 0. Security state and owner actions (before any other L5 step)

**Done on 2026-11-18** (coordinator, on the owner's word "dọn cho tôi"). The script printed only yes/no and made no backup:
- In `environments/local.bru`, `bearerToken` was replaced with `REPLACE_WITH_LOCAL_TOKEN`.
- In the untracked `requests/firebase-auth-helper/001-parent-email-password-sign-in.bru`, the e-mail and password were replaced with `REPLACE_WITH_LOCAL_PARENT_EMAIL` and `REPLACE_WITH_LOCAL_PARENT_PASSWORD`.
- A later scan of the collection found no JWT, no Google API key, no password value and no `@gmail.com` address.

**Still to do (owner), in this order:**

| # | Action | Why |
|---|---|---|
| S-1 | **Rotate the password** that was in the helper. This is unconditional (B1-01). | The value was read into an AI session context before it was cleaned. |
| S-2 | **Done** (2026-11-18): the helper folder is in the local `.git/info/exclude` (`git check-ignore` confirms). | — |
| S-3 | Decide what happens to `local.bru`. It is tracked, and it still differs from `HEAD` because of the owner's other edits (after the token placeholder was restored to the committed text, the diff is 5 insertions / 0 deletions: two local IDs and a `vars:secret [ firebaseApiKey ]` block). Either commit it in the owner's own collection commit after checking it, or restore it. | `git add -u` or `commit -a` would otherwise stage it. |

## 1. Secret-handling rules (B1-02)

1. **Placeholders only** in `environments/*.bru`.
2. **Real tokens and passwords live only in runtime variables, in the collection's own git-ignored `bruno/.env`, or in `--env-var` overrides.** The CLI reads `.env` from `<collection root>/.env` (`features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/.env`, covered by `.gitignore` line 2), not from the repository root. Report masking covers `.env` values and `--env-var` secrets only, so plain shell `process.env` values are not used for secrets.
3. **No request or script persists a token or any other value to disk.** Scripts use `bru.setVar` only (kept in memory). They never use `bru.setEnvVar` (CLI 4.3.0 persists it into the active environment file, i.e. the tracked `local.bru`) or collection-variable setters (persisted into `collection.bru`).
4. **Run reports:** every `bru run` uses `--reporter-skip-all-headers --reporter-skip-body`, because headers and bodies (including a sign-in response) would otherwise be written in full. A report produced without both flags is not kept anywhere.

## 2. Scope (from the register, per inventory)

| Group | Rows / operations | L5 coverage |
|---|---|---|
| BRU-0: connected, no route-specific defect recorded | A02, A08, A17, A20, A22, A26, A27 | positive cases for the current behaviour. Gates: L5-0; SEED-1 S1; **G0 for A17, A20, A22, A26, A27**; **O-L3SCOPE for A08** (a CB route) |
| C-P: Parent first slice | M02, M03, M04, M05, M08, M09, M10, M11 | Full cases (§4).<br>Three new requests use the **M2 paths**: `POST /v1/parent/profiles` (M04), `PATCH /v1/parent/profiles/{profile_id}` (M05), `DELETE /v1/parent/profiles/{profile_id}` (M08). Never the legacy `/api/parent/v1/child-profiles` paths.<br>Add the K2 (delete-pending) read case.<br>M09 summary is OPEN (M2 ledger O3); its cases do not depend on the summary text.<br>M2 already has the envelope and key rules, so C-P negatives are **baseline**, not target. |
| Touched CB / PO+CB rows not covered elsewhere (A06, A07, A09, A10, B01, B02, C01; A08 is in BRU-0; B03, B04, C02 are in the refusal row) | per register | only after **O-L3SCOPE** decides their scope; the freeze marks CB for deprecation (D-171 item 7) |
| Other slices | the register §5 queues: CONV-1, C-M, C-T, C-A, the PROPOSED Parent Lesson Library slice, L2 | added per slice, when that slice is verified |
| Excluded or blocked | B03–B06 (EXCL); AI1–AI3, C02, M14, M23, M24 | auth-boundary and refusal cases only |
| Refusal gaps from P4 | Parent cancel (request 129; O-PROJ, M2 ledger O2); FE-disabled class create (request 007 = B01) | refusal cases until O-PROJ and W-CAP |
| No case yet | M01, M06, M07, M25 (no route); M12, M13 (O-PROJ) | none until their decisions |
| Not audited | the 86 untouched CB, CD, LE and PO+CB operations | existing requests stay as they are; no new work until O-L3SCOPE |
| Payment | none in the frozen list | the payment teammate |

**Reconciliation with the register queues (B1-10, B2-07):** each row belongs to exactly one group, as listed below. Of the 41 web templates and 27 mobile rows, L5 now plans cases for 7 (BRU-0) + 8 (C-P) + 11 (refusal) = 26 rows. 6 rows have no case yet. The remaining rows are added with their slices.
- BRU-0: 7 rows.
- C-P: 8 rows.
- Refusal: 11 rows plus the 2 P4 gaps.
- No case yet: 6 rows.
- Per-slice later: the remaining register rows, in their slice.

## 3. Running rules

1. **Owner-run, outside the Codex sandbox.** On 2026-11-18 a Codex run of the catalog test hung in the asyncio loopback socket setup under `TestClient`, while the same test finished in seconds in the owner's terminal. That observation is in the MGR-8 records. Owner-run is chosen in any case (B1-09).
2. **Disposable seeded environment only:** a local app and a `seed` database (seed Draft 6 guard).
3. **Collection-level pre-request guard (B1-06, B2-02):**
   - A **new** `collection.bru`, created in L5-0, holds a pre-request script that resolves the request URL (`req.getUrl()`) and throws unless its host is loopback (`127.0.0.1`, `::1`, `localhost`). A thrown pre-request script means the request is never sent.
   - Runs are **always folder-scoped** to `requests/l5/...`, never a recursive run from the collection root. This keeps the external Firebase helper and old requests out of L5 runs.
   - Before each run the owner confirms in the run record that the local app is connected to the `seed` database. A loopback URL alone does not prove that.
4. **Repeatability (B1-06):**
   - New requests use a fresh `Idempotency-Key` per run, generated in a pre-request script and stored with `bru.setVar`, except where a case deliberately replays a key inside the same run.
   - **Cascade rule (B2-09):** requests in a chain run in `seq` order. When a step fails, the later steps of the same chain are skipped with `bru.runner.skipRequest()` and are reported as "skipped after <request>". They are never listed as separate unexpected failures.
   - State-changing positives create the data they change, then change and delete it, so the seeded baseline stays intact.
   - A full run starts from a fresh seed (seed S1 and S2). Cases that need S3 or S4 state are one-shot per seed database and are marked time-sensitive.
5. **Existing files stay untouched (B1-03, B1-11):**
   - The 86 existing requests that use `{{bearerToken}}` keep it.
   - New requests use the per-role variables of §5.
   - Editing the old requests is a separate, owner-approved step.
   - Labels such as "stale" or "dev-only" go into a new FEAT-066 list file, not into owner files, until the owner agrees.
6. **The owner's uncommitted collection edits are preserved.** L5 file work starts only after the owner commits them, in their own commit, or hands them over (O-BRU-BASE).

## 4. Case template (one request file per case — B1-07)

All rules follow D-066-68. "Error envelope" means the §9.8 fields `code`, `message`, `correlation_id` and `retryable`, plus the allowed extra `request_id`, which must equal `correlation_id` (C-D1). **Every** response, success or error, carries `X-Request-ID`. On errors it equals `correlation_id` (C-D2, SRS §21.1).

| Operation kind | Positive | Negatives (each its own request) |
|---|---|---|
| Read by ID | 200; key fields; `X-Request-ID` present | <ul><li>unknown ID → 404 `RESOURCE_NOT_FOUND`</li><li>another organization's ID (seed org B) → the **same** 404 shape (C-D4)</li><li>401 `AUTH_REQUIRED` (no token)</li><li>401 `INVALID_TOKEN` (malformed token)</li><li>401 `TOKEN_EXPIRED` where the local auth can produce an expired token (NV)</li></ul> |
| List | 200; default page size 25. The page shape `{items, next_cursor}` is the M2 and Lesson Library current shape; it is a conventions-plan proposal, not part of D-066-68 | <ul><li>`limit=100` accepted</li><li>`limit=101` → 400 `INVALID_REQUEST` (C-D8)</li><li>cursor continuation</li></ul> |
| State-changing command | 2xx; `X-Request-ID` | <ul><li>missing key → 400 `INVALID_REQUEST`</li><li>malformed key (empty, more than 128 characters, non-visible ASCII) → 400 `INVALID_REQUEST` (C-D5). The "two header values" case is NV in Bruno and belongs in a BE unit test</li><li>same key and payload → same result (C-D6)</li><li>same key, different payload → 400 `INVALID_IDEMPOTENCY_KEY`</li><li>invalid body → 400 `INVALID_REQUEST` with `field_errors` (C-D3)</li></ul> |
| Revisioned command — **profile, lesson plan, story or script only** (SRS §21.4 line 1699; not accounts, D-066-69) | 2xx with the new revision | stale revision → 409 `STALE_REVISION` with `current_version` or the current ETag (C-D7) |
| Role boundary | — | <ul><li>wrong role in scope → 403 `ACTION_NOT_ALLOWED`</li><li>out of scope → 404 (C-D4)</li><li>a second Parent reading another Parent's profile → 404</li></ul> |
| Capacity and quota (after the Billing slices) | — | <ul><li>org C create → 409 `CLASS_CAPACITY_REACHED`</li><li>org G create → 409 `SUBSCRIPTION_RESTRICTED`</li><li>exhausted scope → 409 `VIDEO_QUOTA_EXCEEDED`</li></ul>All three are time-sensitive. |
| Privacy (D-066-69) | — | the School Manager roster read returns no profile contents |

**Target versus baseline (B1-07, B2-05):** Bruno has environments, not profiles. CLI 4.3.0 supports `--tags` and `--exclude-tags`, matched against request and folder tags.
- Tests for behaviour that does not exist yet (CONV-1 etc.) sit in **target folders** (`…/target/`), and each target folder carries the tag `target`. Baseline runs use `--exclude-tags target`; target runs use `--tags target`.
- An **expected-failure list** file (`features/FEAT-066-fe-ui-srs-full-review/evidence/L5_EXPECTED_TARGET_FAILURES.md`, pinned per run) lists every target request that is expected to fail until its slice lands.
- A target run passes when its failures equal that list.
- Assertions are never weakened.

## 5. Tokens and identities (B1-06)

**Per-role runtime variables** (values in `process.env` only):

| Role | Variables |
|---|---|
| Platform Admin | `tokenPlatformAdmin` |
| School Manager | `tokenManagerOrgA`, `tokenManagerOrgB` |
| Teacher | `tokenTeacherAssigned`, `tokenTeacherUnassigned` (same organization, no class), `tokenTeacherNoOrg` |
| Parent | `tokenParentP1`, `tokenParentP2`, `tokenParentP3` (no profile) |

Each role variable is read in requests as `{{process.env.<NAME>}}`, from the collection `.env` or an `--env-var` override (§1 rule 2). Example: the header `Authorization: Bearer {{process.env.TOKEN_PARENT_P1}}`. Emulator ID tokens expire (about one hour), so a long run re-mints them first.

How each token is obtained is **O-BRU-AUTH**. Real Firebase accounts would conflict with the seed's no-real-identifier rule. The preferred options are therefore:
- the local Firebase Auth emulator, with the seeded subjects; or
- a development auth provider.

Either way, no credential goes into Git.

## 6. Folder layout (new requests only)

New folders, with existing folders unchanged:
- `requests/l5/<role>/<slice>/`, with roles `parent`, `school-manager`, `teacher`, `platform-admin`, `shared` and slices such as `bru-0` or `c-p`, plus `requests/l5/<role>/<slice>/target/` for target-only cases;
- `requests/l5/refusal/`.

This follows the roadmap's "one folder per role and slice". `ROLE_GUIDE.md` is untracked and belongs to the owner, so the L5 listing goes into a new `requests/l5/README.md` until the owner agrees to merge them.

## 7. Work order

| Step | Content | Gate |
|---|---|---|
| L5-0 | S-1 and S-3 of §0 (S-2 done); O-BRU-AUTH decided; Bruno CLI installed with a pinned version (done: `@usebruno/cli` 4.3.0, installed by the owner on 2026-11-18); O-BRU-BASE; runtime variables (§5); the new `collection.bru` with the loopback guard; the expected-failure list file; the `target` folder tags | owner |
| L5-1 = BRU-0 | Positive cases for A02, A17, A20, A22, A26, A27 (current behaviour); A08 after O-L3SCOPE | L5-0; SEED-1 S1; G0 for the five Lesson Library rows |
| L5-2 | C-P BE cases: the 3 new requests on M2 paths; full baseline cases for the 8 operations; K2 read; second-Parent isolation | **BE-only gates (B2-08):** M2 on `dev` (O-0) and seed S1. These cases test the BE contract, so they do not wait for the FE items. The mobile FE wiring (C-P FE: O-MOB2, O-9, FEBASE, FEAT-081 addendum) is separate |
| L5-3 | CONV-1 target folder becomes baseline | CONV-1 verified |
| L5-4… | One step per verified slice | each slice |
| L5-D | Full run on a clean seeded environment; run record | Phase D |

Each step has its own small Task Approval: the exact files, and the owner-run command.

## 8. Run record

Each run gets an evidence note, plus a header-free summary file under `tmp/feat066-l5/`. The record holds:
- the Bruno CLI version;
- the environment name (placeholders only);
- the seed stage, and the database name pattern (never the URL);
- baseline or target;
- passed, failed and skipped counts;
- each failure, with its request file;
- the expected-failure list pin;
- the collection pin.

## 9. Owner decisions

| ID | Question | Proposal |
|---|---|---|
| S-1 to S-3 (§0) | Password rotation, helper exclusion, the `local.bru` decision | do them now |
| O-BRU | Runner | Bruno CLI, owner-run, version pinned at install |
| O-BRU-BASE | The owner's uncommitted collection edits | the owner commits them first, in their own commit, after S-3 |
| O-BRU-AUTH | How role tokens are obtained | local Firebase Auth emulator with seeded subjects, or a development auth provider; never real accounts |
| O-BRU-TARGET | Target cases | separate target folders plus a pinned expected-failure list |
| O-BRU-LABELS | Stale (004/005) and `dev`-only (128, 131–135) labels | keep them in `requests/l5/README.md`; edit owner files only with the owner's word |

## 10. Disposition of the reviews (not re-reviewed)

**Draft 2 review (B2-01 to B2-09):**

| ID | Disposition |
|---|---|
| B2-01 | §1 rules 3 and 4: `bru.setVar` only; no `setEnvVar` or collection setters; `--reporter-skip-all-headers --reporter-skip-body` on every run; secrets from `.env` or `--env-var` (masked) |
| B2-02 | §3 rule 3: new `collection.bru`, guard on the resolved request URL host, folder-scoped runs only, owner confirms the `seed` database per run |
| B2-03 | §0: S-2 done; `local.bru` diff facts refreshed |
| B2-04 | §1 rule 2: the collection `bruno/.env` |
| B2-05 | §4: `target` folder tags with `--exclude-tags target` / `--tags target`; NV dropped |
| B2-06 | §5: `{{process.env.<NAME>}}` mapping and token re-minting; §7 L5-0 gates O-BRU-AUTH and S-3 |
| B2-07 | §2: overlap removed; reconciliation total |
| B2-08 | §7 L5-2: BE-only gates (M2 on `dev`, seed S1), FE wiring separate |
| B2-09 | §4: the two-header case moved to a BE unit test (NV in Bruno); §3: cascade rule |

**Draft 1 review (B1-01 to B1-11):**

| ID | Disposition |
|---|---|
| B1-01 | §0 S-1 unconditional rotation, S-2 local exclude, S-3 `local.bru`; §1 `.env` named |
| B1-02 | §1 rules 3 and 4: no token persisted, header-free reports |
| B1-03 | §3 rule 5: existing requests keep `bearerToken`; role variables only in new requests |
| B1-04 | §2 and §7: O-L3SCOPE for A08 and the touched CB rows; the five G0 rows listed |
| B1-05 | §4: envelope on errors only, `X-Request-ID` on every response, stale revision limited to the §21.4 list, 401 variants, key-format cases, `request_id` alias, page-shape source stated |
| B1-06 | §5 tokens; §3 rules 3 and 4: loopback guard, fresh keys, create-change-delete, fresh seed per run |
| B1-07 | §4: one request per case; no profiles; tags NV; target folders and a pinned expected-failure list |
| B1-08 | §2 C-P: M2 paths, K2, M09 OPEN, baseline negatives; §7 L5-2 gates aligned with the register |
| B1-09 | §3 rule 1 reworded as an observation |
| B1-10 | §2: refusal gaps 129 and 007; disposition for M01, M06, M07, M12, M13, M25; reconciliation line; §6 role-and-slice folders |
| B1-11 | §3 rule 5 and §6: labels and listing in a new L5 README, not in owner files |

## 11. Not verified

- Bruno CLI behaviour was checked by the reviewer in the 4.3.0 source, not by running it. UUID generation inside the CLI's safe script sandbox is NV.
- The real status codes. Many target cases fail until their slices land.
- How seeded adults sign in locally.
- The content of the owner's other collection edits.

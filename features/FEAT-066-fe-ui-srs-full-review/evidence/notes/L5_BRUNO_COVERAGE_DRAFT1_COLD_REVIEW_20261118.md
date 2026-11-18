# FEAT-066 L5 Bruno coverage plan Draft 1 — cold review (round 1) — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, told effort high. It worked read-only by instruction. It was started by the coordinating session as part of A-5, after the owner said "viết A-5 đi". The scratch folder `tmp/feat066-bruno-review-d1/` was created and left empty.
- **Pin reviewed:** `plan/PLAN_L5_BRUNO_COVERAGE_DRAFT1_20261118.md`, 10,625 bytes, SHA-256 `06750F9A8F324FB282E688A03B73066FD070307697F0BF1C5B5664ABB4E9545B`. These also matched: P4, register Draft 4, seed Draft 6 and the SRS.
- **What the reviewer did not do (its statement):**
  - It ran no tests, builds, validators, Bruno, app, database, network or state-changing git.
  - It opened none of these: the gate secret directory, any `.url` or `.env` file, `environments/*.bru`, `firebase-auth-helper/*.bru`.
  - On the helper it only listed the directory and ran `git status` and `git check-ignore`.
  - Two recursive greps over `requests/` scanned the helper as part of the folder. The reviewer saw file names only and filtered the helper out.
  - It wrote nothing.
- **Verdict:** NOT READY — **P1=0, P2=7, P3=4**.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.
- **Note on the timing of B1-01:** after the review started, the coordinator replaced the token in `local.bru` and the helper's e-mail and password with placeholders, on the owner's word ("dọn cho tôi"). This was done by a script that printed no values. A scan of the collection afterwards found no JWT, Google API key, password value or `@gmail.com` address.

## P2 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| B1-01 | §0(c), §7 | Password rotation is conditional, yet the credential has been in an AI session context. The helper is not git-ignored (`git check-ignore` returned rc=1). `local.bru` is tracked and modified, so `git add -u` or `commit -a` would stage it. | Make rotation unconditional. Add a local exclude for the helper. Revert or clean `local.bru` before any other L5 step. Name the already-ignored `.env` as the safe home for `process.env` values. |
| B1-02 | §0, §2.1, §6 | No rule stops a token from being persisted into the environment file. Run reports from `bru run` probably contain request headers, including Authorization, and §6 keeps them in `tmp/`. | Tokens are runtime or `process.env` only, never persisted. Bruno secret vars are NV. Strip headers from run reports or do not keep them. |
| B1-03 | §2.2 vs §2.7 | Replacing `bearerToken` means editing the 86 existing requests that use it, which contradicts rule 7 and the owner's uncommitted edits. | Keep `bearerToken` for existing requests and use role variables in new requests only, or make the 86-file edit a separately approved step. |
| B1-04 | §1, L5-1 gate | A08 is a CB route and is gated on O-L3SCOPE in the register; the plan omits this. The 11 touched CB rows are missing from the scope table. "G0 for A17–A27" should list only A17, A20, A22, A26 and A27. | Add O-L3SCOPE where the register has it, and list the five rows. |
| B1-05 | §3 | Six problems in the case template:<ul><li>(a) The §9.8 envelope applies to errors only. §21.1 requires only the correlation header on every response.</li><li>(b) Stale-revision 409 applies only to profile, lesson plan, story and script (§21.4 line 1699; D-066-69 exempts accounts).</li><li>(c) The 401 variants `INVALID_TOKEN` and `TOKEN_EXPIRED` are missing.</li><li>(d) There are no key-format cases (1–128 visible ASCII characters, single value).</li><li>(e) The `request_id` alias is not checked.</li><li>(f) `{items, next_cursor}` is a conventions-plan proposal, not part of D-066-68.</li></ul> | Scope each check, add the missing cases, and cite the source of the page shape. |
| B1-06 | §2.2, §2.3, §2.5 | Missing tokens: one Parent token cannot test Parent isolation (P1/P2/P3), and there is none for the unassigned Teacher or the Teacher without an organization. There is no repeatability rule: positive commands mutate seed state, static keys replay durable receipts, and S3 and S4 are one-shot. Nothing stops Bruno from running against a non-local base URL. | Add the tokens. New requests create, change and delete their own data with a fresh key per run. Re-seed per run. Add a collection pre-request guard that aborts unless the base URL is loopback. |
| B1-07 | §3, §8 | Bruno has environments, not "profiles". `bru run` tag filtering is NV. Tags are per request, so each case needs its own file. "Exactly the known gaps" needs a pinned expected-failure list. | One request per case; tag support marked NV; define an expected-failure list file, or use two environments. |

## P3 findings (summary)

| ID | Finding |
|---|---|
| B1-08 | <ul><li>Name the paths of the 3 new C-P requests: M2 `/v1/parent/profiles`, not the legacy paths.</li><li>M09 is still OPEN (ledger O3).</li><li>Align the C-P gate wording with the register (O-MOB2, O-9, FEBASE, O-0). C-P negatives are probably baseline, not target, since M2 already has the envelope and key rules.</li><li>Add the K2 read case.</li></ul> |
| B1-09 | §2.4 states the sandbox finding as fact. Reword it: observed, not yet recorded as evidence; owner-run is chosen anyway. |
| B1-10 | <ul><li>Carry the inventory's refusal gaps: cancel (129) and the FE-disabled class create (007).</li><li>Give a disposition for M01, M06, M07, M12, M13 and M25.</li><li>The roadmap asks for one folder per role and slice; the plan has role folders only.</li><li>No total reconciles the plan with the register queues.</li></ul> |
| B1-11 | The `[STALE]` and `[DEV-ONLY]` labels would edit owner files. `ROLE_GUIDE.md` is untracked and owner-owned. Keep the labels in a new register file until the owner agrees. |

## Checks (reviewer)

- Counts:
  - 145 request files; 13 modified and 5 untracked paths;
  - stale requests 004/005 and the six `dev`-only files;
  - BRU-0 rows;
  - C-P: 8 operations, 3 missing, M11 PARTIAL;
  - 11 refusal rows;
  - 86 = 44 + 35 + 3 + 4.
- Status and error codes agree with SRS §9.8/§21.4 and D-066-68. The privacy case agrees with D-066-69.
- Seed links: org C at capacity, org G RESTRICTED, quota cases marked time-sensitive.
- §0 repeats no secret, and the plan has no local paths.

## Not verified (reviewer)

- Bruno CLI installation and behaviour: tags, secret vars, persisted variables, reports.
- Real status codes.
- How seeded adults sign in. Real Firebase accounts would conflict with the seed's no-real-identifier rule.

## Disposition by the coordinating session

Draft 1 is not edited. A Draft 2 that fixes B1-01 to B1-11 is proposed to the owner (round 2 of 5). The rotation advice in B1-01 is passed to the owner now.

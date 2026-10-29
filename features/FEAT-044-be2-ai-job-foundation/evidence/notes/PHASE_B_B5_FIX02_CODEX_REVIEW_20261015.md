# BE2-01 B5 fix02: Codex takeover, corrections and review — 2026-10-15

- Result: **PASS_CODE_AND_PACKAGE_REVIEW** for the bounded B5-R01/R02 corrections.
- State: **Q01/B5_FIXED_PENDING_RUNTIME_REVIEW**; both findings are
  **FIXED_PENDING_RUNTIME_REVIEW**, not closed. B6 **NOT_STARTED**.
- This supersedes the current-state conclusions of the original B5 review and the fix01
  checkpoint; their files, packages and before-proofs remain historical evidence.
- Same approved Phase B revision 3 scope, 14 business cards, WIP 1, full-card DONE 0.
  Parent BE2-01 remains IN_PROGRESS; B1–B4 and their closed corrections remain closed.

## Authority and exact checkpoint

The user explicitly authorized Codex to temporarily implement and hand back to Claude:

> :)))) tạm thời bạn làm đi tí bàn giao tóm tắt lại cho claude vì nó làm tới đây thì hết token nè

This is an executor continuation within the existing approved B5 correction scope. Original
Phase A/Phase B approval records, approved plans, ADR-0018 and decision record are unchanged;
the quotation does not manufacture another approval or P1/P2/P4 sign-off.

Worktree: `.worktrees/be2-01-ai-job-foundation`; branch
`feature/be2-01-ai-job-foundation`; base
`993a26cae78c0a4fe983033f03881838c886b176`.
Claude's fix01 source was verified against all 43 hashes of manifest
`831147fabe0ceb65f55a10cf128fae2dc143de314ebd7540347671a109e3e6a7`
before Codex changes. Claude had already corrected static-backlog starvation and implemented
strict canonical capability verification, added five unit regressions and one SQL regression,
built fix01 and completed its nine-case host checks. Those results are not remote runtime proof.

The last real Studio result remains the user-reported closed B4 run on
`sketch2life-backend-test`: manifest `f1c6834f`, 104 B2–B4 and 224 Phase A passed, zero skips,
all exit codes zero. Neither original B5 nor fix01 has a reported Studio execution.

## Remaining issues corrected within the same findings

**B5-R01:** Claude's keyset traversal correctly passes released failures, but could keep
chasing newly arriving intents indefinitely. A direct service/fake probe with two initial
rows and one new intent per delivery still needed a forced stop at delivery 13. The final
service captures `pending_side_effects_count()` once, then claims at most that many rows in
total, with `min(claim_limit, remaining)`, strict keyset continuation and fresh lease time
per page. SQL COUNT includes undelivered audit/quarantine rows, including leased rows, and
excludes dispatch rows; fake behavior matches. The same probe now returns after two deliveries
and leaves two new intents for the next call. Initial count is a finite work budget, not a
fixed-membership snapshot or a wall-clock deadline; concurrent arrivals cannot enlarge it.
No new table, migration, persisted cursor, retry policy, scheduler or queue was introduced.

**B5-R02:** Strict whole-token/base64url verification from fix01 is retained. Independent
held-out checks accept 100 valid capabilities and reject 300 noncanonical representations.
Two remaining filter cases were reproduced: capability text in mapping keys survived in a
structured LogRecord, and scrubbing `wcap.v1.%s` before interpolation removed its placeholder
and caused formatting to fail. The filter now formats the full message first, scrubs it,
clears arguments, and recursively scrubs mapping keys and values. Existing extra/exception/
stack scrubbing and removal of RQ argument extras remain. No raw bearer/key is published.

Exactly eight existing source/test paths changed relative to fix01: application port and
service; fake and SQL repositories; worker filter; the two B5 unit suites; SQL audit-durability
suite. Three new unit regressions and one new SQL regression were added. Lease generation,
stable event IDs, sink dedup, transactional completion/receipt/intents, owner-fence fixture
boundary and dispatch bookkeeping guarantees are preserved.

## Actual local verification

| Check | Direct result and limit |
|---|---|
| Three additional regressions on exact fix01 | 3 failed, exit 1; all 43 old source hashes verified before copying new test files |
| Same regressions on final source | 3 passed, exit 0; service/fake and actual log filter, no PG/Redis |
| B2–B5 runner-selected suite | 97 passed, 96 skipped, 193 collected; every skip is unrun PostgreSQL/Redis work |
| Phase A six suites | 223 passed, 1 skipped because local Pillow is missing; 224 collected |
| Fixture runner | 20 PASS, 215 checks, zero failed; optional HTTP surface NOT_RUN 1 |
| Fixture result digest | `d17f58a3c9c535d45a2fe03ed0c1edad42a565422725aede21b22ba45af41f68` unchanged |
| Ruff | PASS on exactly eight changed paths with normal per-file configuration discovery |
| mypy | PASS on 33 relevant source/test files |
| Harness/security/architecture/skeleton/diff | exit 0; final documentation checks recorded separately below |
| Package transport checks | 25 delta paths, 43 source hashes, four byte-identical ZIP members; forward/reverse/repeated-application checks PASS |
| Host runner simulation | 10/10 PASS with stub Docker; this is not PostgreSQL/Redis runtime evidence |

There are 57 B5 unit cases and 32 B5 PostgreSQL/Redis cases. Across B2–B5, 96 runtime cases
remain **NOT_RUN** locally. The local Python is 3.12.10 and RQ 2.11; the previously inventoried
Studio uses Python 3.12.15 and RQ 2.12. No dependency was installed or service started locally.
The first broad Ruff invocation with an explicitly supplied config classified imports
differently; its receipt is retained. The final Ruff claim is limited to the eight changed
paths with the same discovery used for their focused checks, not a repository-wide lint pass.

## Reviewed fix02 package

Local folder: `evidence/local/b5fix02-studio-package-20261015/`.

| Artifact | SHA-256 |
|---|---|
| Closed B4 input manifest | `f1c6834f41dc798fe4475509b7d4b9c8c578ebfd15f34ff07f72f2d4bf24aeb4` |
| `b5fix02_delta.patch` | `3049e1bbb6988161422e1187b68ac4e197cb95047b0a6fd22e13cb983359d0ba` |
| `b5fix02_source.sha256` | `cf196e845d30179c2aa2b89e09970ccaf83777aa6d90fac7b29f68d091ad60d0` |
| `run_b5fix02_on_studio.sh` | `65ec10bade2105254f46b5c2f400d2ebcf5d5ca733bb23fb208d5fdc65bbe767` |
| `be2-b5-fix02-studio-20261015.zip` | `8887a635fcd2b996982a762f539af9016c39d45903876ea4a2e7a7406e98e76e` |

The supported transition is exact closed B4 `f1c6834f` to fix02 `cf196e84`, or verification-only
retry of that exact fix02 source. Original unrun B5 `c7492097`, old fix01 `831147fa`, foreign
tracked/untracked edits, modified known files and corrupted patch are rejected before Docker.
Docker exit 125 propagates and the resulting source can be retried. Nothing resets, cleans,
deletes or overwrites an unknown source state. All 48 old package files remain byte-identical.
Scratch Git trees use `write-tree` without commits, are independent of the real index and
remain ignored evidence.

## Handover and exact next step

1. User uploads **fix02** to the same synthetic Studio and follows ignored operator prompt
   `evidence/local/claude/prompts/B5_FIX02_STUDIO_RUN_20261015.md`.
2. Capture manifest `cf196e84`, 193 B2–B5 passed and 224 Phase A passed, zero suite skips,
   every suite/tee/outer/Studio command exit zero and unchanged fixture digest. These are
   expected results, not observed results. Preserve complete output/receipts.
3. Review actual source-bound output before closing B5. Do not infer success from a previous
   ZIP, collection, mocked host pass or zero exit of `tee` alone. On mismatch, stop at diagnosis.
4. Claude resumes from ignored full handover §X and concise
   `evidence/local/claude/handover/CLAUDE_B5_CODEX_HANDOVER_20261015.md`, first reading/reporting
   the checkpoint. Do not reimplement B5 or automatically begin B6.

OwnerFence remains **ASSUMED_CONTRACT**, not real owner-adapter integration. Real P1/P2/P4
integration, full conformance/B6 and other BE2 cards remain future work. No real provider,
live app wiring, production policy, BE1-owned write, FEAT-018/Wan change, install, service
recreation, real-index staging, commit, push or deploy was performed.

Raw receipts are ignored under `evidence/local/b5-fix01-codex-takeover-20261015/` (capture,
service/security before/after and final tests) and `evidence/local/b5-fix02-20261015/` (builder,
collection, package and ten host cases). Matching public JSON records the exact eight-file
hash changes, 541-path preservation audit and final documentation validation. Operator prompts,
ZIPs, scratch work and handovers remain local and Git-ignored.

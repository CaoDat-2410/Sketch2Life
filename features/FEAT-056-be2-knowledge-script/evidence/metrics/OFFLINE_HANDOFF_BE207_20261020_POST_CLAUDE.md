# BE2-07 post-Claude offline handoff — 2026-10-20

State: `READY_FOR_OWNER_COMPONENT_REVIEW`. Component `NOT_ACCEPTED`; card `IN_PROGRESS / NOT_DONE`.
This revision supersedes the initial handoff's no-known-findings conclusion. The initial
map/checks/handoff and Claude's report remain unchanged historical evidence. Execution stays
within revision1/OD01–08 and its authorized review–fix–retest loops; frozen plan SHA256 remains
`6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36`.

## Finding dispositions

| Finding | Disposition |
|---|---|
| P2-1 | FIXED. Product tests no longer freeze572 shared backend bytes or a permanent07 test-file count. Separate evidence gates verify task-specific immutability and the recorded batch inventory; X01/X02 name the gates and supporting product assertions explicitly. |
| P2-2 | FIXED. Shared domain/DTO token comparison rejects punctuation, whitespace, zero-width format and full-width tiny variants, plus reverse containment. Comparison is conservative, can reject short factual phrases contained in imagined content, and does not detect all semantic/paraphrase/homoglyph variants. Stored text and canonical NFC are preserved. |
| P2-3 | FIXED. Real resolver tests cover wrong hash, unknown/other bundle id and wrong version; positive controls, exact denial, absent export and unchanged storage/commit count are asserted. The removed-hash-check mutant is caught. |
| P3-1 | FIXED. All six previously surviving service mutants are caught by actual assertions. Same-revision audience/source metadata, stale edit body pins and corrupt receipt body/readiness/status now have regressions; expected replay record/status derive from trusted version/requested contract. |
| P3-2 | FIXED. Exact unchanged claim-list resubmission retains the stored attestor and is a no-op; mixed edits preserve A's old claim while B owns new/changed claims. |
| P3-3 | FIXED. Mutation-only pause denies unseen writes; current eligible reads/exact exports and accepted replay remain available. All other disclosure, purpose, membership, consent, basis, audience, source, policy and exact-pin guards remain. Queued pause publication follows the original held-unit linearization. |
| P3-4 | INTENTIONAL UNDER FROZEN R01. Recall before a new unit denies command/resolve, including in-place repair. Create a new bundle from eligible reviewed sources. The denial and new-bundle remedy are tested; no rebase scope is added. |
| P3-5 | FIXED. No claims → NO_ELIGIBLE_SOURCE; claims without fact sections → FACT_SECTION_REQUIRED; ready → no action. Record/resolver agree and strict DTO rejects contradictory pairs. Unavailable requires an explicit bounded action and is never the default persisted-record result. |
| P3-6 | FIXED WITH FROZEN-RECORD EXCEPTION. Routing docs have H1 first/searchable current labels; two note CRLF lines were explicitly normalized with before/after hashes. Hygiene now scans untracked publishable text too. The original approval's trailing blank line is preserved with exact hash, rather than changing authorization history. |

The preserved approval hash is
`0010271d9db68dbbe8b9675021540df3e2cd420f636c0f7a8113ea9b91da2078`.
There is no blanket assertion that every cosmetic P3 was removed. The original all-zero-claim
handling of mixed valid+unknown catalog selection remains a documented fail-closed clarification;
explicit unknown structured fact/imagined refs still reject.

## Verification

The completed product snapshot passed262 focused07 tests, no skips. An independent product
reviewer reran262 and found no remaining concrete product P1/P2/P3. Independent copy experiments
collected262 for every mutant: all six were killed by real assertions, with no import/collection
errors. A harmless comment in copied `assistance.py` left the product suite passing262, while
the extracted evidence baseline assertion detected exactly that changed file. No real source
was modified by the experiments. Pre-fix assertion failures and all raw probes are retained.

Final required01–07 batch: **1,587 collected; 1,584 passed; 0 failed/errors; 3 skipped**.
The selection is50 unchanged baseline files plus6 current07 modules; the evidence tool derives
the current07 inventory. All42 acceptance rows pass offline with354 exact passed JUnit-node
references and15 unique evidence references. X01/X02 have explicit evidence-gate classifications;
no synthetic pytest case replaces the removed unit invariant.

Ruff, evidence-script Ruff, normal/fresh-cache strict mypy, harness/security/architecture/skeleton
validators and tracked `git diff --check` all exited0. The separate text audit covers new/untracked
publishable files with the one frozen approval exception. Three existing Pillow live-app checks
remain skipped/NOT_RUN; the Pillow-importing V2 server test remains excluded/NOT_RUN. No dependency
installation, live provider, database, HTTP server or Lightning execution occurred.

Source/config/tooling manifest:601 entries, SHA256
`eee3e905f008ce65fad341fc34aa47c28d28f5cdf1ecc7c68ba8c98023b792a3`.
Raw JUnit SHA256: `73b80e03d801fa83f1f61453d610834eb4f2525d3ab38ec1ae7ef735cf31be7d`.
Finalization rechecks the exact current file set, sizes/hashes, raw XML identities/status/counts,
command/log receipts and profile/baseline pointers before publishing these new files.
The examples artifact remains SHA256
`0f06aeace8bd0dd50e53096c2f0782a83001e47963c0383e180f117501b90f2c` with JSON-value equality.

The evidence-only invariants preserve572 original backend files,3,309 other tracked files,
frozen approval/plan/prior final evidence, empty index and original HEAD. External invariants
preserve356 main files,1,243 shared-worktree files and6,112 A17 files. The raw external baseline
is available at `evidence/local/execution-baseline/external-before.json` (SHA256
`dea79e2656412d627e27562fa22904e66ac777fcd7074b419da4e5b26192376e`). Pre-fix snapshots and the
explicit restoration of the historical atomic review are retained under
`evidence/local/claude-remediation-20261020/`; the historical atomic review is again its exact
previously audited SHA256 `ee6375258272db67b03b0c0b79e48345137925761276e8427f5e98812585e20a`.

## Review records and boundaries

- [Post-Claude acceptance map](ACCEPTANCE_MAP_BE207_20261020_POST_CLAUDE.json)
- [Post-Claude aggregate checks](BE207_FINAL_OFFLINE_CHECKS_20261020_POST_CLAUDE.json)
- [Remediation plan and receipts](../notes/CLAUDE_REMEDIATION_20261020.md)
- [Independent post-Claude review](../notes/INDEPENDENT_POST_CLAUDE_REVIEW_20261020.md)
- Raw final receipts: `evidence/local/final-offline-post-claude-20261020/`
- Independent mutant receipts: `evidence/local/service-mutants-independent-20261020-878d82f4/`

Final independent audit confirms all42 plan IDs,354 mapped entries (210 unique source test nodes),
raw JUnit/counts,601 source entries,11 command receipts, all evidence refs and external/hygiene
gates. It found no new or undispositioned P1/P2/P3; the P3-4 R01 limitation and P3-6 frozen approval
exception remain explicit. The final review note SHA256 is
`d53b544b09b2c0e248dee3f988d59d8b788114fa8f5573b8b81442d6dfb3395d`.
Final post-output validation receipts are kept in
`evidence/local/final-offline-post-claude-20261020/post-output-verification/`.
Owner component acceptance and runtime adoption remain separate. Real BE1 authority/source adapters, durable
SQL/HTTP, live providers and actual08 held lease/fence/delivery are still open; frozen A17 Studio
remains NOT_RUN. No stage, commit, push, PR, merge, deployment or Lightning run was performed.

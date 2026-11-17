# Independent product review after Claude remediation — 2026-10-20

**Verdict: no remaining P1/P2/P3 findings in the reviewed BE2-07 product source and test scope.**
This is an independent read-only review against `plan/PLAN_REV1_APPROVED.md` and
`evidence/notes/CLAUDE_REMEDIATION_20261020.md`, comparing the current implementation with the
preserved pre-fix copies under `evidence/local/claude-remediation-20261020/before/`. I did not
edit product source or tests. P3-6 is documentation/evidence hygiene and is outside this product
review; it remains with the evidence owner/final audit.

I inspected the actual assertions, not just the test names. P2-1's permanent 572-file/profile
assertion was removed from the unit suite for evidence-runner ownership. P2-2 now uses one
comparison-only NFKC/casefold helper that removes format controls, normalizes whitespace,
compares punctuation-boundary and punctuation-stripped token signatures in both containment
directions, and leaves stored text/canonical bytes unchanged. Tests cover empty signatures,
token-boundary controls, diacritic distinction, punctuation/whitespace/format/fullwidth
variants, reverse containment, and DTO/service enforcement. P2-3 calls the actual exact resolver
with wrong hash, unknown ID, another bundle ID, and wrong version; it asserts the valid control,
denial with no export, unchanged snapshot, and unchanged commit count.

P3-1 has handler assertions for same-revision audience/source changes, both stale edit revisions,
and corrupted receipt body/readiness/status. Replay derives its expected record and status from
the trusted version and contract and checks the receipt key. P3-2 preserves an unchanged prior
claim attestation on claims-list resubmission, proves a true no-op, and proves a mixed edit keeps
the original Teacher on the old claim while attributing the new claim to the authenticated
Teacher. P3-3 removes only the mutation pause from read/resolve; parameterized race tests retain
the other 14 current guards. A pause published during a held unit stays queued under R02, the
accepted unit commits, subsequent new writes are denied, and accepted replay remains historical
and disclosure-checked. P3-4 retains frozen R01's fail-closed recall behavior: in-place source
repair is denied and a new bundle with eligible reviewed sources succeeds. P3-5 derives the
no-claims, claims-without-fact, and ready action states; DTO tests reject contradictions, require
an explicit bounded action for `unavailable`, and confirm the default producer never emits it.
Read/resolve returns the structural content action without exporting content; current-read
guard failures expose no record/export. The producer-example equality test also passed against
the unchanged saved artifact.

I independently reran the six BE2-07 contract/unit files from this worktree with the existing
backend virtualenv and no cache provider or dependency/network operation. Result: exit 0,
262 passed, 0 skipped, 0 failures/errors. JUnit: `evidence/local/reviewer-postclaude-20261020/junit.xml`;
log: `evidence/local/reviewer-postclaude-20261020/pytest.log`. All nine reviewed source/test
files exactly match the focused run's `source-after.json` manifest.

Exact SHA256 evidence:

| File | SHA256 |
|---|---|
| `backend/src/sketch2life/domain/knowledge_bundle.py` | `7d8a6ab8b802917e22abc146fab34cb78c7d6152b7425a42ff88778b5ada4e3a` |
| `backend/src/sketch2life/contracts/schemas/knowledge_bundles.py` | `25e3486a3a6557eadc03c1b6db4ed4f95ef325db347d38f9dfa1f1e5a88927c1` |
| `backend/src/sketch2life/application/services/knowledge_bundle.py` | `af6c3c55e3cf0fedf155b8c0ebbf720ef7e6aec121b5b1871f94191a1e2f6c9f` |
| `backend/tests/contract/test_knowledge_bundles.py` | `9592444b4e8551b540be9fb904ba3cb96b4c0f67012b61226a1bc631f6999448` |
| `backend/tests/unit/test_knowledge_bundle_adapters.py` | `e9ed452a0cdea915f016d05e1e54c440c8ff5d3ec1169f2ac37d900d3537e61d` |
| `backend/tests/unit/test_knowledge_bundle_chain.py` | `ad446875823596879cd8d8237b3d02c1589ca633b3c182c17c7b5a8208a200d7` |
| `backend/tests/unit/test_knowledge_bundle_domain.py` | `db52a05f463c886e92b9669ef7f31d746bc38da2002b4e4b190e966bea304812` |
| `backend/tests/unit/test_knowledge_bundle_races.py` | `0f4979d39d13489959a40db10d9c2c2032af9e82b533f6c3736c94f9d6324e43` |
| `backend/tests/unit/test_knowledge_bundle_service.py` | `97dafef9de0aba207ae7487e727b38ef4a9dfe415b5a5d232f6a100805d3a2e3` |
| `evidence/local/claude-remediation-focused-20261020/source-after.json` | `66d436fdf35570ee3f31a405531695c1a984c70bb3f7a038da9d9df7b9abf818` |
| `evidence/local/reviewer-postclaude-20261020/junit.xml` | `3590cb29e58c3ab001cc377bc7306c733676c56ad7e267ff9fdcd749de606d08` |
| `evidence/local/reviewer-postclaude-20261020/pytest.log` | `6dadfe41b0e32b496c04c905acb613d5a198a12369b93fc7ff468c48b275ee0d` |
| `artifacts/KNOWLEDGE_BUNDLE_EXAMPLES.json` | `0f06aeace8bd0dd50e53096c2f0782a83001e47963c0383e180f117501b90f2c` |
| `evidence/local/part8-examples-generation.json` | `1d252a055823f77cb15bfa6a41d0913fc955b36785783e593ad82bea609e5f87` |
| `plan/PLAN_REV1_APPROVED.md` | `6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36` |
| `evidence/notes/CLAUDE_REMEDIATION_20261020.md` | `42cb077e7074b437b89dd77f171c1172ad9716f415a6788fe01b8403f91b7442` |

This review does not claim owner acceptance, runtime adoption, HTTP/database/provider execution,
or Lightning execution. The final map/JUnit and evidence-hygiene audit remains separate.

## Independent final offline map/JUnit audit — 2026-10-20

**Verdict: no new or undispositioned P1/P2/P3 finding in the post-Claude final batch or its
acceptance map.** I independently parsed the raw JUnit XML and summary, checked the actual
approved-plan IDs and test source, rehashed the captured source manifest against the current
worktree, and verified the referenced evidence. This is an offline evidence audit; it does not
claim owner acceptance, runtime adoption, or product acceptance.

The approved plan has 42 acceptance IDs and the post-Claude map has the same 42 IDs in the same
order. All 354 mapped final-node occurrences (210 distinct names) correspond exactly to the
map's source-node entries, exist as actual test functions, and match passing raw JUnit cases;
none is hidden by a skip. XML and summary agree on 1,587 collected, 1,584 passed, 0 failed,
0 errors, and 3 skipped. The three skips are the explicitly named Pillow-dependent live-app
tests, with reasons recorded in the final checks. The separately excluded V2 server module is
absent from the 56-file selection and is explicitly marked NOT_RUN.

The selected profile is the frozen 50-file baseline plus all 6 current BE2-07 test files.
All 11 command receipts exit 0, and their receipt/log SHA bindings match the files: collection,
pytest, Ruff, evidence-script Ruff, strict mypy, fresh-cache mypy, harness, repository security,
architecture, skeleton, and diff check. The profile gate, source/tracked invariants, external
invariants, and text-hygiene evidence also pass. Independent rechecks matched 356 main-worktree
files and status, 1,243 shared-worktree files and status, and all 6,112 frozen A17 files. The
12 protected approval/plan/prior-evidence records match their frozen hashes, with the separately
recorded historical review-note restoration hash. Repository security validation after the
metrics existed scanned 3,375 publishable files, reported no absolute machine paths, and reported
environment, seed-account, credential/signing-key, and external-reference files excluded by policy.
The publishable metrics themselves contain no absolute path or credential-like value. No source,
test, plan, approval, or frozen historical evidence was edited for this audit; only this designated
independent review note was appended. I also rescanned the current 54-file hygiene scope, including
the two post-batch metrics and post-batch handoff: all passed UTF-8/LF, BOM, trailing-whitespace,
and routing-heading checks except the same frozen approval trailing-blank exception at its exact
recorded hash.

The following disclosed dispositions remain in force and are not blanket-closed as P3s:

- **P3-4 / frozen R01:** recall denies repair of the recalled bundle in place; a new bundle from
  eligible reviewed sources is the documented remedy.
- **P3-6 / frozen approval:** the approval file retains its pre-existing trailing blank line at
  SHA `0010271d9db68dbbe8b9675021540df3e2cd420f636c0f7a8113ea9b91da2078`; no approval bytes
  were edited. The other scanned publishable text passed the recorded hygiene checks.

Exact final evidence SHA256 values:

| Evidence | SHA256 |
|---|---|
| `evidence/metrics/ACCEPTANCE_MAP_BE207_20261020_POST_CLAUDE.json` | `7ab02e13d4b8a936a07ee14bd303e0e4363beb92e0fabfa94bbe123116ff9b9d` |
| `evidence/metrics/BE207_FINAL_OFFLINE_CHECKS_20261020_POST_CLAUDE.json` | `767dccb97189edf4a4070d574339ab95ae5a597654f501383ce60d658ec12520` |
| `evidence/local/final-offline-post-claude-20261020/junit.xml` | `73b80e03d801fa83f1f61453d610834eb4f2525d3ab38ec1ae7ef735cf31be7d` |
| `evidence/local/final-offline-post-claude-20261020/junit-summary.json` | `c744f4bfdee5820d5b9120fbcbbac7da5d24a698c5424071e0208c83548619fd` |
| `evidence/local/final-offline-post-claude-20261020/source-before.json` | `eee3e905f008ce65fad341fc34aa47c28d28f5cdf1ecc7c68ba8c98023b792a3` |
| `evidence/local/final-offline-post-claude-20261020/source-after.json` | `eee3e905f008ce65fad341fc34aa47c28d28f5cdf1ecc7c68ba8c98023b792a3` |
| `evidence/local/final-offline-post-claude-20261020/checks.json` | `05826481f07a66993f6fca7fd2cd21cb87806aa8be49207062883768851c6eb0` |
| `evidence/local/final-offline-post-claude-20261020/selected-files.json` | `daaba05409651d6883a522347904aeb383999d7eeae4a10add0d4914096be430` |
| `evidence/local/final-offline-post-claude-20261020/external-invariants.json` | `b53597ce879cea2c4f00239536b574c0db446fb37c02938b9d8defa35980892e` |
| `evidence/local/final-offline-post-claude-20261020/text-hygiene.json` | `0eec08774c62ec55e5de5dfb719fc05b06393ca202c0e6442c7256fa75e591fa` |
| `evidence/local/execution-baseline/external-before.json` | `dea79e2656412d627e27562fa22904e66ac777fcd7074b419da4e5b26192376e` |
| `evidence/local/execution-baseline/required-01-06-files.json` | `09b25261a8b6dea6c9dba63db0df30e23982d4ec62f7f0d41984d1a300f132db` |
| `artifacts/OFFLINE_BATCH_PROFILE.json` | `b2be18585c72a71fb0cadfa69c2d4528aed50541107e84a43904f52e705b0580` |
| `plan/PLAN_REV1_APPROVED.md` | `6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36` |
| `approvals/TASK_APPROVAL.md` | `0010271d9db68dbbe8b9675021540df3e2cd420f636c0f7a8113ea9b91da2078` |

All 15 map evidence references exist. The acceptance map and publishable checks contain no
absolute machine paths or credential-like values. The map keeps the limits explicit: the three
Pillow skips and V2 server exclusion are NOT_RUN; no live source, provider, database, HTTP,
Lightning, or actual08 held-fence execution is claimed; and component acceptance remains
unaccepted. The profile and all final receipts point to
`evidence/local/final-offline-post-claude-20261020`.

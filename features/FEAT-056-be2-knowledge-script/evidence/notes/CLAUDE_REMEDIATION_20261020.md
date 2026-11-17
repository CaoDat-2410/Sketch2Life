# BE2-07 Claude review remediation — 2026-10-20

## A — Plan before changes

Authority remains the original revision1/OD01–08 approval and its review–fix–retest scope.
Frozen plan and approval bytes are preserved. Claude's read-only report is retained at
`evidence/local/claude-review-20261020T044951Z/REVIEW.md`. It reports three P2 and six P3;
earlier no-known-findings conclusions describe the previous reviewed snapshot only.
The original final batch/map/checks/handoff remain historical evidence and will not be overwritten.
Pre-fix files and tracked diffs are copied into `evidence/local/claude-remediation-20261020/`.

| Finding | Planned action and verification |
|---|---|
| P2-1 | Remove permanent shared-file hash/profile assertions from the backend unit suite. Execute them in the feature-local evidence runner; map X01/X02 to real evidence gates plus relevant product assertions, naming each proof's scope. Derive current07 inventory rather than permanently freezing its count. |
| P2-2 | Use one shared conservative literal-overlap helper in domain/DTO: comparison-only NFKC/casefold, drop format controls, normalize whitespace, compare punctuation-as-boundary and punctuation-stripped token signatures in both containment directions. Preserve stored text and canonical hashing. Regression covers tiny variants, reverse containment, empty signatures and token-boundary positive controls. This remains a literal heuristic, not semantic/paraphrase detection. |
| P2-3 | Actual resolver regressions for wrong hash, unknown/other bundle id and wrong version; assert denial/no export/no writes and a valid-pin control. Independently kill the removed-hash-check mutant. |
| P3-1 | Handler regressions for same-revision audience/source-record changes, both stale edit expected revisions and corrupted receipt body/status. Derive accepted receipt shape/readiness/action and command status from its trusted version/contract, not the possibly corrupted response fields. Rerun the six surviving mutants on copies/in-memory. |
| P3-2 | Preserve original attestation when an unchanged claim is resubmitted in the claims list. Changed/new content is attributed to the authenticated editing Teacher; assert no-op and mixed original/new authorship. |
| P3-3 | Drop only mutation_allowed from read/resolve. Keep all current disclosure, basis/confirmation/applicability, audience/age, contributor purpose/membership/consent, source/policy and exact version/hash guards. Unseen create/edit retain pause checks inside the coordinated unit: visible pause denies; publication while the boundary is held stays queued under approved R02 and becomes visible after commit/rollback, then denies new writes. Paused reads/exact resolve remain available only while every other guard passes; replay stays historical and disclosure-checked. |
| P3-4 | Intentional limitation under frozen R01: recall before a new final unit denies command/resolve, including in-place repair. Preserve fail-closed behavior; document that a new bundle using eligible reviewed sources is required. Add explicit denial/new-bundle regression and do not expand scope to rebase. |
| P3-5 | Derive structural readiness/action consistently: no claims → needs_content_action/NO_ELIGIBLE_SOURCE; claims without fact sections → needs_content_action/FACT_SECTION_REQUIRED; ready → no action. Strict DTO rejects contradictory pairs. Existing unavailable requires an explicit nonempty bounded reason/action; default record producer never emits it and current-read failures expose no record/export. Resolver returns the matching content action. Test the full state/action table, record output and resolver denial/export. |
| P3-6 | Restore H1-first routing docs while preserving historical body bytes, use searchable current feature labels, and explicitly record note EOL normalization. Add an evidence whitespace audit covering untracked publishable files. Preserve the approval record's frozen trailing blank line as a documented exception rather than edit authorization history. |

Create's missing-source draft is covered by §4.4/P03. The mixed valid+unknown catalog-selection
behavior is a retained fail-closed clarification, supported by the existing
`test_missing_source_create_is_zero_claim_draft_with_content_action[mixed_selection]` regression;
the frozen text does not explicitly prescribe that mixed case. It emits no partial factual
content/provider call. Explicit unknown fact/imagined section refs remain rejected under N02.
No blanket claim that the mixed-selection rule is verbatim approved is made.

## Ownership and review sequence

Root owns service/race/service+chain tests, evidence tooling, routing/handoff and mapping.
Domain author owns the literal/readiness helpers, strict DTO changes, domain/contract tests.
Atomic reviewer may add resolver regression tests in adapters after mini-plan review.
Independent final reviewer checks this plan before source changes and re-reviews fixes afterward.
No simultaneous edits to an owned file; reviewers do not edit product source during review.

## B/C — Required verification and handoff

First record focused failures/probes, then fixes and targeted passes. Independently verify
mutation regressions and actual assertions, not just passing test names. Regenerate examples
only if producer values change; preserve previous artifact/receipt bytes in the pre-fix copy.
Pin the completed source/config/tooling snapshot and run the required50 baseline plus current07
offline batch, Ruff, both strict mypy modes, four validators, tracked diff and untracked-text
whitespace/EOL audit. Recheck original572/shared/approval/plan/history/A17 invariants with raw
baseline refs available for independent verification. Preserve all skips/exclusions as NOT_RUN.

Emit a new post-Claude map/checks/handoff revision and retain the previous files. Record each
finding as fixed, disproved with evidence or explicitly dispositioned; do not use a blanket
no-P3 claim while an exception remains. Restore READY_FOR_OWNER_COMPONENT_REVIEW only after
independent review and affected retests. Component NOT_ACCEPTED/card IN_PROGRESS / NOT_DONE;
no stage, commit, push, PR, merge, deploy, install, provider or Lightning execution.

Plan review: PLAN_REVIEW_PASS by independent final reviewer after the three bounded
clarifications above (guard preservation, full state/action table and mixed-selection wording).
Source changes start only after that verdict. Focused/final receipts and C review follow below.

## B — Implemented checkpoint

The domain/strict DTO pre-fix regressions produced18 concrete assertion failures; root service
regressions independently produced5 expected failures (unchanged claim attribution, paused
read, story-only action, corrupted receipt readiness/status). Raw failures remain in
`evidence/local/claude-remediation-domain-20261020/` and
`evidence/local/claude-remediation-20261020/root-prefix/`.

Completed product snapshot:262 focused tests passed,0 skips, Ruff and both strict mypy modes
passed in `evidence/local/claude-remediation-focused-20261020/`. The examples artifact's JSON
values remain identical and its SHA256 stays
`0f06aeace8bd0dd50e53096c2f0782a83001e47963c0383e180f117501b90f2c`.
Product C reviewer independently reran262 tests and inspected actual source/assertions; its
verdict and exact product hashes are in `INDEPENDENT_POST_CLAUDE_REVIEW_20261020.md`.
It found no remaining concrete P1/P2/P3 in product scope; documentation/evidence are a separate audit.

P3-4 remains the intentional R01 denial/new-bundle requirement. P3-6 normalization is explicit
in `evidence/local/claude-remediation-20261020/document-edits.json`; the frozen approval's
trailing blank line is preserved as an audited exception. Follow-up assessment/authored test
notes were relocated to `CLAUDE_RESOLVER_REGRESSION_20261020.md`; the earlier atomic review was
restored to its exact audited SHA256 `ee6375258272db67b03b0c0b79e48345137925761276e8427f5e98812585e20a`.
Both in-flight bytes and the restoration/move receipts are retained locally. No prior final
map/checks/handoff or approval/plan bytes were overwritten.

Independent service-mutant checks now pass: all six previously surviving mutants were killed
by actual assertions, each collecting262 cases with no import/collection errors. The baseline
copy and harmless-comment copy both passed262; the runner's extracted baseline assertion
passed before the copied comment and failed afterward, naming only that file. Real588
source/test files stayed byte-identical. Exact nodes/logs/JUnit/receipts are in
`evidence/local/service-mutants-independent-20261020-878d82f4/`.

Evidence tooling received read-only independent review. Its stale-batch publication gap was
closed before final execution: finalization now binds the exact current source/config/tooling
file set and every hash/size, generator pin, raw JUnit identities/status/counts/hash, individual
command/log receipts and profile/baseline pointers. Re-review found no concrete blocker.
Reviewed runner SHA256 `4761c957f3c666380061e9930c5ba327b0adeb916a690dd028daee369ec0f893`;
finalizer SHA256 `234c857fa071c09a9c4e03bf6ad976c0581583c3d8a6ab8eb93eeb681742810d`.
X01/X02 explicitly distinguish evidence gates from supporting product assertions; they do not
invent JUnit cases for the removed unit invariant.

## Final batch and evidence checkpoint

`evidence/local/final-offline-post-claude-20261020/` completed with1,587 collected,
1,584 passed,0 failed/errors,3 Pillow skips. All11 command receipts exited0; baseline/history/
external/text gates passed. Source/config/tooling manifest601 entries has SHA256
`eee3e905f008ce65fad341fc34aa47c28d28f5cdf1ecc7c68ba8c98023b792a3`;
raw JUnit SHA256 `73b80e03d801fa83f1f61453d610834eb4f2525d3ab38ec1ae7ef735cf31be7d`.
New POST_CLAUDE map/checks retain42 passing offline rows with354 passed exact JUnit references.

Independent finalizer fault probes passed5/5: a mirrored valid control generated42 rows;
new-manifest-entry, changed XML, changed command log and preexisting-output cases each rejected
at the expected real guard before writing new outputs. Real641 source/evidence/authorization
files remained unchanged. Raw probe/receipts are in
`evidence/local/reviewer-finalizer-binding-20261020T053028Z/`. This is evidence-tooling proof,
not an additional product test rerun.

## C — Final independent audit and handoff

The final reviewer independently reconciled all42 plan IDs,354 mapped entries/210 unique test
nodes, raw JUnit/counts, all601 current source entries,11 command receipts, profile/evidence
refs, external baselines and54-file publishable hygiene. No new or undispositioned findings
remain. Its new review note has SHA256
`d53b544b09b2c0e248dee3f988d59d8b788114fa8f5573b8b81442d6dfb3395d`.
Three P2 are fixed; P3-4 remains the intentional frozenR01 limitation and P3-6 retains the
frozen approval EOF exception. Current state is READY_FOR_OWNER_COMPONENT_REVIEW; component
NOT_ACCEPTED/card IN_PROGRESS / NOT_DONE. Final post-output security/diff/text/source receipts
are under `evidence/local/final-offline-post-claude-20261020/post-output-verification/`.

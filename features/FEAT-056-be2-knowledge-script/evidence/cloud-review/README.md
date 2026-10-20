# Portable BE2-07 review evidence

This export supports source review on the published task branch. Run from any checkout:

```sh
python features/FEAT-056-be2-knowledge-script/evidence/cloud-review/verify_evidence.py
```

Use `--expected-commit <published-commit>` to bind the checkout to the requested review commit.
The verifier uses only Python's standard library. It verifies historical evidence consistency;
it does not execute product tests or grant owner acceptance.

## Provenance and sanitization

`EXPORT_PROVENANCE.json` binds every exported payload to its original repository-relative
path, SHA256 and byte count, plus the exported SHA256, size and exact transformations.
Original local files remain untouched. Sanitized XML has its own hash; the unchanged summary
and acceptance map intentionally retain the original local XML hash. The verifier checks both
bindings and compares all 1,587 testcase identities and statuses. Known worktree/interpreter
prefixes become explicit placeholders; machine hostname attributes are removed from XML.
No tokens, credentials, original workbooks/handbooks or real child data are included.

The local `.gitattributes` preserves all evidence bytes across Git checkouts. Historical log
receipts retain their original line endings and are marked `-diff`; inspect their readable
files and the original/export hashes in provenance. Source, JSON, XML, Markdown and this
verifier remain text diffable. This rule preserves log proof bytes; it does not suppress
source review or authorize editing historical data to satisfy whitespace checks.

The original Claude report is a verbatim historical finding report, before the corrections.
The current disposition and independent review are the published feature notes and POST_CLAUDE
handoff. This export does not turn an old CHANGES_REQUIRED report into a new reviewer verdict.

## What is checked now

- Exported bytes, 601-entry equal historical manifests and selected56 test files.
- Current product16 source/test files, examples artifact and frozen plan/approval bytes.
- Historical batch: 1,584 passed, 3 Pillow skips, 0 failures/errors;42 acceptance rows with354
  exact passed node references. This is historical execution evidence, not a fresh cloud run.
- Eight copied focused suites: baseline262pass, harmless-comment262pass and six guard-removal
  mutants with executed assertion failures and no import/collection errors. Delta source hashes
  bind each mutant to the current service. The harmless-comment gate is the actual extracted
  backend-baseline assertion, not a full evidence runner execution.
- Eleven command receipts match their aggregate; each historical log hash binds its original
  local bytes and the export inventory independently binds sanitized log bytes.

## Deliberate limits

The 601-file manifests are exact immutable historical receipts. Their ignored `evidence/local/`
references include local runner scripts, pre-fix metadata and baseline snapshots. Tools are
exported for reading under `historical-tools/`; their old file locations/HEAD/index requirements
make them unsuitable for direct execution after publication. This export does not recreate
the original worktree. Run focused product checks with a new review directory and local
dependencies if available; report missing dependencies as NOT_RUN.

Do not claim full current verification of all601 historical entries. Routing/status/context,
publication and some review documents evolved after the historical test run and are not
frozen by `current-product-pins.json`. Foreign checkout snapshots, tracked-before baselines,
pre-fix source copies, caches, pytest temp outputs and external originals remain local.
`external-invariants.json` and related invariant counts are historical claims:
**NOT_VERIFIABLE_ON_CLOUD** because their omitted foreign baselines and checkouts are absent.
Historical source/profile refs that still name ignored local files are references, not missing
publishable files to invent. The new export inventory supplies portable bindings separately.

Three Pillow skips and excluded `test_lightning_vision_v2_server.py` remain NOT_RUN. No cloud,
provider, DB/HTTP, Lightning, multi-process or actual08 adoption/fence proof is supplied.
Component NOT_ACCEPTED; card IN_PROGRESS / NOT_DONE. Owner acceptance remains separate.

[Cloud review prompt](CLOUD_REVIEW_PROMPT.md) is a current workflow instruction outside this historical
payload inventory. Trust the verified Git commit for that document and the provenance file.

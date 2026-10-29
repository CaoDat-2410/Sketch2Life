# Independent cloud P3-N1 product review — 2026-10-20

Verdict: **NO_BLOCKING_FINDINGS** for the P3-N1 product correction. No new actionable
P0/P1/P2/P3 was found in the five-file product/test diff against published commit
`f0359c4fbb7c3f4a35dd3f2265559779a17951e9`. This reviewer did not author that correction.
The separately authored P3-N2 verifier correction is outside this independent verdict.

## Reviewed behavior

The domain retains the existing comparison-only Cf policy and adds the exact merged Unicode
15.0 Default_Ignorable_Code_Point property ranges. I independently checked the numeric
property records against the official
[Unicode 15.0 DerivedCoreProperties source](https://www.unicode.org/Public/15.0.0/ucd/DerivedCoreProperties.txt).
The implementation and independent source-derived set agree on all 4,174 points.

Filtering before NFKC removes CGJ before it can inhibit composition of a Vietnamese base and
accent. Filtering after normalization/casefold and final NFKC preserve the same comparison
policy for compatibility forms. Ordinary combining marks remain significant; no stored text
or canonical serializer is rewritten. Domain imports remain standard-library/domain imports,
and the strict DTO calls the shared domain Cc predicate. C0, DEL and C1 controls reject, with
LF and TAB preserved as allowed input.

Tests exercise both obfuscated sides through domain projection and strict full-basis DTO,
and actual service edits reject against the full trusted imagined metadata even after the
selection is removed. The real handler tests compare the complete repository snapshot and
commit counter after denial. These assertions cover no-write behavior and existing exact
export/readiness guards continue to run in the full focused suite.

## Fresh independent evidence

Raw files are under `evidence/local/reviewer-cloud-p3-product-20261020/`:

- `focused-receipt.json`, `focused.log` and `junit.xml`: all six task07 modules, **338 passed,
  0 failures/errors/skips**. Eight reviewed source/test files have equal before/after manifests.
- `junit-summary-verified.json`: all 262 exact historical task07 identities from the published
  batch remain present and passed; the current focused run adds 76 nodes. An initial lineage
  comparison used the copied mutant suite's different `backend.tests` namespace and is kept
  as `junit-summary.json`; it is a comparison error, superseded by the exact historical batch
  comparison, with no raw JUnit edits or extra product rerun.
- `probe_unicode.py`, `probe-receipt.json` and `probe-summary.json`: independent in-memory
  policy/property, literal, token-boundary, Vietnamese, control and preservation probes.

The probe enumerated the 4,174 official points and all 170 runtime Cf characters, a union of
4,206 unique points. Every point passed both comparison directions when inserted within a
word and between a decomposed Vietnamese base/accent: 16,824 positive overlap comparisons.
Each point also passed a token-boundary negative control and an empty-signature negative
control. Fourteen further bidirectional controls and eight ordinary combining-mark controls
passed. All 63 forbidden Cc points reject in domain text validation and in both DTO text
fields, giving 126 DTO rejections. Original submitted text including LF/TAB, combining marks
and CGJ is retained exactly.

Bindings:

- Focused raw JUnit SHA256: `78385803d3f1089d23293b1f409439919123e1c5e070d672af694f8b3fffd1f0`.
- Equal eight-file manifests SHA256: `0364626766370f83a907ed7221244f1a776d7f15500a58b3dd2179ef1225e566`.
- Probe driver SHA256: `f5890ec3f88289764832c18eeb23f0bfe559343de2410cb1e97bdb86d1cd465d`.

After this focused run, the root agent applied Ruff's one-assignment line wrapping in
`test_knowledge_bundle_domain.py`. I reconstructed the exact tested prior bytes, matched
their prior SHA256 and verified AST identity excluding source locations. The other seven
reviewed files stayed byte-identical. `format-ast-proof.json` and `format-only-refreeze.json`
record that verification; the final eight-file manifest is `source-after-root-format.json`,
SHA256 `61aa04940431cd09949c2fc0e7aff72f93d15b6ec4308f26277871d5769dd26e`.
The parent final batch will cover those final formatted bytes; this focused run is not
misrepresented as having run after the whitespace change.

## Limits

The exhaustive probe is exhaustive only for the stated Unicode property/Cf insertion model,
not arbitrary Unicode transformations, semantic claims, general homoglyphs or paraphrases.
The literal policy can conservatively equate default-ignorable emoji/complex-script variants;
the existing token-containment false-positive tradeoff remains explicit.

The 56-module local batch, final aggregate/acceptance bindings and independent P3-N2 tooling
review are separate parent evidence. The actual cloud raw archive is still pending; a pasted
summary does not substitute for REVIEW.md, OUTPUT_INDEX.json or its indexed payloads. Keep
the published cloud-review folder until its archive prerequisite is met. Component remains
NOT_ACCEPTED and card IN_PROGRESS / NOT_DONE; no runtime, actual08 adoption or Lightning
execution was performed or inferred by this review.

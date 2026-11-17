# P2-T3 Phase B B4 — held-out fixture authoring record

**Status:** AUTHORING COMPLETE / OWNER REVIEW APPROVED. Evidence ID `EV-003-T3-11`, indexed in
`evidence/README.md` and summarized in `CONTEXT.md`, "P2-T3 Phase B B4 held-out fixture
authoring status (2026-09-07)". This note itself remains local-only (`evidence/notes/` is
gitignored); only the safe summary is published. It does not authorize a B4 runner, model call,
Lightning execution, profile freeze, runtime default, or B5 conclusion.

## Authoring boundary

On 2026-09-07, Person 2 authored exactly eight synthetic geometric held-out PNG fixtures and the
associated manifest, ground truth, and `vision-b4-matching-rule-v1` before any B4 model output was
seen. Image payloads remain ignored under `fixtures/vision-b4/images/`; metadata and hashes are
in `fixtures/vision-b4/` for owner review.

## Reviewed artifacts approved by owner

| Artifact | Location | SHA-256 / status |
| --- | --- | --- |
| Held-out manifest | `fixtures/vision-b4/manifest-v1.json` | `OWNER_REVIEW_APPROVED` |
| Ground truth | `fixtures/vision-b4/ground-truth-v1.json` | `c194c0c2ce1c22c5531e55393cf8554d3a3e31be88e3c99bfdd8302032ec4333` |
| Matching rule | `fixtures/vision-b4/matching-rule-v1.md` | `4e405275257f1428f8f73b5339dac1941ce6f008ff00d39cc19c391c035b96bb` |
| Prompt protocol | B4 Decision Record D-B4-0 | `vision-v2-structured-output-prompt-v2` / `1e880e946dc1f1dcf11731c299702b33ab58e3c098cdda3d6607c080dc8f9fd6` |

The manifest carries every fixture image SHA-256 and the approved eight-category taxonomy. The
ground truth was authored without inspecting B4 model output. It supplies all candidate/reference
relationships needed by the approved matching rule, including one null action endpoint and the
fixed non-scored ambiguous-region case.

## Local, no-model checks

- Each of the eight authored PNG fixtures earned a real local P2-T1 `PASS` using the existing
  deterministic validator and a synthetic companion audio signal.
- Regenerating the eight deterministic B3 scratch-image recipes and comparing SHA-256 sets found
  zero overlap with the eight B4 images.
- The temporary local validation scratch directory was absent after validation.
- No Qwen adapter, model, provider, GPU, Lightning session, dependency/configuration action, raw
  provider output, or prompt body was involved.

## Ground-truth correction before owner review (2026-09-07)

The owner approved a pre-review fairness correction after red-team review. `b4-fixture-02` and
`b4-fixture-03` now each score the directly observable `left of` relation between their authored
circle and square, matching the same canonical relation already present where applicable. Person 2
also reviewed the two previously open cases: `b4-fixture-06` has multiple equally direct spatial
pairs while C1-v2 permits one relation only, so it has no canonical scored relation; in
`b4-fixture-07`, overlap is deliberately the ambiguous-region target and no directional relation
is uniquely scored. The reasons are recorded in `ground-truth-v1.json`.

This correction changes ground truth only. It does not change any image fixture, C1-v2 prompt/hash,
matching rule, taxonomy, B4 runtime setting, code, model/GPU action, or approval boundary. The
manifest ground-truth hash must be recomputed before owner review.

## Owner review approval (2026-09-07)

Following the independent final red-team review, the owner approved the manifest, the ground truth
with SHA-256 `c194c0c2ce1c22c5531e55393cf8554d3a3e31be88e3c99bfdd8302032ec4333`, the matching
rule with SHA-256 `4e405275257f1428f8f73b5339dac1941ce6f008ff00d39cc19c391c035b96bb`, the taxonomy,
and the C1-v2 prompt identity. The owner also acknowledged that fixtures 06 and 07 intentionally
have no scored relation, so their relation aggregate must carry the documented caveat.

## Next gate

The owner subsequently authorized local-only B4 runner/test implementation; it is recorded
separately in `P2_T3_PHASE_B_B4_RUNNER_IMPLEMENTATION.md`. The shared GPU ledger, code review/
commit decision, and separate Lightning reauthorization remain later, independent gates.

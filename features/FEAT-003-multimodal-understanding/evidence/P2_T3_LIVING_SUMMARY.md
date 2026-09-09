# P2-T3 living summary — structured vision research

- Evidence ID: `EV-003-T3-SUMMARY-01`
- Last updated: 2026-09-09
- Status: `IN_PROGRESS` — Phase A and Phase B B1–B3 are complete; the original B4 benchmark is
  complete with a quality `NO_GO`; the prompt-v3 follow-up has completed phases 1–6 and its
  mapping-readiness evaluation returned `MAPPING_READY`. The separate bounded 20-minute L4
  reauthorization covered one readiness check and one v3 pass/repeat pair, but the official
  Lightning Activity ledger records `00:44:41` for that session against a `00:20:00` budget:
  compute governance is `CAP_EXCEEDED` by `00:24:41`.
- Data boundary: synthetic fixtures only; no real child data.

## Maintenance rule

This is the public, Git-tracked living summary for P2-T3. Update it after every meaningful P2-T3
implementation, review, approval, local package-verification, mapping run, benchmark, or final
decision, and include the update in the corresponding Git commit/push. It summarizes safe closed
facts only. Raw model output, prompt bodies, predicted or ground-truth text, local paths,
credentials, and local-only operational details must never be copied here.

The authoritative approval boundary remains `../approvals/TASK_APPROVAL.md`. This summary records
status; it does not authorize a later phase, GPU run, production selection, or work outside the
approved B1–B5 package.

## Objective and contract boundary

P2-T3 builds and evaluates a standalone vision-understanding component that consumes a P2-T1
validated synthetic drawing and returns a traceable, schema-valid structured result. The contract
contains five candidate collections: `entities`, `actions`, `relations`, `themes`, and
`ambiguous_regions`. Original media and provenance remain immutable, failures are typed, and raw
model output is never canonical meaning before later human review.

Phase A established the provider-neutral V1 request/result/profile/catalog/provenance contracts,
the deterministic fake adapter, the synthetic lexical-regression policy, reference-integrity
rules, and lossless complete-fence unwrap as the only repair. Phase B added a disjoint V2 contract
and a real Qwen adapter without changing the V1 behavior or hashes.

## Approved Phase B scope

The owner approved the bounded B1–B5 study on 2026-09-01:

1. B1 — isolated Qwen runtime and additive V2 contracts.
2. B2 — typed Lightning L4 readiness and real GPU preflight.
3. B3 — structured-output mapping study.
4. B4 — held-out synthetic quality benchmark with a mandatory repeat.
5. B5 — evidence-only recommendation and ADR gate.

The study does not choose a production provider, freeze a runtime default, authorize deployment,
or permit real child data. Lightning L4 is development-only and B2–B4 share a one-hour soft cap
that requires operator reconciliation before later GPU work.

## Frozen Qwen study configuration

| Field | Value |
|---|---|
| Profile | `QWEN3_VL_8B_INSTRUCT_BF16_V1` |
| Model | `Qwen/Qwen3-VL-8B-Instruct` |
| Revision | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` |
| Hardware / compute | NVIDIA L4 / CUDA device 0 / BF16 |
| Decoding | greedy; sampling disabled; beam count `1` |
| Output budget / timeout | `max_new_tokens=512`; `120s` |
| Retry / repair | no mapping-failure retry; lossless complete-fence unwrap only |
| Config hash | `3082f03f32a1cb26e6f5c25fe73813039460129b0f18a15e647b9f5ff08e3267` |
| Catalog hash | `72651b96d2c2259344efcb6fb3349807d42b56079a5422530db09c1590f00947` |

Exact dependency pins are `accelerate==1.10.1`, `qwen-vl-utils==0.0.14`, `torch==2.8.0`, and
`transformers==4.57.6`. The real Lightning environment reported `torch 2.8.0+cu128` as matching
the pinned release. The adapter's default prompt builder remains empty; every benchmark prompt is
injected explicitly by its runner.

## Execution and mapping-error history

### B2 — real GPU preflight

The operator-reported Lightning run reached `READY`, verified the immutable revision and all four
dependency pins, loaded four checkpoint shards, and performed one synthetic inference. It returned
`FAILED / VISION_SCHEMA_INVALID / OUTPUT_MAPPING_FAILED`, attempt `1`, with no repair. Measured
latency was `25729.172921999976 ms`; peak VRAM was `17080.0 MB`; the post-call selected-GPU sample
was `0.0 MB`; scratch cleanup was reported clean. This established that the runtime/model-load/
invocation/typed-classification/cleanup pathway ran, not that output mapping or model quality
succeeded.

### B3-C0 — empty-prompt baseline

Eight deterministic scratch fixtures produced `0/8` schema-valid results, `8/8` truncation flags,
and eight `OUTPUT_MAPPING_FAILED` outcomes. Each fixture received one call, with no retry and no
ground truth. This was mapping evidence only, not a quality benchmark.

### B3-C1/C2/C3 — narrowing the schema failure

The first structured protocol was
`vision-v2-structured-output-prompt-v1` with SHA-256
`152ff6c49c657e91b296f60500ef0609b851ad1901fa5291d20e3e30ef65b57e`.

The C2 diagnostic established this boundary:

```text
strict JSON parse                         PASS
JSON root object                         PASS
top-level provider-key allowlist         PASS
VisionUnderstandingSuccessV2 validation FAIL
```

Its safe diagnostics were `SCHEMA_MISSING_REQUIRED_FIELD` and
`SCHEMA_TYPE_OR_CONSTRAINT_INVALID`. A later private C3 classifier used a closed 46-token schema-
path vocabulary: 45 known normalized paths plus `SCHEMA_PATH_UNRECOGNIZED`. The real probe narrowed
the failure to `SCHEMA_PATH_ENTITIES_LABEL` and `SCHEMA_PATH_ENTITIES_CONFIDENCE`, while retaining
the typed `VISION_SCHEMA_INVALID / OUTPUT_MAPPING_FAILED` result. No raw output was persisted or
reconstructed.

### C1-v2 — mapping readiness achieved

Prompt-v2 explicitly fixed the expected entity shapes: `label` is a nested observed-text object
and `confidence` is JSON `null` for this mapping study. Its identity is:

- Protocol: `vision-v2-structured-output-prompt-v2`
- SHA-256: `1e880e946dc1f1dcf11731c299702b33ab58e3c098cdda3d6607c080dc8f9fd6`

The operator-reported probe succeeded with `SCHEMA_VALID`. `C1_PASS_1` and `C1_REPEAT_1` then each
achieved `8/8` schema/mapping-valid runs: `16/16` total, no typed failures, no truncation/fence/
extra-key/invalid-enum flags, and no repair. Peak VRAM samples were approximately `17168–17190 MB`;
the complete pass/repeat wrapper measured `297025.20966299996 ms`. Verdict: `MAPPING_READY`.
This proves structured mapping for that synthetic set, not semantic quality.

## B4 held-out quality benchmark

Person 2 authored eight synthetic held-out fixtures, their manifest and ground truth before any B4
model output. The owner approved the package. It is disjoint from B3 and uses
`vision-b4-matching-rule-v1` with SHA-256
`4e405275257f1428f8f73b5339dac1941ce6f008ff00d39cc19c391c035b96bb`.
Both passes used prompt-v2 and made one call per fixture with no retry.

Both `B4_PASS_1` and `B4_REPEAT_1` achieved `8/8` schema-valid results with no typed failures,
mapping flags, or repair. Their aggregate quality scores were byte-identical:

| Collection | Ground truth | Predicted | Matched | Coverage | Accuracy |
|---|---:|---:|---:|---:|---:|
| `entities` | 16 | 17 | 0 | 0.0 | 0.0 |
| `actions` | 3 | 3 | 0 | 0.0 | 0.0 |
| `relations` | 4 | 0 | 0 | 0.0 | `null` (not measured) |
| `themes` | 2 | 0 | 0 | 0.0 | `null` (not measured) |
| `ambiguous_regions` | 1 | 0 | 0 | 0.0 | `null` (not measured by design) |

The structural pipeline therefore passed, but the held-out quality result is `NO_GO`. A controlled
Step 2 diagnostic recorded two separate safe outcome classes:

- exact-canonical mismatch: `ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH=17` and
  `ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH=3`;
- collection omission: `EXPECTED_COLLECTION_PREDICTED_EMPTY=7` across relation, theme, and
  ambiguous-region expectations.

These counts do not prove semantic incorrectness, a scorer/ground-truth defect, or a frozen-model
limitation. The original B4 result is immutable and must not be rerun, pooled, rescored, or
silently replaced after tuning against its fixtures.

## Direction A prompt-v3 follow-up

The owner selected Direction A to test a generic collection-coverage hypothesis. Prompt-v3 adds
one active-search instruction for each of the five collections while leaving schema, model,
decoding, token budget, timeout, retry, parser, repair, and all B4 artifacts unchanged.

- Protocol: `vision-v2-structured-output-prompt-v3`
- SHA-256: `bf8b9cab5df6b2551e627cf0bb92fe977e0dc182fdaae5f3c5face5bc34615f3`
- Experiment boundary: separate from B3/C1 and the immutable B4 benchmark.

Current status:

1. Exact prompt-v3 text approved — complete.
2. Additive local code and tests — complete.
3. Eight new synthetic mapping-only fixtures and owner image review — complete; committed as
   `f46a6a1` (`feat(vision): add prompt v3 mapping fixtures`). The manifest is
   `vision-v3-map-manifest-v1`; recipe-module SHA-256 is
   `0e68f27ee4ec50ad6a683baea6c187a6c76422c7d53f60b1b4b69a845a5bade2`; local authoring reported
   P2-T1 pass for all eight and no hash overlap with B3 or B4. The set has no ground truth because
   it measures mapping readiness, not quality.
4. Target-Lightning Phase 4 package verification — complete. The operator regenerated all eight
   ignored PNGs at exact commit `f46a6a1`; their ordered IDs, dimensions, hashes, recipe hash,
   and prompt-v3 identity exactly matched the approved manifest. Real P2-T1 passed for all eight;
   B3/B4 overlap stayed zero; authoring scratch was clean; and no model or inference path ran.
   Focused v3 tests, Ruff, strict mypy, and all four repository validators passed. The full Linux
   backend suite passed after deselecting one unrelated Windows-only ASR unit test that depends on
   `os.add_dll_directory`, unavailable on Linux. This is package-only evidence, not mapping or
   quality evidence.
5. Studio-session ledger reconciliation — complete. The operator-provided activity export records
   11 Qwen L4 sessions totaling `06:58:43`; even conservative exclusions exceed the approved
   one-hour soft cap. The owner therefore separately reauthorized at most 20 minutes of new L4
   time, covering one readiness check and one v3 pass/repeat pair only. The original cap is not
   reinterpreted as remaining capacity.
6. `V3_PASS_1` plus `V3_REPEAT_1` — complete on Lightning L4. The dedicated runner never reuses
   the C1 runner and never labels
   a result as C1; every per-fixture result is re-bound to its approved `v3-map-fixture-01..08`
   identity (never the reused primitive's internal label); a real P2-T1 pass over all eight
   fixtures is required before any adapter action; readiness fails closed on a fixture-manifest-
   version mismatch; and the 15-minute repeat-comparability rule is evaluated as exactly
   `V3_REPEAT_1.started_at - V3_PASS_1.completed_at <= 15 minutes`, now stated identically across
   the reauthorization note, the mapping-validation plan, and the implementation. Local focused/
   full-suite tests, Ruff, and strict mypy passed. The fresh environment check returned `READY`
   without loading the model. Each pass then completed exactly eight attempts and eight records;
   each reached `7/8` mapping-valid with no truncation, extra-key, invalid-enum, integrity,
   runtime/device, or comparability blocker. `v3-map-fixture-07` consistently returned the typed
   `VISION_SCHEMA_INVALID / OUTPUT_MAPPING_FAILED` outcome in both passes. The repeat began
   `0.736037` seconds after pass completion, in the same declared Studio session. The verdict was
   `MAPPING_READY`. The operator recorded a prospective Studio-session start of
   `2026-09-09T07:03:09Z`; from there to runner completion at `2026-09-09T07:14:35.240860Z` was
   `00:11:26.240860`. That start is not independently verified as the official Lightning billed
   start clock, and that interval is an application-side observation only, never the billed session
   duration; see the compute-governance entry below for the authoritative ledger value.
7. Mapping-readiness evaluation — complete. The safe report is
   `metrics/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE6_REPORT.json` with SHA-256
   `ea891f1cd540909337c1e9e194981d1c159800c8911cea641696a6b50b5bca20`. It is semantically
   identical to the imported runtime report (whose SHA-256 is
   `236288e3814e0bd06de4f8c32d3a5634f869587b1a76828ec7c6e3fd5848b52b`; the evidence copy adds
   only the repository-standard final newline). It contains only safe typed outcomes, hashes,
   timings, aggregate counts, and the readiness verdict; no raw model output, prompt body,
   predicted text, ground truth, credential, endpoint, or local path. The full execution record,
   including the official ledger reconciliation, is
   `P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE6_EXECUTION_RECORD.md` (`EV-003-T3-14`).
8. Any new held-out quality benchmark — separately gated and not authorized.

### Compute governance for the Phase 6 session — `CAP_EXCEEDED`

The operator supplied the official Lightning Activity export
`Lightning-AI-activity-2026-08-09-to-2026-09-09.csv`. It contains exactly one 2026-09-09
`Qwen 3 VL` Studio row on `1 × L4`:

| Field | Value |
|---|---|
| Official billed session duration | `00:44:41` |
| Official session cost | `0.35` credits |
| Authorized budget | `00:20:00` |
| Exceedance | `00:24:41` |
| Status | `CAP_EXCEEDED` |
| Official Lightning start clock | `NOT_AVAILABLE_FROM_EXPORT` (the export carries a start *date* only) |
| Official Lightning stop clock | `NOT_AVAILABLE_FROM_EXPORT` (not derivable, and deliberately not derived) |
| Operator-recorded prospective session start | `2026-09-09T07:03:09Z` (not independently verified as the official billed start clock) |
| Operator-recorded prospective session stop | `NOT_RECORDED` |

Aggregate L4 use through 2026-09-09 is `12` sessions, `07:43:24`, and `3.93` credits, plus `0.14`
credits of storage, for `4.07` credits total in the export. The delta from the previous
reconciliation is exactly this one session (`+00:44:41`, `+0.35` credits).

The `00:11:26.240860` recorded-start-to-runner-finish interval must never be presented as the billed
duration or as evidence of staying within budget. How much of the `00:44:41` was post-repeat idle Studio time is
`NOT_AVAILABLE_FROM_EXPORT`, and that limitation does not reduce the recorded exceedance. Any
further Lightning or GPU use requires a new explicit owner decision.

The future mapping gate requires exactly eight attempts and eight records per pass, at least `7/8`
mapping-valid independently in both passes, and treats truncation `>=2/8`, configuration drift,
input-integrity failure, or runtime/device failure as blockers. The repeat must start in the same
Lightning session no later than 15 minutes after the first pass; reset, drift, or a longer gap
makes the pair `NON_COMPARABLE`. The passes are never pooled.

Phase 4 completed as package-only verification on the target Lightning checkout: it regenerated
the ignored PNGs deterministically, verified manifest/recipe hashes, ran real P2-T1 validation,
rechecked B3/B4 disjointness and Git-ignore coverage, then stopped before model action.

## Current conclusion

- Phase A: complete.
- Phase B B1: complete.
- B2: real readiness/preflight complete; first mapping call failed safely.
- B3: mapping failure diagnosed; prompt-v2 achieved repeatable `16/16` mapping readiness.
- Original B4: complete; structural mapping passed, held-out quality is `NO_GO`.
- Direction A prompt-v3: phases 1–6 and mapping-readiness evaluation are complete. The bounded
  L4 execution returned repeatable `7/8` per-pass mapping validity and `MAPPING_READY`; this is
  mapping-only evidence and does not override the original B4 quality `NO_GO` or authorize a new
  held-out quality benchmark.
- Compute governance for that same session is `CAP_EXCEEDED`: the official ledger records
  `00:44:41` against the authorized `00:20:00`, an exceedance of `00:24:41`. The technical
  `MAPPING_READY` result stands; the budget overrun is recorded separately and is not offset by it.
- Direction B, the canonical-vocabulary mismatch hypothesis, remains open.
- B5 and any production/runtime recommendation remain unresolved.
- Overall P2-T3 status: `IN_PROGRESS`.

## Canonical public evidence

See this directory's `README.md` for the selected Phase A, B1, B2, B3, and B4 canonical records.
Operator-relayed measurements in this summary retain that provenance and are not represented as
independently executed by the documentation session.

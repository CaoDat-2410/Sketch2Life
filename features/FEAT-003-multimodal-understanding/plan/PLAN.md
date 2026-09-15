# FEAT-003 Multimodal understanding plan

- Status: APPROVED (P2-T1 and P2-T2 Phases A/B complete; P2-T3 B1-B5 study complete with
  no profile frozen or runtime default selected; P2-T4 owner design decisions recorded
  2026-09-13, with the B0 reconciliation package complete as documentation-only evidence;
  the 2026-09-14 docs-only remediation/reissue passed two post-sync audits; the 2026-09-15
  planning remediation holds P2-T4 at `HOLD / NOT APPROVED - plan remediation required`;
  mapping/adoption, contract freeze, and P2-T4 implementation remain gated)
- Plan revision: 6
- Implementation status: IN_PROGRESS (P2-T3 B1-B4, including the Direction A prompt-v3
  follow-up, are complete; prompt-v3 follow-up phases 1-6 and its mapping-readiness evaluation
  complete with a `MAPPING_READY` verdict and a `CAP_EXCEEDED` compute-governance result; prompt-v3
  phase 8 execution/evidence reconciliation complete with `QUALITY_NOT_READY` and a separate
  `CAP_EXCEEDED` result; B5 evidence-only recommendation gate is complete, recommending
  `NOT_ENOUGH_EVIDENCE` to freeze any Qwen3-VL profile, with no profile frozen and no runtime
  default selected; the P2-T4 freeze draft (revision 11) and implementation-approval package
  (revision 15) are `HOLD - NOT APPROVED` as committed at
  `18d0c33d35431ca96a76692a68c6b992098699e7`, and the P2-T4 planning status is
  `HOLD / NOT APPROVED - plan remediation required`; owner freeze, the architecture-validator
  policy choice, mapping/adoption, and separate implementation approval remain pending; P2-T5
  remains gated)
- Owner: Person 2
- Estimate: 10 points total (P2-T1 through P2-T5, 2 points each)

## Scope and boundary

Build a standalone, fixture-driven Python understanding package: deterministic media validation; provider-neutral Whisper and Qwen3-VL adapters; deterministic fusion and conflict preservation; a versioned proposed `P2T4FusedResultV1`; and a CLI evaluation harness. Inputs are synthetic drawings and narration only. Originals are immutable; any normalization produces a separately referenced working copy with provenance. The former `RawUnderstandingResultV1` wording is historical baseline terminology only.

Excluded from this feature: capture UI, Gate A UI/confirmation, session/job state, FastAPI routes, queues, databases, object storage wiring, mobile integration, provider credentials, and any real child data. The standalone runner must never require another Sprint 1 service.

## Shared contract-first foundation

Before code for T1, review and freeze a small versioned contract set with sample fixtures:

- `MediaFixtureManifestV1`: immutable source references, hashes, declared media metadata, expected validation decision, and synthetic-data declaration.
- `MediaValidationResultV1`: `PASS | RECAPTURE`, deterministic reason codes, measured signals, source/working-copy references, and validator/config provenance.
- `AsrResultV1` and `VisionUnderstandingResultV1`: typed result or typed failure, source reference, model/config provenance, quality metadata, and no free-form provider response as a public contract.
- `P2T4FusedResultV1`: source modality predictions, entities, actions, relations, themes, support map, conflicts, uncertainty, and provenance. It explicitly excludes personality, diagnosis, mental-state, and psychological-inference fields. The proposed identity is `P2T4.P2T4FusedResultV1@1.0`, serialized as `P2T4FusedResultV1 / 1.0`.

The former P2-T4 `RawUnderstandingResultV1` identity and shape are retained only as the historical
baseline that motivated the separately scoped B0 reconciliation. The post-sync FEAT-018 tree now
contains its frozen/implemented live-development `RawUnderstandingResultV1 / 1.0` handoff, owned
by FEAT-018 and closed offline at `11468d3a5a327697a491f09251a3210987337da0`; this is current
implementation state, not a historical proposal. The active P2-T4 proposal is
`P2T4FusedResultV1`, and it is neither an alias of nor a replacement for the FEAT-018 Raw handoff.
The FEAT-018 mapper consumes `VisionUnderstandingResultV2` plus optional P2 ASR, while P2-T4
consumes P2 `VisionUnderstandingResultV1`; the output identities/status unions, required
session/image/Gate-A/V2 provenance, ambiguity/fused-claim/conflict/confidence/uncertainty/failure
shapes are incompatible and cannot be silently projected.

The immutable B0 reconciliation report, manifest, and reviews predate the implemented FEAT-018
Raw module. They remain an old reconciliation snapshot with mapping
`P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` / `PROPOSED_NOT_ADOPTED`; separately approved
integration reconciliation is required before adoption, registry change, consumer update, or
edge-3 handoff. The current post-sync review base is
`d706d88a70c6a9136e397bea10d29f96bafd190b`; the future T4 freeze/implementation source commit is
`UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`.

The contract review is part of this plan, not approval to integrate it into the application. Any change after approval requires a plan/approval update.

## Approved implementation slice

P2-T1 and P2-T2 Phases A/B are implemented; the P2-T2 controlled Round-1 execution and repeat are
recorded in `EV-003-T2-05` and `EV-003-T2-06`, without selecting a frozen profile or runtime
default. P2-T3 Phase A and the bounded Phase B B1-B5 study are approved. B1-B3 and the original B4
benchmark are complete; B4 produced schema-valid output but a quality `NO_GO`. The separately
bounded prompt-v3 follow-up has completed phases 1-6 and its mapping-readiness evaluation: both
`V3_PASS_1` and `V3_REPEAT_1` reached `7/8` mapping-valid independently for a `MAPPING_READY`
verdict (`EV-003-T3-13`, `EV-003-T3-14`). That is mapping-only evidence; it does not change the
B4 quality `NO_GO` and does not authorize the separately gated prompt-v3 phase 8 held-out quality
benchmark. Compute governance for that session is `CAP_EXCEEDED` — the official Lightning ledger
records `00:44:41` against the authorized `00:20:00` — so further GPU work needs a new explicit
owner decision. The separately approved prompt-v3 phase 8 held-out quality benchmark then executed
and returned `QUALITY_NOT_READY` / `QUALITY_BELOW_THRESHOLD`, with its own `CAP_EXCEEDED` compute
result (`00:37:22` billed against `00:30:00` authorized). B5, the evidence-only recommendation
gate, is now complete: the comparison table and recommendation are in
`evidence/notes/P2_T3_PHASE_B_B5_RECOMMENDATION.md` (`EV-003-T3-17`) and
`docs/adr/ADR-0007-vision-runtime-dependency-pinning-and-qwen3-vl-candidate-profile.md`. The
recommendation is `NOT_ENOUGH_EVIDENCE` to freeze `QWEN3_VL_8B_INSTRUCT_BF16_V1`, or any
Qwen3-VL profile, for production or runtime-default use: neither B4 nor Phase 8 ever persisted
predicted/ground-truth text (`raw_output_mode: CLASSIFY_ONLY`), and `DECISIONS.md` independently
prohibits rescoring the existing fixtures under a changed rule in any case. No profile is frozen
and no runtime default is selected. A future Direction B experiment (the untested
canonical-vocabulary-mismatch hypothesis) remains conceivable in principle but is not authorized by
B5 and would need its own new plan, approval, and capture/scoring boundary with entirely new
fixtures. The current safe status is maintained in `evidence/P2_T3_LIVING_SUMMARY.md`. P2-T4 and
P2-T5 remain unapproved.

### Prompt-v3 Phase 8 execution-ready status (2026-09-09)

- Local/no-GPU preparation and the bounded D-8 execution are complete. Both passes achieved 8/8
  schema-valid runs and passed the repeat/comparability conditions, but neither met D-5; the
  immutable verdict is `QUALITY_NOT_READY / QUALITY_BELOW_THRESHOLD`.
- D-5 is fixed at `0.80` minimum coverage and accuracy for entities/actions/relations/themes;
  ambiguous-region count-rate must be exactly `1.00` and its accuracy is `NOT_MEASURED`. D-6
  requires 8/8 attempted, recorded, and schema-valid fixtures per pass; both passes independently
  meet D-5, and Repeat starts no later than 15 minutes after Pass 1 completes in the same Studio
  session, with the recorded blocking conditions.
- D-7 is resolved as `CLASSIFY_ONLY`. The local runner rejects `EPHEMERAL_CAPTURE` from both the
  execution decision and the B3 collector before package loading, scratch creation, factory
  invocation, or raw-output writing. This does not change B3's separate raw-output behavior.
- The application-side D-8 interval was `00:08:13.428533`, but the finalized Lightning Activity
  ledger records `00:37:22` and `0.24` credits against the `00:30:00` hard cap. Compute governance
  is therefore `CAP_EXCEEDED` by `00:07:22`; that result is separate from the immutable
  `QUALITY_NOT_READY` technical verdict. No tuning, download, exploratory inference, extra
  diagnostics, or automatic rerun is in scope. Phase 8 execution and evidence reconciliation are
  complete; P2-T3 remains in progress because B5 and any production recommendation remain open.

## Task breakdown and execution order

### P2-T1 — Image/audio input quality validation (2 points, Must)

**Goal:** Implement a pure standalone validator that turns `drawing.png` and `narration.wav` metadata/content checks into deterministic recapture guidance.

**Implementation slices:**

1. Define fixture manifest, decision enum, stable reason-code catalog, and threshold/config version. Reasons distinguish unsupported/corrupt media, image too small, severe blur/darkness/crop risk, audio format/duration error, silence/no-speech signal, and unreadable audio. A single input always produces the same decision and ordered reasons under the same config.
2. Inspect image decodability, dimensions, orientation, luminance/contrast, blur proxy, and framing/crop signals. Inspect audio decodability, duration, sample rate/channels, clipping/silence, and speech-presence proxy. Keep all source files read-only; emit a working-copy reference only if normalization is later requested.
3. Add PASS, every individual RECAPTURE reason, multi-reason ordering, corrupt-file, and boundary-value fixtures. Do not infer meaning or silently continue with one modality when required input is unusable.

**Done when:** `drawing.png + narration.wav` returns `MediaValidationResultV1`; unusable media yields a stable `RECAPTURE` decision and human-readable recapture message; valid media passes; source hashes remain unchanged; unit/contract tests cover every reason code.

**Maintenance — T0 incremental source hashing (approved 2026-09-10, complete):** source hashing
reads the file in fixed-size chunks of at most 1 MiB instead of loading it whole. Digests,
statuses and the serialized `MediaValidationResultV1` are byte-identical for unchanged inputs, so
the validation-provenance hashes recorded by the ASR and vision benchmark helpers are unaffected.
This bounds hashing memory only; byte/pixel limits, decoding cost, optional-audio behavior and the
reason catalog are unchanged and out of that scope.

### P2-T2 — Whisper large-v3-turbo adapter (2 points, Must)

**Goal:** Provide an ASR port implementation that can use `faster-whisper`/Whisper large-v3-turbo, while its public result remains provider-neutral and source-traceable.

**Implementation slices (Phase A, this approval scope):**

1. Define `AsrPort`, `AsrResultV1` as a discriminated union (`AsrSuccessV1`/`AsrFailureV1`), and `AsrProfileCatalogV1` (deterministic fake profile entries only), plus a deterministic fixture fake; accept only a validated audio reference from T1 and preserve `source_audio_ref`/hash in every result.
2. Map fake-adapter output into `AsrSuccessV1`/`AsrFailureV1`: raw transcript (may be empty with `speech_diagnostic=NO_SPEECH_SUSPECTED`), detected language plus confidence/probabilities where available, timestamped segments, ASR quality metadata, model/version/config provenance, `attempt_number`/`repair_attempted`, and typed timeout/provider/schema errors. Do not expose model SDK objects or raw JSON outside infrastructure.
3. Implement the retry/repair matrix (per-error-code retryability, one bounded inference retry only for transient provider failure, one local mapping/serialization repair only for schema-invalid output, enforced inside the adapter); provider failure remains a typed error and cannot overwrite the source or create a canonical meaning artifact.
4. Add Vietnamese and non-Vietnamese synthetic fixtures, Vietnamese-English code-switching, silence-only/no-speech (Case A: `SUCCEEDED` with empty transcript) and unmappable-output (Case B: `FAILED`) cases, noise/recording-condition variation, timeout/failure cases per the retry matrix, and schema round-trip tests.

**Phase B (approved under `approvals/TASK_APPROVAL.md`, still P2-T2 ownership):** implement the real `faster-whisper`/Whisper adapter against experimental `AsrProfileCatalogV1` candidate entries and run the ASR-only profile-selection benchmark. The current readiness layer plans exactly the two Turbo Round-1 profiles; the live run waits only for fixture-source selection and compliant local payload/reference hashes. It does not include the CLI or the ~20-fixture end-to-end report, which is P2-T5. The exact scope — additive contract change, `config_hash` fields, standalone runtime config, Round 1 (`AUTO_DETECT`-only) definition, deferred forced-language convention, GPU preflight/exact-pin requirements, and evidence requirements — is detailed in `P2_T2_ASR_RESEARCH_PLAN.md` and `evidence/notes/P2_T2_PHASE_B_APPROVAL_REQUEST.md`.

**Done when (Phase A):** valid audio produces schema-valid transcript/language/quality metadata with the original audio reference; every fake output is mapped to exactly one of `AsrSuccessV1`/`AsrFailureV1` deterministically; ASR no-speech/language diagnostics never override a P2-T1 `PASS`/`RECAPTURE` decision; no credential, endpoint, raw transcript, or raw media is written to ordinary logs or to `evidence/`. Full contract, discriminated-union fields, retry/repair matrix, and boundary detail: `P2_T2_ASR_RESEARCH_PLAN.md`.

### P2-T3 — Qwen3-VL structured drawing understanding adapter (2 points, Must)

**Goal:** Provide a VLM port that returns strictly validated drawing observations, never a free-form response contract.

**Implementation slices:**

1. Define `VisionUnderstandingPort` and a fixture fake. Its request accepts the validated image reference and an explicit `VisionUnderstandingResultV1` JSON Schema/Pydantic shape.
2. Configure the Qwen3-VL adapter to request structured output, then validate/map it before return. The allowed output is entity candidates, action candidates, relations, themes, unknown/ambiguous regions, confidence/uncertainty, source image reference, and model/config provenance.
3. Reject/mask unsupported fields and prohibited psychological/personality claims. Treat malformed, incomplete, timeout, and provider failures as typed adapter results; allow at most one bounded repair/retry mechanism, never an unbounded conversational loop.
4. Test valid structured outputs, malformed/free-text output, missing source reference, prohibited field, ambiguity, timeout, and source-hash preservation. Use fixture model responses for all contract tests.

**Done when:** `drawing.png` yields only schema-valid structured observations; malformed free text cannot enter fusion; every observation remains traceable to the original image and model/config.

**Phase A approval reference:** the detailed Phase A contract, typed error/retry/repair matrix, safety boundary, fixture matrix, and accepted owner decisions are in `P2_T3_VISION_RESEARCH_PLAN.md`; the authoritative approval is `approvals/TASK_APPROVAL.md` (2026-08-31). The corresponding review record is `evidence/notes/P2_T3_VISION_CONSTRAINT_REVIEW.md`. This authorizes only the deterministic contract/fake-adapter scope. P2-T3 Phase B (real Qwen runtime/profile/GPU/benchmark) remains separately gated. Where the plan resolves ambiguity, prohibited claims are rejected as typed failures rather than silently masked, and the single bounded local repair is a lossless Markdown-fence unwrap only — never JSON completion or value inference.

### P2-T4 — Multimodal fusion and conflict detection (2 points, Must)

**Goal:** Combine validated P2 ASR and Vision results into the proposed
`P2T4.P2T4FusedResultV1@1.0` without erasing disagreement.

**Current status (2026-09-15):** `HOLD / NOT APPROVED - plan remediation required`. The nine
inherited owner decisions and the remediation selections are synchronized across the
documentation package. The freeze draft (`plan/P2_T4_CONTRACT_FREEZE_DRAFT.md`, revision 11)
and the implementation-approval package
(`evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md`, revision 15) are
both `HOLD - NOT APPROVED` at commit `18d0c33d35431ca96a76692a68c6b992098699e7`; that commit is
the immutable freeze/package candidate and is not edited by this planning remediation. The two
independent post-sync final audits passed; the 2026-09-15 planning remediation corrects only
`PLAN.md` and `P2_T4_FUSION_RESEARCH_PLAN.md` so that they match the freeze draft's CF-B1
semantics, exact paths, service boundaries, and governance sequencing. The separately approved
documentation-only B0 reconciliation is complete, but its mapping remains
`PROPOSED_NOT_ADOPTED`. The active
proposed output is exactly `P2T4.P2T4FusedResultV1@1.0` (`P2T4FusedResultV1 / 1.0`); the former
`RawUnderstandingResultV1` wording is historical only. The exact seven-file offline core and
reviewable freeze draft are future/proposed artifacts only. Result statuses are exactly
`FUSED | UPSTREAM_FAILURE`; `NOT_FUSIBLE` is not part of the active v1 design. Contract freeze
and implementation remain unapproved. The rejected live families are exactly
`FEAT018.LiveAsrResultV1@1.0` and `FEAT018.LiveVisionUnderstandingResultV1@1.0`.

**Resolved design boundaries:** narration is support/refute-only and cannot create independent
entities, actions, relations, or themes; themes pass through from vision only; narration support
can affect only `primary_interpretation` among non-conflicting candidates; the exact negation cue
list is `not`, `no`, `never`, `isn't`, `doesn't`, `didn't`; the window is exactly the three
match-view tokens immediately preceding an already-matched claim span; the corroboration
increment is `0.10`, applied at most once and only to the primary candidate with eligible
positive support and no conflict (exact CF-B1 rules below), capped at `1.0`;
`AGREEMENT_WEIGHTED_V1` is retained; and null source vision confidence remains
`NOT_MEASURED` with null certainty even when support exists. Matching is independently against
each validated `AsrSegmentV1.text`; normalized token coordinates are
`(segment_index, claim_start, claim_end)` and both coordinates and the three-token negation
window reset per segment. `transcript_raw` is non-authoritative. The policy/hash representation
of `corroboration_increment` is the exact string `"0.10"`, converted to `Decimal` only for
arithmetic. Ambiguous Vision regions are omitted as fused observations and retain only
canonical source-result provenance. Mixed positive/refuting spans retain support and canonical
positive/refuting refs while suppressing adjustment and primary eligibility. Finite numeric
Vision confidence below the floor may emit `LOW_CONFIDENCE_EVIDENCE` for an entity, action,
relation, or theme; themes remain Vision-only, have no uncertainty row, and never enter primary
ranking.

**Confirmed contract boundary remediation:** the current upstream `AsrSuccessV1` contract permits
duplicate `AsrSegmentV1.index` values, so the P2-T4 admissibility invariant is exactly: `For
AsrSuccessV1, all AsrSegmentV1.index values MUST be unique.` The terminal pipeline is exactly
`identity/version -> strict upstream-contract validation -> P2-T4 admissibility invariants ->
correlation equality -> typed upstream status -> fusion`; the first failing stage is terminal and
ASR is checked before Vision where slot ordering applies. A duplicate index is rejected with
`status=REJECTED`, `phase=ADMISSIBILITY`, `code=INVALID_STRUCTURE`, `input_slot=ASR`, and
`field_code=DUPLICATE_SEGMENT_INDEX`; no duplicated index, transcript, input object, exception,
or validation path is exposed. The phase/field-code tables are closed and reuse
`INVALID_STRUCTURE`. Vision V1 already enforces global `observation_id` uniqueness across
entities, actions, relations, themes, and ambiguous regions through
`_validate_observation_references`; T4 adds no redundant Vision uniqueness rule or new owner
decision. Canonical narration references are ordered exactly by
`(segment_index ASC, claim_start ASC, claim_end ASC)`; identical coordinate tuples are
deduplicated before independently selecting the canonical earliest positive and earliest
refuting reference, independently of source tuple traversal order.

The exact future fixture artifacts, referenced consistently by every authorized handoff,
allowlist, acceptance, and evidence-binding record, are:

```text
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

**Exact seven-file implementation allowlist:** the future offline implementation scope is
exactly these repo-root-qualified paths and nothing else. The schema and service modules are
always named by their full paths; a bare `p2_t4_fusion.py` is ambiguous and is not used.

```text
backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py
backend/src/sketch2life/application/services/p2_t4_fusion.py
backend/tests/contract/test_p2_t4_contract.py
backend/tests/unit/test_p2_t4_fusion.py
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

**Two service boundaries (design only, not implementation):**
`backend/src/sketch2life/application/services/p2_t4_fusion.py` has exactly two boundaries.

- Outer boundary: accepts unknown `object` values; performs safe identity/version
  classification, strict upstream-contract validation, P2-T4 admissibility checks, and
  correlation equality; returns the typed `P2T4FusionInputRejectionV1` on any failure. It
  inspects only the closed identity, version, and discriminator values needed to classify,
  never copies the unknown object into a result, and reduces any validation failure to a
  closed `code`/`field_code`; no Pydantic `ValidationError`, exception text, field path, or
  input value escapes.
- Pure fusion boundary: `fuse(asr, vision, policy, executed_at) -> P2T4FusedResultV1` accepts
  only the exact validated P2 unions `AsrSuccessV1 | AsrFailureV1` and
  `VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1`, plus a validated
  `P2T4FusionPolicyConfigV1` and a timezone-aware datetime. It returns a `FUSED` result or a
  typed `UPSTREAM_FAILURE` result. It has no `object`, mapping, dataclass, or provider-shaped
  overload, never accepts arbitrary objects, and never emits a raw validation error.

**CF-B1 certainty semantics (exact, copied from the freeze draft; B2 primary-only weighting
is closed and not reopened):**

- finite, non-conflicting candidate: `certainty_status=MEASURED`, `certainty = base` by
  default;
- primary candidate (`primary_interpretation=true`) with eligible positive narration support
  and no conflict: `certainty = adjusted`, exactly
  `float(min(Decimal("1.0"), Decimal(str(base)) + Decimal("0.10")))`, applied once;
- supported non-primary candidate: `certainty = base`;
- any conflicting candidate, including a null-confidence candidate with a conflict:
  `certainty_status=NOT_APPLICABLE_CONFLICTING`, `certainty=null`;
- otherwise, null-confidence candidate: `certainty_status=NOT_MEASURED`, `certainty=null`,
  even when support exists;
- `LOW_CONFIDENCE_EVIDENCE` compares the original source confidence using strict
  `base < confidence_floor` before any adjustment; null is never below the floor;
- adjusted certainty MUST NOT affect grouping, ranking, primary eligibility, conflict
  detection, or low-confidence classification. Primary selection happens before adjustment
  and ranks by original source confidence only.

**Freeze immutability and governance sequencing:** the approved freeze/package status is
never mutated after approval. The exact sequence is:

```text
owner approves the exact freeze commit + full normalized digest + identity
  -> the freeze artifact at that commit becomes immutable
  -> governance records (TASK_APPROVAL.md, DECISIONS.md, CONTEXT.md) reference that exact
     approval by commit, digest, and identity
  -> a separate seven-file implementation approval is requested
```

The current candidate is freeze draft revision 11 and package revision 15 at commit
`18d0c33d35431ca96a76692a68c6b992098699e7`. No planning, approval, or governance record may
edit the approved freeze draft or package in place to change its status. If a status change
to the freeze/package is ever required, it needs a new revision, a new normalized digest,
independent review, and renewed owner approval; the previously approved revision remains
immutable history.

**Implementation and evidence sequencing (G1-G9):**

```text
G1  owner freeze approval (exact commit + digest + identity)
G2  separate approval for the exact seven implementation paths above
G3  implement the seven paths, and only those paths
G4  independently review the candidate working tree
G5  commit the exact implementation checkpoint
G6  verify that exact implementation commit (tests, validators, CPython 3.13.x pin)
G7  produce evidence bound to that exact commit hash
G8  independently review the evidence
G9  record completion in the governance records
```

Evidence and governance files are not implicitly authorized by the seven-file implementation
approval (G2). Any new evidence path (for example a feature-local evidence note, manifest, or
validator-output record) must be named in that approval or separately authorized before it is
created. G7 evidence must bind the exact G5 commit hash, the freeze/package digests,
dependency/lock hashes, and the manifest/cases/expected/final-evidence SHA-256 values.

**Canonical runtime pin:** `P2T4-CANONICAL-JSON-V1` serialization and determinism validation
run on CPython 3.13.x. G6/G7 evidence must record `sys.version`, the implementation name
(`platform.python_implementation()`, expected `CPython`), and the major/minor version
(`3.13`). Determinism results from any other interpreter or version are not accepted as v1
evidence.

**Architecture-validator policy gate (owner decision required before G3):**
`python tools/validate_architecture.py` currently reports one pre-existing violation in
`backend/src/sketch2life/application/services/backend_ai_workflow.py` (application layer
imports an outer layer). That file is outside P2-T4 scope and is not modified by P2-T4. The
owner must record exactly one policy before implementation starts; this plan does not select
one:

- Policy A (strict): the architecture validator must be fully green before G5, which
  requires a separately scoped remediation of the pre-existing violation first.
- Policy B (baseline): the exact pre-existing fingerprint (`application imports an outer
  layer: backend/src/sketch2life/application/services/backend_ai_workflow.py`) is accepted as
  known baseline; P2-T4 introduces zero new violations; and the validator failure is still
  reported truthfully in G6/G7 evidence, never suppressed or described as passing.

**Future slices after the gates:**

1. G1: the owner records the contract-freeze approval against the exact freeze commit,
   digest, and identity; the B0 mapping remains a separate `PROPOSED_NOT_ADOPTED` record and
   is not part of the T4 core. The owner also records the architecture-validator policy
   (A or B).
2. G2: a separate approval names exactly the seven offline paths above, plus any evidence
   path that G7 will create.
3. G3-G5: implement pure deterministic fusion, bounded conflict detection, primary-only
   weighting with CF-B1 certainty, and uncertainty calculation only within those seven paths;
   review the candidate tree; commit the exact implementation checkpoint.
4. G3-G5 fixtures: add the approved fusion, pre-validation, privacy-sentinel, round-trip,
   determinism, provenance, reference-integrity, independent schema-parity, and
   prohibited-field fixtures in those seven paths. Include duplicate-index admissibility,
   ASR-before-Vision precedence, coordinate deduplication, and the narration-reference
   selection independence from ASR segment/claim tuple traversal order case (asserting
   identical canonical positive/refuting coordinates and reference choice only, not whole
   fused JSON equality when validated Vision source order changes, because top-level Vision
   observations preserve source order). Include the mandatory primary-only fixtures: two
   same-group finite candidates with positive support and no conflict (exactly one primary,
   only the primary receives `+0.10`, the supported non-primary stays at base); a supported
   null-confidence primary (`primary_interpretation=true` but `NOT_MEASURED`/null); and a
   base below the floor whose hypothetical adjusted value reaches or exceeds the floor
   (`LOW_CONFIDENCE_EVIDENCE` is still emitted from the original base, the candidate is a
   conflict participant, and no adjustment is applied). No mapping cases or
   preservation-envelope implementation belong in this slice.
5. G6-G9: verify the exact implementation commit on CPython 3.13.x, produce evidence bound
   to that commit (source commit, freeze/package digest, dependency/lock hash,
   manifest/cases/expected/final-evidence SHA-256 values, `sys.version`, implementation
   name, and the architecture-validator result under the chosen policy), review the
   evidence independently, then record completion.

**Done when:** fusion generates strict JSON with source support, uncertainty, and conflict provenance; conflicts retain both predictions; the artifact is explicitly an AI proposal for future Gate A, never a `CanonicalUnderstandingResult`.

### P2-T5 — Standalone demo and evaluation harness (2 points, Should)

**Goal:** Deliver a local CLI/demo and reproducible report over approximately 20 synthetic fixture pairs.

**Implementation slices:**

1. Build `validate`, `understand --provider fixture`, and `evaluate` CLI commands. Fixture mode is the CI baseline; the approved P2-T2 Phase B Round-1 profiles may run only through their controlled ASR benchmark boundary, without changing schemas or fixtures.
2. Define a held-out, versioned fixture manifest with reference transcript, language, entities/actions/relations/themes, expected validation decision, and known conflict labels. Keep media local and synthetic; record immutable hashes, manifest version, and split membership.
3. Calculate and report: schema pass/fail rate; image/audio recapture counts by reason; ASR WER and CER against reference transcript; entity/action precision, recall, F1 (and the matching rule); conflict-detection precision/recall where labeled; per-stage and end-to-end p50/p95 latency; provider/config and run timestamp. Report unavailable metrics as `NOT_MEASURED`, never as zero.
4. Save command, environment, manifest/model/config hashes, outputs, and interpretation under `features/FEAT-003-multimodal-understanding/evidence/`. Include success, invalid-input, timeout/provider-failure, and fallback/recapture cases.

**Done when:** a clean local run produces a schema-valid machine-readable report and concise benchmark summary for about 20 fixtures, without mobile/backend/DB dependencies; the report clearly separates fixture results from live-model results.

## Dependency plan

```text
Contract & fixture review
        -> P2-T1
        -> P2-T2 (ASR) -----\
        -> P2-T3 (VLM) ------> B0 contract reconciliation
                                  -> P2-T4 (fusion) -> P2-T5 (CLI/evaluation)
```

For one owner, work sequentially as T1, T2, T3, T4, T5. If two contributors are available inside the P2 workstream, T2 and T3 may proceed in parallel only after the shared schemas and fixture manifest are reviewed; they may not depend on each other's live process.

## Acceptance criteria

- [x] T1 invalid image/audio fixtures deterministically request recapture with stable reason codes.
- [x] Source originals remain untouched and every derived reference carries source hash/provenance.
- [ ] T2 and T3 real or fixture model results validate against their versioned schemas; free-form provider output is never the output contract.
- [ ] T4 preserves conflicting modality predictions with source support and uncertainty; it never produces canonical meaning or psychological inference.
- [ ] T5 reports schema validity, recapture reasons, ASR WER/CER, entity/action accuracy, conflict metrics where labeled, and latency with measurement coverage.
- [ ] Timeout/provider-failure fixtures produce typed standalone errors and never overwrite source artifacts.
- [ ] The runner and all contract tests execute without mobile, backend API, database, queue, or another Sprint 1 workstream.
- [ ] Evidence records command, environment, input/manifest reference, output, timestamp, reviewer, and interpretation.
- [x] P2-T2 Phase B readiness validates a versioned ASR-only manifest and fixed Round-1 metadata plan without model/GPU/CLI/API work; unavailable measurements are explicit `NOT_MEASURED`.
- [x] B0 reconciliation is separately approved and its documentation-only package is complete
      before P2-T4 contract freeze or implementation; its mapping remains unadopted.
- [x] The 2026-09-14 docs-only remediation/reissue records the exact seven-file future offline
      core and creates a freeze draft without creating or editing any implementation path.
- [x] The post-remediation freeze draft passes two independent final audits recorded in the reissued
      implementation-approval package; this does not grant the owner freeze decision.
- [x] The future fixture acceptance artifacts are exactly:
      `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`,
      `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`, and
      `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`;
      none exists in this docs-only task.
- [x] The confirmed ASR admissibility invariant, exact rejection fields, closed phase/code
      additions, terminal pipeline, and ASR-before-Vision ordering are synchronized.
- [x] The upstream Vision global `observation_id` uniqueness fact and no-redundant-T4-rule
      boundary are synchronized.
- [x] Exact repo-root-qualified future fixture paths, canonical narration-reference
      ordering/deduplication, and narration-reference selection independence from ASR
      segment/claim tuple traversal order are synchronized.
- [x] The 2026-09-15 planning remediation synchronizes the exact seven-file paths, the two
      service boundaries, the exact CF-B1 certainty rules, the mandatory primary-only
      fixtures, the CPython 3.13.x pin, freeze immutability, and the G1-G9 sequence in
      `PLAN.md` and `P2_T4_FUSION_RESEARCH_PLAN.md` without touching the freeze draft or
      package.
- [ ] The owner records the architecture-validator policy (A strict or B baseline).
- [ ] The owner records the separate contract-freeze decision (G1) against the exact
      commit, digest, and identity.
- [ ] The owner records the separate seven-file implementation approval (G2).

## Evidence and review gates

1. Contract/fixture review before implementation: schema names, versions, reason-code catalog, and synthetic-data declaration.
2. Approval update: the approver must approve this exact revision and scope before any implementation begins.
3. During implementation: store test output, fixture manifest hashes, model/config hashes, and benchmark summaries in this feature's `evidence/` directory. Do not store original or real child media.
4. Before completion: record a compatibility note for Integration Sprint containing only versioned input/output contracts, typed errors, artifact references, and provenance requirements.

Implementation is blocked for P2-T3 work outside its approved Phase B B1-B5 boundary and for all
P2-T4/P2-T5 work until the corresponding scope is explicitly approved. P2-T3 follow-up phases do
not authorize later phases, GPU work, production selection, or integration by default.

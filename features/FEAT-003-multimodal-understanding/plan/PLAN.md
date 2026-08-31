# FEAT-003 Multimodal understanding plan

- Status: APPROVED (P2-T1 complete; P2-T2 Phases A/B complete; P2-T3 Phase A approved)
- Plan revision: 4
- Implementation status: IN_PROGRESS (P2-T1 and P2-T2 Phases A/B complete; P2-T3 Phase A approved for implementation; P2-T3 Phase B through P2-T5 remain planned)
- Owner: Person 2
- Estimate: 10 points total (P2-T1 through P2-T5, 2 points each)

## Scope and boundary

Build a standalone, fixture-driven Python understanding package: deterministic media validation; provider-neutral Whisper and Qwen3-VL adapters; deterministic fusion and conflict preservation; a versioned `RawUnderstandingResult`; and a CLI evaluation harness. Inputs are synthetic drawings and narration only. Originals are immutable; any normalization produces a separately referenced working copy with provenance.

Excluded from this feature: capture UI, Gate A UI/confirmation, session/job state, FastAPI routes, queues, databases, object storage wiring, mobile integration, provider credentials, and any real child data. The standalone runner must never require another Sprint 1 service.

## Shared contract-first foundation

Before code for T1, review and freeze a small versioned contract set with sample fixtures:

- `MediaFixtureManifestV1`: immutable source references, hashes, declared media metadata, expected validation decision, and synthetic-data declaration.
- `MediaValidationResultV1`: `PASS | RECAPTURE`, deterministic reason codes, measured signals, source/working-copy references, and validator/config provenance.
- `AsrResultV1` and `VisionUnderstandingResultV1`: typed result or typed failure, source reference, model/config provenance, quality metadata, and no free-form provider response as a public contract.
- `RawUnderstandingResultV1`: source modality predictions, entities, actions, relations, themes, support map, conflicts, uncertainty, and provenance. It explicitly excludes personality, diagnosis, mental-state, and psychological-inference fields.

The contract review is part of this plan, not approval to integrate it into the application. Any change after approval requires a plan/approval update.

## Approved implementation slice

P2-T1 and P2-T2 Phase A are implemented; the P2-T2 Phase B benchmark-readiness package and
controlled live Round-1 execution are complete under the approved scope in
`approvals/TASK_APPROVAL.md`. The two executed runs are recorded in `EV-003-T2-05` and
`EV-003-T2-06`; neither selects a frozen profile or runtime default. P2-T3 Phase A is separately
approved; P2-T3 Phase B and P2-T4 through P2-T5 remain planned and must receive their own explicit
approval before work starts.

## Task breakdown and execution order

### P2-T1 — Image/audio input quality validation (2 points, Must)

**Goal:** Implement a pure standalone validator that turns `drawing.png` and `narration.wav` metadata/content checks into deterministic recapture guidance.

**Implementation slices:**

1. Define fixture manifest, decision enum, stable reason-code catalog, and threshold/config version. Reasons distinguish unsupported/corrupt media, image too small, severe blur/darkness/crop risk, audio format/duration error, silence/no-speech signal, and unreadable audio. A single input always produces the same decision and ordered reasons under the same config.
2. Inspect image decodability, dimensions, orientation, luminance/contrast, blur proxy, and framing/crop signals. Inspect audio decodability, duration, sample rate/channels, clipping/silence, and speech-presence proxy. Keep all source files read-only; emit a working-copy reference only if normalization is later requested.
3. Add PASS, every individual RECAPTURE reason, multi-reason ordering, corrupt-file, and boundary-value fixtures. Do not infer meaning or silently continue with one modality when required input is unusable.

**Done when:** `drawing.png + narration.wav` returns `MediaValidationResultV1`; unusable media yields a stable `RECAPTURE` decision and human-readable recapture message; valid media passes; source hashes remain unchanged; unit/contract tests cover every reason code.

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

**Goal:** Combine static `transcript.json` and `vision.json` into `RawUnderstandingResultV1` without erasing disagreement.

**Implementation slices:**

1. Implement a pure deterministic fusion policy over validated ASR and VLM contracts: normalize labels, retain source observations, match support for entities/actions/relations, and calculate configured uncertainty signals.
2. Emit explicit conflict objects with both modality claims, source pointers, reason codes, and recommended reviewer attention. Narration may be higher-weighted for semantic interpretation, but visual evidence is never removed or rewritten.
3. Add fixtures for agreement, audio-only/image-only assertion, contradictory entity/action/relation, low-confidence evidence, duplicate normalization, and upstream typed failures. These tests must execute without a model or network.
4. Add JSON Schema/Pydantic round-trip, deterministic-output, provenance, and prohibited-field tests.

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
        -> P2-T3 (VLM) ------> P2-T4 (fusion) -> P2-T5 (CLI/evaluation)
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

## Evidence and review gates

1. Contract/fixture review before implementation: schema names, versions, reason-code catalog, and synthetic-data declaration.
2. Approval update: the approver must approve this exact revision and scope before any implementation begins.
3. During implementation: store test output, fixture manifest hashes, model/config hashes, and benchmark summaries in this feature's `evidence/` directory. Do not store original or real child media.
4. Before completion: record a compatibility note for Integration Sprint containing only versioned input/output contracts, typed errors, artifact references, and provenance requirements.

Implementation is blocked for every not-yet-approved slice (P2-T3 Phase B through P2-T5) until its
corresponding scope is explicitly approved. P2-T1 and P2-T2 cleared this gate and are implemented;
P2-T3 Phase A is now approved only within its recorded deterministic contract/fake-adapter scope.

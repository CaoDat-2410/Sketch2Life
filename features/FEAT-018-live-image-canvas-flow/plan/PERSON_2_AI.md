# FEAT-018 Person 2 — Real image understanding and mapping

## Mission

Accept one non-sensitive JPG/PNG, validate it before inference, run the exact tech-stack model through the backend-only Lightning adapter, preserve truthful provenance, and produce a versioned observation contract that P1 can map without bypassing Gate A.

## Ownership boundary

Person 2 owns image/audio quality validation, Whisper large-v3-turbo and Qwen3-VL-8B-Instruct adapters, structured output mapping, fusion provenance, and typed provider failures. Person 2 does not own Gate A UI, activity eligibility rules, Pixi playback, or mobile provider configuration.

## Task cards

### P2-T1 — Image input and quality validation

Accept only bounded local-development JPG/PNG references. Validate:

- decodability and MIME/extension agreement;
- maximum bytes, width/height, and aspect ratio;
- orientation and EXIF normalization without overwriting the original;
- luminance/contrast, blur proxy, crop/framing risk;
- duplicate/hash and source provenance.

Return `PASS` or `RECAPTURE` with stable reason codes. A failed input must not call Qwen3-VL.

### P2-T2 — Exact VLM adapter

- Use `Qwen/Qwen3-VL-8B-Instruct` loaded from the local Lightning Studio path.
- Return only `VisionUnderstandingResultV1`/versioned successor: entities, actions, relations, themes, ambiguous regions, confidence/uncertainty, source reference, provider/model/config provenance.
- Reject free text, prohibited psychological/personality fields, missing provenance, schema drift, oversized output, and stale source/session versions.

### P2-T3 — Optional narration path

- If narration is supplied, use `large-v3-turbo` through `faster-whisper`.
- If narration is absent, emit explicit missing-source provenance; never fabricate a transcript.
- Preserve ASR and vision as separate evidence before fusion.

### P2-T4 — Mapping diagnostics for all pilots

For every row in `ACTIVITY_PILOT_MATRIX.md`, cover:

- exact observation;
- ambiguous observation;
- no matching candidate;
- conflicting image/narration;
- low confidence;
- adult Gate A correction.

The output is a proposal/candidate envelope, never an eligibility decision.

### P2-T5 — Live/fixture evaluation harness

- Fixture tests run without network/model.
- Live dev run uses only the approved non-sensitive image and local Lightning URL/token file.
- Evidence stores hashes/metadata only; no raw image, prompt, output, header, or secret.
- Report p50/p95 latency, schema pass rate, recapture rate, provider/model/config ID, and typed failure counts.

## Required evidence

- Image validator matrix: valid, corrupt, unsupported, too large, too dark, blurred, crop-risk, orientation case.
- VLM schema examples for all 20 golden pilots.
- ASR-present and ASR-missing provenance cases.
- Prohibited-field and malformed-output rejection.
- Timeout, retry, rate-limit, stale-session, and provider-error evidence.
- One explicitly approved live run with sanitized metadata.
- Mobile bundle scan proving no provider URL/token/model credential.

## Acceptance criteria

- Valid non-sensitive image reaches the exact Qwen3-VL model through backend-only infrastructure.
- Invalid image never reaches the provider.
- Missing narration remains explicit and truthful.
- Every result has source hash/reference and model/config provenance.
- Observations cannot directly create Gate B or skip Gate A.
- All 20 pilot activities have mapping diagnostics and at least one blocked/ambiguous case.

## Handoff contract

P2 publishes `VisionUnderstandingResultV1`, optional `AsrResultV1`, and `RawUnderstandingResultV1` with versioned provenance. P1 consumes observations for candidate mapping; P3 consumes only approved scene inputs; mobile consumes the backend proposal envelope.

## Definition of done

Validator, exact adapters, typed failures, 20-pilot mapping harness, live smoke evidence, redaction checks, and contract documentation are complete.

## Contract alignment checklist (mandatory)

Before implementation, read [CONTRACT_FREEZE.md](CONTRACT_FREEZE.md). P2 is the sole owner of AI result field definitions. Mobile, P1, P3, and P4 consume the frozen contracts and must not create a simplified `label/confidence` substitute.

### Exact inputs

- `VisionRequestV1` with `SourceMediaReferenceV1` and `media_validation=PASS`.
- Optional `AsrRequestV1`; absence is represented by a missing source, never an invented transcript.
- Transport envelope: `session_id`, `expected_session_version`, `request_id`, idempotency key.

### Exact outputs

- `VisionUnderstandingResultV1` with entities/actions/relations/themes/ambiguous regions/uncertainty/provenance.
- `AsrResultV1` when audio exists.
- `RawUnderstandingResultV1` preserving modality, claims, conflicts, and `gate_a_required=true`.
- `AdapterFailureV1` on failure; never HTTP-only free text.

### Contract tests owned by P2

- extra-field and missing-provenance rejection;
- source hash mismatch;
- all media recapture reasons;
- malformed/prohibited model output;
- typed timeout/provider/rate-limit/retry exhaustion;
- ASR-only, vision-only, both, and missing-audio cases;
- all 20 golden mapping diagnostics without emitting P1 eligibility fields.

P2 must publish schema fixtures before the mobile request or P1 mapper is changed.

## Execution order and stop gates

1. Freeze `SourceMediaReferenceV1` and `MediaValidationResultV1` fixtures.
2. Implement deterministic validation and prove provider is not called on `RECAPTURE`.
3. Validate Qwen/Whisper adapters against schema fakes.
4. Publish live-dev smoke only after redaction and source-hash checks pass.
5. Hand off to P1 only when `RawUnderstandingResultV1` is valid and Gate A is mandatory.
6. Stop on any prohibited field, unbounded output, source mismatch, or fabricated narration.

Evidence naming: `P2_<media-or-contract>_<YYYYMMDD>.json` plus sanitized latency/status `.txt`; raw provider payloads are forbidden.

## Revision-2 engine additions — pending approval

P2 additionally owns `FEAT018-P2-E1` through `FEAT018-P2-E4` in `ENGINE_REFINEMENT_PLAN.md`: enrich provider-neutral observations, publish anchor candidates with provenance, cover unknown/ambiguous/conflicting/adult-corrected cases, and provide the adapter into `SemanticAnchorSetV1`. P2 does not select objectives, templates or activities.
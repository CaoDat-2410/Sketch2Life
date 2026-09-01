# P2-T2 ASR research plan

- Status: APPROVED — Phase A implemented; Phase B benchmark-readiness package implemented; local live Round-1 benchmark executed (2026-08-30) and supplementary Colab validation reviewed (2026-09-01) against 21 synthetic HELD_OUT fixtures, see `evidence/notes/P2_T2_PHASE_B_ROUND1_ASR_REPORT.md`; no profile freeze or runtime default selected
- Owner: Person 2
- Parent plan: `PLAN.md`, revision 4; team allocation: `docs/adr/ADR-0006-parallel-sprint-allocation.md`, `features/FEAT-001-stack-and-team-plan/SPRINT_1_TASK_ALLOCATION.md`
- Input dependency: a `PASS` result from P2-T1 for the immutable narration reference
- Output boundary: provider-neutral `AsrResultV1` for P2-T4; never a canonical interpretation or a Gate A decision

## Research question and decision to make

Assess whether the handbook baseline — Whisper `large-v3-turbo` through `faster-whisper` — can meet the standalone ASR contract for synthetic narration fixtures. The research must produce evidence for a later decision on model revision, decode profile, VAD policy, compute profile, and operational limits. It must not assume that upstream example settings work for Vietnamese or child narration.

The candidate model is appropriate to evaluate because its model card describes it as a faster, pruned form of Whisper `large-v3`; the trade-off is a small claimed quality loss that has not yet been measured on this project's fixtures. `faster-whisper` exposes language detection, timestamped segments, word timestamps, VAD, and diagnostic probabilities, but these fields are provider details to map into a local contract rather than expose directly.

## In scope and explicit non-goals

In scope: source review, provider-neutral contract design, fake-adapter fixtures, experiment design, metric definitions, data/observability safeguards, and a recommendation backed by synthetic-fixture evidence.

Out of scope: installing model dependencies, downloading weights, calling a provider, accessing a GPU endpoint, using real child media, application/API/queue integration, session-state changes, Gate A UI, translation, speaker profiling, diarization, emotion/personality inference, or automatic recapture. P2-T1 remains the sole authority for pre-inference media recapture.

Per `SPRINT_1_TASK_ALLOCATION.md`, P2-T2 owns the ASR contract, the fixture fake, and the real Whisper adapter; it does not own the standalone CLI or the ~20-fixture end-to-end evaluation/benchmark report — that is P2-T5. Where this plan designs an ASR-only benchmark (R3), it is scoped narrowly to ASR profile selection evidence, not a substitute for or duplicate of the P2-T5 harness. No task in this plan is labelled outside the `P2-T1`..`P2-T5` set defined by that allocation document.

## Phase A vs. Phase B scope

This plan was split into two approval scopes so contract work could be reviewed separately from model/dependency work:

- **Phase A (approved and implemented):** freeze `AsrRequestV1`/`AsrResultV1` as a discriminated union, the `AsrProfileCatalogV1` catalog (deterministic fake profile entries only), the retry/repair matrix, and the `AsrPort` interface; implement the deterministic fixture fake adapter and the R2 contract test suite. No dependency install, no model weights, no GPU/provider access, no live inference, no live benchmark.
- **Phase B (approved under `approvals/TASK_APPROVAL.md`):** the additive contract/catalog change, isolated runtime configuration, real `faster-whisper` adapter, and exact-pinned optional dependency are implemented. The readiness slice added the Round-1 manifest contract, scoring normalizer, fixed two-Turbo metadata plan, and report template; the controlled live profile comparison was subsequently executed twice locally, with supplementary Colab validation, with evidence in `EV-003-T2-05`, `EV-003-T2-06`, and `EV-003-T2-07`. Phase B does not implement the CLI or the ~20-fixture end-to-end multimodal report; that remains P2-T5.

## Phase B approval request

This section records the exact Phase B scope that was requested and then approved in
`approvals/TASK_APPROVAL.md`. Detailed rationale for every convention below was produced
across independent review passes recorded in `evidence/notes/P2_T2_LOGIC_CONSTRAINT_REVIEW.md`
and `evidence/notes/P2_T2_PHASE_B_APPROVAL_REQUEST.md`.

### B1. Additive contract change to `contracts/schemas/asr.py`

Phase B implementation begins by amending the already-approved Phase A contract file, additively only — no existing Phase A fake entry's value or behavior changes:

- widen the `AsrProfileId` enum with the approved Phase B candidate members; the readiness layer plans only the two Turbo Round-1 profiles below and does not add or run a large-v3 profile;
- widen `AsrProfileV1.adapter_kind` (currently `Literal["DETERMINISTIC_FAKE"]`) to also accept a real-adapter kind (e.g. `"FASTER_WHISPER"`);
- widen `AsrProfileV1.compute_profile` (currently `Literal["NONE"]`) to also accept real compute descriptors (e.g. `"CPU_INT8"`, `"GPU_INT8_FLOAT16"`, `"GPU_FLOAT16"`);
- add new `AsrProfileV1` fields not present in Phase A: `model_identifier`, `model_revision`, converted-weight provenance plus license, `adapter_version`, `runtime_version`. (`beam_size`, `language_mode`, `vad_enabled`, `word_timestamps_enabled`, `timeout_seconds`, and `idempotent_timeout_retry` already exist on `AsrProfileV1` and need no change);
- replace `phase_a_profile_catalog()` with a single static, versioned, **phase-agnostic** catalog function (e.g. `asr_profile_catalog()`) that returns both the unchanged Phase A fake entries and the Phase B candidate entries. `AsrRequestV1`'s existing validator continues to resolve `requested_profile_id` against this one function call — Phase B does **not** introduce per-request dynamic catalog injection into Pydantic validation, since that would let the same `profile_id` validate in one call site and fail in another, breaking the contract's determinism guarantee.

### B2. `config_hash` formula and required input fields

`config_hash` stays the existing mechanism: SHA-256 over the canonical JSON serialization of the profile (`sort_keys=True`, compact separators — unchanged from Phase A's `profile_config_hash()`). For a Phase B profile, the hashed input must include: `model_identifier`, `model_revision`, converted-weight provenance and license, `adapter_version`, `runtime_version`, `compute_profile`, `beam_size`, `language_mode`, VAD enablement/parameters, word-timestamp enablement, `timeout_seconds`, and the retry policy (`idempotent_timeout_retry`).

No local absolute path may appear in source or evidence. Only the environment-variable name `SKETCH2LIFE_ASR_MODEL_CACHE_DIR` is referenced — never a default path value in code, plan text, or evidence.

### B3. Runtime configuration stays outside the shared backend `Settings`

A new `FasterWhisperRuntimeConfig` is defined in `infrastructure/ai`, constructor-injected into the adapter and any local test runner — the same injection pattern `DeterministicFixtureAsrAdapter.__init__` already uses for its fixtures. The shared `infrastructure/config/settings.py` `Settings` class (which gates production behavior via `enforce_deployment_provider_policy`) is never extended for Phase B, and Phase B introduces no HTTP/API/provider wiring of any kind.

### B4. Round 1 benchmark definition

The first Phase B benchmark round is scoped narrowly:

- `AUTO_DETECT` profiles only — no `HONOR_HINT`/forced-language profile runs in this round;
- candidates for this readiness package: turbo INT8 auto-detect and turbo FP16 auto-detect only; the `large-v3` catalog candidate is not planned or downloaded in Round 1;
- fixed across all Round 1 profiles: VAD disabled, beam size 5, word timestamps disabled;
- the report must record VAD alternatives, beam-size alternatives, and word-timestamp alternatives as `NOT_MEASURED` — never silently omitted, never zero;
- no profile is proposed for freeze and no runtime default is selected from Round 1 alone; results are directional synthetic evidence only (see the ~20-fixture limitation in R3).

The Phase B approval already includes the controlled live Round-1 execution. This readiness
slice deliberately stops before execution because the fixture source and compliant local
payload/reference-transcript refs and hashes still require a `DECISION_REQUIRED` selection.

### B5. Forced-language (`HONOR_HINT`) convention for a later round

Forced-language behavior is provider-specific to `faster-whisper`, confirmed against upstream source (`SYSTRAN/faster-whisper`, `faster_whisper/transcribe.py`): when `language=None`, the model calls `detect_language(...)` and returns a measured `language_probability`; when a language is explicitly supplied, detection is skipped entirely and `language_probability` is hardcoded to `1` — a sentinel indicating "forced," not a per-audio detection confidence.

Convention for any later round that adds a `HONOR_HINT` profile: the adapter sets `language_hint_applied=true`; the resulting `language_probability=1.0` is recorded and reported as a **provider sentinel**, never as detection confidence; that profile's results are excluded from language-detection accuracy/calibration metrics; no report may present a forced `"vi"` as if the model had auto-detected it.

This convention is deliberately **not** enforced by a new `AsrSuccessV1`-level validator. `AsrSuccessV1` is a provider-neutral shared contract; `language_hint_applied` only means "the adapter applied the hint," not "this specific provider hard-forced the language and skipped detection." A different provider's hint mechanism could be a soft bias that still returns a genuinely measured confidence. A schema-wide invariant tying `language_hint_applied` to `language_probability == 1.0` would bake one provider's implementation detail into the shared contract, which contradicts the provider-neutral boundary this contract already keeps elsewhere (provider SDK objects, raw JSON, and other provider details stay inside infrastructure). The sentinel-vs-confidence distinction is instead enforced by the `faster-whisper` adapter's own tests and evidence, the same way today's retry/`attempt_number` correlations are enforced by `DeterministicFixtureAsrAdapter`'s own tests rather than a shared-schema validator.

### B6. GPU preflight and dependency pinning

GPU preflight must invoke the real adapter — a real model load plus one synthetic transcription — not a bare CLI/driver check in isolation. A model/runtime load failure or device unavailability must map to `ASR_MODEL_UNAVAILABLE` using the existing `MODEL_LOAD_FAILED`/`DEVICE_UNAVAILABLE` `AsrErrorDetail` values, per the retry/repair matrix above.

`faster-whisper` and `CTranslate2` must be exact-pinned in `backend/pyproject.toml` before any install — a documented exception to this repository's usual range-pin (`>=X,<Y`) convention, because CTranslate2's cuDNN version requirement has changed across releases and a range pin risks silently breaking local GPU compatibility between installs. The rationale is recorded in the ADR required by R5.

### B7. Evidence and report requirements

Phase B evidence/report must include: both success and typed-failure paths with their `attempt_number`/`repair_attempted` values; the privacy constraints already required by R4 (no raw audio, transcript, credentials, or endpoint details in logs or `evidence/`); weight provenance and license; the versioned Vietnamese normalizer/tokenizer used for WER/CER; an explicit synthetic-only limitation statement (no real child-speech validation); and the ~20-fixture sample size labelled directional, not statistically robust evidence.

## Phase B benchmark-readiness implementation slice (2026-08-30)

This slice prepares the approved Round-1 execution without running it. It adds a strict,
provider-neutral `AsrRound1FixtureManifestV1` contract and a feature-local layout/template;
the manifest is metadata-only until a synthetic/TTS or licensed source is selected. It adds
the versioned `vi-asr-normalizer-v1` scoring views (WER tokens and CER characters), and a
non-CLI planner that validates the manifest, checks the exact two-Turbo Round-1 settings,
and emits deterministic `PLANNED` records with every measurement set to `NOT_MEASURED`.
The planner does not inspect audio, import/call a provider SDK, load a model, use a GPU, or
replace P2-T5's CLI/end-to-end report. No model, audio, transcript, or real-child data is
created by this slice.

## Contract baseline and implementation constraints

The following is the reviewed contract baseline and its implementation constraints. The
Phase A contract and approved Phase B additions are implemented; the readiness additions are
described above and remain metadata-only until a fixture source is selected.

### Request boundary

`AsrRequestV1` accepts only:

- `source_audio_ref` and its SHA-256, copied from a passing `MediaValidationResultV1` — **always required, on every request in every phase**, including Phase A. In Phase A this is populated from a synthetic audio fixture that already carries a P2-T1 `PASS`. It always names the original, untouched audio, never a derived copy, and no adapter may normalize, mutate, or VAD-filter it;
- optional `processing_audio_ref`: a reference to a derived working copy of the audio, populated only if a prior step created one. If set, `derivation_provenance` (transform applied, config/version, and a hash chain back to `source_audio_ref`) is mandatory and must be present in the same request. **In Phase A, `processing_audio_ref` is always `null` and `derivation_provenance` is always absent/`null`** — P2-T2 does not normalize or VAD-filter the source audio in Phase A, no working copy exists, and no adapter may silently create one. Any preprocessing decision beyond this contract is a later, explicitly scoped decision;
- the P2-T1 validator/config provenance reference;
- `requested_profile_id`: a closed reference into `AsrProfileCatalogV1` (see below), never a free-form string — validated at request construction, per the convention immediately below;
- optional `language_hint`: `{value, source, is_ground_truth: false}` — see the language-policy section below;
- a correlation ID, neither containing raw audio nor a transcript.

It must reject an absent/failed P2-T1 result with the typed error `INPUT_NOT_VALIDATED`. It must not normalize, replace, or write the source audio.

**`INPUT_NOT_VALIDATED` convention (fixed by prior revision, unchanged):** it is a schema-valid typed failure inside `AsrResultV1` (specifically `AsrFailureV1`, see below), the same result family as every other ASR outcome — not a separate exception/request-validation type. This keeps `AsrPort` a single-return-type interface, consistent with P2-T1's non-exception `PASS`/`RECAPTURE` pattern. It is a defensive second check only: the correct call path always gates on a P2-T1 `PASS` before invoking ASR at all, so this code should not occur in a correctly wired caller. This convention does not authorize or imply any session/UI/job-state coupling; mapping `INPUT_NOT_VALIDATED` (or any other typed failure) to user-facing or session state remains Integration Sprint scope, not P2-T2.

**Invalid `requested_profile_id` convention:** `AsrRequestV1` can only be constructed after `requested_profile_id` is validated against `AsrProfileCatalogV1`. A profile ID absent from the catalog is a deterministic **request/schema-boundary validation error** — the request is rejected before `AsrPort` is ever invoked, the same way any other structurally malformed field would be. It is not one of the five `AsrFailureV1` error codes, and it is specifically not `INPUT_NOT_VALIDATED`: `INPUT_NOT_VALIDATED` means the request is otherwise well-formed (including a *valid* `requested_profile_id`) but lacks a linked P2-T1 `PASS`. Keeping these separate means an invalid profile ID never masquerades as a P2-T1/provenance problem, and it guarantees `profile_id` in every returned `AsrSuccessV1`/`AsrFailureV1` is always a resolved, valid catalog entry — never ambiguous or unresolved. This error is not silently dropped: request construction/validation must surface it deterministically (e.g. as a `ValueError`/schema-validation error at the request-object boundary), just outside the `AsrResultV1` result family.

### Boundary with P2-T1: diagnostics never override validation decisions

ASR-side signals such as `speech_diagnostic`, `no_speech_prob`, low language-detection probability, or an empty/near-empty segment list are ASR model diagnostics only. They must never trigger a recapture, silently mark a result as failed in place of a typed error, or otherwise override P2-T1's `PASS`/`RECAPTURE` decision — P2-T1 remains the sole authority for pre-inference recapture. If P2-T1 returned `PASS` but the ASR diagnostics suggest little or no speech, T2 preserves that as a diagnostic signal with provenance inside a `SUCCEEDED` result (not a T2-level decision, and never a manufactured `FAILED`); reconciling it against P2-T1's proxy is P2-T4's conflict/uncertainty responsibility, per the project rule that conflicts and uncertainty are preserved, not silently overwritten.

### Result boundary: `AsrResultV1` is a discriminated union

`AsrResultV1` is `AsrSuccessV1 | AsrFailureV1`, discriminated by `status` (`SUCCEEDED` for the former, `FAILED` for the latter). It must not be a flat schema with ambiguous optional fields that are sometimes meaningless depending on status — a field belongs either to the shared envelope, to `AsrSuccessV1`, or to `AsrFailureV1`, never floating as "optional and unclear which branch populates it."

**Shared envelope (required on both `AsrSuccessV1` and `AsrFailureV1`):**

- `contract_version`;
- `correlation_id` echoed from the request, and `executed_at` (timezone-aware) recording when this result was produced — needed to audit repeated runs over the same input;
- `source_audio_ref` and source hash, unchanged from the request;
- `profile_id` actually used (the resolved `AsrProfileCatalogV1` entry; in Phase A this is always the fake profile);
- `attempt_number`: the count of adapter inference attempts actually made for this logical request — an "attempt" is one call to whatever the adapter's inference boundary is (the deterministic fake in Phase A; the real provider/model in Phase B). It is never a claim that a real model ran in Phase A. `0` when no inference attempt was made at all (only `INPUT_NOT_VALIDATED` — rejected before any adapter call); otherwise starts at `1` for the first attempt and can only reach `2` under the retry matrix below — never higher. See "Phase A vs. Phase B meaning of an attempt" below for concrete values;
- `repair_attempted: bool`: whether the one allowed local mapping/serialization repair (no new inference attempt) was used — kept separate from `attempt_number` because a retried inference attempt and a local output repair are different operations (see the retry/repair matrix).

**`AsrSuccessV1`-only fields** (present only when `status = SUCCEEDED`):

- `transcript_raw: str` — the ASR proposal, not a semantic interpretation. It may legitimately be `""`;
- `speech_diagnostic`: a closed enum, `DETECTED | NO_SPEECH_SUSPECTED | INDETERMINATE` — see the empty-transcript rule below;
- detected language and language probability, clearly labelled model diagnostics rather than ground truth; `language_hint_echo` (the request's `language_hint`, if any, echoed back for audit — it must never silently override `detected_language`, and any case where the adapter used the hint to bias/constrain decoding must record that fact here, not hide it);
- ordered segments (may be an empty list, especially when `speech_diagnostic != DETECTED`): stable index, start/end seconds, text, optional average log probability, compression ratio, no-speech probability (a diagnostic only — see the boundary note above), and optional word timing/probability;
- input duration, `vad_enabled: bool`, and `duration_after_vad`: nullable, populated only when `vad_enabled` is true. A `null` value (VAD did not run) must be distinguishable from a value equal to the input duration (VAD ran and removed nothing); never use `0`/the input duration as a stand-in for "not measured";
- model/revision identifier, adapter version, library/runtime version, and normalized configuration hash;
- `quality_metadata` as a closed, versioned schema (not a free-form dict) containing only explicitly enumerated, measurable ASR diagnostics and the source-validation linkage (a reference/hash back to the `MediaValidationResultV1` that authorized this request) — keeping it closed prevents scope creep or an unreviewed field (including any prohibited psychological/personality signal) from entering the contract informally.

**`AsrFailureV1`-only fields** (present only when `status = FAILED`):

- `error_code`: one of `INPUT_NOT_VALIDATED`, `ASR_TIMEOUT`, `ASR_MODEL_UNAVAILABLE`, `ASR_PROVIDER_FAILURE`, `ASR_SCHEMA_INVALID` (see the error-mapping table below);
- `retryable: bool` — whether the matrix classified this failure's underlying cause as inference-retryable (i.e., whether a retry was attempted before this terminal result was returned; `true` only for a transient `ASR_PROVIDER_FAILURE`, or an `ASR_TIMEOUT` under a declared idempotent-timeout policy). It is independent of `repair_attempted`, which covers the separate local-repair path for `ASR_SCHEMA_INVALID`;
- `error_detail`: a bounded, sanitized, enumerated-category description. It is never raw provider JSON, an unbounded stack trace, a credential, or an endpoint URL.

### Empty-transcript determinism: Case A vs. Case B

Two situations both involve an "empty-looking" outcome and must never be conflated:

- **Case A — ASR executed and produced a mappable result, with no or very low detected speech.** This is `AsrSuccessV1` with `status=SUCCEEDED`, `transcript_raw=""` (or near-empty), `segments` possibly `[]`, and `speech_diagnostic=NO_SPEECH_SUSPECTED` (or `INDETERMINATE` if the model's own signals disagree with each other, e.g. conflicting VAD/no-speech-probability evidence, or the audio is too short to classify confidently). This is not a recapture and not a failure; it is diagnostic evidence P2-T4 uses for conflict/uncertainty handling.
- **Case B — the provider/model errored, timed out, was unavailable, or returned output that cannot be mapped into a schema-valid `AsrSuccessV1` at all** (not merely "quiet," but genuinely unusable — non-parseable, wrong types, missing required structure even after the one allowed repair). This is always `AsrFailureV1` with the matching `error_code`. It must never be represented as a `SUCCEEDED` result with an empty transcript, and it must never silently disappear — a caller cannot receive "nothing" as an outcome.

The deterministic rule for the adapter: if the model/provider call itself completed and returned a structure the adapter can map (even if that structure describes silence), the outcome is Case A (`SUCCEEDED`). If the call did not complete successfully, or its output cannot be mapped after the one allowed repair, the outcome is Case B (`FAILED`). There is no third, ambiguous outcome.

### Retry and repair matrix

Inference retry (re-invoking the adapter's inference boundary — the fake in Phase A, the real model/provider in Phase B) and local mapping/serialization repair (re-processing output already received, without a new inference call) are different operations governed by different rules. The following table is authoritative and must be implemented exactly; it is deterministic and unit-testable without a real model — every row is exercised in Phase A by configuring the fake adapter to simulate that outcome on demand, never by invoking a real model:

| Cause | Error code | Retryable (inference)? | Repairable (local)? | Max attempts | Owner |
|---|---|---|---|---|---|
| No linked P2-T1 `PASS` / missing provenance | `INPUT_NOT_VALIDATED` | No | No | `attempt_number` stays `0` (immediate reject) | `AsrPort` — rejected before any inference attempt |
| Model/weights fail to load; device unavailable; out-of-memory at load time (Phase B only — Phase A's fake adapter simulates this outcome on a fixture request without any real load) | `ASR_MODEL_UNAVAILABLE` | No | No | 1 | Adapter load-time check |
| Inference exceeds the configured timeout budget | `ASR_TIMEOUT` | No by default. Retryable only if the adapter's timeout policy can prove the request never started executing on the provider, or the provider contractually guarantees idempotent re-submission — this exception must be declared in the profile's config hash, not decided ad hoc at call time | No | 1, or 2 only under the declared idempotent-timeout policy | Adapter |
| Provider/runtime exception during inference, classified transient (explicit transient/retryable signal, connection reset) | `ASR_PROVIDER_FAILURE` | Yes | No | 2 (1 retry) | Adapter |
| Provider/runtime exception during inference, classified non-transient (invalid request, permanent rejection) | `ASR_PROVIDER_FAILURE` | No | No | 1 | Adapter |
| Provider output received but fails to map/validate against `AsrSuccessV1` | `ASR_SCHEMA_INVALID` | No — never re-invoke the inference boundary for this | Yes — one local mapping/serialization repair over the already-received output | 1 inference attempt + at most 1 repair | Adapter's local mapping layer |

Both the retry and the repair paths are enforced entirely inside the adapter/port implementation. A caller must never add its own retry on top of this table; `attempt_number` and `repair_attempted` on the result make the invariant auditable in tests and evidence. The integration sprint, not this task, maps any outcome to user-facing/session states.

### Phase A vs. Phase B meaning of an attempt

`attempt_number` and the retry/repair matrix have identical semantics and identical counting rules in both phases — only what happens *inside* one attempt differs:

- **Phase A:** an "attempt" is the deterministic fake adapter returning a pre-configured outcome for that fixture. No model runs, no dependency loads, no provider is called. Concretely: `INPUT_NOT_VALIDATED` → `attempt_number = 0` (rejected before the fake is even invoked); an ordinary fake success or a non-retryable fake failure (`ASR_MODEL_UNAVAILABLE`, non-transient `ASR_PROVIDER_FAILURE`, default-policy `ASR_TIMEOUT`, or `ASR_SCHEMA_INVALID` after its one repair) → `attempt_number = 1`; a fake-simulated transient `ASR_PROVIDER_FAILURE` (or idempotent-policy `ASR_TIMEOUT`) that retries once → `attempt_number = 2`.
- **Phase B:** an "attempt" is a real invocation of the provider/model (e.g. `faster-whisper`). The same counting rules apply. That execution is within the current Phase B approval, but this readiness slice does not invoke it.

R2's fixtures assert the Phase A numbers above; nothing in Phase A ever produces or requires a real model invocation to reach them.

### Profile catalog and language policy

`requested_profile_id` is not a free string. It references `AsrProfileCatalogV1`, a closed, versioned registry where every entry declares its task/language mode, decode/beam settings, VAD policy and parameters, timestamp granularity, and compute/precision profile, and is itself hashed for the `config_hash` field.

- **Phase A defines the `AsrProfileCatalogV1` schema itself, plus only deterministic fake entries** — no model, no dependency, no Whisper runtime of any kind (not even a stub that shells out to it). A single default (e.g. `FAKE_DETERMINISTIC_V1`) covers most contract fixtures; a second fake entry that declares the idempotent-timeout retry policy is permitted solely to exercise that one matrix branch in R2's tests. Every Phase A entry is a deterministic ASR-adapter-output fake — it fakes the adapter's return values, never a Whisper/`faster-whisper` runtime. Neither entry, nor any additional fake variant, may invoke a model or require a dependency.
- **Phase A did not add any Whisper candidate entry to the catalog** — not even as an unusable placeholder. The current Phase B approval introduces the real-adapter candidates. The Round-1 readiness layer plans only the two Turbo profiles defined above; no large-v3 profile is added to or run by this slice. Candidate profiles remain `NOT_APPROVED` until R1/R5 evidence supports freezing one, and the exact additive contract change is recorded in B1 above.

`language_hint` is optional, carries its own `source` (e.g. fixture manifest declared language, an upstream UI-provided guess), and is explicitly `is_ground_truth: false`. An adapter may use it to bias decoding only for a profile that documents doing so, and must echo it in `language_hint_echo` either way. The benchmark (R1/R3) must keep "auto-detect" and "honor-hint" as separate, clearly labelled controlled variants — language-detection accuracy reported for the "honor-hint" mode must never be blended with or substituted for the "auto-detect" mode's accuracy, since a hint can trivially inflate apparent accuracy and would hide the model's real detection quality.

Provider SDK objects, provider raw JSON, endpoint details, credentials, and unbounded exception text stop inside infrastructure. Raw audio and transcript text must never enter ordinary logs or this feature's `evidence/` directory — evidence stores only synthetic inputs and approved, traceable summaries, matching P2-T1's precedent.

## Research work packages

### R1 — Establish reproducible candidate profiles

Record the exact upstream source/model revision, adapter/library version, conversion/weight provenance, device class, precision, beam size, VAD setting, word-timestamp choice, language mode (auto-detect vs. honor-hint, kept as separate variants per the language policy above), timeout, and configuration hash for every proposed `AsrProfileCatalogV1` candidate entry. Candidate starting profiles should be compared rather than silently made default:

| Variable | Candidate values to measure | Decision evidence |
|---|---|---|
| Task/language | transcription; auto-detect vs. declared fixture language, as two separate profile variants | language accuracy and Vietnamese/non-Vietnamese WER/CER, reported per variant, never blended |
| Decoding | documented beam-size alternatives | WER/CER and latency trade-off under identical fixture split |
| VAD | disabled; enabled with explicitly recorded parameters | omission/segmentation effects, duration-after-VAD, WER/CER, and latency |
| Timing | segment-only; word timestamps enabled | timing usefulness, schema completeness, latency, and any alignment failures |
| Compute | supported CPU/GPU precision profiles | p50/p95 latency, memory/runtime availability, and equal-quality comparison |

Do not compare provider benchmarks with mismatched decode settings. Keep model load/start-up time separate from per-audio inference latency. This work package is within the approved Phase B scope, but its live execution follows the fixture-source decision. The first Phase B execution slice ("Round 1") is scoped narrowly to the auto-detect/compute/model-size variables only — see "B4. Round 1 benchmark definition" above; VAD, beam-size, and word-timestamp alternatives remain `NOT_MEASURED` until a later round, and any forced-language (`HONOR_HINT`) variant follows "B5. Forced-language convention" above, not this table's language-mode row directly.

### R2 — Freeze the fixture-only contract test suite

Phase A scope. Implement a deterministic `AsrPort` fake that emits candidate `AsrResultV1` (`AsrSuccessV1`/`AsrFailureV1`) objects without importing a model SDK. Cover:

- valid Vietnamese/non-Vietnamese narration (`SUCCEEDED`, `speech_diagnostic=DETECTED`);
- Vietnamese-English code-switching;
- Case A: silence-only audio mapped by the model (`SUCCEEDED`, `transcript_raw=""`, `speech_diagnostic=NO_SPEECH_SUSPECTED`, empty or near-empty segments) — and a fixture asserting this never becomes a typed failure or a recapture signal;
- an `INDETERMINATE` `speech_diagnostic` case (conflicting internal signals or too-short audio to classify);
- Case B: unmappable/garbage provider output (`FAILED`, `ASR_SCHEMA_INVALID`, one repair attempted then still failing) — and a fixture asserting this never becomes a `SUCCEEDED` result with an empty transcript;
- noise/recording-condition variation;
- language uncertainty, and `language_hint` echoed without silently overriding `detected_language`;
- `INPUT_NOT_VALIDATED` without a P2-T1 `PASS` (`attempt_number` stays `0` — the fake adapter is never invoked at all);
- `ASR_TIMEOUT` under the default non-retryable policy, and (separately) under a declared idempotent-timeout profile;
- `ASR_PROVIDER_FAILURE` classified transient (one retry then success, and one retry then still-failed) and classified non-transient (no retry);
- `ASR_MODEL_UNAVAILABLE` (no retry);
- source-hash preservation, and rejection of any request carrying a `processing_audio_ref` without `derivation_provenance`;
- a `requested_profile_id` absent from `AsrProfileCatalogV1` is rejected deterministically at request construction, before `AsrPort` is invoked — asserted as a request/schema-boundary error, never as an `AsrFailureV1` (and specifically never as `INPUT_NOT_VALIDATED`).

Contract acceptance rules:

- every `AsrSuccessV1` validates the local schema and keeps the original audio reference/hash;
- every `AsrFailureV1` is typed and schema-valid; it can never carry `transcript_raw` or any success-only field, and Case B can never be represented as `SUCCEEDED`;
- Case A (quiet-but-successful) can never be represented as `FAILED`, recapture, or a T2-level decision overriding P2-T1;
- timestamps are non-negative, ordered, and contained within the reported input duration;
- transcript and diagnostic fields are retained only as an ASR proposal with explicit provenance;
- `attempt_number` and `repair_attempted` match the retry/repair matrix exactly for every fixture case, with no path exceeding the declared maximums;
- no provider-native object or free-form output crosses the adapter boundary; and
- `profile_id` in every returned result is always a resolved, valid `AsrProfileCatalogV1` entry — an invalid `requested_profile_id` never reaches `AsrPort` and never appears as an ambiguous/unresolved `profile_id` in a result.

### R3 — Design the approved live benchmark (Phase B scope)

Use a held-out, versioned set of approximately 20 synthetic/licensed narration fixtures, scoped to ASR profile selection only — this is not the P2-T5 end-to-end multimodal report, and does not implement its CLI. The manifest must declare fixture ID, immutable audio hash, language, human reference transcript, expected speech presence, noise/recording condition, duration band, and split membership. Do not mix development and held-out results.

The fixture set must include, at minimum: Vietnamese narration, non-Vietnamese narration, Vietnamese-English code-switching (a common pattern in children's narration involving loanwords), silence-only/no-speech audio, and at least one noise/recording-condition variation per language slice; add regional Vietnamese accent variation only if the synthetic/licensed voice source can produce it without real speaker data.

**Known limitation to record explicitly, not assume away:** this benchmark uses synthetic/TTS or licensed voices. It measures ASR behavior on those voices only and is not evidence of performance on real child speech (pitch, articulation, and disfluency differ materially from adult or synthetic narration). Any future evaluation using real child audio requires its own separate approval and data-governance review under this project's real-child-data prohibition; it is out of scope for this research plan and for P2-T2 implementation.

Measure:

- schema-valid result rate and typed-failure count by code;
- WER and CER, including the versioned text normalizer/tokenizer used for Vietnamese and each other language;
- detected-language accuracy and calibration slices for the auto-detect variant, reported separately from the honor-hint variant, without treating probability (or the hint) as truth;
- segment/word-timestamp completeness and ordering validity;
- latency p50/p95 by stage and profile, plus cold-start separately;
- audio duration, duration after VAD, and any silence-removal/omission observations; and
- peak memory/device/runtime availability if the approved environment exposes it.

The report must label any unavailable metric `NOT_MEASURED`, never zero. It must clearly distinguish fake-adapter contract evidence from live-model benchmark evidence, and must not be presented as, or substituted for, P2-T5's end-to-end fixture report.

### R4 — Failure, privacy, and observability review (Phase B live-execution scope; matrix design is Phase A)

The retry/repair matrix above is Phase A design work and applies from the first adapter implementation. Exercising it against a real provider (confirming real timeout/unavailable/provider-failure behavior matches the declared classification) is Phase B.

Log correlation ID, profile/config hash, duration bucket, status/error code, `attempt_number`, `repair_attempted`, and latency metrics only. Keep source media, transcript content, credentials, endpoint URLs, and raw provider payloads out of standard logs and out of this feature's `evidence/` directory. Store only fixture-only (synthetic) benchmark evidence there; real transcript or audio content must never be committed, even after a future live-model run.

### R5 — Review gate and recommendation (Phase B)

Produce one recommendation table comparing `AsrProfileCatalogV1` candidate entries on quality, latency, runtime compatibility, operational risks, and known limitations. A profile may be proposed for freeze only if it has reproducible configuration/provenance, schema-valid outputs, held-out fixture results, and an explicit reviewer decision. If the evidence is insufficient, retain the fake profile as the only usable entry and mark the candidate `NOT_APPROVED`.

This research task owns the candidate profile definitions and this recommendation table only. Selecting which profile actually runs by default at runtime is a separate decision for the Integration Sprint/an ADR that cites this recommendation; P2-T2 must not be read as pre-authorizing a specific runtime default.

Before any model/runtime/provider freeze, record an ADR (or a `DECISIONS.md` entry) covering at minimum: model revision and weight provenance/license; the language-detection policy default (auto-detect vs. honor-hint) and why; the VAD default and its parameters; the timestamp granularity default (segment-only vs. word-level); the compute/precision profile and timeout budget (including whether the idempotent-timeout retry exception is used, and why); the versioned Vietnamese text-normalization/tokenization specification used for WER/CER; and an explicit statement that supporting evidence is synthetic/TTS-only, not validated against real child speech.

## Exit criteria for this research plan

- [ ] Contract fields, error catalog, and provenance requirements are reviewed with the FEAT-003 shared-contract boundary.
- [x] `AsrResultV1` is specified as a discriminated union (`AsrSuccessV1`/`AsrFailureV1`) with no ambiguous shared-optional fields.
- [x] Case A (quiet-but-successful) vs. Case B (provider/model error) is deterministic via `speech_diagnostic` and `status`, with no third ambiguous outcome.
- [x] The retry/repair matrix fixes cause → error code → retryable/repairable → max attempts → owner for all five error codes, with `attempt_number`/`repair_attempted` semantics defined for testing.
- [x] `attempt_number` is defined as an adapter inference attempt, not a "model-invocation" — Phase A's fake adapter simulates attempts deterministically (`INPUT_NOT_VALIDATED`→`0`, ordinary success/non-retryable failure→`1`, one retry→`2`) with no real model ever invoked; Phase B is where an attempt becomes a real provider/model call.
- [x] `source_audio_ref`+hash is always required and always populated, in every phase including Phase A (from a synthetic fixture already carrying a P2-T1 `PASS`) — it is never `null` in Phase A or any other phase. Separately, the optional `processing_audio_ref` + mandatory-when-set `derivation_provenance` are specified for a future working copy; only these two fields — never `source_audio_ref` — are always `null`/absent in Phase A, and Phase A creates no working copy.
- [x] `requested_profile_id` is a closed `AsrProfileCatalogV1` reference, not a free string; Phase A shipped only deterministic fake profile entries (no model, no dependency, no Whisper runtime); the current Phase B approval covers the additive Whisper candidates, while this readiness layer plans only the two Turbo profiles.
- [x] An out-of-catalog `requested_profile_id` is a deterministic request/schema-boundary validation error raised before `AsrPort` is invoked — distinct from `AsrFailureV1` and specifically distinct from `INPUT_NOT_VALIDATED` (which requires a structurally valid request); `profile_id` in every result is always resolved and unambiguous.
- [x] `language_hint` is optional, provenance-tagged, non-authoritative, and the benchmark design keeps auto-detect and honor-hint metrics separate.
- [x] `no_speech_prob`/ASR diagnostics vs. P2-T1 `PASS`/`RECAPTURE` boundary is documented: diagnostics never override P2-T1's decision or trigger self-recapture.
- [x] `INPUT_NOT_VALIDATED` convention is fixed as a schema-valid `AsrFailureV1`, documented as a defensive second check.
- [x] Scope is confirmed against `SPRINT_1_TASK_ALLOCATION.md`: P2-T2 owns contract/fake/Whisper adapter; P2-T5 owns the CLI and the ~20-fixture end-to-end report; no invented task IDs are used.
- [x] The Round-1 fixture-manifest contract/layout and versioned normalizer specification declare synthetic/licensed provenance and the Vietnamese, non-Vietnamese, code-switching, silence-only, and noise/recording-condition slices; the concrete source decision was resolved as `SYNTHETIC` (TTS) and recorded in `EV-003-T2-04`.
- [x] The two Turbo candidate profiles and fixed controlled variables are recorded and validated before any run.
- [x] The benchmark report template/planned-run contract can show WER/CER, schema validity, language behavior, VAD/timestamp behavior, latency, VRAM, and success/failure coverage without concealing unavailable measurements.
- [x] The readiness/privacy review shows no raw audio, transcript, credentials, endpoint details, or absolute local paths in ordinary logs, source, or feature evidence.
- [x] The current task approval explicitly authorizes the Phase B scope, including controlled live Round-1 execution; the preparation slice did not exercise it, and the subsequently executed local runs plus supplementary Colab validation are recorded in `EV-003-T2-05`, `EV-003-T2-06`, and `EV-003-T2-07`.

## Next gated action after readiness (resolved 2026-08-30)

The fixture-source decision was recorded as `SYNTHETIC` (TTS), and the controlled live Round-1
execution already covered by the Phase B approval was run: 21 `HELD_OUT` synthetic fixtures
across the required scenarios, through the two fixed Turbo profiles (`WHISPER_TURBO_INT8_AUTO_V1`,
`WHISPER_TURBO_FP16_AUTO_V1`). See `evidence/notes/P2_T2_PHASE_B_FIXTURE_PROVENANCE.md` for the
tooling/voice provenance and `evidence/notes/P2_T2_PHASE_B_ROUND1_ASR_REPORT.md` for the measured
WER/CER, language accuracy, latency, VRAM, and typed-failure results. Consistent with the
approved scope, no profile is frozen and no runtime default is selected by this round; that
remains a separate R5/Integration-Sprint/ADR decision.

A supplementary Colab execution was reviewed on 2026-09-01 and recorded as `EV-003-T2-07`.
It confirms the same quality, typed-failure, and pure-noise mismatch findings on the same
manifest, while Tesla T4 latency/VRAM remain separate environment-specific measurements.

# Live Vision schema-output remediation plan

- Feature: `FEAT-018-live-image-canvas-flow`
- Status: `IMPLEMENTED — owner Lightning smoke pending`
- Branch: `codex/feat-018-contract-plan`
- Baseline commit reviewed: `65d639b`
- Scope: Lightning `/v2/vision` live demo path only; no video, auth, durable save, or mobile credential changes.

## Problem statement

The Lightning runtime now loads Qwen3-VL-8B-Instruct and completes generation, but the live
route returns `VISION_SCHEMA_INVALID`. The current route constructs `QwenVisionAdapter` with
`enable_bounded_repair=False`. The adapter therefore accepts only one strict JSON object, rejects
unknown top-level/nested fields and rejects invalid references/types before constructing
`VisionUnderstandingSuccessV2`.

The model prompt requests the exact shape, but prompt-only enforcement is not sufficient for a
generative model. The remediation must make the live path tolerant of bounded, deterministic
shape drift without weakening the public contract or allowing invented observations to pass.

## Owner decisions captured

1. Preserve the current schema wherever possible. A contract change is allowed only if evidence
   proves that the current contract cannot support the required live output; any such change must
   be versioned and separately approved.
2. Allow at most one provider repair retry after the first output fails mapping/schema validation.
3. Do not log raw model output, prompts, image bytes, narration, credentials, or child data.
   Diagnostics must use closed error codes/stage tokens only.

## Existing implementation baseline to reuse

This plan composes existing Qwen work instead of creating a second schema-repair system:

| Baseline | Existing capability | Use in this plan |
|---|---|---|
| `3565c94` — `fix: normalize real VLM payload drift` | FEAT-027 bounded normalizer, strict-mode preservation, alias/wrapper handling, reference remapping, safe candidate filtering and tests | Treat `vision_payload_normalizer.py` as the canonical repair implementation; audit and wire it into the live route |
| `b9a8a07` — `feat(vision): add private schema path diagnostics` | Closed schema-path diagnostic table and privacy tests | Attach the existing in-memory hook to sanitized Lightning logging; do not add a public schema field |
| `6161d3a` / `f3014e5` | Closed mapping diagnostics and B3 coverage | Reuse the existing diagnostic vocabulary and tests |
| `8feb713` / `98349bf` | Live `/v2/vision` route, local model handoff and typed result logging | Change only live wiring and bounded retry behavior |
| `5c6caf3` / `ae13d2d` | Killable subprocess runner and bounded Lightning execution | Preserve process isolation/timeout; measure the second-call cost |

The latest merge `65d639b` is P2-T5 fusion/evaluation work and does not change the Qwen adapter.
The current live gap is in `tools/lightning_vision_v2_server.py`: the normalizer exists but the
route passes `enable_bounded_repair=False` and does not attach the mapping-diagnostic hook.

## Design principles

- Keep `VisionUnderstandingResultV2` as the boundary contract.
- Parse strictly first; never substring-extract arbitrary JSON or silently invent observations.
- Apply only a bounded normalizer for known safe shape drift, then run the complete Pydantic and
  cross-reference validation again.
- Preserve fail-closed behavior for malformed JSON, unsupported semantics, duplicate IDs,
  unresolved references, prohibited claims, and values outside contract bounds.
- A repair retry receives a compact, closed diagnostic category rather than raw validator text or
  the previous model response. The retry cannot change the requested profile or image identity.
- Retry count, repair state, diagnostic category, model/config provenance and final contract status
  remain auditable without exposing content.

## Implementation plan

### 1. Establish the live failure taxonomy

- Reuse the closed categories already defined by FEAT-003/FEAT-027. Do not introduce a parallel
  error enum or duplicate schema-path table.
- Confirm closed diagnostic categories for strict JSON parse failure, non-object root,
  top-level key rejection, missing required collection, nested extra field, invalid field type,
  invalid enum/language shape, duplicate observation ID, and reference-integrity failure.
- Attach the existing `on_mapping_diagnostic` hook per request using a local bounded collection.
  Ensure the Lightning log records only `stage`, closed diagnostic(s), `attempt`,
  `repair_attempted` and final typed error code.
- Keep the HTTP boundary behavior unchanged: typed provider/schema failures remain contract results;
  infrastructure failures remain HTTP 503.
- Reuse the existing readiness check for the configured model/profile without loading raw output.

### 2. Harden the prompt and generation contract

- Keep one canonical prompt in the Lightning adapter path and derive it from the versioned profile
  identity where practical, avoiding a second divergent prompt.
- State the exact JSON shape with a minimal valid empty example and explicit `null`/array rules.
- Keep deterministic decoding: no sampling, bounded token count, and no decorative explanation.
- Verify the model generation call does not rely on ignored sampling flags; warnings must not be
  mistaken for schema success.
- Do not make constrained decoding a prerequisite for this fix. If evaluated, it is a later
  capability experiment behind a feature/configuration check and cannot replace the existing
  parser, normalizer or final Pydantic validation.

### 3. Enable bounded normalization safely

- Reuse the existing pure normalizer from `3565c94` and the existing diagnostic path rather than
  adding a second parser.
- Run the existing FEAT-027 regression suite unchanged before wiring the live route.
- Enable bounded repair for the live route only after confirming its allowed transformations:
  known wrapper/result shapes, known field aliases, omitted optional/empty collections, safe
  confidence coercion, and safe dropping of provider metadata.
- Do not broaden FEAT-027's accepted shapes while wiring it. Any transformation outside the
  approved normalizer requires a separate decision and regression fixture.
- Do not normalize away unknown semantic claims, create IDs from meaning, resolve missing refs by
  guessing, or convert an unrelated payload into an empty success.
- Validate the normalized payload against the full `VisionUnderstandingSuccessV2` schema and all
  duplicate/reference/policy invariants. If validation fails, return typed
  `VISION_SCHEMA_INVALID` with a closed diagnostic.

### 4. Add one bounded repair retry

- Add the retry at the adapter decision boundary after the existing `_map_raw_output()` returns a
  typed schema failure. The HTTP route must not parse provider text or construct a second result
  type.
- On first mapping/schema failure only, issue one additional generation request using the same image,
  profile, correlation ID and source hash.
- Use a repair-specific prompt that contains only the closed diagnostic class and the required
  output rules; never include raw model output or unfiltered Pydantic errors.
- Do not retry input-admission, policy, device, timeout, or source-integrity failures.
- Enforce a hard maximum of two provider generations per user request and record
  `attempt_number`/`repair_attempted` consistently.
- If the retry still fails, return the existing typed failure without provider-output leakage.

The current `KillableSubprocessQwenGenerationRunner` creates a fresh worker and loads the local
model for each `generate()` call. The second repair attempt may therefore reload four checkpoint
shards. The implementation must measure this on Lightning, keep the two-call hard cap, and avoid
claiming a latency improvement. Same-worker optimization is out of scope unless the smoke evidence
shows the approved timeout cannot accommodate the second load and a separate runtime change is
approved.

### 5. Contract and regression coverage

- Re-run the existing FEAT-027 normalizer tests first; preserve strict-mode and privacy guarantees.
- Add deterministic unit tests for every accepted bounded repair and every fail-closed case.
- Add tests proving repair cannot invent entities, bypass reference integrity, duplicate IDs, or
  bypass lexical content policy.
- Add route-level tests for: valid first output, valid after one repair, invalid after repair,
  non-retryable failure, retry budget exhaustion, and closed logging fields.
- Add an integration test proving the live route enables the approved normalizer and diagnostic
  hook while the default adapter/test construction remains strict.
- Add a live-shaped fixture suite using sanitized Qwen outputs captured as contract-safe fixtures;
  raw provider output must remain out of Git/evidence.
- Keep existing FEAT-003/FEAT-018 contract versions and downstream Android/Pixi payloads unchanged
  unless a separately approved migration becomes necessary.

### 6. Lightning verification and evidence

- Run repository tests and security validation locally.
- On Lightning, run the model/environment readiness check before a live call.
- The owner manually runs a small smoke matrix under the approved 25-credit ceiling; Codex does not
  call the provider.
- Verify logs contain only closed diagnostics and that successful responses pass the same schema
  validation used by the backend.
- Store sanitized results under this feature's `evidence/` directory: commit, profile/config hash,
  attempt counts, typed outcomes, latency and no-content diagnostics. Do not store raw model output,
  images, tokens or prompts.

## Acceptance criteria

- [ ] Existing `VisionUnderstandingResultV2` remains the live boundary, unless a separately approved
      versioned change is proven necessary.
- [ ] A valid Qwen JSON object succeeds on the first attempt.
- [ ] Known safe shape drift is normalized and revalidated deterministically.
- [ ] At most one repair retry occurs, never more than two provider generations per request.
- [ ] A retry cannot fabricate observations, resolve unknown references, bypass policy, or convert
      an invalid semantic payload into success.
- [ ] Malformed/unsafe output returns typed `VISION_SCHEMA_INVALID` with a closed diagnostic.
- [ ] No raw output, prompt, image bytes, narration, credential or child data appears in logs,
      API results, committed fixtures or evidence.
- [ ] Successful live responses are accepted by the same contract validator used by downstream
      workflow code and continue through Gate A/P1/Gate B without adapter-specific branching.
- [ ] Offline parser/adapter and route tests pass; the live Lightning smoke matrix is recorded by
      the owner under the existing quota gate.
- [ ] `python tools/validate_repository_security.py` passes before commit/push.

## Explicit non-goals

- No video or ASR work.
- No mobile endpoint/token changes.
- No auth or durable persistence implementation.
- No raw-output logging for debugging.
- No unbounded JSON repair, generic LLM repair service, or silent schema widening.

## Approval gate

Implementation is blocked until the owner approves this plan and the exact bounded repair/retry
policy is recorded in `features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md`.

## Detailed implementation contract

### 0. Integration boundary and ownership

- FEAT-027 owns the generic normalizer behavior delivered in `3565c94`.
- FEAT-003 owns `VisionUnderstandingResultV2`, error/detail enums and schema-path diagnostic
  vocabulary. FEAT-018 consumes those contracts and does not fork them.
- FEAT-018 owns live Lightning wiring, the one-repair execution policy, route-level observability
  and owner-run smoke evidence.
- If the FEAT-027 normalizer must change, update its plan/decision/evidence and tests in the same
  change; do not silently alter it from the FEAT-018 route.
- Strict default behavior remains the safety baseline for unit tests and non-demo callers. Only
  the explicitly constructed live demo adapter receives bounded mode.

### A. Current live request path to preserve

The implementation must retain this order:

1. `tools/lightning_vision_v2_server.py` authenticates the backend caller.
2. The request validates source identity, base64, size, MIME signature, SHA-256 and admission.
3. The server writes a temporary image and creates a verified relative image reference.
4. `QwenVisionRuntimeConfig` selects the explicit local Qwen snapshot and CUDA device.
5. `QwenVisionAdapter.understand()` resolves the frozen V2 profile and verifies the image hash.
6. The generation runner loads Qwen3-VL and returns provider text.
7. The adapter parses, normalizes only when enabled, validates the V2 success/failure model and
   runs the content policy.
8. The server serializes the typed result and restores the caller-visible source artifact reference.

No retry or repair may bypass steps 1–5 or run against a different image/profile.

### B. Proposed state machine

```text
ADMITTED
  -> GENERATE(attempt=1)
      -> RUNTIME_FAILURE      => typed runtime failure; no repair retry
      -> RAW_PARSE_FAILURE    => BOUNDED_REPAIR(attempt=2)
      -> SHAPE_FAILURE        => BOUNDED_REPAIR(attempt=2)
      -> REFERENCE_FAILURE    => BOUNDED_REPAIR(attempt=2) only if diagnostic is repairable
      -> POLICY_BLOCK         => typed policy failure; no repair retry
      -> VALID                 => SUCCESS

BOUNDED_REPAIR(attempt=2)
  -> GENERATE with repair prompt and closed diagnostic
      -> VALID                 => SUCCESS(repair_attempted=true, attempt_number=2)
      -> anything invalid      => typed VISION_SCHEMA_INVALID, attempt_number=2
```

The repair transition is entered only for output-mapping/schema failures. It is not entered for
model loading, CUDA, timeout, source hash, admission, profile, or content-policy failures. The
adapter must enforce a local counter so a caller cannot cause a third provider generation.

### C. Allowed normalization allowlist

The normalizer at
`backend/src/sketch2life/infrastructure/ai/vision_payload_normalizer.py` must be reviewed
against this allowlist before it is enabled on the live route:

- unwrap one or two known provider envelope keys (`result`, `output`, `response`, `analysis`,
  `observations`, `data`) only when the nested object contains a recognized collection;
- map known singular/plural collection aliases to the five canonical collections;
- accept a collection object containing a known `items`/`observations`/`records`/`data` list;
- map known text aliases to the canonical `label`, `predicate` or `note` field and wrap a plain
  string into the versioned text/language shape;
- map `id` to `observation_id` and normalize it to the contract ID form;
- map known reference aliases (`actor`, `object`, `subject`, `evidence`) to their typed `*_ref`
  fields;
- normalize a scalar evidence reference into a one-item list;
- normalize language tags and non-finite/out-of-range confidence into the contract-safe form;
- use empty arrays for omitted collections only; never use an empty array to hide an unrecognized
  root object;
- remove provider metadata/unknown optional keys only after the payload has a recognized
  observation collection.

Each allowlisted transformation must set `repair_attempted=true` and be followed by complete
schema validation.

### D. Disallowed normalization and fail-closed cases

The implementation must reject rather than repair when any of these conditions apply:

- invalid JSON, duplicate JSON keys, non-object JSON root, or arbitrary prose around JSON;
- root object contains no recognized observation collection;
- text value is absent/empty or cannot be represented by the canonical text shape;
- duplicate normalized observation IDs remain ambiguous;
- relation endpoints, action references or theme evidence cannot resolve to the permitted kind;
- a relation self-references or a theme has no valid evidence after filtering;
- a payload contains a prohibited claim or attempts to infer child/person traits;
- a repair would require inventing semantic labels, references, confidence values or evidence;
- a model response tries to provide contract envelope fields (`status`, `correlation_id`, model
  provenance, policy state, hashes, timestamps) instead of observation collections.

The final `VisionUnderstandingSuccessV2.model_validate()` and its cross-collection validator are
the source of truth; the normalizer is not allowed to replace those checks.

### E. Repair prompt and retry identity

The retry prompt must be built from:

- the same canonical task prompt;
- a fixed instruction to emit one JSON object only;
- one closed diagnostic token, such as `STRICT_JSON_PARSE_FAILED`,
  `SCHEMA_MISSING_REQUIRED_FIELD`, `SCHEMA_EXTRA_FIELD`, or
  `SCHEMA_REFERENCE_INTEGRITY_VIOLATION`;
- the canonical root keys and minimal empty-array example.

It must not contain raw provider output, raw Pydantic messages, image bytes, file paths,
credentials, narration text, or user identifiers. The second call must preserve:

- correlation ID;
- source image SHA-256 and temporary image path;
- requested profile ID and profile/config hash;
- model revision and runtime device;
- timeout budget and maximum output token budget.

The result envelope rules are fixed:

| Outcome | `attempt_number` | `repair_attempted` | `error_code` |
|---|---:|---:|---|
| First-call success | 1 | false | none |
| Repair-call success | 2 | true | none |
| First-call schema failure without repair execution | 1 | false | `VISION_SCHEMA_INVALID` |
| Repair-call schema failure | 2 | true | `VISION_SCHEMA_INVALID` |
| Runtime/device/timeout failure | 1 or 2 as applicable | false | existing typed runtime code |

No retryable flag is set for schema failure; the retry is internal and bounded, not a request for
the mobile client to repeat the operation.

### F. Observability contract

The Lightning server may log only fields from this closed set:

- `correlation_id` only if it is already a non-sensitive opaque request ID;
- `status`, `error_code`, `error_detail`, `mapping_diagnostics`;
- `attempt_number`, `repair_attempted`;
- `profile_id`, `model_revision`, `config_hash`, `profile_catalog_hash`;
- stage name, latency bucket and retry decision.

The server must not log raw output, prompt text, image path/content, base64, narration, exception
messages that may contain paths or provider text, auth headers, or child data. Public failure
payloads use the existing closed `VisionMappingDiagnosticV2` enum only.

### G. File-level change map

Implementation, after approval, is expected to be limited to these areas:

| File/area | Planned change | Contract impact |
|---|---|---|
| `tools/lightning_vision_v2_server.py` | Use approved repair-enabled adapter configuration; keep prompt and source handoff; add safe outcome logging | No public schema change |
| `backend/src/sketch2life/infrastructure/ai/qwen_vision.py` | Add mapping-failure decision point and one repair-generation path; preserve typed failure matrix | Existing V2 fields only; attempt/repair already exist |
| `backend/src/sketch2life/infrastructure/ai/vision_payload_normalizer.py` | Audit/adjust only allowlisted transformations and diagnostics | No public schema change |
| `backend/src/sketch2life/contracts/schemas/vision_v2.py` | Change only if an evidence-backed contract gap is found; otherwise untouched | Versioned migration required if changed |
| `backend/tests/unit/test_qwen_vision_adapter.py` | Unit coverage for parse, normalization, retry and fail-closed cases | Test-only |
| `backend/tests/unit/test_qwen_vision_schema_path_diagnostic.py` | Closed diagnostic/path coverage | Test-only |
| `backend/tests/contract/` | Lightning route and serialized V2 envelope coverage | Test-only unless gap found |
| `features/FEAT-018.../evidence/` | Sanitized verification note and metrics only after owner-run live smoke | Evidence only |

No mobile source, PixiJS source, asset catalog, auth adapter or persistence schema is in scope.

## Detailed test matrix

### Unit tests

1. Valid canonical JSON succeeds on attempt 1 with `repair_attempted=false`.
2. Complete JSON fence is accepted only as the existing bounded fence case.
3. Known root wrapper and collection aliases normalize to success.
4. Known scalar text/reference/confidence drift normalizes to success only when final validation
   passes.
5. Missing optional collections become empty arrays; missing required observation content fails.
6. Unknown metadata is removed only from a recognized observation payload.
7. Malformed JSON, duplicate keys, prose, array root and metadata-only root fail closed.
8. Duplicate IDs, ambiguous ID aliases, self-relations, unresolved references and invalid evidence
   fail closed after normalization.
9. Prohibited claims remain policy failures and never become schema successes.
10. First schema failure invokes exactly one repair generation with a closed diagnostic.
11. Repair success has `attempt_number=2`, `repair_attempted=true` and valid provenance.
12. Repair failure has a typed schema failure and cannot invoke a third generation.
13. Runtime/device/timeout failure does not invoke schema repair.
14. Hook/log failures cannot alter the typed result or leak raw content.

### Contract/route tests

- Validate the complete `/v2/vision` success envelope after first-call success.
- Validate the complete envelope after repair-call success.
- Validate every schema-failure matrix row, including `model_provenance`, attempt and repair flags.
- Confirm source artifact reference is restored to the caller reference after temporary-file use.
- Confirm no provider response, prompt, token or path appears in serialized responses or captured
  log records.
- Confirm mobile-facing behavior remains: typed failure is surfaced as an AI failure state and no
  Pixi/Gate B transition occurs until a valid success result exists.

### Lightning smoke matrix

The owner manually runs, with synthetic/non-child images only:

| Case | Expected result | Provider calls |
|---|---|---:|
| Canonical/empty-observation response | `SUCCEEDED`, attempt 1 | 1 |
| Known shape drift | `SUCCEEDED`, repair flag depends on normalization | 1 |
| First output malformed, repair valid | `SUCCEEDED`, attempt 2 | 2 |
| First and repair output invalid | `VISION_SCHEMA_INVALID`, attempt 2 | 2 |
| Device/model unavailable | typed runtime failure | 1 |

The smoke run must report request IDs, typed outcomes, attempt counts, latency and config/profile
hashes only. It must not include raw provider text or image content. The total remains inside the
owner-approved 25-credit ceiling; Codex does not issue these calls.

## Rollout and rollback

1. Implement behind the existing live route only; fixture/offline behavior remains unchanged.
2. Run focused tests, contract tests, lint/type checks, repository security validation and diff
   checks.
3. Start Lightning with the exact model snapshot/revision and run readiness before the owner smoke.
4. If live output is still unstable, disable the live repair-enabled route configuration and retain
   the typed fail-closed path; do not widen the schema under pressure.
5. Rollback is the prior commit/configuration where `enable_bounded_repair=False` and no repair
   retry is active. No database or mobile migration is required.

## Definition of done

The task is complete only when the approved implementation passes the local matrix, the owner-run
Lightning smoke matrix demonstrates either valid first/second-attempt results or typed fail-closed
outcomes, the serialized success is accepted downstream, evidence is sanitized and stored under
FEAT-018, repository security validation passes, and the approval/status records are updated.

## Implementation result — 2026-09-22

- Implemented the approved live-route wiring. The Lightning `/v2/vision` construction now enables
  the existing FEAT-027 bounded normalizer, captures only closed mapping-diagnostic tokens, and
  supplies a repair prompt that cannot echo raw provider output, narration, image data or secrets.
- Added one schema-repair generation at most after the first mapping/schema failure. The strict
  adapter path remains unchanged when bounded repair is disabled, and no third provider generation
  is possible through this transition.
- Added adapter regression coverage for repair success, repair fail-closed behavior, strict-mode
  non-retry, and route repair-prompt privacy/deduplication.
- Fixed the live runtime environment fallback so a blank canonical model variable no longer blocks
  startup; the owner convenience alias `MODEL_DIR` is normalized before the legacy
  `SKETCH2LIFE_VLM_ROOT` fallback. The selected value must still point to the real local model
  snapshot.
- Local verification is recorded in the feature evidence note. Owner-run Lightning smoke remains
  the only open validation item; Codex has not issued a live provider request.

# FEAT-027 implementation plan — VLM schema normalization

## 1. Scope

### 1.1 Top-level normalization

In bounded real-AI mode only:

- guarantee the five canonical collections exist;
- accept a single record or a known wrapper such as `items`/`observations`
  and convert it to a list;
- map safe field aliases (`id` → `observation_id`, `name`/`text` → the
  relevant text field, `subject`/`object`/`actor` → reference fields);
- remove unknown provider metadata keys before contract validation;
- retain strict rejection in default/test mode.

### 1.2 Record normalization

For each collection:

- normalize IDs to lowercase `[a-z0-9-]+`; generate deterministic local IDs
  only when an observation has no ID;
- maintain an old-ID → normalized-ID map and apply it to references;
- normalize `label`, `predicate`, and `note` from scalar text or safe text
  objects into `ObservedTextV1` shape;
- normalize language strings and incomplete declarations without claiming
  ground truth; unknown language becomes `NOT_DETERMINED`;
- convert finite numeric confidence strings to numbers; invalid/out-of-range
  confidence becomes `null` in bounded mode;
- supply nullable action references when omitted;
- do not fabricate relation endpoints or theme evidence references.

### 1.3 Conservative candidate filtering

- retain valid entities/actions after normalization;
- drop malformed relations whose endpoints cannot be resolved to an allowed
  entity/action and emit a closed diagnostic;
- drop malformed themes whose evidence references cannot be resolved;
- drop malformed ambiguous regions rather than creating geometry or content;
- preserve all valid candidates and never replace the complete observation set
  with a case-specific fixture or fallback claim.

### 1.4 Validation and diagnostics

- validate the normalized payload with `VisionUnderstandingSuccessV2`;
- if validation still fails, return the existing typed failure and expose only
  closed mapping/schema-path diagnostics;
- add a sanitized normalization diagnostic enum for dropped records and
  normalized fields where needed; never include raw values or Pydantic error
  text in the contract;
- set `repair_attempted=true` whenever any bounded normalization changes the
  payload.

### 1.5 Regression coverage

Add tests for:

- missing collections and singular collection wrappers;
- `id` aliases, invalid IDs, reference remapping and duplicate IDs;
- scalar/incomplete text declarations in Vietnamese;
- string/invalid confidence;
- missing action references;
- safe relation/theme drop when references are invalid;
- unknown keys in bounded mode versus strict mode;
- a representative case-02-shaped payload that becomes a valid success;
- unsafe payloads that remain typed failures.

## 2. Acceptance criteria

- The representative case-02-shaped real-output payload normalizes to a valid
  `VisionUnderstandingSuccessV2` without fixture observations.
- Every successful adapter result passes the V2 Pydantic contract and reference
  integrity validator.
- Default strict tests still reject malformed payloads.
- Bounded mode never fabricates relation/theme endpoints or persists raw model
  output.
- Existing case-01, Qwen adapter, schema-path, FEAT-024 workflow, and catalog
  tests pass.
- `python tools/validate_architecture.py` remains valid.
- `python tools/validate_repository_security.py` is run before commit; any
  unrelated repository blocker is recorded in evidence.

## 3. Implementation order

1. Record approval and add closed diagnostic contract if required.
2. Implement pure normalization helpers with no provider dependency.
3. Connect bounded normalizer to Qwen mapping.
4. Add representative regression payloads and strict-mode tests.
5. Run focused tests, compile, Ruff, architecture and security checks.
6. Run case 01 and case 02 on Lightning; retain only typed result metadata.

## 4. Non-goals

- no fixture fallback;
- no model replacement or retraining;
- no UI/video/Pixi changes;
- no silent change to catalog ranking;
- no guarantee that arbitrary unsafe model output can be made valid without
  dropping the unsafe claim.

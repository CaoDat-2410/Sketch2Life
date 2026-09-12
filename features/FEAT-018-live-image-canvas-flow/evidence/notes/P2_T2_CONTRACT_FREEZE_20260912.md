# FEAT-018 P2-T2 RawUnderstandingResultV1 contract freeze

Status: offline implementation evidence, 2026-09-12.

## Approved boundary

FEAT-018 consumes FEAT-003 `VisionUnderstandingResultV2` through the typed local adapter boundary
and maps it into the FEAT-018-owned `RawUnderstandingResultV1`. FEAT-017's flat V1 and remote HTTPS
adapter are not used. No model, provider, network, GPU or Lightning execution occurred for this
slice.

## Frozen invariants

- Discriminated `SUCCEEDED`/`FAILED` result with `contract_name=RawUnderstandingResultV1` and
  `contract_version=1.0`.
- Correlation/session identity and an immutable source image reference with a required lowercase
  64-character SHA-256.
- Typed entity, action, relation, theme and ambiguous-region observation groups.
- Confidence values are bounded to `0..1`; missing upstream confidence is rejected rather than
  defaulted.
- ASR and fused claims are separate typed collections; conflicts are preserved. The current V2
  upstream contract does not provide an uncertainty field, so Raw records
  `uncertainty_status=NOT_PROVIDED` rather than inventing a derived confidence formula.
- Narration state is explicit: `NOT_SUPPLIED`, `ASR_SUCCEEDED`, or `ASR_FAILED`; ASR failure keeps
  a typed failure instead of collapsing into an empty claim list.
- When ASR is supplied, its correlation ID must match the vision result; mismatches are rejected
  before construction of the Raw result.
- Upstream profile/catalog/config/model provenance is retained on successful model results.
- Typed failure code, retryability and bounded upstream detail; no raw provider payload.
- `gate_a_required=true` is mandatory. The contract has no eligibility, personality, readiness,
  activity, objective or Gate B decision fields.
- Extra fields, broken references, self-relations and unbounded collection sizes are rejected.

## Implementation and verification

The offline implementation consists of the approved FEAT-018 schema, mapper and provider-neutral
port, with unit and contract tests. Mapping is deterministic and performs mandatory source-hash and
correlation checks before constructing the Raw result. Only injected typed objects/fakes are used.

Focused FEAT-018 tests: 17 passed.
Related vision/Qwen/ASR tests: 801 passed, 5 skipped.
Ruff: passed. Mypy: passed for all changed Python source files.

Repository validators and `git diff --check` are run as the final handoff checks. This note contains
no raw image, prompt, model output, credential, endpoint, secret or absolute machine path.

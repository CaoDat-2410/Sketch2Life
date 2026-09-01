# P2-T3 Phase B B1 implementation and validation

- Evidence ID: `EV-003-T3-02`
- Date: 2026-09-01
- Owner: Person 2
- Scope: Approved B1 local code/configuration and no-GPU tests only
- Approval authority: `approvals/TASK_APPROVAL.md` (P2-T3 Phase B)
- Decision record: `docs/adr/ADR-0007-vision-runtime-dependency-pinning-and-qwen3-vl-candidate-profile.md`

## Result

B1 is implemented as an additive V2 contract and isolated Qwen adapter skeleton. The Phase A
V1 module, fake adapter, V1 catalog, V1 hash functions, and V1 behavior were not edited. A
committed regression test pins the existing fake profile and catalog SHA-256 values:

```text
vision_profile_config_hash(V1 fake)    = 065cf4e6ff19abca12e95804ba6d35924d54e3fd727d2df9d82a6d3f8ed37c15
vision_profile_catalog_hash(V1 catalog) = 4038274c65f387a8e04a813d31d9295f3da31e08b10aa4f9fec49bb550a900dd
```

The new V2 surface contains one canonical static profile:

```text
VisionProfileIdV2 = QWEN3_VL_8B_INSTRUCT_BF16_V1
compute_profile   = GPU_BF16
model             = Qwen/Qwen3-VL-8B-Instruct
revision          = 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
license           = apache-2.0
```

V2 profile/catalog hashes are independently named and typed. The V2 request resolves only
against the V2 static catalog; an adapter-side resolve miss produces the typed
`PROFILE_NOT_RESOLVABLE` input failure at attempt `0`.

## Implemented artifacts

- `backend/src/sketch2life/contracts/schemas/vision_v2.py` — frozen, extra-forbidden V2
  request/result/profile/catalog/provenance/decoding models, V2 outcome matrix, V2 hashes,
  strict reference validation, and provenance applicability rules.
- `backend/src/sketch2life/application/ports/vision_understanding_v2.py` — provider-neutral V2
  port.
- `backend/src/sketch2life/infrastructure/ai/qwen_vision_runtime_config.py` — explicit
  constructor-injected local model/cache/device configuration; no shared `Settings` change and
  no default path.
- `backend/src/sketch2life/infrastructure/ai/qwen_vision.py` — lazy optional imports, typed
  model/device/runtime failures, source and processing SHA-256 ingress checks, P2-T1 `PASS`
  gate, strict JSON mapping, lossless complete-fence unwrap only, one sanitized transient retry,
  and a killable subprocess timeout runner.
- `backend/tests/unit/test_vision_phase_b_b1_contracts.py` — V1 golden constants and V2 contract
  matrix.
- `backend/tests/unit/test_qwen_vision_runtime_config.py` and
  `backend/tests/unit/test_qwen_vision_adapter.py` — no-GPU configuration, adapter, retry,
  parser, integrity, policy, and optional-runtime tests.
- `backend/.vision.env.example` — placeholders only.
- `backend/pyproject.toml` — uninstalled exact-pinned `vision-qwen` optional extra.
- `.gitignore` — only the approved local vision model/cache/future image paths were added.

## Provenance and dependency record

The selected exact optional pins are `accelerate==1.10.1`, `qwen-vl-utils==0.0.14`,
`torch==2.8.0`, and `transformers==4.57.6`. The official Qwen guidance establishes the
Transformers route and its minimum/deployment dependency guidance; the release pages are linked
in ADR-0007. No package from the extra was installed, and no model, weight, cache, or provider
runtime was downloaded.

The official source did not publish a single repository-level SHA-256 digest that was verified
for the candidate before download. The V2 provenance therefore carries the explicit paired
absence reason `SOURCE_DOES_NOT_PUBLISH_A_DIGEST`; it does not fabricate a weight hash.

## Timeout and privacy boundary

The default runner owns synchronous loading/generation in a spawned process. The parent polls the
profile timeout, terminates and joins the worker on expiry, and has a kill fallback. A timeout
may terminate attempt `1` or attempt `2`, is never retried, and cannot produce a third attempt.
No provider deadline/cancellation parameter is invented or passed. Exact model/device cleanup,
provider API behavior, and live CUDA/BF16 feasibility remain B2 verification items.

Raw model output remains in memory only long enough for mapping and policy evaluation. Results,
logs, and this evidence note contain only safe typed identifiers/counts; no credentials,
endpoints, local model paths, weights, prompts, model output, or child data are recorded.

## Contract-consistency correction (2026-09-01)

The Qwen parser previously returned `(None, True)` for a complete Markdown fence whose decoded
JSON root was not an object. That diverged from the unchanged V1 fake parser and incorrectly
claimed a repair had occurred. The rule is now explicit and enforced: `repair_attempted=True` is
possible only when one complete fence is losslessly removed and the decoded root is an object;
fenced arrays, scalars, and `null` remain unrepairable schema failures. Complete fenced objects,
including objects that later fail strict schema validation, retain `repair_attempted=True`.

Focused regression coverage in `test_qwen_vision_adapter.py` exercises fenced `[]`, `42`, and
`null`, asserting `VISION_SCHEMA_INVALID` / `OUTPUT_MAPPING_FAILED`, `repair_attempted=False`,
and no raw provider text in the result. Existing fenced-object and plain JSON behavior remains
covered by the same suite.

## Validation performed

The focused no-GPU suite passed with `70 passed, 5 skipped`. The skips are the deliberate input
detail cases in a parametrized test that are already exercised by dedicated attempt-zero tests.
The new tests cover:

- V1 digest and identity regression, V1/V2 type separation, V2 static catalog/hash behavior,
  derivation pairing, dependency-pin ordering/duplicates, and weight-hash absence pairing.
- Every V2 success, input, model-unavailable, timeout, transient, permanent, schema-invalid,
  and prohibited-claim matrix family, including post-retry timeout/permanent/schema/policy traces.
- Required collections, nested `extra="forbid"`, duplicate/reference classification, model
  provenance presence/absence, and raw-output field exclusion.
- P2-T1 media `PASS`, source/processing integrity, profile resolution, lossless parser behavior,
  typed missing-optional-runtime/device/provider failures, policy blocking, and the injectable
  Transformers seam without importing Qwen packages or using a GPU.

Final verification passed: the full backend suite returned `380 passed, 5 skipped`; Ruff returned
`All checks passed!`; strict mypy returned `Success: no issues found in 49 source files`;
`validate_harness.py` returned `HARNESS_VALID`; `validate_repository_security.py` returned
`REPOSITORY_SECURITY_VALID`; `validate_architecture.py` returned `ARCHITECTURE_VALID`;
`validate_skeleton.py` returned `SKELETON_VALID`; and `git diff --check` returned clean. No B2-B5
execution or live provider call is part of this evidence.

## B2-only unresolved items

- Verify the exact pinned Qwen processor/model loading and generation-parameter mapping.
- Verify local VRAM/CUDA/BF16 feasibility and the subprocess cleanup behavior on the approved
  development hardware, using synthetic fixtures only.
- Verify any provider-level cancellation/deadline capability before adding such a parameter.
- Revisit the weight digest only if the official source publishes a usable digest; otherwise keep
  the explicit absence reason.

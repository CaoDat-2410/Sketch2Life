# FEAT-018 P2-T2 live Lightning execution plan - draft

STATUS: DRAFT
NOT AN APPROVAL
NOT AN IMPLEMENTATION AUTHORIZATION

Date: 2026-09-13

This document is a plan correction only. Reading or revising it performs no
Lightning, GPU, model, provider, network, subprocess, or benchmark execution.
It does not change code, contracts, prompts, profiles, approvals, evidence,
fixtures, or runtime configuration. A future live run requires a separate
owner-approved addendum that names the exact runtime source commit, fixture,
prompt, runner, hardware, budget, redaction rules, and evidence paths.

The live decision identifiers in this document are owned by this plan and are
exactly P2T2-LIVE-D1 through P2T2-LIVE-D12. They are not P2-T1 decisions and
must not be recorded or described as P2-T1 decisions. All twelve decisions
remain open until a later owner approval resolves them explicitly.

Planning reference only: the repository HEAD observed while this draft was
corrected was 86f953e436d5e4adebe6a7a5c9f0eba71166c003. That hash is not an
execution authorization. A future approval must pin a separate exact runtime
source commit and the Lightning session must verify that same commit before
any model invocation.

## 1. Objective and exact scope

The proposed future smoke run is exactly one owner-approved, non-sensitive
JPG/PNG image through the existing backend-only FEAT-003
VisionUnderstandingResultV2 boundary and the existing qwen_vision.py
QwenVisionAdapter, followed by the existing FEAT-018
map_vision_result_to_raw mapper. The run records one typed V2 outcome and one
mapped RawUnderstandingResultV1 outcome, or a typed terminal outcome if a
stop gate fires.

The run records truthful cardinality at the phase boundary; it never fabricates
a call or attempt:

- A stop before invoking the adapter records `adapter_call_count=0` and
  `attempt_count=null`. This includes approval, checkout, fixture, readiness,
  configuration, policy, hardware, manifest, and runner-boundary stops. No V2
  result, Raw mapping, or adapter timing is claimed for this path.
- If the adapter is invoked but rejects the input before model generation, it
  records `adapter_call_count=1` and `attempt_count=0`. This is the existing
  typed input-validation path and is not a model-reaching functional pass.
- A model-reaching adapter call records `adapter_call_count=1` and
  `attempt_count` in `{1, 2}`. Attempt 2 is permitted only after an explicitly
  classified transient runtime failure on attempt 1, inside the one adapter
  call. It never becomes 3 and there is no outer retry.

Every authorized run attempt writes exactly one sanitized JSON/Markdown
evidence pair, including a pre-adapter terminal outcome. If evidence creation
is impossible, the harness writes only a safe local ignored incident record at
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; that incident is not
indexed and never substitutes fabricated call or attempt values.

The future run uses exactly the owner-approved runner boundary from
P2T2-LIVE-D1. It does not rely on a constructor default.

In scope:

- The existing FEAT-003 V2 profile
  QWEN3_VL_8B_INSTRUCT_BF16_V1 from vision_profile_catalog_v2().
- The existing local Qwen adapter in
  backend/src/sketch2life/infrastructure/ai/qwen_vision.py, read-only.
- The existing QwenVisionRuntimeConfig, no-model-load environment readiness
  inspection, and typed content-policy boundary, read-only.
- The existing FEAT-018 mapper and RawUnderstandingResultV1 contract, read-only.
- One exact source image, its immutable source identity, its staged
  session-local reference, and the source SHA-256 relationship.
- One Lightning Studio GPU session, subject to the exact TTL and budget
  decision in P2T2-LIVE-D2.
- One sanitized feature-local evidence pair at the exact paths in Section 7,
  created only after a later execution approval.

The V2 profile is consumed exactly as currently defined:

- model identifier: Qwen/Qwen3-VL-8B-Instruct;
- model revision: 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b;
- profile timeout_seconds: 120.0;
- adapter version: qwen3-vl-local-adapter-v2-b1;
- greedy decoding with sampling_enabled=false, beam_count=1,
  repetition_penalty=1.0, seed=0, and max_new_tokens=512;
- image preprocessing identity: qwen3-vl-processor-config-b1;
- exact dependency pins: accelerate==1.10.1, qwen-vl-utils==0.0.14,
  torch==2.8.0, and transformers==4.57.6.

The V2 result is mapped into FEAT-018's already-closed
RawUnderstandingResultV1 contract. The mapper receives the approved synthetic
smoke-session identifier, the staged source digest, the request correlation
ID, and asr_result=None. The mapped envelope therefore retains
gate_a_required=true and narration_status=NOT_SUPPLIED without fabricating
adult confirmation, narration, eligibility, or personality information.

Out of scope and preserved exclusions:

- FEAT-017's remote HTTPS adapter and LightningVisionAdapter; this plan uses
  only the local qwen_vision.py adapter boundary.
- Any FEAT-003 code, contract, prompt, profile, dependency, fixture, runner,
  scoring, benchmark, or historical-evidence change.
- ASR/Whisper execution is excluded from this plan. The image-only smoke run
  assumes ASR_EXCLUDED, subject to the owner's explicit resolution of
  P2T2-LIVE-D3. If the owner wants live narration, this plan remains blocked
  and a separate P2-T3 ASR approval is required.
- Mobile code, mobile builds, mobile transport, mobile credentials, and
  Lightning credentials or endpoints in mobile.
- Gate A UI, adult confirmation/correction, P1ContextV1, eligibility,
  ActivityTemplateV1, P1 filtering, fit computation, or Gate B.
- P2-T4 pilot diagnostics, P2-T5 full evaluation, provider benchmark work,
  p50/p95 benchmark reporting, quality scoring, and production moderation
  claims.
- P3 renderer/assets and P4 provider/media/cache/fallback work.
- Shared session, idempotency, gallery, feedback, handoff, API, queue, or
  production integration.
- Any live execution before a separate approval has resolved
  P2T2-LIVE-D1 through P2T2-LIVE-D12.
- Any new production code, glue code, CLI, wrapper, test, evidence writer,
  approval mutation, commit, or push under this draft.

## 2. Topology, ownership, and explicit construction boundary

The only proposed data path is:

local preflight -> one Lightning session -> staged relative image reference
-> one QwenVisionAdapter.understand() call -> typed V2 result
-> existing FEAT-018 mapper -> sanitized evidence pair.

FEAT-003 remains the owner of the V2 schemas, profile catalog, model runtime,
prompts, and qwen_vision.py implementation. FEAT-018 consumes those inputs
without editing them. The mapper is an already-approved offline boundary; it
does not execute a model, provider, network, or storage operation.

### 2.1 Runtime configuration

The approved future harness must construct
QwenVisionRuntimeConfig explicitly from one owner-approved, session-local
configuration file. The construction boundary is exactly
`QwenVisionRuntimeConfig.from_env_file(approved_session_relative_env_file,
environ={})`; ambient process environment values must not be merged. The exact
file identity, the selected model_dir/model_cache_dir choice, device,
device_index, and allow_model_download fields are recorded under
P2T2-LIVE-D11 and P2T2-LIVE-D4/D10 before approval. In pseudocode:

    QwenVisionRuntimeConfig.from_env_file(
        approved_session_relative_env_file,
        environ={},
    )

The selected file must provide the exact
SKETCH2LIFE_VISION_MODEL_DIR or SKETCH2LIFE_VISION_MODEL_CACHE_DIR,
SKETCH2LIFE_VISION_DEVICE, SKETCH2LIFE_VISION_DEVICE_INDEX, and
SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD values approved in
P2T2-LIVE-D4 and P2T2-LIVE-D10. The file is ignored runtime configuration,
never committed, and never copied into evidence. Its paths are interpreted
inside the Lightning session; a host-local Windows path is never presumed to
exist remotely.

The current no-model-load readiness checker can report READY only when its
own requirements are met, including a configured local model directory,
download disabled, a verifiable pinned snapshot revision, exact dependencies,
CUDA, BF16, and its expected NVIDIA L4 device class. If the selected
configuration cannot satisfy that checker, the future run must stop unless a
separate approval names an equivalent already-approved readiness boundary.
This plan does not authorize modifying the checker.

### 2.2 Content-policy construction

The policy must be explicitly constructed and injected at the existing port.
The exact implementation identity is
`sketch2life.infrastructure.ai.vision_lexical_policy.LexicalRegressionContentPolicy`
and the exact synthetic lexicon factory is
`sketch2life.infrastructure.ai.vision_lexical_policy.synthetic_prohibited_lexicon`:

    content_policy: ObservableContentPolicyV1 =
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())

The resulting exact values are
`content_policy_version=vision-prohibited-lexicon-fixture-v1` and
`policy_match_view_version=vision-policy-match-view-v2`. The approved harness
passes this object as `content_policy` while constructing QwenVisionAdapter;
there is no default, alternate, unreviewed, semantic, or production policy
configuration. The exact import/factory identity, values, and synthetic
fixture/regression purpose are recorded in P2T2-LIVE-D12 and the evidence
pair. The scope limitation and owner decision are P2T2-LIVE-D12.

### 2.3 Prompt construction

The future approval must name the exact owner-approved prompt protocol/source,
its prompt identity, and its SHA-256. The approved harness must inject that
prompt through prompt_builder or the equivalent explicit prompt argument.
The adapter's empty default prompt builder is not acceptable. Prompt text is
kept in memory only and is never logged or written to either evidence file.
The harness must hash the exact UTF-8 text selected for injection immediately
before the adapter invocation:

    sha256(prompt_text.encode("utf-8")).hexdigest() == approved_prompt_sha256

The comparison is an in-memory self-check; the prompt text is not persisted or
logged. A mismatch is a pre-adapter terminal with
`adapter_call_count=0` and `attempt_count=null`.
Changing or adding a FEAT-003 prompt is outside this plan and requires a
separate approval. The decision is P2T2-LIVE-D7.

### 2.4 Runner construction and timeout boundary

Neither existing runner currently satisfies the live boundary. The current
`KillableSubprocessQwenGenerationRunner` has a 120-second child deadline, but
its worker sends `(kind, raw_output)` through an unbounded `Connection.send`.
The current `TransformersQwenGenerationRunner` is in-process and has no hard,
killable deadline. Neither class is selectable for a live approval as-is, and
the current `qwen_vision.py` source remains read-only.

The next authorization may therefore select only
`NEW_GLUE_EXPLICITLY_APPROVED`. That is a staged approval of the new boundary
described in Section 2.5, not permission to execute Lightning, load a model,
or make a live adapter call. The eventual bounded runner is passed to
`QwenVisionAdapter` as `generation_runner`; a test `model_factory` is not a
live runner, and persistent `on_raw_output` or `on_mapping_diagnostic` sinks
are forbidden.

For the proposed boundary, model/processor loading and generation occur inside
the killable child for each generation attempt. The child deadline is exactly
120 seconds per attempt and covers loading, generation, and decoding. A
separate positive `total_adapter_cap_seconds` covers the entire single adapter
call, including a possible second attempt, without resetting on retry. A
readiness inspection may inspect versions, hardware, and a local snapshot
without loading weights; it must not preload weights. Any separate model-load
or download phase requires the staged file-scope approval below.

### 2.5 Proposed new glue boundary (not created by this draft)

Repository conventions use feature-local, directly imported executors under
`backend/src/sketch2life/benchmark/` with focused unit tests under
`backend/tests/unit/`. The smallest proposed source/test scope is exactly:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`:
  the feature-local smoke coordinator and the proposed
  `Feat018BoundedKillableQwenGenerationRunner`. It owns the explicit runtime
  config, synthetic lexical policy, prompt injection/hash check, admission
  and session-relative staging, single-device/post-load placement assertion,
  one-call cardinality, per-attempt/total caps, bounded child IPC, raw-byte
  ceiling before IPC send, bounded non-persistent stdout/stderr, typed result
  and mapper handoff, `finally` cleanup, sanitized evidence pair, and ignored
  incident fallback. It uses the existing FEAT-003 adapter boundary without
  modifying `qwen_vision.py` or any FEAT-003 file.
- `backend/tests/unit/test_feat018_live_lightning_execution.py`: offline tests
  with injected fakes only. It covers raw and IPC overflow, stdout/stderr
  ceilings, per-attempt timeout and total-cap termination, child/IPC cleanup
  on success and failure, pre-adapter `0/null`, adapter input rejection
  `1/0`, model-reaching `1/1`, explicitly transient retry `1/2`, no third or
  outer retry, prompt-hash equality, post-load device placement, evidence
  redaction, and the ignored incident path.

No other new source, wrapper, CLI, fixture, adapter edit, or test file is in
the proposed boundary. These paths are a scope proposal only; no file is
created or authorized until the staged governance sequence in Section 9 is
completed.

### 2.6 Mapper and synthetic session identity

RawResultEnvelopeV1 requires a non-empty session_id. The isolated smoke run
does not invoke shared session or idempotency orchestration, so the approved
harness must create a synthetic, opaque smoke-session identifier and pass it
to map_vision_result_to_raw. The identifier is not sourced from V2, mobile,
or a production session. It must be non-empty, at most 160 characters, contain
no path, URL, credential, or token, and be recorded as safe metadata only.
The exact source, format, and value-handling rule are resolved in
P2T2-LIVE-D11.

The mapper call must be equivalent to:

    map_vision_result_to_raw(
        result,
        session_id=approved_synthetic_session_id,
        expected_source_sha256=staged_source_sha256,
        expected_correlation_id=request.correlation_id,
        asr_result=None,
    )

No session bridge or mapper modification is implied by this plan.

## 3. Preconditions

All of the following must be true before the Lightning GPU session starts.
The future execution approval must record each value; a statement that a
condition is "reasonable", "available", or "unchanged" is not sufficient.

1. Approval gate. A future addendum to
   features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md says
   APPROVED for this exact live smoke scope, names all resolved
   P2T2-LIVE-D1 through P2T2-LIVE-D12 decisions, pins the exact runtime
   source commit, and enumerates the exact two evidence paths. The existing
   offline P2-T2 approval is not live-execution approval.

2. Exact runtime source commit. The approval records one exact 40-hex
   runtime_source_commit. The Lightning checkout verifies, before any model
   invocation, that git rev-parse HEAD equals that value and that the source
   checkout is the intended checkout. A floating branch, tag, latest
   revision, or host-only assertion is invalid. The verified commit is
   recorded in both evidence files or in the single shared evidence metadata
   object.

3. Clean source checkout. Before session startup, git status --porcelain is
   completely empty with no path filter, and git status --ignored --short
   matches the recorded approved ignored baseline. Any modified tracked file,
   untracked file, staged change, generated file, or unexpected/changed ignored
   runtime artifact stops the run. The Lightning checkout repeats the
   source-commit and clean-checkout verification before the adapter call. The
   current planning worktree is not an execution candidate because this draft
   and the preserved P2-T3 draft are untracked.

4. Exact fixture identity. P2T2-LIVE-D6 names exactly one owner-reviewed,
   non-sensitive JPG or PNG fixture_id, source identity, format, dimensions,
   and source_sha256. The owner review reference and whether the image is
   reused or newly reviewed are recorded. No child, personal, production, or
   unreviewed image is permitted.

5. Admission and staging integrity. The exact fixture passes the existing
   P2-T1 D2 image-admission policy before a vision call. It satisfies the bounded limits of
   max_file_bytes=5000000, max_pixels=4000000, max_longest_edge=4096,
   max_frames=1, decodability, and MIME/extension agreement. The approved
   P2T2-LIVE-D8 method mounts, copies, or uploads only a derived
   session-local working reference. The original remains immutable. The
   staged bytes are hashed inside Lightning before inference and must equal
   source_sha256. The request's VisionImageReferenceV1 and the adapter's own
   _verify_image_reference check use that same digest.

6. Exact model/profile. The request uses only
   QWEN3_VL_8B_INSTRUCT_BF16_V1. The exact model identifier and revision are
   Qwen/Qwen3-VL-8B-Instruct and
   0c351dd01ed87e9c1b53cbc748cba10e6187ff3b. The pre-run record includes
   vision_profile_config_hash_v2(profile) and the catalog hash. No other
   model, revision, profile, or decoding value may be substituted.

7. Exact dependencies. The installed versions inside Lightning equal the
   profile's four exact pins: accelerate 1.10.1, qwen-vl-utils 0.0.14,
   torch 2.8.0, and transformers 4.57.6. A mismatch, missing package, or
   unrecorded extra runtime is a stop condition. If a pre-staged local
   snapshot is used, its required files and revision metadata must be
   verifiable. The profile's repository-level weight SHA-256 remains absent
   with reason SOURCE_DOES_NOT_PUBLISH_A_DIGEST; the run must not invent one.

8. Prompt and policy. P2T2-LIVE-D7 records the prompt protocol/source,
   prompt_sha256, and explicit builder injection. Immediately before the
   adapter call, the harness hashes the exact injected text as
   `sha256(prompt_text.encode("utf-8")).hexdigest()` and requires equality
   with the approved hash without logging or persisting the text. P2T2-LIVE-D12
   records the exact import/factory identity (`LexicalRegressionContentPolicy`
   plus `synthetic_prohibited_lexicon()`),
   `content_policy_version=vision-prohibited-lexicon-fixture-v1`, and
   `policy_match_view_version=vision-policy-match-view-v2`. An empty prompt,
   hash mismatch, missing policy, or alternate policy is a pre-adapter stop.

9. Hardware. P2T2-LIVE-D10 records the exact Lightning accelerator/SKU,
   device_count, device_index, minimum_vram_mib, cuda requirement, driver
   facts, and BF16 requirement. The observed GPU SKU, VRAM, CUDA availability,
   device count, and BF16 support are checked inside Lightning. A different,
   unavailable, or unverifiable device is a stop condition. The current
   readiness contract expects the NVIDIA_L4 device class; no prior L4
   choice is silently inherited. The boundary must also require single-device
   visibility or a post-load assertion that the model and inference inputs
   occupy the approved device index; inventory alone is insufficient.

10. Timeout and attempt policy. The profile timeout is exactly 120.0 seconds
     per generation attempt in the proposed killable runner. Its child
     deadline starts after process start and includes model loading, generation,
     and decoding in that attempt. A separate positive
     `total_adapter_cap_seconds`, recorded under P2T2-LIVE-D2, covers the
     entire one adapter call and any permitted retry without resetting. A
     timeout or total-cap terminal is never retried. Before adapter invocation
     record `adapter_call_count=0`, `attempt_count=null`; an adapter input
     rejection before model generation records `1/0`; a model-reaching call
     records `1/1` or `1/2`. Only QwenTransientRuntimeError or a generic
     exception explicitly classified transient on the first generation attempt
     may advance the latter to attempt 2. QwenModelLoadError and
     QwenDeviceUnavailableError are terminal on the first attempt and never
     trigger the internal retry. Model-load failure, device-unavailable
     failure, timeout, total-cap expiry, malformed output, policy rejection,
     mapper failure, cleanup failure, permanent runtime failure, and every
     second-attempt failure are terminal. There is no outer retry.

11. Bounded output and IPC. P2T2-LIVE-D9 records exact numeric raw-output,
    IPC-envelope, stdout, and stderr ceilings and their enforcement
    component. The ceiling is enforced before an unbounded raw value can cross
    the child-parent boundary. stdout and stderr are either disabled or
    captured by a bounded, non-persistent sink; they may not contain prompts,
    raw model output, credentials, URLs, paths, or provider payloads. If the
    selected runner or harness cannot prove these bounds, the run stops before
   model invocation. The exact profile setting max_new_tokens=512 must remain
   recorded and unchanged, but it does not by itself prove a byte bound.

12. Runtime manifest. A sanitized runtime manifest is created inside
    Lightning after source, dependency, CUDA, driver, and GPU checks and
    before inference. The exact allowlist and canonical hash are in
    Section 3A. Any secret, absolute path, prompt, raw output, URL, credential,
    hostname, or non-allowlisted key causes a stop before evidence writing.

13. Budget and TTL. P2T2-LIVE-D2 records positive
     `session_ttl_seconds` and `total_adapter_cap_seconds`, plus at least one
     exact numeric cap: gpu_minute_cap or currency_cap. The total adapter cap
     covers both possible generation attempts; the session TTL and GPU/currency
     cap cover the broader session. If multiple caps are supplied, the first
     reached cap wins. The action at any cap is terminate the session and mark
     the run failed, including when the adapter is in flight. The caps are
     never folded into adapter timing.

14. Evidence destination and file scope. The exact date-qualified JSON and
    Markdown paths in Section 7 are absent before the run and are named in
    the future approval's exact file list. Only that pair may be created by
    the run. A tmp report, shared evidence dump, runtime config, cache,
    generated model output, prompt file, or third evidence artifact is not an
    approved destination.

### 3A. Sanitized runtime manifest

The runtime manifest is a small JSON object with only the following allowlisted
facts. It is collected inside the Lightning session; it is not a full
environment dump or pip-freeze output:

    {
      "manifest_version": "P2T2-LIVE-RUNTIME-MANIFEST-V1",
      "python": {
        "implementation": "<allowlisted interpreter name>",
        "version": "<allowlisted interpreter version>"
      },
      "dependencies": [
        {"package": "accelerate", "version": "<installed exact version>"},
        {"package": "qwen-vl-utils", "version": "<installed exact version>"},
        {"package": "torch", "version": "<installed exact version>"},
        {"package": "transformers", "version": "<installed exact version>"}
      ],
      "cuda": {
        "available": "<boolean>",
        "device_count": "<integer>",
        "runtime_version": "<allowlisted CUDA runtime fact>"
      },
      "driver": {
        "version": "<allowlisted NVIDIA driver fact>"
      },
      "gpu": {
        "device_index": "<integer>",
        "sku": "<allowlisted GPU SKU>",
        "vram_mib": "<integer>",
        "bf16_supported": "<boolean>"
      }
    }

The implementation must reject keys outside this allowlist, sort dependency
records by package, and canonicalize with UTF-8 JSON, sorted keys, compact
separators, and no hash field. runtime_manifest_sha256 is SHA-256 of that
canonical byte sequence. The evidence pair may contain the allowlisted
manifest object and its hash. It must not contain model/cache/runtime-config
paths, environment values, URLs, credentials, tokens, prompts, raw provider
output, hostnames, process command lines, or arbitrary package inventory.

The runtime_source_commit, model identifier/revision, profile/config hashes,
fixture hash, and prompt hash are recorded as separate sanitized metadata; they
are not a reason to widen the runtime-manifest allowlist.

## 4. Execution phases

### Phase 0 - approval and local preflight

This phase occurs before any Lightning session and does not run a model,
provider, network call, benchmark, or live subprocess.

- Verify the future approval is APPROVED for this exact scope, resolves
  P2T2-LIVE-D1 through P2T2-LIVE-D12, and lists the exact evidence pair.
- Verify the exact runtime_source_commit and an empty unfiltered
  git status --porcelain in the execution checkout.
- Verify the fixture_id, owner-review reference, source_sha256, and P2-T1 D2
  image-admission result=PASS. A RECAPTURE or source-digest mismatch stops before
  Lightning starts.
- Verify the profile, catalog/config hashes, dependency pins, prompt identity,
  policy identity, hardware decision, per-attempt timeout,
  `total_adapter_cap_seconds`, TTL, budget, and output ceilings are completely
  recorded.
- Verify the date-qualified evidence paths do not already exist. Never
  overwrite an existing evidence artifact.
- Initialize `adapter_call_count=0` and `attempt_count=null` before any
  pre-adapter check. If a check stops the run, preserve those values and enter
  the terminal evidence path; no adapter, mapper, or model-reaching attempt is
  claimed. If evidence creation is impossible, write only the safe ignored
  incident record described in Section 1 and do not index it.

### Phase 1 - Lightning provisioning and session startup

Start exactly one Lightning Studio GPU session under the approved TTL, total
adapter cap, and budget. Measure provisioning and session startup separately:

- provisioning interval: request/allocate start through session allocation;
- session-startup interval: allocation through approved session readiness;
- session total: session start through confirmed termination.

None of these intervals is part of adapter_wall_clock_ms.

Inside the session, before any model invocation:

- verify git rev-parse HEAD equals runtime_source_commit and the checkout is
  clean; a branch name alone is not evidence;
- load the explicitly selected runtime config without copying its values to
  evidence;
- verify installed dependency versions, CUDA, driver, GPU SKU, device count,
  VRAM, and BF16 facts;
- require single approved-device visibility or, after model load, assert that
  the model and inference inputs occupy the approved device index;
- run only the no-model-load readiness inspection applicable to the approved
  configuration; require READY or stop;
- stage the approved image using the exact P2T2-LIVE-D8 method, keep its
  reference session-local and relative, and recompute the staged SHA-256;
- create and hash the sanitized runtime manifest;
- do not preload model weights. If P2T2-LIVE-D4 approves a model download,
  the download/load occurs inside the selected runner's child model-loading
  phase and is covered by the same 120-second subprocess boundary. A separate
  pre-invocation download requires separate approval.

If provisioning, session startup, readiness, staging, or manifest creation
fails, the resource cleanup finally block in Phase 4 still runs and Phase 5
records the terminal outcome.

### Phase 2 - one bounded adapter call

Construct one VisionUnderstandingRequestV2 with:

- the owner-approved fresh correlation_id;
- the session-local relative source_image_ref and staged source_sha256;
- no processing image unless a separately approved derivation is named;
- media_validation.decision=PASS with its approved provenance;
- requested_profile_id=QWEN3_VL_8B_INSTRUCT_BF16_V1.

Immediately before the single call, set `adapter_call_count=0`,
`attempt_count=null`, and compute the SHA-256 of the exact in-memory UTF-8
prompt text selected for injection. Require that hash to equal the approved
`prompt_sha256` before setting adapter_start. Then increment
`adapter_call_count` to 1 and invoke `QwenVisionAdapter.understand(request)`
exactly once; there is no outer retry counter. Immediately after it returns or
raises, set adapter_end. A prompt-hash mismatch stops before the invocation
with `adapter_call_count=0` and `attempt_count=null` and has no fabricated
adapter duration.
adapter_wall_clock_ms is adapter_end minus adapter_start and includes all work
inside understand(), including adapter-side validation, prompt construction,
model loading, generation, decoding, and any internal transient retry.

For the proposed killable runner, each generation attempt has its own
120-second child deadline after process start. It includes the child
model/processor load, generation, and decoding; it is not a model-load
deadline followed by a separate generation deadline. The separate
`total_adapter_cap_seconds` begins at adapter_start, covers all generation
attempts inside this one adapter call, and is not reset for attempt 2. Either
timeout is terminal and cannot authorize another attempt. The raw provider
string remains in memory only and never reaches stdout, stderr, a hook sink, or
evidence.

If the adapter returns its typed input-validation rejection before model
generation, record `adapter_call_count=1` and `attempt_count=0`, and never
retry or relabel it as a model-reaching smoke run. If the runner is entered,
record `adapter_call_count=1` and `attempt_count=1` or `2`, cross-checking the
value against the adapter's `attempt_number`; attempt 2 requires an explicit
transient runtime classification from attempt 1. No other call/attempt
combination is accepted, and no missing value is invented.

### Phase 3 - typed result and mapper

Independently assert that the in-memory adapter return is exactly one
schema-valid VisionUnderstandingSuccessV2 or VisionUnderstandingFailureV2.
Check profile_id, profile_catalog_hash, config_hash, adapter_version, model
identifier, model revision, dependency pins, source digest, correlation ID,
attempt state, and policy state against the pre-run records.

When a typed V2 result exists, call map_vision_result_to_raw exactly once with
the approved synthetic session_id, staged digest, request correlation, and
asr_result=None. This includes the adapter's typed input-validation result,
which maps to a typed Raw validation failure. A pre-adapter terminal has no V2
result and therefore makes no mapper call; its evidence records
`adapter_call_count=0` and `attempt_count=null`. No ASR or Whisper process is
started. Verify that the mapped result:

- is RawUnderstandingSuccessV1 or RawUnderstandingFailureV1;
- preserves source hash and correlation;
- carries the approved synthetic session ID;
- retains complete provenance on success;
- has gate_a_required=true;
- has narration_status=NOT_SUPPLIED when successful;
- contains no eligibility, personality, readiness, activity, objective,
  Gate B, or semantic-safety decision.

A source/hash mismatch, stale correlation, missing confidence, unsupported
variant, or any other mapper exception is terminal and is never repaired or
retried live.

### Phase 4 - in-memory disposal and resource cleanup

Cleanup is structurally required in a finally block around the entire
authorized run body, including local preflight, session provisioning, success,
timeout, malformed output, policy rejection, mapper failure, and subprocess
failure. For a pre-adapter stop before a session exists, the cleanup operations
are safe no-ops but the same terminal-recording path still runs. The approved
harness must not use early returns that bypass it. The required shape is:

    try:
        run_preflight_session_adapter_call_and_map()
    finally:
        cleanup_runner_ipc_and_child()
        discard_raw_output_and_decoded_tensors()
        terminate_lightning_session()
        confirm_no_residual_gpu_or_runner_process()

The actual implementation may use the proposed boundary, but the approval
must identify it. Cleanup closes IPC, terminates and joins any child, discards
raw model output and tensors, and terminates the single Lightning session.
Cleanup is required for success, timeout, malformed output, policy rejection,
mapper failure, model-load failure, device failure, and every subprocess
failure. If cleanup itself fails, the run status is FAILED with
`run_failure_code=CLEANUP_FAILED`, regardless of the V2 or Raw result, and no
retry or second session is permitted.

### Phase 5 - sanitized evidence and postflight

After cleanup, build the sanitized evidence pair in memory, validate its
allowlist, and write only the exact JSON and Markdown paths in Section 7. This
writer is required for every authorized run attempt, including a pre-adapter
terminal. If the pair cannot be created or atomically completed, write only
the safe ignored incident record at
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; do not index an
incomplete pair or the incident.
The evidence writer must not serialize the V2 or Raw object wholesale because
their provenance may contain fields, URLs, or details that are not allowed in
sanitized evidence. It selects only the allowlisted metadata described below.

Run the postflight inventory after the pair is written. If an unexpected
tracked, untracked, ignored, temporary, cache, runtime-config, or generated
artifact is found, the run fails and the artifact is not published or
indexed. Do not delete or overwrite an unexpected user artifact under this
plan; stop and report its logical category and safe identity.
If pair creation was impossible, run the same safe postflight against the
ignored incident path and leave both the pair and the incident unindexed.

## 5. Assertions and terminal outcome rules

All assertions below are required for a functional PASS:

- a model-reaching run has exactly one adapter call:
  `adapter_call_count=1`;
- a pre-adapter terminal is recorded as `adapter_call_count=0` and
  `attempt_count=null`; an adapter input rejection before model generation is
  recorded as `adapter_call_count=1` and `attempt_count=0`;
- a model-reaching run records `attempt_count=1` or `2`, and attempt 2 occurs
  only after an explicitly classified transient runtime failure on attempt 1;
- no call or attempt value is inferred, backfilled, or fabricated;
- the source fixture was admitted before any vision call;
- the original and staged source SHA-256 values match, and the adapter's
  independent image-reference verification passed;
- the exact runtime_source_commit was verified inside Lightning before the
  adapter call;
- the sanitized runtime manifest is allowlist-valid and its hash matches;
- the exact profile, model identifier/revision, config/catalog hashes,
  dependencies, prompt identity/hash, policy identity, and hardware facts
  match the approval;
- the configured raw-output, IPC, stdout, and stderr ceilings were enforced;
- each generation attempt was bounded at 120 seconds and the separate
  `total_adapter_cap_seconds` covered the complete adapter call, including any
  permitted retry, without resetting;
- the V2 result is schema-valid, or the typed terminal failure is recorded;
- the mapper result is schema-valid when mapping was reached;
- correlation, source, synthetic session identity, and provenance checks pass;
- gate_a_required=true and no P1/Gate A/Gate B decision was fabricated;
- ASR/Whisper was not run and narration is not represented as supplied;
- the adapter timing includes model load, generation, decoding, and internal
  retry, while provisioning/session startup/cleanup are separately measured;
- cleanup ran in finally and cleanup_status=SUCCEEDED; any cleanup failure
  makes the overall run FAILED;
- the exact sanitized evidence pair was attempted for every authorized run
  attempt, including pre-adapter terminals; an impossible pair has only the
  safe ignored incident record and is not indexed;
- postflight inventory satisfies the exact two-file evidence scope.

One smoke run is functional evidence only. It is not a benchmark, does not
establish p50/p95 latency, throughput, quality, accuracy, semantic safety, or
production moderation readiness, and cannot close P2-T2 by itself. Full P2
closure needs separately approved live/evaluation work and its own evidence.

### 5.1 Retry and failure matrix

| Condition | V2 or harness outcome | Retry rule | adapter_call_count | attempt_count |
|---|---|---|---|---|
| Approval, checkout, fixture, readiness, configuration, policy, hardware, manifest, runner-boundary, or session/budget stop before adapter invocation | Harness terminal; no V2 or Raw result | Terminal; no adapter call | 0 | `null` |
| Adapter input validation rejects before model generation | V2 INPUT_NOT_VALIDATED; mapper may produce typed Raw validation failure | Terminal; no retry | 1 | 0 |
| Model-load failure after the runner is entered | V2 VISION_MODEL_UNAVAILABLE / MODEL_LOAD_FAILED | Terminal; no second generation call | 1 | 1 |
| Device unavailable or wrong device after the runner is entered | V2 VISION_MODEL_UNAVAILABLE / DEVICE_UNAVAILABLE | Terminal; no retry | 1 | 1 |
| Timeout on either generation attempt | V2 VISION_TIMEOUT / TIMEOUT_BUDGET_EXCEEDED | Terminal; no retry after timeout | 1 | 1 or 2 |
| Total adapter cap reached | Harness or V2 timeout terminal | Terminal; no retry and no cap reset | 1 | 1 or 2 |
| Explicit or classified transient runtime failure on attempt 1 | Internal adapter retry | One retry only; proceed to attempt 2 | 1 | 2 after retry |
| Transient failure again on attempt 2 | V2 VISION_PROVIDER_FAILURE / TRANSIENT_RUNTIME_FAILURE | Terminal; no third attempt | 1 | 2 |
| Permanent runtime failure after the runner is entered | V2 VISION_PROVIDER_FAILURE / PERMANENT_RUNTIME_FAILURE | Terminal; no retry | 1 | 1 or 2 |
| Malformed JSON, schema-invalid output, duplicate ID, or reference failure | V2 VISION_SCHEMA_INVALID with the existing typed detail | Terminal; no repair/retry outside current adapter behavior | 1 | 1 or 2 |
| Content-policy rejection | V2 PROHIBITED_CLAIM_DETECTED with typed category | Terminal; no retry or semantic reinterpretation | 1 | 1 or 2 |
| Mapper failure or source/correlation mismatch at mapper | RawUnderstandingMappingError; no fabricated Raw result | Terminal; no retry | 1 | 0, 1, or 2 as recorded before mapping |
| IPC, raw-output, stdout, or stderr ceiling exceeded | Harness-level bounded-output failure | Terminal; stop session; no retry | 1 | 1 or 2 |
| Cleanup failure | Harness FAILED / CLEANUP_FAILED | Terminal; no second session | 0, 1 | `null`, 0, 1, or 2 as recorded |

The current subprocess worker maps generic worker exceptions to a permanent
runtime failure; it does not infer transient status from arbitrary provider
text. Only an explicit approved transient seam may produce attempt 2.

### 5.2 Existing source/hash failure mapping

| Condition | Existing adapter outcome | Existing mapper outcome |
|---|---|---|
| Adapter verifies a staged digest mismatch | error_code=INPUT_NOT_VALIDATED, error_detail=SOURCE_IMAGE_HASH_MISMATCH, attempt_number=0, retryable=false; record `adapter_call_count=1`, `attempt_count=0` | RawFailureCode.VALIDATION_REJECTED with upstream detail SOURCE_IMAGE_HASH_MISMATCH |
| Adapter cannot read the staged source | error_code=INPUT_NOT_VALIDATED, error_detail=SOURCE_IMAGE_UNREADABLE, attempt_number=0, retryable=false; record `adapter_call_count=1`, `attempt_count=0` | RawFailureCode.VALIDATION_REJECTED with upstream detail SOURCE_IMAGE_UNREADABLE |
| Mapper sees result.source_image_ref.sha256 different from expected_source_sha256 | No new V2 result | Raises RawUnderstandingMappingError before Raw construction |

The direct mapper mismatch is not RawFailureCode.SOURCE_MISMATCH. That enum
member is not the current V2 mapper path. No mapping change is authorized. A
stop before the adapter has no row in the existing-adapter column and records
`adapter_call_count=0`, `attempt_count=null` in the sanitized harness evidence.

## 6. Negative and stop gates

The following stop the run immediately. They are terminal, are recorded
without raw content, and still pass through the cleanup finally block:

- any missing or unresolved approval decision;
- runtime commit mismatch, dirty checkout, untracked file, or unexpected
  source artifact;
- fixture admission RECAPTURE, fixture identity/hash mismatch, or staged
  digest mismatch;
- unverified model revision, profile/config/catalog drift, or dependency
  mismatch;
- missing or wrong prompt-builder identity, policy identity, or output bound;
- CUDA unavailable, wrong SKU/device count/index, insufficient or
  unverifiable VRAM, BF16 unavailable, or failed model/input placement on the
  approved device;
- a selected runner that cannot bound IPC, stdout, stderr, and raw output;
- model-load failure, device-unavailable failure, timeout, malformed output,
  policy rejection, permanent runtime failure, mapper failure, or cleanup
  failure;
- a cardinality combination other than pre-adapter `0/null`, adapter input
  rejection `1/0`, or model-reaching `1/1` or `1/2`; an outer retry, a third
  generation attempt, or a retry for any non-transient failure;
- `total_adapter_cap_seconds`, session TTL, or GPU/currency cap reached;
- any secret, token, credential, URL, absolute path, prompt, raw provider
  output, transcript, or raw media value entering evidence or logs;
- any artifact outside the exact future-approved evidence pair modified or
  created.

If the adapter returns an input failure with `attempt_number=0`, record
`adapter_call_count=1`, `attempt_count=0`, map that typed result once, and
retain it as a terminal non-functional outcome. It is never retried to force
attempt_count into a model-reaching value. If a stop occurs before the adapter,
record `adapter_call_count=0`, `attempt_count=null`; neither value may be
backfilled from a planned call. Every such authorized terminal still requires
the exact sanitized evidence pair, or only the ignored incident fallback when
pair creation is impossible.

## 7. Evidence policy

After a separately approved run, write exactly this feature-local pair, with
the date replaced by the actual run date:

- features/FEAT-018-live-image-canvas-flow/evidence/metrics/P2_LIVE_SMOKE_<YYYYMMDD>.json
- features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_LIVE_SMOKE_<YYYYMMDD>.md

The future approval must name the exact date-qualified paths, and the paths
must be absent before execution. Do not write a third run artifact, use tmp as
evidence, index before the required review, or overwrite an existing pair.

Every authorized run attempt, including a terminal before adapter invocation,
must produce exactly this JSON/Markdown pair. A pre-adapter terminal records
`adapter_call_count=0` and `attempt_count=null` and omits V2/Raw result claims;
an adapter input rejection records `adapter_call_count=1` and
`attempt_count=0`; a model-reaching call records `adapter_call_count=1` and
`attempt_count=1` or `2`. If the pair cannot be created or atomically
completed, the only fallback is the safe local ignored incident record at
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; it is not feature
evidence, is not indexed, and must contain no prompt, raw output, secret,
credential, URL, path, or raw media.

The sanitized JSON and Markdown companion contain the same bounded run
metadata, with the Markdown providing human-readable interpretation:

- exact runtime_source_commit and verified=true;
- run_id, correlation_id, and synthetic session_id only when they are opaque
  safe identifiers with no path, URL, token, or credential;
- exact fixture_id, source_sha256, staged reference class, MIME, width, height,
  and the approved staging method; never image bytes;
- model identifier, model revision, profile ID, adapter version,
  profile_config_hash, and profile_catalog_hash; never a weight-source URL;
- prompt_protocol_id, prompt_source_identity, and prompt_sha256; never prompt
  text;
- content_policy_version, policy_match_view_version, policy_scope, and
  P2T2-LIVE-D12 result; no lexicon text or semantic-safety claim;
- the allowlisted runtime_manifest object and runtime_manifest_sha256;
- GPU SKU, device index/count, vram_mib, BF16 result, CUDA runtime fact, and
  driver version only through the allowlisted manifest, plus the approved
  single-device visibility or post-load model/input placement assertion;
- max_new_tokens=512, raw_output_max_bytes, ipc_envelope_max_bytes,
  stdout_max_bytes, stderr_max_bytes, and an enforcement=CONFIRMED result;
- adapter_call_count and attempt_count using the conditional cardinality
  rules above, together with the adapter's typed attempt/result status when a
  V2 result exists; no raw model output;
- outcome status SUCCEEDED or FAILED; typed V2/Raw failure code when a valid
  typed result exists; harness-level run_failure_code when mapping, bounds,
  or cleanup fails;
- timing fields: provisioning_wall_clock_ms,
  session_startup_wall_clock_ms, session_total_wall_clock_ms,
  adapter_wall_clock_ms, mapper_wall_clock_ms, and explicit boundary labels;
  adapter timing is not combined with provisioning or session startup; a
  pre-adapter terminal uses no fabricated adapter duration;
- per_attempt_timeout_seconds=120.0, total_adapter_cap_seconds,
  session_ttl_seconds, gpu_minute_cap and/or currency_cap, cap outcome, and
  safe budget-consumed value;
- ASR/Whisper execution=false and narration_status=NOT_SUPPLIED when a Raw
  success exists;
- cleanup_status, postflight_status, and a safe artifact-inventory summary.

Safe hashes may be recorded for the fixture, staged fixture, prompt identity,
runtime manifest, exact source commit, profile/config/catalog metadata, and
the two evidence files. Never hash-and-publish secrets, credentials, raw
output, prompts as a replacement for the required prompt identity rule, raw
media, or arbitrary cache contents. Do not serialize V2 or Raw objects
wholesale.

Never store in either evidence file, normal logs, or tracked Git history:

- raw image/audio bytes or derivative renderings;
- prompt text or raw provider/model output;
- HTTP/session headers, URLs, tokens, credentials, or Lightning secrets;
- transcripts or ASR content;
- absolute local paths, hostnames, command lines, cache paths, or runtime-env
  values;
- child-process exceptions, Pydantic messages, or provider payloads that may
  contain unbounded or user-derived text.

## 8. Postflight inspection and audit

Postflight is required after cleanup and again after the evidence pair is
written. It must inspect all of the following, not only tracked diffs:

1. Tracked files: unfiltered git status --porcelain, git diff --name-status,
   and the exact runtime-source commit relationship.
2. Untracked files: all newly untracked paths in the source checkout and any
   execution workspace.
3. Ignored files: git status --ignored --short, with before/after comparison
   for approved ignored runtime config, caches, and local fixture locations.
4. Temporary artifacts: child-worker files, IPC/pipe remnants, temporary
   directories, scratch logs, and session teardown artifacts.
5. Cache artifacts: model cache, framework cache, compiler cache, and
   generated weight/index files; verify that no new raw output or credentials
   are present.
6. Runtime-config artifacts: the selected env file and any derived config;
   inspect existence and safe logical identity only, never publish its
   contents or secret hash.
7. Generated artifacts: model output, decoded tensors, prompt dumps,
   provider responses, reports, notebooks, and other generated files; none
   may remain as an unapproved run artifact.
8. Evidence artifacts: only the exact JSON/Markdown pair is expected after
   the approved writer runs. Hash both files and record those hashes in the
   local review record or approved evidence metadata as allowed. If pair
   creation is impossible, the only permitted exception is the safe ignored
   incident path from Section 7, which is recorded as an unindexed failure
   artifact rather than evidence.

The postflight result must record safe identities/hashes where applicable:
runtime_source_commit, fixture/source and staged digests, prompt_sha256,
runtime_manifest_sha256, profile/config/catalog hashes, and evidence-file
hashes. It must record category and disposition for every inspected ignored
or temporary artifact without exposing its path or contents in the published
evidence. A new or changed artifact outside the exact approved pair fails the
run and prevents indexing, except for the explicitly permitted ignored
incident path created only when pair creation is impossible.

## 9. Explicit owner decisions required before live approval

Each decision below is owner-decidable and auditable. The owner must select
one stated resolution and record every required field in the future approval.
Blank values, an implicit default, or a prose-only statement does not resolve
the decision.

These labels are live P2-T2 plan identifiers only; they do not alter, rename,
or close any P2-T1 decision.

### Required staged governance sequence

The next authorization is for the proposed bounded boundary, not for live
execution. The stages are mandatory and sequential:

1. Approve the exact two-file glue/test scope in Section 2.5, including each
   file's responsibility and the prohibition on changing the excluded FEAT-003
   adapter.
2. Implement and test that boundary offline with injected fakes only; no
   model, GPU, Lightning, provider, network, subprocess, or benchmark
   execution is permitted in this stage.
3. Obtain an independent code review of the bounded IPC, output sinks,
   killable timeout, total cap, cleanup, cardinality, and evidence behavior.
4. Obtain a separate live-execution approval that resolves P2T2-LIVE-D1
   through P2T2-LIVE-D12 against the reviewed implementation and names the
   exact runtime commit, fixture, budget, redaction rules, and evidence pair.
5. Only after stages 1-4 pass may the operator open Lightning or run the
   approved smoke session.

### P2T2-LIVE-D1 - Runner and deadline enforcement

The next authorization must select `NEW_GLUE_EXPLICITLY_APPROVED`, referring
to the exact source/test paths and responsibilities in Section 2.5. This
first-stage decision authorizes creation and offline testing of that boundary
only; it is not a live-execution approval. The current
`KillableSubprocessQwenGenerationRunner` is not selectable because its IPC is
unbounded, and the current `TransformersQwenGenerationRunner` is not selectable
because it has no hard killable deadline.

The later live-execution approval must record the implemented runner class and
source commit, the deadline enforcer, and proof that model/processor loading,
generation, and decoding are inside a killable 120-second deadline for each
generation attempt. It must also record the separate
`total_adapter_cap_seconds` covering the one adapter call and possible retry,
and verify the conditional call/attempt cardinality. No live runner is
approved by this draft.

### P2T2-LIVE-D2 - TTL and budget cap

Record positive `session_ttl_seconds` and
`total_adapter_cap_seconds`, plus at least one exact numeric `gpu_minute_cap`
or `currency_cap`. The total adapter cap begins at adapter_start and covers
the complete one-call adapter boundary, including any permitted second
generation attempt; it does not reset on retry. The session TTL and
GPU/currency cap cover the broader session. If multiple caps are supplied,
record the cap clock, the currency if applicable, and the exact action
`TERMINATE_SESSION_AND_MARK_FAILED` at the first cap. A total-cap, timeout,
TTL, or GPU/currency terminal cannot trigger another attempt. The owner may
not approve an unbounded session or a cap described only as "small" or
"within budget".

### P2T2-LIVE-D3 - ASR/Whisper exclusion

Select ASR_EXCLUDED for this image-only smoke run and record
asr_execution=false, asr_result=null, and narration_status=NOT_SUPPLIED. If
the owner does not select ASR_EXCLUDED, this plan is blocked and a separate
P2-T3 live ASR/Whisper approval must enumerate its own model, fixture,
budget, redaction, retries, cleanup, and evidence. This plan never combines
the modalities.

### P2T2-LIVE-D4 - Model-weight staging

Select exactly one:

- PRESTAGED_LOCAL_SNAPSHOT: record the session-local model directory
  identity, allow_model_download=false, snapshot completeness, and verified
  revision metadata; or
- APPROVED_ONE_TIME_DOWNLOAD: record the approved source identity, the
  allow_model_download=true setting, the absence of a repository-published
  weight SHA-256, and the acceptance that download/load occurs inside the
  runner's model-loading interval and 120-second deadline.

A download is never a separate unapproved pre-invocation phase. The runtime
manifest and evidence contain no URL, credential, absolute path, or raw
weight data. If the chosen option cannot be verified with the current
readiness boundary, the run stops.

### P2T2-LIVE-D5 - Evidence indexing timing

Select exactly one:

- INDEX_AFTER_INDEPENDENT_REVIEW: record the reviewer, review timestamp,
  review artifact, and the rule that no index update occurs before the
  review; or
- HOLD_FOR_P2_BATCH: record the holding owner/location and the later review
  gate.

This decision authorizes no edit to evidence/README.md in this draft.

### P2T2-LIVE-D6 - Exact fixture identity

Record exactly one owner-approved fixture_id, source/derivation identity,
owner visual-review reference and date, MIME/extension, width, height,
source_sha256, and whether it is a reused Cohort B image or a newly reviewed
image. The original is immutable and never committed. A new image cannot be
used merely because it passes the P2-T1 D2 image-admission policy.

### P2T2-LIVE-D7 - Prompt identity and explicit builder

Record the exact prompt_protocol_id, prompt source identity/version,
prompt_sha256, and the explicit PromptBuilder or prompt injection used by
the approved harness. Immediately before invoking the adapter, hash the exact
in-memory UTF-8 injected text with
`sha256(prompt_text.encode("utf-8")).hexdigest()` and require equality with
the approved `prompt_sha256`; record only the approved hash and safe identity.
Confirm the empty adapter default is unreachable and do not log or persist the
prompt text.
The prompt text is never recorded. Any new or changed FEAT-003 prompt
requires another approval and is not authorized by this plan.

### P2T2-LIVE-D8 - Fixture staging and mount method

Select exactly one owner-approved mechanism:

- MOUNT_SESSION_RELATIVE;
- COPY_SESSION_RELATIVE; or
- UPLOAD_THEN_SESSION_RELATIVE.

Record the method, a logical session-relative artifact_ref, source-to-derived
provenance, pre/post staging digest checks, and immutable-original rule. A
host-local Windows path, signed URL, credential, or unbounded base64/log
transport is not a valid staging reference.

### P2T2-LIVE-D9 - Raw output, IPC, stdout, and stderr ceilings

Record exact positive integer values for raw_output_max_bytes and
ipc_envelope_max_bytes, exact non-negative integer values for
stdout_max_bytes and stderr_max_bytes, the enforcement component and phase,
UTF-8/protocol behavior, and the exact overflow action
TERMINATE_AND_MARK_FAILED. The fixed model bound max_new_tokens=512 remains
in force but does not replace these ceilings. The proposed
`NEW_GLUE_EXPLICITLY_APPROVED` boundary must enforce the raw-output ceiling
before any raw value crosses IPC, send only an envelope already proven to fit
the IPC ceiling, and make stdout/stderr bounded and non-persistent. The
current subprocess `Connection.send` is not proof of that boundary, and the
current in-process runner is not a substitute. These are first-stage
implementation/test acceptance conditions for the exact scope in Section 2.5;
if the implemented boundary cannot prove them, the owner must leave the live
run unapproved.

### P2T2-LIVE-D10 - Exact GPU/SKU/VRAM/BF16 decision

Record accelerator provider/tier, exact GPU SKU, device_count, device_index,
minimum_vram_mib, observed vram_mib, required cuda=true, required
bf16_supported=true, and the readiness mismatch action
TERMINATE_SESSION_AND_MARK_FAILED. The current readiness contract's expected
device class is NVIDIA_L4; selecting another SKU requires an already-approved
readiness boundary and cannot be made true by editing code during the run.
Require either single approved-device visibility or a post-load assertion that
the model and inference inputs are placed on the approved device index;
inventory facts alone do not satisfy D10.

### P2T2-LIVE-D11 - Approved harness, glue boundary, and session ID

The next authorization must select `NEW_GLUE_EXPLICITLY_APPROVED`; no existing
runner or existing harness satisfies the combined deadline and bounded-IPC
requirements. The separate first-stage approval must list exactly these paths
from Section 2.5 and no others:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` for
  the bounded killable runner, coordinator, explicit runtime/policy/prompt
  construction, staging, device-placement assertion, cardinality, caps,
  cleanup, sanitized writer, and ignored incident fallback;
- `backend/tests/unit/test_feat018_live_lightning_execution.py` for all
  offline overflow, timeout, cleanup, cardinality, placement, prompt-hash,
  redaction, and incident-path tests.

That approval occurs before creation and authorizes offline implementation and
tests only. A later live-execution approval must identify the reviewed source
commit and exact evidence-writer paths before any model invocation. Record the
safe synthetic `session_id` handling rule and confirm it is not a production
session, credential, URL, or path.

### P2T2-LIVE-D12 - Functional synthetic content-policy boundary

Select USE_LEXICAL_REGRESSION_FUNCTIONAL_ONLY and record:

- `sketch2life.infrastructure.ai.vision_lexical_policy.LexicalRegressionContentPolicy`;
- `sketch2life.infrastructure.ai.vision_lexical_policy.synthetic_prohibited_lexicon()`;
- `content_policy_version=vision-prohibited-lexicon-fixture-v1`;
- `policy_match_view_version=vision-policy-match-view-v2`;
- synthetic fixture/regression purpose; and
- the policy result in the evidence pair without matched text.

This policy is functional-only/synthetic-regression checking. It is not
semantic safety evidence, model quality evidence, or production content
moderation evidence. No owner may treat a policy PASS as any of those
claims. A semantic or production moderation policy needs a separate plan and
approval; no alternate policy is silently substituted here.

## 10. Final acceptance boundary

The future live smoke is accepted only after the staged governance sequence
passes and the separate live approval covers the exact runtime commit, fixture,
prompt, runner, hardware, budgets, redaction rules, and evidence paths. The
run must then pass exact fixture/staged-digest, profile/dependency, prompt and
policy, hardware/placement, TTL/budget, per-attempt 120-second,
`total_adapter_cap_seconds`, bounded IPC/logging, timing, typed V2-to-Raw
mapping, finally cleanup, sanitized-manifest, postflight, and evidence-pair
checks. Its cardinality must be truthful: pre-adapter `0/null`, adapter input
rejection `1/0`, or model-reaching `1/1` or `1/2` only, with attempt 2 allowed
solely after an explicitly classified transient failure.

Every authorized run attempt must have the exact sanitized JSON/Markdown pair,
including pre-adapter terminals. If evidence creation is impossible, the safe
ignored incident record is the only permitted fallback and the run is not
indexed. No missing call or attempt is backfilled.

A typed failure is useful evidence of a stop gate but is not a functional
PASS. Cleanup failure is always overall FAILED. A smoke result does not
authorize indexing until P2T2-LIVE-D5 is resolved and the required
independent review occurs.

This draft leaves every P2T2-LIVE-D1 through P2T2-LIVE-D12 decision open and
does not authorize live execution, provider benchmark work, or closure of
P2-T2. It also does not authorize any FEAT-017 remote HTTPS adapter,
FEAT-003 modification, mobile, Gate A UI, P1 eligibility, P3/P4, shared
integration, P2-T3 narration, P2-T4/P2-T5 evaluation, commit, or push.

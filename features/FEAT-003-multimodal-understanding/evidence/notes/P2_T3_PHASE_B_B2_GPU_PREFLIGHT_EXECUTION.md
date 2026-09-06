# P2-T3 Phase B B2 typed GPU preflight — execution record

- Evidence ID: `EV-003-T3-06`
- Date: 2026-09-01
- Owner: Person 2
- Scope: one real Qwen model load and one real synthetic inference on Lightning L4, reported
  by the operator running this repository's committed `QwenVisionAdapter` /
  `vision_b2_preflight.run_b2_preflight` (`f3e5830`). This documentation session did not
  execute, observe, or have access to the GPU run itself; the typed fields below are relayed
  from the operator's run and cross-checked in this note against the frozen V2 contract's own
  construction rules (see "Internal-consistency cross-check").
- Approval authority: `approvals/TASK_APPROVAL.md`, bounded P2-T3 Phase B B1–B5 scope. This is
  exactly the B2 work package: "one real model load and one synthetic inference through the
  real adapter on Lightning L4... typed-failure paths proven by injected fakes; record measured
  values or explicit `NOT_MEASURED` reasons."
- Related: `P2_T3_PHASE_B_B2_ENVIRONMENT_SETUP.md` (`EV-003-T3-03`, the readiness checker used
  before this run), `P2_T3_PHASE_B_B2_PREFLIGHT_RUNNER_IMPLEMENTATION.md` (`EV-003-T3-05`, the
  runner's no-GPU implementation/test evidence), and
  `P2_T3_PHASE_B_LIGHTNING_HANDOFF_CONTEXT.md` (`EV-003-T3-04`, updated alongside this note).

## Result summary

The real B2 typed GPU preflight executed once. The runtime/model-load/invocation/
typed-classification/cleanup pathway worked: the post-call VRAM sample on the selected GPU was
`0.0` MB, which supports the cleanup observation without proving on its own that no other
allocation or process existed. The adapter could not map the model output to the strict V2
structured-output contract, producing a typed `VISION_SCHEMA_INVALID` /
`OUTPUT_MAPPING_FAILED` failure — one contract-anticipated data point, which does not by itself
establish a model or adapter defect. B3 is the study that investigates mapping-failure causes;
nothing here is patched or rerun on the strength of this single result. No profile is frozen, no
runtime default is selected, and B3–B5 remain unexecuted; a single run is not a
schema-validity-rate sample.

## Pre-run readiness check

Immediately before this preflight, the operator re-ran the committed no-model-load readiness
checker (`QwenVisionEnvironmentReadinessV1` / `EV-003-T3-03`) against the ignored `.vision.env`
on this Lightning session and reported:

- overall status `READY`;
- model revision state `VERIFIED` (the local snapshot's Hugging Face metadata matched the
  approved immutable revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`);
- the four exact dependency pins matched;
- CUDA available, BF16 supported, normalized device class `NVIDIA_L4`.

The readiness checker itself performs no model load or inference — this pre-check only confirms
the environment was in the state the B2 preflight required before it started.

## Candidate under test

- `VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1`, `compute_profile = GPU_BF16`.
- Model: `Qwen/Qwen3-VL-8B-Instruct`, immutable revision
  `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` (unchanged from B1/ADR-0007).
- Operator-reported environment: one NVIDIA L4 GPU, CUDA and BF16 available.

## What was executed

One call to `run_b2_preflight` against the real `QwenVisionAdapter`:

1. The default `KillableSubprocessQwenGenerationRunner` performed a real model load — the
   operator reported the checkpoint loading across its 4 weight shard files, matching the
   pinned release's shard layout — inside a spawned, killable subprocess.
2. Exactly one synthetic inference call was made through that loaded model, over the runner's
   own synthetic scratch image/audio fixtures (never real child data).
3. The typed result and the runner's own latency/VRAM measurements were captured; no raw model
   output, prompt, endpoint, credential, or local path is recorded anywhere in this note.

## Typed outcome

| Field | Value |
|---|---|
| `status` | `FAILED` |
| `error_code` | `VISION_SCHEMA_INVALID` |
| `error_detail` | `OUTPUT_MAPPING_FAILED` |
| `attempt_number` | `1` |
| `repair_attempted` | `false` |
| `policy_execution_state` | `NOT_EXECUTED` |

## Measured latency and VRAM

| Metric | Value |
|---|---|
| `wall_latency_ms` | `25729.172921999976` (≈ 25.73 s) |
| `baseline_vram_mb` | `0.0` |
| `peak_vram_mb` | `17080.0` (≈ 16.68 GiB) |
| `post_call_vram_mb` | `0.0` |

`post_call_vram_mb` — sampled on the selected GPU device immediately after
`adapter.understand()` returned — was `0.0`. This one sample supports the cleanup observation
(the parent process itself never allocates CUDA memory, so a non-zero reading would have meant
the worker was still alive or had leaked device state); it does not, on its own, prove there was
absolutely no allocation or process remaining anywhere on the device — it is the single measured
value this one call produced.

## Scratch cleanup

The operator reported the scratch fixture directory (`data/runtime/vision-b2-preflight/`) was
confirmed absent after the call returned — labeled `B2_SCRATCH_CLEAN` in the operator's report.
This is consistent with, and now corroborated under a real GPU run for, the cleanup behavior
already covered by the 17 no-GPU tests in `EV-003-T3-05` (`build_fixtures` and the adapter call
both sit inside the function's cleanup-covering `try`/`finally`).

## Internal-consistency cross-check

The reported field combination is exactly the "Schema-invalid, direct" row of the approved V2
terminal-outcome matrix (`P2_T3_PHASE_B_APPROVAL_REQUEST.md`): `VISION_SCHEMA_INVALID` /
`OUTPUT_MAPPING_FAILED` is permitted only at `attempt_number = 1` with `repair_attempted` true
only after a lossless fenced unwrap (here `false`, meaning no lossless fence-unwrap repair was
applied to this call; the raw content itself is not retained, so its exact shape is not
established in this note) and `policy_execution_state = NOT_EXECUTED` (the policy layer runs last and
never inspects a structurally invalid payload). `VisionUnderstandingFailureV2`'s own Pydantic
validators reject any other combination at construction time, so this outcome could not have
been reported as a legitimately typed result unless it actually satisfied every one of those
structural rules.

## Observation for B3 (not acted on)

The operator reported a generation-time warning that decoding flags `temperature`/`top_p`/
`top_k` were ignored. This is consistent with the frozen `VisionDecodingV1` profile — greedy
decoding (`sampling_enabled = False`) with `temperature`/`top_p`/`top_k` required `None` on the
profile itself. The warning's source is not determined here — it is recorded only as an
observation for the B3 structured-output mapping study to investigate; no cause is inferred, no
code was changed, and no rerun was performed in response to it.

## Budget

This one call's measured wall time (~25.7 s) is a small fraction of the one-hour Lightning L4
soft cap shared across B2–B4. Cumulative elapsed time for the whole session remains the
operator's responsibility to track; this note does not claim a cumulative total.

## What this evidence is not

- Not a schema-validity-rate measurement. One run is one data point; B3 is the structured-output
  mapping study with a proper sample.
- Not a profile freeze and not a runtime-default selection — `VisionProfileIdV2` remains a
  candidate under study, per D-11.
- Not B3, B4, or B5 — none of those has executed.
- Contains no raw model output, prompt text, endpoint, credential, or local filesystem path.
  Only closed typed identifiers, the two revision/status tokens named above, and the measured
  numbers in this note were relayed into it.

# P2-T3 Phase B Lightning handoff context

- Evidence ID: `EV-003-T3-04`
- Date: 2026-09-01
- Owner: Person 2
- Purpose: shared operational context for an AI or operator working on the approved, development-only Lightning L4 B2–B4 study

## Authority and interpretation

This is a handoff and debugging context, not a benchmark result, a profile freeze, or a runtime
default. Repository facts below are backed by the approved B1/B2 implementation records. The
Lightning observations are operator-reported setup observations and must not be restated as GPU
preflight or benchmark evidence until a real B2 run records its typed result and measurements.

The authoritative scope is the approved B1–B5 P2-T3 Phase B entry in
`approvals/TASK_APPROVAL.md`. It permits only synthetic fixtures and development-only Lightning L4
work. It does not permit credentials, production/deployment decisions, user-facing use, Gate A,
Integration Sprint work, or a profile/runtime default.

## Repository state an AI must begin from

- Remote branch: `plan/person-2-qwen3-vl-structured-understanding`.
- Committed B2 baseline: `1b9049a` (`feat(vision): add B2 environment readiness check`) and
  `f3e5830` (`feat(vision): add guarded B2 preflight runner`).
- The approved candidate is the sole V2 entry: `QWEN3_VL_8B_INSTRUCT_BF16_V1`, compute profile
  `GPU_BF16`, model `Qwen/Qwen3-VL-8B-Instruct`, immutable revision
  `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`.
- Exact runtime pins: `torch==2.8.0` (a CUDA local suffix is accepted only on this base version),
  `transformers==4.57.6`, `accelerate==1.10.1`, and `qwen-vl-utils==0.0.14`.
- V1 contracts, fake adapter, and their golden digest are frozen. Never widen a V1 identity,
  catalog, hash, or result contract while debugging V2.
- `QwenVisionEnvironmentReadinessV1` is a no-model-load checker. `READY` means setup readiness
  only; it does not prove model loading, inference, timeout cleanup, output mapping, latency, or
  VRAM.

## Operator-reported Lightning setup

- The selected Studio has one NVIDIA L4 GPU and CUDA was reported available.
- The Studio's default Conda environment is in use; the Studio does not permit creating a Python
  virtual environment there.
- The exact B1 dependency pins were installed in that Conda environment, and the editable backend
  package import was reported successful. The existing Torch build reported a CUDA local suffix on
  the approved base version.
- A local Qwen snapshot of approximately 17 GB was downloaded. Its local path and all environment
  values remain only in the ignored `backend/.vision.env` file and must never enter source, logs,
  evidence, prompts, or commits.
- `.vision.env` selects a local model directory, `device=cuda`, device index `0`, and
  `allow_model_download=false`.

These observations do **not** establish that the snapshot contains every pinned load-critical file
or that every local Hugging Face metadata record names the approved immutable revision. The current
checker is the required source of truth for those two questions.

## Work not yet evidenced

- No committed evidence records a real Qwen model load or a real Qwen inference.
- No B2 typed preflight result, latency measurement, VRAM baseline/peak/post-call measurement, or
  subprocess/device-cleanup observation exists.
- B3 structured-output mapping study, B4 held-out benchmark and repeat, and B5 recommendation are
  unexecuted.
- No profile is frozen and no runtime default is selected.

The B2-preflight runner and its tests are committed in `f3e5830`; it was reviewed and hardened
across three same-day passes (a safe `fixtures_dir` cleanup target via
`UnsafeFixturesDirectoryError`; `build_fixtures` inside a cleanup-covering `try`/`finally`; the
VRAM sampler's background thread stopped/joined even when the adapter raises; and
`UnsafeFixturePathError` requiring each builder-returned path to be a relative, existing regular
file strictly inside `fixtures_dir`). Seventeen focused tests against an injected fake pass; see
`EV-003-T3-05`, `P2_T3_PHASE_B_B2_PREFLIGHT_RUNNER_IMPLEMENTATION.md`. This remains code/test
evidence only, not Lightning runtime evidence.

## Required debug and execution order

1. Start read-only: confirm the branch/commit with `git status --short --branch` and `git log -1`.
   Do not treat an untracked runner or a local env file as remote state.
2. From `backend/`, install only the repository package without resolving dependencies:
   `python -m pip install --no-deps -e .`.
3. Run the committed B2 readiness checker against the explicitly selected ignored `.vision.env`.
   Preserve its sanitized JSON result exactly. Do not print the env file, a local path, raw GPU
   output, or a traceback.
4. If the result is `NOT_READY`, stop before model load. Use its closed issue tokens to choose a
   narrow remediation:
   - dependency issue: compare installed versions to the four approved pins;
   - CUDA/index/BF16/device-class issue: inspect availability only and preserve the typed result;
   - snapshot missing or revision `NOT_VERIFIABLE`/`MISMATCH`: do not enable downloads to bypass it;
     re-establish a local snapshot at the approved revision only after owner direction;
   - config issue: correct the ignored local file, not repository defaults or committed evidence.
5. Only after `READY`, and only after the B2 runner has passed review and been committed, perform
   exactly one real model load and one synthetic inference. Record the typed result plus latency,
   VRAM baseline/peak/post-call, and worker/device cleanup. A typed failure is valid evidence and
   must not be retried or rewritten into success.
6. Count every real B2–B4 GPU action against the shared one-hour Lightning L4 soft cap. Stop and
   obtain explicit reauthorization before any further GPU work when the cap is reached.

## Non-negotiable handoff rules

- Never enable model download during a readiness or preflight run.
- Never use real child media, raw model output, prompts, local paths, credentials, endpoints, or
  free-form provider/device errors in repository artifacts.
- Use synthetic fixtures only and keep temporary runtime files inside ignored scratch storage; clean
  them after the run.
- Do not push, benchmark, rerun inference, freeze a profile, or choose a default merely because a
  checker or first preflight succeeds. Those are separate governed actions.

# P2-T3 Phase B B2 preflight runner — implementation and no-GPU validation

- Evidence ID: `EV-003-T3-05`
- Date: 2026-09-01
- Owner: Person 2
- Scope: local code/test only, across three same-day hardening passes. No dependency install,
  no model download, no `.vision.env` edit, no Lightning/GPU/provider call, no Qwen load, no
  inference, no benchmark, at any point.
- Approval authority: `approvals/TASK_APPROVAL.md`, bounded P2-T3 Phase B B1–B5 scope
  (B2 = "one real model load and one synthetic inference... within the authorized one-hour
  soft-cap budget... typed-failure paths proven by injected fakes; record measured values or
  explicit `NOT_MEASURED` reasons").
- Related: `P2_T3_PHASE_B_B2_ENVIRONMENT_SETUP.md` (`EV-003-T3-03`, the no-model-load
  readiness checker) and `P2_T3_PHASE_B_LIGHTNING_HANDOFF_CONTEXT.md` (`EV-003-T3-04`, the
  operational handoff, which named this runner as an unreviewed proposal not in commit
  `1b9049a`).

## Result

The internal (non-CLI) B2 preflight runner at
`backend/src/sketch2life/benchmark/vision_b2_preflight.py`, mirroring the approved
`sketch2life.benchmark.asr_round1_runner` P2-T2 precedent, was reviewed and hardened across
three same-day passes. Given a `VisionUnderstandingPortV2` (the real `QwenVisionAdapter`
tomorrow, or an injected fake today), `run_b2_preflight`:

1. Validates that the caller-supplied `fixtures_dir` is a safe cleanup target — relative, and
   resolving strictly inside the current working directory, never the working directory
   itself or an ancestor of it — and raises `UnsafeFixturesDirectoryError` before writing a
   single byte if not.
2. Calls `build_fixtures(fixtures_dir)` to write exactly one synthetic PNG and one synthetic
   tone into the ignored `data/runtime/vision-b2-preflight/` scratch location — never real
   child data — with that call itself inside the function's outer `try`/`finally`, so a
   builder that writes one fixture and then raises still leaves the scratch directory deleted,
   never half-written debris.
3. Validates the two paths `build_fixtures` returns: each must be relative, must resolve
   strictly inside `fixtures_dir` (never equal to it, never outside it), and must be an
   existing regular file (`Path.is_file()`) — never a directory, never a non-existent path.
   Any violation raises `UnsafeFixturePathError` before P2-T1 validation and before the
   adapter is ever called. This check uses path metadata only (resolution and `is_file()`)
   and never opens or reads either file's contents, so a path pointing outside the scratch
   directory is never touched beyond a stat call.
4. Runs the real `DeterministicMediaValidator` (P2-T1) over those two fixtures. A result other
   than a real, earned `PASS` raises `NoRealP2T1PassAvailableError` and the adapter is never
   called — no fabricated `VisionMediaValidationProvenanceV1` is ever constructed.
5. Builds one `VisionUnderstandingRequestV2` whose `source_image_ref.artifact_ref` is a
   relative POSIX-style path (`Path.as_posix()`), which `VisionImageReferenceV1`'s own
   validator additionally rejects if it were ever absolute.
6. Calls `adapter.understand(request)` exactly once, timing wall-clock latency and sampling
   GPU memory before, during (peak), and immediately after the call via `nvidia-smi` — silently
   inert, never fabricating a value, when `nvidia-smi` is unavailable. The peak-sampling
   background thread, once started, sits inside its own `try`/`finally` around the adapter
   call, so `stop_and_get_peak_mb()` (which sets the stop event and joins the thread) always
   runs — including when `adapter.understand` raises — and no polling thread outlives the
   function.
7. Deletes the scratch fixtures in the outer `finally` block — covering fixture creation,
   path validation, P2-T1 validation, and the adapter call — using the same `fixtures_dir`
   already proven safe in step 1.
8. Returns a frozen `VisionB2PreflightResult`: closed status/error tokens, `profile_id`,
   `profile_catalog_hash`, `attempt_number`, `repair_attempted`, `policy_execution_state`,
   `model_identifier`/`model_revision` (only when the branch's contract permits
   `model_provenance`), wall latency, and VRAM baseline/peak/post-call or an explicit
   `vram_not_measured_reason`. No local path, raw model output, prompt, endpoint, or
   credential can appear in this result — it never carries the request or the raw adapter
   result, only values copied field-by-field from the closed contract plus measured numbers.

The `_VramSampler` helper is a deliberate duplicate of the ASR Round-1 sampler (not an
import), preserving the plan's "P2-T3 must not import from or depend on P2-T2's modules"
boundary noted in `P2_T3_VISION_RESEARCH_PLAN.md`.

## Non-goals preserved

No V1 contract, the V1 fake adapter, or either V1 golden digest was touched. This module adds
no B3 mapping-study loop, no B4 multi-fixture/repeat benchmark, no B5 recommendation, no
profile freeze or runtime default, and no CLI, API, UI, database, or queue surface. It does not
read, write, or reference `.vision.env`; runtime configuration stays entirely the caller's
responsibility (`QwenVisionRuntimeConfig.from_env_file`, unchanged from B1). It never sets
`allow_model_download` and never falls back to a remote model identifier.

## Test evidence

`backend/tests/unit/test_vision_b2_preflight.py` (**17 focused tests**, all against an
injected fake `VisionUnderstandingPortV2` — no GPU, no Qwen import):

- success path: typed `SUCCEEDED` result, `model_identifier`/`model_revision` populated,
  measured latency, VRAM fields `None` with `"VRAM sampling was disabled for this call"` when
  sampling is off;
- failure path: a fake `INPUT_NOT_VALIDATED` / `PROFILE_NOT_RESOLVABLE` result with no
  `model_provenance` reports `model_identifier`/`model_revision` as `None`, never fabricated;
- the adapter receives a real, earned P2-T1 `PASS` (real validator, not a stub) and a relative
  `artifact_ref` (no leading `/`, no drive-letter colon);
- scratch fixtures are deleted after a normal call, and after the adapter raises;
- **a builder that writes one fixture and then raises still leaves the scratch directory
  deleted** (`build_fixtures` runs inside the same cleanup-covering `try`/`finally`);
- fixtures that fail P2-T1 (silent companion audio) raise `NoRealP2T1PassAvailableError`
  before the adapter is ever called (`adapter.calls == 0`);
- `nvidia-smi` unavailable (`subprocess.run` raising `OSError`) leaves every VRAM field `None`
  with the closed `"nvidia-smi was unavailable or returned no sample"` reason;
- **the VRAM background sampler thread is actually created (a fake successful `nvidia-smi`
  response forces `_available=True`) and is confirmed stopped and joined
  (`thread.is_alive() is False`) after the adapter raises** — a direct assertion on the
  sampler instance, not just on its side effects;
- an absolute `fixtures_dir`, a `fixtures_dir` equal to the current working directory, and a
  `fixtures_dir` that escapes the working directory via `..` are each rejected by
  `UnsafeFixturesDirectoryError` before any fixture is written and without calling the adapter;
- **a builder-returned image path that is absolute and outside scratch, one that is relative
  but resolves outside scratch, one that equals `fixtures_dir` itself, one that is a directory
  nested inside scratch, and one that does not exist inside scratch** are each rejected by
  `UnsafeFixturePathError` before P2-T1 validation, with `adapter.calls == 0` and the scratch
  directory cleaned up afterward.

## Validation performed today (2026-09-01)

All commands run from `backend/` against the local `.venv`:

| Command | Result |
|---|---|
| `pytest tests/unit/test_vision_b2_preflight.py` | **17 passed** |
| `pytest` (full backend suite) | **427 passed, 5 skipped** |
| `ruff check .` | All checks passed |
| `mypy --strict src` | Success: no issues found in 51 source files |
| `python ../tools/validate_harness.py` | `HARNESS_VALID` |
| `python ../tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` |
| `python ../tools/validate_architecture.py` | `ARCHITECTURE_VALID` |
| `python ../tools/validate_skeleton.py` | `SKELETON_VALID` |
| `git diff --check` | clean |

## What this evidence is not

No Qwen dependency was installed, no model weight was downloaded, `.vision.env` was not
created or edited, and no Lightning/GPU/provider call occurred at any point today. No
`model_load_performed` or `inference_performed` value exists anywhere in this note because
none was measured. Every VRAM number referenced in the test evidence above (e.g. the
sampler-thread test) comes from a monkeypatched `subprocess.run` fake, never a real
`nvidia-smi` call or a real GPU. This note records reviewed, tested, local code only — the B2
typed GPU preflight itself (one real model load, one real synthetic inference, real
latency/VRAM/cleanup measurements) remains future work, gated on the operator's `READY`
readiness result and executed on Lightning L4 under the shared one-hour B2–B4 soft cap.

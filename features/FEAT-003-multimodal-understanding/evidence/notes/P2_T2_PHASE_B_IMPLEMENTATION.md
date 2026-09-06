# P2-T2 Phase B implementation evidence

- Evidence ID: EV-003-T2-02
- Date: 2026-08-30
- Reviewer: Codex; implementation requested directly by the project owner under the approved Phase B scope (`approvals/TASK_APPROVAL.md`, "Current approved scope — P2-T2 Phase B")
- Data: runtime-generated synthetic WAV only (a 1-second 440 Hz tone, stdlib-generated); no real child data, real speech corpus, provider credential beyond the local GPU/model download, API, queue, database, or mobile access

## Delivered behavior

### B1 — additive contract/catalog change (`backend/src/sketch2life/contracts/schemas/asr.py`)

- `AsrProfileId` gained `WHISPER_TURBO_INT8_AUTO_V1`, `WHISPER_TURBO_FP16_AUTO_V1`, `WHISPER_LARGE_V3_INT8_AUTO_V1`. `AsrProfileV1.adapter_kind` widened to add `"FASTER_WHISPER"`; `compute_profile` widened to add `"GPU_INT8_FLOAT16"`/`"GPU_FLOAT16"`. New fields `model_identifier`, `model_revision`, `weight_provenance` (new `AsrWeightProvenanceV1` model), `adapter_version`, `runtime_version` — all `None` for `DETERMINISTIC_FAKE` entries, all required for `FASTER_WHISPER` entries, enforced by a new `AsrProfileV1` validator.
- `phase_a_profile_catalog()` renamed to `asr_profile_catalog()` — one static, versioned, phase-agnostic catalog covering both the unchanged Phase A fake entries and the Phase B catalog candidates. The readiness contract plans exactly the two Turbo Round-1 profiles; large-v3 is not run by Round 1. `AsrRequestV1`'s existing request-construction validator resolves against this same function; no per-request dynamic catalog injection was introduced.
- `config_hash` (`profile_config_hash()`) is unchanged mechanically (SHA-256 of canonical `model_dump(mode="json")`); it now automatically covers every new provenance field because they live on `AsrProfileV1`.
- Model/weight provenance (verified against upstream sources, not fabricated):
  - Turbo candidates: `deepdml/faster-whisper-large-v3-turbo-ct2` @ `4df90f75321148c3a29a9e2351b7ddf8f5b115a8`, license MIT (HuggingFace Hub API `sha`/`tags`).
  - `large-v3` candidate: `Systran/faster-whisper-large-v3` @ `edaa852ec7e145841d8ffdb056a99866b5f0a478`, license MIT.
  - Adapter/runtime versions: `faster-whisper-asr-adapter-v1` (this adapter's own version string); `faster-whisper==1.2.1;ctranslate2==4.8.1` (exact-pinned, matching PyPI's latest stable releases at implementation time).

### B2/B3 — isolated runtime config and real adapter

- `backend/src/sketch2life/infrastructure/ai/faster_whisper_runtime_config.py`: `FasterWhisperRuntimeConfig` (`model_cache_dir`, `device`, `device_index`), built only via `.from_env(environ)` reading `SKETCH2LIFE_ASR_MODEL_CACHE_DIR`. No default path exists anywhere in the class; an unset/blank env var raises. Not added to `infrastructure/config/settings.py`.
- `backend/src/sketch2life/infrastructure/ai/faster_whisper_asr.py`: `FasterWhisperAsrAdapter` implements `AsrPort`. Constructor-injects `FasterWhisperRuntimeConfig`, an overridable `model_factory` (defaults to a lazily-imported real `faster_whisper.WhisperModel` loader), and an overridable `classify_transient` predicate (defaults to "never transient" — a deliberately conservative choice pending real operational evidence of `faster-whisper`/CTranslate2's exception taxonomy; see code comment and `DECISIONS.md`).
  - Preserves `INPUT_NOT_VALIDATED` (attempt_number 0, no model touched), the retry/repair matrix (`attempt_number`/`repair_attempted` bookkeeping identical in shape to Phase A's fake adapter), and the no-recapture boundary (silence → `SUCCEEDED`/`NO_SPEECH_SUSPECTED`, never a typed failure or recapture signal).
  - Verifies the original source audio's actual SHA-256 and, when present, the derived processing audio's actual SHA-256 before ever invoking the model. The derived working copy is used for inference; the immutable source reference is retained in every result. An unreadable file or hash mismatch is a typed `INPUT_NOT_VALIDATED` failure at attempt `0`, never a raw filesystem/hash exception.
  - `AUTO_DETECT` only: always calls `model.transcribe(..., language=None)`; a `HONOR_HINT` profile raises `NotImplementedError` at the port boundary (unreachable via the current catalog — no such candidate exists in Round 1).
  - Model/runtime device failures map to `ASR_MODEL_UNAVAILABLE`/`DEVICE_UNAVAILABLE` whether raised while loading or during inference (including CUDA, cuDNN, and cuBLAS); ordinary provider failures remain `ASR_PROVIDER_FAILURE`. No raw exception message is surfaced in the result.
  - The timeout wrapper returns at `profile.timeout_seconds`; it does not use an executor context manager, whose implicit `shutdown(wait=True)` would silently wait for blocked inference to finish. The synchronous upstream SDK has no cancellation API, so a timed-out worker can finish in the background; no Round 1 profile permits timeout retry, avoiding a second concurrent inference for one request.
  - One bounded local repair (segment timestamp clamping to the reported total duration; never re-invokes the model) is attempted before `ASR_SCHEMA_INVALID`.
  - No raw audio path, transcript content, or exception text is logged or placed in any result field beyond the closed `AsrErrorDetail` enum.

### Dependency

- `backend/pyproject.toml`: new optional group `asr-faster-whisper = ["faster-whisper==1.2.1", "ctranslate2==4.8.1"]`, exact-pinned (an intentional exception to this repo's usual range-pin convention) with the rationale recorded inline and in `DECISIONS.md`: CTranslate2's cuDNN/CUDA version requirement has changed across releases, and a range pin risks silently breaking local GPU compatibility between installs. No model weights are in Git. On 2026-08-30, the exact Turbo snapshot was explicitly downloaded to a user-selected external D: model location, not the repository or C:. Its revision and SHA-256 were verified against the downloaded metadata before local model-load preflight.

## Contract compatibility evidence for Phase A

- `backend/tests/unit/test_asr_phase_a.py` (all 17 tests, renamed to use `asr_profile_catalog`) passes unchanged; both Phase A fake catalog entries are asserted byte-for-byte identical to their pre-Phase-B values in `backend/tests/unit/test_asr_phase_b_contract.py::test_phase_a_fake_profiles_are_unchanged_after_the_catalog_rename`.
- New `backend/tests/unit/test_asr_phase_b_contract.py` (9 tests): Whisper Round 1 profiles resolve deterministically with correct provenance; `config_hash` is reproducible and distinct per profile; the `AsrProfileV1` validator rejects an incomplete `FASTER_WHISPER` profile, a `FASTER_WHISPER` profile with `compute_profile="NONE"`, and a `DETERMINISTIC_FAKE` profile carrying Whisper provenance fields; an out-of-catalog profile ID is still rejected.

## Commands and results

```powershell
backend/.venv/Scripts/python.exe -m pytest tests -q
backend/.venv/Scripts/python.exe -m ruff check src tests
backend/.venv/Scripts/python.exe -m mypy src/sketch2life
python tools/validate_harness.py
python tools/validate_repository_security.py
backend/.venv/Scripts/python.exe tools/validate_architecture.py
backend/.venv/Scripts/python.exe tools/validate_skeleton.py
git diff --check
```

Final verified result on 2026-08-30 after the adapter-regression corrections:

```text
56 passed
All checks passed! (ruff)
Success: no issues found in 35 source files (mypy)
HARNESS_VALID
REPOSITORY_SECURITY_VALID (publishable_files_scanned=446, absolute_machine_paths=absent)
ARCHITECTURE_VALID
SKELETON_VALID
(git diff --check: clean)
```

## Local GPU preflight

An earlier implementation report claimed an ad-hoc run downloaded approximately 800 MB and then failed on `cublas64_12.dll`; that history remains unverified and is not used as evidence. A controlled replacement preflight ran on 2026-08-30 after the exact Turbo snapshot was explicitly downloaded to a user-selected D: location:

- Snapshot revision: `4df90f75321148c3a29a9e2351b7ddf8f5b115a8`.
- Weight SHA-256: `e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da`.
- The direct local `faster_whisper.WhisperModel` load with `device="cuda"` and `compute_type="int8_float16"` returned `MODEL_LOAD_OK` on the RTX 4060 laptop GPU. No download to C: or model addition to Git occurred.

This proves only dependency/model/GPU **load** compatibility. It is not an inference or benchmark result. The adapter keeps a regression test for cuBLAS-like inference errors; if one occurs in a future controlled inference, it returns `ASR_MODEL_UNAVAILABLE`/`DEVICE_UNAVAILABLE` at attempt `1`, without raw exception text.

### Controlled GPU decode smoke test

On the same date, a one-second silent WAV was generated outside the repository under the user-selected external model location and passed directly to the local `faster_whisper` model with the fixed Round 1 decode settings (`device="cuda"`, `compute_type="int8_float16"`, auto-detect, beam size 5, VAD disabled, word timestamps disabled). This is a smoke test only — silence has no reference transcript and cannot produce WER/CER.

- Model construction: `MODEL_LOAD_OK`.
- Initial decode failed because `cublas64_12.dll` was absent. Per the official faster-whisper Windows guidance, the compatible CUDA 12 cuBLAS + cuDNN 9 archive was then downloaded and extracted to a user-selected external D: runtime location; neither a full CUDA Toolkit nor a global Windows PATH modification was installed.
- With that runtime directory prepended to the PATH of the **single test process only**, decode succeeded: `language="en"`, `language_probability=0.362549`, reported duration `1.0` second, and one emitted segment. Silent input can produce a low-confidence/hallucinated model output, so this result establishes only GPU execution, not ASR quality.
- Consequence: local Windows GPU inference is now operational for Phase B. The direct call still bypassed the project adapter; its adapter-level regression test verifies that a future device-runtime error maps to the closed typed `ASR_MODEL_UNAVAILABLE`/`DEVICE_UNAVAILABLE` result.

### Local env-to-adapter wiring

The ignored local `backend/.asr.env` is now supported without extending shared `Settings`: `SKETCH2LIFE_ASR_MODEL_DIR` selects the already-downloaded local Turbo snapshot, and `SKETCH2LIFE_ASR_NATIVE_LIBRARY_DIR` selects the extracted CUDA DLL directory. It is intentionally separate from the shared backend `.env`, whose unknown fields the application Settings validator rejects. `FasterWhisperRuntimeConfig.from_env_file()` reads that explicitly selected local env file and gives actual process environment precedence. Its process-only helper registers the DLL directory and prepends it to only the running Python process PATH before lazy-loading `faster-whisper`; it does not modify the user/system Windows PATH.

An adapter-level preflight then returned `SUCCEEDED`, `attempt_number=1`, and profile `WHISPER_TURBO_INT8_AUTO_V1` using the same silent WAV. No transcript text was emitted to evidence or logs. The `DETECTED` speech diagnostic from silent audio is further evidence that this smoke fixture is unsuitable for quality claims; it proves only the full local contract → adapter → GPU path works.

**Peak VRAM / p50/p95 inference latency: `NOT_MEASURED`** — the smoke test proves decoding, but a versioned speech fixture/reference transcript and repeated controlled runs are still required for benchmark metrics.

## Round 1 synthetic ASR benchmark (R3-scoped, ASR-only)

**Update (2026-08-30): executed.** Both blockers below were later resolved — see
`P2_T2_PHASE_B_FIXTURE_PROVENANCE.md` and `P2_T2_PHASE_B_ROUND1_ASR_REPORT.md` for the measured
Round-1 results. The account below is left as-is as the historical record of this package's own
scope, which did not include running the live benchmark.

**`NOT_MEASURED` at the time of this package — blocked, not fabricated.** Two independent blockers:

1. No compliant `READY` Round 1 speech fixture manifest or local payload exists yet in this environment. The versioned template now covers the ~20-fixture Vietnamese/non-Vietnamese/code-switching/silence/noise set described in `P2_T2_ASR_RESEARCH_PLAN.md` R3, but a synthetic/TTS-versus-licensed source decision and compliant local payload/reference-transcript refs and hashes are still required.

VAD alternatives, beam-size alternatives, and word-timestamp alternatives remain `NOT_MEASURED` by design (Round 1 scope, per `plan/P2_T2_ASR_RESEARCH_PLAN.md` B4) — not because of the blockers above.

## Limitation and follow-up

No profile was proposed for freeze and no runtime default was selected — none of that was in scope for this implementation. Before real WER/CER evidence can be produced, select the fixture source, populate the existing versioned manifest as `READY` with compliant local payload/reference-transcript refs and hashes, and run the fixed Round 1 profile comparison. The Phase B approval already covers that controlled run. `HONOR_HINT`/forced-language profiles remain unimplemented in the catalog, per Round 1 scope. P2-T5's CLI/end-to-end harness, any cloud/provider deployment, and API/UI/queue/mobile/session/database work were not touched, per the approved boundary.

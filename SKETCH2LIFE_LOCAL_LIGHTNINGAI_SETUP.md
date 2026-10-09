# Local development + LightningAI test setup

Preparation only, 2026-10-10. No remote connection, sync, install, weight download,
GPU inference, child-media upload, TTS or new MP4 was performed.

## Repository location

The current checkout is the existing OneDrive Git repository. The requested
`D:/Codex/Sketch2Life` directory contains private evidence, not a Git checkout.
Do not clone over that directory or copy private evidence into Git. Relocation
requires a separate choice: a new empty checkout directory or an approved migration.
Use `${LOCAL_REPOSITORY_ROOT}` below for the actual checkout.

## Available integration

- Existing `tools/lightning_whiteboard_provider.py` supports a single-source
  AutoPipelineForImage2Image illustration call and a Wan `ti2v-5B` subprocess route.
- The image call does NOT currently support separate Gold/character references.
  `application/ports/illustration_edit.py` defines a preparation-only reference
  contract and metadata mock; it is not connected to HTTP or real inference.
- Existing Wan adapter is retained unchanged. Workspace revision/checkpoint/CLI
  compatibility is UNVERIFIED; a non-empty checkpoint directory is not proof.
- Wan is a video model, not a substitute for an image-edit model.
- V1 remains default; V2 false. No changes to Gates, authentication or upload.

## Safe local commands (repository root)

```powershell
& backend/.venv/Scripts/python.exe tools/verify_lightning_runtime.py --mode mock
& backend/.venv/Scripts/python.exe tools/verify_lightning_runtime.py --mode inventory
& backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_lightning_runtime_setup.py
```

`--mode real` intentionally exits 2: REAL_INFERENCE_NOT_AUTHORIZED. It cannot run
models. Mock does not generate artwork, so its success is not an AI quality PASS.
Inventory queries nvidia-smi and package availability without importing Torch/models.

## LightningAI: owner-run read-only inventory, after connection approval

```bash
git status --short --branch
git rev-parse HEAD
python tools/verify_lightning_runtime.py --mode inventory --wan-repo /absolute/wan-checkout
python -m pip freeze
```

No workspace is created or changed by these commands. Do not assume an old
screenshot establishes current GPU/CUDA/model readiness. No server is started.
After sync is separately approved, export only committed source at the chosen SHA
using `git archive`; inspect the archive before transferring it. Do not copy the
dirty worktree, private reports, master masks, drafts, caches, .env or model weights.
Verify received SHA/manifest and run synthetic mock/unit tests first.

## Dependency manifests and configuration

- Backend `pyproject.toml`: dev, whiteboard-renderer, story-video-image optional extras.
- `config/lightning/requirements-mock.txt`: existing test extras, no GPU model runtime.
  Resolve its relative path from the config directory; do not install this turn.
- `.env.example` and `runtime-profile.example.json`: placeholders only.
- No speculative GPU lockfile: record the actual Wan revision and its requirements,
  then resolve compatible Torch/CUDA/Diffusers in a separate environment after approval.
- Image-edit model, revision, license, hashes, pipeline class and precision remain
  unselected. SDXL single-source compatibility does not imply multi-reference support.

The [official Wan2.2 README](https://github.com/Wan-Video/Wan2.2) documents TI2V-5B
on at least 24GB VRAM with its specified offload flags; this is not a measured
Sketch2Life/L4 acceptance. Image editing has separate GPU/RAM requirements that
must be determined for the selected model. Do not use 14B settings for 5B.

## Real test gate (not executable in the new smoke script)

Before any real test: explicit cost/data/download/inference approval, verified
workspace and package versions, GPU CUDA check, model hashes/licenses, synthetic
fixture input, budget/time limits and private output root. Test illustration first;
compare source identity/Gold style/cross-scene consistency before drawing/video.
Production Gate A/B server records remain distinct from local-demo approval.

Output layout outside Git: `inputs-private/`, `manifests/`, `candidates/`,
`diagnostics/`, `metrics/`. Record prompts, reference roles/hashes, model revision,
seed, elapsed time/peak memory and output hashes. No image data in telemetry.
Real inference smoke and quality acceptance remain BLOCKED pending these gates.

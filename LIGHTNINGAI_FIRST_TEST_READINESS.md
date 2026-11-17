# Sketch2Life — LightningAI First Test Readiness

**Audit date:** 2026-10-10 (Asia/Saigon)
**Checkout audited:** this repository checkout
**Audited HEAD:** `83676ba`
**Decision:** `CONDITIONAL_READY_FOR_REVIEW`; do not push or run GPU inference yet.

## 1. Git readiness

At the start of this audit the branch was 10 commits ahead of its remote-tracking
branch. The current branch remains `codex/feat-018-contract-plan` and the remote is
`https://github.com/CaoDat-2410/Sketch2Life.git`.

The ten pre-existing local commits were:

| SHA | Message |
|---|---|
| `29a010c` | fix(story-video): retain source bytes in V2 canvas reconstruction prototype |
| `c43c655` | feat(experimental): preserve bounded raster stroke and schedule diagnostics |
| `13b9610` | chore(ai-runtime): add fail-closed Lightning inventory and image-edit mock boundary |
| `8dcfc11` | feat(experimental): archive offline semantic authoring and object proof tools |
| `9c309f6` | feat(experimental): preserve optional local character rig motion proof |
| `a66f6bf` | docs(story-video): preserve experiment evidence and stabilization boundaries |
| `04f73ab` | style(docs): remove trailing blank lines from archived proof reports |
| `46756f7` | chore(lightningai): add separated setup verify and test workflow |
| `84d15c4` | test(lightningai): scope remote smoke checks to verified regression set |
| `ce66ba0` | docs: record Windows and LightningAI environment policy |

This readiness task added one narrowly scoped local fix:

| SHA | Message | Files |
|---|---|---|
| `3cd84bd` | fix(lightningai): verify isolated Wan runtime paths | `scripts/lightningai/verify.sh`, `tools/verify_lightning_runtime.py` |

The readiness report was committed as `10ece0f`, followed by the whitespace-only
documentation commit `83676ba`. No push, merge, deploy, reset, rebase or force
operation was performed.

### Current uncommitted files

These remain outside the readiness commit and must not be staged by a broad add:

- `backend/src/sketch2life/infrastructure/media/whiteboard_stroke_extraction.py` — pre-existing V1/user work.
- `backend/tests/unit/test_whiteboard_mvp_renderer.py` — pre-existing V1/user work.
- `backend/tests/unit/test_whiteboard_stroke_extraction.py` — pre-existing V1/user work.
- `backend/src/sketch2life/infrastructure/media/illustrated_story_slice.py` — incomplete/interrupted prototype; not part of this milestone.
- `assets/generated/whiteboard-hand-marker-v1.*` and `whiteboard-hand-marker-v2.*` — unapproved hand-asset drafts and provenance notes.

There are no staged files after the scoped script commit. The dirty files are
preserved and are not included in `origin/codex/feat-018-contract-plan..HEAD`.

## 2. LightningAI scripts

| Script | Verified behavior | Windows status |
|---|---|---|
| `scripts/lightningai/setup.sh` | Requires explicit `SKETCH2LIFE_ALLOW_INSTALL=1`; creates a separate venv; installs only backend dev/whiteboard extras; runs `pip check`; writes inventory; never downloads model weights or runs inference. | Syntax checked; not executed on Windows. |
| `scripts/lightningai/verify.sh` | Requires the separate venv, `nvidia-smi`, `WAN_REPO_DIR`, and `WAN_CKPT_DIR`; checks CUDA/Torch, Wan `generate.py`, checkpoint directory presence, and V1/V2 flags. | Syntax checked; expected to fail closed here because no Lightning venv/GPU paths exist. |
| `scripts/lightningai/run_tests.sh` | Runs the selected V2/V1-contract regression set, scoped Ruff, scoped Mypy, and repository security validation. | Not executed here because it intentionally requires the Lightning venv. |

The `verify_lightning_runtime.py` inventory is read-only. `--mode real` exits
`REAL_INFERENCE_NOT_AUTHORIZED`; it does not download weights, start a server,
upload an image, or invoke paid inference.

The local checks completed:

- Git Bash syntax check for all three scripts: PASS.
- Runtime inventory mock mode: PASS (`MOCK_ONLY`, no artifact generated).
- Lightning runtime setup unit tests: 5 PASS.
- Scoped regression set: **72 passed in 21.45s**, 0 failed, 0 skipped.
- Scoped Ruff: PASS.
- Scoped Mypy: PASS, 7 source files.
- Repository security validator: PASS; 1,694 publishable files scanned, no absolute machine paths, credentials or signing keys detected.
- `git diff --check`: PASS.

The broad repository Ruff baseline is not claimed as clean; this readiness result
only claims the exact scoped files used by `run_tests.sh`.

## 3. Privacy and push safety

The private `familly.jpg`/`family1.jpg`, reviewed masks, pilot MP4s, model caches,
weights, and the unapproved hand drafts are not part of the ten-commit push range.
No credentials, `.env` secrets, private child media, model weight files, or
generated video outputs are staged. Existing public fixture/catalog assets in the
repository are not private source uploads and were not reclassified by this task.

The security check is evidence for the current tracked/untracked working tree; it
is not permission to publish private media. A human review of the dirty files is
still required before any later `git add`.

## 4. Exact push and LightningAI procedure

Do not run the push until approving the exact SHA and dirty-file treatment.

### On the Windows checkout, after approval

```powershell
git status --short --branch
git diff --cached --name-only
git rev-parse HEAD
git push --set-upstream origin codex/feat-018-contract-plan
```

The push contains committed files only; the dirty files listed above remain local.
Do not use `git add .` or `git add -A`.

### In the existing LightningAI Workspace

```bash
cd /path/to/Sketch2Life
git fetch origin
git checkout codex/feat-018-contract-plan
git pull --ff-only origin codex/feat-018-contract-plan
git rev-parse HEAD
```

The final `git rev-parse HEAD` must equal the approved Windows SHA. If it differs,
stop before setup or tests.

Set the existing Wan paths without moving or modifying the Wan environment:

```bash
export WAN_REPO_DIR=/path/to/existing/Wan2.2
export WAN_CKPT_DIR=/path/to/existing/Wan2.2/checkpoints
export SKETCH2LIFE_LIGHTNING_VENV="$PWD/.runtime/lightning-venv"
```

Then, only after approving dependency installation in the isolated venv:

```bash
export SKETCH2LIFE_ALLOW_INSTALL=1
bash scripts/lightningai/setup.sh
bash scripts/lightningai/verify.sh
bash scripts/lightningai/run_tests.sh 2>&1 | tee /tmp/sketch2life-lightning-test.log
cat "$SKETCH2LIFE_LIGHTNING_VENV/runtime-inventory.json"
```

`setup.sh` installs repository development and whiteboard-renderer extras into the
new venv only. It does not install AI model packages or alter the existing Wan
Python environment. `verify.sh` must report the actual GPU, CUDA/Torch readiness,
Wan repository revision, checkpoint presence, and `V1 default, V2 and video
runtime OFF`. A missing path returns `REQUIRES_LIGHTNINGAI_WAN`, not PASS.

## 5. Current model/dependency status

No LightningAI model inventory was performed from this Windows session. The local
checkout does not contain model weights and the image-edit extras are not installed
in the Windows test environment. The current Wan route is a separate text/image-to-
video adapter, not proof that an image-edit model is available.

The existing image-edit boundary is fail-closed and uses the configured
`SKETCH2LIFE_IMAGE_MODEL`; it does not select or download a model automatically.
The next image milestone therefore remains **BLOCKED_PENDING_MODEL_REVIEW**.

A candidate for later approval is `Qwen/Qwen-Image-Edit-2509`: its official model
card documents Diffusers image editing and multi-image editing, and the hosted
repository currently reports about 57.7 GB of files. That is a large download and
does not establish that an L4 can run it within the current Wan workspace budget.
It must be measured on the actual Lightning machine, preferably with an approved
quantized/offload plan, before any download or inference. Source:
[Qwen-Image-Edit-2509 model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2509).

No image was uploaded, no child image was sent to a remote service, and no GPU
inference was run in this milestone.

## 6. Required approval before the next action

1. Approve the exact current HEAD for push, while explicitly leaving the listed
   dirty files uncommitted.
2. Approve use of the existing LightningAI Workspace and installation into the
   isolated `.runtime/lightning-venv` only.
3. Provide/confirm the real `WAN_REPO_DIR` and `WAN_CKPT_DIR` paths in that
   workspace; do not paste secrets into Git or this report.
4. Approve the first Lightning verification/test run. This is infrastructure
   validation only and does not authorize image upload or model inference.
5. Separately approve a model, weight download, input image, and inference prompt
   before the one-image generation milestone.

Until these approvals are given, status remains:

```text
GITHUB_SYNC: READY FOR HUMAN REVIEW, NOT PUSHED
LIGHTNING_GPU: NOT VERIFIED
LIGHTNING_TESTS: NOT RUN ON LIGHTNING
V1: DEFAULT/PRESERVED
V2: OFF
IMAGE_INFERENCE: NOT AUTHORIZED/NOT RUN
```

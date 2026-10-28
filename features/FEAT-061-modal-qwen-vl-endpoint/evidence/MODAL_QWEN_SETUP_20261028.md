# Modal Qwen3-VL-8B endpoint configuration

- Date: 2026-10-28 (Asia/Saigon).
- Approved scope: FEAT-061 (numbered FEAT-048 in the approval record) plan revision 1, direct owner instruction recorded in `approvals/TASK_APPROVAL.md`.
- Model: `Qwen/Qwen3-VL-8B-Instruct` (Qwen3-VL, 8B), revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`, profile `QWEN3_VL_8B_INSTRUCT_BF16_V1`, compute BF16.
- Service: custom Modal ASGI Web Function. The app registers only `GET /health` and the existing authenticated `POST /v2/vision` handler. This preserves the Vision V2 2.0 request/result shapes.
- GPU: one NVIDIA L40S container maximum (Modal lists 48 GB GPU memory); eight vCPU, 32 GiB host memory; scale to zero; 30-second idle scale-down; 300-second startup timeout; 150-second function timeout.
- Model files: read-only named Modal Volume at `/models`, with the exact snapshot under `/models/qwen3-vl-8b-instruct`. Qwen downloads are disabled; the endpoint fails safely if the snapshot is missing.
- Auth: runtime Modal Secret `sketch2life-modal-qwen-auth`, containing key `LIGHTNING_DEV_AUTH`. No secret value is stored in Git or set in the image.
- Package source: `backend/pyproject.toml` optional extra `vision-qwen`; its exact pins are `accelerate==1.10.1`, `qwen-vl-utils==0.0.14`, `torch==2.8.0`, and `transformers==4.57.6`. Base project runtime dependencies are installed from that same project manifest. SAM2, faster-whisper and video model extras/checkpoints are not included.
- Owner-operated runtime correction on 2026-10-29: the Modal image now adds a separate layer pinning `torch==2.8.0` and `torchvision==0.23.0`. The CPU diagnostic identified that Qwen3VL processor initialization requires Torchvision even for the image-only route; after the correction the owner reported `PROCESSOR_READY`. The backend manifest remains unchanged, and this check does not establish GPU inference. See `PHASE_B_OWNER_REPORT_20261028.md` for the original failure and recheck evidence.

## Operator steps for a future authorized Modal account run

Run these steps in the Modal environment/account that will own the development endpoint. They create cloud resources or upload weights and are intentionally not run as part of this repository change.

1. Install and authenticate the Modal CLI on the host that has access to the already staged Qwen snapshot. Do not place the CLI token in this repository.
2. Create a Volumes v2 model store:

   ```sh
   modal volume create --version=2 sketch2life-qwen3-vl-8b-v1
   ```

3. Upload the exact, previously staged snapshot while retaining its revision metadata:

   ```sh
   modal volume put sketch2life-qwen3-vl-8b-v1 <existing-local-qwen3-vl-8b-snapshot-directory> /qwen3-vl-8b-instruct
   ```

   Do not copy weights into the repository or fetch a different model revision as part of this step. Do not add a trailing slash to the remote destination: Modal CLI 1.6.3 appends the local directory's basename when the destination ends in `/`, which can create a nested directory. Confirm `config.json`, tokenizer/processor files and all required weight shards are directly under the destination before serving.
4. In Modal Dashboard → Secrets, create `sketch2life-modal-qwen-auth` with key `LIGHTNING_DEV_AUTH` and a newly chosen bearer secret. Do not put the value in a command line, notebook, repository file, or chat.
5. From the repository root, use Modal's ephemeral local-development command first:

   ```sh
   modal serve deployment/modal/qwen_vision_v2.py
   ```

   It exposes a temporary public URL. Call `/health` first, then submit only an authorized synthetic fixture to `/v2/vision` with `Authorization: Bearer <secret>`; never use real child data in this dev evaluation.
6. Record sanitized HTTP/auth outcomes, cold and warm inference time, peak GPU memory, and billed resource duration in this feature's evidence. Stop the `modal serve` session when finished. A permanent `modal deploy` or backend endpoint integration is outside FEAT-061's current scope.

The Modal function's 150-second web request ceiling is close to the backend's 120-second request timeout. A full path smoke result is necessary before anyone relies on the endpoint; deployment configuration alone does not establish that cold-start latency will fit.

## Evidence and limits

At the original configuration review no Modal credentials, resources, Volume, Secret, model weights, GPU or provider call were used. Subsequent owner-operated setup is recorded separately in `PHASE_A_OWNER_REPORT_20261028.md` and `PHASE_B_OWNER_REPORT_20261028.md`. Remote image build, Modal SDK compatibility, dependency/CUDA installation, token acceptance, inference, timeout behavior and cost remain `NOT_MEASURED`. The historical Qwen-only L4 memory and quality results are in FEAT-003; they are not Modal measurements or production approval. See [Modal GPU guidance](https://modal.com/docs/guide/gpu), [Modal custom ASGI Web Functions](https://modal.com/docs/guide/webhooks), [Modal Volumes](https://modal.com/docs/guide/volumes), [Modal Secrets](https://modal.com/docs/guide/secrets), and [Modal request timeouts](https://modal.com/docs/guide/webhook-timeouts).

## Local configuration checks

- `python -m py_compile deployment/modal/qwen_vision_v2.py`: passed. This checks Python syntax only; Modal and application imports are not run locally.
- `git diff --check`: passed.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`, 2,614 publishable files scanned.
- `python tools/validate_harness.py --feature features/FEAT-061-modal-qwen-vl-endpoint`: the new feature reported no missing paths or approval errors; the repository-wide validator returned `HARNESS_INVALID` because FEAT-045, FEAT-046 and FEAT-047 lack their `evidence/screenshots` and `evidence/metrics` directories. Those unrelated paths were not changed.
- No unit/integration tests, Modal image build, GPU allocation or live inference was run.

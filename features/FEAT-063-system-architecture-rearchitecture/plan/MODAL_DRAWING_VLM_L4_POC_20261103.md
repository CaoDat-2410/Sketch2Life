# Modal drawing VLM L4 POC — 2026-11-03

## Status and authority

- Status: `APPROVED`; the exact plan hash and approval scope are recorded in `approvals/TASK_APPROVAL.md`.
- Feature: FEAT-063; canonical workflow source is `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft, especially §§6.2–6.3, 24.3, 27, 29, and 31.
- Owner instruction: after creating the Modal environment, continue with the next work and host the AI workloads the system needs (direct chat instruction, 2026-11-03).
- Purpose: turn the SRS v2.3 `drawing.analyze` candidate into the first bounded, private Modal inference POC. Image understanding is the first AI stage in the Parent/Teacher drawing-to-video pipeline.
- Model is an experimental POC profile only. It does not amend the SRS, select a production default, or enable any product workflow.

## Exact approved scope

1. Add a separate Modal app at `deployment/modal/srs_v23/drawing_vlm_app.py` for `drawing.analyze` only, using:
   - Hugging Face `Qwen/Qwen2.5-VL-7B-Instruct` at immutable revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`;
   - Modal `dev`, one L4 GPU, FP16/SDPA, one maximum active container, no minimum warm containers, and bounded generation/input sizes;
   - Python 3.11 with `torch==2.7.1`, `transformers==4.53.0`, `accelerate==1.8.1`, `huggingface_hub==0.33.4`, and `Pillow==11.2.1`, plus a CPU-only model-download function;
   - a Volume v2 model-weight mount (read/write for the pinned download function; read-only for inference) and the existing-by-convention Volume v2 job-scratch name for one synthetic input attempt;
   - the existing `ModalWorkerInputV1` path/hash-only envelope. The worker must verify the manifest and image bytes, enforce the existing size cap and exact attempt-prefix containment, and must not accept media bytes or remote URLs in the function payload;
   - no HTTP/web endpoint and no production backend integration.
2. Create one deterministic synthetic butterfly line drawing and a generator/acceptance script at `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_drawing_vlm_poc.py`, with the generated fixture at `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/drawing_vlm_synthetic_butterfly.png`. The script stages the fixture and manifest through the Modal Volume SDK, then resolves the deployed function by name and calls it exactly once. The fixture contains no child data and no image metadata.
3. In Modal `dev` only, create the two named Volume v2 resources if absent, download the pinned public checkpoint, deploy the separate app, and run exactly one bounded synthetic drawing-analysis inference. Do not use `main`, a public endpoint, or a secret/token for this public checkpoint.
4. Record environment/resource names, model revision/license source, dependency/GPU profile, fixture provenance/hash, single-call result, observed timing, billing summary before/after when available, and limitations in task evidence. Update FEAT-063 context, decisions, source register, status, and the global source register additively.

## Files in scope

- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_drawing_vlm_poc.py`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/drawing_vlm_synthetic_butterfly.png`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_DRAWING_VLM_L4_POC_20261103.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `docs/context/SOURCE_REGISTER.md`

## Explicit exclusions

- No real child profile, photograph, voice, lesson, or production data; no real MinIO/S3 transfer.
- No backend route, queue, quota, storage adapter, migration, API contract, mobile/web client, or SRS/ADR amendment.
- No Qwen story/storyboard, ASR, line-art generation, lesson visuals, SAM2, LTX video, TTS, or safety model selection/deployment in this POC. They remain separate pipeline workloads; this task does not claim the AI fleet is complete.
- No production model selection, quality claim, safety certification, persistent always-on GPU, model fine-tuning, secret creation, paid third-party API, commit, push, or merge.
- No broad product test suite. The single live Modal call is the requested POC acceptance check; local checks are limited to syntax, envelope/manifest validation, resource inventory, and the repository security validator.

## Acceptance criteria

- AC1. The pinned model revision and its Apache-2.0 license are recorded from the official model card; the deployment does not use the legacy Qwen3-VL app or its settings.
- AC2. The new app exposes only a private Modal SDK function for `drawing.analyze`; the function uses L4 with `max_containers=1`, `min_containers=0`, no configured retries, finite timeout, bounded image resolution, and bounded output tokens.
- AC3. Model weights are downloaded from the pinned revision to the named Volume v2; inference mounts that volume read-only. The staged input is under a unique attempt prefix on a separate Volume v2.
- AC4. The worker accepts the existing versioned path/hash-only payload, verifies manifest and input SHA-256/size/type, and rejects malformed or out-of-prefix references before model load/inference.
- AC5. Exactly one synthetic image inference completes and returns a bounded structured candidate subject plus an explicit human-confirmation requirement. The result is documented as a smoke check, not an accuracy or safety benchmark.
- AC6. The app is deployed only to Modal `dev`; no web URL is created, no secret is added, and no real child data is transferred.
- AC7. Task evidence and additive FEAT-063/global records are complete, and `python tools/validate_repository_security.py` passes.

## Risks and handling

- A valid payment method is required by Modal for GPU use. If the account cannot allocate L4, record the exact blocker without switching environments or trying a different paid GPU.
- The checkpoint is approximately 16.6 GB and consumes persistent Volume storage. Use only the empty dev Volumes confirmed during preflight; do not delete or overwrite unreviewed resources.
- L4 fit, cold-start, throughput, image quality, and Modal cost are unverified until the bounded call. If the call fails due to runtime or VRAM, record evidence and propose a separate model/GPU change instead of silently changing the approved profile.
- This POC does not provide a calibrated confidence score or a safety decision. The parent/teacher must still confirm the detected subject in the product workflow.

## Verification sequence

1. Confirm plan hash and approval record before implementation.
2. Inspect the Modal `dev` app/volume/secret inventory again before creating resources.
3. Generate and hash the synthetic fixture; run local syntax and payload/manifest validation.
4. Create the named Volume v2 resources in `dev`; download the pinned weights; verify the revision marker.
5. Deploy only `drawing_vlm_app.py` to `dev`, stage the fixture via the Volume SDK, invoke exactly once, and collect structured output/timing.
6. Confirm the function scales to zero and the resource inventory contains no public web endpoint or unexpected secret.
7. Run the repository security validator and complete task evidence/context updates.

## Source basis

- Canonical SRS v2.3-draft, §§6.2–6.3, 24.3, 27, 29, 31.
- Qwen model card: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct
- Qwen model revision: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/tree/cc594898137f460bfe9f0759e9844b3ce807cfb5
- Transformers Qwen2.5-VL usage: https://huggingface.co/docs/transformers/v4.53.0/en/model_doc/qwen2_5_vl
- Modal GPU configuration: https://modal.com/docs/guide/gpu
- Modal Volume v2, read-only mounts, and model weights: https://modal.com/docs/guide/volumes and https://modal.com/docs/guide/model-weights

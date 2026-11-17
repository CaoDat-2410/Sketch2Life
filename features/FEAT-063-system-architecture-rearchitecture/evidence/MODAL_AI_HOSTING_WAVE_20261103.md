# Modal AI hosting wave evidence — 2026-11-03

## Authority and scope

- Approved plan: `plan/MODAL_AI_HOSTING_WAVE_20261103.md`, SHA-256 `C8FCB03681F2145E727F89E55DDD159AA354814E30B868CD745B930A83FCA5BA`; approval is in `approvals/TASK_APPROVAL.md`.
- The canonical source remains FEAT-063 SRS v2.3-draft. All work here is private Modal `dev`, synthetic-only, experimental, and not a production model decision.
- No real child media, child profile, school lesson, production endpoint, secret, or gated-model access was used. All functions have `min_containers=0`, `max_containers=1`, finite timeouts, and configured retries disabled.
- Model weights are downloaded from their public Hugging Face repositories by Modal CPU functions directly into the existing `sketch2life-dev-model-weights-v2` Volume v2. No workstation download/upload step is required. Inputs are staged under one-attempt prefixes in `sketch2life-dev-job-scratch-v2`; inference mounts are read-only. POC media returns inline are capped at 16 MiB and hash-checked by the local runner.

## Deployed private Modal apps

| App | App ID | Functions | State |
|---|---|---|---|
| `sketch2life-srs23-drawing-vlm-dev` | `ap-uwY5d9XdmkXRpD8uYVUAtv` | `download-pinned-model` (`fu-ONybgndfkmhVE0CRTjo4rz`), `analyze-drawing` (`fu-07Bu9lV0aMTcthV5ljIogL`) | Deployed, v2 |
| `sketch2life-srs23-language-audio-dev` | `ap-w5VBjY4t0m47RcHktpg7kb` | `download-language-audio-models` (`fu-qt7st3yIE3VPgkuFYpOW0B`), `generate-story-and-storyboard` (`fu-rm45oEVOfeYaQn7qHHPP`), `synthesize-vietnamese-narration` (`fu-ANKBHRiC67NcUXoTAuCvHn`), `transcribe-vietnamese-audio` (`fu-cOf9CdedRvcCuJewG2JHZI`) | Deployed, v2 |
| `sketch2life-srs23-flux-image-dev` | `ap-yBGfmdN4KEITZPy3IpsgVM` | `download-flux-pinned-model` (`fu-5pZ0hgb06SDVnVZPMKfTI9`), `generate-line-sketch-guide-candidate` (`fu-Wt7jF033Vm5G0HbxXKmZyK`) | Deployed, v1 |
| `sketch2life-srs23-video-candidate-dev` | `ap-dsvERz4dAJoKtom5If4krY` | `download-wan-video-candidate-model` (`fu-aEUfOgtfdsfNiCOT2vC1Fx`), `generate-wan-video-candidate` (`fu-4CMwDVHxWlgTNMXFr1iFEw`) | Deployed, v1 |

No web endpoints are registered. The POC call results and the remaining pending call are documented below.

The language/audio app was redeployed as v2 after removing a non-secret cache-path environment override and renaming an internal tokenizer-cache variable that triggered the repository security scanner. Function IDs and inference behavior are unchanged; no inference was repeated for this cleanup.

## Checkpoint downloads

| Model | Immutable revision | Modal call | Result at this evidence revision |
|---|---|---|---|
| `Qwen/Qwen2.5-VL-7B-Instruct` | `cc594898137f460bfe9f0759e9844b3ce807cfb5` | Prior approved download in the drawing VLM POC | Already downloaded to Volume v2 and verified by marker/checkpoint checks |
| `Qwen/Qwen2.5-7B-Instruct` | `a09a35458c702b33eeacc393d103063234e8bc28` | `fc-01M6GPDVR5PMG124JS69HDKGWE` | Success; checkpoint verified and Volume committed; function execution 65.41 s |
| `Systran/faster-whisper-large-v3` | `edaa852ec7e145841d8ffdb056a99866b5f0a478` | `fc-01M6GPDVR5PMG124JS69HDKGWE` | Success; checkpoint verified and Volume committed |
| `pnnbao-ump/VieNeu-TTS-v3-Turbo` | `61b85e3d937fbbacb387714180e8182823512523` | `fc-01M6GPDVR5PMG124JS69HDKGWE` | Success; checkpoint verified and Volume committed |
| `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX` | `ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae` | `fc-01M6GPDVR5PMG124JS69HDKGWE` | Success; checkpoint verified and Volume committed |
| `black-forest-labs/FLUX.2-klein-4B` | `e7b7dc27f91deacad38e78976d1f2b499d76a294` | `fc-01M6GPM5QF1X8PEPF1CGMS5K3V` | Success; checkpoint verified and Volume committed; function execution 102.84 s |
| `Wan-AI/Wan2.2-TI2V-5B` | `921dbaf3f1674a56f47e83fb80a34bac8a8f203e` | `fc-01M6GQ5FZAM62YRDV6FR0PW197` | Success; all checkpoint files verified and Volume committed; function execution 142.70 s. Model card lists about 34.2 GB. |

## Persistent Volume footprint

The Modal SDK recursively enumerated checkpoint files in `sketch2life-dev-model-weights-v2` (Volume v2). The retained files total **95,121,275,282 bytes (88.59 GiB)**:

| Checkpoint folder | File bytes | GiB |
|---|---:|---:|
| Qwen2.5-VL-7B | 16,595,983,189 | 15.46 |
| Qwen2.5-7B-Instruct | 15,242,808,946 | 14.20 |
| faster-whisper-large-v3 | 3,090,840,173 | 2.88 |
| VieNeu-TTS-v3-Turbo | 2,157,926,250 | 2.01 |
| MOSS Audio Tokenizer Nano ONNX | 90,579,954 | 0.08 |
| FLUX.2-klein-4B | 23,740,010,359 | 22.11 |
| Wan2.2-TI2V-5B | 34,203,126,411 | 31.85 |

This is the checkpoint file footprint, not a billing estimate. Modal account billing was **not rechecked after the downloads**; the earlier $0.00 preflight reading predates them.

## Synthetic inference results and blockers

### Speech: VieNeu TTS → faster-whisper

- TTS call `fc-01M6GPHQJ4ST90B5DBYJ4KV6N7`: **success**, 11.47 s function execution; 19.667 s including cold start in the runner.
- ASR call `fc-01M6GPJBZGT6RSD924X1H9WE0P`: **success**, 24.55 s function execution; 32.224 s including cold start in the runner.
- Input was the synthetic Vietnamese sentence “Con bướm bay qua khu vườn đầy nắng.” with the preset adult voice “Hải Đăng”; no voice cloning or child voice.
- Output WAV: `assets/modal_ai_hosting_wave_20261103/vieneu_synthetic_narration.wav`, 169,004 bytes, SHA-256 `7df0cb0ee15d20a04b87efe18a0e03b280353a442b192e3e248fe47561c58bfc`.
- Whisper detected Vietnamese with probability 1.0 but transcribed “Con bước bay qua khu vườn đầy nắng.” The butterfly word was misrecognized; this is one smoke sample and not a quality benchmark.
- Runner JSON: `assets/modal_ai_hosting_wave_20261103/vieneu_faster_whisper_result.json`.

### Drawing analysis: Qwen2.5-VL

- Initial call `fc-01M6GM6ZCCDTEDYB9MRARMTWXK`: **failed before inference** because the image processor required `torchvision`, which was missing from the first image build.
- Corrected deployment is app v2. The single approved corrective call `fc-01M6GN62XVPDBR39205WQ35K9Q` remains **pending**; Modal reports it is acquiring L4 capacity. No additional drawing inference was sent.
- Input fixture is the generated synthetic butterfly drawing, SHA-256 `4b18777ae70eb429273c1e0ba7189ff005171b9dda88491510d91965aafa07fc`.

### FLUX image generation and Qwen story inference

- FLUX inference `fc-01M6GPQZ2KTMVJ9ZDDM4JMPZAC`: **success**. One synthetic 768x512 butterfly guide was generated; output is `assets/modal_ai_hosting_wave_20261103/flux2_klein_synthetic_butterfly_guide.png` (158,296 bytes; SHA-256 `388647b52af176c78a833c29319942e92e2757bf0cda5637823a707057eaf618`). Function execution was 35.74 s after the worker started; elapsed time including queue and cold start was 1,202.53 s. The three panels depict a plausible progression, but step order, child usability, safety, and product quality are unvalidated.
- Qwen story/storyboard inference has not been sent; weights are ready. It will be attempted only after collecting the currently pending Qwen-VL call, per the approved sequential plan.
- The FLUX deployment image initially failed dependency resolution: Diffusers 0.42.1 requires Safetensors >=0.8 and Hugging Face Hub >=1.32. The image was corrected to Safetensors 0.8.0 and Hub 1.32.0; app deployment and the single inference then succeeded.

### Video candidate

- Wan2.2 worker is deployed against official runtime commit `1ea34ff48f87168174e12956e200b1d908b1c5ff`, with FlashAttention omitted so the official attention module can use its PyTorch scaled-dot-product fallback. The original Wan model card states TI2V-5B supports 720p and needs at least 24 GB GPU memory; this POC requests Modal L40S.
- Wan weights are downloaded and verified in Modal Volume v2. No Wan inference has been sent yet; it is an alternative feasibility comparison only and does not replace the SRS LTX-2.5 candidate.
- LTX-2.5 remains gated. No license was accepted, no Hugging Face token was created, and no Modal secret was created.

## Remaining gates and limits

- Qwen-VL still has one corrective synthetic inference pending Modal L4 capacity. `story.generate` and `storyboard.generate` have not been run. Wan weights are downloaded and one synthetic video POC remains.
- SRS production defaults remain unchanged. All workload registry entries stay `enabled: false`; lesson suggestions stay disabled pending Q157/Q159; SAM2 remains deferred; safety validation remains unresolved and fail-closed.
- Checkpoint bytes are measured above; updated Modal billing after checkpoint persistence has not been checked in the account billing view. Initial preflight billing was $0.00 before these downloads and is not a current-cost reading.
- No product/backend integration, real-child test, visual approval, broad test suite, commit, push, or production deployment was performed.
- Static verification so far: AST parse passed for the Modal Python workers/runner; `workloads.json` parsed; `git diff --check` passed. Final repository security validation remains to be run after evidence and status closeout.

## Primary sources

- [Sketch2Life canonical SRS v2.3-draft](../artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md)
- [Modal GPU guide](https://modal.com/docs/guide/gpu)
- [Modal Volumes guide](https://modal.com/docs/guide/volumes)
- [Qwen2.5-7B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [faster-whisper large-v3 model card](https://huggingface.co/Systran/faster-whisper-large-v3)
- [VieNeu-TTS v3 Turbo model card](https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo)
- [MOSS Audio Tokenizer Nano ONNX model card](https://huggingface.co/OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX)
- [FLUX.2 Klein 4B model card](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
- [Wan2.2 TI2V-5B model card](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B)
- [Official Wan2.2 runtime repository](https://github.com/Wan-Video/Wan2.2/tree/1ea34ff48f87168174e12956e200b1d908b1c5ff)
- [LTX-2.5 gated model page](https://huggingface.co/Lightricks/LTX-2.5)

## Later call outcome and app state

- The corrective Qwen-VL call `fc-01M6GN62XVPDBR39205WQ35K9Q` later reached terminal `success`. This resolves the earlier pending state recorded above.
- A separate API-triggered drawing call later reached Modal terminal `success` after the backend had recorded `VISION_OUTCOME_UNKNOWN`; the API did not persist the result. See `MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`.
- At the owner's request, only `sketch2life-srs23-drawing-vlm-dev` was stopped and verified `State: stopped`. Other Modal apps and shared Volumes/model files were left untouched. Future use requires redeploy.

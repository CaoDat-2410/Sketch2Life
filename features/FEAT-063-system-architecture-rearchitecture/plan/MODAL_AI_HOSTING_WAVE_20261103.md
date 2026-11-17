# Modal AI hosting wave — 2026-11-03

## Status and authority

- Status: `APPROVED` for the exact development-only model hosting and synthetic proof-of-execution scope below.
- Feature: FEAT-063; source of truth is `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft. This plan does not edit or promote the draft SRS model candidates.
- Owner authorization: direct chat instruction on 2026-11-03: Modal environment is ready; continue the next work and host whichever AI the system needs.
- Purpose: move beyond the first drawing VLM POC and stand up bounded Modal `dev` workers for the SRS story, speech, image/line-art, and video capabilities. All outputs are synthetic evaluation artifacts, not product content.

## Workload decisions for this wave

| SRS workload | Dev candidate pinned for this POC | Modal profile | Scope/limitation |
|---|---|---|---|
| `story.generate`, `storyboard.generate` | `Qwen/Qwen2.5-7B-Instruct`, revision `a09a35458c702b33eeacc393d103063234e8bc28`, Apache-2.0 | L4 | One generic Vietnamese butterfly request; bounded structured output. Does not enable lesson suggestions. |
| `asr.transcribe` | `Systran/faster-whisper-large-v3`, revision `edaa852ec7e145841d8ffdb056a99866b5f0a478`, MIT | CPU first | Transcribe only a synthetic adult-voice clip produced in this task. |
| `tts.narration.generate` | `pnnbao-ump/VieNeu-TTS-v3-Turbo`, revision `61b85e3d937fbbacb387714180e8182823512523`, Apache-2.0; codec `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX`, revision `ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae`, Apache-2.0 | CPU/ONNX first | Preset adult voice only; no voice cloning or child voice. One short synthetic Vietnamese sentence. |
| `parent.sketch-guide.generate`, `teacher.sketch-deck.generate`, `lesson.visual.generate` | `black-forest-labs/FLUX.2-klein-4B`, revision `e7b7dc27f91deacad38e78976d1f2b499d76a294`, Apache-2.0 | L4 | One generic line-art/step-guide and lesson-visual candidate evaluation. Does not enable either sketch workflow or establish ordered-step quality. |
| `video.scene.generate` alternative benchmark only | `Wan-AI/Wan2.2-TI2V-5B`, revision `921dbaf3f1674a56f47e83fb80a34bac8a8f203e`, Apache-2.0 | L40S | One short synthetic image-to-video candidate call to compare host feasibility. It does not replace the SRS LTX-2.5 candidate. |

`Qwen/Qwen2.5-VL-7B-Instruct` remains the separate approved drawing analysis POC. `lesson.plan.suggest` stays disabled because SRS Q157/Q159 have unresolved requesting-role scope. `drawing.segment`/SAM2 remains optional and deferred. Scene/final safety remain fail-closed with no selected or calibrated model.

LTX-2.5 remains the SRS video candidate. The current Hugging Face repository is gated and the Modal `dev` environment has no Hugging Face secret. Do not accept its license or create/use a credential on behalf of the owner. Record the exact access gate; the Wan call is a non-production alternative benchmark only.

## Exact approved implementation and operational scope

1. Add separate private Modal `dev` app(s) for the text, ASR/TTS, FLUX image, and Wan video candidate workers. Functions use versioned request manifests staged in the existing Volume v2 scratch area, bounded to the existing 48 MiB contract; payloads contain opaque IDs, hashes, and relative refs only.
2. Reuse the existing `sketch2life-dev-model-weights-v2` Volume v2 for pinned model subdirectories and `sketch2life-dev-job-scratch-v2` for one attempt at a time. Download functions write; inference functions mount weights and inputs read-only. To keep input mounts read-only without adding output infrastructure, synthetic POC media outputs may return inline to the local runner, capped at 16 MiB and verified by SHA-256 before saving under feature evidence. Text outputs remain bounded JSON. Do not create a public/web endpoint, `min_containers`, automatic retries, or persistent GPU.
3. Pin every model and codec to the immutable revisions above. For each runnable model, download and verify the expected checkpoint marker, deploy, and make at most one bounded synthetic inference call. No automatic/manual retry is authorized by this plan. If an inference fails, preserve evidence and stop that model call.
4. Build the speech POC as VieNeu preset-voice synthesis -> faster-whisper transcription. Use only synthetic text/audio generated during this task. Build the Qwen POC around a generic topic and structured story/storyboard output. Build the FLUX POC around a generic butterfly lesson/line-art prompt. Build the Wan POC from the synthetic butterfly drawing with a short output duration.
5. Keep every registry entry `enabled: false` and mark each as POC/development-only until quality, safety, latency, cost, dependency/license, and product-owner gates are separately reviewed. Do not edit the SRS or select a production provider/model.
6. Record source links and revisions, app/function IDs, call IDs, exact command, synthetic input provenance/hashes, output hashes/metadata, timing, observed Modal billing, scale-to-zero state, and failures in feature-local evidence. Update context/decisions/source registers/status additively.

## Explicit exclusions

- Real child data, child images/voices/profile data, real school lessons, Firebase/MinIO/S3 credentials, production endpoints, public URLs, or cross-border production data.
- LTX-2.5 gated-model download, license acceptance, HF token creation, or Modal secret creation. Do not replace the SRS LTX choice; record the access requirement and candidate alternative evidence.
- Safety certification or playback approval, calibrated vision confidence, model fine-tuning, continuous/always-on containers, product/API/queue/storage integration, lesson-plan suggestions, SAM2 deployment, changes to API/SRS/ADR/schema/Docker, commit, push, or merge.
- Broad test suites. Only syntax/security checks and the single explicitly scoped Modal synthetic POC call per runnable model are in scope.

## Acceptance criteria

- AC1. A separate private dev worker is deployed for each approved runnable model family; all functions have bounded resources, finite timeouts, scale to zero, and retries disabled.
- AC2. All request media/text are staged under an exact attempt prefix and verified by manifest hash/size/type; function args contain no raw media, remote URL, token, profile, or child data. Inline POC media responses are capped at 16 MiB and checked against their reported hash before evidence is written.
- AC3. Qwen emits a parseable story/storyboard structure for the synthetic generic-topic request, or a safe recorded failure.
- AC4. VieNeu emits a bounded valid audio file from one synthetic text sentence and faster-whisper returns a transcript from that generated audio, or a safe recorded failure.
- AC5. FLUX produces one synthetic candidate image, or a safe recorded failure; its visual output is retained as experimental evidence and does not become an approved product asset.
- AC6. Wan produces one short synthetic image-to-video candidate, or a safe recorded failure; it remains an alternative benchmark, not an SRS model change.
- AC7. No lesson suggestion, SAM2, LTX-2.5 gated access, safety verdict, production readiness, or product workflow enablement is claimed.
- AC8. Evidence and additive FEAT-063 records are complete; the repository security validator passes.

## Risks and stop rules

- Persistent model weights consume Volume storage while retained; record sizes and observed cost. Do not delete existing weights or Volumes.
- L4/L40S capacity, cold starts, download time, model VRAM, and Modal billing can vary. Use only the profiles in this plan; do not silently switch GPU or invoke another inference after failure.
- FLUX may produce plausible but unordered or inaccurate drawing steps. A single image is feasibility evidence only; ordered-step quality remains unverified.
- Wan2.2 does not demonstrate LTX2.5 behavior, scene consistency across multi-scene stories, Vietnamese narration, final safety, or required end-to-end video latency.
- VieNeu model-card commercial terms do not substitute for project legal review. Do not use outputs with real users in this POC.

## Verification sequence

1. Confirm the plan hash and matching approval record.
2. Inspect current Modal `dev` apps, Volumes, Secrets, and billing before creating apps or downloading weights.
3. Confirm pinned HF metadata/revisions and source/license pages; deploy private apps only.
4. Download model weights to the existing versioned Volume and verify model markers.
5. Run at most one synthetic POC per model, sequentially; collect each result before proceeding to the next GPU-backed model.
6. Verify zero active tasks, no web endpoint, unchanged Secret inventory, and task-scoped scratch cleanup.
7. Run syntax checks and `python tools/validate_repository_security.py`; complete evidence and status records.

## Sources

- Canonical SRS v2.3-draft: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §§6.2–6.3, 24.3–27, 29, 31.
- Qwen2.5-7B-Instruct: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- faster-whisper large-v3: https://huggingface.co/Systran/faster-whisper-large-v3 and https://github.com/SYSTRAN/faster-whisper
- VieNeu-TTS v3 Turbo: https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo and https://github.com/pnnbao97/VieNeu-TTS
- VieNeu codec: https://huggingface.co/OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX
- FLUX.2 Klein 4B: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- Wan2.2 TI2V-5B: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B and https://github.com/Wan-Video/Wan2.2
- LTX-2.5 gated repository/license: https://huggingface.co/Lightricks/LTX-2.5
- Modal GPUs/Volumes/secrets: https://modal.com/docs/guide/gpu and https://modal.com/docs/guide/volumes

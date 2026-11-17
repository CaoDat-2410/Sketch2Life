# FEAT-020 Input Bootstrap Addendum

**Status:** `AWAITING_APPROVAL`
**Date:** 2026-09-12
**Purpose:** add automatic real input generation to the backend-only Lightning workflow.

## 1. New requirement

When the operator does not provide an image, the demo must generate exactly one runtime image. When the run is configured for multimodal input and no audio is provided, it must generate a narration script and synthesize one real WAV through a concrete Google audio/TTS provider.

The generated image and WAV are real runtime inputs. They are not fixtures, checked-in assets, fake audio, or pre-recorded workflow results. They go through the same validation, VLM, ASR, fusion, and provenance path as caller-supplied files.

## 2. Proposed command contract

```bash
python -m sketch2life.workflow_demo \
  --generate-inputs \
  --input-prompt "A child drawing of a butterfly and a flower" \
  --google-tts \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

Equivalent explicit-input mode remains supported:

```bash
python -m sketch2life.workflow_demo \
  --image ./runtime-input/sample.jpg \
  --narration-audio ./runtime-input/narration.wav \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

The final implementation may rename flags after the repository CLI convention is checked, but it must preserve the semantics:

- `--image` omitted + `--generate-inputs`: generate one image;
- multimodal mode + audio omitted: generate one narration WAV;
- no silent fallback to repository fixtures;
- generated files are ignored local/Lightning artifacts;
- generated source checksum, provider, model, voice, locale, seed/request ID, and status are recorded in the sanitized manifest.

## 3. Input-bootstrap sequence

1. Resolve a declared scenario prompt and seed. The default must describe an observable child-style drawing, not a real child or real personal data.
2. Call the approved image-generation adapter and write one PNG/JPEG to the runtime directory.
3. Validate MIME, dimensions, decodability, safety, and checksum.
4. Derive a short narration script from the same scenario or accept an explicit script supplied by the operator.
5. Call the approved Google audio/TTS adapter and write one WAV.
6. Validate WAV container, sample rate, duration, and decodability.
7. Pass both artifacts into the normal image/VLM/ASR workflow.

Failures are typed as `INPUT_GENERATION_FAILED` or `AUDIO_SYNTHESIS_FAILED`; they cannot be reported as a successful workflow.

## 4. Google audio decision that must be confirmed

“Google audio” is not specific enough to lock an implementation contract. Before implementation, select one concrete service:

- Google AI Studio/Gemini text-to-speech; or
- Google Cloud Text-to-Speech.

The selected service must define model, voice, language/locale, API/SDK, authentication through Lightning Secrets, retry/timeout policy, output encoding, and WAV conversion. No key, service-account file, or token may be committed.

## 5. Image-generation decision that must be confirmed

The plan also needs the image-generation provider/model. It may be a local GPU model loaded in Lightning or an approved remote image API accessed from the backend. The selected option must define model revision, prompt policy, seed behavior, output format, safety validation, VRAM/network needs, and provenance fields.

## 6. Acceptance additions

The one real-AI E2E test must be able to run with no checked-in input media:

- generate one image at runtime;
- generate one WAV through the selected Google provider when multimodal mode is enabled;
- assert both generated artifacts are validated and hashed;
- assert ASR is real when WAV generation is enabled;
- assert no fixture ID, fake adapter, or pre-recorded result was used;
- include provider/model/voice provenance in the sanitized manifest;
- keep generated media outside Git and outside feature evidence unless a sanitized metadata-only record is captured.

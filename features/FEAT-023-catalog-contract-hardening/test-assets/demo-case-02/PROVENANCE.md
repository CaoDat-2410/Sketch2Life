# Demo case 02 asset provenance

**Generated:** 2026-09-14
**Purpose:** replaceable backend integration-test input only
**Real child data:** none

## `input-image-framing-safe.png`

- Content: synthetic child-style drawing of a red bicycle, a yellow helmet,
  a simple road, blue sky and a green tree.
- Generator: Codex native image generator (`image_gen` built-in mode).
- Dimensions: 1536 x 1024 pixels.
- File size: 1,407,453 bytes.
- SHA-256: `3c771b183513374cd5d1ef3909940e9d6d0ae0d2d9f82013aca7df821f164b80`.
- No text, logo, watermark, or real-person/real-child content.

## `narration.wav`

- Text: `Chiếc xe đạp màu đỏ đứng bên đường. Chúng mình đội mũ bảo hiểm trước khi đi nhé.`
- Language: Vietnamese (`vi`).
- Generator: `gTTS` 2.5.4 using Vietnamese TTS, generated once; not generated
  during workflow execution.
- Post-processing: converted to mono PCM WAV, 16 kHz, 16-bit with the local
  `imageio-ffmpeg` binary.
- Channels: 1.
- Sample rate: 16,000 Hz.
- Duration: approximately 5.62 seconds.
- File size: 179,790 bytes.
- SHA-256: `8a6d77b5c713950f45633bf256b17bc421acad90f214e395d2d6af927d551400`.
- No API key, token, or service-account content is stored here.

These files are inputs only. The workflow must still call the real VLM and
ASR adapters; it must not read precomputed model outputs from this directory.

## Retained rejected candidate

The first generated image is retained as `input-image.png` solely for
provenance/audit. It is not referenced by the demo manifest or command because
the deterministic validator returned `IMAGE_FRAMING_RISK` (`border_ink_ratio`
`0.58579` > policy maximum `0.55`). The final workflow input is
`input-image-framing-safe.png`, which returned `PASS` with `border_ink_ratio`
`0.0`.

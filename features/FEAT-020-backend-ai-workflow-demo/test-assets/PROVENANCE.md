# FEAT-020 Test Asset Provenance

**Generated:** 2026-09-12
**Purpose:** replaceable backend integration-test input only
**Real child data:** none

## `input-image.png`

- Content: synthetic child-style drawing of a blue/orange butterfly, red flower, grass, and sun.
- Generator: Codex native image generator.
- Dimensions: 1448 × 1086 pixels.
- File size: 2,452,002 bytes.
- SHA-256: `87772c53c89cc0d44aad810d865c25b08a1bc888965ef49bf5393a989af78d63`.
- Original source is preserved as the immutable input; workflow derivatives must use separate artifact IDs.

## `narration.wav`

- Text: `Con bướm xanh đang bay gần bông hoa đỏ.`
- Language: Vietnamese (`vi`).
- Generator: `gTTS` 2.5.4 using Vietnamese TTS, generated once; not generated during workflow execution.
- Post-processing: converted to mono PCM WAV, 16 kHz, 16-bit using `imageio-ffmpeg`.
- Channels: 1.
- Duration: approximately 3.10 seconds.
- File size: 99,150 bytes.
- SHA-256: `f9b3ae77bdfe12d80a3e98a705172bc9714846c6fe5b29bb574ba18fdb0ab9e1`.
- No API key, token, or service-account content is stored here.

These files are inputs only. The workflow must still call the real VLM and ASR adapters; it must not read precomputed model outputs from this directory.

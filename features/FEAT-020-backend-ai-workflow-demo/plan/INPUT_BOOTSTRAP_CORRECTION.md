# FEAT-020 — Correction: Pre-generated Replaceable Test Inputs

**Date:** 2026-09-12
**Status:** `AWAITING_APPROVAL`

## Correct interpretation

The image and WAV are not generated at every workflow run. They are pre-generated test inputs stored outside the application logic. The backend command receives their paths, validates them, and runs the normal real-AI workflow. Replacing either file must not require a code change.

This is different from fixture-backed model output:

- allowed: one replaceable real image and one replaceable real WAV used as test input;
- forbidden: fixture VLM/ASR results, fake adapters, pre-recorded generated video, or hard-coded stage outputs.

## Recommended test-input layout

```text
features/FEAT-020-backend-ai-workflow-demo/test-assets/
├── input-image.png
├── narration.wav
└── PROVENANCE.md
```

The files must be synthetic and contain no real child data. Large/binary files should remain ignored or stored in the local Lightning runtime directory if repository policy disallows binary test assets. The test command must support replacement through paths/environment variables:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

## Audio requirement

The WAV should be synthesized once using the selected Google audio/TTS service, then treated as a replaceable input file. The workflow does not call Google TTS during each test run. The provenance record must contain provider, model, voice, locale, generation date, and checksum, but no API key or service-account content.

## Image requirement

The supplied generated image is a synthetic child-style drawing of a blue/orange butterfly, a red flower, grass, and a sun. It is suitable as the initial test input. It may be replaced with another JPEG/PNG without changing the workflow code.

## Acceptance change

The E2E test must assert that the image and WAV are caller-supplied paths, validated, hashed, and passed to real VLM/ASR adapters. It must not require an input-generation service at runtime. If a future feature wants automatic input generation, that must be a separate optional bootstrap command and must not alter this core workflow contract.

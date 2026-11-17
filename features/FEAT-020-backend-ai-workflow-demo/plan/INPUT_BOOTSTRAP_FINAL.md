# FEAT-020 Finalized Test Input Decisions

**Date:** 2026-09-12
**Status:** `CONFIRMED_FOR_PLAN`

The owner confirmed the following interpretation:

1. Use the generated synthetic image as the default input test asset.
2. Use Vietnamese narration, targeted at Vietnamese children.
3. Use both image and WAV in the single E2E run so VLM, ASR, and fusion are exercised.
4. Commit the synthetic test assets into the repository.
5. Pull the full repository into Lightning Studio and run the backend command using replaceable asset paths.

The assets are pre-generated once. The workflow does not generate them at runtime and must not depend on their filenames internally. Replacement is supported through CLI paths or environment variables.

Default asset paths:

- `features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png`
- `features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav`

Default command:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

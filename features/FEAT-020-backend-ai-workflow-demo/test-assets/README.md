# FEAT-020 Replaceable Test Inputs

These are synthetic, pre-generated input assets for the backend E2E workflow. They are not model-output fixtures.

- `input-image.png`: synthetic child-style drawing generated for this test.
- `narration.wav`: Vietnamese narration generated once for this test.

The E2E command must accept replacement paths, so replacing either file must not require code changes:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

Do not replace these with real child media. Any replacement must be synthetic or have explicit project approval and must remain outside runtime evidence if it contains sensitive data.

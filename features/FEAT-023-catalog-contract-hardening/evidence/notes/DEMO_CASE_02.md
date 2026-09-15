# Demo case 02 evidence

## Scope

Case 02 adds a second pre-generated image/audio pair to the backend-only
workflow demo. It is deliberately different from the baseline butterfly/flower
pair so a Lightning run can exercise a distinct concept family and reveal
whether the semantic matcher is actually using the fused input.

The pair is synthetic and contains no real child data. The image and WAV are
inputs, not fixtures for ASR/VLM/recommendation output. Runtime output must be
written under the ignored `runtime-output/` directory and must retain source
artifact references and hashes.

## Expected run

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-023-catalog-contract-hardening/test-assets/demo-case-02/input-image-framing-safe.png \
  --narration-audio ./features/FEAT-023-catalog-contract-hardening/test-assets/demo-case-02/narration.wav \
  --age-mode all \
  --demo-autopilot \
  --emit-debug-evidence \
  --output ./runtime-output/workflow-result-demo-case-02.json
```

When the real model runtime is configured, this should execute:

`MEDIA_VALIDATION -> ASR -> VLM -> FUSION -> SEMANTIC_NORMALIZATION -> AGE_ADAPTATION -> ACTIVITY_SELECTION -> STORY/ACTIVITY_HANDOFF -> FEEDBACK_READY`

The actual terminal status depends on the Lightning model runtime. This
repository evidence does not claim a Lightning success before that command is
run on the target Studio.

## Asset verification recorded before the run

| Asset | Verification |
| --- | --- |
| `input-image-framing-safe.png` | PASS; PNG 1536 x 1024, 1,407,453 bytes, border ink ratio 0.0, SHA-256 `3c771b183513374cd5d1ef3909940e9d6d0ae0d2d9f82013aca7df821f164b80` |
| `narration.wav` | PASS; mono PCM 16 kHz/16-bit, 5.62 seconds, 179,790 bytes, speech activity 0.807, SHA-256 `8a6d77b5c713950f45633bf256b17bc421acad90f214e395d2d6af927d551400` |

See `test-assets/demo-case-02/PROVENANCE.md` for generation details.

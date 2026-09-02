# Phase 14 - Lightning AI preflight

Run the preflight before a real generation. It checks the provider, Python
runtime, Wan2.2 script, checkpoint directory, FFmpeg, FFprobe, and CUDA.

```bash
python features/FEAT-005-backend-experience/scripts/preflight_lightning.py \
  --config features/FEAT-005-backend-experience/config/lightning.example.yaml
```

`PREFLIGHT_OK` means the environment is ready for one real smoke generation.
`PREFLIGHT_FAILED` lists what must be fixed first. The script does not download
weights, start the model, or create video files.

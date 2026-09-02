# Phase 13 - Configured generation smoke test

`scripts/run_configured_generation.py` is the smallest executable check between
configuration and model generation. It loads one YAML profile, validates the
generation brief, selects the provider, and runs exactly one generation.

## Local mock check

```bash
python features/FEAT-005-backend-experience/scripts/run_configured_generation.py \
  --config features/FEAT-005-backend-experience/config/test.yaml
```

The mock provider only returns deterministic metadata; it does not use a GPU or
create a real MP4.

## Lightning real check

After updating the paths in `config/lightning.example.yaml` and preparing the
Wan2.2 checkpoint, run the same command with that profile. A successful real
check must print an output path whose MP4 file exists. FFmpeg duration and frame
sampling are checked in the next step.

# Phase 10 - Config loader

## Responsibility

The config loader reads a named YAML profile and validates it into typed settings. Runtime code should read model paths, video bounds, dimensions, FPS, and retry limits from these settings instead of hardcoding them.

## Profiles

- `default.yaml`: baseline profile.
- `test.yaml`: lightweight mock/local profile.
- `lightning.example.yaml`: template for a Lightning AI Studio; it contains no credentials.

## Flow

```text
YAML profile
  -> yaml.safe_load
  -> AppSettings.model_validate
  -> WanSettings / VideoSettings / RuntimeSettings
```

Unknown fields and invalid duration ranges are rejected. The loader does not create directories, download models, or contact external services.

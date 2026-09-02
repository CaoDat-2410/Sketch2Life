# Phase 12 - Provider configuration

The YAML profile now selects the generation provider:

```yaml
wan:
  provider: mock   # or wan2.2
```

`create_generation_provider(settings)` converts validated `AppSettings` into
either `MockGenerator` or `Wan2Generator`. The pipeline keeps receiving the
same `GenerationProvider` interface, so changing from mock to Wan2.2 does not
change pipeline orchestration.

## Test order

1. Load `config/test.yaml` and run the mock path locally.
2. Load `config/lightning.example.yaml` on Lightning AI after paths and model
   checkpoints are prepared.
3. Run one real Wan2.2 generation before enabling the full validator loop.

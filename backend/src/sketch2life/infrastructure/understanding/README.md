# Understanding adapters

This package is the infrastructure edge for Person 2's standalone understanding workstream.

- `fixture_adapters.py` is the CI/local deterministic implementation.
- `whisper_adapter.py` maps an injected Whisper-shaped engine result into `AsrResultV1`.
- `qwen3_vl_adapter.py` maps an injected structured-output client into `VisionUnderstandingResultV1`.
- FEAT-017's live Lightning HTTP adapters live in `infrastructure/ai` so provider transport stays outside the provider-neutral contracts.

Provider output is validated at the boundary, and source references are preserved on both success and typed failure. P2 fusion and production provider rollout remain separate concerns.

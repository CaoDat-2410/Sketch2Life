# Understanding adapters

This package is the infrastructure edge for Person 2's standalone understanding
workstream.

- `fixture_adapters.py` is the CI/local deterministic implementation.
- `whisper_adapter.py` maps an injected Whisper-shaped engine result into
  `AsrResultV1`; a future `faster-whisper` integration belongs behind
  `WhisperEngine`.
- `qwen3_vl_adapter.py` maps an injected structured-output client into
  `VisionUnderstandingResultV1`; a future Lightning/Runpod client belongs
  behind `VisionModelClient`.

No adapter resolves storage, calls a provider, reads credentials, or writes
media. Provider output is validated at this boundary, and source references are
preserved on both success and typed failure. P2-T4 fusion and P2-T5 evaluation
are intentionally not included.

# Understanding service boundary

ASR/VLM/fusion adapters and use cases. Provider outputs must become versioned contracts before entering domain logic.

P2-T1 currently supplies a standalone deterministic image/audio validator in the backend package. It reads fixture PNG/WAV sources only, preserves their hashes, and returns `MediaValidationResultV1` with stable recapture reasons. It has no model, HTTP, queue, database, or mobile dependency.

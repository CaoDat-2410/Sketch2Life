# Evidence index

Evidence for FEAT-005 stays inside this feature folder and must be reproducible.

Planned evidence:

- contract/schema test output;
- cache `HIT`/`MISS` traces, including proof that `HIT` does not invoke generation;
- FFmpeg media-integrity and 0/25/50/75/100% frame-sampling output;
- Qwen3-VL validation results with typed reason codes;
- retry and still+narration fallback outputs;
- provenance records;
- Lightning AI benchmark metrics: profile, duration, latency, peak VRAM, OOM, retry, and fallback rate.

Evidence is not complete until the command, environment, input fixture, output, timestamp, and interpretation are recorded.

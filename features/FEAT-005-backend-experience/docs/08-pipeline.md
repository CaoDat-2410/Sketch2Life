# Phase 8 - Standalone pipeline

## Responsibility

`LearningVideoPipeline` orchestrates the isolated Person 4 components. It owns control flow, not provider-specific inference or media decoding.

## Runtime flow

```text
objective
  -> cache-first resolver
      -> CACHE_HIT: return reviewed asset
      -> MISS
          -> generator
          -> FFmpeg frame sampling
          -> Qwen3-VL content validation
              -> PASS: return generated video
              -> RETRY: generate once more
              -> FALLBACK: return reviewed still+narration
              -> BLOCK: stop without fallback
```

Unsafe or age-inappropriate content is `BLOCK` and is not silently replaced. Media failure or non-grounded content can use retry/fallback according to the typed reason code.

The pipeline accepts provider, sampler, validator, and fallback dependencies. Tests use deterministic fakes; real Wan2.2, FFmpeg, and Qwen3-VL adapters can be added later without changing orchestration policy.

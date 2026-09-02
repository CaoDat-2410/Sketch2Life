# Phase 6 - Qwen3-VL content validator

## Responsibility

This phase inspects the five frames produced by FFmpeg against one bounded learning objective and generation brief. It is separate from FFmpeg: FFmpeg checks whether media can be decoded, while Qwen3-VL checks educational content and safety.

## Flow

```text
FrameSamplingResult(PASS)
  + GenerationBrief
  -> Qwen3-VL inspection
  -> PASS / RETRY / FALLBACK / BLOCK
```

## Decision policy

- Prohibited content or age-inappropriate content: `BLOCK`.
- Visual corruption: `FALLBACK`.
- Objective not grounded in the frames: `RETRY`.
- Objective grounded and safe: `PASS`.
- Failed frame sampling: `FALLBACK` without calling the content model.

`MockQwen3VLValidator` makes the policy testable without model weights or GPU. A real Qwen3-VL adapter can later implement the same `VisualContentModel` protocol.

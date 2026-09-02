# Phase 5 - FFmpeg frame sampling

## Responsibility

`FrameSampler` owns media integrity checks and representative frame extraction. It does not judge whether the learning concept is visible; that is the responsibility of the later Qwen3-VL content validator.

## Flow

```text
generated.mp4
  -> ffprobe duration check
  -> duration policy check (5-10 seconds)
  -> ffmpeg frames at 0/25/50/75/100%
  -> FrameSamplingResult
```

## Outcomes

- `PASS`: video is readable and all five frames were extracted.
- `BLOCK`: file is missing, undecodable, outside the duration policy, or a frame cannot be extracted.

The content validator may later convert a readable sampling result into `PASS`, `RETRY`, `FALLBACK`, or `BLOCK` after inspecting the frames.

## Verification

The unit test uses `unittest.mock` to emulate `ffprobe` and `ffmpeg`, so it does not require a real video or system binaries. The integration test and `generate_video_fixtures.py` use real FFmpeg when it is available, such as on the Lightning AI environment.

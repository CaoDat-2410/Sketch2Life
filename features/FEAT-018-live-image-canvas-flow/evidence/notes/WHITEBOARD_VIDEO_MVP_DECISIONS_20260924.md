# Whiteboard MP4 MVP decisions

Date: 2026-09-24  
Feature: `FEAT-018-live-image-canvas-flow`  
Status: `MVP_BASELINE_PROPOSED_FOR_IMPLEMENTATION`

This note resolves the implementation-level TBDs for the first whiteboard MP4
slice. It does not approve production worker placement, durable storage,
provider budget, or a specific cloud vendor.

## 1. MP4 profile

| Item | MVP decision |
|---|---|
| Container | MP4 |
| Video codec | H.264/AVC, High profile, level 4.1 |
| Encoder | FFmpeg with `h264_nvenc` when the approved GPU capability is available; `libx264` deterministic fallback for local/CI execution |
| Resolution | 1280x720 landscape |
| Frame rate | Constant 30 fps |
| Pixel format | `yuv420p` for Android compatibility |
| Video bitrate | Target 4 Mbps, maximum 6 Mbps |
| Audio codec | AAC-LC, 48 kHz, stereo, target 128 kbps |
| Duration | Target 8 seconds; permitted range 5–10 seconds |
| Maximum artifact size | 12 MiB |

The source drawing remains immutable. The MP4 is a derived, session-local
artifact and must retain the source SHA-256 in its provenance.

## 2. Job and stage timeouts

| Stage | Timeout |
|---|---:|
| Localization | 20 seconds |
| Segmentation | 45 seconds |
| Mask validation | 10 seconds |
| Stroke extraction | 20 seconds |
| Deterministic rendering | 20 seconds |
| TTS | 20 seconds |
| MP4 encoding | 45 seconds |
| Final safety/provenance validation | 10 seconds |
| Whole job deadline | 180 seconds |

The whole-job deadline wins over individual stage budgets. A timeout is typed
as retryable only when the stage is listed as retryable below.

## 3. Retry policy

- Maximum attempts: 3 total (initial attempt plus 2 retries).
- Backoff: 2 seconds before retry 1, 8 seconds before retry 2.
- Every retry receives a new attempt record and a new idempotency key while
  retaining immutable source/spec/thread references.
- Retryable failures: provider timeout, temporary segmentation failure,
  temporary encoder failure, and TTS timeout.
- Non-retryable failures: source hash mismatch, missing or mismatched
  `ExperienceSpec`, expired consent, invalid/unsafe mask, invalid strokes,
  provenance mismatch, and content-safety failure.
- After retries are exhausted: expose `RETRYABLE_FAILURE` with a bounded
  `Try again` action and `Back` action. Continue remains locked; no fallback
  success or fake MP4 is emitted.
- Client retries are explicit only. No infinite automatic retry loop.

## 4. TTS policy

- TTS is a separate server-side artifact generated from the approved
  `learning_thread`, never from the child's raw narration track.
- Locale baseline: `vi-VN`.
- Voice baseline: a configured child-safe neutral Vietnamese neural voice;
  the concrete provider/voice identifier is environment configuration, not a
  contract field.
- The implementation must use a provider adapter so tests can use a
  deterministic fake TTS implementation without credentials.
- TTS may not receive raw provider tokens or mobile credentials.
- TTS output must pass duration, format, provenance, and safety validation
  before the job can become `READY`.

## 5. Mask and stroke quality gates

### Localization and mask

- VLM region confidence must be at least `0.75`.
- The region must be finite, in bounds, and have non-zero area.
- Accepted foreground mask coverage: `1%` to `85%` of the source image.
- Reject empty, full-frame, disconnected-corrupt, stale-hash, or
  source-mismatched masks.
- Mask and source must carry the same source SHA-256.

### Stroke extraction

- At least one valid stroke path is required.
- Every path must contain at least two finite points and remain within the
  source bounds after normalization.
- Total extracted path length must be at least `1%` of the source diagonal.
- Reject NaN/infinite coordinates, empty paths, out-of-bounds paths, and
  paths whose provenance does not match the accepted mask.

These are conservative MVP gates and must be represented as versioned config,
not scattered constants. They can be calibrated later using reviewed fixtures.

## 6. Playback and handoff policy

The parent must watch the full whiteboard video before the activity handoff.
The activity transition is enabled only after the player emits a completed
playback event. Seek controls remain available, but seeking does not itself
count as completion; the player must reach the end position after `READY`.

## 7. Explicitly deferred decisions

The following remain outside this MVP baseline:

- Production GPU worker placement and scheduling.
- Durable artifact retention and deletion policy.
- Production TTS vendor contract and cost budget.
- Automatic quality-threshold calibration from a labeled dataset.
- Multi-language voice selection.

Those decisions must not block local contract, fake-pipeline, API, and UI-gate
implementation.

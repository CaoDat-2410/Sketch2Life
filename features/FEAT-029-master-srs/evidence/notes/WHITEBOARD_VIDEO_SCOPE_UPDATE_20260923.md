# Master SRS scope update — PixiJS exploration and whiteboard video

Date: 2026-09-23
Feature: `FEAT-029-master-srs`
Source: owner clarification in the current conversation and the owner-provided whiteboard
architecture proposal.
Related feature plan: `features/FEAT-018-live-image-canvas-flow/plan/PERSONALIZED_DRAWING_EXPLORATION_TAP_25D_PLAN.md`

## Decision summary

The new direction does not replace PixiJS. It adds a separate whiteboard-video implementation
after PixiJS and before the physical activity:

```text
Canonical understanding + Gate A/B
  -> PixiJS Personalized Drawing Exploration
     (tap-to-discover + 2.5D cut-out)
  -> Whiteboard video generation runs in parallel while Pixi is playing
     (VLM localization -> SAM 2.1 Small -> contour/stroke extraction -> MP4 + TTS)
  -> Parent is notified only when the video is ready
  -> Parent continues to video playback
  -> Off-screen activity
```

The video uses the same approved `learning_thread` and `ExperienceSpec` as Pixi. The original
drawing remains immutable. The generated video is a derived, session-local artifact in the current
scope and is not an auth/durable-save implementation.

## Comparison against SRS v1.3

| SRS v1.3 baseline | Owner clarification | SRS v1.4 update |
|---|---|---|
| Pixi/art animation and learning micro-video were described as adjacent media, but the runtime order and implementation boundary were not explicit. | Pixi remains one implementation; whiteboard MP4 is a separate video implementation after Pixi and before activity. | Split Pixi exploration and whiteboard video in B2, B5, B6, B10, B12, B14, B15 and B20. |
| Pixi was mainly described as validated motion/reveal on original art. | Pixi keeps tap-to-discover and 2.5D cut-out. | Add `SceneExplorationPlanV1`, learning thread, focus/relationship beats, tap state and source-derived depth layers. |
| Video was generic 5–10 second learning media. | Video is a whiteboard-style reconstruction of the child’s own strokes where technically possible. | Specify VLM localization, SAM 2.1 Hiera Small, contour/stroke extraction, deterministic render and FFmpeg/NVENC as the target pipeline. |
| Video timing was described as a later phase/flag. | Video generation starts while Pixi is playing and exposes progress/loading. | Add concurrent job semantics, `WHITEBOARD_VIDEO_PENDING/READY/RETRYABLE_FAILURE`, readiness gate and parent notification rule. |
| TTS/narration relationship was not separated from the child narration input. | TTS is a separate narration track generated from the approved learning thread; it is not the child’s raw voice/narration. | Add independent TTS provenance and privacy boundary. Child narration remains an understanding input only. |
| Media failure generally allowed a fallback path, but video-ready gating was not explicit. | Failed generation can be retried; parent continuation is offered only after successful video generation. | Add typed retryable video failure and no “video ready” claim on failure; final exhausted-failure recovery remains an explicit operational TBD. |
| Video provider/implementation was open. | MP4 implementation must be added as the next implementation task; diffusion is not the default path. | Keep LTX/video diffusion as optional future fallback, outside the current deterministic whiteboard MVP implementation task. |
| Derived media persistence was broadly described. | Current video is process-local/session-only; auth and durable save come later. | Add explicit session-only storage/provenance constraint. |

## Resolved owner decisions

- The target product contains both PixiJS exploration and whiteboard video.
- PixiJS is not converted into whiteboard mode; the two are separate implementations.
- The video is generated concurrently during Pixi playback.
- Parent receives the continue action only when the video is ready.
- Generation failure is retryable and must not be presented as success.
- The video uses the same learning thread/ExperienceSpec as Pixi.
- The video preserves original child-drawing identity and does not invent new subject/action content.
- TTS is independent from child narration and is derived from the approved learning thread.
- SAM 2.1 Small is the baseline segmentation model; Grounding DINO and diffusion remain optional
  future/fallback work unless separately approved.
- MP4 generation is the next implementation task; it is not implemented by this documentation
  update.

## Remaining open decisions kept in the SRS

- Exact MP4 resolution, codec/profile, bitrate, audio format and maximum artifact size.
- Exact video job timeout, retry count/backoff and exhausted-failure recovery UI.
- TTS voice/provider, language/locale, voice safety review and whether TTS may be disabled per
  session.
- Quality threshold for accepting a VLM region, SAM mask and extracted stroke path.
- Whether the parent must watch the full whiteboard video before the activity handoff.
- Production worker placement, GPU scheduling, durable storage and provider budget.

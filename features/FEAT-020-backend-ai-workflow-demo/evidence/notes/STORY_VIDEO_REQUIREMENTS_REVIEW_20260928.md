# Story/video requirements review — 2026-09-28

**Current age-scope amendment (2026-10-06):** The review's 0–12 starting point is superseded for product and GenAI execution by the `<9` target (0–107 completed months). Keep 9–12 source records; do not include them in current profiles, sessions, or generation. Other story/video decisions in this historical review remain as recorded.

## Review purpose

Record the owner-requested system-design update and the repository pattern review. This note is planning evidence only. No source code, provider, model, cloud resource, child media, or runtime contract was changed or exercised.

## Owner-confirmed requirements recorded

- Short video target: 40–60 seconds.
- Video retells the adult-confirmed picture and adds age-appropriate knowledge about its subject.
- Age/readiness context is used for retrieval and Montessori-appropriate complexity; the existing 0–12-year catalog bands and per-activity hard rules remain the starting point.
- The source can be redrawn in an illustration style, while the original drawing/audio remains immutable and every generated artifact is a linked derivative.
- Adult can revise with quick actions, free-form instructions, or both; each accepted revision is a complete new script.
- Adult approves the exact script packet before any image-generation request.
- Adult chooses a supported output language and voice category; video visuals and TTS remain separate paths.
- Wan2.2 TI2V-5B remains the current video-model baseline; no model switch was requested.

## Repository pattern findings

- `yogendra-yatnalkar/storyboard-ai`: useful design pattern for separating a global direction from scene plans and per-scene production/assembly. Its prompt-first assumptions are not adopted as product truth. Repository license was identified as GPL-3.0; this plan does not copy code.
- `Atharva-Kanherkar/chalkboard`: useful design pattern for typed scene JSON, per-scene narration and audio-led duration, with provider boundaries. Repository license was identified as MIT; this plan does not copy code.
- The resulting contract proposals deliberately separate confirmed scene understanding, selected `ExperienceSpecV1`, reviewed knowledge claims, adult-approved script, storyboard, TTS assets, illustration assets, video scene outputs, and final validation.

## Documents updated

- `plan/PLAN.md` — amendment status and 40–60 second target.
- `plan/CONTENT_STORY_EXPERIENCE_PLAN.md` — understanding/age/knowledge/script editing/voice/approval plan.
- `plan/VIDEO_STORY_PRODUCTION_PLAN.md` — storyboard/illustration/TTS/Wan scene rendering/assembly/validation/L4 plan.
- FEAT-020 approval/context/decision/evidence records and FEAT-029 SRS v1.7 B30–B32.

## Governance and limitations

- Newly proposed schema/API shapes are `PROPOSED_UNADOPTED`; they require registry reconciliation and explicit approval.
- UI behavior is specified, but FEAT-020 remains backend-only and a separate UI feature is required for frontend implementation.
- The old FEAT-020 approval is historical and does not authorize this amendment’s implementation.
- Wan/L4 fit is only a planning baseline; actual target-L4 peak VRAM, full-job latency, quality, failure rate and concurrency remain unmeasured here.
- No automated tests, provider calls, or GPU benchmark were run for this documentation update.

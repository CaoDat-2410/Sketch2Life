# Owner change: story/video target — 2026-09-28

## Scope and authority

This note records the owner’s explicit request to update planning documents and the master SRS. It is documentation evidence only; it does not evidence runtime implementation, provider execution, GPU performance, or contract adoption.

## Owner-confirmed changes

- Replace the prior story-video duration target of 5–10 seconds with 40–60 seconds.
- Allow the drawing’s subject to be redrawn in an illustration style as a derived artifact; preserve the original drawing/audio unchanged.
- Retell the adult-confirmed picture and teach age/readiness-appropriate subject knowledge, retrieved from reviewed sources with claim-level citations.
- Use the existing ChildProfile/P1 age and readiness context; do not infer age/readiness from media.
- Support script edits through both quick controls and free-form adult instructions; return a full new revision for review.
- Require adult approval of the exact final script packet before any image-generation request.
- Let the adult choose a supported output language and voice category. Keep TTS independent from video model generation and do not default to the child’s raw voice.
- Keep the current Wan2.2 TI2V-5B profile as the video-model baseline.

## SRS treatment

Master SRS is v1.7. B30–B32 define precedence, target flow, new/changed FRs, logical contract inventory, request/API/job semantics, error categories, READY validation, traceability, acceptance scenarios, L4 evaluation and open decisions. FR-017 and FR-055–FR-059 were aligned to the new target; FR-066–FR-076 and NFR-047–NFR-054 were added. The 2026-09-23 decision remains historical where the 2026-09-28 owner change supersedes it; Pixi separation, READY gating, independent TTS and provenance remain in force.

## Planning artifacts

- FEAT-020 `plan/CONTENT_STORY_EXPERIENCE_PLAN.md` covers audience, reviewed knowledge, draft/revision, quick and free-form editing, voice selection, approval hashes, stale state and acceptance criteria.
- FEAT-020 `plan/VIDEO_STORY_PRODUCTION_PLAN.md` covers approved package, storyboard, illustrated stills, per-scene Wan rendering, separate TTS, timing/assembly, validation, retries/cancellation, L4 workload measurement and implementation deliverables.
- FEAT-020 `plan/PLAN.md` records the amendment and points to both plans. Its new requirements are not covered by the earlier plan approval.

## External repository pattern review

- `storyboard-ai`: global director/scene plan and per-scene orchestration pattern; source code not reused. The inspected repository identified GPL-3.0 licensing.
- `chalkboard`: typed scene data, per-scene narration and measured audio-driven timing pattern; source code not reused. The inspected repository identified MIT licensing.
- Wan/L4 feasibility references are the official [Wan2.2 repository](https://github.com/Wan-Video/Wan2.2) and [NVIDIA L4 product page](https://www.nvidia.com/en-us/data-center/l4/). Upstream documents the 5B TI2V profile around a 24 GB offloaded-memory boundary; L4 also has 24 GB. This makes actual peak VRAM, latency and co-residency a benchmark requirement, not an established performance claim.

## Review limitations and open decisions

- No tests, model/provider calls, downloads, GPU run or L4 benchmark were requested or run.
- New `*V1` schemas, API names, error codes, event/state mappings and validators are proposals (`PROPOSED_UNADOPTED`).
- Knowledge corpus/reviewer, citation UI, quick-action catalogue, supported locale/voice inventory, visual styles, scene count, exact model revisions/licenses, codec/resolution/FPS, L4 latency/quality/concurrency thresholds, retention/provider-copy policy and exhausted-failure/fallback behavior remain open.
- FEAT-020 is backend-only; frontend controls/playback need a separate approved feature plan.
- Documentation-only approval does not authorize implementation.

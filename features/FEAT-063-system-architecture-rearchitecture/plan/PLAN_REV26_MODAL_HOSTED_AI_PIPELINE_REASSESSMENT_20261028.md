# Plan revision 26 — reassess Modal-hosted AI models and media flow

- Feature: FEAT-063 — Whole-repository architecture redesign.
- Status: AWAITING_APPROVAL for this exact documentation amendment. This plan follows the owner's 2026-10-28 request to research the supplied review, reassess the AI stack, and propose Modal-hostable alternatives. Product implementation, model calls and benchmark execution are not approved.
- Current authority: full SRS v2.3-draft and Data Table Register v2.3-draft. The pasted assessment is about v2.2 and is review input, not the current source of truth.
- Scope authority: keep the platform layer, Parent and Teacher flows, child-art capture, optional in-session sketches, one-child sample, and personalized image-to-video behavior. Add only changes supported by owner decisions or accepted by the owner after reviewing this revision.

## Scope

- Reconcile each finding in the pasted v2.2 review against current v2.3. In particular, record that the current SRS already routes confirmed scripts through `VIDEO_ADMISSION_PENDING`; update the stale v2.3 Risk R-11 and Open Item OI-11 count references from 91/126 to the current source-declared 89 active / 137 physical target; state that neither count is a live database inventory.
- Refresh the candidate matrix with exact model family/checkpoint, task fit, Modal execution path, GPU/memory evidence, license status, and unverified items. Treat FLUX 3 Image Klein, LTX-2.5, SAM 2/3, Whisper, Qwen3-ASR, Qwen3.5/3.6, VieNeu-TTS, Qwen3Guard and ShieldGemma 2 as candidates; compare alternatives where licensing or task fit makes them useful. Do not promote a model to a final production default without a synthetic benchmark and license review.
- Propose a Modal AI runtime boundary: application backend owns authorization, job contracts, secrets and asset transfer; Modal-hosted functions receive allowlisted task inputs and return versioned outputs with hashes/lineage; clients never call Modal. Distinguish custom Modal GPU functions from Modal-managed Endpoints and retain a provider-neutral application port.
- Redesign the AI flow description for:
  - optional Vietnamese ASR of adult-recorded ideas and adult transcript confirmation;
  - drawing-photo normalization, optional segmentation, VLM observation and adult subject confirmation;
  - structured story/lesson drafting and adult review;
  - optional Parent line-sketch and Teacher Sketch Deck;
  - lesson illustrations/slides;
  - silent child-specific video generation, Vietnamese narration timing, rough/final composition and early/per-scene/final safety gates.
- Keep Parent guide independent of StoryRun. Evaluate a generic topic/difficulty cache for Parent guide and reusable lesson illustrations; cache keys must exclude account, child, profile and artwork data. A disabled sketch toggle must still produce neither a new job nor a guide display.
- Add Teacher Deck progress at activity/sketch level so completed items can be previewed while generation continues; only a complete, current, `READY` revision is eligible for full-deck presentation. Preserve stale-revision behavior.
- Define a benchmark plan, not a benchmark result. Compare 5–8-shot/30–45-second synthetic prototypes, including LTX native multi-shot versus per-shot image-to-video, and compare a lower-license-friction video candidate. Measure quality, safety, latency, cold start, peak GPU memory, GPU-seconds, retries and estimated cost.
- Revisit video quota and Teacher sample-slot UX as explicit options. Do not silently change Q110/BR-11, the existing no-refund rule, or the existing one-sample claim semantics; present bounded alternatives for owner decision.
- After approval, revise the full SRS to v2.4-draft, update the relevant requirements/business rules/acceptance criteria/state and risk references, and create a proposed ADR for the AI/Modal runtime. Update the Data Table Register only if an accepted requirement creates or changes a logical entity. Reconcile DECISIONS, CONTEXT, local/global source registers, STATUS and feature-local evidence.

## Provisional research recommendations

- Keep Modal as the hosting target. Use custom Modal GPU functions/classes for pinned self-hosted checkpoints where the application needs exact runtime and data controls; use Modal Endpoints only when their managed execution and data boundary meet the same requirements.
- Benchmark Whisper large-v3-turbo against Qwen3-ASR-0.6B/1.7B on Vietnamese audio. Qwen3-ASR explicitly lists Vietnamese; Whisper has a current Modal deployment example. Adult transcript confirmation remains mandatory.
- Benchmark Qwen3.5-9B as the first shared VLM/story-LLM candidate and Qwen3.6-27B as a quality challenger. Keep VLM and story-generation contracts as separate stages even if they share a model deployment. The earlier Qwen3-VL NO_GO applies to that earlier checkpoint/runtime evidence and does not disqualify Qwen3.5/3.6.
- Evaluate FLUX 3 Image Klein for generic lesson illustrations and visual assets, with prompt upsampling, output review and provenance. Compare FLUX.2 Klein 4B if a more permissive weight license is needed. Do not use an image generator to replace the child's original drawing.
- Use deterministic crop/perspective/contrast normalization first. Keep SAM segmentation optional and reversible; compare SAM 2.1 with SAM 3 only if it improves paper/drawing masks without removing faint strokes.
- Keep LTX-2.5 as the leading video POC candidate because it supports image-to-video and native multi-shot. Begin a synthetic POC on an 80-GB H100-class Modal GPU; separately test whether a 48-GB L40S is adequate at the selected resolution/precision. Compare Wan2.2 TI2V-5B as a permissive-license alternative. These are POC candidates, not measured recommendations.
- Generate the approved Vietnamese narration after script approval and align its timing before final composition. Request silent LTX output, compare a rough-cut pass and final encode, and validate each generated shot as well as the final muxed video.
- Keep VieNeu-TTS v3 Turbo as the first Vietnamese narration candidate, using an approved adult preset voice and no voice cloning. Benchmark pronunciation, naturalness, timing and license/runtime fit.
- Evaluate Qwen3Guard-Gen-0.6B/4B for text moderation and ShieldGemma 2 4B for image moderation as separate safety candidates. Validate Vietnamese and child-facing policy categories; neither model may be the only safety gate.
- Run prompt/script checks before generation, inspect image/video outputs per stage, then run safety over the final audio, subtitles and video. Unknown or incomplete safety coverage blocks playback. Human publication review remains separate from automated safety.

## Out of scope

- Product source/UI/API changes, schema or migration changes, live database access, provider/model inference, Modal deployment, GPU spending, benchmark execution, generated image/video/audio assets, product tests/builds, real-child data, production rollout, or Git commit/push.
- Final model, checkpoint, GPU profile, quota policy, sample recovery policy, legal interpretation, or final stack lock.
- Removing or rewriting historical SRS snapshots, prior decisions, or source artifacts.

## Acceptance criteria

- AC-26-01: The assessment matrix maps every supplied v2.2 finding to current v2.3 as already addressed, still open, stale, or requiring an owner decision, with evidence locations.
- AC-26-02: Every model candidate has a source link for the checkpoint and relevant capability, a Modal hosting mode, GPU/memory evidence where published, license note, and a clearly marked uncertainty.
- AC-26-03: The revised AI flows name each stage's actor, approved inputs, structured output, version/hash, human gate, failure/retry behavior, privacy boundary and quota owner.
- AC-26-04: The video proposal compares native multi-shot and per-shot generation, places narration/timing before final composition, adds per-shot and final safety gates, and preserves the selected child's artwork as the source reference.
- AC-26-05: Parent sketch stays optional and independent of StoryRun; Teacher Deck may preview completed generation items while presentation remains gated on a complete current READY revision.
- AC-26-06: Quota charging and Teacher sample-slot options are shown with tradeoffs; no existing owner rule is changed without an explicit owner decision.
- AC-26-07: The current SRS and Data Table Register counts agree at 89 active + 48 legacy/read-only = 137 projected physical, and the text expressly says no live DB inventory was performed.
- AC-26-08: Requirement, business-rule, acceptance-criteria, risk and trace matrices are reconciled without duplicate IDs or stale current-state references.
- AC-26-09: The proposed ADR, context, decision log, status, source registers and feature-local evidence agree with the revised SRS; prior snapshots remain intact.
- AC-26-10: The evidence record distinguishes researched documentation from an executed benchmark. No model call, Modal operation, DB access, product test/build or real-child processing is represented as completed.

## Risks and review gates

- Model and weight licenses can differ from the inference-code license; commercial product use requires a specific legal review.
- Modal GPU inventory, pricing, runtimes and model-serving support can change. Reconfirm those details before any approved POC.
- Public model benchmarks do not establish quality on children's drawings, Vietnamese storytelling, Montessori content, or the project's child-safety criteria.
- A unified VLM/LLM deployment may reduce duplicated model hosting but can increase memory contention and couple failure domains; the prototype must compare it with separate task workers.
- The prior user answers Q11 and Q13 leave the roles allowed to initiate AI lesson suggestions unresolved; retain that question until the owner clarifies it.
- Full schema verification remains a separate read-only database-inventory task requiring its own explicit access and evidence plan.

## Verification plan for the documentation amendment

- Check all cited model facts against official publisher/Modal sources and record access date.
- Static-check SRS/ADR/register/status/source links, requirement-ID counts, trace coverage and current target-count arithmetic.
- Inspect the final diff and run document hygiene checks.
- Do not run product tests/builds or provider/model benchmarks as part of this plan.


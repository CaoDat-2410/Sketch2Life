# EV-063-19 — Modal-hosted AI model and pipeline reassessment

- Date: 2026-10-28
- Feature: FEAT-063
- Type: external-source research and current-SRS review
- Status: research recommendations and Plan Rev26 draft only; no canonical architecture approval or implementation is implied.

## Authority and baseline

The owner requested research into the supplied v2.2 assessment, proposed model families and Modal-hosted AI flows. Plan Rev25 approved a different documentation amendment and explicitly did not approve model selection/provider execution. Plan Rev26 awaits approval for the proposed documentation amendment (SHA-256 `ECD0A0A6435193A903313409B699574FE9DB30BAAB8498A714A3FC54C75EEABC`). Current authority remains the v2.3-draft full SRS and Data Table Register.

The supplied review describes v2.2. The active v2.3 SRS already routes script confirmation through `VIDEO_ADMISSION_PENDING`, then to `VIDEO_QUEUED` only after admission receipts. The active SRS's current logical target is 89 active + 48 legacy/read-only = 137 projected physical. Its R-11 and OI-11 entries still contain the older 91/126 numbers and should be reconciled in the next approved SRS amendment. Neither number is a live database inventory. No DB was accessed.

The SRS already keeps Parent Sketch Guide separate from StoryRun, keeps Teacher Deck optional per session, marks LTX per-scene quality/runtime as a POC gate, and fails closed on incomplete final safety coverage. The external review's proposed Teacher progressive preview and quota/sample UX changes remain proposals, not owner decisions.

## Finding-by-finding reconciliation

| Finding in the supplied review | Status in current v2.3 baseline | Proposal for the next approved revision |
|---|---|---|
| 78 active / 126 physical is a large capstone scope | Those figures belong to v2.2. The current platform extension is 89 active + 48 legacy/read-only = 137 projected physical. Both are source-declared design counts, not a live DB inventory. | Keep schema inventory as a separate gate; stage implementation by vertical slice; don't claim the count is verified against a running DB. |
| R-11 still says 91/126 | Confirmed: current v2.3 Risk R-11 and Open Item OI-11 retain 91/126 text. | Correct to 89/137 and keep the explicit no-live-inventory caveat. |
| Script flow skips `VIDEO_ADMISSION_PENDING` | Already addressed in current v2.3. The active flow includes admission pending and only queues after admission receipts; rejection returns to script review. | Keep state/sequence diagrams aligned when they are separately refreshed. Existing diagram/PDF outputs are historical. |
| LTX consistency, Vietnamese TTS and safety need a working prototype | Still open; SRS already treats runtime/quality as a POC gate. | Plan a synthetic A/B benchmark; compare native multi-shot with per-shot jobs; keep safety checks at prompt, shot and final-output levels. |
| 5–15 shots and 30–90 seconds may be too expensive | These are current SRS product targets, not measured capacity. | Use 5–8 shots and 30–45 seconds as a bounded first benchmark case, then decide whether to change product targets. |
| Teacher Deck blocks preview until complete | Current SRS does not yet describe progressive item-level preview. | Track each activity/sketch as queued/running/ready/failed/stale; allow preview of ready items, while full presentation waits for the current complete READY revision. |
| Parent Guide may need a StoryRun first; popular topics should be cached | Current SRS already gives the guide a generic topic/difficulty target independent of StoryRun. | Preserve that boundary; evaluate safe generic caching with a key that contains no account, child, profile or artwork data; disabled means no job or display. |
| Final video-only safety catches failures too late | Current SRS has a final fail-closed gate but not the proposed layered checks in every stage. | Add prompt/script, per-image/per-shot and final video/audio/subtitle checks. Keep automated safety separate from publication review. |
| Audio timing should precede final composition | Current SRS puts TTS after scene composition. | Generate narration after script approval, align timing before the rough cut, then final composition/mux/subtitles and safety checks. |
| Quota is charged on technical/safety failure; sample slot never reopens | These are explicit existing owner rules, not implementation mistakes. | Keep them until the owner changes them; present bounded platform-failure refund/recovery options for review. |
| Verify actual database schema | No live DB/schema was accessed. | Keep as a separate, read-only inventory/restore-rehearsal gate requiring its own access plan and evidence. |
| RQ/outbox may be too complex; compare Temporal | No runtime recovery benchmark has been run. | First test restart/retry/reconciliation with the current simple queue; compare a workflow engine only if that reveals a real recovery gap. |

## Candidate model assessment

| Task | Candidate | Modal feasibility | Fit and main caveat |
|---|---|---|---|
| Adult voice ASR | Whisper large-v3-turbo / faster-whisper; compare Qwen3-ASR 0.6B and 1.7B | Modal has an official Whisper deployment/batching example. Qwen3-ASR can be packaged in a custom GPU function; no project benchmark found. | Qwen3-ASR explicitly lists Vietnamese. Compare Vietnamese accent/noise, CER/WER, correction rate and latency. Keep adult transcript confirmation. |
| Drawing VLM + structured story | Qwen3.5-9B as first candidate; Qwen3.6-27B as challenger | Modal's model catalog lists Qwen3.5/3.6 dedicated endpoints; custom Modal functions can host pinned weights. | Qwen3.5-9B supports image-text input under Apache-2.0. Keep image observation and story generation as separate versioned calls/contracts, even if one model deployment serves both. New Qwen versions require fresh target-task evaluation; old Qwen3-VL NO_GO evidence is not transferable. |
| Lesson/slide illustration | FLUX 3 Image Klein; compare FLUX.2 Klein 4B | Modal supports custom GPU functions and has a Flux image-editing example, but no current official FLUX 3 Modal example was found. The BFL reference pipeline is a custom-container candidate. | FLUX 3 supports text/image generation/editing and layout control, but requires its prompt upsampler for expected prompt quality. The weights use FLUX Kommunity License; the inference code is Apache-2.0. The official repo says its optional safety checks are off by default. FLUX.2 Klein 4B is an alternative with Apache-2.0 weights. Model-generated child-facing visuals still require project safety/review. |
| Drawing photo normalization | OpenCV crop/perspective/contrast; optional SAM 2.1 or SAM 3 | CPU/GPU image containers are hostable on Modal; SAM3 needs a compatible CUDA/PyTorch image and gated checkpoint access. | Prefer deterministic, reversible normalization first and preserve the original. Segmentation can remove faint pencil strokes or produce a poor paper mask; request adult crop/reshoot on low confidence. SAM 3 is an alternative, not a mandatory stage; its separate SAM License must be reviewed. |
| Image-to-video | LTX-2.5 open-weight checkpoint; compare Wan2.2 TI2V-5B | Modal GPU guide supports H100, L40S and B200. Modal's LTX example is for the older LTX-Video pipeline, not an LTX-2.5 deployment. A custom LTX-2.5 runtime is technically plausible but unproven here. | LTX-2.5 supports image-to-video and native multi-shot; minimum published GPU memory is 32 GB, with A100/H100 80 GB recommended. Compare a synthetic H100 POC with a 48-GB L40S profile. The LTX-2.x Community License has commercial-use conditions. Wan2.2 I2V/TI2V is an Apache-2.0 alternative; its I2V-A14B reference command specifies 80 GB, while TI2V-5B supports 720p/24fps. |
| Vietnamese narration | VieNeu-TTS v3 Turbo | Publisher's SDK supports PyTorch on GPU; package can be placed in a custom Modal GPU function. No official Modal example found. | Vietnamese-first candidate, Apache-2.0 per project; use an approved adult preset voice, not voice cloning. Measure pronunciation, naturalness, script timing and warm/cold latency. |
| Safety moderation | Qwen3Guard-Gen-0.6B/4B for text; ShieldGemma 2 4B for images | Custom Modal functions are plausible for these open weights; no project deployment or target-task benchmark exists. | Qwen3Guard claims multilingual coverage; test Vietnamese prompts/story/lesson text. ShieldGemma 2 classifies images but only covers its documented policy categories. Do not use either as the single safety gate. |

## Proposed flow for review

1. Backend validates the capture and stores an immutable original. CPU image processing detects/corrects page perspective and contrast. If confidence is low, adult crop/reshoot is offered. Optional SAM segmentation creates a derived mask only when the POC shows improved stroke preservation.
2. For an adult-recorded idea, ASR runs on Modal with an allowlisted audio asset. The adult reviews/corrects the transcript before any story request. No audio is sent to FLUX or a lesson-generation model.
3. A VLM reads only the selected drawing plus minimal approved profile context. It returns a versioned observation JSON with candidate subject, visual anchors, confidence and uncertainty. The adult confirms the subject; correction creates a new observation revision pinned to the same image hash.
4. Story/lesson planner receives confirmed structured facts, approved age context and permitted lesson direction; it returns strict JSON. The adult reviews the story and storyboard before video inference. Teacher lesson-document upload continues to use parser/filter/allowlist and human extraction review before AI.
5. After script approval and video admission, synthesize Vietnamese narration first. Align the approved text to the actual audio and derive shot/beat timing; then generate silent LTX clips against those target durations. Build a rough cut, adjust timing/cuts, render the final composition and synchronized subtitles, then run final safety. Keep lesson activities after the completed Parent video.
6. Compare LTX native multi-shot against per-shot image-to-video on synthetic drawings. Native multi-shot may reduce stitching and keep connected shots together; it does not guarantee identity consistency. Per-shot work retains targeted retries but can drift. Keep the original child drawing immutable and use it as the reference; every child's video is freshly generated.
7. Evaluate Qwen3Guard for text and ShieldGemma 2 for image classification, but keep deterministic policy checks and fail-closed orchestration around them. Validate prompt/script before inference, each generated shot before composition, and the complete final video/audio/subtitle package before playback. Unknown or missing safety coverage blocks playback. Automated safety does not replace Manager review for Public lessons.
8. Parent sketch remains a generic topic/difficulty capability shown only when the adult turns it on during drawing; no StoryRun is needed to open it. A cache may be considered only for safe, generic, approved guides keyed by topic/difficulty/model/prompt/policy versions, with no child/account/profile/artwork values in the key. Teacher Deck may expose ready sketch previews progressively; full presentation stays gated on the complete current READY revision.
9. Host the work behind the application-owned Modal adapter and durable job boundary. Separate resource profiles by task rather than splitting into many independently managed microservices: light ASR/image preprocessing, a shared Qwen multimodal worker where memory allows, a visual-generation worker, and a high-memory video worker. Persist model/runtime/prompt/policy revisions, input/output hashes, usage/timing and lineage; never log media, transcript, prompt or child identifiers.

## POC acceptance matrix to use after separate approval

| Slice | Synthetic input | Measures |
|---|---|---|
| ASR | Adult speech samples covering Northern/Central/Southern Vietnamese, noise and child-topic vocabulary | CER/WER, adult correction rate, hallucination on silence, p50/p95 time and GPU-seconds |
| VLM/story | Synthetic childlike drawings with intentionally ambiguous subjects and age bands | subject accuracy, uncertainty calibration, attribute hallucination, schema pass rate, adult rewrite rate, Vietnamese age-fit rubric |
| Segmentation | Photos with perspective, shadows, faint pencil and colored drawings | mask IoU, retained-stroke rate, crop success, adult correction rate, false crop |
| Sketch/visual | Common and uncommon lesson topics | 3–5-step progression, recognizability, line clarity, safety/review pass rate, cache hit and generation time |
| Video | Same set of synthetic drawings/scripts at 5–8 shots, 30–45 seconds | subject/style continuity, action adherence, artifact rate, audio/subtitle sync, safety coverage, p50/p95 latency, GPU peak memory/seconds, retries |
| Orchestration | Synthetic jobs with worker termination, timeout, retry and stale revision | duplicate-dispatch protection, idempotent completion, recovery time, orphan assets and quota consistency |

The benchmark should compare RQ/outbox recovery with a workflow-engine POC only if the simple worker-restart/reconciliation test exposes a real recovery gap. Public leaderboard scores are not acceptance evidence for this application.

## Quota and sample-slot options (not decided)

- Current v2.3 rule: a video request consumes a quota unit after admission even if later provider/technical/safety failure occurs; scene retries do not add units. Keep this behavior until the owner selects a policy.
- UX option: reserve quota at admission and release it for a bounded platform-side failure before any playable result; adult-requested quality regeneration remains a new charged request. Decide separately whether a safety block is refundable, with rate limits against repeated harmful input.
- Current Teacher sample rule: the occurrence slot is claimed by the first playable sample and does not automatically reopen later. UX option: permit one audited recovery only when a platform-side moderation/technical event invalidates the sole sample; do not reopen it for a subjective preference change. This needs an owner decision and bounded abuse policy.

## License and hostability gates

- Modal GPU Functions/Classes are a viable custom-hosting path in principle because Modal accepts custom container images and lists GPUs through H100/B200/L40S. The exact current runtime still needs a synthetic deployment test; no Modal inference or account operation was run.
- Modal's catalog of Dedicated Endpoints is a managed serving option, not identical to a custom pinned Modal application. For child media, select only after its execution, retention and logging boundary is accepted.
- LTX-2.5 weights and FLUX 3 weights have separate model licenses. Their publisher's inference code license does not replace the model-weight license. Get legal review before any paid/public product use.
- SAM 3 has a separate license and gated weights; do not use it as the baseline when SAM 2.1/OpenCV meets the task.
- This note is architecture research, not legal advice, proof of compatibility or a benchmark result.

## Sources (official publisher or platform)

- [LTX-2.5 model capabilities](https://docs.ltx.io/models/ltx-2-5)
- [LTX-2.5 self-host system requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements)
- [LTX-2.x Community License](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x)
- [Modal GPU types](https://modal.com/docs/guide/gpu)
- [Modal LTX-Video example (older pipeline)](https://modal.com/docs/examples/ltx)
- [Black Forest Labs FLUX 3 Image Klein reference](https://github.com/black-forest-labs/flux-3-image-klein)
- [Black Forest Labs FLUX 2 reference and Klein licensing](https://github.com/black-forest-labs/flux2)
- [Modal Flux image-edit example](https://modal.com/docs/examples/image_to_image)
- [Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B)
- [Qwen3.6-27B model card](https://huggingface.co/Qwen/Qwen3.6-27B)
- [Qwen3-ASR project](https://github.com/QwenLM/Qwen3-ASR)
- [OpenAI Whisper project](https://github.com/openai/whisper)
- [Modal Whisper deployment example](https://modal.com/blog/how-to-deploy-whisper)
- [Meta SAM 2 repository](https://github.com/facebookresearch/sam2)
- [Meta SAM 3 repository and license](https://github.com/facebookresearch/sam3)
- [Wan2.2 official repository](https://github.com/Wan-Video/Wan2.2)
- [VieNeu-TTS publisher repository](https://github.com/pnnbao97/VieNeu-TTS)
- [Qwen3Guard official project](https://github.com/QwenLM/Qwen3Guard)
- [Google ShieldGemma 2 model card](https://ai.google.dev/gemma/docs/shieldgemma/model_card_2?hl=en)
- [Modal supported model list](https://modal.com/docs/guide/supported-models)

## Work performed and limits

- Read the current FEAT-063 context, SRS, Data Table Register, approval record, Plan Rev25, relevant decisions, source register, and governance workflow/approval policy.
- Searched official model and Modal documentation on 2026-10-28. No model weights were downloaded or run.
- No product code, UI/API, physical schema, migration, live DB, Modal account, provider call, model inference, GPU spend, benchmark, test/build, generated media, deployment or real-child processing was performed.
- Plan Rev25 and its approval record remain unchanged. FEAT-063 SRS/Data Table Register v2.3 remain the canonical unsigned drafts.

## Superseding data-count note - Rev31

The recommendation above was accurate when the Rev26 research note was recorded. The Rev31 implementation review later corrected SRS R-11/OI-11 and reconciled the v2.3 draft baseline (89 active/137 projected physical) with the implementation crosswalk (92 active/140 projected physical). Neither count is a live database inventory. See EV-063-24 and Data Table Register section 14.4.

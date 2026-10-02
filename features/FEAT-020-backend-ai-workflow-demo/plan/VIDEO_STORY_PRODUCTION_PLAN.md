# FEAT-020 Plan B — Illustrated 40–60 Second Story Video

- **Revision:** 2026-09-28, owner-requested scope expansion
- **Plan status:** `DRAFT_FOR_REVIEW`
- **Implementation status:** `NOT_AUTHORIZED_BY_THIS_DOCUMENT`
- **Contract status:** every new contract below is `PROPOSED_UNADOPTED`.
- **Consumes:** `ApprovedStoryPackageV1` from `CONTENT_STORY_EXPERIENCE_PLAN.md`.
- **Video model baseline:** keep the current Wan2.2 TI2V-5B profile; model replacement is not in this proposal.

## 1. Objective

Produce a 40–60 second short video that retells the child’s confirmed picture and explains age-appropriate, source-backed knowledge. Create derived illustration images per scene, generate narration as a separate TTS asset, render silent scene clips with the existing video-model adapter, then assemble and validate the result. This replaces the prior 5–10 second whiteboard-video target for this product experience; it does not alter the separate PixiJS `Personalized Drawing Exploration` renderer.

The original drawing and child narration remain immutable source artifacts. Illustration redraw is allowed for presentation, but every generated still/clip must be clearly marked as derived, tied to the approved story package, and checked against confirmed anchors and approved fact IDs.

## 2. Inspiration and reuse boundary

- `storyboard-ai`: use the planning pattern `global direction → scene list → per-scene image/video/narration work → assemble`; do not adopt free-form one-prompt output as product truth.
- `chalkboard`: use the pattern of typed scene records, per-scene narration/audio assets, provider-neutral voice/render ports, and measured audio duration as timing input.
- These plans borrow patterns only. They do not copy source code. The inspected `storyboard-ai` repo is GPL-3.0 and `chalkboard` is MIT; any future direct code reuse requires separate license review and approval.

## 3. Confirmed requirements and proposed defaults

| Requirement | State | Design consequence |
|---|---|---|
| Total runtime | `OWNER_CONFIRMED_2026-09-28` | Final video target is 40–60 seconds, inclusive. |
| Illustration redraw | `OWNER_CONFIRMED_2026-09-28` | A separate image-generation step may redraw the confirmed subject in an illustration style. |
| Script-first approval | `OWNER_CONFIRMED_2026-09-28` | No illustration/video generation call occurs before final script approval. |
| Narration choice | `OWNER_CONFIRMED_2026-09-28` | Adult chooses output language and supported voice/category; TTS is independent from video generation. |
| Current model | `OWNER_CONFIRMED_IN_CONVERSATION` | Retain existing Wan2.2 TI2V-5B profile as the baseline adapter. |
| Initial scene count | `PROPOSED_UNADOPTED` | Start evaluation with 6–8 scenes; tune using narration and L4 output quality. |
| Per-scene clip duration | `PROPOSED_UNADOPTED` | Prefer short clips (roughly 4–10 seconds) and let the audio timeline determine final cut points. |
| GPU schedule | `PROPOSED_UNADOPTED` | Queue per scene and avoid co-resident VLM/SAM/video weights on the 24-GB L4 unless measured safe. |

## 4. Preconditions and generation order

The video application service accepts work only when:

1. Gate A is confirmed and Gate B/`ExperienceSpecV1` is approved/current.
2. `ApprovedStoryPackageV1` is current and its approval hash matches its script, audience, evidence, locale, and narration selection.
3. Source image/audio refs and checksums are valid and readable under current adult authorization/consent.
4. TTS profile supports the approved locale; a voice sample has been heard/selected where the UI exposes preview.
5. Model adapter preflight confirms current Wan profile, configured weights/runtime, VRAM estimate, storage capacity, and an allowed backend execution environment.

Ordering is strict:

```text
approved script package
  ├─→ TTS per segment → measured audio durations ───────────┐
  └─→ storyboard + per-scene illustrated stills → Wan clips ├→ assemble → validate → READY
                                                           ┘
```

The visual branch may start after script approval. Audio and visuals may run concurrently only after the approved packet exists. Each video-model request is silent; TTS is muxed after visual render. Raw child narration remains an understanding input and is not reused as the video voice track by default.

## 5. Proposed contract set

Every contract name is a logical proposal and must be reconciled with the contract registry before code/API work. Use versioned immutable refs, hashes, idempotency, session-version checks, actor authorization, and backend-held provider credentials.

### 5.1 `ApprovedStoryPackageV1`

Required fields: `contract`, `package_id`, `version`, `session_id`, `session_version`, `source_image_ref + sha256`, optional `source_audio_ref + sha256`, confirmed-understanding ref/hash, Gate A decision ref, Gate B decision ref, exact `experience_spec_ref + sha256`, `story_script_ref + revision + script_hash`, `evidence_set_ref + hash`, `audience_profile_ref + hash`, `locale`, `narration_profile_ref + hash`, `target_duration_seconds={min:40,max:60}`, approval ref/hash, content-validator policy/version/result, `created_at`, `package_hash`.

Invariants: all refs resolve to immutable current records; no generated visual prompt is part of the approved package; script approval is adult-authored decision provenance; changed source/spec/age/evidence/locale/script invalidates the package; no provider request proceeds on mismatch.

### 5.2 `StoryboardPlanV1`

Required fields: plan ID/version/hash, package ref/hash, overall purpose/learning objective, total duration bounds, selected illustration-style profile ref/version, ordered scenes, transitions, audio/video edit plan, and planner provenance.

Each `StoryboardSceneV1` requires:

- `scene_id`, sequence index, narrative segment ID, narrative purpose;
- exact approved narration segment ID and claim IDs used by this scene;
- confirmed anchor IDs/source observation refs depicted;
- `visual_goal`, `allowed_entities[]`, `forbidden_entities[]`, `allowed_actions[]`, `forbidden_actions[]`;
- illustration prompt reference/hash (kept backend-side; not logged raw), style ref/version, reference asset refs;
- expected visual duration range, transition in/out, frame/aspect profile;
- image-generation/render status and generated artifact refs when present.

Hard rule: every scene maps to one or more approved script segments and either a confirmed anchor or explicit educational claim. Scene ordering may not change the approved narration meaning or create facts not in the package.

Proposed opening/middle/closing beats and 6–8 scenes are tuning defaults only, not fixed acceptance unless owner approves after prototype review.

### 5.3 `IllustrationImageRequestV1` / `IllustrationAssetV1`

Request fields: request/idempotency IDs, session/version, approved package ref/hash, storyboard scene ref/hash, source-image ref/hash, exact confirmed entity/anchor refs, allowed/forbidden element lists, style profile ref/version, locale only if text-free image model requires it (normally no text), safety-policy version, model profile/ref, seed policy, output constraints, created timestamp.

Asset result fields: status (`READY | RETRYABLE_FAILURE | BLOCKED | INVALID`), asset ref/hash/MIME/dimensions, derived-from source refs/hash, package/scene/style/model refs+versions, seed metadata if retained, safety validator report, content comparison report, created timestamp, typed error/retryability.

Invariants: the original is never overwritten; no child-identifying details are added; labels/captions are not rendered by the image model; no unconfirmed species or anatomical detail is silently introduced; image output remains an illustration, not a claim that this is a photograph or exact reconstruction. Generated images are treated as untrusted until validated.

### 5.4 `NarrationRenderRequestV1` / `NarrationAssetV1`

Request: approved package ref/hash, ordered segment IDs/text hashes, locale, voice profile ref/version, pronunciation lexicon ref/version, speaking-rate setting, output format profile, idempotency key, session version.

Result: per-segment and complete audio refs/hashes, measured duration, sample rate/channels/codec, locale/voice/model provenance, pronunciation warnings, segment timing map, validation status, retryable typed error, timestamps.

Rules: actual audio duration is timing ground truth. Estimated duration is a preflight check only. If full narration is outside 40–60 seconds, return to script revision; do not cut words or speed-change beyond the approved pace to force-fit. Subtitle/caption generation is `OPEN_TBD`; if enabled later, it must align to measured word/segment timing and selected locale.

### 5.5 `VideoSceneRenderRequestV1` / `VideoSceneArtifactV1`

Request fields: request/idempotency key, job/session/version, package ref/hash, storyboard plan/scene ref/hash, illustration asset ref/hash, approved fact/anchor IDs, Wan model profile + revision, frame/rate/resolution profile, duration target, motion constraints, safety policy, backend-only execution ref, resource preflight result.

Result fields: scene status, silent clip ref/hash, actual duration/frame count/FPS/codec, model revision/config hash, safe provider job ID, seed if supported, source still ref/hash, content/provenance validator report, resource/latency metrics (backend-private), retry class and error code.

Render constraints: call model per scene; do not submit the child’s raw audio or unrestricted history; limit motion to the scene’s approved action; do not allow a generated clip to invent speech/text; retain the approved still and original source refs; respect configured resource limits. Exact resolution, steps, FPS and latency target are `OPEN_TBD` pending L4 benchmark.

### 5.6 `VideoAssemblyRequestV1`, `VideoArtifactV1`, and `VideoValidationReportV1`

Assembly request binds one approved package, one storyboard, one audio timeline, ordered scene artifact refs, transition/edit profile, MP4 output profile and idempotency key.

Final artifact fields: video ID/version/ref/hash, `status`, session/package/storyboard refs+hashes, duration, audio/video streams and codec metadata, ordered scene IDs/asset hashes, audio ref/hash, source-derived lineage, validation report ref/hash, model/TTS/encoder provenance, retention class, timestamps.

Validation report includes:

| Dimension | Minimum checks |
|---|---|
| Container/technical | MP4 decodes; streams open; expected dimensions/FPS profile; duration is 40–60 sec; non-zero audio/video; no truncated final segment. |
| Audio | Approved locale/voice; all approved text represented; segment timing map consistent; no silent/truncated segments; mux succeeds. |
| Narrative | Scene order and claim IDs match approved script; no added facts or contradiction between narration/visual plan. |
| Visual/source | Every scene traces to source/confirmed anchor/approved claim; no prohibited entity/action; subject/style continuity meets evaluator threshold once approved. |
| Safety/privacy | No unsafe/sexual/violent/disallowed content, identity leakage, raw prompt/credential leakage, or unauthorized source access. |
| Provenance | Hashes, model/profile/revision, validator/policy version, job ID, timings, and all parent refs present. |

Each check returns `PASS | WARN | FAIL | NOT_RUN`, reason code, validator version, and evidence reference. `READY` requires all mandatory checks `PASS`; an unrun check is not a pass. Thresholds for visual similarity/continuity and safety evaluation are `OPEN_TBD` and require a reviewed validation corpus before implementation acceptance.

### 5.7 `VideoJobStatusV1`

Fields: `job_id`, session/version, package/storyboard hashes, state, stage, safe progress (stage label/percent only), created/updated timestamps, retry count/budget, idempotency key, public typed status, public-safe message, and opaque resume token if needed. Provider URLs, raw prompts, tokens, hidden chain-of-thought, private file paths, or child media are not returned in Parent live projection.

Proposed states: `QUEUED → PREFLIGHT → NARRATION_READY + ILLUSTRATIONS_READY → SCENES_RENDERING → ASSEMBLING → VALIDATING → READY`; terminal/recoverable states: `BLOCKED`, `RETRYABLE_FAILURE`, `FAILED`, `CANCELLED`, `STALE_INPUT`, `EXPIRED`. Audio/visual subjobs can progress independently after the approval gate; parent-facing progress must not expose model internals.

## 6. Pipeline and orchestration detail

### V0 — Authorization and preflight

Resolve adult, child relationship, consent, session state/version, current approval hash, retention policy, current source refs, allowed style profile, Wan profile and GPU availability. Reject stale/unapproved requests before queueing or provider invocation.

### V1 — Storyboard compilation

Compile one global visual direction plus ordered per-scene plans from approved segments. Every prompt is derived from a typed scene record; prompts are private adapter inputs and are never the canonical script. Pin style and reference-image profiles to reduce character drift; do not ask the video model to invent educational details.

### V2 — TTS narration

Generate segment audio with the selected language/voice. Measure each segment; build a timeline. If duration is out of range or pronunciation warnings affect a learning claim, mark `SCRIPT_REVIEW_REQUIRED` and return to Plan A. Preserve the previous approval and asset versions as history but do not continue with a mismatching package.

### V3 — Per-scene illustration stills

Generate stills from source drawing + approved scene anchors/claims. Run schema/provenance, image safety, subject-presence and text-artifact validation. On failure, offer a bounded retry or reviewed deterministic still-image fallback; never silently substitute a different subject.

### V4 — Per-scene motion

Submit short scene requests to Wan2.2 TI2V-5B. Ensure the adapter can reclaim/offload VLM/SAM/other model weights before starting video work. L4 has a 24-GB device boundary; do not claim that VLM, SAM, image model and video model can all stay resident together without measured memory evidence. Queue by bounded concurrency and account for cancellation/stale jobs.

### V5 — Timeline and assembly

Use measured TTS audio timeline to allocate scene durations and transitions. Trim or extend visual footage only within explicit edit rules; do not truncate narration. Mux selected narration after silent clips render. Add deterministic title/caption overlays only if the approved script/locale contains the exact content; model-generated lettering is prohibited from being relied upon for correctness.

### V6 — Validation and publishability

Run technical, content/claim, visual/source, audio, privacy and provenance checks. A failed output is non-publishable. READY is written atomically only after the complete MP4 and report are durable/readable for the session. A retry creates a new attempt with linked lineage; it does not overwrite a prior artifact.

### V7 — Client playback/handoff

Start video generation after script approval; it can run while Pixi plays. Show parent-safe status and retry action. Parent Continue remains gated on `READY` plus Gate B/activity handoff readiness. On exhausted failure, show typed recoverable status and the separately approved still/activity fallback policy; never label fallback media as AI video success.

## 7. Failure, retry, cancellation, and stale-job rules

| Failure/status | Retry? | Required behavior |
|---|---:|---|
| `SCRIPT_NOT_APPROVED` / `APPROVAL_STALE` | no | Do not enqueue any image/video request; return to script review. |
| `PROFILE_UNAVAILABLE` / `GPU_NOT_READY` | yes after environment change | Fail preflight; do not pretend a generated artifact exists. |
| `ILLUSTRATION_UNSAFE` / `ILLUSTRATION_INVALID` | bounded | Reject asset; optional regenerate under same scene hash or use explicitly labeled still fallback. |
| `VIDEO_SCENE_TIMEOUT` / `VIDEO_PROVIDER_ERROR` | policy-controlled | Retry only within budget; stable idempotency for same attempt, new attempt ID when parameters change. |
| `AUDIO_DURATION_OUT_OF_RANGE` / `TTS_TEXT_MISMATCH` | no silent fix | Return to story review; new approval required if spoken text/language changes. |
| `ASSEMBLY_FAILED` / `MP4_INVALID` | yes | Reassemble from validated components; do not rerender successful scenes unless invalid/stale. |
| `CONTENT_MISMATCH` / `FACT_UNGROUNDED` | no auto-publish | Block; return to adult/script review or create a new storyboard package. |
| `STALE_INPUT` / `SESSION_REVOKED` | no | Cancel provider work where possible; otherwise mark result non-publishable and retain audit lineage per policy. |
| `VALIDATION_FAILED` | depends on reason | Preserve report and failed artifact securely; user sees safe explanation, not raw provider error. |

All commands use request/idempotency key, expected session version, approval/package hash, bounded retry budget, and job concurrency guard. Replays must not duplicate billable generation unexpectedly. Provider result arriving after revoke/approval invalidation cannot transition the current session to READY.

## 8. L4 performance and quality plan

Wan2.2 TI2V-5B remains the current model baseline; this plan does not switch providers/models. Before implementation acceptance, benchmark on the actual target L4 environment with the same approved synthetic corpus and runtime settings. Do not transfer 4090/H100 timing claims to L4.

The upstream Wan2.2 instructions describe TI2V-5B execution with offload on a GPU with at least 24 GB memory; NVIDIA lists L4 memory as 24 GB. This places the baseline at the device boundary, so it is a fit candidate rather than proof that the entire application stack can co-reside. Measure peak VRAM with actual weights/precision and release VLM/SAM/image-model allocations before video rendering where necessary. Sources: [Wan2.2 official repository](https://github.com/Wan-Video/Wan2.2), [NVIDIA L4 specifications](https://www.nvidia.com/en-us/data-center/l4/).

Record per run: hardware/VRAM, model revision/weight hashes, precision/offload/steps, resolution/FPS/frame count, generation latency by stage, total P50/P95, peak VRAM, OOM/retry rate, per-scene quality rating, identity/style continuity, action compliance, fact/subject errors, output duration and rejected-output rate. Benchmark 5–8 scenes for a complete 40–60-second package, plus isolated scene retry and concurrent Pixi playback.

Acceptance gates (numeric production thresholds remain TBD):

- no OOM at approved bounded concurrency on the selected L4 profile;
- every scene/model call receives only the approved scene packet;
- total assembled video is 40–60 seconds and narration remains complete;
- P50/P95 and resource use are measured, reviewed, and fit the interactive session’s approved wait budget;
- output passes source/story/safety criteria on a reviewed evaluation set;
- job can resume/retry safely after one failed scene without corrupting the script or published artifact.

Because exact waiting-time SLA is not supplied, generation remains asynchronous and user sees progress while Pixi plays. An explicit product maximum wait and numeric visual-quality threshold require a later owner/ADR decision.

## 9. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| VP-AC-01 | Unapproved, stale, or unauthorized story package is rejected before any image/video provider call. |
| VP-AC-02 | Final MP4 is 40–60 seconds inclusive and contains the complete approved narration in the selected locale/voice. |
| VP-AC-03 | Illustration redraws are allowed; original image/audio hashes remain unchanged and every derivative has complete parent refs/hashes. |
| VP-AC-04 | Each scene cites approved anchor/claim/script segment IDs, allowed/forbidden content, style and model provenance. |
| VP-AC-05 | Video AI returns silent scene clips; selected TTS narration is muxed through an independent audio path. |
| VP-AC-06 | Measured audio timing controls scene timeline; out-of-range audio returns to script review rather than being truncated. |
| VP-AC-07 | Final validator checks technical decodability, duration, audio completeness, scene/claim consistency, safety, provenance and current approval hash. |
| VP-AC-08 | `READY` is impossible until mandatory validators pass and final MP4 is readable; failed/fallback jobs cannot claim AI success. |
| VP-AC-09 | Asynchronous job, idempotency, stale-session, cancellation/revoke, bounded retry, and partial-scene recovery have typed transitions. |
| VP-AC-10 | Public progress contains only safe phase/status/progress/time; provider identifiers/errors/prompts are redacted. |
| VP-AC-11 | L4 benchmark reports latency distribution, peak VRAM, OOM/retries, scene quality and full-video quality without extrapolating other-GPU timing. |
| VP-AC-12 | Pixi can continue while video renders, but Parent Continue remains blocked until video `READY` and activity handoff is ready. |

## 10. Deliverables and future implementation work packages

| Order | Deliverable | Dependency / exit condition |
|---|---|---|
| V0 | Approved contracts/ADR and model profile | Reconcile proposed schemas with registry; confirm current Wan profile and deployment boundary. |
| V1 | Story package consumer + storyboard compiler | Plan A approval package validates; scene-to-script/claim mapping is total. |
| V2 | Voice catalog/TTS renderer and measured timeline | Supported locale, preview, audio provenance and duration rejection work. |
| V3 | Illustration generation adapter | Provenance, style profile, text-free output, safety and source linkage pass. |
| V4 | Wan per-scene video adapter | Preflight, bounded GPU lifecycle, typed failure and silent scene outputs pass. |
| V5 | Job orchestration/assembly/validators | Retry, idempotency, cancellation, READY gate and traceable final MP4 work. |
| V6 | Mobile experience integration | Parent-safe progress, playback, retry, stale state, and handoff behavior. |
| V7 | L4 quality/performance evaluation | Synthetic evidence and numeric service acceptance thresholds approved. |
| V8 | Privacy/security/governance closure | Redaction/retention/provider policy, feature-local evidence, security validator, final status. |

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Video redraw changes the child’s intended subject | Keep Gate A anchors; compare each derived scene against allowed entities; ask adult to correct uncertainty. |
| Educational hallucination in visual anatomy | Bind scene to approved claim IDs; reject unsupported details; use deterministic labels/diagrams for precise anatomy. |
| Character/style drift across scenes | Generate and validate per-scene reference stills; pin style/subject refs; benchmark continuity before setting threshold. |
| Audio duration exceeds final duration | Estimate before approval and measure after TTS; return to script edit loop; never truncate speech. |
| Wan takes too long or exceeds VRAM | Async render during Pixi, unload competing weights, bounded concurrency, collect actual L4 P50/P95/VRAM. |
| Partial provider success is mistaken as READY | Atomic final publish after assembly/validation; all state transitions require artifact and report refs. |
| Parent-visible technical leakage | Safe status projection; redact provider/job internals, prompt and child payload. |
| Generated derivative has a separate license/retention profile | Record model/style provenance, source lineage, license and retention class; keep provider-copy deletion as an explicit policy gate. |

## 12. Open decisions before implementation freeze

- Exact Wan checkpoint/revision, image-generation model, license and approved L4 deployment profile.
- Aspect ratio, output resolution/FPS/codec/bitrate and target device playback profile.
- Product max wait, P50/P95 acceptance, queue/concurrency policy and retry budgets.
- Scene count, transition policy, visual-style presets, adult style picker and brand/art direction.
- TTS provider/voice inventory, supported locale list, pronunciation dictionaries, voice preview retention, subtitles/captions.
- Objective visual-quality rubric, identity continuity threshold, validator/evaluation dataset and human-review sampling.
- Whether every short video is mandatory after Pixi or can be skipped with a clearly labeled degraded handoff.
- Artifact persistence/retention, provider copy retention/deletion, consent coverage and process-local versus durable lifecycle.
- Parent behavior after repeated failures and whether an approved still-narration fallback meets product completion criteria.

## 13. Related records and references

- `CONTENT_STORY_EXPERIENCE_PLAN.md`
- `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` B30–B32
- `features/FEAT-029-master-srs/evidence/notes/WHITEBOARD_VIDEO_SCOPE_UPDATE_20260923.md` (historical baseline; superseded only where v1.7 explicitly says so)
- `https://github.com/yogendra-yatnalkar/storyboard-ai`
- `https://github.com/Atharva-Kanherkar/chalkboard`

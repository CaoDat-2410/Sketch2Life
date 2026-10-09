# FEAT-030 feature decisions

## Accepted owner decisions

| ID | Decision | State | Rationale |
|---|---|---|---|
| D-030-11 | Start spatial grounding/segmentation after Gate A; wait for Gate B before compiling the final motion and experience-specific plan. | ACCEPTED 2026-09-25 | Hides preparation latency without weakening Gate B authority. |
| D-030-12 | Cover every drawing topic through the complete archetype registry and mandatory generic/rigid/unknown fallbacks. | ACCEPTED 2026-09-25 | No valid drawing is left without a safe path; specialized movement remains evidence-bounded. |
| D-030-13 | Run auto-rig as an isolated worker/service on the same Lightning L4 host, subject to measured VRAM and GPU scheduling. | ACCEPTED 2026-09-25 | Separates lifecycle/failure while reusing available GPU infrastructure. |

## Architecture decisions (proposal history and approved integrated additions)

| ID | Decision | State | Rationale |
|---|---|---|---|
| D-030-01 | Keep `RendererLoadCommandV1` and whole-drawing fallback during migration. | PROPOSED | Rollback and old-client safety. |
| D-030-02 | Do not restore `/v2/localize` as an unconditional second Qwen call. Introduce replaceable spatial-grounding and segmentation ports. | PROPOSED | The prior path doubled model work and produced invalid regions/503s. |
| D-030-03 | Track auto-rig with an independent job; do not add `GENERATING_EXPERIENCE` to the business session state machine. | PROPOSED | Current session state is already `EXPERIENCE_READY`; media preparation is orthogonal and must not block session validity. |
| D-030-04 | Send V2 package references/capabilities through the bridge, not mesh arrays. | PROPOSED | The current bridge message limit is 4096 bytes; meshes and weights exceed it. |
| D-030-05 | Start with CPU skinning in PixiJS and animate bones/parameters through GSAP. | PROPOSED | Easier validation and deterministic fallback before custom shaders/GPU skinning. |
| D-030-06 | Allow motion only up to safety level 2 by default; motion must be justified by selected subject, observed relation/action, and learning objective. | PROPOSED | Prevents invented, distracting, or unsafe behavior. |
| D-030-07 | Use fallback order `FULL_AUTO_RIG → CUTOUT_MICRO_MOTION → BBOX_VISUAL_FOCUS → WHOLE_DRAWING_V1`. | PROPOSED | Each degradation preserves the child's original and completes the flow. |
| D-030-08 | Classify masks/cutouts/meshes as `ORIGINAL_DERIVED`, separate from creative supplemental assets. | PROPOSED | They require provenance/integrity review, not the same visual-approval semantics as generated decoration. |
| D-030-09 | For MVP, avoid destructive background inpainting. Translation is allowed only when a validated background patch exists; otherwise use internal deformation, pivot motion, camera focus, or V1. | PROPOSED | Prevents visible holes and fabricated drawing content. |
| D-030-10 | Split delivery into separately approved milestones; a plan approval does not authorize every model/dependency at once. | PROPOSED | The feature crosses AI, backend, storage, mobile, renderer, and governance boundaries. |
| D-030-14 | Compile the playback timeline during load and expose a non-zero authoritative duration before autoplay. | ACCEPTED 2026-09-26 | Prevents mobile from disabling pause/seek and makes control state deterministic. |
| D-030-15 | Use a 12–15 second guided intro followed by a bounded idle loop. | SUPERSEDED_BY_D-030-23 | The owner later requested a 15–30 second multi-beat sequence followed by a still rest, not a continuing idle loop. |
| D-030-16 | A full rig requires validated subject and part masks; a full-frame mesh is never a successful full rig. | ACCEPTED 2026-09-26 | Prevents the current whole-image stretching failure. |
| D-030-17 | AI may ground/segment/estimate parts; final animation remains an allowlisted deterministic archetype profile. | ACCEPTED 2026-09-26 | Improves extraction while preserving explainability, safety and reproducibility. |
| D-030-18 | Select SAM 2.1 Hiera Small for the MVP benchmark/integration path and exclude gated SAM 3. | ACCEPTED 2026-09-26 | Removes checkpoint-access friction, keeps the backend-only model small, and preserves the no-second-Qwen-call rule. |
| D-030-19 | Keep initial single-L4 GPU admission serialized and require measured 4 GiB peak headroom plus a 100-job stress pass before concurrency. | PROPOSED REVISION 4 | Qwen3-VL 8B BF16 and segmentation residency must not be assumed safe on 24 GB. |
| D-030-20 | Use AI only for subject/part perception; keep rig construction and animation deterministic. | PROPOSED REVISION 4 | Produces explainable package artifacts and avoids generative redraw or invented motion. |
| D-030-21 | Keep Lightning `/v2/vision` single-pass by default; expose bounded Qwen retry only as an explicit benchmark flag, enable safe structural normalization in memory, and generate SAM2 box prompts from bounded colored-ink regions in the backend. | IMPLEMENTED 2026-09-26 | Prevents one request from loading Qwen twice while salvaging common JSON shape drift and fixing `PROMPT_REQUIRED` without restoring an unconditional localization call or permitting full-frame prompts. |
| D-030-22 | Treat a successful SAM2 subject mask as usable only after a separate bounded read capability, integrity/source checks, and renderer consumption; reconstruct only pixels inside the verified mask with deterministic inpainting, while retaining the immutable original. If the mask itself is invalid, show source plus retry rather than automatically switching V2 to V1. | SUPERSEDED/REFINED_BY_D-030-25_AND_D-030-27 2026-09-29 | Owner directed no automatic legacy animation fallback; background risk is handled by bounded image processing and explicit error state, not a silent whole-image motion. |
| D-030-23 | Use a 20-second default animation (bounded 15–30 seconds), with several authored part-specific action beats and a still ending; keep the camera fixed and do not start an infinite completion idle. | ACCEPTED 2026-09-28 | Direct owner clarification: multiple movements then rest, fixed camera; replaces the earlier short intro/idle direction. |
| D-030-24 | Prefer validated SAM2.1 part masks and derive bounded disjoint masks from the verified subject silhouette when usable model parts are missing; unsupported/invalid results do not silently become a whole-art animation. | REFINED_BY_D-030-25 2026-09-29 | The owner's latest no-fallback direction supersedes automatic legacy Pixi recovery while keeping deterministic mask processing and source preservation. |
| D-030-25 | Never automatically switch a failed Renderer V2 load to classic/V1 whole-art motion. Emit `PLAYBACK_FAILED`, retain the exact original image, and expose an explicit retry/error state. Continue to parse explicit legacy V1 launch contracts for compatibility. | ACCEPTED 2026-09-29 | Direct owner request: “ko đc fallback”. This resolves the earlier automatic V2-to-V1 fallback behavior without disguising failure or altering the original. |
| D-030-26 | Begin subject/part preparation after Gate A as already implemented; request final renderer package immediately after Gate-B approval, show a native loading overlay through Pixi artifact decode/inpainting, and allow up to 90 seconds before a retryable timeout. | ACCEPTED 2026-09-29 | Uses adult confirmation time for work and makes real preparation latency visible instead of displaying an empty stage or switching renderer. |
| D-030-27 | Reconstruct the background by local deterministic raster inpainting restricted to pixels inside the verified subject mask; never use a global four-corner paper-color check as the only eligibility test. | ACCEPTED 2026-09-29 | Handles photographed-paper shadows/framing while preserving mask boundaries and immutable original pixels; malformed/unsafe masks remain rejected. |
| D-030-28 | For high-pigment drawings, require credible low-chroma paper donors for reconstruction and explicit parent/part mask alignment checks; reject low-confidence cutouts without whole-art fallback. | ACCEPTED_UNDER_INTEGRATED_APPROVAL_2026-09-29; OFFLINE_IMPLEMENTATION_PARTIAL | The integrated approval covers synthetic donor/mask checks. Real drawing/source-mask attribution and Android visual acceptance remain open. |
| D-030-29 | Calibrate SAM 2.1 subject/part mask acceptance using reviewed synthetic ground truth and boundary/region metrics; evaluate bounded multimask candidate selection before any policy change. | ACCEPTED_UNDER_INTEGRATED_APPROVAL_2026-09-29; SYNTHETIC_SELECTOR_IMPLEMENTED | A typed model success is not proof of correct anatomy. Candidate selection remains bounded and Qwen remains single-pass. The synthetic benchmark is not real SAM accuracy; live-model/L4 and Android acceptance remain open. |
| D-030-30 | Allow one bounded backend AI call after Gate B to compose a structured visual Pixi show from the Gate-A subject/experience, verified rig capabilities, and rights-cleared individually approved sprite IDs; use evidence-bounded image processing to propose missing parts inside the accepted subject mask. | OWNER-APPROVED 2026-10-01 — IMPLEMENTATION IN PROGRESS | Owner approved Pixi sprite show plan revision 4; exact approval/hash in `approvals/TASK_APPROVAL.md`. Scope: visual beats only (voice/captions deferred), distinct companion sprites permitted, one bounded source crop may be used for advisory visual/behavior classification but cannot override Gate A/B, image-label conflict returns to caregiver confirmation, and failure produces a visible typed error without automatic retry or substitute show. Sprite gap audit covers supported behavior classes; walker/flyer are initial evaluation cases. Visual approval of existing assets is separately recorded under FEAT-028, but rights/runtime eligibility remain pending. |

## Clarification of full-topic coverage

The initial registry must include `butterfly`, `bird`, `flower`, `tree_branch`, `fish`, `biped`, `rigid`, `generic_organic`, and `unknown`. Topic aliases map into this registry using canonical Gate A semantics. A topic without a trustworthy specialized fit goes to `generic_organic`, `rigid`, or `unknown`, then to an appropriate lower visual tier. “Full-topic coverage” therefore means a defined, safe, testable outcome for every input—not unrestricted skeleton or motion generation.

These owner decisions and the remaining proposed architecture must be recorded in the relevant ADR before implementation that depends on them.

## Renderer donor recovery refinement — 2026-09-30

Under approved D-030-27/D-030-28 and the integrated cutout-quality scope, renderer reconstruction
now prefers local credible paper donors and may use a deterministic estimate from credible,
unmasked pixels elsewhere in the same source image only when local donors are absent. This estimate
seeds reconstruction but never expands the verified mask or changes pixels outside it. If no credible
unmasked paper samples exist, the typed failure remains. Synthetic regression evidence is
`E-030-FIX-014`; this is an implementation detail within the approved donor-quality scope, not a new
model/provider or fallback-tier decision.

## SAM 2.1 prompt-refinement decisions — owner-approved — 2026-09-30

- Keep the current SAM 2.1 Hiera Small/checkpoint path; do not fine-tune, change models, or add a
  checkpoint/dependency in this work.
- Generate positive/negative prompts only from high-confidence target/part evidence; use color/edge
  cues to propose or rank, never to silently synthesize or rewrite mask pixels.
- Permit at most two extra SAM predictions per source image for one refinement round; no generic
  retries, extra Qwen inference, concurrent GPU work, or relaxation of mask/fallback policy.
- State: APPROVED under plan revision 1 by the owner's “ok, implement” on 2026-09-30. Plan:
  `plan/SAM21_PROMPT_REFINEMENT_FOLLOWUP_20260930.md`. Approval hash/timestamp are recorded in
  `approvals/TASK_APPROVAL.md`.
- Implementation detail under that approval: only localized evidence keyed to the confirmed
  target is reused; otherwise deterministic image-ink proposals are prompt-only. Background
  negatives require neutral paper outside the target box. Part positive/correction seeds are
  removed unless they lie inside the already accepted subject silhouette. Iterative correction is
  limited to one subject and one part; it cannot alter the original or relax part-mask containment.

## Local preview activation — 2026-10-02

- Owner-approved local/test-only activation is separate from production runtime approval. Keep the
  environment gate default-off and reject the preview path outside `local`/`test`.
- Allowlist only cycles passing provenance/hash and conservative frame-alpha QA. Current allowlist:
  avian walker and corgi walker. Keep flyer and all other cycles blocked until their own evidence
  passes; never substitute a different cycle silently.
- Preserve production rights fields and manifest eligibility unchanged. A successful Metro bundle
  load is not proof of visible sprite playback; Android acceptance remains pending until a complete
  image flow visibly animates the selected cycle.

## Sprite-cycle renderer sidecar — accepted — 2026-10-02

ADR-030-09 accepts additive capability-bound cycle reads and Pixi V4 playback while preserving
V1/V2/V3. User visual approval does not clear legal/provenance, technical, catalog, renderer, or
Android gates; the expansion manifest remains runtime-ineligible. See
`adr/ADR-030-09-sprite-cycle-renderer-sidecar.md` and
`evidence/notes/SPRITE_CYCLE_PIXI_INTEGRATION_20261002.md`.

## Owner direction — adaptive original-art rendering — 2026-10-08 (plan approved)

- Preserve the source drawing and prefer a validated full part rig. When part masks are incomplete but the subject mask is valid, the desired presentation is a source-derived cutout in a topic-matched scene.
- Reuse the existing single post-Gate-B planner call. Let it select only among supported strategies and backend-supplied eligible scene candidates; the child-selected topic and Gate-A/Gate-B decisions remain authoritative.
- The exact plan revision 1 was approved by the owner at 2026-10-08 22:20 Asia/Saigon; its pre-approval hash and scope are recorded in `approvals/TASK_APPROVAL.md`. Implementation is authorized within that scope; live-provider execution and production activation remain gated.

## Adaptive rendering implementation — 2026-10-08

- Keep the approved one-call boundary. The worker packages the source crop and eligible candidate previews into one bounded contact sheet for the existing post-Gate-B planner request; preview bytes are transient and never placed in logs or evidence.
- Keep strategy and theme selection closed: the planner may select only a strategy supported by the validated rig tier and asset IDs from the backend allowlist. The child-selected topic plus Gate-A subject and Gate-B activity/objective remain authoritative.
- Preserve the existing part-mask containment/coverage threshold. An incomplete partition cannot be labeled `FULL_AUTO_RIG`; use the validated source cutout/topic-scene strategy when supported, otherwise cutout micro-motion or static source.
- Keep the source drawing intact as the lead subject. Theme assets render behind it, and `STATIC_SOURCE` disables source translation.
- Local implementation and verification are recorded in `evidence/notes/ADAPTIVE_ART_AND_TOPIC_SCENE_IMPLEMENTATION_20261008.md`. Live provider, rights/runtime, privacy/L4, and Android acceptance remain separate gates.

## 2026-10-09 — bounded Pixi planner responsiveness and output validation

- Keep the planner's single-call 120-second server deadline. Give only the mobile renderer-preparation command 150 seconds so it does not abort while the approved call is still running.
- Keep the Pixi V4 result schema and fail-closed behavior. Clarify exact schema enums, coordinate/timing bounds, and a three-beat response in the prompt; accept only a single optional outer JSON code fence before the same strict parser and validation.
- Split invalid-output logs into closed stage codes only. Do not log model output, prompt, image/crop, candidate metadata, or Pydantic input values.
- No retry or substitute show is added. A still-invalid response remains a visible typed failure.

## 2026-10-09 — Pixi schema-invalid prompt follow-up

- Prompt constraints must not contradict required schema values: require IDs from the supplied allowlist and forbid only invented/unlisted IDs. State JSON array and nullable-field shapes directly.
- If schema validation still fails, logs may include only a bounded allowlisted schema path and Pydantic error type; never include input values or error messages.
- Evidence: `evidence/notes/PIXI_SCHEMA_INVALID_PROMPT_CONTRADICTION_FIX_20261009.md`.

## 2026-10-09 — Pixi root-validator failure follow-up

- Express the still-tail rule as `lastBeat.endSeconds <= durationSeconds - 2` and require unique selected IDs, with every supplemental beat ID present once in the list.
- Map only known Pydantic validator messages to fixed diagnostic codes; retain generic `root:value_error` for unknown messages and never log the raw message.
- Evidence: `evidence/notes/PIXI_ROOT_VALIDATOR_DIAGNOSTICS_AND_CONSTRAINTS_20261009.md`.

## 2026-10-09 — Pixi numeric still-tail prompt bound

- Render duration stays contract-authoritative; include its actual numeric value and `duration - 2` final-beat cutoff in the one planner prompt to avoid symbolic ambiguity.
- Continue to reject invalid output. Never clamp, rewrite, retry, or replace a planner response.
- Evidence: `evidence/notes/PIXI_DYNAMIC_STILL_TAIL_BOUND_20261009.md`.

## 2026-10-09 — Pixi planner capability whitelist

- Derive the V4 prompt's render strategy and source-action options from the same deterministic rig-tier/part-role rules used by the backend compiler.
- Whole-cutout tiers may use only whole-subject actions; static source may use only NOTICE/SETTLE; articulated actions require their corresponding verified role and FULL_AUTO_RIG. BBOX_VISUAL_FOCUS supports STATIC_SOURCE only.
- Continue to fail closed if the planner violates the whitelist and log only a fixed internal reason code.
- Evidence: `evidence/notes/PIXI_RIG_CAPABILITY_PROMPT_FIX_20261009.md`.

## 2026-10-09 — Pixi final-beat output constraint

- Keep the existing `SETTLE` final-beat invariant and strict fail-closed validator.
- State the invariant by exact array index and field values after the full V4 request context so the planner receives it as the final instruction; do not normalize a malformed model response.
- Evidence: `evidence/notes/PIXI_FINAL_SETTLE_PROMPT_FIX_20261009.md`.

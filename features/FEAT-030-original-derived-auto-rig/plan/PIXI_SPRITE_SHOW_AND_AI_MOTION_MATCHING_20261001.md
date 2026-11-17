# Pixi sprite show and AI motion matching

- Feature: FEAT-030 original-derived auto-rig, integrated with FEAT-028 approved Pixi asset library
- Revision: 4
- Status: APPROVED FOR IMPLEMENTATION
- Date: 2026-10-01
- Approval: owner-approved revision 4 on 2026-10-01; exact pre-approval hash and implementation boundary are recorded in `approvals/TASK_APPROVAL.md`

## Owner direction captured

1. Use sprite assets; the owner has now visually approved all 144 currently catalogued frames. Keep rights clearance and runtime eligibility as separate gates.
2. If SAM does not yield enough useful part masks, try image-processing-based part separation.
3. AI may classify the confirmed subject's movement behavior, propose how it should move, choose from eligible sprites to compose into the Pixi scene, and shape a content-bearing PixiJS show—not only a basic motion loop.

## Problem and current baseline

- The existing Pixi renderer already turns validated source masks into source-derived sprites. With only a subject mask it can move the whole cutout gently, but it cannot honestly animate separate legs, wings, or other parts.
- The full-rig path requires validated part masks. Current SAM and bounded deterministic image-processing paths can still fail to produce enough usable parts for a drawing.
- Existing animation plans are mostly fixed archetype tracks; there is no structured AI-authored, content-bearing show contract that combines the confirmed drawing subject, the selected experience, motion profiles, and supplemental sprites.
- FEAT-028 has generated atlas drafts, but the current feature record says those sprites are review-pending and not available to runtime. They must not be treated as approved merely because an AI ranks them.

### Confirmed repository findings for revision 4

- FEAT-028 contains 144 catalogued sprite frames across 24 atlas sheets. The owner visually approved all 144 on 2026-10-01; the decision and exact catalog hash are recorded in FEAT-028 `assets/REVIEW.md`. Rights clearance is still pending, and catalog entries remain `runtimeEligible=false`; therefore none is currently eligible for app/runtime use.
- The current FEAT-028 candidate builder is deterministic, approved-only, text-only and bounded; it is not wired to a live model or Pixi runtime. It returns a typed no-match when no approved entries qualify. Until rights/state are cleared, the show planner must see an empty eligible list, not the 144 visual-only approvals.
- Existing atlas entries are single static drawings, not walk-cycle or flight-cycle frames. The motion-effects atlas contains static effects. They can be positioned/translated as whole sprites, but do not provide limb/wing animation by themselves.
- Current FEAT-030 `RendererLoadCommandV2` and `VisualAnimationPlanV2` do not carry supplemental sprite references or authored scene beats. FEAT-028 prohibits silently changing frozen FEAT-018 contracts; a separately reviewed additive contract/ADR is required before renderer integration.
- `derive_part_masks_from_subject_mask()` currently assigns pixels by nearest fixed archetype anchor and returns a constant confidence of `0.7`. That can manufacture plausible-looking regions without image-boundary evidence. This heuristic is not acceptable as proof of anatomical part masks and must be benchmarked/replaced or restricted to non-articulated visual proposals.
- The existing rig archetype (`bird`, `fish`, `biped`, etc.) is not a locomotion class. `walker`/`flyer` must be a separate behavior label. Gate A remains the authority for the represented subject; the new AI is for behavior/show planning, not subject rediscovery or activity reselection.
- The atlas style is consistent flat digital illustration, but does not automatically match every crayon/pencil drawing. Composition must preserve the child's drawing as the lead visual and apply an explicit compatibility decision; AI selection alone does not prove a style match.

## Goal

Create a safe, explainable Pixi show that preserves the child's drawing as the main character, improves part extraction when possible, and composes it with a small, reviewed library of supplemental sprites. AI may propose a short story/action sequence and rank compatible approved assets; deterministic validators and Pixi allowlists retain final authority over what can run.

## Proposed scope

### 1. Review and curate the sprite library

- Treat the existing owner visual approval as recorded, but keep every current asset blocked from runtime until rights/provenance review is completed and `runtimeEligible` is deliberately enabled through the catalog workflow.
- Build a gap matrix across the supported subject/archetype registry and its distinct behavior classes—not just `walker` and `flyer`—plus scene-support roles (`environment`, `prop`, `effect`, optional `companion`). Include applicable classes such as walking (biped/quadruped), flying, swimming, crawling/slithering, and rolling, but only where the source subject and renderer can truthfully support them. Record per class/role whether the catalog supplies a static sprite, animation-ready frames, or no suitable asset. Start implementation/evaluation with walker and flyer as representative cases, then extend from measured coverage gaps.
- Reuse existing approved static props/background/effects where they pass the child's drawing style/role fit. Do not describe static icons as walk/flight cycles. If motion-specific assets are needed, create new isolated sequences under FEAT-028 `assets/generated/` with explicit frame IDs, pivots, baseline/ground contact, loop boundaries, transparency/crop safety, source/brief/generator, timestamp, hash, and rights record.
- The requested expansion is gap-driven, not “generate a larger catalog” by default. Add only missing assets required by approved behavior/scene examples, across the supported behavior classes identified by the gap matrix; each new frame/sequence requires its own visual approval before promotion. Do not create every class up front without a concrete scene/test need.
- Extract/copy only selected approved frames to an optimized runtime package (or retain a measured approved atlas); never ship all 24 atlases by default. Record decoded dimensions, bytes, load time, and memory. Use lazy selection/loading and an explicit maximum selected-asset count/byte budget fixed from Android measurements.
- Preserve the original drawing as the primary subject. The owner permits distinct companion-character sprites. They may accompany or interact with the drawing, but may not replace, repaint, duplicate, or silently cover the confirmed subject; keep their count within the measured scene/asset budget.
- AI receives only a compact manifest of eligible approved asset IDs and metadata; it cannot invent an asset ID, load an unapproved path, or approve assets.

### 2. Improve part-mask recovery

- Keep validated SAM 2.1 part masks as the preferred source. When the accepted subject mask exists but requested parts are missing, run a bounded image-processing proposal stage inside that silhouette; evaluate connected components, source-color/edge boundaries, local contrast and archetype role anchors as cues, not as independent semantic truth. Do not add a new dependency until the benchmark/ADR justifies it.
- Compare the current nearest-anchor/Voronoi splitter against evidence-aware proposals. The fixed `0.7` confidence must be removed; source method, parent-mask hash, algorithm/parameter version, calibrated quality signals, and rejection reasons must be carried in provenance. A spatial split without visible boundary support cannot enable limb/wing articulation.
- Define role templates separately from motion classes: e.g. `fore_leg`, `hind_leg`, `wing`, `body`, `head`. All proposed parts must map to visible source regions, retain the accepted subject mask as parent, obey registered overlap/seam limits, avoid duplicate/empty masks, and pass alignment/edge and minimum-area checks before a full rig can be considered.
- Add synthetic, layered ground-truth fixtures for upright and quadruped walkers, birds/insects, and representative touching/high-pigment drawings. Freeze development thresholds before held-out scoring. Report IoU/Dice, boundary F-score, false inclusion/exclusion, thin-detail recall, disconnected/fragmented regions, role correctness, and parent containment separately; aggregate IoU cannot hide lost legs/wings.
- If image processing cannot establish a trustworthy part, do not promote a full rig. A supplemental approved sprite may still contribute a scene beat, but it must not be presented as an extracted part of the child's drawing.
- If no valid part masks survive, retain the existing honest subject-only capability. Do not claim a gait or wing articulation that the package cannot render, and do not automatically switch to Renderer V1.

### 3. Introduce typed behavior profiles and AI-authored show plans

- Define a versioned planner output (working name `PixiShowPlanV1`) separately from the renderer command. It carries `behaviorClass`, confidence/reason code, an ordered bounded beat list, approved asset IDs (possibly empty), allowlisted interaction/action IDs, and duration/rest policy. It contains neither executable JS nor arbitrary Pixi keyframes.
- Gate A supplies the authoritative confirmed subject and visible tags; Gate B supplies the already-selected ExperienceSpec/activity. The multimodal planner may independently classify what the crop appears to show and suggest a behavior class as a consistency check, but it cannot silently replace Gate A, change activity membership/ranking, override caregiver conditions, or readjust the Montessori objective. If the visual subject hint conflicts with the confirmed subject, return a typed conflict and require caregiver reconfirmation at the existing subject-confirmation step before playback.
- After Gate B, make at most one backend-only multimodal AI planning request, using the minimum needed context: confirmed subject label/tags, selected activity and objective labels, validated rig tier/part roles/quality state, a bounded local list of eligible asset descriptors, style/placement constraints, and a bounded image crop from the already-confirmed source. Prefer a server-created crop around the confirmed subject; include the full source only when the planner needs surrounding visual context and the existing inference privacy gate allows it. The image may independently classify the apparent subject, behavior and visual fit as advisory evidence, but cannot change Gate-A subject authority or Gate-B activity. A subject mismatch stops show planning and asks the caregiver to reconfirm through the existing Gate-A step. Never send the child's name/ID, voice transcript, free-form profile, secret, or provider endpoint. Do not persist the crop or include image bytes/URLs in logs. No concurrent Qwen/SAM inference and no automatic retries.
- Build the candidate list deterministically before inference: require rights-cleared `APPROVED/APPLIED`, `runtimeEligible=true`, compatible style and role; rank by Gate-A topic + selected Gate-B context; cap to a small top-K chosen in the contract ADR. If no asset qualifies, call AI with no asset candidates only if story generation without supplements has been approved; otherwise return a typed `NO_ELIGIBLE_ASSETS` outcome without fabricating content.
- AI classifies behavior from confirmed subject semantics plus verified part capabilities, using a versioned extensible registry (initial examples: `walker`, `flyer`; potential later classes: `swimmer`, `crawler/slitherer`, `roller`). It may not classify the structural rig from a sprite ID alone. If text and capability disagree (e.g. “fly” but no supported flyer capability), backend rejects or maps to a lower truthful behavior, never promotes a tier.
- AI returns only enums/IDs and small bounded values: an optional `visualSubjectHintId` from a server-supplied subject ontology, behavior class, beat template/action IDs, target role (`source_subject` or an eligible supplemental ID), motion preset IDs, ordered time slots, and no more than the registered sprite/beat limits. Use a reviewed interaction grammar (e.g. enter → notice → approach/interact → settle) rather than open-ended scene code. Every beat must map to a deterministic compiler/template and an allowed Gate-B objective.
- The backend validates schema, Gate A/B references, activity/objective integrity, approved ID subset, sprite roles/style, action-to-part capability, no unsupported collision/occlusion, timing, placement bounds and policy. A deterministic compiler expands the validated intent into supported renderer tracks; Pixi never interprets model-generated code or arbitrary URLs.
- Initial action registry includes `walk_step/weight_shift` for walker and `flap/glide` for flyer. Articulated gait/wingbeats require corresponding valid source-derived parts or explicitly approved animation-ready sprite sequences. Whole-source translation may be used only within the existing fixed frame and motion envelope; do not claim separate leg/wing motion when absent.
- “Content-bearing show” in this draft means visual story/action beats composed in Pixi only. Captions and generated voice/narration are deferred to a later, separately planned update; no new narration or caption UI is included now.
- The single post-Gate-B multimodal request is serialized behind segmentation and other Qwen work. Establish timeout, latency and peak-VRAM budgets from the L4/Android benchmark before live activation; show the existing loading state during planning. On timeout/invalid output, return a visible typed error and preserve the original; never silently substitute V1, whole-art motion, or a deterministic show. No automatic retry; a retry, if offered, is an explicit user action.

### 4. Preserve playback and provenance invariants

- Keep the source drawing immutable; all masks, part sprites, background patches, show plans, and placements retain source/asset provenance.
- Keep the camera fixed, use the existing 15–30 second bounded duration (20 seconds default), several beats followed by a still ending, and no infinite idle, whole-art zoom, or whole-art rotation.
- Keep all provider calls backend-side. The mobile app receives only a validated playback contract/capability and approved asset references.
- Pixi accepts only known contract versions, motion primitives, rig roles, and approved asset IDs. Malformed, unsupported, stale, or provenance-mismatched inputs fail visibly and preserve the original image.

## Phased delivery and go/no-go gates

| Phase | Deliverable | Go/no-go gate |
|---|---|---|
| 0. Product/architecture freeze | Record the owner decisions below; write ADR and versioned contract design; identify which feature owns each schema/adapter and asset state. | Do not alter frozen FEAT-018 V1/V2 contracts until the additive migration and compatibility plan is approved. |
| 1. Asset rights + gap audit | Confirm FEAT-028 rights evidence for existing owner-visual-approved frames; create role/style/motion gap matrix; decide whether and which new sequences are required; prepare visual contact sheets per frame. | Only rights-cleared, separately approved frames become candidate-eligible. If no eligible assets, do not claim sprite composition is live. |
| 2. Mask quality | Compare SAM masks, current anchor splitter, and evidence-aware bounded image processing on synthetic development/held-out fixtures; record provenance/metrics and reject weak parts. | Freeze thresholds before held-out results; no full-rig enablement if role/detail quality fails. No model/fine-tune/checkpoint change. |
| 3. AI show planner | Add application port, backend adapter, deterministic approved-only candidate builder integration, bounded multimodal prompt/output schema, validator and typed failures. Use a fake runner with image/crop fixtures in tests; never commit real child images. | No live provider default until latency, output-validity, privacy/retention and VRAM gates pass. AI output cannot alter Gate A/B. |
| 4. Versioned renderer integration | Add the approved additive renderer contract/sidecar, capability-bound sprite resolution, deterministic intent-to-motion compiler, loading/progress and Pixi scene composition. Preserve V1/V2 parsers unchanged. | Reject unknown/stale asset IDs, refs, hashes, contract versions and action IDs. No asset URL/path is supplied by model/mobile. |
| 5. Offline visual/device verification | Render synthetic bird/flyer and quadruped-walker scenes using source-derived masks plus selected supplements/companion characters; test both full-rig and subject-only capability; validate load/error/manual-retry/pause/seek/orientation/app-resume. | Visual review confirms original remains primary, companions do not obscure it, no clipping/ghosting/overlap, fixed camera and a still ending. No release activation without fresh Android review. |
| 6. Gated live rollout | Owner-controlled test with eligible approved assets; measure single-call latency, timeouts, peak GPU memory, asset transfer/decode, and Pixi frame/render behavior; canary/rollback plan. | Record live evidence separately from synthetic tests and keep default disabled until ADR thresholds are met. |

## Out of scope

- Fine-tuning SAM, migrating to SAM 3/3.1, downloading checkpoints, changing the current SAM model, or adding unapproved dependencies/providers.
- Unbounded AI/SAM retries, a separate extra Qwen vision call beyond the one bounded show-planning request, concurrent GPU inference, or bypassing the existing L4/ADR activation gates. The single multimodal show-planning request after Gate B must be separately measured before activation.
- AI-generated replacement artwork, arbitrary JavaScript/animation code, unreviewed sprites, changes to Gate A/B authority, or automatic V1 recovery.
- Voice narration, TTS, subtitle/caption UI for this increment (deferred to a later plan), caregiver controls, and blanket runtime activation of the full 144-frame catalog. New assets are limited to demonstrated movement/scene gaps, not a catalog expansion for its own sake.
- Use of real child drawings or personal data in repository fixtures/evidence.

## Acceptance criteria

- AC-SHOW-01: The existing 144 visual approvals are distinguished from rights status; none is runtime eligible until provenance/rights state is cleared. Every new runtime frame has per-frame review, provenance, bounds/hash, and approved/applied state. Unapproved IDs fail server-side and renderer-side.
- AC-SHOW-02: The child's source drawing remains the primary, byte-preserved source. Supplemental sprites never replace it, and provenance links source-derived versus supplemental content distinctly.
- AC-SHOW-03: When SAM part masks are absent, bounded image processing proposes only source pixels inside a validated parent subject mask; malformed, duplicate, role-incompatible, or low-quality parts do not enter `FULL_AUTO_RIG`.
- AC-SHOW-04: Synthetic ground-truth evaluation reports region/boundary metrics, thin-detail recall, false inclusion/exclusion, and correct part-role assignment by archetype; thresholds are frozen before held-out scoring, and no synthetic metric is described as real SAM accuracy.
- AC-SHOW-05: The AI planner emits only the versioned intent schema. Unknown asset IDs, unsupported actions, prompt injection in metadata, contract drift, unsafe duration, activity/subject drift, and motion unsupported by the verified rig are rejected or safely normalized before renderer delivery.
- AC-SHOW-06: Walker/flyer behavior is capability-aware: articulation only occurs when validated corresponding parts exist; subject-only mode never claims separate limb/wing motion.
- AC-SHOW-07: A validated show includes multiple semantically relevant visual beats, uses approved sprites only, remains 15–30 seconds (20-second default), holds still at the end, and keeps the camera fixed without whole-art zoom/rotation or infinite idle.
- AC-SHOW-08: AI planning failure returns a visible typed error, preserves the original image, and never triggers V1, a deterministic substitute show, or an unlabelled downgrade. No automatic retries; any retry is explicitly user-triggered.
- AC-SHOW-09: Backend, contract, renderer, security validation, and synthetic visual review pass. Live model latency/VRAM, Android playback, and actual asset composition are separately reported and remain gated until owner review.
- AC-SHOW-10: Repository security validation passes; no secrets, real child data, provider payloads, or unreviewed assets are committed or referenced at runtime. Runtime image crops are transient and excluded from logs/evidence.
- AC-SHOW-11: Frozen FEAT-018/FEAT-028 V1/V2 schemas remain unchanged. Any sprite/story renderer data uses a separately approved additive version/sidecar, contract tests, old-client compatibility tests, and a recorded ADR/SRS addendum.
- AC-SHOW-12: Runtime loads only the selected bounded asset subset lazily; catalog/atlas bulk download is never required. Measure package bytes, decoded texture memory, asset load/decode time, planner latency and render-frame performance on the agreed Android target before choosing numeric budgets.
- AC-SHOW-13: AI failure is observable with a typed state and sanitized log; the UI preserves the source and reports the error without an automatic retry or substitute animation. No silent V1 fallback, invented content, or misleading “AI-ready” state.
- AC-SHOW-14: Synthetic evaluation distinguishes static supplement composition from actual source-derived articulation. A static single-frame sprite moving as a whole is not counted as a walk/flap cycle.
- AC-SHOW-15: The asset gap matrix covers every behavior class in the supported subject/archetype registry and scene-support role. New sprite sequences are added only for evidenced gaps, receive per-frame visual/provenance review, and are never represented as supporting a class/behavior that the renderer cannot actually play.
- AC-SHOW-16: If the planner's visual subject classification conflicts with Gate A, it returns a typed conflict and routes to caregiver reconfirmation; it never silently changes the confirmed subject or proceeds with a mismatched show.

## Risks and controls

- **Visual mismatch:** Sprite art may clash with the child's drawing. Start with a tiny curated set, preview in context, and require per-asset visual approval.
- **AI overreach:** A planner may request unsupported actions/assets. Use schema validation, allowlists, provenance checks, and capability-aware normalization; never execute model-generated code.
- **False anatomy from image processing:** Texture boundaries can resemble limbs/wings. Keep proposals inside the parent mask, test thin/touching shapes, and refuse full-rig promotion below registered criteria.
- **Latency/VRAM:** SAM refinement and a show-planning call can add latency or contend with Qwen. Keep GPU work serialized, use one bounded planning call after Gate B, and measure before enabling live defaults.
- **Image privacy:** A source crop may be sent to the configured backend model for the one planning request. Keep it transient, minimize crop area, disclose/guard the provider data path, and gate live activation on retention/privacy review; never add real drawings to fixtures or logs.
- **Scope creep in “content”:** This revision defines content as visual beats only. Narration and captions are deferred to a later update.
- **Rights/approval ambiguity:** Owner visual approval is recorded, but the app catalog remains blocked until per-frame provenance/rights review and runtime state are explicitly completed.
- **Static sprite mistaken for rig:** Existing catalog frames are one-pose drawings, not animation sequences. Require source part masks or separately approved animation-ready sequences for articulation.
- **Unbounded scene/story:** Use an allowlisted visual-beat grammar, Gate-B grounding, an exact beat/asset cap, fixed duration and no open-ended scene code.
- **Behavior/archetype confusion:** Keep movement class separate from structural rig archetype; only validated subject semantics and mask capability authorize a class/action.

## Required verification and evidence

- Synthetic fixtures and reference masks only; no real child drawing in repository/evidence.
- Store manifests, review decisions, hashes, test output, approved composition previews, schema-invalid cases, and sanitized latency/VRAM results under feature-local `evidence/` directories. Asset approvals belong in FEAT-028; rig/show implementation evidence belongs here.
- Run `python tools/validate_repository_security.py` before any commit/push.
- No SAM/Qwen/Lightning runtime call, asset promotion, code change, or model activation is part of this planning step.

## Approval gate

This is a proposed scope only. The owner has separately approved the visual appearance of the existing 144 frames; this does not clear rights or make those entries runtime-eligible. The four product choices below are now resolved, but implementation is still not approved. Before implementation, the owner must approve this exact plan revision; then record exact plan hash/approval in FEAT-030 `approvals/TASK_APPROVAL.md`. FEAT-028 rights/provenance and any newly generated frame approvals remain separate prerequisites for runtime selection. The multimodal AI-planning contract/provider budget and existing L4/ADR gates must be recorded before live activation.

## Owner decisions resolved — 2026-10-01

1. **Show content:** visual beats only for this increment; captions and voice/narration are deferred to a later update.
2. **Companions:** distinct approved sprite characters may accompany the drawing, subject to the scene/asset budget; they cannot replace, duplicate, or obscure the confirmed subject.
3. **Image input:** the single post-Gate-B planner request may include a bounded crop (preferred) or, only when needed and allowed by privacy controls, the source image. It may independently classify the apparent subject/behavior and assess style fit as advisory evidence; conflicts with Gate A require caregiver reconfirmation, and it cannot override Gate A or Gate B.
4. **Planner failure:** return a visible typed error, preserve the original image, do not automatically retry or play a substitute show. Any retry is explicit user action.

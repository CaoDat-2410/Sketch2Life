# Adaptive original-art rigging and topic-matched Pixi scenes

- Feature: FEAT-030 original-derived auto-rig, integrated with FEAT-028 approved Pixi assets and FEAT-018 live-image flow
- Plan revision: 1
- Status: APPROVED FOR IMPLEMENTATION
- Date: 2026-10-08
- Owner direction: attempt both subject-background extraction and body-part separation; prefer separate-part motion when masks validate; if full rigging is unsupported, keep the verified original-subject cutout and compose it into a Pixi scene matching the child's chosen topic; let AI choose among supported rendering strategies; reuse the existing single post-Gate-B planner request.
- Relationship to prior approval: additive follow-up to `PIXI_SPRITE_SHOW_AND_AI_MOTION_MATCHING_20261001.md` revision 4. It supersedes the prior no-substitute rule only for the explicit incomplete-part-mask -> verified-subject-cutout/topic-scene path described here. Other planner failures remain visible and fail closed.

## Goal

Make the child's original drawing move as separate parts when validated masks support it. When a full rig is not supportable but the subject mask is valid, preserve the complete drawing as a cutout and compose it into a Pixi scene selected for the child's chosen topic. Reuse the existing single post-Gate-B planner request to recommend a bounded rendering strategy and compatible scene composition.

## Confirmed baseline

- `derive_part_masks_from_subject_mask()` proposes only large connected-color regions with image-boundary evidence inside the accepted subject mask. A same-color silhouette with no internal boundary returns no parts.
- `FULL_AUTO_RIG` requires independently validated part masks. When parts are unavailable, current runtime can only claim subject-only cutout motion; it must not claim limb or wing articulation.
- The existing post-Gate-B planner sends a bounded source crop, confirmed subject and Gate-B activity/objective context, rig tier/part roles, and a bounded candidate list. Its current result selects behavior, assets, and visual beats; it has no explicit renderer-strategy or scene-theme decision.
- Candidate descriptors currently contain text metadata rather than preview pixels, so the existing request cannot directly compare the drawing's visual style with a candidate scene image.
- Existing FEAT-028 rights, provenance, catalog, and runtime-eligibility gates remain closed for production. No live provider request or fresh Android scene playback is part of this plan.

## Scope

### 1. Prefer truthful source-part motion

- Continue to use the approved segmentation/mask path and bounded image-processing proposals inside the verified parent subject mask.
- Only deliver `FULL_AUTO_RIG` when the required independent masks pass registered containment, geometry, role, boundary, detail, and quality checks.
- Improve or constrain part proposals using synthetic, layered drawings and reviewed reference masks. Record mask provenance and per-part rejection reasons. Never manufacture anatomical boundaries from anchors alone.
- Do not add another SAM/Qwen call, model/checkpoint, dependency, fine-tuning step, or unbounded retry loop in this increment.

### 2. Fall back to the original subject cutout and a topic-matched scene

- If a full part set is unavailable but the complete subject mask passes validation, retain the verified source-derived subject cutout and request a scene composition in the existing planner call.
- Supply the child's chosen topic from the current workflow as an authoritative input, together with Gate-A-confirmed subject context and Gate-B-selected activity/objective. The planner may select a visual theme and compatible scene assets; it cannot change the chosen topic, confirmed subject, activity, or learning objective.
- Extend the planner through new versioned request/result contracts. The result may select only bounded strategies supported by verified capabilities, such as `FULL_AUTO_RIG`, `CUTOUT_TOPIC_SCENE`, `CUTOUT_MICRO_MOTION`, or `STATIC_SOURCE`.
- Let the planner compare the minimized source crop with small previews of at most the existing bounded candidate set so it can assess visual fit as well as topic fit. Candidate previews and the source crop stay within one aggregate request-size limit set in the contract/ADR; both are transient and excluded from logs/evidence.
- Candidate scene/background/prop/effect/companion assets must be supplied by the deterministic backend allowlist and pass FEAT-028 rights, provenance, style, topic, and runtime-eligibility checks. The model cannot invent IDs, URLs, or assets. If no compatible scene asset is eligible, a truthful cutout-only or static-source strategy may be selected if supported; otherwise preserve the original and return a visible typed failure.
- The child's original drawing remains the lead subject. A supplemental sprite or scene may not replace, repaint, duplicate, or obscure it. Cutout-only movement is described as whole-subject motion, never as articulation.

### 3. Keep safety and decision authority deterministic

- AI chooses only among the closed strategy/theme/asset options supplied in its one request. Backend validators check mask readiness, selected topic, activity/objective, style/role compatibility, asset IDs, action support, scene budget, and contract version before renderer delivery.
- Gate A remains authoritative for the subject; Gate B remains authoritative for the selected activity and objective. AI scene planning is presentation-only.
- Incomplete part masks plus a valid subject mask authorize the specific `CUTOUT_TOPIC_SCENE` fallback above. Invalid/absent subject masks, mismatched subject/topic, invalid AI output, planner unavailability, or no safe supported strategy preserve the source and produce a visible typed error. Do not retry automatically or substitute an unrelated show.
- Keep the existing one-call post-Gate-B boundary. Do not add a separate AI query.

## Acceptance criteria

1. The uploaded source remains immutable and hash-linked to every derived subject/part mask and renderer package.
2. Part motion is enabled only when each required part mask is independently validated and the role/geometry/detail checks pass; unsupported anatomy never enters a full rig.
3. When parts are incomplete but the parent subject mask is valid, the planner can choose a topic-matched scene using only the child's chosen topic, confirmed subject, Gate-B activity/objective, and supplied eligible candidates.
4. The planner receives enough bounded visual information to assess candidate fit, returns a closed versioned strategy/theme/asset plan, and cannot introduce arbitrary asset IDs, URLs, code, topics, subjects, activities, or objectives.
5. `CUTOUT_TOPIC_SCENE` preserves the original drawing as the main subject. Any whole-subject movement is not represented as limb/wing articulation.
6. Invalid masks, incompatible or unapproved assets, planner failure, schema errors, topic/activity drift, and missing safe strategies fail closed with the original preserved, a typed result, and no automatic retry.
7. Synthetic tests cover clean part masks, partial masks, same-color silhouettes, background extraction, child-topic/scene matching, visual-style mismatch, empty candidate lists, hallucinated IDs, and unavailable planner behavior. No real child drawing is used in tests/evidence.
8. Additive contract compatibility, renderer behavior, privacy/retention, aggregate request size, and Android visual acceptance are recorded separately. No live model/provider activation or production asset enablement occurs until its existing FEAT-028/FEAT-030 gates pass.

## Verification and evidence plan

- Inspect current auto-rig outputs and planner construction using synthetic fixtures only.
- Add focused domain, application, contract, planner-adapter, and renderer checks after approval.
- Render representative part-rig and cutout-scene cases and record the source/derived relationship, topic match, style fit, masks, and scene selections under FEAT-030 evidence.
- Report synthetic mask metrics separately from any later held-out/SAM quality result.
- Keep live provider calls, Android visual acceptance, rights clearance, and production rollout as separate gates.

## Non-goals

- Generating replacement artwork or arbitrary scene images with AI.
- Selecting a new segmentation or multimodal model, running extra model calls, changing provider infrastructure, or invoking a live provider during implementation.
- Changing Gate-A/Gate-B authority, frozen FEAT-018 contracts, source artwork, asset rights, FEAT-028 runtime eligibility, or production rollout.
- Claiming full articulation from a subject-only cutout or a static supplemental sprite.

## Approval gate

This exact plan revision was approved by the owner on 2026-10-08 22:20 Asia/Saigon (2026-10-08 15:20 UTC). Pre-approval SHA-256: `FC634C8899AB4B4FC618AF8311BDBD9C7391CC0C952C2F24AF60EC33D12428EF`. The approval ledger records the approval. Existing FEAT-028 asset-rights and FEAT-030 provider/Android gates remain mandatory.

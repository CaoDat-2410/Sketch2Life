# Integrated child-profile personalization and auto-rig quality plan

- Coordinating feature: FEAT-018 live-image supervised flow
- Participating features: FEAT-020 semantic catalog/backend recommender; FEAT-030 SAM 2.1 and original-derived auto-rig; renderer consumer in FEAT-018
- Revision: 1
- Status: APPROVED_FOR_IMPLEMENTATION; IMPLEMENTATION_IN_PROGRESS
- Approval model: one owner approval for this integrated scope; technical workstreams stay independently testable and are released together only after both pass.
- Detailed workstream plans: `CHILD_CONTEXT_MONTESSORI_PERSONALIZATION_PLAN_20260929.md` (this folder), `../../FEAT-030-original-derived-auto-rig/plan/SAM21_MASK_ACCURACY_AND_AUTO_RIG_QUALITY_PLAN_20260929.md`, and the related high-pigment reconstruction plan `../../FEAT-030-original-derived-auto-rig/plan/HEAVY_PIGMENT_MASK_ALIGNMENT_AND_BACKGROUND_20260929.md`.

## Owner question and outcome sought

Deliver one coordinated increment that lets an adult edit an explicit test profile for a child and
see how it changes Montessori activity recommendations, while improving SAM 2.1 subject/part-mask
quality and the renderer's handling of pigment-heavy cutouts. The original drawing and adult gates
remain authoritative. No AI success status may be mistaken for correct segmentation, and no
psychological attribute may be inferred from the drawing, narration, voice, or behavior.

The owner confirmed one integrated plan and one approval, the profile fields, session-only handling
for the current increment, and editor placement on 2026-09-29. This revision records those choices.
No implementation is authorized before explicit approval of its final hash.

## Current-state findings

### Montessori and child profile

- `resolve_activity_options_v2` currently ranks by confirmed visual/narrated scene, age and catalog
  match; it does not take a persisted child profile or longitudinal outcomes.
- The resolver assigns an anchor-order `child_interest_alignment` proxy (primary versus secondary
  scene anchor). This measures relevance to the current picture, not the child's explicit or
  historical preference.
- The selected child in the mobile demo is mock data. The P1 workflow supplies age and confirmed
  anchor/narration context; feedback can record completion, interest and independence, but the
  recommender does not consume a child's history and completion is not mastery.
- The current source loads a 100-profile MVP catalog plus 200 curated variants. Catalog size alone
  does not resolve the lack of explicit, trustworthy child context or prove metadata coverage.
  Measure exact gaps before adding entries.
- This recommendation path is deterministic semantic/catalog matching, not a Qwen call. The UI
  should make clear that testing a profile changes recommender inputs/ranking; it does not retrain
  Qwen or add an extra vision inference.

### SAM 2.1 masks and renderer

- The SAM adapter returns one candidate per prompt and checks structural properties, but no
  calibrated mask-boundary/reference-ground-truth score currently establishes anatomical accuracy.
- The worker batches existing grounded subject/part prompts and reuses image embedding. A model
  `SUCCEEDED` result can still be structurally valid yet omit or include the wrong pixels.
- Existing part containment/overlap and package gates are useful but do not replace pixel-level
  benchmark measurements. High-pigment cutout/background inpainting is a separate consumer issue
  with its own plan and must be scored separately from SAM mask quality.
- No matching source/mask or live runtime artifact was available for this documentation review.
  Screenshots and child artwork are not placed in Git.

## Proposed integrated scope

### Workstream A — adult-editable profile and recommender

1. Add an adult/Guide-facing profile editor and an edit entry next to the child selector at the very
   beginning of the main flow. The in-flow edit is available only at child selection, not midway
   through an active child workflow. Provide an explicit active-child/test-profile selector,
   editable values, clear/reset controls, and a review of effective values before requesting
   activity options.
2. The approved editable fields for this scope are current age, child-stated/adult-confirmed
   interests, explicit dislikes/avoidances, adult/Guide-confirmed accomplishments/progression with
   date and provenance, current readiness and available materials, and optional explicitly selected
   non-clinical learning supports. Do not include inferred mental state, diagnosis, personality or
   emotion.
3. Pass explicit profile context through a reviewed versioned contract to the deterministic
   Montessori resolver. Preserve Gate A and Gate B. Apply safety, age, supervision, prerequisites,
   readiness, available materials and approved explicit avoidances as eligibility constraints
   before personalized ranking. Explain each recommendation's profile/topic signals and exclusions.
4. Distinguish scene relevance from personal preference in naming, scoring and evidence. Never infer
   mastery from completion alone; only use adult/Guide-confirmed milestones or explicitly observed
   progression under the policy approved for this plan.
5. Show a testable before/after recommendation comparison or equivalent clear reason/explanation
   view, and a deterministic reset/no-profile path so the owner can verify that changing one profile
   field has a bounded, understandable effect.
6. Audit all current catalog profiles/variants for the dimensions above. Add reviewed entries only
   for named measured gaps; do not expand catalog size for its own sake.

### Workstream B — SAM 2.1 mask precision and renderer quality

1. Establish a reviewed, synthetic, pixel-ground-truth corpus spanning all registered archetypes,
   high-chroma crayon, weak/no outlines, touching objects, thin details, shadows, overlap, and
   incomplete shapes. Keep child media out of repository evidence.
2. Measure the current SAM/prompt/part pipeline using per-class IoU/Dice, boundary F-score, thin
   detail recall, false inclusion/exclusion, part-parent consistency, typed failure rate, latency,
   package size and peak L4 VRAM. Separate target/prompt, segmentation, deterministic part
   partition, and renderer/inpainting failures.
3. Compare the current one-candidate path with bounded multimask candidate selection inside the
   existing prediction flow. Calibrate cues/thresholds on tune fixtures, lock them before held-out
   evaluation, and do not add inference retries, unbounded prompts, another Qwen call or
   `/v2/localize`.
4. Integrate only approved quality gates for parent and part masks; preserve source hash, dimensions,
   provenance, containment and anatomy. Report SAM boundaries separately from renderer cutout,
   background inpaint, and Pixi motion.
5. Include the pending high-pigment reconstruction scope: credible low-chroma paper donors, bounded
   source-derived reconstruction, exact outside-mask pixel preservation, and synthetic edge/seam
   checks. No inpainted pixels may expand or conceal an invalid SAM mask.
6. For invalid/low-quality artifacts, keep the exact original and show an explicit retryable failure.
   Do not silently claim a successful rig, downgrade to an unapproved tier, or automatically switch
   V2 to Renderer V1/whole-art animation.

### Shared sequencing and release

1. Freeze this plan's scope, session-only profile handling, contract ownership and test fixtures; record
   any required FEAT-003 contract reconciliation/ADR before implementation.
2. Implement the profile context/editor and resolver path against synthetic fixtures; separately
   implement mask benchmark/quality gates and renderer reconstruction against synthetic masks.
   Parallel work is allowed only after compatible contracts and no-shared-file ownership are agreed.
3. Integrate both paths into the existing supervised flow without bypassing the adult approval gates.
4. Run affected backend, mobile, renderer, schema compatibility and security checks; run Android
   emulator smoke for the editor/recommendation explanation. Use synthetic art for repository visual
   comparisons. Any owner-run live SAM test is a separately operated acceptance step, not a Codex
   provider call.
5. Release the coordinated increment only when the profile behavior and mask/renderer quality
   criteria both pass. A failed independent workstream blocks the combined release; it does not
   cause hidden behavior or fallback.

## Acceptance criteria

- AC-INT-01: An adult can edit the approved child-profile fields, select/clear a test profile, inspect
  the effective context sent to the recommender, reset it, and observe an explained before/after
  option change. The profile is editable from the Parent/Guide profile area and from the child
  selector at the start of the main flow only; it cannot be edited midway through an active flow.
  No child-facing flow can edit adult-owned safety fields.
- AC-INT-02: New profile data has an owner-approved retention boundary and provenance. Profile-free
  behavior remains valid. Contract changes are versioned, registry-compatible and documented in an
  ADR when required.
- AC-INT-03: Age, safety/supervision, prerequisite, readiness, material and explicit policy
  constraints are hard gates before ranking; preference scores only reorder eligible matches.
  Gate A/B identity and adult confirmation behavior are unchanged.
- AC-INT-04: The system labels current-scene relevance separately from the child's explicit
  preferences. It does not send profile data to Qwen or infer psychology from artwork/voice. It does
  not equate completion with mastery.
- AC-INT-05: Catalog audit reports coverage and named gaps for the approved fields; any additions
  have reviewed Montessori/age/safety/provenance metadata, duplicate checks and strict compiler fit.
- AC-INT-06: The fixed synthetic segmentation benchmark reports region, boundary, detail, failure,
  runtime and VRAM metrics for baseline and selected mask policy; thresholds are set before held-out
  evaluation and meet the owner-approved measured targets.
- AC-INT-07: Parent/part mask validation and high-pigment reconstruction tests catch shifted,
  overgrown, fragmented, wrong-object and saturated-donor artifacts. Pixels outside verified masks
  and all original provenance remain unchanged.
- AC-INT-08: Poor/invalid masks preserve the exact original and produce an explicit retryable failure;
  there is no silent false success, unapproved tier downgrade, automatic V1 fallback, or automatic
  model retry.
- AC-INT-09: Affected Python/TypeScript schemas and tests, backend/mobile/renderer suites, app
  TypeScript/build checks, repository security validation and Android emulator smoke pass; feature-
  local evidence is reproducible and contains no child media, real profile data, tokens or provider
  payloads.
- AC-INT-10: Both workstreams pass independently and the integrated flow passes before the combined
  release is called complete.

## Data handling and explicit exclusions

- **Current implementation scope:** profile edits exist only in the active session/test profile and
  are sent to the backend recommendation flow for that session. Do not write child-profile changes
  to durable storage in this increment.
- **Long-term product direction:** profiles are intended to persist through the backend and an
  approved storage adapter. This plan records the seam and migration requirements, but the durable
  persistence implementation is a future separately approved milestone after the storage choice,
  consent, actor/Guide authorization, audit, retention/deletion and authentication are reconciled
  with FEAT-029/legal requirements and an ADR. Firebase Storage/Firestore/Realtime Database remain
  prohibited by repository policy.
- No model training/fine-tuning, Qwen prompt or checkpoint changes, AI-inferred child psychology,
  live provider run by Codex, child-media commit, external cloud persistence, authentication change,
  new fallback, or change to Gate A/B authority is authorized by this draft.
- No assumption that every drawing has a bespoke rig; generic/unknown subjects remain safe and
  truthful. Mask rejection is acceptable when evidence does not support a precise cutout.

## Risks and verification

Key risks are stale/misleading adult-entered profile data, over-personalization, sensitive child
profiling, catalog bias, synthetic-to-real mask generalization, multimask L4 latency, pigment-driven
edge confusion, and coupling two independent capabilities into one release. Mitigate with editable
provenance, profile reset/no-profile tests, hard safety gates, held-out fixtures, per-stage failure
metrics, serialized GPU admission and independent workstream gates.

Keep tests, catalog coverage outputs, synthetic reference masks, sanitized benchmarks, emulator
screenshots and review notes under each owning feature's `evidence/`; cross-link the evidence in
FEAT-018 and FEAT-030. Record commands/environment/device/model/config, input fixture/version,
timestamp, reviewer, interpretation and limitations. Never store real child profiles, artwork,
provider secrets or raw provider payloads.

## Owner scope decisions recorded

- 2026-09-29: One integrated plan and one owner approval cover FEAT-018/020/030; both technical
  workstreams retain independent test gates before the coordinated release.
- 2026-09-29: The current profile remains session-only; long-term persistence through backend and
  approved storage is a future target, not a write in this implementation.
- 2026-09-29: Include interests/dislikes, adult-confirmed accomplishments/progression, readiness,
  available materials, and optional explicit non-clinical support preferences.
- 2026-09-29: Provide editing in the Parent/Guide profile area and at child selection at the start
  of the main flow; do not add a mid-flow editor.

## Approval gate

This document and its linked detailed plans remain unapproved. No UI/backend/catalog/contract/model/
renderer/persistence implementation, dependency/checkpoint work, live provider request, or release
is authorized until the owner approves this exact integrated revision and SHA-256 in
`features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md`. The approval covers the
participating FEAT-018/020/030 scopes and current session-only boundary. Durable profile/history
writes are explicitly excluded and require a later approval plus privacy/consent, authorization,
storage ADR and deletion decisions.

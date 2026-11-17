# SAM 2.1 mask accuracy and auto-rig quality plan

- Feature: FEAT-030 original-derived auto-rig; renderer consumer in FEAT-018
- Revision: 1
- Status: IMPLEMENTATION_IN_PROGRESS_UNDER_APPROVED_INTEGRATED_PLAN
- Plan type: approved implementation workstream; real-model acceptance remains open
- Coordination: this workstream is governed by FEAT-018 `INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md`; it is not a separate approval request.
- Related plan: `HEAVY_PIGMENT_MASK_ALIGNMENT_AND_BACKGROUND_20260929.md` addresses downstream cutout/inpainting artifacts; this plan addresses upstream subject/part segmentation quality.

## Problem statement and current evidence

Owner reports show subject/part masks that omit a salient object or follow colored child-drawing
boundaries inaccurately. This can create visibly detached or incomplete rigs even when SAM reports
successful inference. A successful HTTP/model status is not a segmentation-quality result.

Read-only source inspection found:

- `backend/src/sketch2life/infrastructure/ai/sam21_runtime.py` currently requests one mask candidate
  per prompt (`multimask_output=False`) and applies coarse mask-shape/area checks; it does not score
  alignment against drawing boundaries or reference masks.
- `tools/lightning_vision_v2_server.py` batches the already-derived subject/part prompts and reuses
  the image embedding for a segmentation request. Parent containment, part-size and overlap checks
  exist, but they do not establish pixel-accurate agreement with the intended anatomy.
- Backend package validation enforces confidence/containment/coverage rules, but the confidence
  value is not a calibrated boundary-quality guarantee. A typed `SUCCEEDED` mask can therefore be
  structurally acceptable yet visually wrong.
- The renderer's high-pigment background reconstruction is a separate downstream risk and already
  has its own pending plan. Do not attribute every cutout seam or wedge to SAM without a source/mask
  comparison.

These findings are code-review evidence, not a claim that SAM 2.1 is intrinsically unable to segment
children's drawings. The supplied screenshots are not copied into the repository; no source image,
mask, Lightning request, or checkpoint execution was available for this audit.

## Goal

Measure and improve SAM 2.1 subject and part-mask precision for diverse, pigment-heavy children's
drawings, then pass only independently validated, source-bound parts into the deterministic rig and
Pixi renderer. Keep the original drawing immutable and make a failed quality gate visible rather than
presenting a bad rig as success.

## Proposed work, gated by approval

1. **Build a safe evaluation set.** Create deterministic synthetic drawings across butterfly, bird,
   flower, tree/branch, fish, biped, rigid, generic-organic and unknown archetypes; vary saturated
   crayon fill, weak/no outlines, touching objects, thin appendages, paper texture/shadows, overlap,
   and incomplete shapes. Produce reviewed pixel-level subject and part ground truth. If an
   owner-approved non-child sample is later used, keep its pixels and masks local/ephemeral and put
   only sanitized metrics in Git.
2. **Measure the present baseline.** Run the existing prompts/runtime on the fixed evaluation set
   with the pinned SAM2.1 config/checkpoint and record per-class mask IoU/Dice, boundary F-score,
   thin-detail recall, false inclusion/exclusion, parent/part consistency, typed failure rate,
   latency, peak VRAM, and package size. Distinguish model miss, wrong prompt/target, post-processing
   damage, and renderer composition.
3. **Evaluate bounded candidate selection.** Compare the current single candidate against requesting
   the model's bounded multimask candidates in the same existing prediction call and selecting one
   using validated prompt geometry, parent containment, connected components, color/edge evidence,
   and calibrated model signals. Such cues may rank candidates, but must not invent pixels or expand
   a mask beyond the source/parent bounds. Select the final policy on held-out fixtures; avoid
   per-image hand-tuned thresholds.
4. **Improve part prompts and relationships.** Evaluate role-specific subject/part prompts already
   grounded by the confirmed understanding and archetype. Validate that each requested part is
   actually visible, inside its parent, non-duplicative, and large enough to animate without
   separating attached fine details. Unknown/generic topics must not be forced into a bird/butterfly
   skeleton. Do not re-run Qwen to repair segmentation.
5. **Add quality gates and typed diagnostics.** Calibrate acceptance thresholds from the baseline
   and reviewer agreement before opening the held-out set. A mask that fails quality checks must
   not be labeled a usable part/full rig. Retain the source and return the existing explicit,
   retryable preparation/playback failure. Do not automatically switch to Renderer V1 or silently
   animate a lower-quality whole image. Any already-supported non-full-rig tier remains subject to
   its own explicit mask validation and existing product policy.
6. **Confirm runtime budget.** Measure the candidate policy on the actual single-L4 deployment with
   Qwen residency considered. Keep the existing serialized GPU admission and bounded prompt set;
   do not add retry loops, another Qwen/localization request, or unbounded SAM calls. If multimask
   selection exceeds approved latency/VRAM, retain the measured safer policy rather than weakening
   quality criteria.
7. **Integrate and verify.** Add regression tests for every diagnosed failure class, Python/TypeScript
   contract parity where affected, and synthetic renderer comparisons using the exact selected masks.
   Record all artifacts and sanitized evidence under this feature's `evidence/` directory.

## Acceptance criteria

- AC-MASK-01: A versioned, reproducible synthetic benchmark has pixel-level reference subject and
  part masks for every registered archetype, including adversarial high-pigment, weak-boundary,
  touching-object and thin-detail cases.
- AC-MASK-02: Baseline and proposed candidate policies report per-class region and boundary metrics,
  failure taxonomy, reviewer agreement, latency and peak VRAM on fixed train/tune and held-out sets.
  Acceptance thresholds are recorded before the held-out evaluation; no unsupported numeric target
  is invented in this plan.
- AC-MASK-03: Any mask passed as riggable meets the approved calibrated subject/part criteria and
  retains verified source hash, dimensions, provenance, containment and anatomy relationships.
  Deliberately shifted, fragmented, overgrown, wrong-object and missing-detail masks fail typed tests.
- AC-MASK-04: The selected policy does not increase the workflow to multiple Qwen calls, restore
  `/v2/localize`, add automatic inference retries, or exceed the measured single-L4 latency/VRAM
  budget accepted in the plan review.
- AC-MASK-05: A rejected/low-confidence mask preserves the exact original and reports an explicit
  retryable failure; there is no automatic V2-to-V1 fallback or silently successful invalid rig.
- AC-MASK-06: Focused backend/renderer tests, relevant contract/type checks, full affected suites,
  and synthetic visual comparisons pass. Evidence contains no real child artwork, provider secrets,
  or raw model payloads.

## Boundaries, dependencies, and risks

- Preserve the immutable source, its hash, existing Gate A/B authority, and deterministic motion
  allowlist. SAM perceives masks; it does not choose another topic, invent anatomy, or author motion.
- Keep FEAT-030's approved SAM 2.1 Hiera Small path and existing backend-only Lightning boundary.
  Checkpoint/config/license changes or production activation require their existing separate ADR and
  benchmark gates; this plan does not authorize downloads or live provider calls by Codex.
- No changes to adult subject selection, the three topic choices, tap-to-localize interaction,
  Montessori recommendation, story, or mobile credentials.
- Main risks: synthetic fixtures may not represent real crayon variation; edge cues may follow
  texture rather than anatomy; multimask candidates may cost additional GPU time; overly strict
  quality gates may reject many valid drawings; and image inpainting artifacts can be mistaken for
  segmentation errors.
- The existing heavy-pigment plan remains complementary. Acceptance requires reporting mask quality
  and cutout/background reconstruction separately.

## Verification and evidence plan

Store the benchmark manifest, synthetic-only fixtures/ground truth, commands, model/config hashes,
metrics, reviewer scoring rubric, and sanitized comparison images in
`features/FEAT-030-original-derived-auto-rig/evidence/`. Report environment, GPU/runtime, timestamp,
reviewer, interpretation, and limitations. Never commit real child media or provider credentials.
No model execution is requested as part of plan drafting.

## Approval record and remaining gates

This is the detailed SAM workstream under FEAT-018
`INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md`, the single owner-approval artifact for
the coordinated FEAT-018/020/030 increment. The integrated plan is approved and explicitly covers
bounded multimask candidate evaluation; see its approval hash in FEAT-018. Synthetic selector tests
are not SAM accuracy results. Live-model accuracy, held-out reviewed references, L4 latency/VRAM,
deployment activation, and Android visual acceptance remain open; any activation change must still
follow the existing model ADR.

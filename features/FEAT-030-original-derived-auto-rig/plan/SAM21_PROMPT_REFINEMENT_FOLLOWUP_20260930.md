# SAM 2.1 prompt and mask refinement follow-up

- Feature: FEAT-030 original-derived auto-rig
- Revision: 1
- Status: APPROVED
- Implementation status: IMPLEMENTED LOCALLY; VISUAL/QUALITY ACTIVATION GATES PENDING
- Scope: improve SAM 2.1 subject/part prompts and bounded mask refinement; no fine-tuning
- Parent plan: `SAM21_MASK_ACCURACY_AND_AUTO_RIG_QUALITY_PLAN_20260929.md`
- Sources: `meta-sam21-small-official` in `docs/context/SOURCE_REGISTER.md`; official SAM 2 image predictor supports point/box/mask prompts, multimask output and low-resolution mask-input refinement.

## Current-state review

The parent plan's multimask selector and synthetic metrics are already implemented under the
integrated FEAT-018/020/030 approval. This follow-up does not repeat that work. Code review found:

- `sam21_runtime.py` already requests three mask candidates and applies area, box, and any supplied
  positive/negative-point checks. The service path currently supplies no subject points or region;
  the adapter falls back to a largest colored-ink component proposal.
- The Lightning worker gives each derived part box a center positive point. The service path does
  not currently derive negative points from nearby competing components or paper/background.
- `mask_input` iterative refinement is not currently used. Existing synthetic results improve
  region/boundary scores but show thin-detail recall falling from 1.0000 to 0.6394 without an
  explicit grounded anchor. Those numbers describe constructed candidate masks, not SAM accuracy.
- Real reviewed mask references, SAM/L4 latency and VRAM, and fresh Android visual acceptance are
  still open under FEAT-030. No SAM model or provider was run for this review.

## Goal

Improve the alignment and useful detail of subject and part masks on marker/crayon-heavy drawings,
while preserving the original, bounded runtime, explicit failures, and existing renderer/mask
admission policy.

## Scope

1. **Ground prompts from existing evidence.** Trace normalized source coordinates from image intake
   and the already-confirmed Gate-A target through the SAM request. Reuse existing subject region
   evidence when present; otherwise derive only deterministic, confidence-bounded ink/edge
   proposals from the original image. Select positive points from confidently interior target
   strokes and negative points from confidently exterior/background or competing-component regions.
   For a part, constrain seeds to its existing role-specific region and the accepted parent subject
   mask. Do not invent points in uncertain boundaries; report that a safe point was unavailable.
   Do not make another Qwen call or add a subject-selection UI in this increment.
2. **Improve candidate ranking without editing source pixels.** Keep current multimask output and
   hard area/box/point/parent checks. Evaluate a bounded score using prompt agreement, SAM's quality
   signal, connected-component consistency, and boundary/color evidence computed from the original
   image. Protect explicitly anchored thin features; do not use generic erosion/dilation or color
   thresholding to silently alter the accepted mask. Calibrate thresholds before held-out evaluation.
3. **Add one bounded iterative refinement stage.** For an ambiguous/low-quality initial result only,
   feed the selected candidate's low-resolution logits as `mask_input` with deterministic corrective
   points. Permit at most two additional SAM predictions per source image total: one for the subject
   and one for the highest-priority eligible requested part. Stop after that single refinement
   round; no automatic retry loop. If ROI-crop refinement is evaluated, it consumes one of those
   two calls and all crop-to-source coordinates must round-trip correctly. Keep the first valid
   candidate if refinement does not improve the registered quality score; otherwise fail closed
   under current policy.
4. **Preserve part semantics and safety.** Continue to use only archetype-allowed requested roles.
   A part mask must remain inside its accepted subject mask and be independently useful for the
   existing rig. Missing, ambiguous, duplicate, or detail-destroying masks cannot promote a package
   to `FULL_AUTO_RIG`. Do not claim SAM can infer anatomy merely from a whole-subject mask.
5. **Verify under fixed budgets.** Add synthetic, layered child-style drawings with pixel-level
   ground truth for all nine registered archetypes, including saturated pigment, weak outlines,
   touching objects, paper shadows, overlap, and thin appendages. Compare the current selector to
   prompt-seeding, scoring, and one-step refinement variants. Preserve the existing serialized
   single-L4 gate; any live SAM benchmark must use the existing approved runtime/checkpoint and
   report latency/peak VRAM before any activation decision.

## Out of scope

- Fine-tuning/training SAM 2.1, collecting a training dataset, downloading checkpoints, or changing
  model, license, dependencies, or default activation.
- SAM 3/3.1 migration, another Qwen/localization inference, unlimited crops/tiles, generic inference
  retries, or concurrent GPU execution.
- Relaxing mask-area, provenance, parent containment, failure, no-V1-fallback, Pixi, or Gate A/B
  policies; modifying original drawing pixels or storing real child artwork in Git/evidence.

## Acceptance criteria

- AC-PROMPT-01: tests prove consistent pixel/normalized/crop coordinate mapping after the existing
  image orientation/normalization steps; every positive/negative point is inside the intended
  source bounds and obeys its target/part role.
- AC-PROMPT-02: prompt generation never fabricates a positive or negative point when the visual
  evidence is ambiguous; blank, competing-component, touching-object, and no-safe-seed cases have
  explicit typed outcomes and preserve existing safe failure behavior.
- AC-PROMPT-03: candidate selection uses the registered cues and held-out thresholds; metrics
  include IoU/Dice, boundary F-score, false inclusion/exclusion, connected components, parent/part
  consistency, and thin-detail recall. No metric may be represented as a SAM model result when
  only synthetic masks were used.
- AC-PROMPT-04: an iterative path is deterministic and bounded to at most two extra SAM predictions
  per source image, with no retry loop, extra Qwen call, or change to serialized GPU admission.
  Refinement does not replace a valid first result unless the registered score improves; otherwise
  the current explicit rejection/downgrade policy applies.
- AC-PROMPT-05: no held-out archetype regresses beyond the reviewer-approved boundary/detail
  thresholds; thresholds are frozen before held-out scoring. An improved IoU cannot mask lost thin
  features or wrong-part assignment.
- AC-PROMPT-06: full existing mask admission/provenance constraints remain unchanged; wrong-object,
  shifted, fragmented, oversized, detail-missing, and parent-escaping masks cannot become a usable
  full rig.
- AC-PROMPT-07: focused backend tests, full affected suites, lint/type checks, and synthetic overlay
  review pass. Real SAM/L4 and Android results are reported separately and remain activation-gated.
- AC-PROMPT-08: no fine-tuning, new checkpoint/dependency, SAM 3 migration, raw child image, secret,
  or provider payload is added to the repository.

## Risks and mitigations

- Color/edge cues may follow crayon texture rather than the subject boundary: use them as bounded
  ranking/prompt evidence, not as an unconditional foreground classifier; retain held-out thin-edge
  and touching-object tests.
- Negative points can exclude real appendages when subjects touch: place only high-confidence points
  outside the target/part and reject uncertain seeds.
- Refinement may increase latency and GPU memory: hard-cap two additional predictions per image,
  keep serialized admission, and compare against the already-approved L4 budget before activation.
- Synthetic drawings may not predict photographed child artwork: document the gap, do not claim
  real-world accuracy, and require a separate owner-controlled visual validation before rollout.

## Verification and evidence

Use generated/layered fixtures and synthetic reference masks only for repository tests. Store the
fixture manifest, command output, per-archetype metrics, overlays, latency/VRAM measurements when
available, and sanitized failure taxonomy under
`features/FEAT-030-original-derived-auto-rig/evidence/`. Never store user/child drawings, raw model
outputs, provider credentials, image URIs, or profile data. Plan drafting performs no SAM/Qwen or
external runtime request.

Implementation was blocked pending explicit approval of this exact plan revision; the owner
approved it before code changes, as recorded in `approvals/TASK_APPROVAL.md`. Local implementation
is complete for the bounded prompt/scoring/refinement path. Live model activation remains governed
by the existing FEAT-030 ADR and L4 benchmark gates. Held-out mask-quality review and Android visual
acceptance remain open; passing repository tests do not establish real-image SAM accuracy.

## Approval

The project owner approved this exact scope with “ok, implement” on 2026-09-30 at 23:17:06
Asia/Saigon. Approved pre-implementation plan SHA-256:
`79500D1A0634AC7C30C184C405048A6A30AC267ECE5CA5A39948F77CD1D8030E`.

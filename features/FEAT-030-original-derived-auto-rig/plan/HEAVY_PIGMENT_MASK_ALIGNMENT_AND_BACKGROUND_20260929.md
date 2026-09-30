# Heavy-pigment mask alignment and clean cutout follow-up

- Feature: FEAT-030 original-derived auto-rig / FEAT-018 Pixi playback consumer
- Revision: 1
- Status: IMPLEMENTATION_IN_PROGRESS_UNDER_APPROVED_INTEGRATED_PLAN
- Trigger: owner-provided Android playback screenshot showing pale radial wedges around a brightly colored butterfly cutout.

## Evidence and diagnosis

The screenshot shows reconstruction artifacts near moving part boundaries. No source image, SAM
subject/part masks, rig package, or corresponding Lightning request logs were available in this
workspace at diagnosis time; the screenshot is not copied into the repository because it may contain
child artwork. Therefore, the exact contribution from segmentation versus Pixi composition is not
yet established.

Code inspection found a concrete high-risk cause in
`packages/art-renderer/src/subjectCutout.ts`: `sampleLocalBackground` accepts neutral/light pixels
only when at least two are immediate neighbors; otherwise it averages every unmasked neighbor,
including saturated crayon strokes. `inpaintMaskRegion` then propagates that seed color through the
entire masked region by eight-neighbor breadth-first averaging. On dense, high-pigment boundaries this
can produce color streaks/wedges in the reconstructed paper. Separately, the current artifact checks
verify source hashes, mask dimensions/area and region bounds, but do not score mask-to-ink alignment or
part-boundary quality. These are hypotheses to test, not a claim that SAM alone caused the screenshot.

## Goal

Improve mask-edge and reconstructed-background quality for densely colored children's drawings while
preserving exact source pixels/provenance and the already approved no-automatic-V1-fallback behavior.

## Proposed scope

1. Add deterministic synthetic fixtures for saturated crayon strokes, overlapping colors, disconnected
   wing/leaf-like parts, neutral paper with mild lighting variation, and colored objects adjacent to
   the target. Keep all fixtures synthetic; do not add the owner screenshot or real child media to Git.
2. Add diagnostics/tests that separate parent-mask alignment, part-mask coverage/overlap, foreground
   edge extraction, and background inpainting so the source of artifacts can be localized.
3. Replace unconstrained color propagation with a bounded, pigment-aware reconstruction strategy that
   draws estimates only from credible local paper donors and rejects low-confidence regions. Do not
   let high-chroma drawing marks seed paper color. Preserve all pixels outside the verified subject mask.
4. Add conservative mask/part quality checks for boundary support, disconnected fragments, and
   parent/part consistency. Any cleanup must stay inside existing verified mask/part bounds; do not
   erase thin crayon detail or silently expand masks across unrelated objects.
5. If alignment/background quality cannot be established, keep the original drawing still and show
   the existing retryable V2 error state. Do not animate the whole drawing or automatically select V1.
6. Record a feature-local synthetic visual comparison and tests; run renderer/mobile checks and a local
   Android WebView smoke test without making a provider/model call.

## Acceptance criteria

- AC-030-PIG-01: Saturated foreground colors cannot be used as background seeds merely because neutral
  samples are scarce; the synthetic dense-pigment fixture has no radial color wedges in its masked
  paper reconstruction.
- AC-030-PIG-02: All source pixels outside the verified subject mask remain byte-identical, source
  provenance is unchanged, and thin/disconnected colored marks represented by the verified mask are
  retained in the foreground cutout.
- AC-030-PIG-03: Parent and part mask checks detect deliberately shifted, overgrown, fragmented, or
  inconsistent synthetic masks and return a typed failure rather than silently animating a visibly
  misaligned rig.
- AC-030-PIG-04: A quality failure retains the exact original image and exposes retry; it never emits
  automatic V2-to-V1/whole-art fallback.
- AC-030-PIG-05: Focused renderer tests, complete renderer tests, TypeScript/mobile checks and a
  synthetic Android visual smoke pass; evidence records limitations and does not include real child
  images, credentials, or provider payloads.

## Out of scope and risks

- No SAM/Qwen/Lightning model, checkpoint, prompt contract, provider configuration, dependency, or
  additional inference is changed in this plan.
- No changes to Gate A/B, story, topics, motion choreography, source ownership, or explicit legacy V1
  compatibility.
- Aggressive edge cleanup can remove fine crayon marks; color-based cues are supplemental only and
  may not replace a verified segmentation mask.
- A locally smooth paper reconstruction cannot reliably recreate complex objects hidden behind the
  subject. In low-confidence cases, the correct outcome is still image plus retry, not fabricated
  background or legacy animation.

## Verification

- Reproduce the wedge symptom with deterministic synthetic pixel fixtures before changing the
  algorithm; save only synthetic fixture outputs under this feature's `evidence/` tree.
- Unit-test donor selection, mask boundaries, connectivity, part consistency, typed failures, exact
  outside-mask equality, and source immutability.
- Run art-renderer tests/typecheck/demo build, mobile UI copy and TypeScript checks, and the approved
  local backend/emulator development route. Do not submit any drawing to an AI provider.
- If a later owner-run real drawing is used for final visual acceptance, inspect its mask locally in
  the live session only; do not copy it or its mask into Git/log evidence.

The integrated plan is approved; its exact current SHA-256 is recorded in FEAT-018's approval
record. The local synthetic reconstruction change and renderer regressions are implemented.
Real-drawing visual acceptance and verified parent/part mask correspondence remain pending. Durable
profile/history work is outside this plan and requires the separate privacy/authorization decisions
stated in the integrated approval.

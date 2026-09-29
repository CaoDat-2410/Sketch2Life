# High-pigment cutout artifact diagnosis — 2026-09-29

- Evidence ID: `E-030-FIX-011`
- Status: diagnosis only; implementation awaits approval of `plan/HEAVY_PIGMENT_MASK_ALIGNMENT_AND_BACKGROUND_20260929.md` revision 1.

## Observed symptom

The owner-provided Android playback screenshot shows pale orange/beige radial wedges around the
butterfly's moving cutout. The screenshot was reviewed in the Codex conversation and was not copied
into this repository to avoid retaining potentially identifiable child artwork.

## Findings

- The current `createSubjectCutoutLayers` verifies mask dimensions, area and source provenance, then
  reconstructs the masked background with eight-neighbor breadth-first RGB averaging.
- `sampleLocalBackground` prefers neutral/light neighbors only if at least two qualify. If fewer are
  available, it averages all immediate unmasked neighbors, including saturated crayon colors; the
  resulting color is propagated through the masked subject region. This mechanism can create the
  observed radial color streaks on densely colored boundaries.
- The backend validates mask integrity and basic dimensions/regions but does not yet score mask
  alignment against source drawing edges or measure part-boundary defects.
- After the requested emulator reboot, the app was at onboarding, not the captured playback. No
  matching source image, SAM mask, part masks, or request logs were available to determine whether
  SAM segmentation also contributed. Therefore the screenshot supports the artifact symptom, not a
  definitive claim that SAM itself is misaligned.

## Safety and next step

No provider/model request was made and no source code was changed for this diagnosis. The proposed
plan uses only synthetic fixtures, tests pigment-aware local reconstruction and mask/part alignment
separately, and preserves the no-automatic-V1-fallback decision. Await exact owner approval before
implementation.

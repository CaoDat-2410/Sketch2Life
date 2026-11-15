# Rev87.13 — OpenMoji source amendment for Parent progressive SVG guides

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** APPROVED as a source-selection amendment to Rev87.12 under the owner's request to research suitable SVG sources, connect them to Parent UI, and display the original color illustration at the final step.<br>
**Canonical SRS:** FEAT-063 v2.7-draft; §§1–31 remain requirements, §32 is append-only as-built evidence.

## Why the Rev87.12 source choice changes

The Noto color illustrations render well as color pictures, but deriving line guides from their filled regions creates internal contour clutter and does not produce a clean drawing sequence. The Noto candidate previews were rejected for runtime use. OpenMoji provides a paired black line-art SVG and color SVG for each pictogram. The black source has clean, rounded outlines; the paired color source can be shown unchanged beside the completed guide.

This amendment supersedes Rev87.12's Noto runtime dataset selection. It preserves the approved Parent route/UI scope, final color reveal, source provenance, and all non-goals. Noto files remain only as rejected curation evidence and are removed from the runtime pack and Docker image.

## Selected source pack

- **Existing Arcadia Gallus source:** retain the pinned CC0 chicken guide as-is.
- **OpenMoji 17.0.0:** pin repository revision `f9fc506a3f913be9897ab0181d611d4c910a4104`; use paired `black/svg` and `color/svg` files for:
  - `U+1F422` turtle — simple profile, 12 source drawing elements.
  - `U+1F98B` butterfly — 9 source drawing elements, symmetric and child-recognizable.
  - `U+1F415` dog — 6 source drawing elements, familiar silhouette.
- Keep the import bounded to these six SVG files plus the official CC BY-SA 4.0 license text and attribution metadata. Do not vendor the full dataset.
- Do not include apple/chick from OpenMoji or any Noto candidate in this implementation: they do not provide enough independent line elements for the already approved 4–8-stage drawing sequence without inventing geometry.

### License and attribution

OpenMoji artwork is CC BY-SA 4.0. Preserve its source/revision and file hashes. Distribute any adapted/derived OpenMoji guide under CC BY-SA 4.0, include the required attribution in the UI and project asset metadata, and retain the license text. The final color image is the exact paired OpenMoji source artwork, not a regenerated image. No content is presented as original Sketch2Life artwork.

Required visible credit: **“Ảnh: OpenMoji · CC BY-SA 4.0”**, linked to OpenMoji and the license where the UI supports links. The mobile screen includes the credit beside the color reference on the last step.

## Implementation

1. **Curated source resolver**
   - Parse only a pinned, hash-verified local source pack. Accept only SVG root/viewBox and safe drawable geometry needed by the selected files; reject scripts, external references, stylesheets, embedded images, transforms, unknown elements, and excessive files/paths.
   - Derive guide geometry only from the selected black SVG line group. Normalize `line`, `polyline`, `polygon`, `circle`, and `ellipse` primitives to geometrically equivalent SVG path data for the current API/React Native path renderer; preserve source geometry and verify every normalized path against the pinned source element.
   - Build the final color reference from the matching original color SVG, preserving fill, stroke, width, cap, join, and order. Verify the line group matches the black source in normalized geometry and element order.
   - Pin source, license, manifest, and per-asset hashes. Stage order and short Vietnamese instructions are explicit manifest data, not inferred at runtime.
   - Keep source lookup ahead of Modal fallback; unsupported topics retain the existing behavior.
2. **Progressive drawing stages**
   - Create 4–8 sequential stages per selected subject, grouping source elements by recognizable body part. Every black-source drawable appears once, with complete coverage and no new animal geometry.
   - Preserve each source element's identity in `path_lineage`; distinguish shape-to-path normalization from exact path reuse.
   - Validate line-only output, exact source geometry after normalization, source/color pair alignment, complete path coverage, stage count, path count, and the sanitizer.
3. **Parent mobile UI**
   - Keep the drawing guide optional and nonblocking. Connect the real Parent topic flow to the source guide route.
   - Animate cumulative source strokes in order. On the last step, show the completed line guide and the paired original color illustration together, without hiding either image.
   - Display the OpenMoji attribution next to the color reference. Reset steps when topic/guide changes. The following photo capture remains mandatory.
4. **Docker and records**
   - Package only Arcadia and the selected OpenMoji assets/licenses/manifests. Remove the rejected Noto pack from runtime image paths.
   - Save asset previews, stage renders, hashes, source/license notes and final UI evidence in the FEAT-063 evidence folder.
   - Update source register, feature decisions/context/status and append the as-built report to SRS §32 only. Do not alter SRS §§1–31.

## Acceptance criteria

- [ ] Three selected OpenMoji guides (turtle, butterfly, dog) resolve locally by topic through the real Parent API route before Modal fallback.
- [ ] Each guide has 4–8 stages, coherent age-appropriate instructions, complete nonduplicated source-element coverage, and no invented animal geometry.
- [ ] Source and paired color artwork are pinned to OpenMoji 17.0.0, integrity-checked, and accompanied by CC BY-SA 4.0 license/provenance.
- [ ] Parent UI progressively draws each selected black source and shows its exact color illustration beside the completed line guide at the final step, with required visible attribution.
- [ ] User-facing flow still proceeds to mandatory capture; guide remains optional and sends no child image/profile/voice data to the source resolver.
- [ ] Docker runtime includes only selected, licensed sources; Noto candidates are not active runtime sources.
- [ ] Manual source/artwork inspection is recorded. No Android/Firebase E2E or automated tests are claimed unless run separately.

## Limits

No video generation, FLUX, model inference/deployment, database migrations, profile/consent/seed/account or `.env` changes, public publishing, shared service restart, commit, push or merge. No weakening of safety/security validators. No target-SRS change outside §32.

## Sources

- OpenMoji project/source and asset variants: https://github.com/hfg-gmuend/openmoji
- OpenMoji 17.0.0 release: https://github.com/hfg-gmuend/openmoji/releases/tag/17.0.0
- OpenMoji style guide: https://openmoji.org/styleguide
- CC BY-SA 4.0 legal code: https://creativecommons.org/licenses/by-sa/4.0/legalcode
- Arcadia Science Free Organism Illustration Library v1.0: https://zenodo.org/records/17203578
- Noto Emoji source/license, reviewed and rejected for progressive line derivation: https://github.com/googlefonts/noto-emoji and https://github.com/googlefonts/noto-emoji/blob/99701e07d3d1fe1bdbcdb14964547f0fd592966f/2D/svg/LICENSE

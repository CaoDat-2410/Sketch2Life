# Walker/flyer motion sprite drafts — 2026-10-01

Status: generated draft only. All eight frames need owner visual approval individually; rights,
catalog registration, approved/applied promotion, and runtime use remain blocked.

## Walker: corgi-like quadruped

- File: `walker-corgi-cycle-draft.png`
- Dimensions/mode: 1536 × 1024 RGBA; 2 × 2 pose layout.
- Frame order: row-major, proposed IDs `draft.walker.corgi.v1.frame-01` through `frame-04`.
- SHA-256: `363F3ECFA508D48D67355384BEA7BAA58E3EC6B937BFC852C305DB0559F015C8`.
- Generator: built-in ImageGen; generation output `exec-356ff277-e1d9-405c-a348-20a738ea9df6.png`; background-removal edit output `exec-efe57bee-ca07-49ab-bf48-28702af57cb4.png`.
- Generation prompt: “Create a cute small corgi-like dog companion shown in four distinct sequential walking poses in a clean 2-by-2 sprite-sheet grid. Keep character identity, proportions, face, colors, outline, and scale consistent; vary leg positions with a slight body bob. Use a cheerful flat childlike hand-drawn sticker style. Keep each pose fully visible at consistent baseline and scale, with true transparent background, no text, grid lines, shadows, props, landscape, or extra characters.”
- Edit prompt: “Change only the supplied sheet's checkerboard background to genuine transparent alpha; preserve the four dog drawings, pose differences, line art, colors, scale, layout, canvas and spacing; keep character pixels opaque; add no grid, labels, shadows, or other content.”

## Flyer: songbird

- File: `flyer-songbird-cycle-draft.png`
- Dimensions/mode: 1536 × 1024 RGBA; 2 × 2 pose layout.
- Frame order: row-major, proposed IDs `draft.flyer.songbird.v1.frame-01` through `frame-04`.
- SHA-256: `2EC3D765A815BC5C8C721EA6449BAE5BCAFFED673290A968D314776DA23B7C3E`.
- Generator: built-in ImageGen; generation output `exec-9226347c-6b4b-4c89-b827-a7fc4de882c0.png`; background-removal edit output `exec-23e6bee3-8ae2-4f63-8c32-c9caafb4aaed.png`.
- Generation prompt: “Create one friendly small songbird companion shown in four sequential flying poses in a clean 2-by-2 sprite-sheet grid. Keep identity, proportions, face, beak, colors, outline, and scale consistent; vary both wings through raised, mid-downstroke, lowered, and recovery positions to form a readable flap cycle. Use a cheerful flat childlike hand-drawn sticker style. Keep each bird fully visible with consistent scale/pivot, transparent background, no text, grid lines, shadows, sky, props, or extra characters.”
- Edit prompt: “Change only the supplied sheet's checkerboard background to genuine transparent alpha; preserve all four bird drawings, distinct wing positions, line art, colors, scale, layout, canvas and spacing; keep character pixels opaque; add no grid, labels, shadows, sky, or other content.”

## Review checklist

- Confirm each pose remains the same character and the motion is readable at target Pixi size.
- Confirm silhouettes, extremities, and pivots are not clipped by cell boundaries; add explicit frame
  rectangles and transparent padding before any atlas/catalog import.
- Review style harmony against the existing flat-doodle library; revise if the shading/outline feel
  too glossy or inconsistent.
- Record separate approval/rejection for all eight frames. Until then the drafts must remain
  outside catalog candidates and cannot be loaded by the renderer.
- Rights/provenance review is independent from visual approval; only after both pass may FEAT-028
  create versioned frame records and FEAT-030 consume selected capability-bound IDs.

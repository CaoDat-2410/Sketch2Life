# Rev87.14 — Parent richer SVG guide source pack

**Date:** 2026-11-14<br>
**Status:** APPROVED by the owner's direct instruction to raise the illustration quality modestly above the current emoji-like guides.<br>
**Canonical SRS:** FEAT-063 v2.7-draft; target §§1–31 remain authoritative and unchanged; implementation evidence goes in §32 only.

## Goal

Add a more illustrative, moderately detailed option for the Parent turtle, butterfly and dog guides while preserving the current simple OpenMoji drawings as a low-detail fallback. The final guide and color reference must depict the same subject/pose closely enough that the child can compare them. Keep the existing Arcadia chicken source.

## Candidate sources to curate

Use only individually selected Openclipart SVGs, not the complete 178k+ dataset:

- Turtle: `turtle crawling - color` (Openclipart asset 325115) and `turtle crawling - line art` (325116), both uploaded by `hund` on 2020-11-08.
- Butterfly: `Simple Detailed Butterfly Clipart` (352665) and its linked `Simple Detailed Butterfly Lineart` remix (352671), both by `teck5`.
- Dog: `dog - coloured` (213982) and `dog - lineart` (213981), by `frankes`.

Openclipart states uploaded artwork is provided under CC0 1.0. Preserve the Openclipart page, author, asset ID, license evidence, source revision/content hash and adaptation record for each selected file. Do not assume that a similarly named pair has identical geometry: inspect silhouette, pose, line quality, and color/line correspondence before activation.

## Implementation boundaries

1. Download only these candidates from their primary Openclipart SVG links; pin each file by SHA-256. No full dataset import.
2. Render candidate color/line pairs locally at a consistent square size. Select the pair for a topic only if it is visibly the same subject/pose, child-friendly, moderately detailed, and feasible to stage in 4–8 drawing steps without inventing animal parts.
3. If the separate line/color assets are materially mismatched, derive the line guide from the line-art source and retain the current OpenMoji pair for that topic. Do not synthesize or hand-repair an unrelated source into a false match.
4. Add a hash-pinned local resolver ahead of OpenMoji, Arcadia and Modal. It receives only the generic topic; no photo/profile/voice data. Validate safe SVG, line-only guide geometry, full one-time path coverage, explicit step sequence, and attribution/provenance.
5. In Parent UI, preserve progressive strokes. On the last step, show the finished line guide beside the matching original color source and credit the selected source. Continue to mandatory photo capture.
6. Package only approved per-topic files and CC0 notice in Docker. Keep OpenMoji as the fallback and do not remove historical evidence.
7. Update the source register, context, decisions, status, evidence README/report, and append §32.29 to the canonical SRS. Do not edit §§1–31.

## Acceptance criteria

- [x] At least two of the three Openclipart pairs pass source/pose/complexity curation; any rejected pair stays on the existing OpenMoji source.
- [x] Each active richer guide uses only source line geometry, has 4–8 explicit stages, and covers each source element once without adding unsupported animal features.
- [x] Paired color reference matches the line guide subject/pose and is returned with the completed guide; screen wiring is present in source, but UI runtime display was not exercised.
- [x] Openclipart source page, author, CC0 status, per-file hashes and adaptation lineage are recorded; the runtime pack contains only selected assets.
- [x] Existing OpenMoji and Arcadia sources remain available as fallbacks; unsupported topics keep their existing behavior in source.
- [x] Manual previews are recorded. No app/API/Android runtime verification is claimed.

## Limits

No video, FLUX, Modal inference/deploy, database/profile/consent/seed/account/`.env` mutation, publication, shared service restart, commit, push, merge, or quality-gate relaxation. No automated tests or app/API runtime test in this scope. If exact primary SVG files cannot be retrieved or inspected, stop before enabling the candidate and report the blocker.

## Sources

- Openclipart CC0/asset FAQ: https://openclipart.org/share
- Turtle color: https://openclipart.org/detail/325115/turtle-crawling-color
- Turtle line art: https://openclipart.org/detail/325116/turtle-crawling-line-art
- Butterfly color: https://openclipart.org/detail/352665/simple-detailed-butterfly-clipart
- Butterfly line art: https://openclipart.org/detail/352671/simple-detailed-butterfly-lineart
- Dog color: https://openclipart.org/detail/213982/dog-coloured
- Dog line art: https://openclipart.org/detail/213981/dog---lineart-by-frankes-213981
- Openclipart dataset card (provenance/supporting index only; not imported): https://huggingface.co/datasets/kawwaaa/openclipart

## Execution record — 2026-11-14

Selected the butterfly pair (352665/352671) and turtle pair (325115/325116), each with six stages. The butterfly has 39 guide paths and 70 color-reference paths; the turtle has 35 guide paths and 8 color-reference paths. Rejected the dog pair because its fur contours were too dense, and rejected alternate turtle outline 325114 because it did not match the selected color turtle's pose. Manual preview review found a moderate-detail option above the previous emoji-style art; this is not educator or child validation.

Added the local source resolver, data pack/notice, Docker allowlist/copy, and Parent UI recognition for the new source-derived guide. Automated tests, build, API, app, Android, Modal and educator/child evaluation remain unrun per the scope limits. Source hashes, previews and detailed limits are in `evidence/EV-063-109_PARENT_RICHER_OPENCLIPART_GUIDES_20261114/REPORT.md` and SRS §32.29.

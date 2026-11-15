# EV-063-109 — Parent richer Openclipart SVG guides

**Date:** 2026-11-14<br>
**Plan:** `plan/PLAN_REV87_14_PARENT_RICHER_OPENCLIPART_GUIDES_20261114.md`<br>
**Status:** source integration and manual preview inspection complete; app/API runtime not verified.

## Result

The selected drawings are not overly simple compared with the previous emoji-style options. The butterfly has layered wing outlines, antennae, body details and interior patterns. The turtle has a recognizable head, legs and a segmented shell. They provide a moderate-detail option while remaining legible as a child's drawing guide. The six-stage sequence adds source contours progressively, from the large silhouette toward smaller details.

This is not an educator or child usability evaluation. If the team later needs age-specific difficulty, it should curate separate simple and detailed guide variants rather than add arbitrary contour detail to every picture.

## Curated source pairs

| Topic | Color asset | Line-art asset | Guide paths / stages | Decision |
|---|---|---|---:|---|
| Butterfly | Openclipart 352665, teck5 | Openclipart 352671, teck5 | 39 / 6 | Selected; same recognizable subject and pose, with suitable wing detail |
| Turtle | Openclipart 325115, hund | Openclipart 325116, hund | 35 / 6 | Selected; same crawling pose, with clear shell, head and limb details |
| Dog | Openclipart 213982, frankes | Openclipart 213981, frankes | — | Rejected; fur contours are too dense for this guide |
| Alternate turtle outline | Openclipart 325114 | — | — | Rejected; its pose does not match the selected color turtle |

The active butterfly stages describe wing outline, body/antennae, large wing curves, right-wing details, left-wing details and final details. Turtle stages describe body/shell outline, head/neck, large shell divisions, legs, shell plates and remaining detail. Every guide source path is assigned once to exactly one stage; no new animal geometry was invented.

## Source and provenance

Openclipart states that uploaded artwork is dedicated to the public domain under CC0 1.0 ([Openclipart sharing and FAQ](https://openclipart.org/share)). Each selected asset is pinned by source URL and SHA-256:

- Butterfly color: [asset 352665](https://openclipart.org/detail/352665/simple-detailed-butterfly-clipart), `996da47b11cbb90db4ad69dc08c92caf9b6b8b92297b9a7db98f7bb0941237c7`.
- Butterfly line art: [asset 352671](https://openclipart.org/detail/352671/simple-detailed-butterfly-lineart), `736e5a6ab508198b12da9a360f4ae84aca3aec815e2f39912fdd9b311aba645e`.
- Turtle color: [asset 325115](https://openclipart.org/detail/325115/turtle-crawling-color), `8ee643ed8bb8e05dc81f6df7bc35953b36eb016774053bdaee628a7fb5a201b5`.
- Turtle line art: [asset 325116](https://openclipart.org/detail/325116/turtle-crawling-line-art), `8f9eca29b6f48c1a30f9212ab720dcac72473d72c22ada347d058c46d861d180`.

The runtime pack contains only these two selected pairs, their source-derived guide data, a pinned manifest and `NOTICE.md`. The manifest SHA-256 is `570aa1bfa36c3e43d832edc745a2ce8320fd2cbe83880816016f793776099f3e`; the notice SHA-256 is `231f9a0024319227977fa0ffc248334188f2df01e2f3fbdd40d76ad5f432d4e3`. The Docker build allowlist and backend image copy include only the Openclipart pack directory. Existing OpenMoji and Arcadia sources remain available.

## Evidence files

- `butterfly-color-preview.png`, `butterfly-line-preview.png`, `butterfly-normalized-progression.png`, `butterfly-reference-preview.png`
- `turtle-color-preview.png`, `turtle-line-preview.png`, `turtle-normalized-progression.png`, `turtle-reference-preview.png`
- Rejected-candidate previews: `dog-color-preview.png`, `dog-line-preview.png`, `turtle-outline-alternate-preview.png`
- `build_openclipart_pack.mjs` records deterministic normalization, path assignment, metadata and hash generation; `render_candidate_previews.ps1` records the manual preview-rendering procedure.

The progression images are manually rendered source previews, not screenshots from Parent UI. The route is intended to return the local guide for a recognized topic without dispatching Modal; this behavior was not exercised in this amendment.

## Verification limits

Manual inspection covered the selected and rejected color/line candidates and the six cumulative source-contour stages for each selected guide. Static source review confirmed the 4–8 stage range, unique path IDs, one-time stage coverage, path-size limit, source/license hashes, sanitizer call, manifest pin and Docker packaging changes.

No automated tests, build, API request, app/browser run, Android emulator, database mutation, Modal inference/deployment, educator review or child study was performed. Therefore API behavior, mobile rendering, actual dashed-current-stage animation, production packaging and instructional suitability remain unverified. This report is as-built evidence only; SRS target §§1–31 remain unchanged and the SRS remains unsigned.

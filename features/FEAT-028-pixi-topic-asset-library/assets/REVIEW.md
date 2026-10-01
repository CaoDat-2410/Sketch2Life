# FEAT-028 frontend asset review

The table below is the original inventory snapshot. Its visual `REVIEW_PENDING` entries are superseded by the dated owner decision below; rights/runtime eligibility are tracked separately and remain pending.

| Asset ID | Generated path | Review status | Reviewer | Reviewed at | Notes |
|---|---|---|---|---|---|
| topic-weather-sky-v1 | generated/weather-sky-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-land-water-v1 | generated/land-water-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-plants-v1 | generated/plants-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-animals-v1 | generated/animals-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-people-roles-v1 | generated/people-roles-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-places-buildings-v1 | generated/places-buildings-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-transport-v1 | generated/transport-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-food-v1 | generated/food-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-everyday-classroom-v1 | generated/everyday-classroom-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-learning-play-v1 | generated/learning-play-materials-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-fantasy-underwater-space-v1 | generated/fantasy-underwater-space-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-motion-effects-v1 | generated/motion-effects-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; visual approval required |
| topic-science-technology-v1 | generated/science-technology-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; actual image is 1535px tall; inspect final-row bounds and crop margins |
| topic-dinosaurs-prehistory-v1 | generated/dinosaurs-prehistory-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect horn/crest/tail edge clearance |
| topic-farm-animals-v1 | generated/farm-animals-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect large silhouettes for clipping at cell edges |
| topic-wild-animals-v1 | generated/wild-animals-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect long necks/tails and edge clearance |
| topic-ocean-life-v1 | generated/ocean-life-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect tentacle/flipper crop bounds |
| topic-insects-small-creatures-v1 | generated/insects-small-creatures-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; check segment/wings readability at target scale |
| topic-music-instruments-v1 | generated/music-instruments-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect bow, neck, and trumpet bell crop bounds |
| topic-sports-outdoor-play-v1 | generated/sports-outdoor-play-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; racket/rope/frame shapes need crop and cell-overlap review |
| topic-construction-tools-v1 | generated/construction-tools-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; crane/excavator may approach shared cell edge; inspect separation |
| topic-home-kitchen-v1 | generated/home-kitchen-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect furniture and tableware crop boundaries |
| topic-clothing-accessories-v1 | generated/clothing-accessories-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect paired boots and accessory isolation |
| topic-celebrations-seasons-creative-play-v1 | generated/celebrations-seasons-creative-play-atlas-v1.png | REVIEW_PENDING | — | — | 6 frame entries; inspect balloons/cake at cell boundaries; no cultural assumptions intended |

## Owner visual approval — 2026-10-01

- Decision: the project owner explicitly approved the visual appearance of all existing catalog sprites (“duyệt các sprite hiện có luôn nhá”). I inspected all 24 atlas PNGs against the catalog/manifest; the approval covers each of the 144 indexed frames, not just the atlas sheets.
- Exact approved visual scope: every `assetId` in catalog version `2.0.0`, SHA-256 `9358F1CEC62072EFDAEDB0DFE4470E29962B67422AF439237920C916F4FDEAFB` (144 IDs across 24 atlases). Catalog frame rectangles are the per-frame identity/bounds.
- Visual checks: six isolated entries per atlas; generated flat illustration style; transparent RGBA backgrounds; no obvious embedded text/logos or a visible crop defect in the inspected sheets. This is a visual approval, not a claim that every sprite will stylistically match every child's drawing or be suitable for every scene.
- Provenance: the generation manifest records built-in ImageGen generation and no external asset sources. This does not itself constitute a legal opinion or complete rights clearance.
- Rights/runtime state: `RIGHTS_REVIEW_PENDING`; none is copied into `approved/` or `applied/`, and none is runtime-eligible until the rights/provenance gate is separately cleared and the integration plan is approved. The catalog's current `REVIEW_PENDING`/`runtimeEligible=false` values remain intentionally unchanged.
- This approval does not authorize contract changes, runtime references, remote asset fetches, or implementation outside the separately approved plan.

## Motion-sequence draft additions — 2026-10-01 (NOT APPROVED)

These two sheets were generated for the FEAT-030 approved walker/flyer gap audit and are draft-only.
The existing 144-frame approval does not cover them. No frame has been accepted, entered into the
catalog, moved to `approved/` or `applied/`, rights-cleared, or referenced by runtime code. See
`assets/generated/SPRITE_MOTION_DRAFTS_20261001.md` for prompts, hashes, frame IDs, and checks.

| Draft sheet | Proposed frame family | Current review state | Runtime state |
|---|---|---|---|
| `walker-corgi-cycle-draft.png` | Four quadruped walk poses | VISUAL_REVIEW_PENDING — each of 4 frames separately | BLOCKED; uncatalogued and rights pending |
| `flyer-songbird-cycle-draft.png` | Four songbird wing-flap poses | VISUAL_REVIEW_PENDING — each of 4 frames separately | BLOCKED; uncatalogued and rights pending |

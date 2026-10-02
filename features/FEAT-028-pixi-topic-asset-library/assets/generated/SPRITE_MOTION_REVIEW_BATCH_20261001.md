# Pixi motion sprite review batch — 2026-10-01

Status: owner visual approval recorded on 2026-10-01 for all seven sheets and all 28 proposed frames.
These remain concept sprite sheets: they are not frame-cropped, catalogued, rights-cleared,
promoted to `approved/` or `applied/`, or referenced by runtime code. See `../REVIEW.md` and
`../../evidence/notes/MOTION_SPRITE_VISUAL_APPROVAL_20261001.md` for the approval boundary.

## Batch inventory

| Motion family | Draft file | Canvas | Proposed frame IDs | Style reference | ImageGen output ID | SHA-256 |
|---|---|---:|---|---|---|---|
| Quadruped walker | `motion-walker-corgi-v2-20261001.png` | 1217×1293 RGBA | `draft.walker.corgi.v2.frame-01`…`04` | `animals-atlas-v1.png` | `exec-c6a4ca9a-a00f-4fad-944e-dca7194eccac` | `2043BCF6BF68BD45E7FCFD097ABFF6C4276B7A0AC29DAD39BF6F3672AF7566F2` |
| Biped walker | `motion-walker-child-v2-20261001.png` | 1230×1278 RGBA | `draft.walker.child.v2.frame-01`…`04` | `animals-atlas-v1.png` | `exec-970e141b-cb7b-4762-a298-020987915916` | `7007929EEDB042733FA0179D0AB60663775E41C372944B0E39C22A3A059280C5` |
| Flyer | `motion-flyer-songbird-v2-20261001.png` | 1536×1024 RGBA | `draft.flyer.songbird.v2.frame-01`…`04` | `animals-atlas-v1.png` | `exec-c2160893-246a-479c-9ed2-7fe8a9347e1c` | `8A3DBCFE013A49D5CCC5E939AC450FD8BE37402988D52E6B99F2F7AC95AA7311` |
| Swimmer | `motion-swimmer-goldfish-v1-20261001.png` | 1536×1024 RGBA | `draft.swimmer.goldfish.v1.frame-01`…`04` | `ocean-life-atlas-v1.png` | `exec-9418f8cc-3678-4e29-bbab-bbc1f026409f` | `8F8B1D76A02EE5C97324A945772E64694A2726DBB32EA6EDFA6EBE5544ACC5F2` |
| Crawler | `motion-crawler-snail-v2-20261001.png` | 1536×1024 RGBA | `draft.crawler.snail.v2.frame-01`…`04` | `insects-small-creatures-atlas-v1.png` | `exec-ccbab8cf-c821-4d7a-8519-29a4c99076e3` | `33FB05B5152457B1EEB0358DB3661F37492C520C431C0260B22F6F482CDCEFAF` |
| Slitherer | `motion-slitherer-snake-v2-20261001.png` | 1536×1024 RGBA | `draft.slitherer.snake.v2.frame-01`…`04` | `insects-small-creatures-atlas-v1.png` | `exec-df4a0214-54c0-42cd-a805-ac38a60fa4f0` | `9BA55A9360EBC68DBAE56D0D1271D02A9975D35A5BA0BFE9475FB85F1130E965` |
| Roller | `motion-roller-car-v1-20261001.png` | 1536×1024 RGBA | `draft.roller.car.v1.frame-01`…`04` | `transport-atlas-v1.png` | `exec-682b20c8-95b4-47a9-a1c0-5e4687d37087` | `10ED1353542A7966FB1DE93F256C343BA257153F89518251C98D2960D1C361FD` |

## Prompt set and provenance

All assets used the built-in ImageGen tool with `transparent_background=true`. Style-reference
images were used only to match the existing flat, child-friendly Pixi sticker family; no catalog
pixels were copied into these new sheets.

### Quadruped walker — first pass

> Create one friendly small corgi-like dog companion walking in a readable four-pose cycle. Match
> the existing approved Sketch2Life animal sticker atlas: simple flat childlike 2D sticker
> illustration, clean solid cheerful fills, bold dark outline, minimal shading; no glossy 3D look.
> Exactly four full-body side-view poses in a 2-by-2 arrangement, same dog identity, scale,
> orientation, and ground baseline; clearly alternating front and rear leg positions with a small
> natural body bob; generous transparent padding. True transparent background; no checkerboard,
> floor, shadows, grid lines, cell borders, labels, text, props, extra characters, or watermark;
> nothing clipped.

### Biped walker — edited pass

> Edit the provided sprite sheet only to make the walking cycle unmistakable. Preserve the same
> fictional child character identity, hair, clothes, face, flat sticker style, colors, transparent
> background, exact 2-by-2 layout, scale, and generous spacing. Change only the four poses: frame 1
> heel-strike with left leg forward and right arm forward; frame 2 passing pose with feet close and
> arms crossing through neutral; frame 3 opposite heel-strike with right leg forward and left arm
> forward; frame 4 opposite passing pose. Keep torso and head nearly fixed, feet on one shared
> baseline, each limb silhouette visibly distinct in every frame. True transparent alpha; no text,
> grid, shadows, backdrop, new elements, or clipping.

### Flyer — first pass

> Create one friendly small songbird in a readable four-pose wing-flap cycle. Match the existing
> approved Sketch2Life bird sticker: flat childlike 2D sticker, cheerful solid colors, bold dark
> contour, minimal shading, no glossy 3D. Exactly four full bird poses in a 2-by-2 layout; consistent
> bird identity, side-facing direction, body scale, and pivot; wings clearly show upstroke,
> mid-transition, downstroke, recovery; generous transparent spacing. Genuine transparent
> background; no checkerboard, sky, perch, cloud, shadows, lines, borders, labels, text, extra birds,
> or watermark; no clipping.

### Swimmer — first pass

> Create one friendly little goldfish swimming in a readable four-pose cycle. Match the existing
> approved Sketch2Life ocean-life sticker: simple flat childlike 2D illustration, bright solid fills,
> bold dark outline, minimal shading, no glossy 3D. Exactly four complete fish in a 2-by-2 layout,
> identical fish identity, side-view facing right, same scale and pivot; tail and fins visibly
> alternate in a natural swim cycle while body silhouette stays consistent; transparent spacing.
> True transparent background; no checkerboard, bubbles, water, shadows, grid, labels, text, extra
> animals, or watermark; no clipping.

### Crawler — edited pass

> Edit the provided 2-by-2 sprite sheet only to make a clear slow crawling sequence. Preserve the
> exact same cute snail, shell pattern, face, palette, bold outline, flat sticker style, transparent
> canvas, and cell arrangement. Make the four poses visibly progressive: (1) foot and neck extended
> forward; (2) neck beginning to retract as the foot glides forward; (3) shell/body compresses and
> advances while the head is lower; (4) neck extends forward again with the shell now advanced,
> completing the loop. Keep a consistent shell size and stable ground baseline, with enough
> transparent spacing; do not simply repeat the same pose. True transparent alpha; no ground,
> shadows, labels, grid, text, added objects, or clipping.

### Slitherer — edited pass

> Edit the provided 2-by-2 sprite sheet only so its four poses form a clearly readable slither
> cycle. Preserve the same friendly green snake identity, face, thickness, flat sticker style, bold
> dark contour, colors, transparent canvas, 2-by-2 cell layout, and scale. Keep the head at a
> consistent position and facing direction. Make the body curves distinctly different in sequence:
> broad S bend left, near-straight passing wave, broad S bend right, opposite passing wave; use clear
> but gentle side-to-side body displacement without changing snake length or adding segments. Same
> pivot and roomy transparent gutters. Do not repeat identical body curves. True transparent alpha;
> no grass, shadows, labels, grid, text, extra elements, or clipping.

### Roller — first pass

> Create one small cheerful yellow toy car in a readable four-pose rolling cycle. Match the existing
> approved Sketch2Life vehicle sticker atlas: simple flat childlike 2D sticker art, bright solid
> fills, bold dark outline, minimal shading; no glossy 3D. Exactly four complete side-view cars in a
> 2-by-2 layout, identical car design, scale, orientation, and baseline; body remains stable while
> both wheels rotate through four visibly different spoke positions; transparent padding between
> cells. Genuine transparent background; no checkerboard, road, shadows, speed lines, grid, borders,
> labels, text, extra vehicles, or watermark; wheels and body fully inside canvas.

## Review limits

- Alpha channels and transparent canvas corners were verified for every copied PNG. Several sheets
  include partially transparent anti-aliased edge pixels near the canvas boundary; inspect gutters,
  margins, frame identity, and crop safety before any per-frame registration.
- This is visual concept review, not proof of a seamless loop, consistent exact pivots, rights
  clearance, catalog metadata, production frame boundaries, or Android runtime behavior.
- Owner visual approval applies to every proposed frame ID in the inventory above; it does not
  remove any of these technical, provenance, rights, catalog, or runtime gates.
- The earlier `walker-corgi-cycle-draft.png` and `flyer-songbird-cycle-draft.png` remain preserved
  as prior drafts; this batch is a style-aligned replacement candidate, not an approval or deletion.
- No code/runtime/catalog change is made by this review batch. The approved visual concepts inform
  the separate FEAT-030 subject/behavior registry plan draft; that draft still requires owner review
  and task approval before implementation.

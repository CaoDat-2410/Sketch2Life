# FEAT-028 generated asset provenance

- State: all 24 atlases and their 144 frame entries are GENERATED / REVIEW_PENDING; none is approved, applied, or runtime eligible.
- Generator: built-in ImageGen tool (not CLI/API mode).
- External asset sources: none used.
- Reference media: generated atlas style reference only; no child/user image was provided or used.
- Shared prompt brief: illustration-story; transparent PixiJS sprite atlas; exactly six isolated subjects arranged in a 2-column x 3-row invisible grid; flat 2D childlike doodle, rounded shapes, bold dark outline, simple fills; no text, logos, watermark, scene background, cast shadow, or glow; genuine transparent alpha; generic original art, not based on a real child.
- Frame map: nominal 2 columns x 3 rows of 512x512 cells, row-major; per-frame bounds in asset-catalog.v2.json are authoritative. Science/technology output is 1024x1535, so its final-row frames are 511px high. Inspect crop margins during visual review.
- Style-reference chain: first atlas has no reference; each later prompt used the immediately preceding generated atlas as style-only reference. This provides a consistent generic starter look, not an actual per-child style match. Dynamic local profile adaptation remains planned.

| Atlas | Prompt subjects, row-major | Style reference | ImageGen output file | Generated at (Asia/Saigon) | Bytes | SHA-256 |
|---|---|---|---|---|---:|---|
| weather-sky-atlas-v1.png | smiling sun; fluffy cloud; rainbow; raindrops+puddle; snowflake; lightning bolt | none | exec-54865265-eb89-4886-806e-4bfdd9bbc6e4.png | 2026-09-17 14:13:46 +07:00 | 1608215 | 853f46ee643bfc00f6f1010d841b9527eb94757eb399902e3a3950a2a4f48a31 |
| land-water-atlas-v1.png | mountain; hill+path; lake+reeds; ocean wave; cave entrance; island+palm | weather-sky atlas | exec-1b52ab5f-5099-45c3-9bf2-0cb235865319.png | 2026-09-17 14:17:07 +07:00 | 1538172 | 2bc240f440ef09cb5d2e057dbd717765ce53ac91da790597143ed08223de3c73 |
| plants-atlas-v1.png | leafy oak; pine; sunflower; tulip; potted cactus; leafy vine | land-water atlas | exec-0890d465-ef9b-431e-b607-e23927af8e60.png | 2026-09-17 14:18:38 +07:00 | 1567070 | 98d9cc36c41bbb2c2977884cb0f3db69480435ae52e15e4e9809a2e7f91c8b85 |
| animals-atlas-v1.png | cat; dog; rabbit; songbird; fish; butterfly | plants atlas | exec-668e95f0-a465-4e6c-821c-c19d427c6a24.png | 2026-09-17 14:19:47 +07:00 | 1574424 | 0621d7a241bad318b9e1c53d86122eebd0c9e021bd28f24f3819abbe9b9b035e |
| people-roles-atlas-v1.png | child-short-hair; child-curly-hair; caregiver; teacher; gardener; doctor | animals atlas | exec-7e6d1fa7-3d12-4bed-949f-91747e82fd7b.png | 2026-09-17 14:20:59 +07:00 | 1608421 | 5ab1440d14f4486217d4f695495299ed5ad8ba2fc4778cc0a50b93a58095c95e |
| places-buildings-atlas-v1.png | small house; schoolhouse; barn; arched bridge; tent; fairytale castle | people/roles atlas | exec-fb533916-7577-47bb-ade9-ac7201e6bdaa.png | 2026-09-17 14:22:14 +07:00 | 1592532 | c075303d1db063c6f8a5fc10dd5993bc346a1bccc33f4b0ebc9abf518d1a7e89 |
| transport-atlas-v1.png | bicycle; car; city bus; sailboat; airplane; train | places/buildings atlas | exec-de5bd044-b527-48ce-a3b5-d2a60d96dbfd.png | 2026-09-17 14:23:31 +07:00 | 1484121 | 833d63ccee7827738d6218cfa629257efa3534b513c5409bd4c7702b42086559 |
| food-atlas-v1.png | apple; banana; strawberry; carrot; bread loaf; soup bowl | transport atlas | exec-56b7eb59-3b51-4800-a5ec-8273215eff29.png | 2026-09-17 14:24:45 +07:00 | 1396038 | b8625deb9762e6fd5d832b568aeb548ca9165c22b53c29638e2465b508116e17 |
| everyday-classroom-atlas-v1.png | picture book; pencil; play ball; chair; umbrella; backpack | food atlas | exec-8adda3f2-fcf0-49b8-bba9-51ffdb5cb36e.png | 2026-09-17 14:26:07 +07:00 | 1434937 | c9e620b066e527c28734827641ce706634c9316992ae9deb718ebb62361599fc |
| learning-play-materials-atlas-v1.png | wooden blocks; number rods; counting beads; sorting bowls; pitcher+cup; geometric puzzle board | everyday/classroom atlas | exec-64c58041-5164-43bb-839b-99e151987ada.png | 2026-09-17 14:27:07 +07:00 | 1433006 | e3d3527d7f8341675a4b53ea91a109f10b1b88061caed1d4fe118684122635d7 |
| fantasy-underwater-space-atlas-v1.png | rocket; ringed planet; astronaut; submarine; friendly dragon; mermaid | learning/play atlas | exec-17f2654a-bbd5-4a94-8b45-bd13aecfc2f6.png | 2026-09-17 14:28:30 +07:00 | 1627448 | cb7a3a4d12cc1c626fc536683496b1394abebdd0f6317f008dbab10686857be3 |
| motion-effects-atlas-v1.png | sparkle cluster; bubble cluster; dust puff; motion streaks; swirling leaves; confetti | fantasy/space atlas | exec-b2cc0600-9313-4c80-becc-fdfdb22b27a2.png | 2026-09-17 14:29:39 +07:00 | 1383456 | 2ca9974e7dd49bd44a290bf9fa16a9840a475536b896a85bafea7394cfc8c6b3 |

The local PNG copies under this folder were verified as 1024x1536, 32-bit ARGB, with transparent (alpha=0) top-left pixels. This is a spot check, not full visual/alpha approval. The original ImageGen outputs remain in the local generated-images directory named in the tool output; the repository copies are the feature-owned generated drafts.

## Review decision

Pending project-owner visual review. Do not move/copy any sheet or sprite frame to approved/applied or reference it from runtime until the owner records a decision in assets/REVIEW.md.

## Revision 2 generated atlases — 12 additional packs

- Generator: built-in ImageGen, one distinct generation request per atlas (not CLI/API).
- Prompt set: transparent PixiJS atlas, exactly six named isolated subjects in an invisible 2-column by 3-row grid; flat 2D childlike doodle, rounded forms, bold dark outline, clean fills; no visible grid, scenery, text, logo, watermark, shadow, or glow. Science/technology used no reference image. The other packs requested the latest generated atlas as a style-only reference.
- Reference grouping: science/technology had none; dinosaurs/farm/wild referenced science/technology; ocean/insects/music referenced wild animals; sports/construction/home referenced music; clothing/celebrations referenced home/kitchen. No child artwork or real child media was used.
- Source UTC timestamps, ImageGen output IDs, sizes, and hashes are recorded below. All copies were checked as RGBA with alpha=0 at top-left and six non-empty grid cells. Crop/visual review remains pending; science/technology is 1024x1535 and its final-row frame heights are recorded as 511px in catalog v2.

| Atlas | Prompt subjects, row-major | ImageGen output | Generated at UTC | Bytes | SHA-256 |
|---|---|---|---|---:|---|
| science-technology-atlas-v1.png | microscope; bubbling lab flask; friendly robot; tablet; telescope; circuit board | exec-727c14a9-e460-4efc-becd-04f16a3e5bf6.png | 2026-09-17 07:55:31Z | 888266 | ba4e63983fbc72d0ce7c01798d515b7c77e34785966534281d999411d7546a3c |
| dinosaurs-prehistory-atlas-v1.png | T-rex; triceratops; stegosaurus; long-neck dinosaur; pteranodon; footprint fossil | exec-b7d10c23-e4cd-4a0f-82d5-4f3600fef3b5.png | 2026-09-17 07:56:47Z | 1743867 | ef049f0ede440d5c866f211c547a328a5d3e80f179e22e1d605abf5d5be75842 |
| farm-animals-atlas-v1.png | cow; pig; sheep; horse; hen and chick; duck | exec-553b5825-882a-4da1-9410-b341a8a52dfe.png | 2026-09-17 07:57:33Z | 1718141 | 3e2be01f03c5806f7030633dfbee0b2ed25f88d4ce0c0b3817258f7b624437f1 |
| wild-animals-atlas-v1.png | elephant; lion; giraffe; monkey; tiger; bear | exec-d449966f-0f64-4f91-9743-5cfe9f4bd968.png | 2026-09-17 07:58:23Z | 1766477 | 95205f6deedb6c3351484dd9dbcff56bf6b280f3214047dd7be811781b8a5a11 |
| ocean-life-atlas-v1.png | whale; dolphin; sea turtle; octopus; crab; jellyfish | exec-188d081d-831a-48b5-a73f-6b7aae9d791b.png | 2026-09-17 07:59:26Z | 1850319 | 6d36d3ae2b9c1281ee7a2ed822a8d08a1998587dfd37b3bcad2ea38c88043e04 |
| insects-small-creatures-atlas-v1.png | bee; ladybug; caterpillar; snail; frog; dragonfly | exec-45da5e18-1b0c-42a8-8e5c-7d3e226f5c6b.png | 2026-09-17 08:00:05Z | 1694536 | 57a2bcd2419eaed3cb65dae2e2c125cb6f49a67c38f6b676bfd86e17acd118d8 |
| music-instruments-atlas-v1.png | drum; acoustic guitar; piano keyboard; violin; xylophone; trumpet | exec-70348549-b9e9-4ec6-b0fc-a1aac21ffd2f.png | 2026-09-17 08:01:04Z | 1756230 | 0acdf46c12f482578b6838da2bc0e5318ce154745739bae6558b19d9d8503a1d |
| sports-outdoor-play-atlas-v1.png | soccer ball; basketball; tennis racket; badminton racket; jump rope; swing | exec-8a8dacc5-81b9-4fb7-93d8-b13971467289.png | 2026-09-17 08:02:10Z | 1681483 | 83c1225d5272c368ab6fe498e73893801abdb316f6a19b279f73ddd65438ebbb |
| construction-tools-atlas-v1.png | excavator; tower crane; dump truck; hard hat; hammer; wrench | exec-d27d2496-1a9d-4445-9de5-04ce2db8e71b.png | 2026-09-17 08:02:57Z | 1594945 | 3b9477a9c9d2c9ef2c446548a87c34a3a8bfcdea93fb18394b9b873322fd35f9 |
| home-kitchen-atlas-v1.png | bed; table lamp; sofa; cooking pot; cup and spoon; sandwich | exec-895c7346-a5e7-4412-917d-44af1a2aba09.png | 2026-09-17 08:03:52Z | 1636038 | ef2c219eea3e1bc6cbcf5395ca435e3e077556777f17fa8ef3a8a89b8d028a81 |
| clothing-accessories-atlas-v1.png | t-shirt; rain boots; cap; backpack; eyeglasses; scarf | exec-ad147f6f-1fc1-4de9-bced-4c11534466e4.png | 2026-09-17 08:05:03Z | 1634005 | 1c61af9345dd34df5c1b7ee7a23670de35adf63c032f9c8c04624f61638b679e |
| celebrations-seasons-creative-play-atlas-v1.png | birthday cake; balloons; gift; party hat; autumn leaf; paint palette and brush | exec-03fd31d6-95f8-43b6-bd16-7ba826200dc8.png | 2026-09-17 08:05:52Z | 1677263 | 3d7d3c6f9b2f73bd15819bacb1427965cbcb0c489f92f7f2ed56e5f9778ad0da |

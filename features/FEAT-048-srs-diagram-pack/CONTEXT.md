# FEAT-048 context — SRS v3.1 diagram pack

- Status: IN_PROGRESS — plan 25 / approval 25 final ERD audit and layout refinement PASS locally; publish the approved source/record allowlist to the existing FEAT-048 branch. Drive replacement remains blocked by automatic approval review.
- Owner: Khoa / project owner
- Goal: create an editable Draw.io file and diagram-as-code counterparts for Khoa's assigned ERD, System Architecture, and Package diagrams from the current canonical SRS.
- Scope: one `.drawio` file with three assigned pages plus a separately named architecture comparison page, and Mermaid sources under `src/diagrams/`; the curated sources are published on the FEAT-048 branch. Intended Drive destination for the Draw.io file is the folder supplied by the user (ID `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`).
- Non-goals: runtime/schema/API implementation, choosing unapproved infrastructure, modifying the SRS, publishing or sharing the Drive folder.
- Dependencies: canonical SRS v3.1 at `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`; connected Google Drive access.
- Risks: B7/B21 data model and B8 bounded contexts/contracts are labeled `PROPOSED`; the diagrams must retain those labels and not present them as adopted implementation.

## Context snapshot

### Final ERD audit and layout refinement — 2026-10-23

Fresh B7.1/B21.5 audit found no additional relationship/cardinality mismatch. Final Draw.io and Mermaid sources retain 17 entities, 21 named relationships, and 37 selected attributes. Added an explicit selected-fields/logical-overview caveat; moved ConsentRecord to a clear top-right lane so its `id` no longer overlaps PortfolioEntry's `id`; routed `protected` below PortfolioEntry and added right-edge margin. The final official viewer render passes: every relationship diamond has exactly two endpoints, no dangling references/out-of-bounds vertices, no page/render errors or blocked requests; Mermaid 12.2.0 renders 17/21/37. The three non-ERD tabs are unchanged. Current artifact SHA-256: `b5b33a5f55ccdf88971f686e7d572537f6268620e23dd042238447b2562aa040`. Evidence: `evidence/notes/ERD_FINAL_AUDIT_AND_LAYOUT_20261023.md`, `evidence/metrics/ERD_FINAL_REFINEMENT_VALIDATION_20261023.json`, and the local-only screenshot `evidence/screenshots/erd_final_refinement_20261023_r2.png`.

### ERD repair and source curation — 2026-10-23

Plan 23 / approval 24: local repair PASS. All six formerly detached diamonds now have both correct entity connectors; the three reversed endpoint counts are corrected; protected/Class/shared/personal/owns routes render through distinct corridors. CanvasDocument has exactly one applicable owner mode (group XOR participant); maximum documents per owner remains proposed. New child-authored operations require a selected verified participant even though historical attribution can be optional. Draw.io retains 17 entities/21 named relations/37 attributes and all four tabs; the other three page fingerprints match the fresh baseline. Mermaid ERD and Architecture v2 render at 17/21/37 and 14/19. Evidence: `evidence/notes/ERD_REPAIR_20261023.md`, `evidence/metrics/ERD_REPAIR_VALIDATION_20261023.json`.

GitHub publication is complete on `feature/feat048-srs-diagram-pack`: editable `.drawio`, `logical-erd.mmd`, `system-architecture-v2.mmd`, source README/drawing rules, text-only icon provenance, and necessary textual feature records. Rendered images, builder/renderer scripts, separate icon SVGs, raw Drive baselines and the duplicate Mermaid wrapper are excluded. The same-ID Drive update was rejected by automatic approval review; remote content remains the 153,149-byte baseline until the owner explicitly permits replacing that file.

### ERD recheck — 2026-10-23

Plan 22 / approval 23 review is COMPLETE. Fresh Drive bytes still match the delivered artifact (153,149 bytes, SHA-256 4d5e2f54e0066b8f9e95108ce593ad426ba221c6d89bd43860679ccad3a4ac39). Actual ERD render/XML/SRS review confirms six detached diamonds/twelve missing connector targets and three reversed owner/contributor counts, plus routes hidden behind unrelated shapes or merged with other routes. Scope/field parity passes (17/21/37), current Mermaid syntax/render and reviewerRef representation pass. Model remains NOT_READY. No diagram/source/Drive repair in this review. See evidence/notes/ERD_RECHECK_20261023.md and metrics; latest screenshot erd_recheck_20261023.png.

### Technology logos and Mermaid export — 2026-10-23

Plan 21 / approval 22 completed the five technology marks and two Mermaid sources. The latest ERD repair supersedes the previously documented detached endpoints and reversed counts. Fresh Drive metadata before the repair attempt still matched the 153,149-byte baseline, modified 2026-10-23T05:11:21.479Z; upload was blocked afterward, so there is no repaired Drive readback yet. See `evidence/notes/TECHNOLOGY_LOGOS_AND_MERMAID_20261023.md` for the local artwork provenance history.

### Latest v2 presentation checkpoint — 2026-10-23

Plan 20 / approval 21 is COMPLETE. Removed the eight redundant note/legend/subtitle/footer cells and redrew v2 with short labels, white neutral boundaries, clearer routes and an external frame fitted to its service stack. The 3200×1740 canvas renders to 3168×1692; diagram-architect and senior-architect reviews PASS. Fourteen components, nineteen relationships, all fourteen official AWS SVG payloads and the other three page fingerprints are preserved. The owner-saved tab order is ERD / System Architecture / System Architecture v2 / Package Diagram. Same-ID Drive readback: 154,128 bytes, modified 2026-10-23T04:50:38.358Z, SHA-256 81d34b919b98b03990044b159accba0e9a424c05637f553a98a08f3156007378, identical to the reviewed artifact. Source/provenance/security/async/CRDT caveats remain in evidence/notes/SYSTEM_ARCHITECTURE_V2_CLEAN_REVIEW_20261023.md. ERD repair remains separate and open.

### Latest v2 spacing checkpoint — 2026-10-23

V2 now uses a 3200×2000 canvas, 150/170px inter-column gutters, 90px integration rows, 17px body text and 48px main AWS icons. Diagram-architect and senior-architect reviews pass after actual rendering; semantic text and all 19 relationship signatures are unchanged. Three protected tabs match the freshly read owner-saved Drive baseline. Same-ID update/readback is byte-identical: 158,482 bytes, modified 2026-10-23T04:26:02.598Z, SHA-256 790d2e3981d4c1736bba0b6ad7cb097432aea0e3b6dfe3e0a7bdcbaf8509d614. See evidence/notes/SYSTEM_ARCHITECTURE_V2_SPACING_REVIEW_20261023.md. ERD is not repaired by this spacing increment.

### AWS icon redraw checkpoint — 2026-10-23

Final checkpoint: existing Drive file updated in place to 158,272 bytes, modified 2026-10-23T04:09:01.423Z; raw readback is byte-identical to local (SHA-256 f39862a42fc6da9ead34225b707419d8d4b0c66d662770072f3071cc73dc21e9). V2 has 14 main components, 14 official AWS General/Category SVG cells and 19 valid edges; official viewer render and Mermaid semantic/render checks pass. All three original page fingerprints are unchanged.

The subsequent owner-requested review (plan 18 / approval 19) found the existing ERD is NOT_READY: six detached diamonds/12 unattached endpoints, three reversed ownership/contributor cardinalities, Mermaid syntax failures and reviewer_ref representation mismatch. These findings supersede old structural pass claims. ERD remains preserved; see evidence/notes/DUAL_DIAGRAM_REVIEW_20261023.md.

The owner directly requested official AWS icons and a redraw on the existing v2 tab. This supersedes the earlier Lucide-only choice for that tab while preserving all SRS status boundaries. The current machine has `feature/feat048-srs-diagram-pack` checked out at the repository root; the older sibling FEAT-048 path no longer exists. Fresh Drive metadata still reports the known 134,056-byte four-page artifact, modified 2026-10-22T17:14:24.595Z. Only the v2 tab and its supporting sources/records are in scope.

The user assigned Khoa ERD, System Architecture Diagram, and Package Diagram, requested the framing from SRS v3.1, then supplied a Drive folder and asked Codex to proceed. The canonical SRS is the authority; source register ID `collaborative-srs-v3-20261010` points to FEAT-029. Owner-confirmed technology baseline is Android/React Native plus FastAPI. Logical ERD entities, most architecture choices, realtime transport, and infrastructure candidates remain proposed/TBD.

## Icon preview update — 2026-10-22

- Khoa requested each proposed icon separately for review. A feature-local catalog now shows 16 named Lucide line icons mapped to System Architecture roles: `evidence/rendered/lucide_icon_catalog_preview.png` and `.svg`.
- The catalog is only a preview. Confirmed technology names stay in text; undecided infrastructure remains generic. The Draw.io page, Mermaid source, Drive file, and SRS were not modified.
- Evidence and icon mapping: `evidence/notes/LUCIDE_ICON_CATALOG_PREVIEW_20261022.md`. Final icon selection and application remain pending owner review.

## Mermaid source update — 2026-10-22

Khoa directly requested Mermaid counterparts and a careful review of all three assigned diagrams. The current approved deliverable now includes `src/diagrams/logical-erd.mmd`, `system-overview.mmd`, and `package-diagram.mmd`, alongside the existing Draw.io artifact. Review is limited to the three assigned diagrams; state-machine and activity diagrams are not added without a team allocation change. At this 2026-10-22 checkpoint the owner had asked not to push; approval revision 17 later superseded that restriction for the FEAT-048 branch.

## System Architecture icon demo — 2026-10-22

Khoa requested an image demo before changing the existing diagram, then said the first preview looked AI-generated. Visual revision 11 uses plain Draw.io-style boxes, minimal neutral SVG pictograms, a text list for B8 contexts, and direct solid/dashed connectors. Confirmed technologies and proposed/TBD choices retain separate labels. The preview does not change the Draw.io artifact, Mermaid source, or Drive copy; see `evidence/notes/SYSTEM_ARCHITECTURE_ICON_PREVIEW_20261022.md`.

## Current artifact snapshot — 2026-10-21

- System Architecture layout revision 8 improves whitespace and separates the nine proposed B8 context groupings from the Application/Ports/Adapters flow; the same Drive file was updated and byte-verified. See `evidence/notes/SYSTEM_ARCHITECTURE_LAYOUT_REVIEW_20261021.md` and its geometry preview.

- Generated `artifacts/Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio` with exactly three pages.
- Structural review passed: XML parses, all edge endpoints resolve, the ERD follows B7.1's 16 relationships, and its 1:N marker direction aligns with the source.
- Semantic review covers SRS v3.1 B3/B7/B8/B21; detailed entities/contexts/candidate infrastructure remain visibly proposed.
- The supplied Drive folder was inspected. `Ver_1` contains prior sequence/state diagrams and `OLD` contains archived versions; no ERD, system architecture, or package diagram was present in the root.
- Uploaded the file to the supplied folder and verified its metadata by listing the folder. Drive file ID: `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`.
- Khoa said the first visual version looked too AI-generated and asked whether a diagram skill exists. No dedicated diagram-drawing skill is installed; `senior-architect` covers architecture content, while this revision applies restrained diagram conventions directly.
- Visual revision 2 simplified all pages; revision 3 matches the Chen reference on ERD with a dark grid-free canvas, green entity rectangles, blue relationship diamonds, pink attribute ovals, and underlined keys. Architecture and Package retain white grid-free canvases.
- Updated the same Drive file ID in place. Revision 3 is in the supplied folder; size 65,956 bytes, modified 2026-10-21 12:47:01 UTC.
- Khoa supplied a Chen-style ERD reference. Revision 3 redraws the ERD with entity rectangles, relationship diamonds, attribute ovals, and underlined primary keys while keeping B7.1 cardinalities.
- Khoa then showed the opened ERD and said the light/dark treatment looked awkward. Revision 4 now uses a white canvas like the other pages, muted Chen fills, dark labels, and slightly larger symbol/cardinality text. The other two pages and the diagram content are unchanged.
- Revision 4 was regenerated locally and updated in place in Drive. Readback confirmed the same file ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, the supplied parent folder, and modified time `2026-10-21T13:04:06.349Z`.
- Notation review classifies the page as a proposed conceptual/logical ERD using Chen symbols with `1` / `0..N` min-max labels. All 16 relationship endpoints and labels match B7.1. B7 says Enrollment's final cardinality is TBD; the GroupMembership composite key shown by underlining is an inference because the SRS does not specify its key.
- Rendered-image QA in diagrams.net is still pending; the source and file metadata are verified, but no fresh image render was available in this execution.

## Correctness revision 5 — 2026-10-21

- Khoa approved corrections after the ERD review. The implementation changes only the ERD page and its generator; Architecture and Package source builders were left unchanged.
- The prior Drive ERD had dangling endpoints on `owns`, `checkpoints`, and `reviewed`, and reversed `authorizes` cardinality. All 16 B7.1 relationship diamonds now connect to both endpoints; `authorizes` is Class `1` to TeacherAssignment `0..N`.
- Added selected B21.5 references: OrganizationScope–Class, StudentProfile–ChildParticipant, shared/personal CanvasDocument ownership, optional CanvasOperation contributor, and the TeacherReview reviewer reference. Added notes for exclusive canvas ownership modes, generic `target_kind` scope, and the proposed GroupMembership episode key.
- Scope now explicitly says 16 B7.1 entities plus OrganizationScope and selected B21.5 links, not all 34 B7 dictionary entities. `ConsentRecord.purposes` is marked multi-valued. The SRS itself was not changed.
- Local and Drive readback checks passed: 3 pages (ERD 161 cells, Architecture 38, Package 38), 17 ERD entities, 21 relationship diamonds, no dangling edges, all relationship diamonds have two connectors, correct `authorizes` endpoint labels, and no accidental vertex-box overlaps.
- `owns` now has explicit waypoint routing below SessionGroup and around GroupMembership. Drive readback confirms the two waypoint arrays (2 points and 3 points).
- Drive file ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x` remains in the supplied folder `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`; final readback is 74,783 bytes, modified `2026-10-21T13:49:26.985Z`.
- The source snapshot reviewed for this correction is `origin/dev` commit `f220781876472950093856e97bbdaaec5170a7c1`. B7.1 omissions and the proposed membership key remain SRS follow-up items; no canonical SRS edit was made.
- Rendered-image QA remains pending because a diagrams.net renderer/editor was not available in this execution.

## Visual legend revision 6 — 2026-10-21

- Khoa requested replacing the long ERD notation sentence with concrete symbol annotations. The legend now displays an Entity rectangle, Relationship diamond, Attribute oval, underlined `id` key oval, and a `1 — ◇ — 0..N` endpoint-cardinality example.
- Scope/TBD notes remain separate. They retain the 16 B7.1 + OrganizationScope + selected B21.5 scope, Enrollment TBD, proposed GroupMembership episode key, exclusive canvas-owner modes, optional contributor reference, and DATA-24's broader review targets.
- Before updating Drive, metadata showed a newer owner-saved revision at `2026-10-21T14:02:58.156Z`. The removal of the old footer note was preserved; its needed caveats were moved into the scope note. ERD data vertices retained their values, styles, and positions. Architecture and Package cell IDs, labels, styles, and positions matched the local builders after normalizing default connector style tokens.
- Final Drive readback verified file ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, size 76,421 bytes, modified `2026-10-21T14:10:55.993Z`, and all three expected pages.
- Raw readback confirmed the shape labels and samples, 21 named ERD relationships plus one legend diamond, no unconnected relationships or dangling edges, correct `authorizes` cardinality, and both `owns` waypoint arrays.
- Rendered-image QA remains pending because a diagrams.net renderer/editor was not available.

## Workspace handoff — 2026-10-21

- FEAT-048 is continued in local branch `feature/feat048-srs-diagram-pack`, created from `origin/dev` commit `f220781876472950093856e97bbdaaec5170a7c1`, in `.worktrees/feat048-srs-diagram-pack`.
- The feature folder was copied into that worktree and all 13 files were SHA-256 verified. The separate main checkout is currently on `feature/feat018-p2t5-evaluation-harness`; its local untracked FEAT-018 plan draft was left untouched.
- See `HANDOFF.md` for the current artifact state and the remaining rendered visual QA step.

## System Architecture correction — 2026-10-21

- The latest fetched Drive owner revision contained edits to the ERD page; its ERD and Package pages were preserved exactly while updating System Architecture locally.
- Architecture now represents Application -> outbound ports and proposed adapters -> ports (`implements`), removing direct Application-to-adapter arrows in line with B8 and the repository dependency rule. Revision 7 was synced to the existing Drive file and verified by exact raw-byte SHA-256 readback.
- The page generator now replaces only the Architecture page in an existing artifact so later builds retain owner-authored ERD and Package edits.
- Local and Drive page counts are ERD 168, System Architecture 35, Package 38. Rendered QA remains pending; see `evidence/notes/SYSTEM_ARCHITECTURE_REVIEW_20261021.md`.

## AWS-inspired architecture preview — 2026-10-22

- Khoa requested an SRS-based demo after discussing an AWS-style architecture reference. The separate local preview uses cloud-architecture layout conventions with generic service pictograms and no AWS product names/logos.
- It preserves SRS B8 status: Android/React Native/TypeScript and FastAPI/Python are confirmed; teacher/admin UI frameworks are TBD; B8 contexts and infrastructure/provider choices remain proposed or TBD.
- SVG and 1920×1260 PNG are in `evidence/rendered/system_architecture_aws_style_srs_preview.*`; visual review is in `evidence/notes/SYSTEM_ARCHITECTURE_AWS_STYLE_PREVIEW_20261022.md`.
- Draw.io, Mermaid, canonical SRS, and Drive are unchanged. The preview is local to FEAT-048 and no GitHub push occurred.

## System Architecture v2 — 2026-10-22

Khoa requested a more conventional, Draw.io-native architecture version with a Mermaid counterpart and explicit drawing rules after reviewing the AWS-inspired preview. Page 4, `System Architecture v2`, uses editable stock shapes, orthogonal connectors, restrained white/gray surfaces, and visible text labels for status. It adds no AWS products, logos, or deployment claims. The original ERD, System Architecture, and Package Diagram page fingerprints were preserved from the latest owner-saved Drive baseline. SRS B8 and repository policy still govern confirmed facts, candidates, proposals, and TBD decisions; see `ARCHITECTURE_DRAWING_RULES.md` and `evidence/notes/SYSTEM_ARCHITECTURE_V2_20261022.md`.

The same Drive file ID was updated in place and finally read back at 113,485 bytes, modified `2026-10-22T16:53:42.570Z`, in the supplied folder. The raw response declares four pages and contains `System Architecture v2` with separate confirmed-surface / TBD-framework labels. FEAT-048 remains local; no commit or push occurred. diagrams.net/Mermaid rendered-image QA remains pending.

## Lucide icons applied to System Architecture v2 — 2026-10-23

After Khoa pointed out that the discussed icons were missing, revision 14 applied the previously previewed Lucide v1.61.0 set to selected primary nodes on page 4. The page contains 20 embedded SVG image cells across 16 icon types; the nine B8 context cards and most adapter rows remain text-only. Icons are neutral role cues and do not encode status. The Mermaid source includes the icon mapping in comments, and the drawing rules describe placement, licensing, status, and offline embedding. Local SVG sources, license notices, and checksums are retained in `assets/icons/lucide-v1.61.0/`.

The Draw.io builder validated the 107-cell v2 page (81 vertices, 24 edges, and 2 root cells) with zero dangling edge endpoints and confirmed unchanged fingerprints for the original three pages. Drive readback on 2026-10-23 confirmed the same file ID and parent folder, 130,669 bytes, modified `2026-10-22T17:05:18.037Z`, four pages, and 20 v2 image cells. This is structural/source readback, not rendered visual QA; diagrams.net inspection remains pending. See `evidence/notes/SYSTEM_ARCHITECTURE_V2_ICONS_20261023.md` and `evidence/raw/DRIVE_READBACK_SYSTEM_ARCHITECTURE_V2_ICONS_20261023.txt`.

## Lucide image URI repair — 2026-10-23

Khoa shared a screenshot showing broken-image placeholders. The SVG data URI had `;base64` inside a semicolon-delimited Draw.io style value, which split the image source. The builder now percent-encodes local SVG sources, parses all 20 decoded payloads, and rejects invalid/external image URIs. Plan revision 15 / approval revision 16 record the correction. Same-ID Drive readback confirms the corrected styles in all 20 image cells. Pixel-level verification in diagrams.net remains pending because this environment has no Draw.io renderer; see `evidence/notes/SYSTEM_ARCHITECTURE_V2_ICON_RENDER_FIX_20261023.md`.

## Cross-machine continuation — 2026-10-23

Khoa authorized committing and pushing `feature/feat048-srs-diagram-pack` so work can continue on another machine, superseding the earlier no-push instruction for FEAT-048. The branch remains separate from `dev` and FEAT-018. Plan revision 16 / approval revision 17 record this publication scope. `HANDOFF_FOR_NEW_SESSION.md` contains checkout steps, artifact/Drive links, icon fix evidence, and the remaining diagrams.net visual-QA step. No `dev` merge was requested.


## Cross-machine handoff update — 2026-10-23

The expanded standalone handoff is HANDOFF_FOR_NEW_SESSION.md. Khoa explicitly authorized publishing FEAT-048 on feature/feat048-srs-diagram-pack; the branch is pushed and remains separate from dev and FEAT-018. The main checkout may be on FEAT-018, so continue in the FEAT-048 worktree/branch. The handoff records all four Draw.io pages, Mermaid sources, current Drive state, icon URI repair, validation results, pending rendered QA, and an ERD Mermaid/Draw.io relationship-count discrepancy that must be reconciled.

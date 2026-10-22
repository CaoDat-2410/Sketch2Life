# FEAT-048 context — SRS v3.1 diagram pack

- Status: IN_PROGRESS — original three pages remain preserved; System Architecture v2 now includes the previously previewed Lucide icons and is synced to Drive; rendered QA is pending
- Owner: Khoa / project owner
- Goal: create an editable Draw.io file and diagram-as-code counterparts for Khoa's assigned ERD, System Architecture, and Package diagrams from the current canonical SRS.
- Scope: one `.drawio` file with three assigned pages plus a separately named architecture comparison page, and Mermaid sources under `src/diagrams/`; intended Drive destination for the Draw.io file is the folder supplied by the user (ID `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`). Mermaid sources remain in the repository worktree.
- Non-goals: runtime/schema/API implementation, choosing unapproved infrastructure, modifying the SRS, publishing or sharing the Drive folder.
- Dependencies: canonical SRS v3.1 at `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`; connected Google Drive access.
- Risks: B7/B21 data model and B8 bounded contexts/contracts are labeled `PROPOSED`; the diagrams must retain those labels and not present them as adopted implementation.

## Context snapshot

The user assigned Khoa ERD, System Architecture Diagram, and Package Diagram, requested the framing from SRS v3.1, then supplied a Drive folder and asked Codex to proceed. The canonical SRS is the authority; source register ID `collaborative-srs-v3-20261010` points to FEAT-029. Owner-confirmed technology baseline is Android/React Native plus FastAPI. Logical ERD entities, most architecture choices, realtime transport, and infrastructure candidates remain proposed/TBD.

## Icon preview update — 2026-10-22

- Khoa requested each proposed icon separately for review. A feature-local catalog now shows 16 named Lucide line icons mapped to System Architecture roles: `evidence/rendered/lucide_icon_catalog_preview.png` and `.svg`.
- The catalog is only a preview. Confirmed technology names stay in text; undecided infrastructure remains generic. The Draw.io page, Mermaid source, Drive file, and SRS were not modified.
- Evidence and icon mapping: `evidence/notes/LUCIDE_ICON_CATALOG_PREVIEW_20261022.md`. Final icon selection and application remain pending owner review.

## Mermaid source update — 2026-10-22

Khoa directly requested Mermaid counterparts and a careful review of all three assigned diagrams. The current approved deliverable now includes `src/diagrams/logical-erd.mmd`, `system-overview.mmd`, and `package-diagram.mmd`, alongside the existing Draw.io artifact. Review is limited to the three assigned diagrams; state-machine and activity diagrams are not added without a team allocation change. FEAT-048 is local-only per the owner's explicit no-push instruction.

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

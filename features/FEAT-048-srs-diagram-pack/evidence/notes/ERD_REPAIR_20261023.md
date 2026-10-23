# ERD repair and Mermaid source selection — 2026-10-23

**Local repair: PASS. Drive sync: blocked by automatic approval review.** Plan 23 / approval 24 records Khoa's direct request. The repaired Draw.io file, Mermaid sources, rendered evidence and current feature records are local in FEAT-048.

## Source and preservation

- Authority: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` v3.1, source-register ID `collaborative-srs-v3-20261010`, sections B7/B7.1 and B21.5. The relevant statements are DATA-15 (line 1634), DATA-17 (1638), DATA-24 (1654–1656), CS-008 (876), and the ownership invariant (1688).
- Fresh Drive metadata immediately before the attempted update still matched the reviewed baseline: file `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, parent `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`, 153,149 bytes, modified `2026-10-23T05:11:21.479Z`; baseline SHA-256 `4d5e2f54e0066b8f9e95108ce593ad426ba221c6d89bd43860679ccad3a4ac39`.
- Local repaired artifact: 153,869 bytes, SHA-256 `ede63ac3f48db3b072be46e4d5017270988fd218fdc37b41b560538bb868ff43`. Page order remains ERD / System Architecture / System Architecture v2 / Package Diagram. The other three pages match the fresh baseline fingerprints exactly.
- Canonical SRS, runtime/schema, Drive file identity, destination folder, and the other three Draw.io pages were not changed locally.

## Repairs

- Reattached all twelve formerly floating edge targets to the six intended diamonds: `228/229 → 266 contains`, `234/235 → 267 has`, `240/241 → 268 owns`, `246/247 → 269 checkpoints`, `252/253 → 270 reviewed`, and `261/262 → 271 personal canvas`. Removed the old absolute target points. All 21 named relationship diamonds now have degree two; all 79 ERD edges resolve.
- Reversed the entity-end counts for shared canvas, personal canvas, and operation attribution. Group/participant ends show `0..1`; document/operation ends show `0..N`. The `0..N` number of documents per group/participant remains proposed because the SRS does not settle that maximum. Exactly one owner mode applies to a CanvasDocument: shared group XOR personal participant.
- Kept historical operation attribution optional. DATA-17 and CS-008 still require a selected, verified, bound participant for each new child-authored operation.
- Rerouted edge 222 below the `collects` diamond and PortfolioEntry; moved Class attributes away from `contains` with separate paths; routed shared-canvas edges 258/259 through separate corridors; separated the session `owns` paths and the personal-canvas path. The actual diagrams.net render was visually inspected.
- Clarified endpoint-count notation, the proposed canvas count, and that `reviewed` shows only the SketchProposal review subset; DATA-24 also supports knowledge-video and learning-content review targets.

## Source parity and render evidence

- ERD remains the same logical overview: 17 entities, 21 named relationships, and 37 displayed attributes. Physical foreign-key columns are not claimed by this Chen overview.
- `src/diagrams/logical-erd.mmd` now mirrors the corrected counts and qualifications; SHA-256 `82066252a5a451a5e43ac67f51558b53685be288638f4102ed035c553b167a92`. Mermaid 12.2.0 parsed and rendered 17 entities, 21 relationships and 37 attributes with no browser errors or external requests.
- `src/diagrams/system-architecture-v2.mmd` remains 14 components and 19 flows; its comments now describe embedded Draw.io marks without requiring external SVG assets. SHA-256 `c82430d41055b5c4743ddfc62cdb99631a6416c22bb575bc3347fd30c729c05a`; Mermaid 12.2.0 rendered with no browser errors or external requests.
- `artifacts/MERMAID_DIAGRAMS.md` is synchronized with both `.mmd` files as a local copy-and-paste convenience. GitHub will use the two `.mmd` sources directly.
- Actual Draw.io render uses the cached official diagrams.net viewer, 3401×1987, 168 cells including the two roots, with no failed images, page errors or blocked requests. PNG/SVG and renderer metadata remain local evidence and are excluded from GitHub.

## Curated GitHub file selection

Publish the editable artifact and current source counterparts:

- `artifacts/Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio`
- `src/diagrams/logical-erd.mmd`
- `src/diagrams/system-architecture-v2.mmd`
- `src/diagrams/README.md`
- textual FEAT-048 plan, approval, decision, status, handoff, and ERD repair evidence records needed to explain the delivered state

Exclude rendered PNG/SVG files, the combined duplicate Mermaid wrapper, `src/build_drawio.py`, `src/add_system_architecture_v2.py`, renderer scripts, original icon SVG bundles, temporary inputs, and raw Drive baseline/readback files. The `.drawio` source embeds its marks and remains editable; separate image exports are not needed.

## Drive status

The same-ID update was attempted after a fresh metadata check but automatic approval review rejected it. Its stated reason was that the transcript did not explicitly authorize replacing that specific existing Drive file with this private Draw.io artifact and did not establish trusted account ownership. No alternate upload path was used. Drive therefore remains at the baseline revision above; no post-update readback exists yet.

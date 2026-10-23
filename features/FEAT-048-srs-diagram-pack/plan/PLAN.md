# Feature plan — SRS v3.1 diagram pack

- Status: IN_PROGRESS
- Plan revision: 26
- Implementation status: IN_PROGRESS

## Goal

Create a clear, editable Draw.io file and Mermaid source files for the three diagrams assigned to Khoa, grounded in canonical SRS v3.1.

## Current increment — final ERD audit and visual refinement (2026-10-23)

- Status: COMPLETE — final ERD audit/refinement and curated GitHub publication PASS in commit `2c37ad97` on `feature/feat048-srs-diagram-pack`.
- Plan revision: 25; approval revision 25.
- AC-51: PASS — compared all 16 B7.1 relationships plus five selected B21.5 links, current endpoint counts, and displayed fields. No additional relationship/cardinality defect was found; Enrollment, GroupMembership key, per-owner CanvasDocument count, historical attribution, and DATA-24 review target scope remain explicitly unresolved/proposed. The audit is recorded in `evidence/notes/ERD_FINAL_AUDIT_AND_LAYOUT_20261023.md`.
- AC-52: PASS — preserved 17 entities/21 relations/37 selected attributes and added the explicit selected-fields/logical-overview caveat without changing the SRS or implying a physical schema.
- AC-53: PASS — refined the ConsentRecord/PortfolioEntry spacing, protected route, right margin, and caveat hierarchy; retained conventional Chen notation, white canvas, and restrained colors. The final actual render has no overlapping attributes.
- AC-54: PASS — the final 3372×1987 diagrams.net render has no failed images, page errors, blocked requests, dangling references, or out-of-bounds vertices; all 21 relationship diamonds have degree two. Mermaid 12.2.0 renders 17/21/37 with no errors. The three other Draw.io pages are byte-equivalent after XML canonicalization.
- AC-55: PASS — updated FEAT-048 evidence/status and published only the editable `.drawio`, changed `.mmd` source, and text records in commit `2c37ad97`; generated images, icon SVGs, and render/build scripts were excluded.

## Current review — user screenshots versus published ERD (2026-10-23)

- Status: COMPLETE — provided screenshots match the last-known Drive baseline; the current published ERD passes the full structural and bounds audit, so no diagram-source change is needed.
- Plan revision: 26.
- AC-56: PASS — the supplied crops match the last-known Drive baseline hash `4d5e2f54…ac39`, which has six detached relationship diamonds and 12 unbound targets; current published source is hash `b5b33a5f…a040`. The prior viewer render and source metadata confirm the baseline version.
- AC-57: PASS — all 21 current relationship diamonds have exactly two bound entity connectors, all references resolve, all endpoint counts match the reviewed SRS model, and no vertex lies outside the 3400×2050 page. Blue selection controls are editor UI only.
- AC-58: PASS — recorded the old/current version comparison and screenshot explanations in `evidence/notes/ERD_USER_SCREENSHOT_AUDIT_20261023.md`; no current-source defect remains to fix.
- AC-59: PASS — only text evidence/status will be published; user screenshots and rendered media remain local, and Drive replacement was not performed in this review.

## Planned increment — ERD repair and GitHub source curation (2026-10-23)

- Status: IN_PROGRESS — local ERD repair/render and Mermaid sources are complete; curated GitHub publication passed in commits `2432fd0e` and `197048d7`. Same-ID Drive replacement was rejected by automatic approval review and remains blocked pending explicit permission.
- Repair the current ERD page and `src/diagrams/logical-erd.mmd` against the latest review and canonical SRS v3.1 B7/B7.1/B21.5. Bind both connector halves to all six detached relationship diamonds; correct the three reversed endpoint counts; keep conditional CanvasDocument owner XOR, optional historical contributor reference, and unresolved 0..N document counts accurately qualified.
- Reroute the verified protected, Class-attribute, and shared-canvas paths so they stay attached, avoid unrelated shapes, and remain distinguishable. Clarify that cardinality labels are endpoint counts and that `reviewed` denotes the sketch-review subset.
- Preserve the 17 entities, 21 named relationships, 37 displayed attributes, other three Draw.io pages, owner tab order, and canonical SRS. The existing Drive file was checked immediately before the update; automatic approval review rejected replacing it, so leave Drive unchanged and record the blocker.
- GitHub deliverable shortlist: editable `.drawio` artifact plus the two requested `.mmd` sources (`logical-erd.mmd` and `system-architecture-v2.mmd`) and the necessary feature plan/approval/review/status records. Exclude rendered PNG/SVG outputs, renderer/build scripts, temporary inputs, and Drive baseline/readback copies from publication. Do not stage unrelated files or publish images.
- AC-45: PASS — all 21 relationship diamonds have exactly two bound connector edges whose source/target entities and relationship IDs are correct; no dangling or floating endpoints remain.
- AC-46: PASS — shared-canvas, personal-canvas, and contributor counts are on the correct endpoints; owner-mode XOR and conditional ownership remain explicit; unconfirmed per-owner maxima remain proposed.
- AC-47: PASS — verified crossing/merged paths use distinct orthogonal corridors; the final actual Draw.io render was visually reviewed.
- AC-48: PASS — Mermaid retains the same 17/21/37 ERD overview, corrected counts and qualifications, and renders successfully; the architecture source remains 14/19 and also renders.
- AC-49: PASS — published the editable `.drawio`, two current `.mmd` sources, source README/drawing rules, text-only icon provenance, and necessary FEAT-048 records in commits `2432fd0e` and `197048d7`. Render images, builder/renderer scripts, temporary/raw Drive copies, standalone icon SVGs, duplicate wrapper, and unrelated worktree files were excluded.
- AC-50: BLOCKED — replace the existing Drive file only after explicit permission is granted for this payload and destination; verify the same-ID raw readback without changing its parent or owner-saved tabs.

## Previous review — ERD recheck (2026-10-23)

- Status: COMPLETE — fresh Drive/actual render/XML/Mermaid/SRS recheck recorded; ERD NOT_READY for bindings/cardinality and route ambiguity. No diagram/source/Drive changes; approval revision 23.
- Fetch the latest Drive artifact and compare its ERD with the current Mermaid and canonical SRS B7/B7.1/B21.5. Review entity scope, displayed attributes/keys, relation endpoints, cardinality, ownership/attribution constraints and known pending findings.
- Inspect an actual official-viewer ERD render and current Mermaid parser/render evidence. Distinguish syntax/export acceptance from domain/model correctness, and distinguish a logical overview from a physical database schema.
- AC-43: findings identify exact affected relationships/cells/source lines, SRS support, practical meaning and an appropriate correction or unresolved assumption. Confirm previously fixed parser/representation issues separately from remaining ERD defects.
- AC-44: feature-local review/metrics/current status record the fresh baseline and conclusions; Draw.io/Mermaid/SRS/runtime/schema and Drive bytes remain unchanged in this review.

## Previous increment — technology logos and two Mermaid sources (2026-10-23)

- Status: COMPLETE — five official technology logos verified/rendered, both Mermaid sources and combined wrapper delivered, independent review PASS, same-ID Drive readback byte-identical; approval revision 22. ERD model issues remain a separate open scope.
- Replace five named-technology icons on System Architecture v2 with unmodified official FastAPI, Firebase, React Native, PostgreSQL and Redis artwork. Retain AWS General/Category symbols for logical roles and undecided storage/AI capabilities, all existing component text/statuses, geometry and 19 flows.
- Record exact official asset URLs, hashes, source revision where available, usage terms and icon mapping. Preserve original artwork/aspect ratio and keep embedded images offline.
- Read the latest owner-saved Drive artifact, preserve ERD/original Architecture/Package tabs and tab order, change only v2 icon cells, render/review and update the same Drive ID with raw-byte readback.
- Produce two usable, portable Mermaid sources for the actual current ERD and System Architecture v2. Architecture retains 14 components and 19 directed/dashed flow semantics; record mixed icon mapping in comments without mandatory external icon packs.
- ERD counterpart mirrors the 17 displayed entities, 21 named relations, shown overview attributes and reviewerRef attribute representation. Repair Mermaid syntax/quoting, not the Draw.io model: preserve and explicitly document the three known reversed cardinalities and detached-diamond source issues rather than silently changing the diagram being exported. Keep source-backed caveats in comments/evidence and preserve the previous source snapshot.
- Provide a feature-local Markdown wrapper containing both Mermaid code blocks for convenient review/copy. Parse/render both actual final sources using the pinned available Mermaid runtime.
- AC-40: five official technology logos replace their generic symbols; nine AWS icons remain; total 14 embedded images, all verified original SVG bytes and no broken images in the actual render.
- AC-41: all non-icon v2 cells and 19 flow semantics, three protected pages and owner tab order match the fresh baseline; same-ID Drive readback equals the rendered artifact.
- AC-42: ERD and architecture Mermaid parse/render successfully; entity/attribute/relation representation is traceable to the displayed diagrams; known ERD model errors are documented separately from parser success. Both sources and the combined code wrapper are delivered.
- No runtime/schema/SRS edit, automatic ERD model repair, commit, push or merge in this increment.

## Previous increment — simplify v2 presentation (2026-10-23)

- Status: COMPLETE — clean v2 rendered, diagram/architecture reviews PASS, graph/icons/protected tabs verified and same-ID Drive raw readback is byte-identical; approval revision 21.
- Remove explanatory note boxes, the large legend, redundant status repetition and provenance text from the v2 canvas. Retain source/usage/security/architecture explanations in feature records.
- Redraw as a restrained engineering diagram: white background, thin neutral boundaries, short component labels, official unmodified AWS General/Category SVGs, clear orthogonal routes and balanced whitespace. Keep the expanded readable scale.
- Preserve the 14 logical components, nine domain contexts, six port/adapter mappings and 19 flow/dependency directions. Retain concise explicit candidate/proposed/TBD qualifiers so simplification cannot freeze undecided technologies.
- Start from the freshly fetched owner-saved Drive revision; preserve the other three pages. Render, inspect and review the final v2 using diagram-architect and senior-architect, then replace the same Drive file and verify raw readback.
- AC-37: no standalone explanatory note boxes or large legend remain; the rendered page is readable with short labels, consistent styling, no clipped text and no routes crossing unrelated component interiors.
- AC-38: graph endpoints/directions, official icon payloads and protected-page fingerprints remain correct against the fresh baseline; Mermaid remains semantically consistent and detailed caveats survive in evidence.
- AC-39: actual rendered review and same-ID byte-identical Drive readback are recorded inside FEAT-048. This increment does not repair ERD, change the SRS/runtime/schema or authorize a commit/push.

## Previous increment — expand v2 layout and review (2026-10-23)

- Status: COMPLETE — expanded layout, actual render, diagram/architecture review and same-ID readback PASS; approval revision 20 records the owner's two direct instructions.
- Expand only System Architecture v2 from its cramped 2400×1580 layout: provide wider inter-column gutters, taller integration rows/cards, larger text and separate connector corridors. Keep the editable canvas and official AWS General/Category artwork.
- Preserve all 14 logical components, 19 relationships, statuses, source text semantics, and original three tab fingerprints; do not repair ERD or select technology in a spacing task.
- After rendering, apply diagram-architect and senior-architect to review readability, endpoints, arrow direction, ports/adapters, realtime and async completion against SRS B3/B8. Record actual results, including unresolved limitations.
- AC-34: v2 has materially larger clearances and readable labels without clipped/overlapping cards or hidden edges in the actual diagrams.net render.
- AC-35: logical graph and image bytes remain unchanged; same-ID Drive readback matches the reviewed artifact and protected tabs match the freshly checked baseline.
- AC-36: feature-local review note and screenshot record diagram/architecture validation after the spacing change.

## Current review — ERD and architecture correctness (2026-10-23)

- Status: review COMPLETE with actionable ERD findings; direct owner request recorded as approval revision 19. Feature remains IN_PROGRESS pending ERD repair.
- Review the actual ERD and architecture pages with diagram-architect, database-architect and senior-architect against canonical SRS B3/B7/B7.1/B8/B21.5; do not rely on historical pass claims.
- Render the actual ERD and current AWS v2 with the official diagrams.net viewer. Compare logical Mermaid cardinalities, endpoint attachment, labels and scope with the Draw.io pages.
- Distinguish the unchanged Lucide Drive copy from the AWS redraw currently local. Verify official AWS asset identity and actual contrast before completing the already authorized same-ID v2 update.
- Record specific findings and evidence, including unresolved ERD issues. Preserve ERD bytes during this review; no SRS/schema/runtime change or automatic ERD repair is included.
- AC-33: review findings identify exact relation/component references and supporting SRS sections, with rendered evidence and current-vs-historical status.

## Current increment — AWS icons on System Architecture v2 (2026-10-23)

- Status: COMPLETE — official AWS sources, v2 redraw/render, Mermaid parity and same-ID Drive readback verified; direct owner instruction is recorded in approval revision 18.
- Redraw only the existing `System Architecture v2` tab with official AWS Architecture Icons. This supersedes the earlier Lucide-only presentation choice for that tab; it does not select AWS hosting or AWS services.
- Use source-backed general/resource icons with original colors and preserve their provenance. Do not map generic PostgreSQL, Redis/RQ, identity or AI capabilities to unselected RDS, SQS, Cognito or Bedrock services.
- Keep about 14 main components: three client surfaces; API; application; grouped domain contexts; grouped outbound ports; aligned adapters; five external capability boundaries; a separate worker. Retain all nine B8 context names and six port/adapter mappings as readable detail.
- Show WebSocket as a proposed client/backend transport via the backend realtime adapter, following SRS B3/B8. Keep runtime calls distinct from inward adapter-to-port dependencies and draw typed async completion back to Application for scope/version checks.
- Preserve the original ERD, System Architecture and Package Diagram pages, including owner edits. Read the latest same-ID Drive file before replacing only v2; keep the supplied parent folder and sharing unchanged.
- Update the v2 Mermaid counterpart, drawing rules, context, decisions, handoff/status and feature-local evidence. Only diagram-generation tooling may change; no application/runtime/schema/SRS changes, commits, pushes or merges are authorized by this increment.
- AC-28: official AWS icon sources, package version, checksums, original names and mappings are recorded; embedded SVGs decode correctly and use no remote runtime assets.
- AC-29: exactly four tabs remain; canonical fingerprints of the three protected tabs match the freshly read baseline; only v2 is redrawn.
- AC-30: v2 has valid endpoints, readable status labels and routes; inspect an actual diagrams.net render when possible, otherwise distinguish a generated preview from official renderer QA.
- AC-31: same-ID Drive update is verified by a fresh raw readback and unchanged parent folder; report an unavailable connector or materialization honestly.
- AC-32: Mermaid and Draw.io agree on the grouped components, six port mappings, proposed realtime path and async result flow. Rendering and semantic checks are recorded separately.

## Scope

- Page 1: conceptual Chen ERD for the 16 B7.1 core entities/relationships plus OrganizationScope and selected B21.5 references, with selected attributes and cardinalities.
- Page 2: system architecture showing actors/clients, API, application/domain boundaries, ports/adapters, external providers, persistence and async/realtime candidates.
- Page 3: UML-style package diagram showing bounded contexts and inward dependency direction.
- Comparison tab: System Architecture v2 uses editable shapes and official AWS General/Category SVGs. Owner plan 20 removes the on-canvas legend/notes; full drawing rules and caveats remain in feature records. The original architecture tab remains preserved.
- Provide semantic Mermaid source counterparts for all three pages under `src/diagrams/`: logical ERD, System Overview/Architecture, and Package Diagram. Keep the Draw.io artifact as the editable visual companion; the Mermaid files are the diagram-as-code sources in the repository.
- Re-review all three diagrams against SRS v3.1 before finalizing the Mermaid sources. Retain the current ERD scope (B7.1 core plus selected B21.5 links), and do not expand to unassigned state-machine/activity diagrams in this increment.
- Distinguish confirmed facts from proposed/TBD design with concise component/flow labels. Plan 20 supersedes the earlier v2 legend requirement.
- Save the source file in this feature's `artifacts/` directory and target the user's supplied Drive folder for upload when Drive write access is available.
- Revision 2: respond to the owner's visual review by simplifying the page treatment and improving readability while preserving SRS meaning.
- Revision 3: redraw the ERD in Chen notation to match the owner's reference image: entity rectangles, relationship diamonds, attribute ovals, and underlined primary keys. Leave the other two pages unchanged.
- Revision 4: make the ERD canvas light to match the other pages and restore comfortable contrast after the owner found the dark/light treatment awkward. Slightly increase symbol labels while retaining the existing layout.
- Revision 5: repair the ERD in response to the owner's correctness review. Preserve all 16 B7.1 relationships, repair all missing connector endpoints, correct `authorizes`, add the B21.5 relationships identified in review, make `GroupMembership`'s episode identity a clearly marked proposal, distinguish the multi-valued consent purposes attribute, clarify the ERD's scope, and keep the other two pages unchanged. Update the existing Drive file in place.
- Revision 6: replace the ERD's long prose legend with a visual key using the actual entity, relationship, attribute, and key shapes plus a cardinality example; keep scope and unresolved caveats in a separate compact note. Preserve the other pages and update the same Drive file.
- Revision 7: respond to the owner's visual review of System Architecture by increasing whitespace, regrouping the nine proposed B8 contexts into a 3×3 grid, and separating use cases, outbound ports, and infrastructure adapters into clear areas. Preserve all B8 meaning, the other two pages, and the same Drive file identity.
- Revision 9: produce a local System Architecture image preview with restrained SVG-style pictograms, following SRS v3.1 and the existing Mermaid source. Mark Android/React Native and FastAPI/Python confirmed; keep undecided infrastructure vendor-neutral and visibly PROPOSED/TBD. This is a review preview only; do not replace the Draw.io page or edit/upload diagram sources in this step.
- Revision 10: revise the icon preview after the owner said it looked AI-generated. Use conventional Draw.io-style square component boxes, a white canvas, a compact legend, fewer icons/status badges, a plain list for the nine contexts, and direct connector routing. Keep the existing Draw.io/Mermaid/Drive files unchanged while presenting the revised preview.
- Revision 11: create a separate icon catalog sheet so the owner can inspect each proposed Lucide SVG icon individually before any diagram source is changed. Map each icon to its architecture role, use one consistent outline style, and keep the catalog preview separate from Draw.io, Mermaid, and Drive artifacts.
- Revision 12: create a separate AWS-inspired architecture preview following SRS v3.1. Reuse the familiar boundary-and-service-icon visual language, but keep the diagram vendor-neutral: show only SRS-confirmed technologies as confirmed and label undecided infrastructure/provider choices `PROPOSED` or `TBD`. Store only a feature-local SVG/PNG preview and leave Draw.io, Mermaid, SRS, Drive, and GitHub unchanged.
- Revision 13: add a clearly named System Architecture v2 comparison page to the existing Draw.io file without replacing its original three pages; create a semantically corresponding Mermaid source and a concrete drawing-rules guide. Use Draw.io-native shapes, orthogonal connectors, restrained status styling, and only SRS-backed technologies. Preserve undecided choices as candidates/proposals/TBD; update the existing Drive artifact in place after fresh metadata/readback checks; do not change the canonical SRS or push the local branch.
- Revision 14: apply the Lucide icon family already previewed to selected primary nodes in System Architecture v2. Use a small consistent outline treatment, embed SVGs locally in the Draw.io file, document icon meaning/provenance/license, and keep status encoded in text. Add the icon mapping to the Mermaid source as comments. Preserve the three original pages, update the same Drive file in place after readback checks, and do not change the SRS, runtime code, or push the local branch.
- Revision 15: repair the v2 icon data-URI serialization after the owner reported broken-image placeholders. Encode SVG payloads so Draw.io style delimiters cannot split the image URL; validate the encoded payloads and preserve the page/file identity while updating the same Drive file.
- Revision 16: prepare this feature for continuation from another machine. Write a complete handoff record with the local/remote branch, source baseline, artifacts, Drive location, validation state, icon serialization diagnosis, and pending visual QA. The owner explicitly superseded the earlier no-push instruction and authorized two focused commits plus push of the FEAT-048 branch; do not merge into `dev` or touch FEAT-018.

## Steps

1. Use SRS v3.1 B3, B7, B8, B19, B21, and B22 as the source; preserve source labels and unresolved decisions.
2. Generate a native `.drawio` XML document with three editable pages.
3. Review diagram labels, relationships, dependencies, and proposal markers against the source.
4. Record evidence and current upload status. Upload only through the connected Drive tool when it is available.
5. Compare the three Mermaid sources with the Draw.io pages and SRS requirements; record discrepancies and disposition in feature evidence.

## Acceptance criteria

- AC-01: ERD shows the connected entities in SRS B7.1, including roster, session/collaboration, portfolio, and consent, with primary relationships grounded in B7/B21.
- AC-02: ERD and proposed logical schema are explicitly labeled as proposed, not an adopted database migration.
- AC-03: architecture diagram identifies the confirmed FastAPI and Android/React Native clients, keeps domain/application independent from frameworks/providers/storage, and labels unadopted adapters/transports/infrastructure as proposed.
- AC-04: package diagram shows bounded contexts and inward dependencies; infrastructure implements ports and domain has no outward framework/database dependency.
- AC-05: document contains the three assigned editable pages and no legacy Parent/Guide, under-nine, or payment assumptions from superseded SRS versions; any explicitly approved comparison page is separately named and preserves the original pages.
- AC-06: file is saved in the user-provided Drive folder and verified by readback. If Drive operations are unavailable, leave this criterion pending and report the local artifact path accurately.
- AC-07: all pages are grid-free, light-background diagrams with aligned groups and connectors behind nodes; Chen entity, relationship, and attribute symbols use distinct, low-saturation fills with dark labels.
- AC-08: ERD keeps the 16 core B7.1 relationships and uses readable labels; selected fields remain abbreviated to preserve overview scale.
- AC-09: ERD uses Chen symbols and carries all 16 B7.1 relationships with 1-to-0..N cardinalities; selected B7 attributes appear as ovals and primary-key ovals are underlined.
- AC-10: all 16 B7.1 relationship diamonds connect to the correct two entities; every connector endpoint resolves. `authorizes` shows Class `1` and TeacherAssignment `0..N`, matching B7.1.
- AC-11: ERD supplements B7.1 with B21.5-backed links for OrganizationScope–Class, StudentProfile–ChildParticipant, SessionGroup/ChildParticipant–CanvasDocument, and ChildParticipant–CanvasOperation. It explicitly records the `TeacherReview` reviewer reference to AdultAccount. Personal and shared canvas ownership is stated as conditional/exclusive; contributor attribution is optional.
- AC-12: the page labels its scope as the 16 B7.1 core entities plus selected B21.5 relationships, not the complete 34-entity B7 dictionary. Enrollment cardinality, the proposed GroupMembership episode key, and generic `target_kind` review scope are visibly qualified.
- AC-13: `ConsentRecord.purposes` is shown as a multi-valued Chen attribute; `GroupMembership` no longer implies an unqualified `(participantRef, groupRef)` primary key that prevents rejoining the same group.
- AC-14: ERD `owns` is placed so its route does not pass through or visually attach to SessionGroup; the other pages remain semantically and structurally unchanged.
- AC-15: regenerated local artifact and same-ID Drive file both contain the corrected three-page XML; Drive metadata readback confirms the existing file identity and folder.
- AC-16: ERD notation is explained with visible shape examples and a `1 — ◇ — 0..N` cardinality sample. Scope, Enrollment TBD, and proposed GroupMembership episode key remain in a separate readable note.
- AC-17: System Architecture groups the nine proposed B8 contexts in a spaced 3×3 arrangement; actors, clients, API, application use cases, outbound ports, and proposed adapters have distinct non-overlapping areas; connector endpoints resolve and arrows remain consistent with inward dependency direction.
- AC-18: Three Mermaid source files exist in `src/diagrams/`, corresponding to the ERD, System Architecture/System Overview, and Package Diagram pages; they preserve the approved scope and distinguish confirmed, proposed, and TBD design.
- AC-19: The logical ERD source represents the selected B7.1 entities and relationships plus the approved selected B21.5 links, with key/reference fields and cardinalities labeled consistently; it remains a proposed logical model and does not generate SQL or claim an adopted physical schema.
- AC-20: System Overview source shows system components, external service/provider boundaries, and main data flows; Package Diagram source shows package/context boundaries and inward dependency direction. All claims are checked against SRS B8 and repository architecture rules.
- AC-21: a feature-local PNG preview demonstrates the proposed SVG-icon treatment for the System Architecture, keeps the SRS confirmed/proposed/TBD distinction, and does not alter the existing Draw.io artifact, Mermaid source, or Drive file.
- AC-22: the revised preview follows conventional technical-diagram styling, removes repetitive cards/badges and decorative shadows, preserves key SRS components and flows, and remains separate from the current Draw.io/Mermaid/Drive artifacts.
- AC-23: a separate feature-local SVG/PNG contact sheet shows each proposed Lucide icon in its own labeled tile, names the icon and the System Architecture role it represents, and leaves Draw.io, Mermaid, and Drive artifacts unchanged.
- AC-24: a separate feature-local AWS-inspired but vendor-neutral architecture preview follows SRS v3.1 and `system-overview.mmd`; it distinguishes confirmed Android/React Native/TypeScript and FastAPI/Python from proposed/TBD infrastructure, shows the client-to-API request path and asynchronous candidate flow, avoids unapproved AWS product names/logos, and does not modify Draw.io, Mermaid, SRS, Drive, or GitHub.
- AC-25: the Draw.io file has an additional clearly named System Architecture v2 comparison page built from editable Draw.io-native shapes; the original ERD, System Architecture, and Package Diagram pages are preserved. `system-architecture-v2.mmd` expresses the same components, statuses, and principal flows. A drawing-rules guide explains boundaries, shape meanings, status styling, connector meanings, layout rules, and SRS decision limits; the page itself includes a concise legend. PostgreSQL, Redis/RQ, and S3-compatible storage are labeled candidates; WebSocket is proposed; identity/AI providers and deployment topology retain their correct confirmed/proposed/TBD status. The same Drive file ID/folder is updated and verified by readback; no SRS edit or GitHub push occurs.
- AC-26: System Architecture v2 uses the previously previewed Lucide outline icon family on primary actor/client/backend/port/external capability/async nodes, without adding icons to every small context box; icons have one consistent stroke/color/scale and are embedded locally rather than fetched from a CDN. Icon labels and mapping are recorded in Mermaid source comments and the drawing-rules guide. Icons do not encode confirmation status or introduce vendor decisions. Preserve all original pages, SRS meaning, and same Drive file identity; include source/version/license provenance; do not change runtime code or push to GitHub.
- AC-27: every v2 icon cell uses a Draw.io-compatible SVG data URI that does not contain a literal style delimiter in its payload; the local builder verifies that the URI decodes to valid SVG. All previously mapped icons render as images instead of broken-image placeholders, original three pages and same Drive file identity are preserved, and the same Drive artifact is verified by raw readback.
- AC-28: `HANDOFF_FOR_NEW_SESSION.md` lets another machine continue FEAT-048 by identifying the repository branch/base, remote checkout command, Draw.io and Mermaid paths, Google Drive file/folder, icon fix and verification, remaining visual-QA step, and project constraints. The local branch is published to the matching `origin/feature/feat048-srs-diagram-pack` ref in two focused commits, without merging to `dev` or modifying FEAT-018.

## Current verification

- AC-01 through AC-05: PASS. Reviewed against canonical SRS v3.1; proposal markers and dependency boundaries retained.
- AC-06: PASS. Revision 6 was updated in place; raw-content and metadata readback verified the same Drive file ID and destination folder.
- AC-07: source styling is complete across the three pages with a light canvas, muted fills, and dark labels. Rendered-image QA remains pending.
- AC-08: relationship labels and overview fields are preserved. Readability at the user's diagrams.net zoom remains pending rendered QA.
- AC-09: PASS. All 16 B7.1 relationships are represented using Chen notation and their stated cardinalities.
- AC-10: PASS. All 16 B7.1 relationships connect to both intended entities; `authorizes` shows Class `1` and TeacherAssignment `0..N`.
- AC-11: PASS. Selected B21.5 reference links and conditional ownership/optional contributor notes are present.
- AC-12: PASS. The page identifies its limited B7.1/B21.5 scope and visibly qualifies the Enrollment, GroupMembership, and generic review-target assumptions.
- AC-13: PASS. `ConsentRecord.purposes` is double-oval; GroupMembership does not imply a fixed participant/group pair key.
- AC-14: PASS. `owns` has explicit waypoint routing below SessionGroup and around GroupMembership; Architecture and Package builders were not changed.
- AC-15: PASS. The local artifact and same-ID Drive file contain the corrected three-page XML. Drive raw readback verified 76,421 bytes, modified `2026-10-21T14:10:55.993Z`, and the supplied folder.
- Structural/layout verification: PASS. Three pages contain 168/38/38 cells; the ERD has 17 entities and 21 named relationship diamonds plus one legend diamond; named relationships each have two endpoints; zero dangling edges; correct `authorizes` cardinality; zero accidental vertex-box overlaps. Drive readback confirms the two `owns` route arrays with 2 and 3 waypoints.
- Notation/source review: PASS for Chen symbol structure and B7.1 mapping. Enrollment cardinality and `membershipId*` remain provisional; selected B21.5 links are documented as supplemental rather than an SRS amendment.
- Visual render QA: PENDING; no diagrams.net renderer/editor is available in this execution.
- AC-16: PASS. Visible shape examples show Entity, Relationship, Attribute, and underlined Key, plus a `1 — ◇ — 0..N` sample. Scope/TBD/proposal notes remain separate.
- Revision 6 implementation and Drive readback: COMPLETE. Before writing, inspected the newer owner-saved Drive revision; kept its removal of the old footer note, preserved ERD data geometry, and confirmed Architecture/Package cell IDs, labels, styles, and positions match after default-style normalization.
- Visual render QA remains pending; the feature remains IN_PROGRESS only for that rendered inspection.

## System Architecture correction — revision 7 (2026-10-21)

- AC-03: PASS locally. Application uses outbound port contracts; proposed infrastructure adapters implement them. There are no direct Application-to-infrastructure or Application-to-realtime-adapter arrows.
- The correction follows canonical SRS v3.1 B8 and the repository's inward-dependency rule. Realtime/presence is included among proposed infrastructure adapters, and its interface is listed among outbound ports.
- Local structure: 3 pages (ERD 168, System Architecture 35, Package 38 cells); all Architecture edge endpoints resolve. Application links to the ports vertex; the proposed adapter vertex implements those same ports.
- Before Drive sync, fetched the newer owner-saved revision (84,271 bytes, modified `2026-10-21T14:55:37.614Z`). Its ERD and Package pages were preserved byte-for-byte at page level in the merged artifact. Updated the existing Drive file in place; final readback verified 82,965 bytes, modified `2026-10-21T15:01:58.601Z`, same folder and ID, and byte-for-byte SHA-256 equality with the local artifact.
- Rendered visual QA remains pending because a diagrams.net renderer/editor is unavailable in this execution.

## System Architecture layout — revision 8 (2026-10-21)

- Owner approved a layout-only revision after noting that the architecture page was crowded. Canonical SRS v3.1 and all diagram meanings remain unchanged.
- Increased whitespace and arranged the nine B8 proposed context groupings in a 3×3 grid. Actors, clients, FastAPI, Application use cases, outbound ports, and candidate adapters now occupy distinct areas. Each client HTTPS connector has a separate API entry anchor.
- AC-03: PASS — confirmed technologies and surfaces remain distinguished from proposed contexts/infrastructure, and the Application → ports ← adapters dependency direction remains intact.
- AC-17: PASS — XML geometry is within page bounds; all 10 Architecture edges resolve; nine proposed context cards are present; there are zero accidental vertex overlaps; three HTTPS entry anchors are distinct.
- Local artifact: 3 pages (ERD 168, System Architecture 36, Package Diagram 38 cells). Preview is in `evidence/rendered/system_architecture_revision8_preview.png`; it is a geometry/style preview, not a diagrams.net export.
- Updated the existing Drive file in place. Readback verified ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, parent folder `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`, size 83,228 bytes, modified `2026-10-21T15:12:51.660Z`, and byte-for-byte SHA-256 equality with the local artifact.
- Actual diagrams.net rendered QA remains pending because that renderer/editor is unavailable in this execution.

## Mermaid source review — revision 9 (2026-10-22)

- AC-18: PASS for source presence and scope. Added `src/diagrams/logical-erd.mmd`, `system-overview.mmd`, and `package-diagram.mmd`; they correspond semantically to the three Draw.io pages. State-machine/activity diagrams remain outside Khoa's current allocation.
- AC-19: PASS for textual review. The logical ERD has 17 entities and 22 relationship lines: all 16 B7.1 relationships plus six selected B21.5 references. PK/FK/reference fields and proposal caveats are labeled; no SQL or physical-schema claim was added.
- AC-20: PASS for textual review. System Overview names all nine proposed contexts, confirmed client/API choices, candidate persistence/external boundaries, and request/job/result flows. Package Diagram groups client, inbound-adapter, application, domain, and infrastructure namespaces; six infrastructure adapters realize application ports, with no direct application-to-infrastructure dependency.
- AC-21: PASS. A separate SVG/PNG icon demo is rendered and visually inspected; existing Draw.io, Mermaid, and Drive sources are unchanged.
- AC-22: PASS. The revised preview uses a plain white canvas, square technical boundaries, restrained line icons, compact text lists, and clear solid/dashed connectors; all confirmed/proposed/TBD labels and the core SRS components remain visible.
- AC-23: PASS. A feature-local SVG/PNG catalog shows 16 individually labeled Lucide icons and their architecture roles; the source diagram files remain unchanged.
- Static source comparison: all 16 B7.1 relationship names/endpoints match; no unresolved ERD endpoints; all nine contexts and six port realizations are present. Client-to-backend links are labeled as runtime protocols, separate from backend package dependencies.
- SRS boundaries remain explicit: provider names and exact outbound payload fields are TBD; realtime is proposed; Enrollment cardinality is TBD; `membershipId` is proposed; CanvasDocument owner modes are exclusive; consent purposes remain multi-valued with physical normalization TBD.
- Mermaid syntax was checked against the official ERD and class-diagram references. No Mermaid/PlantUML renderer is installed in this worktree, so rendered-image QA remains pending; no visual-render pass is claimed.
- Sources were added to the local FEAT-048 worktree only. No GitHub push or Drive update was made in this revision.

## AWS-inspired architecture preview — revision 12 (2026-10-22)

- AC-24: PASS. Added a separate SVG/PNG concept preview based on SRS v3.1 B8 and `src/diagrams/system-overview.mmd`; confirmed client/API technologies, proposed B8 context groupings, ports/adapters, candidate external capabilities, and the asynchronous worker/result flow are represented.
- The composition borrows AWS architecture diagram conventions (logical boundary, colored square service pictograms, labeled flows) without AWS product names, logos, or deployment claims. Provider and infrastructure choices remain generic and marked `PROPOSED`/`TBD`.
- SVG parsed as XML, rendered with headless Chrome at 1920×1260, and the PNG was visually inspected for readability, connector direction, and label overlap.
- Preview files: `evidence/rendered/system_architecture_aws_style_srs_preview.svg` and `.png`; review record: `evidence/notes/SYSTEM_ARCHITECTURE_AWS_STYLE_PREVIEW_20261022.md`.
- Draw.io, Mermaid, canonical SRS, and Drive were not changed. No commit or GitHub push was made.

## System Architecture v2 comparison page — revision 13 (2026-10-22)

- AC-25: PASS for content, structure, and Drive synchronization. The Draw.io document has four pages: the original ERD, System Architecture, and Package Diagram, plus a separately named `System Architecture v2` page.
- The builder uses editable native Draw.io rectangles, swimlane boundaries, actor symbols, storage cylinders, queue symbol, and orthogonal connectors. It appends/replaces only the v2 page and verifies fingerprints for the original three pages before and after.
- The v2 page contains 87 `mxCell` elements including the two root cells (61 vertices, 24 edges); all 24 edges resolve to existing source and target cells. Main client/API/Application/domain path, outbound ports/adapters, candidate persistence and queue, policy-bound identity, TBD AI provider, and proposed realtime/async flows are represented.
- Semantic/status review follows SRS v3.1 B8 and repository architecture/security rules. Android/React Native/TypeScript and FastAPI/Python are confirmed; PostgreSQL, Redis/RQ, and S3-compatible object storage are candidates; WebSocket and the async processing flow are proposed; AI provider/payload, web frameworks, and deployment topology remain TBD. Firebase Authentication is limited to adult identity by repository policy; the adapter remains incomplete/TBD.
- Mermaid counterpart: `src/diagrams/system-architecture-v2.mmd`. Concrete symbol, status, arrow, boundary, and layout rules: `ARCHITECTURE_DRAWING_RULES.md`. Both are indexed in `evidence/README.md`.
- Drive sync: updated the existing file in place. Final readback on 2026-10-22 confirmed ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, parent folder `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`, size 113,485 bytes, modified `2026-10-22T16:53:42.570Z`, and four pages including `System Architecture v2` with the mixed-status labels.
- No canonical SRS, application/runtime/schema code, or GitHub state was changed; FEAT-048 remains local and was not pushed.
- Actual diagrams.net rendering and normal-zoom visual QA remain pending because an official renderer/editor is unavailable in this execution. Structural XML checks and remote readback are complete; no rendered-image pass is claimed.

## System Architecture v2 Lucide icons — revision 14 (2026-10-23)

- AC-26: PASS for icon integration, source mapping, provenance, structural validation, and Drive sync. Applied the previously previewed Lucide v1.61.0 outline icons to selected primary roles on the existing `System Architecture v2` page. The page contains 20 locally embedded SVG image cells across 16 icon types; small B8 context cards and most adapter rows remain text-only.
- Icons use one neutral stroke and identify component roles only. Confirmed/proposed/candidate/TBD/policy status stays in text and status styling. No vendor logos, remote image URLs, or runtime icon dependencies were introduced.
- Local source SVGs, checksums, and applicable ISC/MIT notices are retained in `assets/icons/lucide-v1.61.0/`. Mermaid comments map icon names to roles; concrete placement and attribution rules are in `ARCHITECTURE_DRAWING_RULES.md`.
- The builder reports four pages; the v2 page has 107 cells including roots (81 vertices, 24 edges, 2 roots), 20 icon image cells, and zero dangling edge endpoints. Original ERD, System Architecture, and Package Diagram page fingerprints are unchanged.
- Updated the existing Drive file in place. Readback on 2026-10-23 verified file ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, parent folder `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`, 130,669 bytes, modified `2026-10-22T17:05:18.037Z`, four page names, and 20 v2 SVG image cells. Extracted readback summary: `evidence/raw/DRIVE_READBACK_SYSTEM_ARCHITECTURE_V2_ICONS_20261023.txt`.
- AC-26 rendered-image QA: PENDING. The SVG cells and XML structure were inspected from source/readback, but no diagrams.net screenshot or export was available; no rendered-visual pass is claimed. No canonical SRS/runtime change, commit, or GitHub push occurred.

## System Architecture v2 SVG serialization repair — revision 15 (2026-10-23)

- AC-27: PASS locally. The prior image styles contained `data:image/svg+xml;base64,...`; the literal semicolon split the data URI as a Draw.io style delimiter and caused broken-image placeholders. Replaced it with a percent-encoded non-base64 SVG data URI.
- Builder validation: all 20 Lucide image cells use a local `data:image/svg+xml,` URI; every decoded payload parses as an SVG root element. Existing four-page artifact remains valid, all 24 connector endpoints resolve, and fingerprints for the original three pages are unchanged.
- Same-ID Drive update and readback passed: file ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, parent `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`, 134,056 bytes, modified `2026-10-22T17:14:24.595Z`. Raw readback contains all four pages and all 20 valid SVG data URIs with zero base64/parse failures.
- AC-27 rendered-image QA: PENDING; no diagrams.net editor/renderer is available for screenshot-level confirmation. No SRS/runtime change, file identity/folder change, commit, or GitHub push occurred.

## Risks and mitigations

- Dense entity model: group entities by domain and include only key fields on the overview ERD.
- Proposed design mistaken for implementation: show status badges/legend and use dashed styling for proposals.
- If Drive access is unavailable in a later revision, retain the local source and report the sync state accurately.

## Verification plan

- Inspect generated XML/page count and source references.
- Compare all diagram claims with SRS v3.1 and this plan.
- Verify Drive placement by listing or reading metadata after upload; no upload success claim without connector readback.

## Evidence plan

- `evidence/README.md` indexes the source authority, local artifact, diagram review notes, and Drive upload status.

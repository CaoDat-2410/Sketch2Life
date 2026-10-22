# ERD notation and source review — 2026-10-21

## Artifact reviewed

- Local source: `features/FEAT-048-srs-diagram-pack/artifacts/Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio` (visual legend revision 6).
- Drive file: `Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio`, ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`.
- Final Drive readback after revision 6: 76,421 bytes, parent folder `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`, modified `2026-10-21T14:10:55.993Z`.
- Requirement source: canonical SRS v3.1, B7/B7.1/B21; source-register ID `collaborative-srs-v3-20261010`.

## Classification and findings

- This is a proposed conceptual/logical ERD, not a physical schema or SQL migration.
- It uses Chen symbols: entity rectangles, relationship diamonds, attribute ovals, and underlined key attributes. Selected attributes and omission of repeated reference fields keep the page at overview level.
- SRS B7.1 is written as a Mermaid ER diagram using Crow's Foot endpoints. The Draw.io page translates those markers to Chen-style relationship diamonds with endpoint labels `1` and `0..N`.
- Reviewed all 16 B7.1 relationship names and endpoint pairs against B7.1. Revision 5 repairs the Drive version's dangling connectors on `owns`, `checkpoints`, and `reviewed`; each relationship diamond now has two connector edges. The source and target sides align, including the 1-to-optional-many interpretation.
- Corrected `authorizes`: Class is `1`; TeacherAssignment is `0..N`.
- Added selected B21.5 links: OrganizationScope–Class, StudentProfile–ChildParticipant, SessionGroup/ChildParticipant–CanvasDocument, and optional ChildParticipant–CanvasOperation. `TeacherReview.reviewerRef → AdultAccount` is recorded as a selected reference attribute.
- CanvasDocument's shared-group and personal-participant ownership modes are conditional/exclusive. `CanvasOperation.contributorRef` is optional. `ConsentRecord.purposes` is a double oval for its multi-valued semantics.
- The proposed GroupMembership episode key is shown as dashed `membershipId*`; `participantRef` and `groupRef` are not presented as an established composite key.
- The page scope is 16 B7.1 entities plus OrganizationScope and selected B21.5 links. It does not claim to model all 34 B7 entities.
- The two `owns` edges use explicit waypoint arrays (2 points and 3 points) to route below SessionGroup and around GroupMembership; Drive raw readback confirms those route arrays.
- Revision 6 replaces the prose-only legend with shape examples for Entity, Relationship, Attribute, and Key plus `1 — ◇ — 0..N`; scope and caveats are in a separate two-line note.
- Before updating Drive, compared the newer owner-saved revision: all non-legend ERD data vertices retained their values, styles, and positions; Architecture and Package cell IDs, values, styles, and positions matched the local builders after normalizing default connector style tokens. The removed footer note stayed removed.
- Local and Drive XML structural verification passed: 3 pages (168/38/38 cells), 17 ERD entities, 21 named relationship diamonds plus one legend diamond, two endpoints per named relationship, zero dangling edges, correct `authorizes` labels, and zero accidental vertex-box overlaps. Drive readback confirms the 2-point and 3-point `owns` route arrays.
- The cardinality labels use min-max notation (`0..N`) with Chen symbols. That is a valid readable variant, but it is more precise to call this “Chen symbols with min-max cardinalities” than to imply every mark is the classic `1:N` ratio style.

## SRS caveats

- B7.1 is explicitly proposed. B7 says Enrollment's final cardinality is TBD. The separate scope note now marks this; displayed Enrollment cardinalities reproduce the current proposal and must not be treated as settled database constraints.
- `membershipId*` is a proposed episode identifier, not a confirmed SRS field. Confirm whether an episode key is needed to preserve leave/rejoin history before treating it as normative.
- B7.1 omits several references modeled in B21.5. The diagram records those selected links for traceability; update the canonical SRS only through a separately approved SRS revision.
- B21.5 `target_kind` supports review targets beyond SketchProposal. The ERD's explicit `reviewed` diamond is the B7.1 SketchProposal relationship; the note calls out the broader target scope.
- Enrollment's final cardinality remains TBD. The labels are the current B7.1 proposal and must not be treated as settled schema constraints.
- Rendered-image QA in diagrams.net was not available during this review. XML, endpoint, cardinality, and geometric bounding-box checks passed, but this is not a claim of visual-render inspection.

## References

- Canonical SRS: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, B7/B7.1/B21.
- Mermaid's official ERD documentation describes Mermaid's crow's-foot endpoints and cardinality semantics: https://mermaid.js.org/syntax/entityRelationshipDiagram.html
- Indian Institute of Management Ahmedabad, *Entity Relationship Model*, section 8, summarizes Chen's relationship diamond and endpoint cardinality labels: https://mcrhrdi.gov.in/cio2022/presentations/ERDNOTE.pdf

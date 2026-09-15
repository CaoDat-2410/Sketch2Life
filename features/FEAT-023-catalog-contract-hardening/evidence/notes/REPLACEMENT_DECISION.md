# Coverage-based replacement decision

## Decision

FAM-ANIMAL-HABITAT was replaced by FAM-ANIMAL-BUTTERFLY in the curated
expansion revision. The replacement keeps the selectable catalog at 300
profiles (100 MVP plus 200 curated expansion variants).

## Evidence

Before replacement, the family contributed ANIMAL_GENERIC and
NATURE_OBSERVATION, both already covered by other families in every age
band. Its OBJ_COSMIC_INTERCONNECTION objective was also covered by the sky
families in every age band. No concept-age or objective-age pair became empty
when the family was removed in the coverage analysis.

The replacement adds the previously absent ANIMAL_BUTTERFLY concept with
four age variants and preserves the existing activity ID slots ACT-0113 to
ACT-0116, so downstream references remain versioned and deterministic.

## Revision

The loader materializes the companion variant contract manifest as
catalog-2026-09-expansion-2; the original expansion-1 source files remain
unchanged in their role as authored family data.

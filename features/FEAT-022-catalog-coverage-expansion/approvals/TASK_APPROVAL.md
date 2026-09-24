# Task approval

Status: APPROVED

Approved by user on 2026-09-14.

Approval scope: implement the catalog expansion plan, including curated catalog schema/governance, coverage and diversity validation, approved-only runtime loading, seeded selection evaluation, and evidence. Do not implement PixiJS runtime, video generation, UI integration, caregiver persistence, or runtime AI activity creation.

This feature plan is ready for review. No implementation is authorized until the user explicitly approves this plan, in accordance with the repository harness.

Requested scope:

- expand the curated activity catalog toward 200-250 selectable variants;
- add coverage, quality, provenance, and diversity validation;
- improve recommendation diversity and no-match/unavailable observability;
- validate with a 100-300 scene evaluation corpus and a Lightning AI smoke run;
- do not implement PixiJS runtime, video generation, UI integration, or production caregiver persistence.

## Owner approval — activity preparation and printable-asset classification — 2026-09-23

- Approver: Project owner direct instruction in the current conversation: “duyệt”.
- Approved artifact: `plan/ACTIVITY_PREPARATION_ASSET_CLASSIFICATION_PLAN.md`.
- Approved scope: classify every selectable activity as `NO_PRINTABLE_ASSET`,
  `PRINT_RECOMMENDED` or `PRINT_REQUIRED`; add the versioned preparation profile contract,
  catalog manifest, validation/reporting and backend metadata projection.
- PDF/A4 is the future canonical print format; editable SVG/PNG sources may be retained.
- Explicit exclusions: creating or reviewing printable files, parent/guide UI, download/print
  endpoints, storage/auth/persistence, AI-generated activities, PixiJS, video and Lightning changes.

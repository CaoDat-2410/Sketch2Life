# FEAT-063 draft reconciliation — 2026-10-26

> Historical checkpoint only. It predates owner answers Q80–Q104 and is superseded by the current SRS and DATA_TABLE_REGISTER review drafts. Its 87-active/17-legacy count and Mermaid renders are not current and must not be reused as final.

## Scope

This records an earlier documentation-only draft checkpoint. Answers Q21–Q79 have since arrived; follow-up questions Q80–Q86 are open. It does not approve implementation, migrations, Modal calls, live provider calls, or database access.

## Reconciliation results

- Source table inventory: 86 production mappings, matching the declared source list in SRS §11.2.
- New target table definitions: 18 (`parent` 2, `profile_context` 1, `lesson` 5, `story` 10).
- Draft target count: 69 retained/refactored + 18 new = 87 active; 17 legacy archive tables; 104 physical while archive stays in PostgreSQL.
- Five test-only fixture tables are excluded from production counts.
- Earlier draft Mermaid source blocks: 12; they rendered with `@mermaid-js/mermaid-cli` 12.0.0 using `--size 1200 --scale 1.5` before the latest instruction to defer diagram work. These artifacts are unapproved, do not match the current requirement baseline, and must not be used as final diagrams.
- Earlier draft diagram sources and PNG previews: `evidence/mermaid_draft_20261026/`.
- Plan revision 3 hash matches the approval record: `4386E788B916F4CE75ACD119309671F3A7C85B825E4222AF9C0C642AAFCE2D0F`.

## Historical draft source hashes

These hashes identify an earlier draft checkpoint, not the current Markdown after Q21–Q70 answers and status updates.

| File | SHA-256 |
|---|---|
| `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | `A455317B7D85B8510FE302ECDA4D3D7015B63CF6F99E905BD294A191A89A6E63` |
| `artifacts/DATA_TABLE_REGISTER.md` | `BF2722A653F90CA1E87819DE93B604F128D01B2742F67DFEF4CC722472A43377` |
| `../../../docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md` | `2914A79631F2D8C2916D0306C33082C574CC55AF2F7541FC938E04887D9662F9` |

## Open owner answers

Q21–Q79 answers have been received. Follow-up questions Q80–Q86 cover video-per-day scope, class limits, profile intake, pre-video review, legacy ERD/data retention, Parent custom activity, and deletion lifecycle. The current SRS/register still contain older assumptions and an unreconciled target table count. Do not generate or update diagrams or a PDF until the owner decisions are incorporated and both Markdown documents agree.

## Limits

- Counts are source-declaration/document counts. No deployed database was inspected.
- No product tests/builds were run; no database, provider, or Modal runtime was contacted.
- No real child data was used.
- This is draft Mermaid rendering evidence, not final PDF page-layout QA.

## Superseding review checkpoint — 2026-10-27

- Owner requirements are recorded through Q104.
- Current proposal: 51 retained/refactored + 37 new = 88 active; +35 preserved read-only legacy = 123 physical after additive migrations. Five test fixture tables are excluded; 86 is a source declaration count, not a live database count.
- The owner asked to approve the Markdown SRS and data-table register before final diagrams or PDF. This checkpoint does not generate or approve either.
- Current review sources: ../artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md and ../artifacts/DATA_TABLE_REGISTER.md.

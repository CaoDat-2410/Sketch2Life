# Registration form v1.5 original-style correction — 2026-10-06

## Owner direction and source

- After reviewing v1.4, the owner directed that the original form presentation be kept and approval-waiting wording be removed. This correction is recorded in plan revision 6 and `approvals/TASK_APPROVAL.md`.
- Controlling plan SHA-256: `47D943EE8499145F67F314C74F75B79FAA9645DDD2E2297E52B590FD6EAE56D2`.
- Supplied source v1.1: `owner-local attachment Phieu_FA26SE225_updated.docx`; SHA-256 `21739477916A1FC2E03CC0E22B6F8DD383A03F6831F2EA4EEB1593747CABB548`.
- Current form v1.5 derives directly from v1.1: `artifacts/Phieu_FA26SE225_v1.5.docx`; SHA-256 `47F23FD4486A4605208BB44A7B3696081F973DF74D4F1B8D56F7D35C34DF6956`.
- Earlier v1.2, v1.3 and v1.4 artifacts remain preserved; v1.4 is superseded as the user-facing presentation.

## Preservation and content review

- The v1.5 form retains the source's 159 paragraphs, three tables, supervisor/student/signature sections, and eight-page layout. No new package table or form section was added; the package details use the existing Other Comments slot.
- The derivation checked that all original table cell contents remain unchanged and that `word/document.xml` is the only changed DOCX package part. All other package-part contents and relationships are preserved from v1.1.
- The form now states the supported age as under 9 years / 0–107 completed months, preserves 9–12 catalog rows outside the current product scope, records the three product bands in the research scope, and makes age context adult/profile-sourced for story generation rather than inferred from media.
- Activity discovery follows the complete confirmed-topic/exact-age set, with catalog, safety/policy and required-supervision constraints; adult-confirmed interests may order results. Readiness, prior work, prerequisite sequence and material availability do not exclude otherwise eligible activities.
- The existing Other Comments paragraph lists Free (10 monthly credits), Gia đình (99,000 VND/month, 30 pooled credits), Lớp học (499,000 VND/class/month, 120 pooled credits), the 10/30/60-credit top-ups, one-credit experience lifecycle, manual renewal, and backend payment confirmation.
- Internal review/draft/provisional/waiting-for-owner-approval and implementation-state commentary was removed. Product adult approvals and child-research consent safeguards remain as actual requirements.

## Render review

- Canonical `render_docx.py` was attempted and could not find `soffice.exe` on PATH.
- Microsoft Word exported `evidence/rendered/v1.5-source-retained/word-6/Phieu_FA26SE225_v1.5.pdf`, SHA-256 `45164A82C730C352A56289AEC142F9B18A3D85947C8FC1C2DBBC6D77CEF93618`.
- The bundled PDF renderer produced eight page images in `evidence/rendered/v1.5-source-retained/word-6/pages/`. Every page was inspected at original resolution. Page count, tables, final comment, signature placement, and text flow were intact.
- No application automated tests, provider calls, or payment transactions were run as part of this form correction.

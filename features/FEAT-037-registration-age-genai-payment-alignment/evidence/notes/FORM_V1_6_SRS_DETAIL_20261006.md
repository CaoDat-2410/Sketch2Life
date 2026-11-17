# Registration form v1.6 — detailed SRS alignment (2026-10-06)

## Owner request and approval

- Direct user request: “chi tiết hơn, dựa trên srs”.
- Approved plan: revision 7, SHA-256 `2F9A1F2E08101E63EE4B356BCD42B3955FD8FB76D9944D3E0AD85435ED569D49`.
- The original form presentation correction from plan revision 6 remains in force.

## Sources and lineage

- Supplied form v1.1: `owner-local attachment Phieu_FA26SE225_updated.docx`; SHA-256 `21739477916A1FC2E03CC0E22B6F8DD383A03F6831F2EA4EEB1593747CABB548`.
- Previous clean derivative v1.5: `artifacts/Phieu_FA26SE225_v1.5.docx`; SHA-256 `47F23FD4486A4605208BB44A7B3696081F973DF74D4F1B8D56F7D35C34DF6956`.
- SRS baseline: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, version 2.0; principal sources are B5, B10–B12, B21 and B30–B35.
- Current output v1.6: `artifacts/Phieu_FA26SE225_v1.6.docx`; SHA-256 `A8491249AA6A631AE638FF0998FCDF6E063E50EADA1BDD750F17AF55B57E78CE`.
- Derivation helper: `src/derive_form_v1_6.py`.

## Changes and preservation

The v1.6 edit expands existing fields in the supplied form. It describes the adult-supervised profile/capture and consent flow; separate Gate A, Gate B and exact-script approval; complete B33 topic/exact-age discovery and interest ordering; source-grounded age-aware story planning; immutable script revisions, TTS, illustrated scenes/video, READY validation and recovery; privacy/provenance; Parent Web plan/payment/credit functions; and study questions, measures and consent controls.

Age remains under 9 years (0–107 completed months; bands 0–35, 36–71 and 72–107). Age is adult/profile-sourced. Readiness, prior work, sequence and material availability do not filter otherwise eligible discovery results. Package terms and the one-credit lifecycle match SRS B35. Internal review, draft, waiting-for-approval, SRS-section-reference and unresolved payment-provider notes are absent from the form; actual product adult gates and research-consent safeguards remain.

The document retains 159 paragraphs, all three original tables and their cell content, original section order, and supervisor/student/signature blocks. No new section or package table was added. Relative to v1.5, `word/document.xml` is the only changed DOCX package part. Microsoft Word renders the detailed content as 11 pages.

## Rendering and visual review

- Canonical `render_docx.py` was attempted first and could not run because LibreOffice `soffice.exe` is unavailable on PATH.
- Microsoft Word exported `evidence/rendered/v1.6-source-retained/word/Phieu_FA26SE225_v1.6.pdf`; SHA-256 `069427B5A3F9BAB269896561CA96517A0BB004028F1A0D956576A204E4262809`.
- The bundled PDF renderer produced 11 page images under `evidence/rendered/v1.6-source-retained/word/pages/`. All 11 pages were inspected at original resolution after the final edit. Text is within the page bounds; the original registration tables and final signature block remain intact.
- The derivation helper verified the source hash, paragraph/table counts, unchanged table contents, required age/discovery/package/payment/research content, prohibited internal-note phrases, and the changed package-part boundary.
- No application tests, payment transactions, or provider calls were run for this document-only revision.

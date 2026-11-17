# Registration form v1.7 alignment evidence

- Date: 2026-10-12 (Asia/Saigon)
- Task: FEAT-037, registration form update
- Owner authorization: direct request “update lại phiếu FA26” in the task conversation
- Approved plan: revision 8, `plan/PLAN_FORM_V1_7_20261012.md`, SHA-256 `A91DDF14D32141D891CB52B5321754D298A5BB55B546587A441125F1DC5521E3`
- Product authority: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, v3.1; owner answers in FEAT-039 approval and source-register row `registration-phieu-fa26se225`

## Source and output lineage

- Owner-supplied form v1.1: `owner-local attachment Phieu_FA26SE225_updated.docx`; SHA-256 `21739477916A1FC2E03CC0E22B6F8DD383A03F6831F2EA4EEB1593747CABB548`, recorded by FEAT-037.
- Existing clean derivative used for this update: `artifacts/Phieu_FA26SE225_v1.5.docx`; SHA-256 `47F23FD4486A4605208BB44A7B3696081F973DF74D4F1B8D56F7D35C34DF6956`.
- v1.6 historical note: `evidence/notes/FORM_V1_6_SRS_DETAIL_20261006.md` reports an output hash, but `artifacts/Phieu_FA26SE225_v1.6.docx` is absent from the current repository. It was not used as an input.
- Current derived form: `artifacts/Phieu_FA26SE225_v1.7.docx`; SHA-256 `003AA55B24BB612C8E8FA27CE241D96C3CAA8FCD09925A3A2E1C8336E41F75E3`.
- Derivation helper: `src/derive_form_v1_7.py`. It checks the v1.5 source hash and paragraph prefixes, preserves the original form's run formatting, verifies required current-scope statements, rejects selected superseded claims, checks all tables, and confirms that only `word/document.xml` differs in the DOCX package.

## Changes

The form now names the collaborative creative-learning product and describes the confirmed 3–12 age scope, managed child profiles with QR/session-code admission, school/class/group sessions, individual and collaborative Android drawing, Teacher control and per-suggestion review, child hide/decline choices, reviewed knowledge/video, off-screen activity, reflection, descriptive assessment, consent, retention, and recovery.

It records the one-school, one-class/up-to-40-child pilot target; school collection of legal-representative consent with authorized Teacher/Super Admin evidence and purpose records; and the 90-day-after-session-end default for session and artwork data only. It removes the superseded under-9/Parent/billing/package/credit/old-video-duration/fixed-screen-time requirements. It does not select AI models, providers, or unresolved implementation policies.

The v1.7 DOCX retains 159 body paragraphs, all three original tables and their content, section order, class/duration fields, and supervisor/student/signature areas. Source v1.1, v1.5, and earlier derivatives were not modified. The current output contains no Parent portal, package/payment/credit, under-9, fixed screen-time, or 40–60-second video claims.

## Render and visual review

- The documents skill `render_docx.py` was attempted. The renderer and its verbose run both stopped at `FileNotFoundError: LibreOffice soffice.exe was not found on PATH`.
- Microsoft Word opened the v1.7 DOCX read-only and exported `evidence/rendered/v1.7/Phieu_FA26SE225_v1.7.pdf`; PDF SHA-256 `DF356FC74C12B3BDFAB4D2635491C3A49DEFDEA9B9DF7BB23B37347012B893F1`.
- Bundled `pypdfium2` rendered all 8 pages to `evidence/rendered/v1.7/pages/page-01.png` through `page-08.png` at scale 2. Every page image was inspected at original resolution after the final edit. Text is within the page bounds; the title, section flow, lists, original tables, and signature block are intact, with no clipping or overlap.

## Scope and verification boundary

This was a document-only task. No product code, API, provider, billing, cloud resource, or real child data changed. No application tests were run. Structural, source-lineage, content, DOCX-package, page-count, and visual checks are recorded above.

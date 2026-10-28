# Backend Lesson library scope and upload review — EV-063-21

- Date: 2026-10-28 (Asia/Saigon).
- Feature: FEAT-063.
- Purpose: record the owner's scope choices and repository/SRS implications for Plan Rev28.
- Owner choices: include School Manager approval/Public publication and Parent read/share in the first backend plan; include Teacher lesson-plan upload.

## Read-only findings

- FEAT-063 SRS v2.3-draft already describes Manager approval for Teacher Public lessons, Public/School/Selected visibility, Parent access to Public/shared lessons, revocable grants and PDF/PPTX/DOCX upload limits (25 MB and 100 pages/slides; no encrypted files or scanned-page OCR).
- Data Table Register `lesson.source_documents` and `lesson.document_revisions` are keyed to `lesson.occurrences`. Reusable library lessons have separate `lesson.library_items`, `lesson.library_versions` and `lesson.version_activities`. A reusable library upload should not point at an occurrence-owned document record.
- The register's Core upload-session/parts and Parent-group/access-grant entries are architecture targets. Repository searches found no general reusable-library upload route or mounted Parent lesson-read API in the backend composition.
- Plan Rev28 therefore proposes library-owned source-document/extraction-revision records and an additive Data Table Register update before migrations. It does not assert those tables or APIs already exist.

## Evidence boundary

This is repository/SRS review evidence and a record of the owner's direct answers, not implementation evidence. No database was inspected; no files were uploaded; no parsing, tests/builds, AI/model/provider/Modal calls, real accounts, credentials or child data were used.

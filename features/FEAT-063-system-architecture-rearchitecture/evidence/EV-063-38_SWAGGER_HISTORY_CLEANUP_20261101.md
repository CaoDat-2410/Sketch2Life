# EV-063-38 — Current-only Swagger cleanup

- Approved plan: Plan Rev48, SHA-256 DA706B55D7B1310C9CB87288A1A606604FDA3E9D931BC7FFD386E89E482668E3.
- Owner request: remove the old Swagger Markdown files from the pending commit and keep the current work.
- Removed 12 superseded standalone documents: Swagger plans Rev38–42 and Rev44, plus evidence EV-063-30–34 and EV-063-36. Current SRS v2.2 snapshot Rev45 and evidence EV-063-37 remain.
- Current feature/global indexes no longer link to the removed plan/evidence documents. The approval ledger keeps a concise summary of prior approved scope; the current operation and acceptance criteria are in Plans Rev45–48.
- Backend route/auth/runtime behavior was not changed by this cleanup. The internal route contract metadata remains because the current FE projection and exporter depend on it.

## Verification

- OpenAPI exporter passed: 17 FE paths, 24 SRS v2.2 operations; 124 full runtime operations preserved and 11 unmounted candidates excluded.
- Targeted Ruff passed for the Swagger implementation, exporter, and related contract files. This run found and corrected formatting-only findings in the upload middleware and OpenAPI amendment module; API logic and payloads are unchanged.
- git diff --check passed.
- Repository security validator passed: 5,802 publishable files scanned; no machine-specific absolute paths detected.
- Backend test suites were not run.

## Commit and publication

- The single local consolidated dev commit retains parent 111ae547007801d7d171dd12f3ac6f1085d22199 and replaces the two Swagger commits named in Plan Rev46.
- The remote update uses force-with-lease against expected origin/dev tip 6d77d2ad41370f118386d9861fed4cd031ddea67; publication remains pending GitHub authentication.

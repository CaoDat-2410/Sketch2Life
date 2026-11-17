# EV-063-34 — Swagger review and local commit

## Scope and authority

- Approved plan: `plan/PLAN_REV42_SWAGGER_REVIEW_AND_COMMIT_20261030.md`; SHA-256 `E8A809729BDE4B83D0A6FD0AC21336C8F3721F55B7BDFA7431F1125922D026E8`.
- Approval: the owner directly requested `coi và commit cho tui` in the current chat. Plan Rev42 supersedes prior commit exclusions only for this exact local commit; push remains excluded.
- Source API catalog SHA-256: `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.

## Review findings and resolution

- Reviewed the pending Swagger/OpenAPI code, all 124 mounted operation records, the 11 unmounted candidates, role/domain tags, examples, synthetic fixture, snapshot exporter, generator, quickstart, approval hashes and feature records.
- Contract and presentation match the current local Swagger surface: 124 operations, 111 paths, 18 tags and 11 unmounted candidates. The served `/openapi.json` equals the regenerated feature-local snapshot (SHA-256 `C1F2B453E5D893AF5328C9091A51B183CB2D67FED2587411C0D45598F47A9466`).
- Review found that the new typed 413 response echoed an arbitrary `X-Request-ID` into a response header. The middleware now applies the API's safe identifier format, restricts contract-shaped handling to exact session media upload paths, and caps the reported session version consistently with the existing validation response. An invalid-input regression check was added.
- The synthetic PNG is an abstract sun-and-hills graphic, 128 × 96 RGBA, 504 bytes; it contains no person, child or personal data.

## Verification

- Focused Swagger and upload-size suite: **5 passed**.
- Targeted Ruff check: **passed** (`E501` ignored, consistent with the existing long contract metadata module).
- Python compilation for changed runtime/test modules: **passed**.
- Local OpenAPI exporter: **passed**, 124 mounted operations, 111 paths and 11 unmounted candidates.
- Served `/openapi.json` matches the regenerated snapshot: **passed**; 18 tags. The local `/docs` surface remains available.
- Plan Rev38–Rev42 SHA-256 values match the approval register: **passed**.
- `git diff --check`: **passed** (Git reports only the existing line-ending normalization warning for the approval register).
- `python tools/validate_repository_security.py`: **REPOSITORY_SECURITY_VALID**; 5,806 publishable files scanned, no absolute machine paths or credential material found.

## Publication boundary

The reviewed changes are authorized for one local commit on `dev`. No push, deployment, database/provider operation, Firebase credential or route authorization bypass is included. Protected BE1/Lesson Library interactive requests still need a separately configured valid test identity and persistence services.

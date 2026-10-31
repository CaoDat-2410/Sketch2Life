# Plan Rev48 — Remove superseded Swagger revision documents

## Status

- Lifecycle: APPROVED for the exact documentation cleanup and amendment of the not-yet-pushed consolidated commit.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Branch: `dev`.
- Date: 2026-11-01, Asia/Saigon.

## Goal and owner instruction

Remove obsolete Swagger revision Markdown files from the consolidated `dev` commit so it carries the current SRS v2.2 Swagger work, not prior revision writeups. The owner showed the old revision files in the pending commit view and requested: “bỏ đi mấy cái md này nè và chỉ lấy cái mới thôi”.

## Exact removal scope

Delete the superseded standalone Swagger documents:

- `plan/PLAN_REV38_SWAGGER_OPENAPI_CONTRACT_20261030.md`
- `plan/PLAN_REV39_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md`
- `plan/PLAN_REV40_LOCAL_SWAGGER_QA_KIT_20261030.md`
- `plan/PLAN_REV41_SWAGGER_INFO_PRESENTATION_20261030.md`
- `plan/PLAN_REV42_SWAGGER_REVIEW_AND_COMMIT_20261030.md`
- `plan/PLAN_REV44_FE_SWAGGER_CONTRACT_AND_GROUPING_20261031.md`
- `evidence/EV-063-30_SWAGGER_OPENAPI_FEAT063_REV37_20261030.md`
- `evidence/EV-063-31_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md`
- `evidence/EV-063-32_LOCAL_SWAGGER_QA_KIT_20261030.md`
- `evidence/EV-063-33_SWAGGER_INFO_PRESENTATION_20261030.md`
- `evidence/EV-063-34_SWAGGER_REVIEW_AND_COMMIT_20261030.md`
- `evidence/EV-063-36_FE_SWAGGER_CONTRACTS_AND_GROUPING_20261031.md`

Keep the current SRS v2.2 OpenAPI snapshot and Plan Rev45, plus the current approval/history-cleanup plans Rev46–48 and evidence for the current Swagger/history operation. In required feature registers, remove prior standalone Swagger revision entries while retaining current Rev45–48 status and approval records. Do not remove unrelated FEAT-063 planning records or product/API contract source code.

## Acceptance criteria

- AC1: The superseded standalone Swagger Plan Rev38–44 and Evidence EV-063-30–36 files listed above are absent from the final `dev` tree.
- AC2: The current `OPENAPI_FEAT063_REV45_20261101.json`, current plans/approvals/evidence, source contract metadata, and active FEAT-063 register files remain.
- AC3: Approval records and current source/status/context do not point to deleted standalone Swagger plan/evidence files.
- AC4: Current OpenAPI exporter, targeted Ruff, `git diff --check`, and required repository security validation pass. Backend tests are not run.
- AC5: Amend the one consolidated commit, keep its parent `111ae547007801d7d171dd12f3ac6f1085d22199`, and update `origin/dev` only by force-with-lease against `6d77d2ad41370f118386d9861fed4cd031ddea67`.

## Explicit exclusions

- No deletion of non-Swagger FEAT-063 plans/evidence or unrelated context records.
- No route/auth/payload/runtime changes; backend test suites are not run.
- No modification of unrelated branches or commits.

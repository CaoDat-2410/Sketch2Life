# Plan Rev47 — Remove obsolete Swagger artifacts before push

## Status

- Lifecycle: APPROVED for the exact pre-push cleanup and commit amendment below.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Branch: `dev`.
- Date: 2026-11-01, Asia/Saigon.

## Goal and owner follow-up

Before publishing the consolidated Swagger commit, remove files that are not used by the current SRS v2.2 FE Swagger. The owner follow-up was: “nếu vậy thì không xóa bớt mấy cái không xài tới để đỡ có nhiều file rác commit lên ah”.

## Exact cleanup scope

Remove these obsolete artifacts from the consolidated commit and current tree:

- `artifacts/OPENAPI_FEAT063_REV37_20261030.json` (superseded snapshot)
- `artifacts/OPENAPI_FEAT063_REV44_20261031.json` (superseded snapshot)
- `artifacts/LOCAL_SWAGGER_QA_QUICKSTART_20261030.md` (local/demo routes are not in FE Swagger)
- `artifacts/qa-fixtures/synthetic-demo.png` (local/demo fixture)

Remove only the process-local Demo request examples from the internal generated OpenAPI schema, its exporter assertions, and its existing contract-test expectations. Keep runtime Demo routes untouched; keep the current Rev45 FE snapshot, contract metadata source, authorization/response metadata helpers, and historical approval/evidence records. The existing consolidated commit `cccc9fb9d0f97868f8c45c2e2ad0916129d1ce5e` is amended before any remote push.

## Acceptance criteria

- AC1: The four obsolete files above are absent from the final `dev` tree; no published FE schema references them.
- AC2: Runtime routes and non-documentation behavior remain unchanged; full mounted operation metadata and the 24-operation FE projection still export successfully.
- AC3: Targeted Ruff, OpenAPI exporter, `git diff --check`, and required repository security validation pass. Backend tests are not run.
- AC4: The single amended consolidated commit remains parented to `111ae547007801d7d171dd12f3ac6f1085d22199` and replaces only the two prior Swagger commits.
- AC5: Update `origin/dev` with force-with-lease only if the expected old tip is still `6d77d2ad41370f118386d9861fed4cd031ddea67`.

## Explicit exclusions

- No deletion of historical plan/evidence/approval records.
- No backend route, auth, DTO, payload, persistence, or behavior change.
- No change to unrelated branches or commits; no backend test execution.

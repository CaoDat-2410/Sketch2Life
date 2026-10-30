# Plan Rev41 — Swagger overview presentation

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED under the project owner's direct `làm cho đẹp` request in the current chat on 2026-10-30, applied to the overview shown in the supplied Swagger screenshot and the exact scope below.
- Source reference: owner-provided screenshot of the local Swagger `info.description` block in the current chat.
- Approval record: `approvals/TASK_APPROVAL.md` (this plan's SHA-256 is recorded there).

## Goal

Make the Swagger overview easier to scan by replacing its long paragraph with a compact, clear summary of coverage, authorization, and unmounted candidates.

## Scope

1. Rewrite only FastAPI's top-level `info.description` as concise Markdown with a one-line introduction and clearly labeled coverage, Try it out/authentication, and unmounted-route notes.
2. Preserve the API title/version, existing operation/tag presentation, all routes, schemas, auth behavior, request examples, and counts.
3. Regenerate the feature-local OpenAPI snapshot and restart the already-running loopback Swagger API so the screenshot target shows the updated copy.
4. Record the exact overview text, snapshot hash and HTTP status results in FEAT-063 context, source, status and evidence records.

## Acceptance criteria

- AC1: The Swagger overview is concise and scannable, with the local coverage counts, bearer-token note, tag/authorization distinction, and 11 unmounted candidates easy to identify.
- AC2: No route, authentication, schema, request/response behavior or tag grouping changes.
- AC3: OpenAPI remains at 124 operations, 111 paths, 18 tags and 11 unmounted candidates for the enabled local profile; the snapshot matches the served OpenAPI.
- AC4: The restarted loopback `/docs` and `/openapi.json` endpoints return HTTP 200.

## Verification

- Regenerate the OpenAPI snapshot using the existing local-profile exporter and check its counts.
- Request `/docs` and `/openapi.json` from the local server and compare the served OpenAPI object with the regenerated snapshot.

## Explicitly excluded

Custom Swagger CSS/theme, product/API/auth changes, candidate route mounting, test credentials or data, database/provider operations, commit, push, and deployment.

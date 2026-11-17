# Plan Rev40 — local Swagger QA kit and upload error parity

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED under the project owner's direct `duyệt` in the current chat on 2026-10-30, applied to the exact scope and acceptance criteria below.
- Authority: follow the recommendation to make the local Swagger page practical for a first synthetic workflow test, correct the known 413 contract mismatch, and report any blocker before broader QA.
- Source contract: owner-supplied `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md`; SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.
- Approval record: `approvals/TASK_APPROVAL.md` (this plan's SHA-256 is recorded there).

## Goal

Let the owner run a bounded, synthetic session-and-image workflow from local Swagger and ensure transport-level oversized image/audio errors match the documented `MobileWorkflowResultV1` contract.

## Scope

1. Change only the `/v1/sessions/{session_id}/media/image` and `/media/audio` body-limit response to a valid `MobileWorkflowResultV1` failure with stable `UPLOAD_TOO_LARGE` code and safe message. Preserve the existing generic transport response for other middleware-managed upload routes.
2. Replace the Rev38 OpenAPI `oneOf` mismatch annotation for those two 413 responses with the single declared `MobileWorkflowResultV1` schema. Keep Rev37 operation, request, auth, and response parity checks intact.
3. Add accurate, copyable Swagger examples for synthetic session creation and multipart image upload. Add one deterministic, tiny synthetic PNG under this feature's artifacts for Swagger `Try it out`.
4. Add a short local QA quickstart with the exact request order, headers, expected version handoff, loopback URL, fixture path, and teardown/restart behavior. Make clear that local demo sessions are process-local and contain synthetic non-child material.
5. Document the current protected-route test boundary: existing integration tests use disposable PostgreSQL and synthetic principals through test-only dependency overrides; Swagger's application routes require a real Firebase ID token. Do not add a fake-token route or persist a QA account/token. Report the absence of a configured Firebase Auth Emulator if that prevents authenticated Swagger testing.
6. Run the approved focused 413 regression, Swagger parity/export checks, and synthetic create/upload workflow; regenerate the OpenAPI snapshot and update FEAT-063 context, source, decision, status, and evidence records.

## Acceptance criteria

- AC1: An over-limit image or audio request returns HTTP 413 whose JSON validates as `MobileWorkflowResultV1` and whose failure code is `UPLOAD_TOO_LARGE`.
- AC2: The published 413 response schema for both operations is exactly `MobileWorkflowResultV1`; the runtime-mismatch extension is absent.
- AC3: Swagger shows usable examples for session creation and image upload, and the supplied synthetic PNG completes the documented local demo workflow without external providers or persistent database writes.
- AC4: OpenAPI contract parity remains at 124 mounted operations across 111 paths, with 11 candidate operations unmounted and 18 documented tags.
- AC5: Focused checks and the snapshot exporter pass; `/docs` and `/openapi.json` return HTTP 200 from the loopback server after restart.
- AC6: Evidence records exact results and clearly states that Firebase-protected routes remain unavailable for interactive QA without a valid Firebase ID token/Auth Emulator setup.

## Verification

- Run focused tests for the image hard body cap, mobile-workflow result validation, and OpenAPI catalog parity.
- Run `scripts/export_openapi_rev37.py` with local storage examples enabled and verify the generated snapshot and operation counts.
- Execute session creation and synthetic image upload through the app's in-memory TestClient; confirm no external AI/provider request or database write occurs.
- Restart only the known local loopback Swagger process and request `/docs` and `/openapi.json`.

## Explicitly excluded

Adding or mounting APIs, changing route authorization, adding a development/test-token bypass, creating Firebase users or credentials, inspecting or writing the persistent application database, running against real child data, calling AI/Firebase/AWS or remote providers, deployment, commit, and push.

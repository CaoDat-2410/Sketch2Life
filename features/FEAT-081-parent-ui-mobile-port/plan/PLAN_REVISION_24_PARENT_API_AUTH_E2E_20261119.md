# FEAT-081 — Plan Revision 24: Parent API, auth configuration, and full-flow verification

- **Status:** APPROVED and launched by the owner's direct instruction on 2026-11-19: inspect/fix Parent APIs and run the Parent workflows through the real UI; product quota must not block the local synthetic test.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 canonical working SRS v2.7-draft, Rev71, unsigned. Read `docs/context/SRS_AUTHORITY.md`, the canonical SRS, and FEAT-063 `SOURCE_REGISTER.md`. Use FEAT-081 plans only for implementation history and currently approved execution limits.

## 1. Goal

Explain and fix the registration error shown in the owner's screenshot, compare the Parent app's API calls with the locally served OpenAPI/SRS, and run the real Parent Expo Android workflow against the local backend and Modal where the corresponding route/worker exists.

Target workflow:

`Parent signup/sign-in → create/select synthetic profile → choose topic or shared lesson → optional SVG drawing guide → attach synthetic drawing → drawing understanding → adult subject confirmation → catalog-first activity selection and persistence → story generation/review/confirmation → silent LTX-2.5 video request/result if the Parent video API and worker are executable → post-video lesson activities`.

## 2. Screenshot investigation and configuration rules

- Inspect app error mapping, Expo public config, backend registration response, Firebase Auth/Admin initialization, and sanitized logs to identify the actual failure boundary.
- The local `.env` remains the single source file in the CAPSTONE project. Expo config may locate it by walking upward to an ancestor containing `pnpm-workspace.yaml`; it must not copy values into another `.env`, print values, read arbitrary parent `.env` files, or bundle Firebase Admin credentials. Only the existing public mobile fields may enter Expo's public config.
- Preserve Firebase Authentication as the only Firebase product. Do not read, print, or store passwords, ID/refresh tokens, service-account JSON, API keys, or full environment values in evidence.
- Signup verification uses a newly generated synthetic test identity if needed. Never retry signup for an email whose prior request outcome is uncertain; use the returned server result/log to determine whether it created an identity first.

## 3. API review and implementation scope

1. Inventory Parent/Auth routes from the running backend's `/openapi.json`; compare operation, method, request/response contract, authorization, SRS workflow step, UI call site, and runtime status.
2. Exercise safe read/health/contract routes before mutation. For writes, use only the test-owned synthetic Parent account, profile, run, and generated artwork. Do not use fixtures, preview harness, direct database writes, or real child data.
3. Fix only defects in the approved Parent flow and supporting auth/config/API contract. Quota and payment endpoints are explicitly outside this test; a local video-quota bypass may only be server-side, synthetic-only, default OFF, and non-production as already required by Rev23.
4. If an API is absent or a worker is a fail-closed scaffold, record that as unavailable and implement only within Rev23's existing Parent/video scope. Do not claim an endpoint works from source presence alone.

## 4. Bounded live execution

- One fresh Android Parent E2E path using synthetic data only.
- After offline fixes and readiness checks, at most one live request each for drawing understanding, activity suggestions, story generation, and silent video. Do not retry, double-submit, warm a model, replay a terminal job, or retry storyboard scenes. Existing failed Drawing VLM attempts are not replayed; this amendment permits one new attempt in the fresh path after verifying the worker fix.
- Stop immediately at a failed contract/business/safety gate; do not bypass required adult confirmation or synthesize a successful result.
- Quota/payment are not evaluated. Any no-quota video path must remain local-only, synthetic-only, server-guarded, auditable, and disabled by default.
- If LTX-2.5 is still unavailable, stop before provider substitution and report the exact blocker. No Wan/legacy video route, fixture, mocked, or cached sample output.

## 5. Evidence and cleanup

- Save the API crosswalk, sanitized request/log identifiers, elapsed time, response status/error code, and screenshots of completed workflow screens under `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.
- Do not capture credentials or unrelated UI screens. Include an explicit pass/fail/unavailable status for every Parent/Auth OpenAPI route reviewed; distinguish routes exercised through UI from contract-only or out-of-scope routes.
- Stop only task-owned Expo/Metro, local Docker services, and Modal apps started/used for this test after evidence is written. Do not stop unrelated user services or the deployed video app unless this run started/used it.

## 6. Acceptance criteria

- The screenshot error is tied to a verified failure boundary and corrected in code/config when repository-controlled.
- Expo running from the feature worktree receives the intended public Firebase and local API settings from the single CAPSTONE `.env`; server-only Firebase Admin credentials never enter the mobile bundle.
- Served OpenAPI routes are crosswalked against Parent UI/SRS, with broken/missing/unavailable API flows explicitly recorded.
- Every stage reported PASS has been reached through the real Android UI and persisted/returned by the real backend/AI worker; no fixture or backend-only substitution.
- All failure results, exhausted one-shot calls, and unimplemented stages remain visible as failures, not false success.

## 7. Authorized paths and boundaries

- `apps/ui-mobile/app.config.js`, `apps/ui-mobile/src/parent/**`, and focused `apps/ui-mobile/tests/**`.
- Parent-specific backend code/contracts/routes/persistence/OpenAPI and focused tests within the existing Rev23 authorization; `deployment/modal/srs_v23/**` only for the approved Parent workloads/video path.
- This plan, `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`, feature `status/STATUS.md`, and new evidence directory specified above.
- Additive migrations only when a demonstrated persistence gap requires one, with the matching FEAT-063 data register updated and applied only to disposable local dev data.
- No quota/payment implementation or tests, Teacher flow, production changes, real child data, secret/env-file edits, direct DB mutation, fixtures, commit, push, branch/history operations, or unrelated service shutdown.

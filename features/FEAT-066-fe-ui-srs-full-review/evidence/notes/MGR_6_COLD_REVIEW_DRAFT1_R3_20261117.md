# MGR-6 Cold Review Draft 1 — R3

Status: DRAFT / READ-ONLY REVIEW / NOT AN IMPLEMENTATION APPROVAL.

## Task identity and pins

- Observation/report worktree: `D:\GitHub\Sketch2Life\.worktrees\manager-api`
- BE branch / HEAD / locally resolved `origin/dev`: `feature/feat066-manager-api-contracts` / `1c9148e88600a101887e477541c4c4893ba1c7df` / same commit.
- Final source observation: 2026-11-17 23:07:39 +07:00 (Asia/Saigon). Cold review completed 2026-11-17 23:06:56 UTC (23:06:56 Asia/Saigon).
- FE worktree: `D:\GitHub\Sketch2Life\.worktrees\ui`; branch / HEAD: `codex/fe-ui-web-remediation` / `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2`.
- FE audit plan: `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV52_WEB_API_INTEGRATION_AUDIT_20261117.md`, 51,614 bytes; SHA-256 `64D74F5873E8FF6F84CF6BED6753BC4553EB38B5EFB3058E9B0DFB87FAE765D4`.
- Canonical requirement authority: repository `docs/context/SRS_AUTHORITY.md` identifies Rev60 as the current unsigned working SRS. Canonical file: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 553,948 bytes; SHA-256 `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`. No external Rev69 copy was used as current authority.

### MGR-6 document pins

| Document | Before this task | After correction and cold review |
|---|---|---|
| `plan/PLAN_MGR6_IMMUTABLE_LESSON_VERSION_REVIEW_CONTRACT_DRAFT1_20261117.md` | 19,130 bytes; SHA-256 `5310303E9B197A031AA81A8D89A78DCBF26F670E6EC84E452C9DB2158C752C07` | 19,776 bytes; SHA-256 `514066776BFAF0AC5BABDC9BE4D87C3E1A2C9892E28DB51B6F39BE9AEEB7FFAC` |
| `evidence/notes/MGR_6_IMMUTABLE_LESSON_VERSION_REVIEW_CONTRACT_DRAFT1_20261117.md` | 17,060 bytes; SHA-256 `E2FAD0BE89A37FA5A928CB0E0D239ADE49325A7BFBA342505F4B71841A0E2E18` | 17,407 bytes; SHA-256 `9991DCEB80FA51DE6FA533FFC5093E17FE2E46F67CD8A099B4CC9C98A20C1434` |
| This R3 cold-review report | Absent before creation | Hash/bytes recorded in the task completion response; this report does not self-embed its own hash. |

## Corrections recorded

- The organization-level Manager grant-list and decision paths were already corrected in the two current drafts and are retained after rechecking the pinned router: `GET /api/lesson-library/v1/organizations/{organization_id}/access-grants` and `POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` (plan lines 30–31; source evidence lines 28–29). The router declarations, static composition, static catalog, separate legacy projection, and unverified runtime/gateway boundary remain distinct.
- Plan line 44 and source-evidence line 37 now identify the source-level error-envelope mismatch. For Lesson Library HTTP exceptions, request validation, and unhandled exceptions, `app.py` branches at lines 467–491, 612–622, and 725–740 statically emit `code`, `message`, `request_id` and `X-Request-ID`; Rev60 §9.8 lines 824–839 names `correlation_id` and `retryable` as required body fields. Optional `retry_after_seconds` and `field_errors` need not be present. No runtime response is claimed.
- Plan line 69 records the envelope mismatch as an unresolved BE/owner contract item alongside permission and state/hash error mapping. The drafts preserve the distinction between SRS requirement, source behavior, technical proposal, and OPEN owner/technical decisions.
- The mismatch evidence is source-backed in `backend/src/sketch2life/interfaces/http/app.py`; related SRS clauses are canonical Rev60 §§9.8, 21.1, 21.4, and 31.3. Pagination default 50/max 100 versus SRS default 25/max 100 and changed-payload idempotency 409 `IDEMPOTENCY_KEY_REUSED` versus SRS 400 `INVALID_IDEMPOTENCY_KEY` remain documented gaps.
- No code, API, test, OpenAPI, SRS, decision, approval, status, context, or pre-existing review/evidence file was edited. No test/build/validator/runtime command was run.

## Worktree status at observation

At the final identity check, the BE worktree still had the expected branch/HEAD and locally resolved `origin/dev` pin, with zero staged paths. Pre-existing modifications to FEAT-066 `CONTEXT.md`, `DECISIONS.md`, and `status/STATUS.md`, and pre-existing untracked MGR-1–6 records/plans were preserved. The two target MGR-6 documents and this one new report are the only files authorized by this task. No staging, commit, push, stash, reset, restore, or clean was performed.

## Cold reviewer response — recorded verbatim

## Cold review result

**Reviewer:** `/root/mgr6_cold_review` (Codex subagent)  
**Completed:** 2026-11-17 16:06:56 UTC (23:06:56 Asia/Saigon)

**Verified pins:**

- Plan: 19,776 bytes; SHA-256 `514066776BFAF0AC5BABDC9BE4D87C3E1A2C9892E28DB51B6F39BE9AEEB7FFAC`
- Evidence note: 17,407 bytes; SHA-256 `9991DCEB80FA51DE6FA533FFC5093E17FE2E46F67CD8A099B4CC9C98A20C1434`
- Rev60: 553,948 bytes; SHA-256 `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`
- FE audit plan: 51,614 bytes; SHA-256 `64D74F5873E8FF6F84CF6BED6753BC4553EB38B5EFB3058E9B0DFB87FAE765D4`

BE branch/HEAD and local `origin/dev` match the requested pin. FE branch/HEAD also match the evidence note. Recorded BE source hashes and the FE `ManagerScreens.tsx` and `backendApi.tsx` hashes match.

### Verdict and findings for verbatim recording

**ACCEPT**

**Findings:** None (P0–P3).

### Review basis

The two source paths are correctly recorded as organization-level routes: `GET /api/lesson-library/v1/organizations/{organization_id}/access-grants` and `POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision`. Router declarations, static composition, catalog entries, and the separate legacy projection are distinguished correctly; runtime and gateway reachability remain unverified.

The Rev60 requirements are separated from current source behavior, technical proposals, and open choices. The source stores `version_id` on the grant, exposes no grant hash, and the decision path uses that stored version without comparing it to the current version pointer. The draft does not infer superseded-grant policy or race guarantees. Persistence-boundary immutability is explicitly unverified.

The pagination, replay, revision, and error comparison matches the inspected source: grant-list default 50/max 100 versus Rev60’s default 25/max 100; changed-payload idempotency returns `409 IDEMPOTENCY_KEY_REUSED` versus Rev60’s `400 INVALID_IDEMPOTENCY_KEY`; stale revision returns `409 STALE_REVISION`; and all three cited Lesson Library exception branches return `code`, `message`, and `request_id` with `X-Request-ID`, omitting Rev60’s required `correlation_id` and `retryable`.

The FE audit pin matches. The Manager page calls the grant list, current lesson detail, and decision APIs. Its guard compares version IDs and requires content; it does not verify a hash.

### Remaining unverified boundaries

No generated full OpenAPI, runtime, gateway/proxy mapping, deployed routing, database state, or concurrency behavior was checked. Database enforcement of content/hash immutability and route-specific runtime error behavior remain unverified. No tests, builds, validators, or other prohibited commands were run.

**This is a planning-only review. It grants no approval or integration authorization.**

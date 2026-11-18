# MGR-3 Teacher Candidate and Class Assignment Contract — Source Evidence Draft 1

**Date:** 2026-11-17  
**Worktree:** `.worktrees/manager-api`  
**Branch / HEAD:** `feature/feat066-manager-api-contracts` / `1c9148e88600a101887e477541c4c4893ba1c7df`  
**Purpose:** source/SRS evidence for contract planning only. No implementation, test, OpenAPI generation, runtime, database, FE, or approval work is authorized or performed here.
**Revision note:** this evidence note was corrected in place with Draft 1 after independent cold review, only to clarify §9.8 error requirements and D-066-62 provenance at §4.1. It remains Draft 1 and grants no approval.

## 1. Preflight and pins

Preflight was performed before creating either MGR-3 draft. Branch and HEAD matched the requested baseline. Staged file count was 0. The worktree had 8 pre-existing status paths, all preserved:

- Modified: feature `CONTEXT.md`, `DECISIONS.md`, and `status/STATUS.md`.
- Untracked: MGR-1 owner disposition note; MGR-2 source evidence note; MGR-2 cold-review owner disposition note; MGR roadmap plan; MGR-2 plan.

The MGR-3 plan and this evidence note were not present in that preflight status. No staged or unrelated file was changed by the MGR-3 draft authoring step.

| Input record | Bytes | SHA-256 |
|---|---:|---|
| Repository `AGENTS.md` | 3,406 | `89ACC84AA4D838730205A03917B40DEB37E9622AAF7092E982476D934EC29A61` |
| Root `.codex/sketch2life-harness.md` | 2,178 | `0364DD280483D7AB56EAAF7F0B2CEF56A86D627393CA9996FC88A14E3318E12F` |
| `docs/context/SRS_AUTHORITY.md` | 4,054 | `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F` |
| Canonical FEAT-063 Rev60 SRS | 553,948 | `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B` |
| `docs/context/PROJECT_CONTEXT.md` | 81,664 | `EDEC7010C6B351E6DC6E9145941F479E5C39DF4770060625FD9BBAF719AD04BF` |
| `docs/context/SOURCE_REGISTER.md` | 113,526 | `D09F5849F4A3829EC4241FF1A840319225909E0EECA93A9BF6964625C4E987A0` |
| FEAT-066 `CONTEXT.md` | 54,263 | `CBF0EB1C980C43095E0AF8286A243EF6A4DA3214C0D38E04F192CEA87499707C` |
| FEAT-066 `DECISIONS.md` in the current working tree; D-066-62/63 are not in pinned HEAD | 38,951 | `A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C` |
| FEAT-066 `DECISIONS.md` at pinned HEAD; Git blob `ca0143cfd432bb70bfdf79e988228ef2066d9b50`; neither D-066-62 nor D-066-63 is present | 34,226 | `6BA0A8D21A2A78D03A121B1851F0B76CAFAB914309B3E00C7DF5D1E0A5371172` |
| FEAT-066 `status/STATUS.md` | 47,967 | `41B71598BA64426A0DAD917A1ECF68D77FD74381FAF8AD06644BB7F41B4D90CE` |
| MGR roadmap plan | 18,974 | `5E7CDB0AF03A27FF0DABFE949E41F7230D1BE7453EF56274E8CED388F6F196ED` |
| `approvals/TASK_APPROVAL.md` | 35,351 | `F1E24987615C2E8D0C303BDD29A6B8F3C8B1971D4B198431021300E80C7605A2` |
| MGR-1 owner disposition note | 4,016 | `B32D4CBC47811960A5DE2B2F1A3CAA9C84B64F8F9DC7F79CD0CD68F92F37883A` |
| Owner-authored MGR-1 task attachment explicitly listing D-066-62 | 6,173 | `A274A6BF0F1680FE6E1602C41454FD5F59D3580A10F542CCB1276286723BB305` |
| MGR-2 plan Draft 1 | 22,177 | `900EA080B8E3E3C59FCF338D2249E1967FBEAEE87FF072422C1C534DB72A5A8E` |
| MGR-2 evidence Draft 1 | 12,644 | `EEA5343F1FA42A8EE1E06B97329A4C9D814144E4FC8E0EE56F37E6CEC3CAE0C5` |
| MGR-2 cold-review owner disposition | 3,808 | `7F6BD4C2E9A9562904ABE55C4C26E7DE53CAD0077F88951E203B3DAE08DF2C47` |
| Prior MGR-3 cold-review result, retained unchanged | 3,137 | `C96F0204AC0D5238663B0C661903815752A0F466982AEB09DBA8ADA569F247EA` |

### Decision provenance and baseline

At pinned HEAD `1c9148e88600a101887e477541c4c4893ba1c7df`, `DECISIONS.md` is 34,226 bytes / SHA-256 `6BA0A8D21A2A78D03A121B1851F0B76CAFAB914309B3E00C7DF5D1E0A5371172` (Git blob `ca0143cfd432bb70bfdf79e988228ef2066d9b50`). A direct search of that blob contains neither D-066-62 nor D-066-63; its final decision is D-066-61. The pinned commit is not represented as containing either later decision.

In the current working tree, `DECISIONS.md` is 38,951 bytes / SHA-256 `A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C`; D-066-62 is at lines 260–268 and D-066-63 at lines 270–280. The read-only comparison with HEAD showed these sections appended after the D-066-61 outcome. This file was already modified before the MGR-3 drafts and was not edited for this provenance update.

- **D-066-62:** owner decision recorded in the current working tree, not present at pinned HEAD. Owner provenance is confirmed by the owner-authored MGR-1 task attachment (listed and pinned above), whose lines 24–27 say the MGR-1 decisions are already recorded as D-066-62 and explicitly set the same-organization verified-Teacher eligibility and BE1 authority. The current MGR-1 disposition note, lines 14–18 and pinned above, records the same decision. MGR-3 relies on this working-tree owner decision only for candidate eligibility and assignment-time revalidation; it is not a Rev60 route/field requirement and does not close the broad Manager permission resolver.
- **D-066-63:** owner decision recorded in the current working tree, not present at pinned HEAD. Its provenance is the owner's direct MGR-2 correction instruction in this conversation, which specified the idempotency, GRACE/RESTRICTED, effective-time suspension, 404/403, and unresolved Billing/public-mapping boundaries recorded in D-066-63. The current MGR-2 owner-disposition note, lines 34–36 and pinned above, records the same MGR-2 direction. That direct instruction is not a pinned repository artifact. D-066-63 is MGR-2-only and supplies no MGR-3 candidate or assignment policy.

The owner decisions are therefore known from their owner-task sources but remain outside the pinned Git baseline. A reviewer restricted to HEAD must treat them as absent there. The previous MGR-3 cold review returned CHANGES REQUIRED on precisely this baseline distinction; this provenance update does not replace or revise that historical review.

The external Downloads SRS selected for MGR-2 was not used as MGR-3 authority. MGR-3 follows repository `SRS_AUTHORITY.md` and the pinned Rev60 file above. No SRS or authority record was changed.

## 2. SRS and decision evidence

| Source | Relevant evidence | MGR-3 interpretation |
|---|---|---|
| Rev60 FR-T-02, lines 521–522 | Authorized School Manager assigns exactly one responsible Teacher per class; permission storage/resolver is OPEN at §31.10. | One active responsible Teacher is a product requirement. Broad Manager permission resolution is not decided here. |
| Rev60 FR-T-14/17, lines 533 and 536 | Reassignment/offboarding uses a BE1/Story saga; emergency conflicting-run closure is explicit, reasoned, audited, metadata-only, and preserves media/quota/sample claims. | Full transfer is a distinct lifecycle from initial assignment. Do not claim it is implemented or closed by MGR-3. |
| Rev60 §9.8, lines 820–839 | Every API error uses the stable safe envelope `code`, `message`, `correlation_id`, `retryable`, with optional `retry_after_seconds` and `field_errors`; HTTP 403 `ACTION_NOT_ALLOWED` is only for a known in-scope action denial; HTTP 404 `RESOURCE_NOT_FOUND` has the same shape for nonexistent and out-of-scope resources. | These codes and envelope are SRS-SPECIFIED. Current BE1 `SCOPE_DENIED` / `ACCOUNT_SCOPE_UNAVAILABLE` responses and `request_id` envelope are source gaps, not target policy. Assignment-specific conflict mapping remains OPEN where Rev60 does not define it. |
| Rev60 UC-12, lines 1498–1508 | Preflight current assignment version; revoke old access/token and make class read-only; Story owner/lock transfer; BE1 finalizes only after receipt; compensate or stay pending/read-only for reconciliation; enforce exactly one current Teacher. | Full saga scope is a proposal for a separate contract task pending owner disposition. |
| Rev60 UC-13, lines 1510–1519 | Teacher onboarding/identity recovery has a verified-identity lifecycle before activating assignment/scope. | Current source does not evidence the complete candidate identity/onboarding source. No onboarding is added to this task. |
| Rev60 §21.1, lines 1605–1614 | Idempotency key for state-changing commands; retain key on retry; stable opaque cursor, default 25/max 100, explicit deterministic order. | Apply to candidate list and assignment command. Exact route, cursor encoding/order field and literal idempotency header stay open. |
| Rev60 §21.2, lines 1616–1624 | `POST /v1/classes/{class_id}/assignments`, exactly one active Teacher, success HTTP 200 with assignment revision. | Existing 201/no-revision response is a contract gap. SRS path to BE prefix mapping stays open. |
| Rev60 §21.4, lines 1668–1672 | Same idempotency key and payload replays; different payload returns `INVALID_IDEMPOTENCY_KEY`; some revisioned commands require expected revisions, but this list does not prescribe an assignment precondition. | Idempotency semantics are specified. Assignment precondition and revision increment details remain open. |
| Rev60 §31.10(14), line 2726 | Principal/role/tenant mapping, assignment persistence, resolver/version/cache/revocation remain OPEN. | Candidate eligibility policy is not from the SRS. The general resolver/storage implementation remains OPEN. |
| D-066-62, current `DECISIONS.md` lines 260–268 | Owner decision recorded in the current working tree, not present at pinned HEAD. Owner-authored MGR-1 task attachment (6,173 bytes / `A274A6BF0F1680FE6E1602C41454FD5F59D3580A10F542CCB1276286723BB305`, lines 24–27) explicitly records the same verified same-organization Teacher rule and BE1 write-time authority. | MGR-3 uses this working-tree owner instruction for candidate eligibility/revalidation only. It does not choose candidate route/fields or the broad resolver. |
| D-066-63, current `DECISIONS.md` lines 270–280 | Owner decision recorded in the current working tree, not present at pinned HEAD. Owner's direct MGR-2 correction instruction in this conversation and current MGR-2 disposition note lines 34–36 support its MGR-2-only direction. | No MGR-3 policy is based on D-066-63. It remains MGR-2-only and does not approve implementation. |

## 3. BE source facts and evidence level

The listed source files below were read directly at the branch/HEAD in §1. Byte counts and SHA-256 pins appear in §4. Line references are to that pinned worktree source.

### 3.1 Current caller assignment read

- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:107–126` declares `GET /organizations/{organization_id}/me`. It verifies the caller assignment, then queries rows matching the path organization, `principal.subject`, and `active=True`. Its response reports that same caller's subject and role/class pairs. It is not a Teacher directory.
- No candidate route or candidate DTO was found in the audited BE1 registry surface. No candidate route appears in the relevant full OpenAPI catalog or Rev22 projection allowlist. This absence is bounded to the inspected BE1 source and catalog/projection; it is not a runtime enumeration claim.

### 3.2 Current assignment command

- `be1_registry.py:129–207` declares `POST /classes/{class_id}/assignments`, under router prefix `/api/be1/v1`.
- `be1_runtime.py:19–24` includes the registry router. `router_composition.py:35–46` mounts the BE1 runtime in classroom composition; `router_composition.py:64–78` reuses classroom composition for the combined app. `app.py:1004–1010` selects combined/classroom composition. This is static composition evidence, not a runtime request.
- `be1_runtime.py:39–41` defines `CreateAssignmentRequest.subject`, 1–256 characters. The base request rejects extra fields. The handler has bearer `get_verified_adult` for the caller, no idempotency parameter, and no expected assignment revision.
- The handler locks an active class row (`be1_registry.py:136–143`), requires caller `school_admin` assignment (`144–150`), and counts active class Teacher assignments (`151–166`). It trusts request subject to create the assignment (`167–183`) and returns raw subject with assignment ID, role, class ID, and active flag (`184–207`). No candidate role/state/org-membership check is present in this handler.
- `be1_common.py:91–139` checks the caller's active identity and assignment rows. It raises 403 when assignment/account scope is missing; it does not validate the body-selected candidate.
- `be1_models.py:37–58` defines identity state/account role/role revision. `be1_models.py:63–90` defines assignment state without assignment revision or transfer-pending state. Its unique constraint is the full organization/subject/class/role tuple, not one active Teacher per class.
- `be1_common.py:64–75` creates code/message failures; `Be1Error` in `be1_runtime.py:449–452` serializes code, message, and `request_id`. The BE1 exception handler in `app.py:488–522` emits this source envelope and an `X-Request-ID` response header. Rev60's error fields are not all present in this source envelope.

### 3.3 Other identity/assignment mutations

- `platform_admin_accounts.py:40–68` accepts Teacher as an account role and requires organization ID only for School Manager.
- `platform_admin_accounts.py:290–340` provisions a Teacher identity with `account_role=teacher`; the organization-assignment helper is invoked only for a School Manager. `GET /api/platform-admin/v1/accounts` is Platform Admin account discovery, not a tenant-scoped Manager candidate API.
- `platform_admin_accounts.py:181–204, 373–455` contains role-change logic that can deactivate assignment rows. Changing account state to disabled updates identity state/provider account but does not set assignment rows inactive in the inspected path. `AdultIdentityModel.role_revision` increments on role/state changes; no assignment revision is written there.
- `auth_registration.py:143–151` creates a Parent identity. `be1_bootstrap.py:22–59` provisions an initial organization and school-admin assignment. These do not populate an organization-scoped Teacher candidate source.
- A repository-source search of direct `OrganizationAssignmentModel` construction found the class-Teacher write in `be1_registry.py` and school-admin account/bootstrap writes. No separate Teacher invitation, candidate read, assignment revoke, or Story transfer-saga route was found in the inspected HTTP composition/source. This is a source-search result, not a runtime claim.

### 3.4 OpenAPI, tests, and runtime are separate

- `openapi_contract.py:3723–3755` catalogs the current caller assignment read. `openapi_contract.py:10856–10908` catalogs assignment POST with X-Request-ID, `CreateAssignmentRequest {subject}`, bearer security, 201 generic object, and generic error responses.
- `openapi_srs_v22.py:8–25` includes the current caller read and assignment POST in its projection allowlist. This is the source for a versioned projection, not evidence that a generated schema was refreshed. It is not the current product SRS authority.
- `test_m2_s1a_teacher_routes.py:28–36, 91–173` contains source assertions for the subject-only DTO, class row lock, existing-Teacher conflict, and 403 missing-class denial. These assertions were not run.
- `test_m2_s1a_teacher_postgres.py:235–285` contains a two-request assignment race test source asserting one 201 and one 409. It was not run; presence is not execution evidence. The source uses synthetic fixtures and is not runtime evidence for this review.
- No `app.openapi()` call, test, build, validator, backend/runtime, database, Docker, network/provider, or Modal command was run. Generated schema and current runtime status remain OPEN / NOT VERIFIED.

## 4. Source pins

All paths are relative to the repository root. Git HEAD in §1 pins the baseline; hashes below let the cold reviewer verify the files directly.

| Source file | Bytes | SHA-256 |
|---|---:|---|
| `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` | 20,549 | `B090F30C4F87FB53D8A85A83C53391AD77F086AF83F0A1E202EACB0F1C0375FE` |
| `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | 16,707 | `7B3C7FD2F767D3E0062CC6B2217A5DDE39FCE5D9566EA4A4C350CC7C35FA31E1` |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | 28,152 | `515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666` |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | 16,142 | `74AA865DFB2C925244F1CA446BFA054F48A42B0645E39FF0C144657E5510B3CC` |
| `backend/src/sketch2life/interfaces/http/routers/be1_runtime.py` | 1,014 | `89C54AC8EDB63FD2DC9A92910BE817645D9429B8A54E0485F86A826BA6A863A7` |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 | `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` |
| `backend/src/sketch2life/interfaces/http/app.py` | 73,905 | `A25495D8F61590926B90F08BE3044B588E1C81F55C33C0377C5ECEB73271C8DC` |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | 11,122 | `29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3` |
| `backend/src/sketch2life/interfaces/http/routers/platform_admin_accounts.py` | 17,541 | `1D43D61B68182E621E1409B7983D2C3D5651751ED0C6C67432BC871397E9945D` |
| `backend/src/sketch2life/interfaces/http/routers/auth_registration.py` | 7,099 | `48631EEB0C74B55FE9399A5504FD6655CB28A68A33CD3DA67615CBBC69C93336` |
| `backend/src/sketch2life/infrastructure/persistence/be1_bootstrap.py` | 3,484 | `4BABCCFD85FEF81C282EF0741CFFB242B49EAF3781BEB013632FDB7456F1A09B` |
| `backend/tests/contract/test_m2_s1a_teacher_routes.py` | 9,031 | `A3BE759D8031FA0EC80A697E2D6226D739EA4D772811376F91EA6A8600D8B003` |
| `backend/tests/integration/test_m2_s1a_teacher_postgres.py` | 14,168 | `93EEBFFD8E51ADE58F63D19AF707A56F8F0E859BE0648D38B3D15CE2DA9EDDEB` |

## 5. Open items retained

- Candidate path, request filters, response field names, display-label/PII policy, candidate-reference semantics, and stable ordering key.
- Existing verified Teacher organization-membership source and its relationship to UC-13 onboarding/provisioning.
- Manager authorization resolver/storage/version/revocation details under §31.10(14); current `school_admin` check is observation only.
- Assignment revision representation/increment rules, any expected-revision precondition, and operation-specific stale/conflict mapping.
- Literal idempotency header, key format/length, fingerprint/canonicalization, missing-key result, and replay receipt retention/storage.
- A concurrency invariant that covers every assignment-affecting writer; no unique index/table or transaction boundary is selected.
- Candidate/assignment route-prefix mapping and generated OpenAPI output.
- Whether full UC-12 saga is split from MGR-3; the plan's split is a proposal awaiting owner disposition.
- Owners for BE1 identity, organization membership, persistence, identity provisioning, and Story transfer are not identified by the source. Do not assign owners by inference.

## 6. Review handoff and status

This evidence note accompanies plan Draft 1 at `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MGR3_TEACHER_CANDIDATE_ASSIGNMENT_CONTRACT_DRAFT1_20261117.md`. The prior cold-review result is preserved unchanged in `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_3_COLD_REVIEW_DRAFT1_20261117.md` (3,137 bytes / SHA-256 `C96F0204AC0D5238663B0C661903815752A0F466982AEB09DBA8ADA569F247EA`). It returned CHANGES REQUIRED with a P2 finding because D-066-62/63 were absent from pinned HEAD. This task adds provenance context only; it does not create a new review session or change that verdict.

The prior non-ACCEPT verdict means no MGR-3 checkpoint is appended to feature `CONTEXT.md` or `status/STATUS.md`. No review verdict is duplicated or rewritten here. MGR-3 remains DRAFT / NOT APPROVED / NOT LAUNCHED until a later owner decision and separate Task Approval.

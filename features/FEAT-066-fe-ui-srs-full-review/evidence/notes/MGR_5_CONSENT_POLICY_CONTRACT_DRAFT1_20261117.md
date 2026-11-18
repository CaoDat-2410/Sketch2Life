# MGR-5 Draft 1 — Consent-policy source evidence

Status: DRAFT / NOT APPROVED / NOT LAUNCHED. This is planning evidence only. Line references below are tied to the pinned worktree identities listed at the end and should be rechecked if those pins change.

## Product authority and decision provenance

- SRS_AUTHORITY.md (4,054 bytes; SHA-256 032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F) points to canonical FEAT-063 v2.7-draft Rev60 (553,948 bytes; SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B). Rev60 is unsigned and remains a draft; it is nevertheless the repository's current product authority.
- Rev60 §§31.3, FR-PL-07, and AC49 state Parent ownership/authority for Parent-profile consent and grants and prohibit a default implication of Manager access to child profile/media. No separate school-managed consent workflow is specified in the cited current SRS requirements.
- Current working DECISIONS.md: 38,951 bytes; SHA-256 A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C. D-066-62 is at lines 260–268.
- Pinned-HEAD DECISIONS blob: ca0143cfd432bb70bfdf79e988228ef2066d9b50, 34,226 bytes. D-066-62 and D-066-63 are absent. Do not represent D-066-62 as committed at HEAD.
- MGR-1 owner disposition note: 4,016 bytes; SHA-256 B32D4CBC47811960A5DE2B2F1A3CAA9C84B64F8F9DC7F79CD0CD68F92F37883A. Lines 14–18 corroborate the owner-task boundary: Parent remains the actor for Parent-profile consent/grants; staff cannot create/revoke effective Parent consent; a staff-created pending record is not effective Parent consent; separate school-managed consent remains undecided.
- D-066-63 is MGR-2-specific and is not used as a MGR-5 basis. Historical external Rev69-header SRS referenced by MGR-2 is not canonical and is not used here.

## BE declaration and handler evidence

Pinned BE branch/HEAD: feature/feat066-manager-api-contracts / 1c9148e88600a101887e477541c4c4893ba1c7df.

| Method/path | Source and line evidence | Observed implementation | Limits / gap |
|---|---|---|---|
| GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | backend/src/sketch2life/interfaces/http/routers/be1_registry.py:548–579 | Verified-adult dependency; assignment/scope checks, class lookup, organization/class-filtered rows; response exposes consent_id, purpose_ref, state, and effective=false. | No pagination, revision, or effective Parent-grant resolution in this handler. No runtime invocation performed. |
| POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | be1_registry.py:493–545; request schema backend/src/sketch2life/contracts/schemas/be1_runtime.py:52–57 | Verified-adult dependency; route/body class equality; assignment check; creates pending row; responds 201 with effective=false; records audit/event. | No idempotency/revision input. Inspected handler does not call get_class or verify child belongs to class. Treat this as source gap. Pending is not proof of approved policy or Parent consent. |
| POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke | be1_registry.py:582–631 | Verified adult and assignment check; lookup scoped by org/class/consent; revoked is idempotently returned as observed source behavior; otherwise state changes to revoked and audit/event is recorded. | No request key or revision. This is record-state revocation, not Parent grant revocation. Source's same-result behavior is not a substitute for SRS command idempotency. |

Request DTO RecordConsentRequest is exactly class_id, child_id, purpose_ref, optional evidence_ref (be1_runtime.py:52–57). Persistence model ConsentRecordModel at backend/src/sketch2life/infrastructure/persistence/be1_models.py:238–257 constrains state to pending/revoked and stores organization/class/child/purpose/evidence/recorded actor/time/verification_note. It has no effective Parent-grant state or record revision. Runtime persistence behavior and audit retention were not exercised.

Authorization helper evidence: backend/src/sketch2life/interfaces/http/routers/be1_common.py:83–139 checks verified adult and assignment; the current list handler calls get_class (lines 142–152), while create does not in the inspected body. The existing helper's 403/404 mapping is implementation behavior, not target policy. Rev60 §9.8 requires RESOURCE_NOT_FOUND for nonexistent or out-of-scope resources and ACTION_NOT_ALLOWED for a known in-scope denial. Current BE codes such as SCOPE_DENIED/ACCOUNT_SCOPE_UNAVAILABLE, where returned, need mapping review; the HTTP wire envelope is NOT VERIFIED. FastAPI detail is produced by be1_common.py:64–65.

## Static mount and API catalog evidence

- backend/src/sketch2life/interfaces/http/routers/be1_runtime.py:19–24 includes be1_registry.router with prefix /api/be1/v1.
- backend/src/sketch2life/interfaces/http/router_composition.py:35–45 includes the BE1 router in classroom composition; lines 60–75 include classroom and lesson-library routers in the combined composition.
- backend/src/sketch2life/interfaces/http/app.py:256 and 1004–1011 select and create the default/combined application composition. This is static source evidence only; it does not establish deployed mounting or runtime success.
- backend/src/sketch2life/interfaces/http/openapi_contract.py contains static operation metadata for GET, POST, and revoke near lines 2975, 3124, and 3273. backend/src/sketch2life/interfaces/http/openapi_srs_v22.py:8–45 includes consent operations in the legacy v2.2 FE-facing projection. No OpenAPI generator was run and no generated full OpenAPI artifact was inspected in this task. Catalog entries and a projection are not runtime evidence.
- No test was run. Source-only related assertion at backend/tests/integration/test_be1_postgres_api.py:738–755 covers a pending/effective=false response; test-file presence is not evidence that it passed.

## FE evidence

Pinned FE branch/HEAD: codex/fe-ui-web-remediation / 297a28b1f406ab80e25d6e0aa5577e4b6f505ee2.

- apps/web/src/modules/school-manager/be1/services/managerBusinessService.ts:58–62 exposes a consent list GET method.
- apps/web/src/modules/school-manager/be1/pages/RosterConsentPage.tsx:221–255 loads and displays the rows, including purpose/state/effective fields; line 254 states the page is read-only while suitable policy is pending.
- No Manager service method or page call for consent record/revoke was found in the inspected Manager flow. The shared generic API's unrelated consent helpers do not establish a Manager write caller.
- The BE response hardcodes effective=false; FE must not translate a pending/revoked staff record into Parent consent. The FE fixture/test source is not runtime evidence and was not run.

## Contract questions left OPEN

1. Does the product need a separate school-managed consent workflow at all? If yes, owner must specify purpose and legal basis, authorized actor/role, organization/class/child scope, whether Parent participation is required, effective-state semantics, evidence, transitions, revocation, interaction with Parent-owned consent, audit and retention. Until answered, all Manager consent writes are unavailable.
2. Which consent fields, if any, may a School Manager read? The current UI is read-only implementation evidence, not an approved field-visibility policy.
3. For any later state-changing route: literal idempotency header and format, replay receipt/retention, record revision, stale-write result, and transaction boundaries remain open. Rev60 §§21.1 and 21.4 supply the general idempotency requirement; no route-specific syntax is inferred here.
4. Existing create's class/child relationship validation, exact target error-envelope mapping, audit delivery/retention, and external prefix mapping require source/contract follow-up. No runtime behavior is claimed.

## Baseline pins

BE worktree D:\GitHub\Sketch2Life\.worktrees\manager-api, branch/HEAD above. FE worktree D:\GitHub\Sketch2Life\.worktrees\ui, branch/HEAD above. Key source pins captured during authoring:

| Worktree-relative source | Bytes | SHA-256 |
|---|---:|---|
| BE backend/src/sketch2life/interfaces/http/routers/be1_registry.py | 20,549 | B090F30C4F87FB53D8A85A83C53391AD77F086AF83F0A1E202EACB0F1C0375FE |
| BE backend/src/sketch2life/contracts/schemas/be1_runtime.py | 16,707 | 7B3C7FD2F767D3E0062CC6B2217A5DDE39FCE5D9566EA4A4C350CC7C35FA31E1 |
| BE backend/src/sketch2life/infrastructure/persistence/be1_models.py | 28,152 | 515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666 |
| BE backend/src/sketch2life/interfaces/http/be1_runtime.py | 16,807 | 62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85 |
| BE backend/src/sketch2life/interfaces/http/router_composition.py | 3,743 | 2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463 |
| BE backend/src/sketch2life/interfaces/http/routers/be1_common.py | 16,142 | 74AA865DFB2C925244F1CA446BFA054F48A42B0645E39FF0C144657E5510B3CC |
| BE backend/src/sketch2life/interfaces/http/openapi_contract.py | 1,377,229 | 175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE |
| BE backend/src/sketch2life/interfaces/http/openapi_srs_v22.py | 11,122 | 29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3 |
| FE apps/web/src/modules/school-manager/be1/services/managerBusinessService.ts | 2,409 | 2FDE883554E5A1D7E02B74ED80A7B1B1D145A92315A2EA391A2E7ADD22414B8D |
| FE apps/web/src/modules/school-manager/be1/pages/RosterConsentPage.tsx | 11,344 | 5E3D3B5D234FAFCE31D0DF0ADA24926510A432D3C5D9468FB395578EF8FE5F96 |

No source or FE file was modified. The source pins identify the files reviewed, not runtime evidence.

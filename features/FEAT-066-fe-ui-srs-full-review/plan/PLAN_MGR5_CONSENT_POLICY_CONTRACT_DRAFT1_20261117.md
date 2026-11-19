# MGR-5 — Consent-policy contract (Draft 1)

Status: DRAFT / NOT APPROVED / NOT LAUNCHED  
Scope: planning and contract review only; no implementation is authorized.

## Goal

Establish a source-backed contract boundary for Manager consent visibility and any possible school-managed consent workflow. The current evidence does not establish that such a workflow is required or authorized. Until an owner decision defines it, Manager consent write actions remain unavailable. A pending staff-origin record must never be represented as Parent consent or as effective consent.

## Authority and provenance

- Current product authority: repository SRS_AUTHORITY.md selects FEAT-063 Rev60. Rev60 is a draft pending formal sign-off, but is the current repository product baseline for this planning task.
- Rev60 §§31.3, FR-PL-07, and AC49 make the Parent the owner/actor for Parent-profile consent and grants and do not define a separate school-managed consent workflow. The SRS must be consulted directly before any later policy decision.
- D-066-62 is recorded in the current working-tree DECISIONS.md at lines 260–268, but is absent from DECISIONS.md at pinned HEAD 1c9148e88600a101887e477541c4c4893ba1c7df. The pinned blob is ca0143cfd432bb70bfdf79e988228ef2066d9b50 (34,226 bytes). D-066-62 is an owner decision recorded in the current working tree, not content present at pinned HEAD. MGR-1 owner disposition evidence at lines 14–18 records the same boundary. It says staff cannot create or revoke effective Parent consent; Parent remains the actor for Parent-profile sharing consent/grants; a staff-created pending record is not effective Parent consent; a distinct school-managed workflow is not decided.
- D-066-63 concerns MGR-2 only and is not a basis for this contract.
- FEAT-066 records are implementation evidence, not product-policy authority.

## Current source inventory

The route prefix declared by the BE router is /api/be1/v1. Full-path descriptions below are source paths; external gateway/proxy rewriting has not been verified.

| Method and source path | Declared behavior | Auth/scope and DTO | Current response and behavior |
|---|---|---|---|
| GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | Declared in be1_registry.py:548–579 | Verified adult; organization/class assignment check; class lookup; no query pagination/revision contract | Lists consent record identifiers, purpose, state, and effective=false. |
| POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | Declared in be1_registry.py:493–545 | Verified adult; school_admin/teacher assignment check; body RecordConsentRequest has class_id, child_id, purpose_ref, optional evidence_ref. Body class must equal path class. | Creates a pending ConsentRecordModel; returns 201 with state=pending and effective=false; audit/event recorded. No idempotency or revision input is present. Handler does not call get_class or verify child-to-class membership in the inspected path; treat that as an implementation gap, not permission to infer scope policy. |
| POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke | Declared in be1_registry.py:582–631 | Verified adult; school_admin/teacher assignment check; lookup scoped by organization/class/consent | Changes a record to revoked; an already revoked record is returned as-is; response reports effective=false. This is not Parent grant revocation. No idempotency key or expected revision is present. |

Persistence at be1_models.py:238–257 allows only pending/revoked states and records organization, class, child, purpose, optional evidence, recording actor/time and verification note. It does not model an effective Parent grant, revision, or an SRS-defined school-consent lifecycle. Source audit/event calls exist; end-to-end audit retention and delivery are NOT VERIFIED.

Static composition evidence: be1_runtime.py:19–24 includes the registry router; router_composition.py:35–45 mounts BE1 in the classroom composition and lines 60–75 include it in the combined composition; app.py:256 and 1004–1011 select compositions. This establishes static registration paths only, not runtime reachability or deployed configuration.

Static OpenAPI evidence: openapi_contract.py has metadata entries for GET, POST, and revoke near lines 2975, 3124, and 3273. openapi_srs_v22.py:8–45 projects these consent operations into the legacy FE-facing v2.2 projection. No generated full OpenAPI artifact or runtime endpoint has been inspected for this draft. These catalog/projection facts do not establish runtime success.

## SRS boundary and proposed contract

| Topic | Current product requirement / evidence | Draft treatment |
|---|---|---|
| Parent-profile consent/grant actor | Rev60 §§31.3, FR-PL-07, AC49; D-066-62 in working tree only | Parent is the actor for effective Parent-profile consent/grants. A Manager-created pending record cannot imply Parent consent or effective state. |
| Separate school-managed consent | No distinct workflow, actor authority, legal basis, effective state, or revocation semantics found in the cited Rev60 provisions | OPEN — OWNER DECISION REQUIRED. Do not expose Manager record/revoke actions until decided. |
| Existing BE pending record | Current handler creates pending/effective=false | FACT about source only. It is not evidence of a valid school consent policy or effective Parent grant. |
| Manager read visibility | Current FE displays organization/class consent rows read-only | Field allowlist, purpose, legal basis, and whether Managers may see these records remain OPEN unless existing owner-approved policy is located. Keep current page informational and avoid implying consent validity. |
| Idempotency/revision | Current write routes have neither. Rev60 §§21.1 and 21.4 define generic idempotency expectations for state-changing commands; route-specific key syntax, retention, and any revision model are not established here. | Any future state-changing contract must satisfy the current SRS idempotency rules. Exact header, replay receipt, record revision, and stale-write mapping remain OPEN pending contract definition. |
| Authorization and organization scope | Source checks verified adult plus assignment for school_admin/teacher; create handler does not validate class existence/child membership in the inspected function. Rev60 §9.8 standardizes errors. | Proposed Manager contract must revalidate actor and organization/class/child scope server-side at write time. Missing/out-of-scope resources use the SRS 404 RESOURCE_NOT_FOUND shape; 403 ACTION_NOT_ALLOWED is for known in-scope denial. Existing source error mapping is a source gap until directly reconciled. |
| Error envelope | Rev60 §9.8 defines the standard envelope and error codes. BE helper currently raises FastAPI HTTPException detail objects (be1_common.py:64–65); deployed wire shape is NOT VERIFIED. | Target the §9.8 envelope. Record actual source mapping as a gap; do not claim wire-level conformance. |
| Audit | Source calls audit/event recording on create/revoke | Proposed future contract must retain actor, organization/class, action, target, reason/evidence references, timestamp, and correlation where policy permits. Exact retained fields, retention, and delivery guarantee are OPEN. |

No new route or schema is selected by this draft. Existing route shapes are implementation facts, not an approved Manager policy contract. If an owner approves a distinct school-managed workflow, a follow-up contract must define actor and scope, purpose/legal basis, evidence, effective-state meaning, transitions, revocation, interaction with Parent consent, read visibility, audit/retention, idempotency, revision, errors, and FE controls before any write becomes available.

## FE behavior observed

The Manager consent page is RosterConsentPage.tsx. It calls the Manager business service GET method, renders purpose/state/effective fields, and states that the screen is read-only while appropriate policy is pending (page lines 221–255). managerBusinessService.ts:58–62 contains the GET path; there are no Manager service record/revoke methods in that file. The shared generic client contains other consent-related code, but no Manager page call establishes a consent write path. Current page data can therefore be shown only as source-reported pending/revoked records; the UI must not label them as Parent authorization.

## Dependencies and exclusions

- Depends on MGR-1 consent actor/source/effective-state disposition and a new explicit owner decision on whether a distinct school-managed consent workflow exists.
- MGR-2 capacity, MGR-3 assignment, MGR-4 membership, and MGR-6 lesson review may proceed independently where scopes remain disjoint.
- Excludes Parent-profile consent creation/revocation UI, child-profile/media access, legal interpretation, new consent state machine, database changes, route implementation, and FE writes.
- MGR-7 write-scope approval is blocked for any MGR-5 consent command until the owner decision and contract review are complete.

## Acceptance criteria for a future contract

1. It traces every policy statement to Rev60 or a clearly labeled owner decision; unowned points remain OPEN.
2. It distinguishes a staff-origin pending record from Parent consent and effective grant state in API, UI, and audit language.
3. It defines actor, tenant/class/child scope, purpose, evidence, transitions, revocation, idempotency/replay, staleness, errors, audit, and read fields before enabling writes.
4. It binds all state-changing commands to server-side authorization and scope revalidation; wrong-organization/out-of-scope behavior follows Rev60 §9.8 unless a separately approved exception is recorded.
5. Manager write actions stay disabled until the owner policy, BE contract, and separately approved verification pass.

## Future verification plan (not run)

After explicit policy and implementation approval: verify route declaration and composition; inspect generated full OpenAPI separately from the public SRS projection; exercise authorized/unauthorized, cross-organization, invalid class/child, duplicate/replay, stale revision, pending/revoked, audit, and error-envelope cases with synthetic fixtures; verify Manager UI exposes only approved fields and leaves writes disabled until the contract gate passes. Runtime claims require a separately authorized runtime verification. No tests, build, validator, OpenAPI generation, or runtime command was run for this planning draft.

## Planning disposition

Draft 1 is suitable for independent review as a source-backed boundary and owner-decision brief. It is not an approved policy, implementation contract, or launch authorization. MGR-5 writes remain unavailable.

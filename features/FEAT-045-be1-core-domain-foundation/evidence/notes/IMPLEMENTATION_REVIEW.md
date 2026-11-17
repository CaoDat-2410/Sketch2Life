# BE1-01 implementation and architecture review

- Reviewed: 2026-10-14 (Asia/Saigon).
- Scope: FEAT-045 plan revision 1, approved BE1-01 fixture/domain foundation only.
- Authorities: `features/FEAT-045-be1-core-domain-foundation/plan/PLAN.md`, `approvals/TASK_APPROVAL.md`, ADR-0015, and canonical Master SRS v3.1 (FEAT-029).
- Evidence index: `../README.md`.

## Acceptance review

| Criterion | Result | Evidence and boundary |
|---|---|---|
| AC-01 | PASS | Boundary models are strict, frozen, versioned, and reject unknown fields. `unknown-command-field` probes `FIELD_NOT_ALLOWED`. Fixture metadata marks the candidate contract `PROPOSED_UNADOPTED`. |
| AC-02 | PASS | Authorization requires a verified identity-port principal, capability, role where applicable, and organization/resource scope. Forged principal, wrong scope, admission class mismatch, and canvas target mismatch are rejected before mutation. |
| AC-03 | PASS | Synthetic cases accept 36 and 155 completed months and reject 35 and 156. The domain does not calculate age from a date of birth or inspect media. |
| AC-04 | PASS within the modeled foundation | Effective consent is child-, organization-, and purpose-specific. Admission requires an open session, pending membership, consent, and matching class/group scope. Pending devices cannot use roster/art/canvas capabilities. Canvas writes require admitted membership, a matching active turn, device, and canvas grant. Gallery contributor IDs are projections after audience authorization; they are not an access grant. |
| AC-05 | PASS for the port contract and fixture adapter | Stale revision and changed-payload idempotency conflict reject without mutation; exact replay returns the stored revision. The fixture ledger performs compare-and-swap plus receipt storage under one lock. This does not prove distributed or durable transaction behavior. |
| AC-06 | PASS | 20 synthetic cases cover authorization, profile/consent, session/admission, turn/canvas, gallery/portfolio, and data lifecycle, with typed negative outcomes. |
| AC-07 | PASS | The standalone runner uses only synthetic JSON and the feature-local in-memory ledger. It makes no live service, provider, account, or database call. |
| AC-08 | PASS within the scoped layers | Static import inspection found only standard-library imports in the domain and standard-library/domain imports in ports. Application imports ports and domain inward. Pydantic is used at the explicit contract boundary. Source status is retained on each fixture and manifest entry. |

## Source status and target gaps

- Master SRS v3.1 confirms the 36–155 month boundary and core behavior such as scoped permissions, teacher-controlled admission, selected-child turn attribution, consent/access controls, gallery/portfolio, and export/delete capability.
- B12 and B21–B22 describe candidate logical contracts. The manifest and every fixture therefore label the contract `PROPOSED_UNADOPTED`; fixture pass status does not approve those schemas for HTTP, database, or mobile use.
- Exact consent verification authority/process, jurisdiction, mixed-age policy, detailed shared-artwork deletion, provider/backup purge evidence, and several data-class retention periods remain `TBD` or proposed. Data-request completion here checks only its modeled state and unresolved-item count; it does not inventory or prove deletion of every copy.
- Identity resolution is represented by a port and a synthetic server-resolved principal. No live authentication, QR/admission credential lifecycle, or account provisioning is implemented.
- Revision/idempotency atomicity is an adapter requirement demonstrated by an in-memory fixture ledger. No durable storage, distributed locking, migration, API, queue, or integration adapter exists in this feature.
- Age is an adult/profile-supplied completed-month value. This feature does not implement DOB calculation or migrate the existing older age helper.
- Gallery and portfolio return authorized contributor/source references only. They do not copy media, assign unverified contributions, rank children, or apply a retention policy. The owner-confirmed 90-day session/artwork default is not enforced here.
- BE1-02, cross-workstream integration, production readiness, and load/performance proof are outside this approved task.

## Review findings closed

1. Bound requested canvas session/canvas/class/group/child scope to the loaded turn and membership, and return `SCOPE_DENIED` before mutation on mismatch. Added `canvas-target-scope-mismatch`.
2. Require admission target class to match the loaded membership class. Added `admission-target-class-mismatch`.
3. Preserve requirement-status labels in fixture schema/data and mark the candidate contract separately as `PROPOSED_UNADOPTED`.

## Verification record

- Runner: `python features/FEAT-045-be1-core-domain-foundation/src/run_fixture_validation.py` — 20 domain fixtures and 1 contract probe passed. Full output: `../raw/fixture-runner-output.txt`.
- Quality: Ruff 0.16.3 on Python 3.14.7; check and format check passed for six new Python files. Output: `../raw/quality-checks.txt`.
- Dependency scan: domain and ports passed the static import boundary scan. Output: `../raw/dependency-scan.txt`.

## Review result

AC-01 through AC-08 are satisfied for the approved BE1-01 isolated foundation. Completion means the synthetic domain/contract harness is reviewable and reproducible; it is not a claim that proposed SRS contracts are adopted or that the system is integrated or production-ready.

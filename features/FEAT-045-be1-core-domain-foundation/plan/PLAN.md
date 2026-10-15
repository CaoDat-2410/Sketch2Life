# BE1-01 — Core domain, ports, and fixture contracts

- Status: APPROVED
- Plan revision: 1
- Implementation status: NOT_STARTED
- Created: 2026-10-14 (Asia/Saigon)
- Owner request: “làm task người 1, be 1, làm các cái core”
- Allocation interpretation: P2 / BE1 core, per ADR-0015; bounded to the independent foundation card BE1-01.

## Goal

Create a framework-independent backend foundation for the core classroom and collaboration handoffs: domain types and rules, application ports, closed/versioned boundary schemas, synthetic fixtures, and a standalone fixture runner. Preserve the distinction between owner-confirmed requirements and SRS proposals that still need decisions.

## Authorities

- `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`, BE1-01.
- `docs/adr/ADR-0015-four-person-role-and-integration-allocation.md`.
- Canonical Master SRS v3.1, especially B19–B26 and its scope/status labels.
- `docs/architecture/DEPENDENCY_RULES.md` and `docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md`.
- Direct owner instruction in this conversation, 2026-10-14 (Asia/Saigon).

## Scope

1. Define typed core command/result/failure envelopes and conventions for aggregate revisions, compare-and-swap, idempotency keys, and request fingerprints.
2. Define domain value types and application ports spanning authorization/scope, organization/class/managed profile/consent, session/group/admission/turn, canvas operations, gallery/portfolio observations, and data-lifecycle requests.
3. Publish closed, versioned schemas and synthetic fixtures for the above handoffs. Every fixture manifest identifies its contract version, owner, source trace, and synthetic-only data policy.
4. Provide a standalone runner using in-memory adapters. Positive and negative cases must exercise scope denial, role forgery, age boundaries, stale revisions, and duplicate idempotency keys with changed payloads.
5. Record evidence and an architecture review inside this feature folder.

## Explicit boundaries

- This is BE1-01 only. BE1-02 storage adapters/migrations, HTTP routes, live authentication, database/object-store/queue adapters, deployments, cross-workstream wiring, and production readiness are excluded.
- No Firebase Storage, Firestore, or Realtime Database. No provider calls, credentials, real accounts, or real child data.
- Do not freeze the remaining technology stack or convert SRS `PROPOSED`/`TBD` choices into product defaults. Preserve source-status labels in schemas/fixtures; only the task's direct acceptance checks and owner-confirmed facts are enforced here.
- Age input is adult/profile supplied in completed months. Validate the owner-confirmed inclusive 36–155 boundary; do not add a date-of-birth calculation or mixed-age compatibility policy.
- No edits to the in-progress FEAT-037 registration artifacts or its untracked age helper as part of this feature.

## Acceptance criteria

- AC-01: Core command/result/failure schemas are versioned, immutable at the boundary, and reject undeclared fields.
- AC-02: Authorization evaluates verified principal role and explicit organization/class/session/resource scope; a caller-supplied or forged role cannot grant access.
- AC-03: Managed-profile age validation accepts 36 and 155 completed months and rejects 35 and 156. It does not infer age from media or DOB.
- AC-04: Consent and membership are purpose- and scope-specific; a pending join or declared contributor ID alone never grants roster/art/canvas access.
- AC-05: Aggregate revision mismatch returns a typed stale failure without changing state. Reusing an idempotency key with the same request fingerprint replays the receipt; a different fingerprint returns a typed conflict without resetting state.
- AC-06: Synthetic contract fixtures cover authorization, class/profile/consent, session/group/admission, turn/canvas, gallery/portfolio, and data-lifecycle handoffs, including expected results and typed failures.
- AC-07: The standalone runner requires no live service/provider/database and reports every fixture/probe result reproducibly.
- AC-08: Domain code has no framework/infrastructure imports; ports are inward-facing; evidence documents source-vs-target gaps and limitations.

## Steps

1. Translate BE1-01 and SRS B19–B26 into a bounded contract map, retaining confirmed/proposed/TBD labels.
2. Implement pure domain value types and typed errors, plus application ports and fixture-only in-memory adapters.
3. Add closed versioned boundary models, synthetic manifest and positive/negative fixtures.
4. Implement the standalone validator and acceptance probes; capture its command and output under this feature's evidence.
5. Review dependency direction, fixture provenance, scope boundaries, and unadopted proposals; update context, decisions, evidence index, and status.

## Risks and mitigations

- B19–B26 contain many candidate contracts. Keep only the BE1-01 boundary in scope and label every unadopted candidate.
- Existing prototype modules may encode older product behavior. Avoid modifying unrelated in-progress feature files; document any collision for a later approved migration.
- A fixture pass proves only this isolated contract/domain harness, not persistence, API integration, concurrency under load, or production readiness.

## Verification and evidence plan

- Run the feature-local standalone fixture runner and record exact command, environment, output, timestamp, and interpretation.
- Inspect imports for framework/infrastructure leakage and review contracts against the BE1-01 trace list.
- Store manifest, fixtures, runner output, and architecture/source-gap notes only under `features/FEAT-045-be1-core-domain-foundation/`.

Implementation is allowed only for revision 1 and this exact bounded scope, as recorded in `approvals/TASK_APPROVAL.md`.

# P2-T4 Blocker-0 contract reconciliation approval request

- Evidence ID: EV-003-T4-RECON-01
- Date: 2026-09-13
- Owner: Person 2
- Feature: FEAT-003 multimodal understanding
- Status: **REQUESTED - NOT GRANTED**
- Governing plan: `../../plan/P2_T4_CONTRACT_RECONCILIATION_PLAN.md`
- Related research plan: `../../plan/P2_T4_FUSION_RESEARCH_PLAN.md`
- Authoritative task approval: `../../approvals/TASK_APPROVAL.md` (unchanged)

## Request

Approve a separately scoped Blocker-0 reconciliation workstream for the
conflicting P2-T2/P2-T3/P2-T4 provider-neutral contract family and the live
FEAT-018 provider-shaped contract family. The owner has selected B0 Option 3:
reconciliation must be completed and approved separately before P2-T4 can
freeze an implementation contract.

This request is for the reconciliation workstream only. It does not approve
P2-T4 fusion implementation, schema implementation, migrations, fixture
production, runtime wiring, provider execution, or any FEAT-018 implementation.

## Direction already selected

The following direction is recorded in the FEAT-003 decision record and the
P2-T4 research plan:

- B0 Option 3 is selected: reconcile the live FEAT-018 family with the
  P2-T2/P2-T3/P2-T4 family under a separately approved workstream.
- This selection does not choose a final canonical shape, authorize a
  migration, or authorize implementation.
- `TASK_APPROVAL.md` remains unchanged and does not grant this request.

## Reconciliation deliverables

If approved, the workstream will produce an auditable decision package that:

1. inventories each producer, consumer, route, adapter, port, fixture,
   manifest, and Gate A/P1 handoff that currently uses either contract family;
2. provides a field-by-field compatibility matrix, including serialized names,
   discriminators, optionality, failure representation, source references,
   provenance, uncertainty, privacy constraints, and version identifiers;
3. selects either one canonical versioned contract or an explicit versioned
   mapping between the families, with ownership and authority recorded for
   every retained, renamed, transformed, or rejected field;
4. defines the compatibility boundary and migration/non-adoption behavior,
   including a synthetic migration fixture or equivalent deterministic proof;
5. defines deterministic fail-closed behavior for unsupported versions,
   ambiguous mappings, missing required provenance, malformed payloads, and
   identity collisions;
6. records the downstream checks required by the FEAT-018 contract freeze,
   Gate A, P1, and FEAT-015 integration fixtures; and
7. records rollback and non-adoption criteria so no producer or consumer is
   changed until the selected mapping or canonical contract is separately
   approved.

The package must not silently settle the P2-T4 fused result shape by treating
the research plan's candidate sketch as frozen. Any final shape decision must
be visible in the reconciliation record and receive the approval required by
the repository governance rules.

## In-scope repository surfaces after approval

The reconciliation may update only the documentation, registry, and
compatibility evidence needed to complete Blocker 0. Depending on the selected
outcome, the affected surfaces may include:

- `features/FEAT-003-multimodal-understanding/plan/` and its source/contract
  register references;
- the FEAT-015 fixture manifest, expected payload, loader, or flow only when a
  deterministic compatibility fixture is required;
- FEAT-018 `plan/CONTRACT_FREEZE.md`, contract registry records, and related
  provider/consumer documentation;
- P1/Gate A consumer documentation and checks; and
- a clearly named, synthetic-only compatibility fixture and its evidence.

This approval request itself does not edit those implementation or fixture
surfaces. Any implementation change discovered to be necessary must be
listed as a follow-up scope and separately approved before execution.

## Non-goals and prohibitions

The approved reconciliation workstream will not:

- implement P2-T4 schemas, fusion code, migrations, adapters, routes, or
  runtime wiring;
- implement or modify FEAT-018 production contracts, routes, adapters, or
  ports as part of this request;
- run live providers, GPU workloads, Runpod, Lightning, or external model
  services;
- install dependencies or download models, weights, or external payloads;
- create real child data, credentials, tokens, secrets, or provider endpoints;
- modify P2-T2 or P2-T3 source contracts or their immutable baselines;
- authorize the complete P2-T4 fusion implementation; or
- modify the authoritative `TASK_APPROVAL.md` as part of drafting or
  requesting approval.

## Acceptance criteria for this request

The reconciliation workstream is complete only when all of the following are
true and separately reviewed:

- the conflicting contract identities and all relevant producers/consumers are
  enumerated with source paths;
- a canonical versioned contract or explicit versioned mapping is selected,
  with no unowned or silently transformed fields;
- source reference, provenance, uncertainty, privacy, status, discriminator,
  and failure semantics are compatible with the selected boundary;
- a synthetic deterministic compatibility/migration fixture proves the
  selected boundary, or records why a fixture is impossible and supplies an
  equivalent proof;
- unsupported, ambiguous, malformed, and privacy-invalid payloads fail closed;
- FEAT-015, FEAT-018, Gate A, and P1 consumers have recorded compatibility
  checks or explicit follow-up ownership;
- rollback/non-adoption conditions and the next approval gate are recorded;
- no implementation or runtime behavior changed under this request; and
- the reconciliation evidence is stored under this feature's `evidence/`
  directory and passes the required repository validators.

## Validation plan

Before any reconciliation commit or push, run from the worktree root:

```text
git diff --check
python tools/validate_harness.py
python tools/validate_architecture.py
python tools/validate_repository_security.py
python tools/validate_skeleton.py
```

Also perform focused read-only checks for the source register, contract
registry, approval links, version/discriminator consistency, fixture hashes,
and the unchanged `TASK_APPROVAL.md`. No evidence may contain real provider
payloads, secrets, credentials, or model-generated free text.

## Approval boundary

Approval requested: **Blocker-0 contract reconciliation only**.

Approval not requested or granted: P2-T4 fusion implementation, any schema or
runtime change, migration execution, FEAT-018 implementation, or any provider
execution. `TASK_APPROVAL.md` remains unchanged. A later implementation plan
and approval request are required after reconciliation completes.

**This document records a request, not an approval.**

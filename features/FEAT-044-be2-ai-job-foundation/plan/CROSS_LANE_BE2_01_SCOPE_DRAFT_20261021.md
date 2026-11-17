# BE2-01 cross-lane dispatch scope addendum

- Status: DRAFT / AWAITING_OWNER_APPROVAL
- Card: FEAT-044 / BE2-01, foundation dispatch ownership
- Addendum to: plan/PHASE_B_PLAN.md revision 3; does not rewrite or supersede it
- Integration design: FEAT-057 plan revision 4, SHA256
  6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601
- Proposed scope SHA256: fill after final review, before approval

## Purpose and approval boundary

The existing Phase B approval covers its pinned B1-B6 scope. It does not cover
dispatching BE2-08 jobs into the separate VideoWorker, nor does the Phase B approval
adopt BE2-07 source fencing, BE2-08 atomic submission/finalization, BE2-09 review, or
BE2-14 policy binding. This addendum proposes only the BE2-01-owned dispatch route.
No source work is authorized until the owner approves this exact addendum and its
final file manifest.

## Baseline facts

- DispatchWorker currently calls the foundation AiProviderPort directly.
- WorkerDispatchEnvelope contains a DispatchMessage and capability. The message
  identifies a job type and request reference; it does not directly carry the full
  BE2-07 source pin or the BE2-08 idempotency key.
- BE2-08 owns VideoWorker and VideoWorkerAdmission. The receiving admission boundary
  must load the persisted authoritative job/request and verify the envelope; the
  router must not synthesize trusted source or session fields.
- Unknown job types must fail closed and must not fall through to a generic provider.

## Proposed implementation scope

1. Add a typed route selection for the BE2-08 job type at the foundation dispatch
   boundary. Preserve the existing provider route for job types already owned by it.
2. Route the original envelope to the adopted BE2-08 worker entrypoint. Do not edit
   BE2-08-owned ports or implementation from FEAT-044.
3. Require the receiver to verify persisted job identity, request reference, attempt,
   organization/scope and capability. An absent, mismatched, stale, or unknown mapping
   is rejected without a provider call.
4. Keep the dispatch envelope unchanged unless a reviewed contract diff proves a
   field is missing. If the route requires payload/schema/migration changes, stop and
   submit a separate contract change request before implementation.
5. Preserve at-least-once dispatch behavior. Idempotent admission and duplicate/lost
   acknowledgement recovery belong at the receiver's authorized admission/finalizer
   boundary, not in a router-side cache.

## Candidate allowed files

- Modify: backend/src/sketch2life/infrastructure/ai_jobs/worker.py
- Add only if the current worker cannot hold a small typed router cleanly:
  backend/src/sketch2life/infrastructure/ai_jobs/typed_dispatch.py
- Add: backend/tests/unit/test_ai_job_video_dispatch.py
- Existing regression, read-only during this scope unless a failing test needs an
  approved in-scope correction: backend/tests/unit/test_ai_job_b4_dispatch.py and
  backend/tests/integration/ai_jobs/test_dispatch_recovery.py
- FEAT-057 composition tests and adapter files remain owned by FEAT-057 and are not
  editable under this card approval.
- No migration, job schema, envelope schema, router, provider, or BE1 file is included.

The addendum review must confirm each exact path. Any new path or shared contract
change requires a revised manifest and renewed approval.

## Acceptance criteria

| ID | Required result |
|---|---|
| F01 | An adopted BE2-08 job type selects exactly one registered receiver, passes it the unchanged envelope, and does not also call the generic AiProviderPort. |
| F02 | The receiver performs authoritative persisted-job/request/attempt checks; altered or stale envelope identity causes no VideoWorker generation and no generic-provider fallback. |
| F03 | Unknown job type fails closed with the existing typed failure/retry policy; it never reaches AiProviderPort by default. |
| F04 | Re-delivery remains safe through BE2-08 admission receipts; FEAT-044 does not claim exactly-once broker delivery. |
| F05 | Existing BE2-01 dispatch/recovery regressions pass and the route has unit coverage for known, unknown, duplicate and mismatched envelope cases. |
| F06 | No direct BE2-08/BE1 table writes, no new source-pin/idempotency fields, no schema migration, and no change to Phase B acceptance/status. |

## Dependencies and exclusions

- Depends on BE2-08 approving the worker entrypoint and admission contract, including
  authoritative mapping from foundation request/job to video run and idempotency.
- Depends on the BE2-08 submission boundary creating the foundation job through the
  authorized foundation path.
- Excludes X05, X05c/CR09-02, BE2-13 route, live queue, PostgreSQL/provider/Lightning,
  environment work, and publication.
- X09-08 can be reported separately. Passing this card's tests does not close X09 or
  prove a complete BE2-01–14 runtime path.

## Proposed implementation sequence

1. Freeze the type discriminator, recipient interface, error mapping, and allowed files.
2. Implement the typed route and its negative/duplicate tests.
3. Run focused BE2-01 dispatch tests and the approved offline foundation regression.
4. Compose through FEAT-057 only after BE2-08 approval and report X09-08 separately.
5. Record independent review and fixes before any card acceptance decision.

## Approval state

No implementation approval is recorded. The companion file in approvals is an empty
approval draft. The existing Phase B approval remains unchanged and does not authorize
this added route.

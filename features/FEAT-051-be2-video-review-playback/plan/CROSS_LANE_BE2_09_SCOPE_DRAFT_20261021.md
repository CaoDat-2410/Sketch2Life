# BE2-09 cross-lane exact-artifact review scope addendum

- Status: DRAFT / AWAITING_OWNER_APPROVAL
- Card: FEAT-051 / BE2-09, review-owned projection and records
- Addendum to: plan/PLAN.md revision 1; frozen plan remains unchanged
- Integration design: FEAT-057 plan revision 4, SHA256
  6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601
- Proposed scope SHA256: fill after final review, before approval

## Purpose and approval boundary

BE2-09 already has local review components and own persistence. CR09-01 remains open
for the canonical review-head / combined DATA-27 projection of a committed BE2-08
artifact. This addendum proposes that bounded review-owned delta. It does not close
X05, authorize playback/session access, or make X05d appear adopted.

## Proposed implementation scope

1. Consume the final BE2-08 artifact only through an adopted public read contract.
   Bind review to exact organization/session/video ID, video version, artifact
   reference and media hash, plus source/bundle/script/context/audience/policy lineage.
2. Own the canonical review head, immutable review history, idempotency receipt and
   combined DATA-27 projection in BE2-09. Projection is keyed to the exact artifact
   hash/version and must not overwrite an unrelated or later artifact.
3. Reconcile CR09-01 with the existing ReviewWriteAccess and ReviewWriteBoundary
   contracts. A commit/replay must re-check current Teacher authority and adopted
   source/policy fences under the review UoW; a cached boolean or historical receipt
   is not current authorization.
4. Keep review writes and review-owned migration under FEAT-051. Do not update
   BE2-08 rows, schemas, or published migrations. If the shared DATA-27 shape needs a
   cross-owner change, stop for a versioned CR and matching approval.
5. Do not include CR09-02 session-start/access gateway, actual media playback, or
   current-source resolver implementation. X05c stays open. X05d stays BLOCKED until
   an already-adopted resolver/fence is identified.

## Candidate allowed files

- Modify only if CR09-01 requires card-owned behavior:
  backend/src/sketch2life/domain/video_review/model.py
  backend/src/sketch2life/application/video_review_write.py
  backend/src/sketch2life/application/ports/video_review_write.py
  backend/src/sketch2life/contracts/schemas/video_review.py
  backend/src/sketch2life/infrastructure/video_review/tables.py
  backend/src/sketch2life/infrastructure/video_review/sql.py
  backend/src/sketch2life/interfaces/http/routers/video_review.py
- Card-owned tests:
  backend/tests/unit/test_video_review_write.py
  backend/tests/unit/test_video_review_persistence.py
  backend/tests/contract/test_video_review_contract.py
  backend/tests/contract/test_video_review_http.py
- Excludes BE2-08 rows/migrations, BE1 session/access tables, BE2-07 invalidation
  receiver, FEAT-057 composition tests, and all CR09-02 implementation.

No migration is included in this draft. If the accepted DATA-27 projection cannot use
the existing review-owned schema, stop and prepare a schema-specific plan revision
and approval before changing any table or migration.

## Acceptance criteria

| ID | Required result |
|---|---|
| R01 | Review resolves the exact committed artifact and rejects absent, substituted, changed, stale, or mismatched artifact hash/version. |
| R02 | Canonical head and combined projection identify the same exact artifact and preserve the independent BE2-09 review revision. |
| R03 | Approve/reject/request-changes append immutable history and update the review-owned head, receipt and event atomically. |
| R04 | Concurrent CAS/replay has one winner; exact same operation returns its authoritative original result after reauthorization; changed body conflicts. |
| R05 | Teacher identity, organization/session, audience, source and policy checks either pass under adopted current gates or fail closed; no successful review is recorded while a required gate such as X05d is unavailable. A historical receipt is not present authorization. |
| R06 | No direct BE2-08/BE1 writes or migration edits; existing BE2-09 offline regression passes. |
| R07 | X05d remains BLOCKED without an already-adopted current-source resolver/fence; X05c/CR09-02 remains OPEN and no playback/session pass is claimed. |

## Dependencies and stop conditions

- BE2-08 must publish/adopt the exact final artifact read model and identity mapping.
- BE2-07 current-source fence adoption is required for a complete X05 claim. A new
  resolver/fence is outside this addendum and requires an owner-approved scope.
- BE2-14 policy currentness must be consumed as an adopted gate, not inferred from
  the BE2-09 or BE2-08 local fixture.
- CR09-02 remains independent and is not authorized by this scope.

## Proposed implementation sequence

1. Resolve the CR09-01 canonical head and DATA-27 projection payload against the
   actual BE2-08 artifact read contract.
2. Freeze review-owned file and migration manifest.
3. Implement exact-artifact binding and guarded projection with replay/CAS tests.
4. Run the focused BE2-09 regression and independent review/fix/retest.
5. Report CR09-01 evidence separately; keep X05 partial until X05d and CR09-02 gates
   have their own adopted contracts and approvals.

## Approval state

No implementation approval is recorded. Existing BE2-09 revision 1 approval covers
its card-local P1-P4 work and does not approve this CR09-01 cross-card addendum.

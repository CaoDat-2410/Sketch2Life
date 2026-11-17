# BE2-07 cross-lane exact-source scope addendum

- Status: DRAFT / AWAITING_OWNER_APPROVAL
- Card: FEAT-056 / BE2-07, exact knowledge producer ownership
- Addendum to: plan/PLAN_REV1_APPROVED.md and the accepted component scope; neither is rewritten
- Integration design: FEAT-057 plan revision 4, SHA256
  6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601
- Proposed scope SHA256: fill after final review, before approval

## Purpose and approval boundary

BE2-07 already provides exact current export resolution and the offline component is
accepted. That does not prove a producer-validity fence stays effective through the
separate BE2-08 finalizer commit. This addendum proposes only the source-owned identity
and currentness side of that boundary. It does not claim distributed locking, change
card acceptance, or grant BE2-08 permission to write producer state.

## Baseline facts

- KnowledgeBundleService.resolve_exact checks the current exact bundle version/hash
  and current producer rules before returning an export.
- KnowledgeScriptVideoSourceResolver verifies organization/session/bundle/version/hash,
  editorial/context/audience revisions, source references, and non-empty script text.
- KnowledgeCommitCoordinator orders only the BE2-07 fixture process. Its own
  documentation explicitly says it is not a distributed fence.
- The returned exact read plus a later re-read cannot, by itself, prove no source
  invalidation occurred between revalidation and BE2-08 commit.

## Proposed implementation scope

1. Define a small versioned source-validity contract owned by BE2-07. It must bind the
   exact producer identity: organization/session, bundle ID/version/hash, editorial,
   context and audience revisions, and the exact source ref/version/hash set.
2. Expose that contract through the public BE2-07 application boundary. A consumer may
   request exact currentness only; it may not assemble a weaker pin from internal rows.
3. Define the producer-side invalidation/currentness signal and its failure behavior.
   Unknown, unavailable, superseded, revoked, or mismatched state fails closed.
4. Specify how a consumer holds or atomically revalidates this producer authority
   through BE2-08 finalization. The exact durable mechanism is a blocking design gate:
   it must be adopted by BE2-07 and BE2-08 before the implementation claims X01 PASS.
   The process-local coordinator is not an acceptable substitute.
5. If the only available implementation is a source re-read immediately before
   finalization, record X01 as PARTIAL because a race window remains. Do not claim the
   required fence or silently broaden the accepted contract.

## Candidate allowed files

- Modify only after the public contract is agreed:
  backend/src/sketch2life/application/ports/knowledge_bundle.py
- Modify if needed to return the producer-owned exact currentness result:
  backend/src/sketch2life/application/services/knowledge_bundle.py
- Modify source-owned fixture implementation/tests only:
  backend/src/sketch2life/infrastructure/knowledge_bundle/coordination.py
  backend/src/sketch2life/infrastructure/knowledge_bundle/fakes.py
  backend/tests/unit/test_knowledge_bundle_service.py
  backend/tests/unit/test_knowledge_bundle_races.py
- Existing source export and producer examples remain immutable unless an approved
  contract revision explicitly requires new fields.
- Excludes FEAT-057 adapter paths, BE2-08 media/worker/finalizer ports, BE2-01 owner
  fence implementation, new database schema/migration, and real cross-service lock.

This is a candidate manifest, not permission to edit every listed file. Review must
reduce it to the paths actually needed. A durable cross-owner fence requiring a new
schema/service/transaction owner stops for a revised approval.

## Acceptance criteria

| ID | Required result |
|---|---|
| K01 | Exact source identity contains all producer-owned revisions and source hashes needed to bind the BE2-08 pin. |
| K02 | Exact resolution rejects changed head/version/hash, audience/context/source revision, revoked or unavailable currentness. |
| K03 | Race tests demonstrate that a currentness change cannot be mistaken for a successful held fence; if the durable hold is not adopted, the result is explicitly PARTIAL. |
| K04 | Consumer-facing API is public and typed; no direct producer-table reads or caller-supplied allowed/current booleans. |
| K05 | Existing BE2-07 component acceptance and offline regression remain green; evidence does not claim a production or distributed adapter. |
| K06 | No change to old bundle bytes, source provenance, accepted card status, or runtime/provider scope. |

## Dependencies and exclusions

- BE2-08 must approve the matching consumer contract and finalization phase.
- FEAT-057 owns composition tests and records whether the implemented mechanism truly
  holds through the finalizer's commit.
- X05d remains BLOCKED: this addendum does not create an already-adopted current-source
  resolver/fence for BE2-09 review/playback.
- Excludes X02 invalidation delivery, CR09-02/session access, Modal, Lightning,
  provider, database provisioning, and publication.

## Proposed implementation sequence

1. Review the exact versioned identity and producer-side currentness semantics.
2. Agree the durable hold/revalidation protocol with BE2-08; stop if no adopted
   transaction/fence owner exists.
3. Implement producer-owned contract and race tests only in the frozen manifest.
4. Have BE2-08 consume the contract in its own approved files; FEAT-057 then runs the
   composition evidence on a pinned snapshot.
5. Preserve X01 PARTIAL until both sides and the composition test prove the selected
   boundary; do not infer full acceptance from component tests.

## Approval state

No implementation approval is recorded. Existing offline component acceptance is
unchanged and does not approve this cross-card producer-fence addendum.

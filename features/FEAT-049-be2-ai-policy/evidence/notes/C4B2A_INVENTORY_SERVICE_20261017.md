# C4b2a — current-owner/source inventory application composition

2026-10-17 Asia/Saigon, feature/be2-08-14 parent 87b3863. Approved P4;
plan/C4_COPY_LIFECYCLE.md updated before code. Previous turn committed inventory
persistence/tests: progress. Original attached goal read again; later actual
BE2-14 approval governs current work, not completion of BE2-12/full goal or PG
provisioning authority. No published foundation/shared contract changes.

## Implemented

Strict context/read and trusted source/coverage proof DTOs. Internal service
register/read/coverage/fence action bindings use current owner guard with actor/
org/exact data-request ref/scope/operation digest. Registration needs authenticated
source ref/hash and original copy/profile provenance; coverage caller provides
only revision/attestation ref, never verified flag or asserted source sets.
Backend outputs strictly/native revalidated; wrong scope/digest/hash/revision,
unverified or expired evidence rejected before registry mutation.

Own registry UoW remains inside owner/source/profile guard; confirm unchanged
current rights and source deadline before exit. Replay registration/fence still
rechecks source/rights and produces no repeated mutation. Metadata read retains
reported-only coverage semantics. Shared own validate_copy_grant helper reused by
C4a, with all original verifier tests passing. No provider dispatch or new schema.

Guard confirmation under registry lock must not acquire outer locks/network;
actual owner deadline-at-commit fence remains unbound. Guard-exit failure after own
commit is not fictitious rollback; exact current-authorized retry sees existing
registration. Guarded source verification is not durable source evidence history
yet; registration stores original profile/id only. Operation/envelope/history
storage remains next C4b2b, C4c dispatch/current lifecycle/receipt application open.

## Evidence

- 56 new service cases PASS with ASSUMED boundary/transactional MEMORY inventory.
- All 16 own contract/unit suites: 617 PASS /zero skip. Ignored JUnit
  .runtime/be2-14-c4b2a/component.xml. Six known Alembic offline warnings and eight
  intentional malformed native-model serializer warnings, fourteen total.
- Existing 477 selected regression and 114 targeted foundation application/
  review-regression/q00 suites PASS separately; source-pinned receipt under ignored
  .runtime/learning-content-component/20261017-165325-196265.
- Two new actual SQL service cases collected: source/coverage/fence composition
  and precommit owner denial rollback. Copy pack21, all PG65 prepared NOT_RUN.
  Runner transitive source pin includes new assumed inventory fixture.
- Focused Ruff/format PASS on eight source/test files, Mypy PASS on five source
  files; architecture/harness/security/whitespace PASS before commit.
  No real owner/source/provider calls, dependency install or server start.

First combined run: 96 PASS/one FAIL because fixture validated its deliberately
malformed nested coverage before returning it, yielding safe dependency error
instead of exercising service-native output rejection. Fixture now explicitly
model_constructs malicious output; production validation unchanged, test confirms
SOURCE_MISMATCH. Formatting/import/generic syntax adjusted to project Python3.12
style without lint suppression or weaker validation.

## Remaining

Durable exact operation intents/envelopes and immutable authority/source evidence
history (C4b2b), typed missing-hook/dispatch/acknowledgment/current-copy/receipt
application (C4c), real source/request commit-fence/BE1/P4/provider adoption,
actual SQL runtime, C5 projections/binding and consolidated full-card acceptance.
No actual cancel/purge/deletion, provider-wide closure, full card/goal DONE or
push/merge/deploy. Scope/consumer obligations in artifacts/C4B2A_INVENTORY_SERVICE_HANDOFF.md.

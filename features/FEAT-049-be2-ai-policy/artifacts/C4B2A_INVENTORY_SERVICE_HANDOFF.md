# C4b2a — guarded original-copy inventory service

ProviderCopyInventoryService is internal backend composition, not a mounted
endpoint/CMD-48 action or provider dispatcher. Requires own inventory store and
CopyInventoryBoundary; no default production/fake auth adapter mounted.

- register(actor, org, context, registration, source_ref): context exact data-request
  id/version/hash and scope; proposed original copy/profile metadata; immutable
  source reference/hash. Backend verifier authenticates actual original provenance,
  not caller assertion or latest profile alias. Duplicate exact registration still
  rechecks source/current rights; changed provenance cannot overwrite originals.
- page(actor, org, read_request): strict limit/revision cursor and current read
  authority. Stored coverage is historical reported metadata, not fresh attestation
  of provider-wide completeness or permission. Intervening mutation rejects scan.
- fence(actor, org, context): current independently authorized monotonic scope
  block, not cancellation/purge effect, provider acknowledgment or operation intent.
- coverage(actor, org, context, expected_revision=..., reference=...): only source
  reference/revision input, no client source sets/verified flags. Trusted resolver
  returns authenticated scoped original report with matching ref/hash/revision.
  Registry CAS rejects intervening mutations; reported_complete still not deletion.

Boundary guard pre-acquires actual BE1 subject/purpose/revocation/source/profile
fences. Grant binds actor/org/exact action/command digest/revision/deadline. Source
proof strictly typed, verified exact binding/reference and deadline; native bool
coercions rejected. Guard held through registry transaction, unchanged authority
and proof expiry confirmed again before UoW exit. Confirmation under registry lock
must not acquire outer locks or call provider network. Real source/request deadline
at owner's commit fence remains required; app precheck/mutex alone is not proof.

Results are inventory/initial metadata, not current lifecycle, dispatch/child-media
exposure grant, actual deletion or BE1 closure. Registration persistence stores
original profile/copy ids; source-proof verification is not yet a durable source
evidence-history record. C4b2b must add exact operation envelope/intents/authority+
evidence history; C4c supplies typed dispatch/acknowledgment and verified receipt
application/current copy lifecycle. Real hook/foundation CR adoption remains OPEN.

Own transaction errors roll back own writes when propagated. If an outer guard
fails after DB commit, do not claim rollback/refund: report safe dependency outcome,
then exact authorized retry rechecks current rights and observes existing record
without duplicate mutation. No blind new operation/key to hide uncertainty.

56 new service cases, 617 own total PASS; ASSUMED owner/source and MEMORY inventory,
not real provider verification. Two added actual SQL composition cases prepared;
copy pack21, all PG65 NOT_RUN. Commands/profile/impact/log-return instructions:
artifacts/C2_SQL_RUNTIME.md. No server install/start, provider call or actual deletion.

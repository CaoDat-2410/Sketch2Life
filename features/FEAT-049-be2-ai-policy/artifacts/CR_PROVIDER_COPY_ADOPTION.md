# ProviderCopyLifecycle — cross-owner integration gaps (OPEN, not approval)

Owner BE2-14; BE2-01 foundation provides candidate/fake support. P4 approved for
BE2-14 implementation, not permission to silently rewrite published foundation.

Inspected source at e0f77b1:

- domain/ai_jobs/provider_copy.py: ProviderCopy has org/scope/kind/profile string;
  PurgeReceipt has copy id/outcome/verified/evidence kind, but no org/scope/profile/
  operation/bytes hash binding. apply_receipt trusts verified truthiness. Existing
  candidate is safe only behind authoritative typed verifier, not raw client input.
- application/ports/ai_jobs.py: ProviderCopyRegistryPort list_scope returns a tuple,
  not coverage/pages; scope_lock has no durable fence guarantee. Adapter purge has
  no explicit durable operation key and cancel returns None, not acknowledgment.
- application/services/provider_copy_lifecycle.py: lifecycle replays stored receipts
  under scope lock; external call precedes receipt persist, leaving crash/restart
  deduplication dependent on adopted adapter idempotency. No verified request guard
  or own SQL registry supplied. Only infrastructure/ai_jobs/fakes.py implements it.

## Required additive adoption / acceptance

1. Durable operation envelope: org/scope/data-request exact ref/current authority
   revision/copy kind+id/exact profile/action/operation key; never a URL/token. Same
   envelope/key dispatch replay must deduplicate at provider hook; different binding
   conflicts. BE2-04/08 owns hook implementation, BE2-14 verifies exact receipts.
   Persist original profile version/hash; current profile alias alone cannot
   reconstruct original provenance or authorize silent repinning of older copies.
2. Hook response: typed receipt reference/hash or Pending/Unsupported/Exception,
   not raw verified=true. Separate cancel acceptance/confirmation and purge outcome.
   No hook/timeout is not deleted or synchronously stopped. No fabricated receipt
   claiming provider evidence merely to satisfy the current required enum.
3. Registry: stable scoped pagination + snapshot/coverage revision, known sources
   and completeness, durable scope-purging fence/atomic copy+receipt+intent, late
   registration quarantined. Empty tuple cannot certify provider-wide deletion.
4. Current request guard: BE1 authority/subject/purpose/expiry/revocation through
   commit; no actual provider call under DB lock. Persist intent first and verify
   acknowledgment after dispatch; race/restart/late results remain traceable.
   Expiry must be enforced by owner/registry commit fence; a scope mutex alone
   cannot freeze wall-clock deadlines. C4a entry checks are not that integration.
5. Verification cases: wrong org/scope/profile/copy/action/key/digest/hash, expired
   grant/receipt, fixture vs authenticated provider, stale/revoked replay, duplicate
   crash/restart, timeout, unsupported, partial/late discovery. Overall BE1 request
   never closed merely from BE2 scope report or fixture deletion.

No existing foundation/shared bytes changed by C4a. CR remains OPEN; do not present
it as adopted provider protocol, actual deletion proof or blocked whole-card work.
BE2-14 can continue own validation/registry/projection code; real owner/provider
adoption is separately gated, with BE1/P4 wiring deferred per user instruction.

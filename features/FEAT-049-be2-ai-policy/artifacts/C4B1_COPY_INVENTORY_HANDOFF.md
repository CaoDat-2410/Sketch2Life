# C4b1 — original-copy inventory persistence, NOT current lifecycle

SqlProviderCopyInventoryStore implements own scoped ProviderCopyInventoryStore
under ai_policy, forward ap_0004. Four tables: scope, immutable registration,
coverage observation history and audit/outbox event. No ai_jobs/BE1 writes or old
migration/shared contract changes. No production route/authorization adapter.

`transaction(org, scope, principal_id=verified_actor, for_update=...)` holds own
scope UPDATE for writes, SHARE for existing-scope reads. Caller must retain real
current-owner/profile/discovery guard and expiry commit fence through UoW. Storage
does not authenticate caller or coverage attestations. Never call provider under
this lock. Let mutation errors escape UoW for rollback; do not swallow them.

- register requires CopyRegistryRegistration with exact ORIGINAL profile ref,
  copy kind/id/org/scope. Same exact duplicate no-op; changed original conflicts.
  No status/deleted/verified assertion accepted. Immutable initially_quarantined
  records whether registration happened after scope purge fence.
- get(copy_id) is scoped by the bound transaction, not global foundation get.
- mark_purging is monotonic/idempotent, no unpurge. Earlier registrations remain
  fenced by page.scope_purging regardless of their original quarantine flag.
- page uses limit1..256, sorted copy-id keyset and expected_revision for continuation.
  Intervening mutations reject stale cursor rather than mixing snapshots. Missing
  scope returns observed empty revision0/unknown, no later phantom-row queries.
- record_coverage takes backend scope-bound report with expected_revision,
  registry revision, exact source attestation reference/hash, explicit required
  source set and observed subset. CAS to next scope revision, audit atomic. New
  registration/fence invalidates old observation. Empty registry defaults unknown.

CopyRegistryPage.coverage_status unknown/partial/reported_complete reflects only
declared-source report. It is NOT authenticated provider-wide coverage, deletion
or BE1 request closure. Real source attestation/current-owner guards remain unbound.
Coverage changes also invalidate pagination revision; caller must restart scan.

RegisteredProviderCopy.initial_copy derives only initial metadata with foundation
request_purge for late quarantine. It is NOT the latest copy lifecycle, a dispatch
request, purge receipt, permission or proof of cancellation. C4b2/C4c must persist
operation intents/current state/verified exact receipts and compose C4a verifier;
do not expose or dispatch copies from this metadata alone. Current scope purge
fence must always override original registration flag, including earlier copies.

Own scope/registration/coverage/audit share transaction; source authority and provider
effects do not. Guard/registry expiry fence, original profile adoption, operation
key dispatch deduplication/typed acknowledgment, missing-hook outcomes and actual
provider verification remain OPEN in CR_PROVIDER_COPY_ADOPTION.md. No implicit
foundation interface adoption from the own scoped port. Real BE1/P4 wiring deferred.

Component: 561 own cases PASS (27 new inventory checks +2 runner); 19 copy PG cases
prepared NOT_RUN, 63 all PG cases. Commands, environment/impact and logs to return:
artifacts/C2_SQL_RUNTIME.md. No provider API call, server install/start or actual
deletion. Full BE2-14 remains IN_PROGRESS.

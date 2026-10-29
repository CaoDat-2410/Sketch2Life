# C4c6 — exact operation receipt lease / consumer handoff

2026-10-18 Asia/Saigon, feature/be2-08-14 parent6f2e2c0. Previous goal turn made
progress through candidate discovery. Re-read original goal/current clean branch/
HEAD/approval/context/source register/plan; later actual BE2-14 approval governs,
not completion/redefinition of original BE2-12 goal. C4c6 subplan before code.

## Implemented

ProviderCopyOperationReceiptVerifier.verify(actor, org, original command, key,
expected_revision) is an internal context manager, no default/live adapter/route.
Current command authority precedes inventory read. Derive exact reference/hash
from stored receipt_available state and immutable original envelope/profile.
New own verifier port authenticates actual bytes/issuer/original profile/action;
proof binds full envelope/delivery revision/reference/current authority revision.
Native output/echo/expiry/action mismatch rejected. No source lookup/network under
own DB lock. Current owner/source/profile/proof fences held through caller commit.

Frozen lease exposes binding, proof and current authority, and confirms unchanged
rights/proof deadline before use/exit; no use after closed. apply_purge validates
exact current copy then reuses existing foundation request_purge/apply_receipt:
unverified deletion stays pending, fixture deletion is not actual. Separate cancel
confirmation cannot be used as purge deletion or directly mutate jobs/BE1.
Provider-kind synthetic outputs prove classifier rules, not actual evidence.

NEXT COMPOSITION: hold lease, enter own scope UPDATE UoW, re-read operation/
delivery/current copy, CAS expected revisions, persist proof/grant/result/history/
outbox atomically, lease.confirm() before commit, then exit lease. This checkpoint
does not write copy/proof state. Historical result is not execution authority.
Guard-exit failure after own commit is uncertainty, not invented rollback. Real
source/request deadline-at-commit fencing remains a separate adoption gate.

## Verification

- 29 new ASSUMED/MEMORY cases PASS: exact binding/profile/reference, fixture/
  provider-kind classification, unverified/pending/unsupported/exception, separate
  cancel acknowledgment, wrong action/native bool/hash/expiry, authority denial/
  revocation, stale revision, repinning, wrong current copy, unavailable receipt,
  private errors and immutable/closed lease with deadline reconfirmation.
- Own875 contract/unit PASS, zero failure/error/skip; ignored raw JUnit
  .runtime/be2-14-c4c6/component.xml. Twenty known warnings: six Alembic offline
  deprecations and fourteen intentional malformed serializer outputs.
- Selected source-pinned BE2-12/foundation477 PASS:
  .runtime/learning-content-component/20261017-174421-416735.
- Targeted foundation114 PASS/zero skip, .runtime/be2-14-c4c6/foundation.xml.
- PG93 unchanged NOT_RUN (15 lifecycle+10 activation+19 ledger+49 copy collected).
  No new SQL cases for lease-only/no-write code, no server/provider call.
- Focused Ruff/format5 files, Mypy3 source files, architecture/harness/security/
  whitespace PASS before commit. Ordinary import/line/nested-context fixes, no
  suppression or functional test failure. Fixture setup supports cancel/purge and
  preserves envelope command through helper dispatch. A late patch context mismatch
  made no edits; corrected against current import before proceeding.

## Open

Atomic current-copy/proof/cancel acknowledgment persistence/reconciliation,
restart/late-result/provider dedup conformance, kill delivery, C5 safe binding/
projections, C6 and actual SQL/current-owner/provider integration. No actual
cancel/deletion/cost/BE1 closure/full-card or goal DONE, push/merge/deploy.

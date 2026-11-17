# C4b2b2 — exact cancel/purge intent scheduling

2026-10-18 Asia/Saigon, feature/be2-08-14, parent edc1d40. Read original attached
goal and actual later approved BE2-14 revision1/P1–P5. Previous goal checkpoint
edc1d40 was progress; intervening user question only explained copy-file names.
Revalidated clean current branch/HEAD, approval/context/plan and open provider CR.
Extended C4 subplan before implementation; no frozen approval/plan/foundation edit.

## Implementation

Strict immutable operation envelope and authority observation DTOs; stable key
excludes renewed grant/time, exact body digest includes original target/profile
and data-request. Guarded internal schedule reuses current copy verifier boundary,
authorizes before read, resolves exact original profile outside SQL lock, re-reads
registration and confirms current authority before commit. Own SQL UoW adds exact
operation/history persistence, queued event and purge fence; forward ap_0006 has
immutable tables/scoped FKs. Replay keeps original envelope, fresh authority
history and no duplicate mutation. Known-key recovery reads immutable metadata;
does not deliver work, authorize a replay or acknowledge provider side effects.

## Evidence

- 44 new local operation cases PASS: cancel vs purge, exact binding/key, renewed
  authority preserving original grant, denial/revocation/expiry, profile pinning,
  conflicting request body, privacy error, missing copy, malformed native fields,
  original-registration change, commit rollback, postcommit guard uncertainty,
  native observation validation, exact frozen DDL/trigger, SQL write/replay shape,
  stored column/payload substitution, historical recovery and wrong actor/read-only.
- 689 own contract/unit PASS /0 fail/error/skip. Ignored JUnit:
  .runtime/be2-14-c4b2b2/component.xml. Eighteen expected warnings: six known
  Alembic offline deprecations and twelve intentionally malformed serializer outputs.
- Source-pinned selected BE2-12/foundation regression runner477 PASS:
  .runtime/learning-content-component/20261017-171027-983498.
- Targeted foundation application/review-regression/q00:114 PASS /0 skipped;
  .runtime/be2-14-c4b2b2/foundation.xml. Existing shared source unchanged.
- 15 lifecycle +10 activation +19 ledger +34 copy =78 PG cases collected only,
  NOT_RUN. Eight new SQL operation cases prepared. Runner pins new transitive
  operation fixture and frozen migration. No server/environment provisioned.
- Focused Ruff/format/Mypy, architecture/harness/security and whitespace checked
  before commit; normal formatting/import findings fixed without suppressions.
  No functional test failure in this checkpoint's backend runs; an initial patch
  context mismatch made no edit and was corrected before code.

## Remaining acceptance

Pending operation discovery/claims and actual dispatch/recovery, provider hook
adoption/idempotency, typed cancel acknowledgment/current lifecycle/receipt
verification/application, kill intent delivery, C5 safe binding/projections and C6
consolidation. Actual current-owner/source commit fencing, SQL atomicity/races and
provider cancellation/deletion remain unproven. No whole-card or original BE2-12
goal completion, actual cost/child-data exposure/BE1 closure, push/merge/deploy.

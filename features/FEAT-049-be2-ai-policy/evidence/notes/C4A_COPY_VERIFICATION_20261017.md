# C4a — scoped exact provider-copy receipt verification

2026-10-17 Asia/Saigon, feature/be2-08-14 parent e0f77b1. Approved P4;
plan/C4_COPY_LIFECYCLE.md before code. Prior turn committed guarded accounting:
progress. Read original attached goal again; later actual BE2-14 approval applies,
without marking original BE2-12/full goal complete or inheriting PG provisioning.

## Inspected and implemented

Foundation domain/provider_copy, application lifecycle service and ProviderCopy
ports/shared candidate report inspected. Reuse existing lifecycle/PurgeReceipt,
do not duplicate status transitions. Registry infrastructure is fake only; tuple
scope discovery lacks pages/coverage; hook has no operation key, cancel returns
None; receipt lacks org/scope/profile/action hash binding. Published source left
unchanged. Open CR in artifacts/CR_PROVIDER_COPY_ADOPTION.md, not cross-owner
adoption or permission to silently rewrite foundation.

Own reference-only command/grant/binding/receipt shapes, current authoritative
guard/verifier port and context-managed bridge. Exact actor/org/command/current
authority revision/copy kind+id/scope/profile version+hash/operation key binding;
strict native revalidation rejects booleans masquerading as typed values. Backend
verifier authenticates immutable receipt reference/hash/outcome, not caller flags.
Grant checked before/after verifier; revoked/expired/changed authority denied.
Return existing foundation PurgeReceipt under held guard, no registry mutation.

Fixture proof remains fixture, unverified deletion pending. Synthetic provider-kind
mapping test is NOT actual provider-deletion proof. Original profile provenance
must come from adopted registry, not latest alias. Real owner commit fence must
enforce deadlines: scope mutex/entry expiry check alone cannot prove eligibility
at future registry commit. No actual provider/BE1 adapter supplied or mounted.

## Executed checks

- 44 new component cases PASS: exact binding, wrong org/scope/profile/digest/hash,
  current/revoked/expired authority, malformed native grants/proofs, client extra
  authority fields, fixture/provider-kind mapping, pending/unsupported/exception,
  cancel-is-not-purge, private error sanitization, replay/current-rights and guard
  cleanup. Three expected serializer warnings from malformed native-model cases.
- All 14 own policy/accounting/copy contract+unit suites: 532 PASS /zero skipped;
  ignored JUnit .runtime/be2-14-c4a/component.xml. Four existing Alembic warnings
  plus existing allowed=1 negative-case warning recur, eight warnings total.
- Targeted foundation suites test_ai_job_application.py,
  test_ai_job_review_regressions.py, test_ai_job_q00_followups.py: 114 PASS. Includes
  same-key purge dispatch and stale-cancel-vs-purge regression cases.
- Existing source-pinned 477-case pack PASS, ignored receipt
  .runtime/learning-content-component/20261017-162806-940777.
- Focused Ruff/format (four files), Mypy (three source files) and repository
  architecture/harness/security/whitespace gates PASS before checkpoint commit.
  No new migration or published foundation file changed.

First Ruff run found import/long-line/format issues, corrected by normal formatter
without suppressions. Initial tests already passed; no acceptance weakened.
No PostgreSQL execution/provider call/install/server start. All 44 prepared actual
SQL cases remain NOT_RUN, not counted as component/runtime integration PASS.

## Remaining

C4b own durable registry/original profile metadata/pages/coverage and intent/replay
orchestration, current owner/expiry UoW fence, late-registration quarantine; typed
cancel/purge hook acknowledgment and missing-hook outcomes, verified durable
receipts, restart/race proof. Actual provider/foundation CR adoption and BE1/P4
wiring separate, not blocked whole-card work. C5 operations projections/binding
and consolidated full-card acceptance remain. No actual deletion, synchronous
cancel, overall BE1 closure, full goal/card DONE, push/merge/deploy claim.

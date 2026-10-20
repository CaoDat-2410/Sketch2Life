# C4c7 — atomic verified receipt resolution / consumer handoff

2026-10-18 Asia/Saigon, feature/be2-08-14 parent544f499. Original pasted goal,
AGENTS/current project context/source register, feature status/context/approval
and C4 subplan inspected. Later explicit BE2-14 revision1/P1–P5 approval governs
this card; original BE2-12 goal is not redefined or declared complete. Previous
turn was status-only; this continuation revalidated dirty checkpoint and verified
and completed it. No user changes discarded, no external activation/provisioning.

## Implemented

ProviderCopyReconciliationService.reconcile(actor, org, original command, key,
expected_delivery_revision, expected_copy_revision) holds exact receipt verifier
lease while own scope UPDATE transaction re-reads original operation, receipt-
available delivery/reference/hash and current lifecycle. Apply existing foundation
purge semantics or separate monotonic cancellation acknowledgment, then atomically
write current-copy CAS, immutable before/after/binding/proof/grant and audit/outbox.
Confirm current rights and proof deadline immediately before transaction exit.
No network/provider receipt lookup while holding own SQL scope lock.

Stable resolution key includes exact original envelope/delivery/reference and
proof outcome/verified/evidence kind/reason, not renewed grant/time/expiry. Exact
authorized retry produces no extra mutation and returns current state; changed
verification semantics require current-copy CAS. Unverified deletion stays pending;
fixture deletion never actual. Same receipt ID cannot silently change hash.
Confirmed cancellation/provider kind cannot downgrade; cancellation never deletes
copy or changes job/BE1 tables. Foundation/shared contract source is unchanged.

Forward ap_0009 adds two own tables. Append-only history and monotonic current
state triggers, strict historical reconstruction, current snapshot/history match
and original operation binding protect reads/restarts from malformed metadata.
Historical proof is not current permission. Guard exit failure after commit is
uncertainty, never invented rollback. Actual authority/deadline-at-commit adapter
adoption remains external; no default permissive production adapter supplied.

## Verification

- 20 new local cases PASS: fixture deletion/exact authorized replay, four
  nonterminal/unverified outcomes, cancel acknowledgment distinction, stale copy/
  delivery, failure rollback, precommit revocation, forged historical result/native
  proof, invalid lifecycle fields, pending-to-verified upgrade, monotonic provider-
  kind cancel classification, SQL insert/update writer shape and frozen DDL shape.
- Own895 contract/unit PASS, zero fail/error/skip:
  ignored .runtime/be2-14-c4c7/component.xml. Twenty-one known warnings: six
  Alembic offline deprecations and fifteen intentional malformed-model serializer
  warnings. No warning suppression or permissive conversion introduced.
- Selected source-pinned regression477 PASS:
  .runtime/learning-content-component/20261017-175401-100502.
- Targeted foundation114 PASS, .runtime/be2-14-c4c7/foundation.xml.
- PostgreSQL99 collected: lifecycle15, activation10, accounting19, copies55.
  Six new actual SQL cases prepared, NOT_RUN: restart/retry, cancel acknowledgment,
  immutable history update/delete, forced history failure and concurrent duplicate.
  No BE2-14 server started or actual provider proof obtained.
- Focused Ruff/format12 changed Python files and Mypy4 source files PASS;
  architecture/harness/security/whitespace checked before commit. Expanded format
  check found existing runner/test formatting and a long line; formatting corrected,
  runner15 tests rerun PASS. No functional failure in this continuation.

## Consumer and deferred external test package

Construct service with existing inventory store, exact operation receipt verifier
and trusted clock. Supply original caller/organization/command/key plus expected
delivery/copy revisions, not caller-provided proof or invented outcome. Missing
receipt/current authority or stale CAS must fail closed. A stored record or receipt
reference is not permission for a new provider call. Actual-only downstream checks
must inspect verified provider-kind evidence; a fixture status is not real proof.

Batch SQL command/preconditions/mutation scope/expected99 identities and return
artifacts: artifacts/C2_SQL_RUNTIME.md, using commit containing this note.
Runner --copies source-pins receipt fixture and transitives. Use only separately
authorized disposable synthetic PG17; runner creates/drops exact per-case DBs.
Do not run against production/shared DB or infer authorization to provision.
Owner may test provider/model/GPU separately on Lightning after real adapter
configuration; this SQL pack does not require GPU or prove those behaviors.

Remaining: kill delivery/current-copy conformance, C5 safe binding/projections,
C6 review and actual SQL/current-owner/provider adoption. Real BE1/P4 wiring left
to teammates per owner. No full-card/goal DONE, push/merge/deploy or live provider.

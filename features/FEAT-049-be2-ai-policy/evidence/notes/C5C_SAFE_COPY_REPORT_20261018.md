# C5c — guarded redacted copy report / consumer handoff

2026-10-18 Asia/Saigon, feature/be2-08-14 parent1d4d185. Prior continuation was
concrete code/test/commit progress. Original pasted goal/current clean branch/HEAD,
AGENTS/project context/source register, actual BE2-14 approval/current context and
approved P4/P5/AC08/09/11 inspected; subplan before code. No original BE2-12 goal
redefinition/completion, missing real-owner adoption remains separate.

## Implemented

ProviderCopyInventoryService.report(actor,org,CopyInventoryReadRequest) uses existing
exact BE1 data-request scope/purpose/expiry/current-read authority, including final
grant/deadline confirmation. Operations role alone is insufficient. Distinct read
digest binds projection/request; not a bearer grant. Scope SHARE transaction spans
page and each current lifecycle state, all same inventory revision. Existing SQL
reads validate current state against immutable resolution/original operation.

Pure project_copy_report validates native original/current registration equality,
org/scope, revision/coverage binding, bounded request length/order/cursor. Report
rejects oversized pages before state fanout. Existing <=256 keyset limit retained;
bounded per-item state reads are not measured runtime capacity/load evidence.

Field rationale / allowlist:

- org/scope/revision/purging: scoped snapshot metadata, not request permission.
- copy id/kind/current revision: link per-copy state without original profile/
  data-request/source/identity details. No raw reason/proof/authority/prompt/media.
- label/actual_deletion_proven: reuse foundation report_label and lifecycle rule;
  fixture_deleted_not_actual distinct from recorded verified provider deletion.
  Provider-kind synthetic tests prove classifier, never actual provider evidence.
- purge_receipt ref/hash and evidence_kind: opaque immutable backend metadata,
  no receipt bytes/provider URL/secret. Not permission for another purge/call.
- cancel_acknowledgment: not_confirmed, fixture_confirmed_not_actual or
  provider_confirmed_recorded, separate from purge or BE1/job closure.
- next_after: scoped raw keyset position; continuation requires same revision and
  current request guard, never an auth token. Final page not global completeness.
- inventory_coverage: stored scoped/revision-bound attestation only; explicitly
  stored_attestation_not_current_completeness. No fresh remote/expiry verification.
- overall_deletion always not_established. Empty rows, full stored coverage,
  receipt availability, cancellation or all labels on a page never close BE1.

No new SQL table/migration, shared foundation change, default app/route mount or
provider/network operation under DB lock. Historical report is not execution or
exposure authority. Actual trusted adapters/BE1 closure integration remain deferred.

## Verification

- 30 new local cases PASS: empty not-complete/no phantom, scoped pagination/stale
  revision/read-only/redaction, late purge quarantine, partial/full stored coverage,
  reconciled fixture purge/cancel distinctions, synthetic provider-kind classifier,
  denial before storage/final revocation, native flags/page/source mismatch, invalid
  request, oversized fanout rejection, duplicate/backward/stale/wrong-coverage
  pages, strict response preventing fake overall completion/fixture promotion.
- Initial focused24 PASS/1 FAIL: redaction assertion mistook static semantics word
  attestation for private attestation_ref field. Corrected exact private-field
  assertion and added explicit per-item field allowlist; production output unchanged.
  Normal formatter corrected initial long-line/import findings; no suppression.
- Own1010 unit/contract PASS, zero fail/error/skip:
  ignored .runtime/be2-14-c5c/component.xml. 23 known warnings: six offline Alembic
  deprecations and seventeen intentional malformed-model serializer warnings.
- Source-pinned selected regression477 PASS:
  .runtime/learning-content-component/20261017-180926-634915.
- Targeted foundation114 PASS: .runtime/be2-14-c5c/foundation.xml.
- Focused Ruff/format7 files, Mypy3 sources, architecture/harness/security/diff
  PASS before commit. Prepared actual PG104 collected:15 lifecycle/10 activation/
  21 accounting/58 copies. Three new report cases NOT_RUN; no server started.

## Consumer / next

Use existing inventory service's report method instead of exposing its raw page
registration DTO. Supply verified caller/org and strict exact data_request_ref/
scope_ref/limit; continue using returned next_after and revision as expected_revision.
Always reauthorize, including replays. Preserve coverage/overall/fixture labels.
Opaque receipt references require adopted backend verification port to resolve;
never forward provider credentials/bytes or accept client verified flags. Owner
BE1 alone decides overall request closure with actual evidence and completeness.

Consolidated external SQL commands/preconditions/impact/return artifacts remain
artifacts/C2_SQL_RUNTIME.md, commit containing this note; copies58/all104 exact
inventories. No piecemeal external test required now. Next C6 full acceptance audit,
remaining conformance and consolidated runtime/owner handoff. Stop-generation CR,
real owner/provider/SQL adoption gates open; no full-card/goal DONE/push/merge/deploy.

# C4b2b1 — inventory authority/source history

2026-10-18 Asia/Saigon, feature/be2-08-14, parent c3710e8. Read original attached
goal and actual later BE2-14 approval; original BE2-12 full goal is not declared
complete. Prior goal turn was status-only/no progress; current turn implements
the next available approved local work, not provider integration or provisioning.
C4 subplan extended before code; frozen revision-1 plan/approval unchanged.

## Changes and boundaries

Strict historical evidence DTO, same-UoW application recording, append-only SQL
table/trigger in forward ap_0005 and strict native/JSON binding codec. Prior
ap_0004/foundation source unchanged. Retain exact source/profile/data-request/
authority proofs; no historical proof may be reused as current dispatch grant.
Exact mutation replay stores new observations without duplicate mutation events.
Reads remain read-only; no action/router/default owner adapter introduced.

28 new history cases cover exact body reconstruction, immutable migration shape,
codec column substitution/hash forgery/native bool rejection, transaction actor/
scope/read-only checks, retry/revocation, coverage, and evidence+inventory rollback.
Five new actual PG cases prepared: reconnect, update/delete rejection, forced
evidence insert failure and isolated migration roundtrip. PG remains NOT_RUN,
not passed from schema compilation or memory rollback tests.

## Verification

- 645 own contract/unit PASS, 0 failure/error/skip. Ignored raw JUnit:
  .runtime/be2-14-c4b2b1/component.xml. Fifteen warnings: six known Alembic
  path_separator deprecations and nine intentional malformed-model serializers.
- Existing source-pinned component runner PASS: 477 selected BE2-12/foundation
  cases; .runtime/learning-content-component/20261017-170243-766645.
- Targeted foundation application/review-regression/q00: 114 PASS, 0 skipped;
  .runtime/be2-14-c4b2b1/foundation.xml. No shared source rewrites.
- Collection: lifecycle15 +activation10 +ledger19 +copy26 =70 actual PG cases
  prepared NOT_RUN; no DB server installed/started or external call.
- Focused Ruff/Mypy, architecture, harness, security and whitespace checked before
  checkpoint commit. Repository validators remain unchanged.

First test invocation from repo root failed collection because fixture imports
require backend cwd; corrected invocation, no package/path workaround. Initial
focused backend run had82 PASS/one FAIL because synthetic expiry clock omitted
the newly added observation timestamp; updated its sequence to expire at the
same final proof check. All denial/rollback assertions retained. Lint/format
findings fixed normally; no validator suppression or reduced inventory.

## Open

Exact operation envelope/intents/recovery and operation evidence history,
typed provider dispatch/ack and current lifecycle/verified receipt application,
kill intent delivery, C5 safe composition/projections, real PostgreSQL runtime,
owner/provider adoption and consolidated acceptance. No actual deletion/cost/
provider cancellation/BE1 closure, no full-card or full-goal DONE, no push/merge.

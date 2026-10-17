# C4c2 — delivery state, typed responses and own SQL persistence code

2026-10-18 Asia/Saigon, feature/be2-08-14 parent f2afc7e. Prior goal turn made
progress via C4c1 commit; re-read original attached goal/current context/approval/
plan/source register and clean HEAD. Later actual BE2-14 P1–P5 approval remains
applicable; original BE2-12 goal is not completed or redefined. C4 subplan written
before code, extended before persistence; frozen plan/approval/foundation unchanged.

## Changes

Separate pure delivery state machine, expected-revision/token/deadline fences,
claim-start time, used-token history, exact replay and unsupported/receipt no-auto-
redispatch. Typed hook protocol and strict native response bridge bind exact
operation key/body digest with references only. No transport success is reported
as cancellation/deletion. Own ap_0007 current snapshot/history plus scope-UoW
CAS/outbox code and strict codec, immutable history/current-key/revision triggers.
No current-authority adapter, worker loop, hook call or provider effect.

## Verification

- 56 pure delivery/contract/bridge tests PASS: exact claim/retry, busy, expired
  takeover/stale response, token reuse, input native validation, bad snapshots,
  deadline/predating response, immutable terminal metadata, false hook deletion/
  cancellation outcomes and spare client assertions/reference requirements.
- 22 offline delivery storage tests PASS: strict codec roundtrip/negatives, same-
  transaction SQL state/history/event shape, no-op replay/CAS miss, snapshot/row/
  original binding, missing operation, read-only mutation, frozen DDL/trigger shape.
- All own local contract/unit suites786 PASS, zero failure/error/skip. Raw ignored
  JUnit .runtime/be2-14-c4c2/component.xml. Eighteen existing known warnings retained.
- Source-pinned selected BE2-12/foundation477 PASS:
  .runtime/learning-content-component/20261017-172557-573938.
- Targeted foundation application/review-regression/q00:114 PASS /zero skip;
  .runtime/be2-14-c4c2/foundation.xml. No shared source rewrite.
- Actual SQL collected: lifecycle15 +activation10 +ledger19 +copy42 =86 cases,
  six new delivery PG cases prepared NOT_RUN. No service installed/started/called.
- Focused Ruff/format on13 files, Mypy7 source files, architecture/harness/security
  and whitespace PASS before commit. Normal line/import/nested-condition findings
  fixed without suppressed rules. No backend functional test failure in this turn.

## Open

Guarded claim/deadline/retry-authority composition and pending filter, hook dispatch
outside DB lock, response application with current guard, typed cancel confirmation,
verified purge receipt/current lifecycle, late-result/restart/conformance, kill
delivery, C5 safe wiring/projections and C6 acceptance. No SQL atomicity proof from
offline shape, no provider dedup/actual deletion/cost/closure/full-card or goal DONE.
Consumer obligations in artifacts/C4C2_DELIVERY_STATE_HANDOFF.md. No push/merge.

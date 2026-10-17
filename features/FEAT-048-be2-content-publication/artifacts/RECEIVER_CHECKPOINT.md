# BE2-12 receiver checkpoint — candidate handoff, NOT integrated DONE

Current handoff entrypoint, 2026-10-17. Receiver owns BE2-08–14; sender owns 01–07.
Work branch feature/be2-08-14 (user-requested local rename; scope still BE2-12).
No push/merge/deploy authorized
or performed. This checkpoint is usable for teammate integration, not a claim
that all original BE2-12 acceptance or external adoption is complete.

## Delivered component surface

- Versioned content lifecycle, separate capabilities, exact shared DATA-24 safety/
  pedagogical reviews, fresh approvals after edit and safe terminal-version handling.
- Immutable own PostgreSQL schema/migration, atomic state/proof/receipt/event/outbox,
  record/review CAS, duplicate recovery, real SQL races/rollback/restart evidence.
- Current default/exact published resolution and derived stale-review history.
- Fixed CMD-48 four-branch routing, concrete strict model/typed handler binding,
  unavailable slots and one candidate HTTP factory. Routing selector is NOT the
  final complete preset/policy semantic payload schema union.
- Typed published-reference/query/notice/ack ports, outbox metadata projection,
  consumer conformance and actual HTTP/SQL producer test. No fake delivery ack.
- Owned one-event send/ACK service with exact PostgreSQL NOWAIT outbox lock,
  strict matched ACK, pending on failure, restart/no-op and lost-ACK replay proof.
  See OUTBOX_DELIVERY.md; real fixed logical sink/transport adoption remains open.
- API/schema/authority rationale, original AC01–14 audit and explicit remaining gates.

## One command: selected component handoff checks

From repository root with the existing backend virtualenv:

```powershell
./backend/.venv/Scripts/python.exe features/FEAT-048-be2-content-publication/src/run_component_checks.py
if ($LASTEXITCODE -ne 0) { throw 'Component handoff pack did not pass' }
```

The runner collects an exact 16-file/477-case selected inventory (367 feature +
110 foundation regressions), compares full JUnit identities, rejects missing,
skipped, duplicate, unexpected or failed cases, and pins source before/after.
It then runs focused BE2-12 Ruff/Mypy plus architecture/harness/security/whitespace.
Ruff uses backend working directory/config, not another root's import ordering.
Foundation regression tests run but their source is NOT changed/linted under this
card. Mypy covers 16 owned production files. Source pin covers 333 files at this
checkpoint, including transitive backend Python source, migrations and fixtures.

Exit 0 = selected component pack PASS; 1 = FAIL; 2 = NOT_RUN. Missing existing
pytest/ruff/mypy never triggers installation. Logs/JUnit/summary go to ignored
.runtime/learning-content-component/<timestamp>. Summary explicitly says SQL
not run by this pack, real owner integration NOT_RUN and full_goal_complete=false.
Do not replace those fields with DONE based on a green component receipt.

## PostgreSQL pack: separate authority and evidence

Existing approved portable controller runs C2 9 + projection 1 + command/history/
HTTP-consumer/delivery 23 = 33 SQL cases. The component runner does NOT start a service,
download PostgreSQL, use network, install anything or merge/push.

```powershell
$pythonPath = (Resolve-Path ./backend/.venv/Scripts/python.exe).Path
$runtimeParent = [IO.Path]::GetFullPath((Join-Path (Get-Location) '.runtime/pg-test'))
& ./features/FEAT-048-be2-content-publication/src/run_local_pg_c2.ps1 `
  -RuntimeParent $runtimeParent -Python $pythonPath `
  -IncludeC3Projection -IncludeC3Commands
if ($LASTEXITCODE -ne 0) { throw 'Authorized SQL pack incomplete or failed' }
```

Only use an explicitly authorized isolated synthetic profile; do not migrate a
shared/production DB or reuse deleted passwords. Portable controller downloads
official archive, binds loopback, uses disposable DBs, stops/removes its runtime.
Latest actual SQL receipt is C4d's 33 PASS, ASSUMED authority ports, no skip.
New producer delivery SQL covers actual acknowledgement, invalid/lost ACK, NOWAIT
concurrency and transactional rollback. Durable synthetic receiver is NOT a real
BE1/P4 implementation. Compare pinned dependency hashes before carrying proof forward.

## Teammate reads/wires next

1. GOVERNANCE_BINDING_HANDOFF.md: fixed dispatcher/model binding, not a second
   router or foreign table shortcut. Receiver's separately planned 13/14 define
   their semantic payloads/handlers; BE1-15 owns non-AI policy behavior.
2. CONTENT_CONSUMER_HANDOFF.md: reference metadata is not a grant. BE1/P4 binds
   real authority/source/review and session-start commit consistency, plus trusted
   durable consumer/ack/dedup. Never infer permission from a cached notice/pin.
3. REVIEW_HISTORY_CANDIDATE.md and REINTRODUCTION_RULE.md: originals/pinned history
   preserved; stale reasons and fresh-version review are explicit.
4. ACCEPTANCE_AUDIT_20261017.md: follow-up notes supersede historical absence
   findings, but external owner adoption/full semantic schemas/real delivery and
   integrated closure remain unachieved. Default app still does not mount candidate
   route. No production identity or fake successful adapter supplied.

Sender 01–07 can consume this checkpoint's ports/examples without waiting for
all receiver business tasks; candidate/assumed boundaries stay labelled. Whole
goal cannot be marked complete until the original integrated gates are proven.
Starting another card needs its own plan/approval; no BE2-14 implementation is
silently activated by this handoff or component PASS.

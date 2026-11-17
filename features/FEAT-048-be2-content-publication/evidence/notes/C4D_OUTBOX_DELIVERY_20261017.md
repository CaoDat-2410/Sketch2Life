# C4d — real owned producer send/ACK, not owner integration

Date: 2026-10-17, Asia/Saigon. Parent b358bc7; branch feature/be2-08-14,
renamed at owner's request without rewriting history. Existing plan revision 1,
P1–P4 approval applies; owner explicitly requested continuing BE2-12. No other
business card activated. Executor self-review, not independent owner sign-off.

## Change and acceptance

Preimplementation acceptance: artifacts/OUTBOX_DELIVERY.md. New application
ContentNoticeDelivery and own SqlContentDeliveryStore implement one-event send
under scoped row lock. Valid strict ACK must match event/org/configured consumer.
Only actual successful transaction commit returns delivered. Already delivered
does not send again; concurrent lock returns busy before sink invocation. Wrong
scope/payload/ACK, sink exception, marker/commit failure keep pending. Receiver
acceptance followed by lost ACK may replay; no exactly-once claim.

No schema/migration/shared contract/body changes, foreign-table access, production
auth, default route mounting, scheduler, retry budget, consumer choice or timeout
default supplied. Existing one-marker model requires ONE fixed logical sink;
separate independent consumers/fanout cannot share this delivered_at as their
individual receipt. Trusted sink must bound transport and durably deduplicate.

## Actual local component run

Command from repo root:

```powershell
./backend/.venv/Scripts/python.exe features/FEAT-048-be2-content-publication/src/run_component_checks.py
```

Receipt: .runtime/learning-content-component/20261017-080356-971377/summary.json,
junit.xml, pytest.log and individual check logs. Exact 16-file / 477-case selected
inventory PASS, 0 skipped, 4.71s; 367 feature + 110 unchanged foundation regressions.
23 new unit cases. 333 source hashes unchanged. Focused Ruff PASS, strict Mypy 16
production files PASS, architecture/harness/security/diff checks all exit 0.
Additional focused Ruff over updated integration test and SQL runner PASS before
commit. Raw outputs remain ignored, not committed.

## Actual PostgreSQL 17.11 run

Existing authorized portable controller, existing backend Python, explicit
D:/Codex/Sketch2Life/.runtime/pg-test runtime parent, both IncludeC3 switches.
Official archive SHA256 80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f.
Restricted disposable test databases, loopback 127.0.0.1:60435, no Windows service.

- C2: .runtime/learning-content-c2/20261017-080513-227571 — 9 PASS.
- Projection: .runtime/local-pg-c2/lc-pg-2de5e29b738b4759ba5c29b83e588f4f/
  c3-projection-junit.xml — 1 PASS / 1.20s.
- Commands/history/HTTP/producer delivery:
  .runtime/learning-content-c3b/20261017-080525-302198 — 23 PASS / 16.25s,
  24 dependency hashes unchanged. Nine new PostgreSQL cases.
- Total 33 PASS, no failure/skip; controller exit 0. Existing Alembic
  path_separator deprecation warnings retained, not hidden as acceptance.
- Producer delivery proves restart/no resend, malformed/mismatched ACK and sink
  exception pending, simultaneous send exclusion, wrong organization/payload,
  actual SQL division-by-zero after marker update rolls back. Separate SQLite
  durable synthetic receiver commits, loses ACK, reopens and returns duplicate;
  producer finishes once without another receiver record.

Authority/review fixtures remain ASSUMED. Synthetic receiver is NOT BE1/P4 durable
consumer integration. Previously pure-projection test still leaves its own rows
pending intentionally; new delivery tests legitimately commit delivered_at.

Portable controller stopped server and deleted exact private cluster/passwords/
archive/binaries root lc-pg-2de5e29b738b4759ba5c29b83e588f4f. Subsequent Test-Path
returned False. Safe logs/environment/JUnit retained under ignored repo runtime.
No GPU/cloud/provider, dependency install, push, merge or deploy.

## Remaining gate, not waived

F04 local producer implementation is now present; real fixed sink binding,
transport authentication/timeout, owner durable dedup/audit/session effects and
integration remain NOT_RUN. F01 final owner-specific preset/policy semantics,
F02 real current authority/source/review fencing, default app composition and
F05 integrated closure still need actual adopted contracts. Full BE2-12 NOT DONE.

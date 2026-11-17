# C4c typed consumer pack and owned HTTP/SQL producer proof — 2026-10-17

Parent 9dd904b, feature/be2-12-content-publication. Approved H-CONTENT-PRESET/
P3/P4 scope. Receiver 08–14 clarified; no other business card implemented.
Executor self-review, not BE1/P4 owner sign-off.

## Deliverables

Strict 0.1-candidate ContentReferenceQuery/PublishedContentReference/Lifecycle
Payload/Notice/Ack contracts. Existing outbox metadata shape is checked against
closed action/state combinations; no extra secret/body fields. Consumer query
port implemented over current ContentEligibility; no cached ref/notice/receipt
substitutes for current scope/source/policy/reviews. Pure notice_from_outbox
adapter checks expected org; it neither reads nor acknowledges/delivers rows.
Typed sink protocol documents durable scoped idempotency/body conflict/ack and
trusted transport obligations without inventing BE1 effects or runtime policy.

See artifacts/CONTENT_CONSUMER_HANDOFF.md: integration sequence, exact pins,
immutable history, delayed publication, producer authentication, lost ack and
session-start consistency limits. No new HTTP delivery gateway or foreign writes.

## Actual verification

- contract/test_content_consumers.py: 25 PASS. Synthetic sink explicitly labelled
  memory-only: duplicate/body conflict, delayed publication cannot restore retired
  exact version, pinned history unchanged. Query cases deny current review/source/
  READ/policy withdrawal and recall; strict scope/hash/ref/notice validation.
- Combined selected local feature/foundation suite: **438 PASS / 0 skip, 4.07s**
  (328 feature + 110 foundation), not the whole repository suite.
- Focused Ruff and strict Mypy three new source files PASS. Initial import/line
  formatting findings fixed before final checks; no functional failure relabelled.
- Actual portable PostgreSQL 17.11: C2 **9 PASS, 6.46s**; projection **1 PASS,
  1.08s**; expanded commands/history/HTTP-consumer **14 PASS, 9.39s**; no skip.
- New SQL case uses actual FastAPI route/client, SQL lifecycle/shared reviews,
  authoritative query projection and typed notice conversion from six real outbox
  rows. Recall denies new resolution; notice exact reference matches pinned hash.
- Owner identity/guard still injected ASSUMED ports. No real owner/transport
  authentication, durable sink, BE1 effects or session-start transaction proof.
- All six SQL outbox rows delivered_at=NULL, intentionally proving no delivery
  claim. Memory sink is not used to mark SQL rows delivered.
- Runner pins 22 source files before/after, unchanged true. Existing Alembic
  path_separator warnings: 11 + 1 + 14, not hidden.

## Raw receipts and scope binding

- .runtime/learning-content-c2/20261017-074101-672684/
- .runtime/learning-content-c3b/20261017-074113-415001/
- .runtime/local-pg-c2/lc-pg-fafd6b4558354681851213664ced0748/

Changed producer-contract source SHA256:

- application/content_consumer_queries.py:
  20e91f351490d2ca55b7ad2930df3fc257a937bff7457fab2f88380a45b55338
- application/ports/content_consumers.py:
  0aeab0713e7be17a1877ffb8c22cb160c6c1a7a0eedd3cfcc5dbd752ed7bc2c4
- contracts/schemas/content_consumers.py:
  338894c801c5b690f75e131e34dc638f585b0034eb7f28039dc543e35a4aa7a8
- tests/integration/learning_content/test_commands_sql.py:
  1b49822435c5a32714977e873e986374a58fed4c17363b0f38ce931d27972a5d
- feature src/run_c3_commands_sql.py:
  9bd7a1c6e77d06648489be9473a4ef69756fa5064efb714e3a32a96b010bdd1a

## Cleanup and remaining acceptance

Official ZIP hash matched approved portable runtime; loopback 127.0.0.1:52413,
random private credentials/disposable DBs. Server stopped, exact UUID directory
removed including cluster/passwords/binaries/ZIP; read-only checks confirm absent
directory and no listener. Logs retained privately. No unrelated files deleted;
no system service/GPU/model/package install/push/merge/deployment.

Receiver-owned consumer contract/conformance pack is supplied. Real owner payload
schema/handler/authority/source/review/sink/session-commit adoption and integrated
acceptance remain separate; full BE2-12 not marked DONE from these tests.

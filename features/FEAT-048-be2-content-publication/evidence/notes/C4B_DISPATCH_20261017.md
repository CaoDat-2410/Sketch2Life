# C4b fixed dispatcher and typed validation adapter — 2026-10-17

Parent 566dade; branch feature/be2-12-content-publication. Approved revision 1
CMD-48 seam plus user's receiver-08–14/sender-01–07 clarification. No BE2-13/14
business implementation or new authority adopted. Executor self-review.

## Implementation

New governance routing/result candidate contracts and application dispatcher.
Fixed content/preset/policy-ai/policy-core routes, eight known actions; no unknown
registry. Selector validates routing only. Bound owner adapter validates full
concrete frozen strict extra-forbid model, checks shared envelope/target/reason/
review-set before effectful handler, and checks typed response scope/target.
Handler receives typed model and verified principal/org/precondition, not a
passthrough dictionary. Missing owner is explicit unavailable, never content
fallback. Current capability/policy/transaction/receipt belongs to owner handler.
Response validation is not a cross-owner transaction rollback guarantee.

Existing HTTP factory now delegates to one governance factory; safe parsing,
identity injection, body bound, precondition and error semantics retained.
Known unavailable branch returns 503; unknown kind/policy/action or invalid bound
payload returns 422. Bound owner models included in finite inline OpenAPI.
Compatibility content factory creates same route; do not mount both factories.
No default app registration or new delivery route. No owner SQL writes.

## Actual checks

- Dispatcher tests 50 PASS; HTTP integration seam tests 9 PASS (59 new cases).
- All 24 owner branch/action combinations use exactly one typed handler with
  separate verified scope/precondition and zero content-store side effects.
- Invalid branch/action/shared target/full bound fields never reach owner; missing
  binding never writes; wrong model/response scope denied; safe HTTP errors and
  one-path inline schema checked. Fixture owner payloads are minimal/synthetic,
  NOT actual preset rules/AI/core policy adoption or authority proof.
- Combined selected local feature/foundation suite: **413 PASS / 0 skip, 4.34s**.
- Focused Ruff and strict Mypy 3 new/changed source files PASS. Initial generic
  syntax/import/line-length findings fixed before final checks; no functional
  test failure relabelled PASS.
- Repository architecture/harness/security and whitespace checks before commit.

No storage/domain/migration changes in this checkpoint; no repeated PostgreSQL
download/test claimed. Prior 23 SQL results remain historical source-bound owned
storage/application evidence, not C4b real-owner integration proof.

## Remaining

Complete semantic owner command schemas/handlers and real BE1 authority/source/
review/consumer adapters still need adoption. Fixed routing and concrete typed
binding are not falsely reported as the final complete semantic schema union.
Candidate dispatch can be handed off and receiver-owned work can proceed without
waiting for full other-card implementations. Entire goal remains incomplete;
no push/merge/deploy, new card implementation or model/provider activation.

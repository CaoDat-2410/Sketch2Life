# BE2-08 acceptance audit —2026-10-18

Current C4b parent c7b17ac; self-audit, no external owner integration sign-off.
Reviewed plan revision1 unchanged. Status IN_PROGRESS, full_card_complete=false.

| Criterion | Current owned evidence | Still required for full acceptance |
|---|---|---|
| A1 strict/current eligibility | Strict CMD-40/pin/native DTO, create lease and strategy adversarial fixture tests | Actual07 bundle bytes and BE1 current consent/session/audience/source/profile/rights authority held through commit |
| A2 atomic dedup/no orphan | Owned domain/create/idempotency/row CAS tests;11 actual isolated PostgreSQL cases PASS (E09) | Adopted foundation same-UoW/recovery bridge, concurrent submission/start/completion and failure/restart tests (CR08-01); own SQL does not prove job atomicity |
| A3 reviewed-library lineage | Explicit library strategy independent of model; exact catalog/rights/profile tests and ready_for_review only | Actual published/recall/rights resolver/current guards and final-session09 consumer adoption |
| A4 actual generation | Injected generator/composer + bounded media/report validation; actual tiny synthetic GIF fixture decoding only | Approved selected provider/profile/runtime; generated video fully decoded and checked; quality/rights evidence. NOT_RUN |
| A5 no unsafe late exposure | Worker/receipt/lost stage+final ACK/current-boundary adversarial cases; closed outcomes | Actual attempt/retry/cancel/stop-generation epoch/deadline and private staging/journal/atomic completion; race protection for accepted refs vs cleanup |
| A6 exact copy lifecycle | Strict original-copy producer, scoped14 hook, stable original key/profile and truthful Pending/Unsupported/receipt references | Actual copy bootstrap/source registration, completeness, durable external dedup, supported operations and authenticated separate14 cancellation/deletion verification |
| A7 separated reproducible tests | Source/node-pinned local runner, explicit mock-vs-fixture labels; separate actual own SQL11 PASS with scoped receipts/cleanup | Selected decoder/provider/adopted integration packs; own SQL never replaces those gates |
| A8 handoff/integration | Frozen approval, dependency register/CR, worker/copy/local/runtime handoffs and this audit | Actual07/BE1/foundation/14/09 adoption and owner acceptance of A1–A7, not implied by deferral |

## Current implementation boundary

P1 pure/DTO and P2/P3 local surfaces available. P4 local runner, authored decoder
fixture pack and audit/handoff available; actual own SQL11 PASS. Production-decoder/
adopter evidence remains open. P5 actual generation not activated. No production default
identity, durable job bridge, storage journal, provider endpoint/model/profile,
Teacher approval/playback or deploy added. Existing12/14 evidence remains theirs,
not08 completion. Real BE1/P4 wiring remains teammate-deferred, not waived.

## Concrete outstanding groups (not7 completed cards)

Own SQL group completed:11 PASS with separate approval; no foundation atomicity
inferred. Four remaining acceptance groups:

1. Adopt exact07/current BE1/14 authority and foundation submission/start/completion
   + private staging/recovery/accepted-reference cleanup protection; real race tests.
2. Adopt actual copy journal/discovery/14 registry bootstrap and original source
   completeness + per-copy control/dedup/authenticated receipt verification.
3. Select/approve provider, rights/profile/encoding/decoder and test budget; run
   actual decoder/generation/error/cancel/restart/late-result batch and quality review.
4. Obtain09/consumer/owner acceptance and update audit only against actual evidence.

Groups1/2/4 include delegated cross-owner integration; owner has not asked this
agent to implement teammates' missing adapters. Group3 requires explicit runtime
decisions. This list is acceptance work, not an inferred new backlog/task allocation.
P4 local proof can be handed off while these remain; full08 cannot be marked DONE.

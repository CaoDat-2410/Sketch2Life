# FEAT-049 — BE2-14 AI policy / limits / kill switch

- Goal: full BE2-14 card, including ProviderCopyLifecycle and redacted projections.
- Latest C4b2a: current-owner inventory service composes register/read/coverage/
  fence with authenticated reference-only source proofs and own UoW, rechecks
  unchanged rights/deadlines before exit. Shared own grant validator reused by
  C4a. 56 new cases, 617 own +477 regression +114 targeted foundation PASS.
  Two new copy SQL service cases prepared (65 all PG NOT_RUN). Boundary remains
  ASSUMED; no durable source-proof history/operation dispatch or actual deletion.
- Latest C4b1: own copy inventory SQL/UoW/forward ap_0004; immutable original
  profile registration, monotonic purge fence/late quarantine, revision-bound pages,
  scoped source coverage reports and audit/outbox. 27 new offline/codec/shape +2
  runner cases, 561 own component PASS. 19 copy PG cases prepared NOT_RUN (63 total).
  Inventory/initial metadata and reported_complete are not current lifecycle,
  verified provider completeness, dispatch/deletion or BE1 closure. Guard/intent/
  acknowledgment/receipt orchestration remain C4b2/C4c; old foundation unchanged.
- Latest C4a: exact current-authority/profile/operation/receipt verification bridge
  to existing foundation PurgeReceipt/state machine; no duplicate lifecycle or
  published foundation changes. 44 new tests, 532 own component +477 regression
  +114 targeted foundation application/regression cases PASS. No dispatch, registry
  mutation or actual deletion proof. Open CR documents durable pagination/coverage,
  original profile provenance, operation key/cancel acknowledgment/commit-fence gaps.
- Latest C3c3c: ResourceAccountingService composes held current-use lease,
  authoritative quote/evidence guard and own ledger UoW. Stable original-pin/attempt
  reservation id, native proof revalidation, current-rights/evidence replay and
  cleanup after stop without new use permission. 49 new tests, 488 own component
  PASS; actual PG inventory 44 (19 ledger), NOT_RUN. No actual owner/evidence adapter
  mounted; snapshots are not dispatch grants. C4/C5/full-card acceptance still open.
- Latest C3c3b: own five-table resource ledger, serialized org/feature lock,
  reservation/counters/receipt/audit intent UoW and forward ap_0003. Composite
  feature-scoped FKs, immutable terminal provenance and pending audit/outbox.
  439 own component PASS; 17 new actual PG ledger cases prepared NOT_RUN
  (42 total PG). Current-use/quote/proof application composition still pending;
  persistence code is not runtime capacity enforcement proof or execution authority.
- Latest C3c3a: pure accounting transitions and exact trusted quote/evidence
  contracts/ports. Per-budget-bucket held/spent and global org/feature slots;
  idempotent settlement preserves original terms, verified actual overrun retained.
  81 new cases, 417 own component +477 existing regression PASS. No atomic ledger
  SQL/service or real quote/evidence adapter yet; AC06 remains open.
- Latest C3c2: exact request/policy/profile pin and held current-use leases at
  create/dispatch/retry/completion/exposure. Verified origin activation history
  prevents pin epoch forgery; stop history denies old pin even after reactivation.
  53 new tests, 336 own component PASS; 15+10 SQL cases prepared, NOT_RUN.
  No numeric budget/concurrency or provider permission implied by a lease snapshot.
- Latest C3c1: internal emergency stop with current DISABLE, scope epoch CAS and
  atomic intent/receipt, including known feature before first policy publication.
  31 new tests, 283 own component PASS; old replay cannot disable a newer pin.
  15+7 actual SQL cases prepared/collected, still NOT_RUN; no provider stopped claim.
- Current C3b: all eight application handlers, guarded receipt/replay, exact
  reviews and atomic effective scope publish/disable; forward migration ap_0002.
  252 own component PASS +477 existing regression PASS; 15+4 actual SQL cases
  prepared, still NOT_RUN. Registry/review/transaction memory fixtures assumed.
  No C3c atomic budget/emergency kill/provider completion claims from this work.
- Current C3a: server-side exact-definition compatibility validator and candidate
  authoritative registry guard implemented. 59 new fixture cases, 219 own component
  PASS plus 477 existing regression PASS. No activation/usage grant from validation,
  no production registry/current-authority adapter or durable fence proof supplied.
- Status: IN_PROGRESS; owner approved revision 1/P1–P5 by direct reply "duyệt".
- Owner: receiver BE2-08–14, same branch feature/be2-08-14.
- Baseline: f0ff7a840d1910f1f80df327c3fd0239db5ea8e1; working tree clean before planning.
- User request: "tiếp tục task tiếp", following explicit BE2-14 next-task proposal.
  Initially preparation only; subsequent "duyệt" approves pinned revision 1/P1–P5.
- BE2-12 component handoff available, integration deferred to teammates. Do not
  redefine that task's full acceptance as done or reopen BE1/P4 wiring now.
- Sources: SRS3.1 UC-036/037/038, DATA33/25/35, CMD48, FEAT040 BE2-14;
  FEAT044 receiver handoff/roadmap/tracker; ADR0015/0018; FEAT048 dispatcher.
- Dependencies: BE2-01 existing candidate job/fence/provider-copy support and
  BE2-12 strict delegate binding; real owner auth/consent and provider hooks absent.
- Non-goals: provider choice/inference/deploy, BE1/session/job table writes,
  frontend, generic admin platform, preset/video business logic.
- Risks: published foundation compatibility, budget-window semantics and trusted
  receipt verification. P1–P5 approved for this card, not adopted production values
  or another owner's contracts. Shared DATA-24/foundation left unchanged.
- C1: exact AI-policy review target, strict action fields, reference-only allowlist,
  mandatory true gates and stdlib immutable lifecycle. 124 component PASS; existing
  regression pack 477 PASS; no SQL/runtime activation or complete services yet.
- C2 code now includes own lifecycle SQL UoW/six-table metadata/frozen independent
  migration and additive Alembic registration. 36 new offline/runner tests PASS,
  160 BE2-14 component cases total; 15 actual PostgreSQL cases prepared/collected,
  NOT_RUN pending separately authorized environment. No server started/downloaded.
  Effective scope/epoch/reservation tables deferred to C3 when their behavior exists.
- Next: C4b2b durable exact operation envelopes/intents and immutable authority/
  evidence history, then C4c dispatch/acknowledgment/verified receipt and remaining C5
  safe binding/projections; real foundation/provider CR adoption separate;
  actual SQL/accounting race proof and real owner/provider adoption still separate;
  existing actual SQL pack still pending authority/proof;
  real production
  activation/provisioning and external adoption remain separate gates.

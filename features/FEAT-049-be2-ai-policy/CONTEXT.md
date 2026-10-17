# FEAT-049 — BE2-14 AI policy / limits / kill switch

- Goal: full BE2-14 card, including ProviderCopyLifecycle and redacted projections.
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
- Next: actual SQL pack authority/proof and C3c2 accounting/current-use eligibility;
  real production
  activation/provisioning and external adoption remain separate gates.

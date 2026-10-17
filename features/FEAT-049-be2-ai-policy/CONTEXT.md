# FEAT-049 — BE2-14 AI policy / limits / kill switch

- Goal: full BE2-14 card, including ProviderCopyLifecycle and redacted projections.
- Status: AWAITING_APPROVAL; implementation NOT_STARTED.
- Owner: receiver BE2-08–14, same branch feature/be2-08-14.
- Baseline: f0ff7a840d1910f1f80df327c3fd0239db5ea8e1; working tree clean before planning.
- User request: "tiếp tục task tiếp", following explicit BE2-14 next-task proposal.
  Authorizes preparation; repository gate still requires reviewable plan approval.
- BE2-12 component handoff available, integration deferred to teammates. Do not
  redefine that task's full acceptance as done or reopen BE1/P4 wiring now.
- Sources: SRS3.1 UC-036/037/038, DATA33/25/35, CMD48, FEAT040 BE2-14;
  FEAT044 receiver handoff/roadmap/tracker; ADR0015/0018; FEAT048 dispatcher.
- Dependencies: BE2-01 existing candidate job/fence/provider-copy support and
  BE2-12 strict delegate binding; real owner auth/consent and provider hooks absent.
- Non-goals: provider choice/inference/deploy, BE1/session/job table writes,
  frontend, generic admin platform, preset/video business logic.
- Risks: published foundation compatibility, policy review target not learning
  content, budget-window semantics and trusted receipt verification. Proposed
  decisions P1–P5 in plan, not adopted policy or real integration proof.
- Next gate: owner approval plan revision 1; no production code/test changes yet.

# FEAT-049 — BE2-14 AI policy / limits / kill switch

- Goal: full BE2-14 card, including ProviderCopyLifecycle and redacted projections.
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
- Next: C2 persistence under existing approved plan; real production
  activation/provisioning and external adoption remain separate gates.

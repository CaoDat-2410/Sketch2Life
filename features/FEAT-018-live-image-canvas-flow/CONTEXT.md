# FEAT-018 live image and canvas context

- Status: P1 complete; isolated P2-T1 D2 reviewed and accepted; D3-R2 Cohorts A and B formally
  executed, independently verified and owner-approved; D3/P2-T1 closed for offline Cohort A+B;
  downstream scopes remain pending
- Plan revision: 2 with approved P2-T1 D2 and D3-R2 addenda
- Owner: shared integration allocation pending contract freeze approval
- Goal: run a non-sensitive real JPG/PNG through validation, backend-only Qwen3-VL understanding, Gate A, one-anchor/one-objective ExperienceSpec compilation, P1/Gate B, PixiJS canvas, P4 cache/fallback, off-screen handoff, gallery journey and feedback.
- Data policy: non-sensitive test image only; no child/personal data, production data, or provider credential in Git/mobile/evidence.
- Dependencies: FEAT-003 understanding contracts, FEAT-015 fixture contracts, FEAT-016 runtime/session contracts, FEAT-017 live Lightning development path, FEAT-004 PixiJS/GSAP renderer plan, ADR-0006 allocation rules.
- Contract authority: `plan/CONTRACT_FREEZE.md`.
- Pilot: 20 golden activities for full device/integration flow; 100 MVP activities for offline catalog/reference validation.

## Current state

P2 research round 1 is complete as documentation only (2026-09-09). Working research
and handoff notes remain local-only; publish selected completed P2 records after
owner review through the evidence index. See
`plan/P2_OFFLINE_FIRST_PLAN.md` (P2-R1, awaiting owner review). The proposal separates
offline work from later FEAT-003 producer connections and full live acceptance.
The owner reports Phase 8 executed with insufficient quality. A new untracked Phase 8
report appeared during final verification and records `QUALITY_NOT_READY`, with both
passes schema-valid 8/8 but below quality thresholds; its hash and provenance are in
the local research report. No FEAT-003 state, report or approval was changed by this research.

The repository has a fixture UI and backend-only live P2 route. The approved P1 slice is now implemented offline: the reviewed catalog is loaded through a typed template adapter, adult context and hard eligibility rules run before fit scoring, and the fixture-only ExperienceSpec compiler locks anchor/objective/template/spec identity at Gate B. PixiJS/GSAP runtime/bridge, approved asset pack, live media consumers and gallery journey remain downstream work and are still pending their own approval.

The D3-R2 harness review found and fixed only evaluation-boundary issues: non-blocking stdin
submission so a child that does not read its pipe still reaches the parent timeout; clean-worktree
validation now rejects untracked files; aggregation recomputes timing status instead of trusting a
spoofed field; child output locks the environment envelope; and missing source digests are allowed
only for the bounded byte-budget rejection. These changes do not alter D2 admission behavior.

Formal Cohort A execution completed at commit `c77230ca1593d5cd31098b5e58f3ff2a13d18a63` with
320 forward and 320 reverse samples. The sanitized metrics artifact and independent verification
report were owner-approved on 2026-09-11 and are indexed under `evidence/README.md`. This closes
D3/P2-T1 for the synthetic Cohort A scope at that time. Formal Cohort B was subsequently executed
and independently verified; the combined closure is recorded below.

## P2 image admission (D1) — 2026-09-10

An isolated image admission and decoding design was accepted and published
(`evidence/P2_IMAGE_DECODE_DESIGN_20260910.md`, `EV-018-P2-DECODE-DESIGN-01`), conditional on
preserving the existing FEAT-003 image-research path. The follow-on D1 specification is now
complete and published as revision 2 (`evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md`,
`EV-018-P2-D1-SPEC-01`): exact admission outcomes, bounded snapshot flow, a measured PyAV
decoder profile, a FEAT-018-local fixture manifest design, and an implementation acceptance
checklist. The specification is additive to FEAT-018 and changes no FEAT-003 default,
validator, inspector, contract, policy, prompt, model profile, fixture, scoring rule,
benchmark runner or historical evidence.

The owner subsequently approved U1 (`av==18.1.0` in a new optional `image-admission` extra
in `backend/pyproject.toml`) and the isolated D2 scope, recorded in `approvals/TASK_APPROVAL.md`
"Approved P2-T1 D2 scope addendum — 2026-09-10". **D2 implementation and its deterministic
tests are reviewed and accepted** (`evidence/notes/P2_D2_IMPLEMENTATION_20260910.md`,
`EV-018-P2-D2-IMPL-01`): 58 focused tests passed; the full 900-test backend collection reported
895 passed and 5 skipped, together with clean lint, type and repository validators. **D3
performance/memory evaluation revision D3-R2 now has an implemented, verified harness and a
successful non-reporting Cohort A preflight.** The fresh-process protocol, bounded I/O/cleanup,
Win32 native reads, conservative `[L,U]` classification, deterministic 16-profile manifest and
aggregation are covered by 32 tests. A 320-sample preflight completed without process or memory
failures and required no reversed-order pass, but it used an uncommitted working tree and is not
canonical D3 evidence. Formal exact-commit execution and owner review are complete for Cohort A.
Formal Cohort B was subsequently executed, independently verified and owner-approved. D2/D3 remain
additive to FEAT-018 only; FEAT-003 and all provider/mobile/public-contract integration remain
unchanged and separately gated.

## D3/P2-T1 closure - 2026-09-12

Formal Cohort B completed with 24 samples from eight owner-approved images, three fresh-process
repeats per image, all admitted and within the approved timing and memory targets. Independent
verification reproduced every published data value with zero discrepancies and accepted the result as
`PASS WITH FINDINGS`. D3/P2-T1 is closed for the offline Cohort A+B evaluation scope. The three
verification findings remain follow-up work before a future formal run relies on the same cleanliness
safeguard. Provider, mobile, Gate A, public-contract and shared-integration scopes remain separately
gated.

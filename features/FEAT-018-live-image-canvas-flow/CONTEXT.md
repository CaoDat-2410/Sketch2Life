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
**D3-R2 performance/memory evaluation is implemented, formally executed and independently
verified for offline Cohort A+B.** The fresh-process protocol, bounded I/O/cleanup, Win32 native
reads, conservative [L,U] classification, deterministic 16-profile manifest and aggregation are
covered by the D3 test suite. D3/P2-T1 is closed for the owner-approved offline Cohort A+B scope;
D2/D3 remain additive to FEAT-018 only. FEAT-003 and all provider/mobile/public-contract
integration remain unchanged and separately gated.
## Canonical P2 integration — 2026-09-11

The approved canonical P2 branch `origin/feature/feat018-p2-image-validation` was merged into `codex/feat-018-contract-plan` as merge commit `627260c`, after carrying the P2 integration approval addendum. The merge includes the reviewed D2 image-admission implementation, deterministic media validation, P2 offline fixtures and related evidence. The other P2 branches remain research references. D3 measurement, FEAT-003 producer connection, live provider execution, mobile/public-schema integration, P3/P4 implementation and production work remain pending.

## P3/P4 offline integration — 2026-09-11

The approved P3 renderer branch `origin/plan/person-3-art-animation-poc` was merged as `2851bb6`. It contributes the closed Motion DSL, PixiJS/GSAP browser player, source-art provenance loader, butterfly fixture/demo, validation, fallback and benchmark support. The approved latest P4 branch `origin/feat-018-person-4-media-integration` was merged as `77745c4`, followed by its replay entrypoint update `ccd1ea5` in merge commit `da1a369`. It contributes versioned learning-media contracts, cache-first resolver, safe fallback, replay fixtures and sanitized evidence. These are offline/scoped integrations; live provider execution, Android/mobile wiring, production assets and production deployment remain pending.


## P1 strict continuity polish — 2026-09-11

The approved P1-only polish is implemented in the application compiler. `P1_STRICT_CONTINUITY_V1` now hard-gates exact primary-anchor label/tag and semantic-kind compatibility, objective membership, downstream identity continuity and the immutable spec hash before Gate B approval. Bridge wording is child-facing and derived from the selected anchor and objective title while its versioned references remain locked to the same template.

The feature-local fixture set covers the butterfly fold-and-print pass, unrelated sorting rejection, unsupported anchor kind, unrelated objective, ambiguous selection, bridge drift, media-plan drift and spec-hash drift. The catalog audit confirms 20 non-production golden templates with non-empty anchor labels, supported kinds and known objective references. No P2/P3/P4 code, contract version, provider, mobile or production scope changed.

Validation evidence: `evidence/metrics/P1_STRICT_CONTINUITY_20260911.json` and `evidence/notes/P1_STRICT_CONTINUITY_IMPLEMENTATION_20260911.md`.


## P1 catalog and Gate integrity polish — 2026-09-11

The approved follow-on P1 integrity plan is implemented. The golden catalog adapter now removes objective IDs and broad area taxonomy values from `supported_anchor_labels`, normalizes and de-duplicates labels, and fails closed when meaningful labels or objective titles are missing. The compiler rejects duplicate template IDs, validates injected objective titles, enforces optional selected activity/objective refs when supplied, routes compilation through the same Gate B approval path, and independently verifies deterministic `spec_id` and `spec_sha256`.

The contract versions remain unchanged and no P2/P3/P4/shared/mobile source changed. The expanded P1 suite covers catalog hygiene, all optional context ref mismatch/partial cases, Gate B re-checks, duplicate registration, spec ID drift and downstream consumer compatibility. Evidence: `evidence/metrics/P1_CATALOG_GATE_INTEGRITY_20260911.json` and `evidence/notes/P1_CATALOG_GATE_INTEGRITY_IMPLEMENTATION_20260911.md`.

## P1 online-model compatibility tests — 2026-09-11

The approved compatibility addendum is implemented as an offline boundary suite. Provider-shaped Qwen3-VL-8B-Instruct and Whisper large-v3-turbo payloads pass through the existing structured adapters, preserve source hashes and provenance, and feed the existing adult-confirmed `SemanticAnchorSetV1` into the butterfly P1 compiler and Gate B. Malformed, prohibited, unknown, timeout, retry, empty-entity, low-confidence and unrelated-model cases fail closed. No live provider, model download, token, raw media or downstream source change was used.

Evidence: `evidence/metrics/P1_ONLINE_MODEL_COMPATIBILITY_20260911.json` and `evidence/notes/P1_ONLINE_MODEL_COMPATIBILITY_IMPLEMENTATION_20260911.md`.
## D3/P2-T1 closure - 2026-09-12

Formal Cohort B completed with 24 samples from eight owner-approved images, three fresh-process
repeats per image, all admitted and within the approved timing and memory targets. Independent
verification reproduced every published data value with zero discrepancies and accepted the result as
`PASS WITH FINDINGS`. D3/P2-T1 is closed for the offline Cohort A+B evaluation scope. The three
verification findings remain follow-up work before a future formal run relies on the same cleanliness
safeguard. Provider, mobile, Gate A, public-contract and shared-integration scopes remain separately
gated.

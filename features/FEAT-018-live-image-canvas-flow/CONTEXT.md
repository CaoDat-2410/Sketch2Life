# FEAT-018 live image and canvas context

- Status: P1 complete; D3/P2-T1 closed for owner-approved offline Cohorts A+B; P2-T2 contract
  boundary and bounded offline implementation complete; P2-T3 optional narration planning is in
  progress as a DRAFT and is not implementation-approved; live Lightning execution and downstream
  scopes remain separately gated
- Plan revision: 2 with approved P2-T1 D2/D3-R2 and P2-T2 offline addenda
- Owner: shared integration allocation pending contract freeze approval
- Goal: run a non-sensitive real JPG/PNG through validation, backend-only Qwen3-VL understanding, Gate A, one-anchor/one-objective ExperienceSpec compilation, P1/Gate B, PixiJS canvas, P4 cache/fallback, off-screen handoff, gallery journey and feedback.
- Data policy: non-sensitive test image only; no child/personal data, production data, or provider credential in Git/mobile/evidence.
- Dependencies: FEAT-003 `VisionUnderstandingResultV2` and local Qwen adapter boundary, FEAT-015 fixture contracts, FEAT-016 runtime/session contracts, FEAT-004 PixiJS/GSAP renderer plan, ADR-0006 allocation rules. FEAT-017's remote HTTPS path is not used by P2-T2.
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

## P2-T2 contract and offline implementation approval - 2026-09-12

The owner approved FEAT-018 consumption of FEAT-003's typed `VisionUnderstandingResultV2` and
local `qwen_vision.py` adapter boundary. FEAT-003 ownership is unchanged and its schemas, runtime,
profiles, dependencies, benchmarks, fixtures and evidence may not be modified. FEAT-017's flat V1
contract and remote HTTPS `LightningVisionAdapter` are excluded from P2-T2.

FEAT-018 owns a separate `RawUnderstandingResultV1` with typed observation groups, confidence
bounded to `0..1`, required source SHA-256, typed failures, preserved ambiguity/conflicts and
`gate_a_required=true`. The approved implementation slice is offline-only and limited to the exact
schema, port, mapper, unit/contract tests and one sanitized feature-local evidence note listed in
`approvals/TASK_APPROVAL.md`. Live Lightning/GPU execution, model-weight download, provider/network
calls, mobile, Gate A UI, P1 eligibility, P3/P4 and shared integration remain separately gated.

## P2-T2 offline implementation closure - 2026-09-12

The owner approved the completed offline P2-T2 implementation at commit
`11468d3a5a327697a491f09251a3210987337da0`. The change adds the mandatory ASR correlation guard
before `RawUnderstandingResultV1` construction and regression coverage for matching and mismatched
ASR results. Focused tests (17) and the related vision/Qwen/ASR sweep (801 passed, 5 skipped) passed;
ruff, mypy, repository validators and `git diff --check` were clean. The independent verification
report found no blocker and confirms the published contract/data scope is unchanged.

P2-T2 offline is complete. Live Lightning/GPU/model execution, provider/network calls, P2-T3 through
P2-T5, mobile, Gate A UI, P1 eligibility, P3/P4 and shared integration remain separately gated.

## P2-T2 bounded-runner offline implementation - 2026-09-14

The owner approved the FEAT-018 P2-T2 bounded-runner offline implementation on revision 5 of the
approval package (`evidence/notes/P2_T2_BOUNDED_RUNNER_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260914.md`,
SHA-256 `f36216432620e21eba2fc2f3f0c735ace529d15f827ad957dcf9b5e74ab8c9e5`) after independent audit
verdict `PASS_WITH_FINDINGS`. The implementation adds exactly the two approved files:
`backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` and
`backend/tests/unit/test_feat018_live_lightning_execution.py`. It implements
`Feat018AdapterCallSupervisor` (supervisor-authoritative deadline, `CONTAINMENT_READY` gate
protocol on POSIX/Windows with a real process handle for Windows Job Object assignment and a
bounded retry for POSIX group confirmation, a closed progress state machine with a formal
`FROZEN` state), `Feat018BoundedKillableQwenGenerationRunner` (bounded per-attempt subprocess
generation implementing the existing `QwenGenerationRunner` seam), and
`Feat018EvidenceCommitWriter`/`read_committed_pair` (the three-state evidence commit protocol
with a one-way hash DAG and a single JSON-rename commit point). The three MINOR findings from the
independent audit (Windows handle usage, POSIX bounded retry, a stale cross-reference in the
approval package) were addressed. The completed independent review and follow-up test hardening
record 154 focused offline tests and 839 related Qwen/vision/FEAT-018 tests passed, with 5 skipped.
The tests use injected fakes for live behavior and one real stdlib `spawn` context only to
construct (never start) the production-configured non-daemon outer Process; no real subprocess,
model, GPU, network, or Lightning execution occurred. Ruff and strict mypy are clean on the
bounded-runner source/test scope. `validate_harness.py`, `validate_repository_security.py`,
`validate_skeleton.py`, and `git diff --check` pass; the architecture validator retains the
unchanged `PRE_EXISTING_UPSTREAM` `backend_ai_workflow.py` violation. `qwen_vision.py` and all
other FEAT-003/FEAT-017 source are unmodified.

This closes only the offline bounded-runner implementation and independent-review stage. The
default inner launcher is verified to be constructed only after `CONTAINMENT_READY`; actual OS
nested spawning and real containment behavior remain deferred to a separately approved live-smoke
assertion. All twelve `P2T2-LIVE-D1` through `P2T2-LIVE-D12` decisions remain open, and no live
Lightning/GPU/model/provider/network execution is authorized by this entry.

## P2-T2 live-plan four-finding correction - 2026-09-15

Independent plan review identified an overstated coordinator completion claim.
The historic runner is a bounded adapter/status and evidence-storage primitive;
full admission/staging, runtime inventory, typed mapper handoff and incident
orchestration remain incomplete. The live plan now states the concrete remaining
two-file coordinator boundary and keeps D1/D11 BLOCKED alongside D4.

The intermediate 2026-09-14 checkpoint recorded 170 focused tests; that number
is historical and is not the current total. The owner-requested offline
correction adds `Feat018EvidenceFinalizer` and a precommit hook in the existing
writer. Cleanup and the caller's complete postflight audit precede final
publication; failed/exceptional checks or modified provisional bytes cannot
publish success. Successful cleanup is the approved quiescent-session boundary:
all supervised processes and descendants are absent, no runtime writer remains,
and evidence finalization is the sole authorized writer. The inventory is
rechecked after Markdown rename immediately before JSON commit. This is not a
filesystem-wide atomicity claim or protection from an unrelated hostile writer.
The finalizer supplies ordering and safe failure handling, not the still-missing
live coordinator. D10 approval inputs are separated from observed GPU facts, and
the exact live non-authorization marker is present. A subsequent checkpoint adds
worker-local mapping through the unchanged Raw mapper and a closed raw_status
terminal claim.
The supervisor retains that claim only from an accepted terminal event;
late/malformed claims are rejected. The correction also adds bounded explicit-root
artifact inventory, a sanitized incident writer, and `finalize_smoke_run`, which
connects supervisor status, session cleanup, exact provisional inventory and the
JSON commit point. Incident fallback is accepted only at
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`, after the future
coordinator/preflight explicitly confirms that destination is Git-ignored; tracked,
publishable, traversal, mismatched-run, symlink/reparse and arbitrary absolute
destinations are rejected. A synthetic session ID may be serialized in adapter
worker bootstrap arguments under spawn, but is bounded/opaque and is excluded
from progress/event IPC and evidence payload bodies. The current focused suite is
 196 passed; the related sweep was 885 passed, 5 skipped and 422 deselected;
 170 is only the historical checkpoint above. Final validation and
the F1-F4 dispositions are recorded in the ignored local report
`tmp/feat018-p2t2-four-findings-finalization-20260915/REPORT.md`.

No live execution, model acquisition, Stage 4 approval or P2-T2 live closure
is granted by this correction.

## P2-T3 optional narration planning - 2026-09-14

The optional narration plan is currently a DRAFT and planning work is in progress. It preserves
the completed P2-T2 typed ASR boundary and truthful `NOT_SUPPLIED`/success/failure provenance.
This draft does not authorize P2-T3 implementation, model or provider execution, GPU/Lightning
work, approval-record changes, or a commit. A separate owner approval is required before any
P2-T3 implementation begins.

## P2-T2 reviewed-runtime source binding - 2026-09-16

The owner bound `reviewed_runtime_code_commit` to
`9549a341194f40b1a9be419d6fce0d70f1ca0384` for the exact reviewed FEAT-018
runner/coordinator source and test blobs. This is a source-identity binding
only: D4, the remaining D1-D12 decisions, Stage 4, and all Lightning/GPU/model/
provider/network execution remain blocked or unauthorized. The binding is
recorded in the task approval and does not authorize a live run, commit, or
push by itself.

## P2-T2 D4 pre-staged snapshot approval - 2026-09-17

The owner approved `PRESTAGED_LOCAL_SNAPSHOT` for `P2T2-LIVE-D4` after a
Lightning-side completeness audit. The approved identity is
`Qwen/Qwen3-VL-8B-Instruct` at revision
`0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`, logical snapshot
`qwen3-vl-8b-instruct`, with sanitized manifest SHA-256
`8a1d50d6aef809130acd7b05b71369cccbb2360192b157f7871de2bd40c43eaf`.
The manifest contains 16 files and four indexed safetensors shards, and the
runtime download flag is `allow_model_download=false`. The observed NVIDIA L4
and 23034 MiB VRAM are runtime facts only and remain separate from D10 approval
inputs.

This closes D4 snapshot readiness only. Model loading, Lightning inference,
Stage 4, provider/network execution, and production use remain unauthorized;
D1 and D11 plus the remaining live decisions still require their own approval.

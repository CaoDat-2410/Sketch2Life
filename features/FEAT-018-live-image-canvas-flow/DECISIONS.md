# FEAT-018 decisions

- 2026-09-09 research record: user requested one P2 research round and proposals;
  any FEAT-003 change or connection requires user review first. Proposed offline
  slices and contract decisions are recorded in `plan/P2_OFFLINE_FIRST_PLAN.md`
  and local working research notes. Technical recommendations
  remain pending owner review; no implementation or contract migration is approved.

- 2026-09-09 publication decision: at the user's request, the P2 engine-handoff
  review and round-1 research working notes remain local and are ignored by Git.
  Only selected completed P2 records are published after owner review and indexed
  as canonical evidence, following the FEAT-003 publication distinction.

- 2026-09-07: Use one shared contract registry and JSON Schema compatibility gate before any person implements. Individual plans may not introduce parallel field names or versions.
- 2026-09-07: Freeze `VisionUnderstandingResultV1` for FEAT-018; the fixture reference to V2 requires a separately approved migration.
- 2026-09-07: Correct the canonical ACT-0004 mapping before integration: primary `OBJ_OBJECT_PERMANENCE`, secondary `OBJ_RECEPTIVE_LANGUAGE`.
- 2026-09-07: Full device pilot covers all 20 golden activities; all 100 MVP activities receive offline catalog/rule/provenance coverage before broader device rollout.
- 2026-09-07: User-provided non-sensitive image is a runtime source artifact, never committed; evidence stores hash/metadata only.
- 2026-09-07: PixiJS 8 + GSAP 3 remains the renderer baseline inside a controlled WebView/bridge; source artwork is preserved and derived visuals cannot silently replace it.

- 2026-09-09: Approve FEAT-018 revision 2 for the P1 implementation slice only; keep P2/P3/P4/shared integration and live/production execution pending separate approval.

- 2026-09-09: Implement P1 as a fixture-only compiler behind typed contracts. Catalog loading stays in infrastructure, selection/fit/Gate B stays in the application/domain boundary, and no downstream provider, renderer, cache or mobile code may select a different identity. The butterfly fold-and-print case is a test fixture only and does not change the 100/20 catalog counts or production eligibility.

- 2026-09-10 publication decision: publish the completed P2 D1 image admission and decoding
  specification (revision 2) as a selected canonical record,
  `evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md` (`EV-018-P2-D1-SPEC-01`), built on the
  previously accepted isolated design. Publication records the specification as complete and
  implementation-ready; it does not start, authorize, or approve D2 implementation, and does
  not amend `approvals/TASK_APPROVAL.md`. Dependency decision U1 (`av==18.1.0` in a new
  optional `image-admission` extra) remains an explicit open owner decision. The source
  revision-2 working note stays local; only this canonical record is published.

- 2026-09-10 completed-output decision: accept the isolated P2-T1 D2 image-admission
  implementation after review and publish `evidence/notes/P2_D2_IMPLEMENTATION_20260910.md`
  (`EV-018-P2-D2-IMPL-01`) through the feature evidence index. The accepted slice includes
  bounded single-snapshot acquisition, internal typed admission policy, the injected PyAV
  decoder, the exact optional dependency, deterministic fixtures and regression coverage.
  This decision authorizes recording and committing the reviewed D2 output only. It does not
  approve D3 measurement, mark P2-T1 complete, connect FEAT-003 producers, or authorize
  Qwen/ASR, mobile, Gate A, shared integration, public-schema migration, push or PR creation.

- 2026-09-10 D3-R2 approval decision: approve the isolated P2-T1 offline performance/native-memory
  evaluation plan and D3-U1 through D3-U6. The 5-second target binds only to the committed D2
  `admit()` interval. The 256-MiB target binds only to the conservative `[L,U]` working-set bracket;
  a crossing bracket is `INCONCLUSIVE`, never a pass. Cohort A implementation/execution may begin.
  Cohort B execution remains gated on owner visual review of the actual eight non-sensitive images,
  and completed sanitized evidence requires owner review before indexing or closing D3/P2-T1. No
  D2, FEAT-003, provider, mobile, Gate A, public-contract or production-isolation scope is approved.

- 2026-09-10 D3 implementation-state record: the approved D3-R2 harness and deterministic Cohort A
  manifest are implemented and preflight-verified. The 320-sample run is explicitly non-reporting
  because it used an uncommitted working tree; it cannot be indexed, treated as canonical target
  evidence, or used to close D3/P2-T1. Formal execution must identify the exact reviewed commit.
  Cohort B and completed-output publication gates are unchanged.

- 2026-09-11 D3 double-review record: two explicit review passes were completed against the
  implementation and tests. The first pass covered protocol/contract correctness and scope
  isolation; the second covered adversarial inputs, stdin/output limits, cleanup, privacy,
  Win32-memory validation and aggregation/statistics. Verified fixes are limited to the D3 harness:
  asynchronous bounded stdin writing, rejection of untracked worktrees for formal runs, timing
  status recomputation during aggregation, strict environment-envelope validation, and a narrow
  exception for missing digests only on byte-budget rejection. Regression tests cover each fix.
  D2 behavior, FEAT-003 and all downstream scopes remain unchanged; formal exact-commit execution,
  owner review and evidence indexing remain pending.

- 2026-09-11 owner approval and closure decision: approve the Formal Cohort A execution at commit
  `c77230ca1593d5cd31098b5e58f3ff2a13d18a63`, including the sanitized metrics artifact and the
  independent verification report. Index both reports and the JSON metrics under FEAT-018 evidence
  and close D3/P2-T1 for the synthetic Cohort A scope only. Cohort B remains unapproved and must
  retain its visual-source gate. No D2, FEAT-003, provider, mobile, public-contract or shared
  integration scope is thereby authorized.

- 2026-09-12 owner approval and closure decision: approve the Formal Cohort B execution and its
  independent verification with verdict `PASS WITH FINDINGS`. The 24-sample result (eight images,
  three fresh-process repeats each) is accepted with zero data discrepancies. Index the sanitized
  Cohort B report, metrics and independent verification, update the feature context and plan, and
  close D3/P2-T1 for the offline Cohort A+B scope. Carry the three verification findings as
  follow-up work; no Cohort B rerun is required. Provider, mobile, Gate A, public-contract and
  shared-integration scopes remain separately gated.

- 2026-09-12 P2-T2 contract decision: supersede the 2026-09-07 FEAT-018 V1 freeze for this task.
  FEAT-018 P2-T2 consumes FEAT-003's typed `VisionUnderstandingResultV2` through the approved
  `vision_v2.py`/`qwen_vision.py` boundary; ownership remains FEAT-003 and no FEAT-003 change is
  authorized. FEAT-017's flat V1 and remote HTTPS `LightningVisionAdapter` are not used. FEAT-018
  owns a separate `RawUnderstandingResultV1` with typed observation groups, `0..1` confidence,
  required source hash, typed failures, preserved ambiguity/conflicts and mandatory Gate A. The
  exact bounded file list is approved for offline implementation only. Live Lightning/GPU/model
  execution, provider/network calls and downstream integration require separate approval.

- 2026-09-12 P2-T2 offline closure decision: approve the implementation and ASR correlation fix at
  commit `11468d3a5a327697a491f09251a3210987337da0`. The mapper rejects a supplied ASR result whose
  correlation ID differs from the vision result before constructing Raw output; matching, absent and
  typed-failure ASR cases remain supported. Focused and related tests, lint/type checks, repository
  validators and diff checks passed. This closes only the offline P2-T2 contract/mapping slice;
  live Lightning/GPU/model execution and all downstream/provider/mobile/shared scopes remain gated.

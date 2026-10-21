# FEAT-018 evidence index

Evidence belongs under this feature only.

P2 publication policy: working research, review briefs and handoff drafts remain
local and are not canonical public evidence. Publish only selected completed P2
records after owner review, then add them to this index. Completing a research
round alone does not promote its working note to a public record.

P2-T4 draft-review distribution — 2026-10-20: the owner requested that the two sanitized documents
`plan/P2_T4_MAPPING_DIAGNOSTICS_PLAN_DRAFT_20261020.md` and
`plan/P2_T4_MAPPING_INPUT_REVIEW_DRAFT_20261020.md` be pushed on the Task 4 branch for Claude Cloud
review. They remain draft plan/input proposals, not completed canonical evidence or implementation
approval. The raw relayed review remains local. This scoped distribution does not change the policy
for other working research, review attachments or handoff drafts.

## P2-T4 diagnostic branch review distribution — 2026-10-20

Person 2's coordinator-chat instruction on 2026-10-20 was “OK đẩy lên đi sau đó cập nhật và viết lại
prompt review cho tôi”, in response to the proposal to push the Task 4 branch for Claude Cloud review.
At the time of this one-time branch distribution, the diagnostic note
([note](notes/P2_T4_MAPPING_DIAGNOSTICS_20261020.md)) and metrics
([report](metrics/P2_T4_MAPPING_DIAGNOSTICS_20261020.json)) recorded the initial partial result. It
is not canonical evidence publication or owner acceptance. B2/B3 were then NOT_RUN and Task 4
remained OPEN. A later Modal Notebook execution updated the report and completed B1/B2/B3. The
2026-10-21 owner amendment later permitted diagnostic-deliverable acceptance without changing the
row-level product gaps; independent final review and valid final gates remain open. This record does
not broaden the earlier plan/input review distribution or the general P2 publication policy.

## P2-T4 Modal execution evidence update — 2026-10-20

The owner supplied the Modal Notebook test result (368 passed, one Pydantic deprecation warning) and
generated report. The report tuple is 2,162,088 bytes, SHA-256
`15d4c5dfaecb2212205e1e705a85ef64493f37a3f54800579b051250227233a0`. It records B1/B2/B3 COMPLETE
for 120 primary cases and execution COMPLETE for 43 supplemental cases, with 60 primary and 5
supplemental requirements still UNRESOLVED. The report remains diagnostic evidence only, not owner
acceptance or Task 4 completion.

## P2-T4 diagnostic acceptance rebase — 2026-10-21

Person 2 issued `W2_FEAT018_P2_T4_DIAGNOSTIC_ACCEPTANCE_REBASE_01`; the exact issuance is in
`../approvals/TASK_APPROVAL.md`. It permits acceptance of the approved 120-primary/43-supplemental
diagnostic deliverable while preserving the report's 60 primary and 5 supplemental
`UNRESOLVED` results as product gaps. Follow-ups remain unassigned and are not implicitly moved to
Task 5. The Modal report's execution measurements and row-level findings are retained. Any
acceptance annotation is separately attributed and does not alter those measurements. Task 4 remains
open pending valid final gates and independent final review. See
[`P2-T4 diagnostics note`](notes/P2_T4_MAPPING_DIAGNOSTICS_20261020.md) for gate results, review
limits and follow-up IDs.

The latest local focused run passed 368 tests after installing the declared Pillow dependency into
the ignored virtual environment. Ruff, scoped mypy, architecture, skeleton and security checks pass.
The repository-wide harness remains `HARNESS_INVALID` because FEAT-045/046/047 lack unrelated
evidence directories. Person 2 dispositioned this on 2026-10-21: it stays `HARNESS_INVALID`, is not
a pass, and is a separate repository-wide issue outside P2-T4. Task 4 remains open until artifacts
are synchronized, validation evidence is bound to the final commit, valid gates are confirmed and
the final handoff commit receives independent review.

The checked-in JSON is a coordinator-annotated derivative, not the original Modal file. Its current
tuple is 2,163,861 bytes, SHA-256
`06d467a2629f5d03511cc4ef41997a5c9d84480a2dc7aa3433b3e8ed18e691b0`. The JSON annotation retains
the original Modal tuple and links to the note's review/gate record. The diagnostics note keeps both
tuples distinct.

## P2-T4 local Claude handoff review — 2026-10-21

The owner supplied an initial local Claude preliminary-handoff review (attachment named `Pasted text.txt`,
received 2026-10-21; 9,303 bytes,
SHA-256 `8aea9063f2fc35b19af315a8597d44fa50907da8ab94a16477bbf2609231b5e4`). It reported
`PASS WITH NOTES` for a static read of the amended handoff. This was performed in local Claude, not a
GitHub Cloud session. The reviewer used Read/Grep only, but explicitly did not review the Git diff,
verify file hashes/byte counts, or audit every JSON row; it could not establish that the files it read
matched HEAD `54d482d5`. A later re-review by the same Claude reviewer checked the prior candidate's
diff, tuples and JSON rows, but did not rerun gates and is not an independent final review. The
coordinator applied the re-review findings afterward; neither review covers the current working tree
or satisfies the independent final review required by the owner amendment.

The review's substantive notes are tracked in the diagnostics note: bind gate evidence to the
handoff state; distinguish the original Modal JSON from the current annotated JSON; make review
limitations and observed findings discoverable from plan/status/report; label the local
Pillow-blocked pytest result accurately; and state the exact overlap between static hypotheses and
runtime findings. No acceptance status is inferred from this review.

Selected completed P2 design record:
[isolated image admission and decoding](P2_IMAGE_DECODE_DESIGN_20260910.md)
(`EV-018-P2-DECODE-DESIGN-01`, owner-accepted design; implementation not started).

Selected completed P2 D1 specification, built on that design:
[image admission and decoding specification](P2_IMAGE_ADMISSION_SPEC_20260910.md)
(`EV-018-P2-D1-SPEC-01`, revision 2; implementation-ready specification; isolated from FEAT-003
behavior and contracts; followed by the separately reviewed D2 record below).

Selected completed P2-T1 D2 implementation record:
[bounded image admission implementation and validation](notes/P2_D2_IMPLEMENTATION_20260910.md)
(`EV-018-P2-D2-IMPL-01`; reviewed and accepted; subsequent D3/P2-T1 Cohort A closure is recorded below).

Selected completed P2-T1 D3-R2 Cohort A evidence, owner-approved 2026-09-11:
[Formal Cohort A execution report](notes/P2_D3_COHORT_A_FORMAL_20260911.md)
(`EV-018-P2-D3-COHORT-A-EXEC-01`; 640 samples at exact commit
`c77230ca1593d5cd31098b5e58f3ff2a13d18a63`; forward and reverse passes preserved).
[Independent verification report](notes/P2_D3_COHORT_A_INDEPENDENT_VERIFICATION_20260911.md)
(`EV-018-P2-D3-COHORT-A-VERIFY-01`; zero new discrepancies).
[Sanitized Cohort A metrics](metrics/P2_D3_COHORT_A_FORMAL_20260911.json)
(`EV-018-P2-D3-COHORT-A-METRICS-01`; 1,818,208 bytes;
SHA-256 `32e5e2373376eec0b7e30a488b0a7416a8cec4fe5c2b16957794373664606f40`).
The metrics artifact and all reports contain sanitized metadata only. Cohort B was subsequently
executed, independently verified and owner-approved as recorded below.

Selected completed P2-T1 D3-R2 Cohort B evidence, owner-approved 2026-09-12:
[Formal Cohort B execution report](notes/P2_D3_COHORT_B_FORMAL_20260912.md)
(`EV-018-P2-D3-COHORT-B-EXEC-01`; 24 samples from eight owner-approved images, three fresh-process
repeats per image; all samples admitted and within the approved timing and memory targets).
[Independent Cohort B verification report](notes/P2_D3_COHORT_B_INDEPENDENT_VERIFICATION_20260912.md)
(`EV-018-P2-D3-COHORT-B-VERIFY-01`; PASS WITH FINDINGS and zero data discrepancies).
[Sanitized Cohort B metrics](metrics/P2_D3_COHORT_B_FORMAL_20260912.json)
(`EV-018-P2-D3-COHORT-B-METRICS-01`; 24 samples; manifest correction disclosed and independently
verified). The raw images and local manifest remain ignored and are not published.

Selected completed P2-T2 offline contract/mapping record, owner-approved 2026-09-12:
[RawUnderstandingResultV1 contract freeze and offline implementation](notes/P2_T2_CONTRACT_FREEZE_20260912.md)
(`EV-018-P2-T2-CONTRACT-01`; implementation verified at commit
`11468d3a5a327697a491f09251a3210987337da0`; no model, provider, network or GPU execution).
The local independent verification report remains an ignored working artifact; this index contains
only the sanitized feature-local contract record.

- `raw/`: sanitized command output and contract-run summaries.
- `metrics/`: validation, latency, FPS, memory, cache/fallback and pilot reports.
- `screenshots/`: device screenshots with no personal data.
- `notes/`: allocation, contract-freeze, review and reconciliation notes.

Current pre-approval review: [completeness findings and required reconciliation](notes/PRE_APPROVAL_COMPLETENESS_REVIEW_20260908.md).

Person 4 registry reconciliation: [P4 contract registry reconciliation](notes/P4_CONTRACT_REGISTRY_RECONCILIATION.md).

Shared Android image-only UI/backend wiring and offline verification:
[Android demo integration verification](notes/UI_BACKEND_ANDROID_DEMO_VERIFICATION_20260918.md).
The note records fake-provider test results and the remaining operator-run emulator/live checks;
no live Lightning call was made by Codex.

Never store raw images, prompts, model output, tokens, signed URLs, personal metadata, or provider headers here. Store source SHA-256 and bounded metadata only.

Required evidence groups:

1. contract registry/schema compatibility;
2. media validation and provenance;
3. AI typed success/failure;
4. P1 mapping and Gate A/B invariants;
5. Pixi asset/bridge/source-preservation;
6. cache/fallback and 20-row device pilot;
7. harness/security validation.

Selected P1 strict continuity implementation record:
[P1 strict continuity polish](notes/P1_STRICT_CONTINUITY_IMPLEMENTATION_20260911.md)
(`EV-018-P1-STRICT-CONTINUITY-20260911`; approved compiler policy, fixture regression coverage and offline validation).

Selected P1 catalog and Gate integrity implementation record:
[P1 catalog and Gate integrity polish](notes/P1_CATALOG_GATE_INTEGRITY_IMPLEMENTATION_20260911.md)
(`EV-018-P1-CATALOG-GATE-INTEGRITY-20260911`; catalog hygiene, optional context locks, Gate B fail-closed checks and offline validation).

Selected P1 online-model compatibility implementation record:
[P1 online-model compatibility tests](notes/P1_ONLINE_MODEL_COMPATIBILITY_IMPLEMENTATION_20260911.md)
(`EV-018-P1-ONLINE-MODEL-COMPATIBILITY-20260911`; provider-shaped adapter fixtures, P1 handoff coverage and offline validation).

Selected live VLM schema-output remediation implementation record:
[Live VLM schema remediation](notes/LIVE_VISION_SCHEMA_REMEDIATION_IMPLEMENTATION_20260922.md)
(`EV-018-LIVE-VISION-SCHEMA-20260922`; bounded live-route repair wiring and sanitized local
verification; owner-run Lightning smoke remains pending).

Selected main-flow reliability implementation record:
[Main-flow hardening](notes/MAIN_FLOW_HARDENING_IMPLEMENTATION_20260928.md)
(`EV-018-MAIN-FLOW-HARDENING-20260928`; deterministic request/feedback/image/audio regressions,
mobile typecheck, UI validation, renderer suite/build, backend contract confirmation and Android
Metro bundle; emulator and live-provider acceptance remain operator-run).

Selected Pixi Android WebView bridge recovery record:
[Pixi Android WebView bridge recovery](notes/PIXI_ANDROID_WEBVIEW_BRIDGE_RECOVERY_20260928.md)
(`EV-018-PIXI-WEBVIEW-BRIDGE-RECOVERY-20260928`; bridge-size/readiness/cache/capability fixes and
offline regression checks passed; fresh-session Android playback acceptance remains pending).

Approved subject-recall and Pixi main-flow implementation:
[implementation and verification record](notes/SUBJECT_RECALL_AND_PIXI_MAIN_FLOW_HARDENING_IMPLEMENTATION_20260930.md)
records the bounded alias/ranking and adult-recovery changes, the stage watchdog and typed playback
failures, focused offline checks, and the remaining live rig/emulator visual acceptance boundary.
The earlier diagnosis remains available at
[`BIRD_SUBJECT_TOPIC_RECALL_DIAGNOSIS_20260929.md`](notes/BIRD_SUBJECT_TOPIC_RECALL_DIAGNOSIS_20260929.md).

Pixi mask-background renderer regression:
[synthetic local-donor fix](../../FEAT-030-original-derived-auto-rig/evidence/notes/PIXI_MASK_BACKGROUND_RECONSTRUCTION_FIX_20260930.md)
(`E-030-FIX-013`; offline checks pass; Android visual acceptance pending).

The repeated `MASK_BACKGROUND_RECONSTRUCTION_FAILED` follow-up and same-image paper-donor recovery
are recorded in FEAT-030 [E-030-FIX-014](../../FEAT-030-original-derived-auto-rig/evidence/notes/PIXI_MASK_BACKGROUND_RECONSTRUCTION_FIX_FOLLOWUP_20260930.md).
The backend delivered renderer artifacts successfully; renderer/mobile offline checks pass, while a
fresh Android visual retest remains pending.

Part-aware Pixi playback verification is recorded in FEAT-030:
[Pixi part-motion restoration](../../FEAT-030-original-derived-auto-rig/evidence/notes/PIXI_PART_MOTION_RESTORATION_20260928.md)
(`E-030-FIX-008`; synthetic/offline checks pass; Android visual and live SAM acceptance remain pending).

Documentation-only Montessori/profile audit:
[child-context audit](notes/CHILD_CONTEXT_MONTESSORI_AUDIT_20260929.md) identifies the current
age/current-scene boundary and lack of consumed longitudinal preferences. The proposed integrated
editor, recommender and SAM/renderer plan is
[`INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md`](../plan/INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md)
is approved. The implementation record is
[indexed here](notes/INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_IMPLEMENTATION_20260929.md); it
distinguishes passing offline evidence from pending Android/L4/live-mask acceptance.

## Closure Gate 3 disposition and latest candidate — 2026-10-21

Person 2 issued `W2_FEAT018_P2_T4_GATE3_HARNESS_DISPOSITION_01`. `HARNESS_INVALID` remains the
repository-wide result, not a pass or waiver, and is outside the P2-T4-specific gate set. Gate 3 is
met only when every listed P2-T4 gate passes with a valid result bound to the final handoff commit.

Person 2 subsequently issued `W2_FEAT018_P2_T4_CONTINUATION_AND_FINAL_GATE_SCOPE_01`. Its fresh
candidate Ruff command with `--no-cache --no-fix --no-fix-only` passed with exit 0 and
`All checks passed!`. The prior cache-denied run remains a distinct no-verdict record in the note.
The other six valid candidate results remain applicable because source/config/tool versions were
verified unchanged at HEAD `4310fcbf`.

The amended C/D order permits candidate synchronization now. The JSON annotation records
`CANDIDATE_CHECKS_PASS` and points to `W2_FEAT018_P2_T4_POST_COMMIT_GATE_RECORD_01`; it does not
claim Gate 3 MET. That final proof will be a chat record bound to the full handoff commit SHA after
separate commit permission and a final seven-gate cycle. Task 4 remains OPEN pending that proof and
independent final review; current stage/commit/push authority is absent. See the
[diagnostics note](notes/P2_T4_MAPPING_DIAGNOSTICS_20261020.md) for commands, provenance and limits.

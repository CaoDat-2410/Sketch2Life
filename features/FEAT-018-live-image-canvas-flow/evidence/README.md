# FEAT-018 evidence index

Evidence belongs under this feature only.

P2 publication policy: working research, review briefs and handoff drafts remain
local and are not canonical public evidence. Publish only selected completed P2
records after owner review, then add them to this index. Completing a research
round alone does not promote its working note to a public record.

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

- `raw/`: sanitized command output and contract-run summaries.
- `metrics/`: validation, latency, FPS, memory, cache/fallback and pilot reports.
- `screenshots/`: device screenshots with no personal data.
- `notes/`: allocation, contract-freeze, review and reconciliation notes.

Current pre-approval review: [completeness findings and required reconciliation](notes/PRE_APPROVAL_COMPLETENESS_REVIEW_20260908.md).

Never store raw images, prompts, model output, tokens, signed URLs, personal metadata, or provider headers here. Store source SHA-256 and bounded metadata only.

Required evidence groups:

1. contract registry/schema compatibility;
2. media validation and provenance;
3. AI typed success/failure;
4. P1 mapping and Gate A/B invariants;
5. Pixi asset/bridge/source-preservation;
6. cache/fallback and 20-row device pilot;
7. harness/security validation.

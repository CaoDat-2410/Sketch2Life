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
(`EV-018-P2-D2-IMPL-01`; reviewed and accepted; D3 not started and P2-T1 not complete).

- `raw/`: sanitized command output and contract-run summaries.
- `metrics/`: validation, latency, FPS, memory, cache/fallback and pilot reports.
- `screenshots/`: device screenshots with no personal data.
- `notes/`: allocation, contract-freeze, review and reconciliation notes.

Current pre-approval review: [completeness findings and required reconciliation](notes/PRE_APPROVAL_COMPLETENESS_REVIEW_20260908.md).

Person 4 registry reconciliation: [P4 contract registry reconciliation](notes/P4_CONTRACT_REGISTRY_RECONCILIATION.md).

Never store raw images, prompts, model output, tokens, signed URLs, personal metadata, or provider headers here. Store source SHA-256 and bounded metadata only.

Required evidence groups:

1. contract registry/schema compatibility;
2. media validation and provenance;
3. AI typed success/failure;
4. P1 mapping and Gate A/B invariants;
5. Pixi asset/bridge/source-preservation;
6. cache/fallback and 20-row device pilot;
7. harness/security validation.

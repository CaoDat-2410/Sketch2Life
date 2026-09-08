# FEAT-018 evidence index

Evidence belongs under this feature only.

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

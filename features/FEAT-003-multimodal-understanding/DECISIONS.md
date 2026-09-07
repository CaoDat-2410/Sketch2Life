# FEAT-003 decisions

- Original input references are immutable; preprocessing creates working copies.
- Raw model output is never canonical meaning until Gate A.
- Conflicts and uncertainty are preserved, not silently overwritten.
- Prohibited psychological/personality inference fields are excluded from the contract.
- P2-T2 and P2-T3 use injected provider protocols plus deterministic fixture adapters; provider SDKs, endpoints, credentials, and network calls remain outside this sprint slice.
- ASR/VLM adapters return versioned typed success/failure contracts. Provider SDK objects and raw provider payloads never cross the infrastructure boundary.
- Source hashes are nullable when a source cannot be read; a path-derived digest is never presented as media-content provenance.

## Compatibility review decision — 2026-09-05
- Record independent test success separately from integration readiness. P2 vision schema mapping is not a Montessori mapping adapter.
- Recommend versioned fixture/contract agreement, P2 fusion/evaluation, and a separately approved integration allocation under ADR-0006; do not merge or implement wiring during this review.
- Evidence: evidence/notes/P2_P1_REVIEW_20260905.md.

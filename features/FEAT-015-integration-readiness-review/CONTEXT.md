# Integration readiness review
- Status: DONE
- Owner: project owner / Codex reviewer
- Goal: inspect all fetched member branches and propose an integrated flow and test strategy.
- Scope: read-only code review, existing offline checks, branch topology and conflict inspection, documentation.
- Non-goals: implementation, merge, commit/push, provider/GPU execution, visual changes, final integration allocation.
- Sources: docs/context/PROJECT_CONTEXT.md; docs/context/SOURCE_REGISTER.md; ADR-0006; docs/architecture/CONTRACTS_AND_INTEGRATION.md; member feature plans and evidence at pinned commits.
- Risks: stale status records; independent green tests do not establish integration readiness.
- Next gate: report review; a separate implementation plan/allocation and approval are required before integration code.

## Review completion — 2026-09-05
- EV-015-01 completed: evidence/notes/READINESS_REVIEW.md.
- P1/P2 prior same-day checks reused at unchanged commits; P3 checks reproduced; P4 failure/skip and mock demos recorded.
- Integration proposal and test strategy remain PROPOSED, with no implementation approval. No product code changed.

## Owner decisions recorded — 2026-09-05

- P1 owns canonical activity/objective IDs and versions across the integration slice.
- Gate A is mandatory before P1 filtering.
- ASR/vision disagreement preserves both claims and requires adult confirmation/correction.
- No eligible P1 activity leads to additional context collection and re-evaluation.
- The first vertical slice is the fixture/mock path: media -> P2 result -> Gate A -> P1 filtering -> Gate B -> P3 DRAW_REVEAL + P4 cache hit -> activity handoff.
- The integration plan includes a PixiJS asset work package: synthetic fixture asset, versioned manifest, source hash/provenance, loader validation, and visual approval before product application.

## Asset decisions clarified — 2026-09-05

- First integration asset: use WHOLE_DRAWING as the primary path; keep support for CROP, TRANSPARENT_PNG, and MASK in the contract/loader so the renderer can build those paths later without making them a first-slice dependency.
- The first slice uses fixture/demo assets only; no asset is applied to the mobile product yet.
- A shared integration fixture means one synthetic, immutable test package consumed by multiple workstreams: source drawing/audio, manifest and hashes, expected P2 result, explicit P1 context, expected Gate A/B decisions, P3 asset/plan expectation, and P4 media expectation. It is test input, not shared mutable runtime state or a database.
- Preserve P3's existing butterfly fixture. Create a separate integration fixture package derived from the same reviewed synthetic scenario so P3 remains independently runnable.

## Implementation update — 2026-09-05

The approved bounded fixture slice is implemented. The package is synthetic, hash-checked and read-only by loader convention; the harness covers eight named scenarios and the tests pass. Broader P2 fusion, P3 bridge, P4 provider exception handling and runtime integration remain separate approved work.

## Revision 2 implementation update — 2026-09-05

The approved offline integration adapters are implemented and verified: P2 fusion preserves modality claims/conflicts, Gate A/B enforce session versions and canonical P1 identity, P3 validates the whole-drawing asset bridge, and P4 returns cache/fallback/block results with approved identity preserved. The flow is in-memory and synthetic only.

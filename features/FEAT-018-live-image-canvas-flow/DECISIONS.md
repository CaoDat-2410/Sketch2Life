# FEAT-018 decisions

- 2026-09-07: Use one shared contract registry and JSON Schema compatibility gate before any person implements. Individual plans may not introduce parallel field names or versions.
- 2026-09-07: Freeze `VisionUnderstandingResultV1` for FEAT-018; the fixture reference to V2 requires a separately approved migration.
- 2026-09-07: Correct the canonical ACT-0004 mapping before integration: primary `OBJ_OBJECT_PERMANENCE`, secondary `OBJ_RECEPTIVE_LANGUAGE`.
- 2026-09-07: Full device pilot covers all 20 golden activities; all 100 MVP activities receive offline catalog/rule/provenance coverage before broader device rollout.
- 2026-09-07: User-provided non-sensitive image is a runtime source artifact, never committed; evidence stores hash/metadata only.
- 2026-09-07: PixiJS 8 + GSAP 3 remains the renderer baseline inside a controlled WebView/bridge; source artwork is preserved and derived visuals cannot silently replace it.

- 2026-09-09: Approve FEAT-018 revision 2 for the P1 implementation slice only; keep P2/P3/P4/shared integration and live/production execution pending separate approval.

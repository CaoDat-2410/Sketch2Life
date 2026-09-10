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

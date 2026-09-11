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

- 2026-09-11: Use `origin/feature/feat018-p2-image-validation` as the canonical P2 branch for FEAT-018 offline integration. Merge commit `627260c` connects the reviewed P2-T1 D2 image-admission slice to `codex/feat-018-contract-plan`; the other P2 branches remain research-only references. This does not authorize D3 measurement, FEAT-003 producer migration, live provider execution, mobile/public-schema integration, P3/P4 implementation, or production deployment.

- 2026-09-11: Integrate the approved P3 renderer and latest approved P4 media branches into the FEAT-018 integration branch. Keep P3 source-art preservation and renderer fallback, and keep P4 objective/activity/template identity propagation through cache and fallback. Root replay entrypoint `scripts/replay_learning_media.py` is part of the P4 integration so the feature replay test runs from a clean checkout. No live provider, Android/mobile, production asset or production deployment scope is opened.


- 2026-09-11: Implement the approved P1 strict continuity polish as an application/compiler-only policy revision. `P1_STRICT_CONTINUITY_V1` requires exact anchor label/tag and semantic-kind compatibility, objective membership, consistent bridge/media/activity identities and a matching `ExperienceSpecV1.spec_sha256` before Gate B approval. Existing contract versions and P2/P3/P4 consumers remain unchanged; unrelated, ambiguous or tampered fixture flows block closed.


- 2026-09-11: Implement the approved P1 catalog and Gate integrity polish without changing contracts or downstream code. Exclude `OBJ_*` and broad area taxonomy labels from anchor metadata; treat optional selected activity/objective refs as exact constraints when present; use one Gate B approval path; and fail closed on duplicate template IDs, missing objective titles, spec ID drift and spec hash drift.

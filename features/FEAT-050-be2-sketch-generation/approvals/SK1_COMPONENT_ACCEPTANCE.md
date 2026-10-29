# BE2-04 SK1 component acceptance

- Status: ACCEPTED (offline component scope only, with the owner dispositions below)
- Checkpoint: SKETCH_COMPONENT_OFFLINE (SK1)
- Accepted by: Person 2 (owner of BE2-01–07), direct instruction in the Claude session
- Recorded at: 2026-10-18 23:15 +07:00 (Asia/Saigon), recorded by Claude
- Basis (latest focused review): `../evidence/notes/SK1_CODEX_FOLLOWUP3A_REVIEW_20261018.md`
  (PASS; F3-R31, N1, N2 closed; no new actionable finding), SHA256
  c084884c663c6e0c5c745a2f0b52fe93d36c5b0048c5de1eb3430772065d6c20, and
  `../evidence/metrics/SK1_CODEX_FOLLOWUP3A_REVIEW_20261018.json`, SHA256
  10ace5f604180d9e74637e0f6a39f760df5442a0796e5e132eed3e1700384719. Reviewed delta:
  `../evidence/notes/SK1_CLAUDE_FOLLOWUP3A_20261018.md` (2932fc19…) and
  `../evidence/metrics/SK1_CHECKS_FOLLOWUP3A_20261018.json` (eeca663f…).
- Review chain (history, unchanged): `../evidence/notes/SK1_IMPLEMENTATION_EVIDENCE_20261018.md`,
  `SK1_CODEX_FOLLOWUP_20261018.md`, `SK1_CLAUDE_FOLLOWUP3_20261018.md`,
  `SK1_CODEX_FOLLOWUP3_REVIEW_20261018.md`, `SK1_CLAUDE_FOLLOWUP3A_20261018.md`,
  `SK1_CODEX_FOLLOWUP3A_REVIEW_20261018.md` and their metrics.
- Snapshot check at recording time: all 15 source/test/fixture references in the final review
  metrics match SHA256 and byte length (0 drift); the four preserved references, the follow-up 3A
  note/metrics, approval and approved plan match their pinned hashes. Independent focused SK1:
  175 passed, 0 skipped; Ruff, strict mypy and the four validators pass (final review metrics).
  Historical regression X01–X03: 875 passed, 3 skipped (Pillow live-app imports), source-bound to
  unchanged production files.
- Approval and plan (unchanged): `TASK_APPROVAL.md` SHA256
  0f356d32b7cab883be6b3079400ada26495555cef160a6fb6a2a3b742a607d25;
  `../plan/PLAN_REV5_APPROVED.md` SHA256
  461d06849899ea41f2c93432ed8b88c5a64428cf17bce5d2959a6d26ef4fa819.
- Identity: worktree `.worktrees/be2-04-sketch-generation`, branch
  `feature/be2-04-sketch-generation`, HEAD 113cdf956a09336a0abf5561bd939f5e13b31ea0, staged 0;
  SK1 work uncommitted.

## Accepted snapshot (source/test/fixture, from the final review metrics)

| Path | SHA256 | Bytes |
|---|---|---|
| `backend/src/sketch2life/domain/sketch_proposal.py` | 09203d4b8a0e808c2df056093b2d2391bc21dab835e3a9912a0eb5ad6aac6cde | 33161 |
| `backend/src/sketch2life/application/ports/sketch_generation.py` | 94d06cbd53dc5600ce21b06301d126c5afa2b8cd37981d7581fbf37324accf60 | 11682 |
| `backend/src/sketch2life/application/services/sketch_generation.py` | 47cfbebefc44e6257d7d7b34e6bd45a13ee6d7d437be86d5fd0533f57ae8c24f | 51815 |
| `backend/src/sketch2life/contracts/schemas/sketch_proposals.py` | c31f6b83a08de912dfaf5eae76fb66ee837156ee1618489fedf7d92937dee029 | 5806 |
| `backend/src/sketch2life/infrastructure/sketch_generation/__init__.py` | 62b01e7232b952e6bd04b4652ece5d4caab4f30382b3eb06e53d30762f8f7ed0 | 86 |
| `backend/src/sketch2life/infrastructure/sketch_generation/adapters.py` | 7b45ffe72559e34269c1798009b98dcdbe08096f41298dd4e0e64f67003d99f0 | 27337 |
| `backend/src/sketch2life/infrastructure/sketch_generation/fakes.py` | de94d1a336c61b38816ca9b890dd41851fe4974d8501521b79c7377692d554e2 | 19022 |
| `backend/src/sketch2life/infrastructure/sketch_generation/harness.py` | 63c1eed9b71daef8e50ec8c7459588b5c88660a446921d49ed45650443cfdf68 | 35470 |
| `backend/tests/unit/test_sketch_proposal_domain.py` | c29251e5d51be4e6f06e3cc92bdc3e327795fabe5e11065c8ac4fe26f76e1635 | 15908 |
| `backend/tests/unit/test_sketch_generation_service.py` | 50db6c216e8e6980dbd43cd09a428b6b16512bee2af3aa5cb3bcc0d91157e2bc | 26431 |
| `backend/tests/unit/test_sketch_generation_adapters.py` | 03e46038873bc94c69091ce17b0ed24a133a6d83032b4177f1360451e6da7dfe | 16963 |
| `backend/tests/unit/test_sketch_generation_chain.py` | 2071924f070e23052b0684a8e9cae84864d0667896e2ab7ac5ed26d0925f0a65 | 30936 |
| `backend/tests/unit/test_sketch_generation_races.py` | 964cb21c67ca0c34e658f3d5601da3eb607f2c372a87a7a1d83a00db05ec615f | 70668 |
| `backend/tests/contract/test_sketch_proposal_contracts.py` | 6c3a1be1bd02a46ae9a7dfcb8f69dbfdef28a6f584df0c7847b0350ddc7491ad | 7044 |
| `features/FEAT-050-be2-sketch-generation/fixtures/h_ai_review/sketch_proposal_examples.json` | 96598b51c479c36672a88b1f295976f5d5bd32b53e728eeb2e09c3504fc5da5b | 3898 |

These 15 rows equal `verified_file_references` in the final review metrics.

## Verbatim decision

> - Tôi chấp nhận deviation F-5 trong phạm vi SK1 offline: chain harness dùng SketchChainEligibility để route eligibility theo job_type khi sweep job dùng chung; Sketch dùng SketchEligibility, Vision giữ hành vi AssistanceEligibility. Đây là chấp thuận riêng cho composition fixture, không phải chấp thuận kiến trúc production hay sửa foundation/A1.
> - Tôi chấp nhận các mục N04/N08/N11 ở mức chain và C03/C03b ở cột contract còn PARTIAL tại mốc SK1. Giữ nguyên nhãn và bằng chứng thực tế; đưa phần còn thiếu vào danh sách phải xử lý trước khi claim integration tương ứng.
> - Tôi chấp nhận callback A1 end-to-end còn NOT_RUN tại mốc SK1. Ghi nó thành gate kiểm thử khi mở checkpoint tích hợp; không coi checkpoint tích hợp đã được phê duyệt qua quyết định này.
> - Tôi ghi nhận residual N16: phản hồi Child cancel có thể phân biệt proposal tồn tại và không tồn tại. Chấp nhận residual này trong fixture SK1; không coi đây là quyết định cho public API/production.
> - Tôi nghiệm thu BE2-04 SKETCH_COMPONENT_OFFLINE (SK1) trên snapshot khớp review cuối, cùng các giới hạn nêu trên.
> - Nghiệm thu này không đóng toàn bộ card BE2-04, không chứng minh Studio/PG/Redis/RQ/provider/decoder hoặc durable multi-process.
> - Quyết định này cho phép ghi hồ sơ nghiệm thu và chuẩn bị kế hoạch commit. Chưa cho phép stage, commit, push, merge, deploy hay tạo nhánh mới.

## Residuals carried forward (labels unchanged)

| Item | Label at SK1 | Carried to |
|---|---|---|
| F-5 `SketchChainEligibility` in the chain harness | Accepted deviation, fixture composition only | Not a production architecture decision; foundation/A1 unchanged |
| SK-N04 chain (real BE2-02 analysis with non-accepted status) | PARTIAL | Must be demonstrated before claiming the corresponding integration (03→04 seam) |
| SK-N08 chain (wrong job type / digest mismatch through real jobs) | PARTIAL | Same |
| SK-N11 chain (malformed variants beyond `canvas_operations`) | PARTIAL | Same |
| SK-C03 / SK-C03b contract column (golden vectors only in domain/chain tests) | PARTIAL | Same |
| A1 post-commit callback → `SketchStageAdapter` end to end | NOT_RUN | Test gate of the future integration checkpoint (that checkpoint is **not** approved by this decision) |
| N16 Child cancel distinguishes existing vs missing proposal | Accepted residual in the SK1 fixture | Not a public API/production decision |
| SK-NI01, Studio, PostgreSQL, Redis/RQ, live provider/model, decoder | NOT_IMPLEMENTED / NOT_RUN | Runtime/live gates of card BE2-04 |

## Not included

Full BE2-04 card acceptance, production adoption, other owners' sign-off (P1/P2/P4, BE2-14), any
runtime/provider evidence, Git publication (stage/commit/push/merge/deploy), creation of the
shared branch `feature/be2-01-07`, or any new checkpoint. BE2-01 stays WAITING_STUDIO, BE2-02
PARKED, BE2-03 A1 accepted offline / card IN_PROGRESS, BE2-04 IN_PROGRESS / NOT_DONE.

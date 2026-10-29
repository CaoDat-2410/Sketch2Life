# Task approval — BE2-08

- Status: APPROVED
- Approver: project owner, direct chat reply
- Plan revision: 1
- Approved scope: revision1 P1–P4, P5 preparation and scoped checkpoint commits
- Approved at: 2026-10-18, Asia/Saigon (chat date; exact wall-clock not asserted)
- Approval evidence: actual user reply "duyệt làm task 08" after plan presentation
  and scope conformance explanation. This supersedes earlier planning-only reply.
- Notes: Actual provider/runtime/provisioning/SQL environment decisions remain
  separately gated. No push/merge/deploy or real BE1/P4 integration sign-off inferred.

- Plan SHA256: 370c6c04573a684c0e51c0ef1c276224d8e1f01ecd701624b2d925751cfa0b04

Do not edit reviewed plan bytes following approval; use a new revision for scope
changes. Hash identifies proposed bytes, not evidence of approval.

## Supplemental cross-lane submission/finalization approval — 2026-10-21

- Status: APPROVED — supplemental offline scope only.
- Card: FEAT-050 / BE2-08.
- Approved addendum: plan/CROSS_LANE_BE2_08_SCOPE_DRAFT_20261021.md
- Approved addendum SHA256: 6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0
- Scope: two separate atomic boundaries for submission and finalization with external generation between them, including replay/lost-ack/late-result behavior, adopted source-currentness and phase-specific policy gates. CR08-01 and owner-boundary details remain explicit gates.
- Existing revision-1 approval and plan remain unchanged. Exact execution file subset must be recorded before editing; any migration or unlisted/shared-contract path requires a revised scope and approval.
- Excludes direct foundation writes, provider/runtime/Lightning/Modal, BE2-09 review/access, publication, and card status/acceptance changes.
- Approver: project owner, direct instruction in Codex chat.
- Recorded: 2026-10-21, Asia/Saigon; exact message timestamp not independently asserted.

### Verbatim owner approval

> Duyệt scope BE2-01, BE2-07, BE2-08, BE2-09 và BE2-14 theo đúng nội dung và SHA trong hồ sơ. Chỉ làm offline. Giữ X05d BLOCKED, X05c/CR09-02 mở; không chạy Modal, Lightning, provider hay runtime.

## Supplemental BE2-VIDEO-LIFECYCLE/1 persisted seam approval — 2026-10-22

- Status: APPROVED — exact FEAT-050 manifest below, offline only.
- Card: FEAT-050 / BE2-08.
- Scope: `../FEAT-057-be2-01-14-offline-integration/plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md`
- Scope SHA256: `F170809FCBB71D1B588960466350D6086568EFB6384232AB0F178DF7D350C052`
- Previous exact approval target: `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`; the original owner approval quote below is retained verbatim.
- Owner-authorized metadata-only amendment: the machine-specific Worktree locator was removed; contract terms, §2 boundaries, §3 environment limits, and §4 owner manifest are unchanged. Owner instruction: “sửa theo đề xuất” in the current Codex conversation on 2026-10-22 (Asia/Saigon). No scope expansion is authorized.
- CR08-01 adopted as `BE2-VIDEO-LIFECYCLE/1`, covering A/S/B and identity-failure exactly as defined in §2 of that hash-pinned scope. BE2-01 owns each transaction's begin/commit/rollback; BE2-08 participates through the typed transaction-bound contract and writes only BE2-08 rows. No SQL connection is exposed through an application port.
- This approval freezes only these FEAT-050 paths for the scoped implementation and tests:
  - `backend/src/sketch2life/domain/knowledge_video/model.py`
  - `backend/src/sketch2life/infrastructure/knowledge_video/codec.py`
  - `backend/src/sketch2life/infrastructure/knowledge_video/sql.py`
  - `backend/src/sketch2life/application/ports/knowledge_video.py`
  - `backend/src/sketch2life/application/ports/knowledge_video_worker.py`
  - `backend/src/sketch2life/application/knowledge_video_create.py`
  - `backend/src/sketch2life/application/knowledge_video_worker.py`
  - `backend/src/sketch2life/contracts/schemas/knowledge_video.py`
  - `backend/src/sketch2life/infrastructure/knowledge_video/foundation_lifecycle.py` (NEW)
  - `backend/tests/unit/test_knowledge_video_domain.py`
  - `backend/tests/unit/test_knowledge_video_persistence.py`
  - `backend/tests/unit/test_knowledge_video_create.py`
  - `backend/tests/unit/test_knowledge_video_worker.py`
  - `backend/tests/contract/test_knowledge_video_contract.py`
- Source/test work and database creation may begin only after all three FEAT-044/050/057 approval records contain this scope hash and their exact §4 owner manifests, and that state is verified.
- Local database permission is limited to §3: a dedicated, newly created loopback PostgreSQL 17 database with a random `be2_xlane_...` name and synthetic data, used only for offline transaction/persistence verification. No shared, staging, or production database; no provider, Modal, Lightning, HTTP server, deployed service, or runtime. Existing approved schema only; no schema or migration additions or edits.
- Excludes all paths not listed above, BE2-07/01/09/14-owned paths, D4, BE1 implementation, route/envelope changes, card acceptance/status changes, and durable BE2-07 source-fence implementation. The fence remains a separate gate and X01 remains `PARTIAL` until a fence held through finalization is proven.
- Approver: project owner, direct instruction in this Codex conversation; recorded 2026-10-22, Asia/Saigon (exact wall-clock time not asserted).

### Verbatim owner approval

> Chốt adopt contract `BE2-VIDEO-LIFECYCLE/1` gồm A/S/B và identity-failure theo §2 của Rev2, SHA256 `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`. Cho phép cập nhật ba approval record FEAT-044, FEAT-050, FEAT-057 với scope hash và file list chính xác theo §4. Cho phép PostgreSQL cục bộ cô lập, dữ liệu tổng hợp, chỉ để kiểm thử offline theo §3. Chưa sửa source/test hoặc tạo database cho tới khi các approval được ghi và xác minh. Giữ durable source fence ngoài scope và X01 ở PARTIAL.

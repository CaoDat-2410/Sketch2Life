# BE2-01 Phase B task approval

- Status: **APPROVED**.
- Approver: user / project-task owner, explicit reply in this Codex chat on 2026-10-15.
- Recorded by: Codex, documentation/handoff only; Claude remains the backend implementation executor.
- Recorded at: 2026-10-15T11:59:42+07:00 (recording clock; chat message has no separate timestamp).
- Feature/branch: FEAT-044 BE2-01; `feature/be2-01-ai-job-foundation`.
- Approved plan: `plan/PHASE_B_PLAN.md` revision 3, B1–B6; sha256
  `bb20d5be45dc0552a803f67b5927d4a38dc113cabe10b3a6088644d874ba5848`.
- Approved decision packet: `plan/PHASE_B_DECISION_RECORD.md` revision 8 §13, sha256
  `0d5fdbfd783ddde3c08e739c23fe936784be73bcf8cb43dddf079dffde67164f`.
  The byte-identical approved revision is preserved in feature-local evidence; current revision 9
  records this actual directive and gate reconciliation without changing the accepted decisions.
- Review basis: `evidence/notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md` PASS at design scope;
  reviewed sequences draft revision 2 and current component-scope reconciliation in
  `evidence/notes/PHASE_B_B1_CLOSURE_AND_HANDOFF_20261015.md`. Acceptance remains plan B-01..B-12;
  approval does not mark runtime criteria passed.
- Phase A disposition: accepted candidate/fixture checkpoint. Candidate P1/P2/P4 details and
  Q1–Q8 are accepted as **PROJECT_OWNER_DIRECTIVE**, never as those role owners' sign-off.
  Actual role concurrence/registry/production adoption and real integration remain deferred.
- Environment: synthetic-only `sketch2life-backend-test`, existing isolated Python3.12 runner,
  PostgreSQL17/Redis8. Retain `fixture.durable_jobs.v0` as fixture-only. §13 includes selected
  source/test synchronization to this Studio, without secret/media/data transfer.
- Execution order: B1 component decisions/documentation closed; **first Claude code turn B2 only**
  (SQL schema + migrations + relevant validation/evidence); stop for review before B3. Approval
  covers unchanged B1–B6 scope, so no repeat approval is needed for routine authorized work.
- Excluded: BE2-02..14, live router/provider/model, durable ProviderCopyLifecycle, production
  policy/deployment, BE1-owned implementation/writes, FEAT-018/Wan changes, commit/push/deploy.
- Phase A `approvals/TASK_APPROVAL.md` is preserved byte-for-byte. This separate file is explicitly
  requested by the user; do not rewrite the historical Phase A approval or the approved rev3 plan.
- State at recording: Phase B backend code **NOT_STARTED**; active handoff **Q01 / B2 READY_FOR_CLAUDE**.

## Approval evidence (verbatim user reply)

```text
Tôi nghiệm thu Phase A trong phạm vi candidate/fixture.

Tôi chấp thuận PHASE_B_DECISION_RECORD.md revision 8 §13
dưới dạng PROJECT_OWNER_DIRECTIVE; không coi đây là sign-off P1/P2/P4.

Tôi duyệt BE2-01 Phase B theo PHASE_B_PLAN.md revision 3,
phạm vi B1–B6, sử dụng Studio sketch2life-backend-test.

Claude ghi nguyên văn lệnh này vào approvals/PHASE_B_TASK_APPROVAL.md,
giữ nguyên approval Phase A. Triển khai B2 trước,
dừng để review trước B3. Không commit, push hoặc deploy.
```

## Supplemental cross-lane dispatch approval — 2026-10-21

- Status: APPROVED — supplemental offline scope only.
- Card: FEAT-044 / BE2-01.
- Approved addendum: plan/CROSS_LANE_BE2_01_SCOPE_DRAFT_20261021.md
- Approved addendum SHA256: AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD
- Scope: typed route for the adopted BE2-08 job type at the foundation dispatch boundary, with unknown types failing closed. The envelope/schema and existing provider path remain unchanged unless a new reviewed scope is approved.
- This supplements, and does not replace or expand, the prior Phase B B1-B6 approval. Exact execution file subset must be recorded before editing; paths outside the approved addendum require a new approval.
- Excludes BE2-07/08/09/14-owned files, schema/migrations, runtime/provider/Lightning/Modal, publication, and card acceptance/status changes.
- Approver: project owner, direct instruction in Codex chat.
- Recorded: 2026-10-21, Asia/Saigon; exact message timestamp not independently asserted.

### Verbatim owner approval

> Duyệt scope BE2-01, BE2-07, BE2-08, BE2-09 và BE2-14 theo đúng nội dung và SHA trong hồ sơ. Chỉ làm offline. Giữ X05d BLOCKED, X05c/CR09-02 mở; không chạy Modal, Lightning, provider hay runtime.

## Supplemental BE2-01 execution manifest — 2026-10-21

Before the first source edit, the exact BE2-01 execution subset is frozen under
the supplemental approval above:

- Modify `backend/src/sketch2life/infrastructure/ai_jobs/worker.py`.
- Add `backend/src/sketch2life/infrastructure/ai_jobs/typed_dispatch.py`.
- Add `backend/tests/unit/test_ai_job_video_dispatch.py`.
- Run `backend/tests/unit/test_ai_job_video_dispatch.py` and the existing
  `backend/tests/unit/test_ai_job_b5_capability.py` as offline validation. The
  existing regression file is read-only unless the approved behavior itself
  makes it fail.

The video job type is supplied explicitly by composition and forwarded unchanged
to the registered BE2-08 `VideoWorker`; this does not create a new shared
envelope value or authorize runtime registration. Existing `sketch_assistance`
provider dispatch is preserved. Unregistered job types fail closed before
provider execution. No other BE2-01 path, shared contract, schema, migration,
card status, acceptance, or Phase B scope is included. The remaining four card
manifests are not implied by this one.

## Supplemental BE2-VIDEO-LIFECYCLE/1 persisted seam approval — 2026-10-22

- Status: APPROVED — exact FEAT-044 manifest below, offline only.
- Card: FEAT-044 / BE2-01.
- Scope: `../FEAT-057-be2-01-14-offline-integration/plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md`
- Scope SHA256: `F170809FCBB71D1B588960466350D6086568EFB6384232AB0F178DF7D350C052`
- Previous exact approval target: `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`; the original owner approval quote below is retained verbatim.
- Owner-authorized metadata-only amendment: the machine-specific Worktree locator was removed; contract terms, §2 boundaries, §3 environment limits, and §4 owner manifest are unchanged. Owner instruction: “sửa theo đề xuất” in the current Codex conversation on 2026-10-22 (Asia/Saigon). No scope expansion is authorized.
- CR08-01 adopted as `BE2-VIDEO-LIFECYCLE/1`, covering A/S/B and identity-failure exactly as defined in §2 of that hash-pinned scope. BE2-01 owns each transaction's begin/commit/rollback; BE2-08 participates through the typed transaction-bound contract and writes only BE2-08 rows. No SQL connection is exposed through an application port.
- This approval freezes only these FEAT-044 paths for the scoped implementation and tests:
  - `backend/src/sketch2life/application/ports/ai_jobs.py`
  - `backend/src/sketch2life/application/services/ai_jobs.py`
  - `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py`
  - `backend/tests/unit/test_ai_job_application.py`
  - `backend/tests/unit/test_ai_job_lifecycle.py`
  - `backend/tests/integration/ai_jobs/test_sql_repository.py`
  - `backend/tests/integration/ai_jobs/test_completion_recovery.py`
- Source/test work and database creation may begin only after all three FEAT-044/050/057 approval records contain this scope hash and their exact §4 owner manifests, and that state is verified.
- Local database permission is limited to §3: a dedicated, newly created loopback PostgreSQL 17 database with a random `be2_xlane_...` name and synthetic data, used only for offline transaction/persistence verification. No shared, staging, or production database; no provider, Modal, Lightning, HTTP server, deployed service, or runtime. Existing approved schema only; no schema or migration additions or edits.
- Excludes all paths not listed above, BE2-07/08/09/14-owned paths, D4, BE1 implementation, route/envelope changes, card acceptance/status changes, and durable BE2-07 source-fence implementation. The fence remains a separate gate and X01 remains `PARTIAL` until a fence held through finalization is proven.
- Approver: project owner, direct instruction in this Codex conversation; recorded 2026-10-22, Asia/Saigon (exact wall-clock time not asserted).

### Verbatim owner approval

> Chốt adopt contract `BE2-VIDEO-LIFECYCLE/1` gồm A/S/B và identity-failure theo §2 của Rev2, SHA256 `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`. Cho phép cập nhật ba approval record FEAT-044, FEAT-050, FEAT-057 với scope hash và file list chính xác theo §4. Cho phép PostgreSQL cục bộ cô lập, dữ liệu tổng hợp, chỉ để kiểm thử offline theo §3. Chưa sửa source/test hoặc tạo database cho tới khi các approval được ghi và xác minh. Giữ durable source fence ngoài scope và X01 ở PARTIAL.

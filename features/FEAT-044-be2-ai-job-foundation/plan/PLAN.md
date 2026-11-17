# Kế hoạch BE2-01 — AI/job contract foundation

- Status: APPROVED (Phase A revision 1)
- Plan revision: 1
- Implementation status: IN_PROGRESS
- Approval status: APPROVED — Phase A A1–A9 only, 2026-10-14; see approvals/TASK_APPROVAL.md
- Date: 2026-10-14, Asia/Saigon
- Branch: `feature/be2-01-ai-job-foundation`
- Owner: P3 / BE2
- Baseline: `b9204d8c9eb4f8a1ee6d4db4de5ee23672e0392c`

## 1. Mục tiêu và nguồn

Xây nền tảng chung cho Vision/Sketch/video: yêu cầu có scope và nguồn cố định, job/attempt lifecycle, retry/cancel/completion và trạng thái an toàn cho UI. Runner đầu tiên dùng synthetic fixtures/fake ports, chạy độc lập với BE1, app và provider thật.

Nguồn: FEAT-040 card BE2-01; canonical SRS v3.1 B19.10/B19.11/B22.3, DATA-25, CMD-44; FR029/030/037/051/054; UC-019/025/032; P-NFR-16; ADR-0015. FR030/054 và refinement/policy chưa adopt giữ nhãn PROPOSED. Toàn bộ 14 card và thứ tự nằm trong `BE2_ROADMAP.md`.

## 2. Phạm vi: hai chặng riêng

| Chặng | Đầu ra | Điều kiện | Giới hạn nghiệm thu |
|---|---|---|---|
| **A — đề nghị làm trên nhánh này** | Domain job/attempt; DATA-25; payload candidates DATA-21–29/33; CMD-44; completion/repository/queue ports; fake clock/provider/authorization/artifact/queue; standalone runner | Approval cho Phase A revision 1 | Contract/component semantics, chưa durable hoặc live |
| **B — follow-on riêng** | Durable DATA-25 repositories/migrations, request/attempt CAS, dispatch/completion receipts, transactional outbox và queue adapter | Plan/approval riêng; adopted runtime/storage/queue ADR; generic persistence contract từ BE1 | Actual restart/concurrency/dispatch/recovery evidence |

P3 giữ ownership cả hai chặng. Fake repository không là durable storage. Phase A không chứng minh real generation, actual provider deletion hoặc toàn BE2 runtime DONE. Current change chỉ viết tài liệu; không sửa runtime hay cài dependency.

## 3. Checklist Phase A theo thứ tự

| Bước | Cần làm | Đầu ra review được |
|---|---|---|
| A1 | Mapping SRS fields/status/authority; pure job/attempt domain và transition guards | Field map, CONFIRMED/PROPOSED/TBD register, transition table |
| A2 | DATA-25 validator/projection và shape fixtures DATA-21–29/33 | Candidate schema version, positive/negative fixtures, manifest/hash |
| A3 | Repository/idempotency/receipt, context/authorization, queue/provider/clock/artifact/audit ports | Protocols và deterministic fake adapters có fault injection |
| A4 | Create/dispatch/progress/retry orchestration | Same request → one job; same key/different payload → conflict; bounded named policy |
| A5 | Cancel/completion với active attempt, request revisions, hash và live eligibility | Stale/rejected/duplicate receipts; no late publication; fake CAS |
| A6 | Scoped CMD-44 query và thin HTTP adapter trong isolated fixture/test app bằng dependency overrides | `GET /jobs/{job_id}`, safe role projections, ETag/poll hints, typed errors; không inject fake grants/provider vào main live app |
| A7 | Provider-copy discovery/cancel/purge/receipt fake support | Fixture-marked outcomes, Pending/Unsupported/Exception và conformance |
| A8 | Standalone runner; domain/application/schema/HTTP tests | Một lệnh offline, actual reports và fault traces |
| A9 | Cross-review/handoff P1/P2/P4; context/decisions/evidence/status update | Consumer example, error catalogue, compatibility/adoption note |

A2 chỉ dựng shape/fixtures cho các card khác, không triển khai nghiệp vụ của 13 card còn lại. Shared DATA-24 exact review có primary owner BE2-05; ProviderCopyLifecycle có primary owner BE2-14. Candidate schemas có thể giao từ foundation; live adoption vào registry do cross-review ghi nhận riêng.

### Candidate file map

Paths dưới đây là đề xuất, chưa tồn tại; tên cuối cùng có thể tinh chỉnh theo review:

| Tầng | Path từ repo root | Trách nhiệm |
|---|---|---|
| Domain | `backend/src/sketch2life/domain/ai_jobs/` | Python thuần: entity/value objects/transitions/policy |
| Ports | `backend/src/sketch2life/application/ports/ai_jobs.py` | Job/receipt/context/dispatch/completion interfaces |
| Application | `backend/src/sketch2life/application/services/ai_jobs.py` | Create/retry/cancel/complete/query orchestration |
| Contract | `backend/src/sketch2life/contracts/schemas/ai_jobs.py` | DATA-25 parsing/mapping; versioned public view |
| HTTP | `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py` | CMD-44 thin adapter; fixture composition tách live wiring |
| Fakes | `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py` | Deterministic stores/queue/provider/clock/faults |
| Tests | `backend/tests/unit/test_ai_job_lifecycle.py`, `backend/tests/unit/test_ai_job_application.py`, `backend/tests/contract/test_ai_job_contracts.py`, `backend/tests/contract/test_ai_job_polling.py` | Transitions/dedup/stale/schema/HTTP scope |
| Runner/fixtures | `features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py`, `fixtures/` | Standalone entry, synthetic manifest/policies/consumer examples |

Domain không import FastAPI/Pydantic/storage/queue/model SDK. Application phụ thuộc domain và ports; providers/persistence ở infrastructure. Giữ source và đường legacy; không bulk migrate old workflow contracts trong Phase A.

## 4. Contract và invariants

DATA-25 candidate map giữ identity: `job_id`, `organization_id`, `job_type`, `job_revision`, `request_ref`, `attempt_id`, `attempt_number`, `correlation_id`, timestamps. Public fields: state/progress/result_refs/failure/poll hints theo SRS; typed failures không mang traceback/token/provider URL.

- States: `queued`, `running`, `succeeded`, `failed_retryable`, `failed_exhausted`, `blocked_unsafe`, `cancelled`.
- Disposition riêng: `accepted`, `stale`, `rejected`. Stale không phải job state mới.
- Progress: `unknown|stages|percentage`; unknown có value null, percentage phải là dữ liệu thật trong [0,100].
- Job success giữ exact result version/hash/provenance, không đồng nghĩa Teacher approved, video played hoặc session complete.
- CMD-44 minimized projection; Child không lấy pending media/ref nhạy cảm trước exact Teacher review. BE1 CMD-59/60 vẫn giữ query/delivery gateway; BE2 cung cấp eligibility/projection ports.
- Poll policy dùng named `JOB_POLL_MIN_INTERVAL`, bounded backoff và nullable hints; không adopt số polling cũ thành production. ETag theo revision; authorization chạy trước cache/304.

### Transition table candidate

| Từ | Sự kiện hợp lệ | Sang / hiệu lực |
|---|---|---|
| Chưa có job | Authorized request, new semantic fingerprint | `queued`, attempt đầu và request receipt |
| `queued` | Start đúng attempt/current scope | `running` |
| `queued/running/failed_retryable` | Authorized cancel/revocation/session-end notice | `cancelled`; invalidate scheduled retry; late output không publish |
| `running` | Completion và output hợp lệ/current | `succeeded`, disposition accepted |
| `running` | Retryable failure/timeout, policy còn attempts/budget | `failed_retryable` |
| `failed_retryable` | Policy retry được phép | `queued`, attempt mới trên semantic job cũ |
| `running/failed_retryable` | Hết attempts/budget | `failed_exhausted` |
| `queued/running` | Unsafe tại guard tương ứng | `blocked_unsafe` |
| Bất kỳ | Wrong attempt/request/hash/revision/context hoặc revoked completion | Stale/rejected receipt; không áp result/overwrite attempt mới |
| Terminal | Duplicate cùng identity/fingerprint | Receipt cũ nếu actor còn read authority; không reopen |

Terminal: succeeded/failed_exhausted/blocked_unsafe/cancelled. Teacher retry sau exhausted thuộc BE2-10 và là explicit new cycle theo adopted policy; không generic reset. Table là implementation proposal cần review guards trước code.

### Idempotency/completion acceptance

Command idempotency scope theo SRS B22.1: `(organization_id, principal_id, contract_name, target_id, idempotency_key)` với normalized payload fingerprint; same scoped key/different payload conflict. Command receipt identity tách business/semantic dedup: policy semantic request giống nhau có thể resolve cùng job nhưng không chia sẻ receipt/quyền giữa principals. Read/replay receipt vẫn recheck current disclosure authority. Queue redelivery vẫn một attempt; chỉ policy retry tạo attempt kế tiếp. Retry/start recheck current eligibility và cancellation; cancel trong backoff invalidates scheduled retry để callback cũ không tạo attempt mới. Kill-switch policy notice cũng phải làm pending work không tiếp tục ngoài policy hiện hành. Attempts/timeout/backoff/budget dùng named synthetic policy PROPOSED, không hardcode giá trị production.

Completion: verify internal worker capability → current receipt disclosure authority → duplicate/fingerprint lookup → với completion mới, active attempt + expected request/job revisions + input hash + current context/session/config epochs → consent/purpose/audience/cancellation/recall/source-expiry checks qua owning ports → persist result/disposition/receipt/event once. Same identity/different output là conflict/incident. Superseded attempt stale. Worker không có public Android completion route và không mutate session/portfolio trực tiếp.

Phase A mô phỏng CAS/receipts bằng fake; Phase B mới chứng minh transaction và durable outbox. Provider-copy fake receipt có nhãn fixture; ongoing/unverified purge là Pending/Unsupported/Exception, không report actual Deleted.

## 5. Acceptance Phase A

| ID | Case | Kết quả bắt buộc |
|---|---|---|
| A-01 | Standalone runner | Không cần live BE1/app/DB/broker/provider SDK/credentials; deterministic report |
| A-02 | DATA-25 round-trip/invalid fixtures | Required fields/enums/ranges đúng; reject malformed, không sửa ngầm |
| A-03 | Duplicate semantic request | One job/attempt/immutable receipt; không tăng semantic cost |
| A-04 | Same key đổi payload/scope | Typed conflict, nguồn/job cũ giữ nguyên |
| A-05 | Queue redelivery/duplicate completion | One effect; retry delivery không thêm attempt |
| A-06 | Fake concurrent CAS / same identity đổi output | One winner; changed output conflict/incident |
| A-07 | Timeout/retry đến policy limit | Bounded attempts → failed_exhausted, không infinite loop |
| A-08 | Unknown/stage/percentage progress | Unknown null; preserve truthful values, reject malformed/range |
| A-09 | Poll ngoài organization/audience/current grant | Safe denial; không leak protected existence/artifact/provider internals |
| A-10 | ETag/cache poll sau revoke | Recheck quyền trước cache/304; không leak old result |
| A-11 | Wrong attempt/request/revision/hash completion | Stale/rejected receipt; active state/result không bị overwrite |
| A-12 | Source/context/config đổi khi running | Lineage giữ nguồn cũ; không tự áp result vào context mới |
| A-13 | Cancel queued/running/failed_retryable backoff/ngay trước completion | Outcome rõ, invalidate scheduled retry; no new attempt/resurrection/late publication |
| A-14 | Consent revoke/session end/content recall/source expiry/kill-switch notice | Current eligibility chặn dispatch/retry/new acceptance/exposure |
| A-15 | Unsafe/malformed output | Typed blocked/failure; no exposure; diagnostic redacted |
| A-16 | Success/result pending review | Exact refs/provenance; chưa approve/play/complete; Child projection safe |
| A-17 | Worker capability sai / client completion | Deny; card chỉ expose public CMD-44 |
| A-18 | Fake copy discover/cancel/purge duplicate/errors | Scoped fixture receipts; Pending/Unsupported/Exception không là Deleted |
| A-19 | DATA-24/ProviderCopyLifecycle candidates | Version/owner rõ; video/library consumer fixtures không chờ Sketch live |
| A-20 | Handoff P1/P2/P4 | Schemas/hash/errors/example/compatibility note và actual conformance report |

A-06/A-18 chỉ chứng minh fake semantics; chưa actual DB concurrency/deletion. Phase A ready không có nghĩa BE2-01 durable/full card DONE.

## 6. Verification và evidence

Current change chỉ là planning; commands implementation dưới đây **planned, chưa chạy/pass**. Dùng existing compatible environment. Default Python audit thiếu pytest/FastAPI/ruff/mypy/redis/rq; không cài runtime/GPU mới trên Windows. Missing dependency được ghi `REQUIRES_LIGHTNINGAI_TEST` và chạy ở separate Sketch2Life LightningAI environment sau approval. Runner bản pure-domain phải import mà không phụ thuộc cwd.

```text
python features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py
python -m pytest backend/tests/unit/test_ai_job_lifecycle.py backend/tests/unit/test_ai_job_application.py backend/tests/contract/test_ai_job_contracts.py backend/tests/contract/test_ai_job_polling.py
python -m pytest backend/tests/unit/test_ephemeral_storage_ports.py backend/tests/unit/test_whiteboard_video_job.py backend/tests/unit/test_story_video_job_input_gate.py backend/tests/contract/test_mobile_workflow_contracts.py
python -m ruff check <changed_python_files>
python -m mypy <changed_python_modules>
python tools/validate_harness.py --feature features/FEAT-044-be2-ai-job-foundation
python tools/validate_architecture.py
python tools/validate_repository_security.py
python tools/validate_skeleton.py
git diff --check
```

Backend tests từ repo root cần environment `PYTHONPATH=backend/src`; paths tests mới là proposed outputs. Scope ruff/mypy theo code thực tế và config repo. Khi cần model/integration, dùng `scripts/lightningai/setup.sh` → `verify.sh` → `run_tests.sh` theo project policy; suite phải bổ sung BE2 checks đã approved, scripts legacy chưa chứng minh BE2 pass.

Evidence trong feature: command/environment/time/reviewer, fixture hashes, schema/transition report, redacted fault traces, adapter conformance, cross-review/adoption note. Actual checks của planning nằm ở `evidence/notes/VALIDATION.md`. LOCAL_CODE_READY, LIGHTNINGAI_ENVIRONMENT_READY, LIGHTNINGAI_TEST_PASS, VISUAL_QA_PASS là gates riêng.

## 7. Handoff và review

| Reviewer/consumer | Nhận từ BE2 | Giữ trách nhiệm |
|---|---|---|
| P1 / FE | Safe job state/progress/error/poll fixtures, consumer example | UI/device behavior; review usability payload |
| P2 / BE1 | Context/authorization/persistence/outbox/asset/audit boundary pack, copy receipts | Review scope/generic ports; own CMD-59/60/lifecycle authority |
| P4 | Runner, composition ports, schema pack, env/activation/compatibility notes | Registry/live wiring và combined test coordination |

BE2 tự giao domain/application/adapters/component tests/fault evidence và sửa defects. CMD-48 sole dispatcher thuộc BE2-12; BE2-13/14 là typed branches; non-AI core policy qua BE1 port. Không cross-module DB coupling.

## 8. Phase B và các quyết định còn mở

Trước Phase B: separate plan/approval; ADR database/queue/outbox/transaction/recovery/service identity; adopt BE1 generic persistence interfaces; uniqueness/CAS/receipt semantics P2/P4 review. Numeric retry/poll/timeout/cost/priority cần versioned policy.

Acceptance B: restart sau commit giữ request/job/attempt/receipt; broker down vẫn recoverable queued; dispatcher retry không tạo semantic attempt; actual concurrent completion chỉ một winner; crash/replay sau provider output bảo toàn fingerprint/disposition; durable outbox dedup; cancel/revoke race chặn exposure; actual migrations/adapter fault reports. Provider-specific lifecycle và real inference evidence thuộc BE2-04/08/14 tương ứng.

Model/license/support modes/video strategy/rights/moderation/production capacity vẫn quyết định ở card tương ứng. Reviewed-library path có thể đi trước generation-model decision; toàn BE2-08 chỉ DONE khi có actual generation evidence cho scope đã chọn.

## 9. Next gate

Plan revision 1 sẵn để review. `approvals/TASK_APPROVAL.md` giữ generated placeholder AWAITING_APPROVAL; không tạo approval runtime từ yêu cầu planning. Chỉ bắt đầu A1–A9 sau explicit approval Phase A revision 1 và record đúng phạm vi. Phase B và 13 card khác có plan/approval riêng.

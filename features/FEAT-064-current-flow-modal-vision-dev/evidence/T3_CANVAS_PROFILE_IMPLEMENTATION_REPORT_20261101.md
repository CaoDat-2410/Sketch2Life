# T3 — BE1 canvas operation profile report

- Status: XONG-CHƯA REVIEW.
- Plan: plan/T3_BE1_CANVAS_PROFILE_IMPLEMENTATION_PLAN_20261101.md
- Plan SHA-256: 347CC6C7D8B7DC0877E933A1AB13D68629F6BE849B7AAA3E07E3D1683ABE347A
- Approval: G1 T3 entry in approvals/TASK_APPROVAL.md, including the append-only plan-path correction.
- Layers: L1 domain/request contract and L5 session/HTTP append. L3 persistence schema/migration was not changed.

## Implemented

- New pilot-enabled local/test sessions receive the server-owned CanvasOperationProfileV1 configuration. Caller configuration cannot set the reserved profile keys.
- Profiled append requests must echo the exact profile version. The server validates stroke-only payload shape, palette, widths, normalized finite coordinates, precision, point count, and the existing 32 KiB bound before persistence.
- Accepted operations retain the server profile id. Invalid or mismatched operations reject before persistence. Previously created sessions without a profile keep their previous payload interpretation.
- Eligibility, identity, current-turn, epoch, revision, idempotency, and append-only guards remain independent.

## Test and static-check evidence

- New unit profile tests: 39 passed.
- Final combined CPU/offline baseline and G1 contract/unit set: 267 passed, 4 skipped.
- Final isolated PostgreSQL synthetic-pilot module: 31 passed.
- The exact T3 red-phase count was not retained in the current ledger/output record; it is not reconstructed here.
- Ruff lint: passed for all 10 changed/new Python files. Ruff format: 9 files passed; test_app_composition.py has a pre-existing formatter suggestion in an unrelated route-map comprehension. Its approved change is only the exact T9 route entry, so that unrelated line was left untouched.
- Strict mypy on L1 files (domain profile, schema, and new unit tests): no issues in 3 files.
- Strict mypy over all 10 G1 Python files has the same 5 existing router diagnostics as the HEAD-source shadow run; no new mypy diagnostics remain.

## HỢP ĐỒNG CHO UI

**Đính chính câu ở bản G1 trước:** Child không đọc `configuration.canvas_operation_profile.version` từ session response. G1 review-fix thêm `profile_version` nullable ngay trong response reconnect; Child phải đọc trường đó từ reconnect rồi gửi lại khi append. Session cũ trả `null` và tiếp tục hành vi legacy.

Reconnect:

```http
GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect?after_revision=0
X-Be1-Grant: <device-grant>
X-Be1-Device-Key: <device-key>
```

```json
{
  "contract": "Be1CanvasReconnectV1",
  "canvas_id": "synthetic-group-00000000000000000000000000",
  "turn_id": null,
  "profile_version": "CanvasOperationProfileV1",
  "document_epoch": 1,
  "current_revision": 0,
  "checkpoint": null,
  "operations": []
}
```

Khi session paused hoặc chưa có active turn, `turn_id` là `null`; session active có thể trả turn hiện hành. Profile cũ không được bịa: `profile_version` là `null`. UI hiện chưa được sửa: `apps/child-ui/src/services/sessionClient.ts` khai báo `turn_id: string` và chưa có `profile_version`; L6 vẫn DEFERRED-BY-OWNER.

Append một stroke synthetic hợp lệ:

```http
POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations
X-Be1-Grant: <device-grant>
X-Be1-Device-Key: <device-key>
Idempotency-Key: synthetic-stroke-001
Content-Type: application/json
```

```json
{
  "operation_id": "synthetic-operation-001",
  "turn_id": "synthetic-turn-001",
  "document_epoch": 1,
  "expected_revision": 1,
  "profile_version": "CanvasOperationProfileV1",
  "operation_payload": {
    "kind": "stroke",
    "points": [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
    "color": "#FFD21F",
    "size": 5
  }
}
```

Response khi được nhận:

```json
{
  "contract": "Be1CanvasOperationReceiptV1",
  "status": "accepted",
  "canvas_id": "synthetic-group-00000000000000000000000000",
  "resulting_revision": 1,
  "operation_id": "synthetic-operation-001"
}
```

Giới hạn profile: chỉ `kind=stroke`; palette đúng 5 mã `#FFD21F`, `#FF596C`, `#1685F8`, `#31C978`, `#9250E8`; `size` là một trong 5, 9, 14; 2–512 cặp `x/y`; toạ độ finite trong [0,1], tối đa 6 chữ số thập phân; phần `operation_payload` tối đa 32 KiB. Client phải làm tròn trước khi gửi; ví dụ giá trị JSON `0.30000000000000004` bị 422, server không tự sửa thành `0.3`. Request profile thiếu/sai version trả 409 `CANVAS_PROFILE_MISMATCH`; payload stroke ngoài profile trả 422 `CANVAS_PROFILE_INVALID`. Cả hai không lưu nét; UI phải reconcile nét bị từ chối và không blind-retry.

Mã lỗi append ở biên HTTP: 401 auth/grant không hợp lệ; 403 `FORBIDDEN_ROLE`, `SCOPE_DENIED`, `INVALID_TURN`; 404 group/device scope không tồn tại; 409 profile mismatch, revision/idempotency conflict hoặc guard trạng thái; 422 request validation/profile invalid. Body BE1 là object cấp cao nhất gồm `code`, `message`, `request_id`, không phải FastAPI `detail` lồng nhau.

### R4 bổ sung kết quả kiểm và giới hạn

- R0 trước review đã ghi 267 passed, 4 skipped và 31 passed cho module PostgreSQL; đó là số lịch sử. R4 chạy lại hiện tại: CPU/offline **294 passed, 4 skipped**; PostgreSQL synthetic-pilot **48 passed**. HEAD archive tương ứng: 227/4 và 4 PG pass.
- Ruff lint và format đều sạch trên 7 file Python trong lượt review-fixes. Strict mypy so 6 file source hiện tại với HEAD: hiện tại 5 diagnostic, HEAD 7, **0 diagnostic mới**.
- OpenAPI snapshot generated không đổi. Không sửa UI, export/render/admission, migration, BE2/provider, Modal/GPU, production config hay dữ liệu trẻ thật.

## Câu hỏi mở cho owner

- Stroke có hai điểm trùng nhau hiện vẫn được chấp nhận; quyết định spec mới chưa có.
- Kích thước export 1024 và tham số render thuộc profile v1 hay T4/T5/version sau.
- Checkpoint snapshot vẫn là dictionary tự do; T4 phải dựng export từ accepted operations, không tin snapshot.

## G1 closeout

- Group validators: HARNESS_VALID; REPOSITORY_SECURITY_VALID; ARCHITECTURE_VALID; `git diff --check` clean. See `status/PILOT_GOAL_LEDGER_20261101.md` for the recorded commands and full G1 summary.
- Local ignored snapshot: `.claude/handoff/snapshots/G1_20261101T115654/`.

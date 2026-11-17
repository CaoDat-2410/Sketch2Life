# T2 — Child canvas reconnect report

- Status: XONG-CHƯA REVIEW.
- Plan: plan/T2_CHILD_CANVAS_RECONNECT_IMPLEMENTATION_PLAN_20261101.md
- Plan SHA-256: 4DFD74DD41B433ED85C9BA3C6FDA4946A4E1B8304E438A136FDD09A8D8657E6B
- Approval: G1 T2 entry in approvals/TASK_APPROVAL.md.
- Layers: L1/L2 reuse the existing typed status-read and eligibility decisions; L5 changes reconnect response/route. No persistence or migration change.

## Implemented

- Reconnect authenticates through get_verified_device_status, which binds organization/session path parameters to the admitted grant and requires an admitted membership.
- The route derives the group from that membership and applies the current typed legal-or-synthetic eligibility gate before returning group canvas data.
- Active and paused sessions are supported without requiring an active Child turn. A matching current turn is returned when present; otherwise turn_id is null. Empty canvas revision is 0 and the initial epoch is 1.
- Finished sessions, invalid/revoked credentials, foreign session paths, revoked/expired proofs, non-admitted membership, and missing group remain denied. The write guard and legal-only routes were not broadened.
- The stale helper docstring was corrected to describe its actual two call sites: stroke append and reconnect.

## Test evidence

- Test-first red observations recorded earlier: one contract failure and three reconnect PostgreSQL failures before the route used the status-read path.
- Final combined CPU/offline baseline and G1 contract/unit set: 267 passed, 4 skipped.
- Final isolated PostgreSQL synthetic-pilot module: 31 passed, including active/paused no-turn reads, scoped turn response, foreign path, revoked grant, finished session, and revoked/expired proof denials.
- One intermediate expired-proof test setup violated the existing expires_at > issued_at database CHECK. The fixture now moves issued_at earlier than expires_at while keeping the proof expired; the focused case passed and the final full module passed.
- Ruff lint passed. Ruff format passed for 9 files; see the T3 report for the unrelated pre-existing formatter suggestion in test_app_composition.py.
- Strict mypy comparison against HEAD-source shadows found no new errors; the current and baseline runs each report the same 5 existing router diagnostics.

## HỢP ĐỒNG CHO UI

Child dùng grant và device key của chính mình:

```http
GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect?after_revision=0
X-Be1-Grant: <device-grant>
X-Be1-Device-Key: <device-key>
```

Ví dụ response tổng hợp đã khớp schema và response của test synthetic:

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

Session `active` và `paused` đều cho phép Child admitted đọc canvas của nhóm mình khi grant, membership và eligibility còn hiệu lực; không cần turn active. Khi không có active turn, `turn_id` là `null`. Session cũ không có profile trả `profile_version: null`, không được tự gán profile. Child không gửi lại request chỉ vì reconnect bị từ chối; giữ request reference hiện có và chờ trạng thái/điều phối phía người lớn. Session `finished`, grant bị thu hồi/khóa xoay, membership không admitted, group không tồn tại hoặc eligibility không còn hợp lệ vẫn bị từ chối.

Schema cho phép `turn_id` nullable. `apps/child-ui/src/services/sessionClient.ts` hiện vẫn khai báo `turn_id: string` và chưa có `profile_version`; đây là việc cần UI sửa sau, không thuộc allowlist G1 review-fixes. UI code và visual AC20 vẫn DEFERRED-BY-OWNER / NOT RUN.

### R4 bổ sung kết quả kiểm

- R0 trước review đã ghi 267 passed, 4 skipped và 31 passed cho module PostgreSQL. Đây là số lịch sử của lần G1 trước.
- R4 chạy lại module PostgreSQL synthetic-pilot trên DB acceptance loopback: **48 passed**. Bản HEAD archive có **4 passed** trong module cũ hơn. Không chạy migration.
- Bộ CPU/offline hiện tại sau review: **294 passed, 4 skipped**; HEAD archive: **227 passed, 4 skipped**. Full unit/full contract và giới hạn môi trường được tổng hợp trong `evidence/G1_REVIEW_FIXES_REPORT_20261101.md`.

Không dùng migration, artifact/rendering, provider, Modal/GPU, hoặc dữ liệu trẻ thật.

## G1 closeout

- Group validators: HARNESS_VALID; REPOSITORY_SECURITY_VALID; ARCHITECTURE_VALID; `git diff --check` clean. See `status/PILOT_GOAL_LEDGER_20261101.md` for the recorded commands and full G1 summary.
- Local ignored snapshot: `.claude/handoff/snapshots/G1_20261101T115654/`.

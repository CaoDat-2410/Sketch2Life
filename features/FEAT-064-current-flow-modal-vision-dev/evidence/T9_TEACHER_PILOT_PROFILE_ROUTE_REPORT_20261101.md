# T9 — Teacher session-scoped pilot profile route report

- Status: XONG-CHƯA REVIEW.
- Plan: plan/T9_TEACHER_PILOT_PROFILE_ROUTE_IMPLEMENTATION_PLAN_20261101.md
- Plan SHA-256: D9BD291A35F7C97E07632C7953D2A58469A7D6FE9F52F77D7260B8117FD941BC
- Approval: original G1 T9 approval plus append-only route-surface correction in approvals/TASK_APPROVAL.md.
- Layers: L1 typed response schema and L5 HTTP route. No migration/composition wiring change.

## Implemented

- Added GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles.
- Requires an assigned teacher or school_admin, a session in lobby, local/test environment, and synthetic pilot enabled.
- Returns only child_id and display_name for active SYNTHETIC_DEV profiles whose proof matches organization, class, child, purpose, exact session, expected schema/origin, current validity interval, and unrevoked state.
- The route does not use pilot_run_ref as an authority boundary and does not return age, consent, proof identifiers, evidence, or eligibility rationale.
- Existing class-wide legal-only profile listing remains unchanged.

## Test and static-check evidence

- Before route implementation, the response-schema contract test failed because the response type was absent. The T9 PostgreSQL filter showed 13 failures and 1 passing foreign-scope denial; after implementation the T9 cases passed.
- Final combined CPU/offline baseline and G1 contract/unit set: 267 passed, 4 skipped.
- Final isolated PostgreSQL synthetic-pilot module: 31 passed, including the scoped route, invalid/expired/revoked proof, profile/session/org/class scope, disabled pilot/environment, non-lobby session, and assignment cases.
- The compatibility route-surface assertion allows exactly the new path. The T9 plan was revised and its approval append-only addendum pins SHA-256 D9BD291A35F7C97E07632C7953D2A58469A7D6FE9F52F77D7260B8117FD941BC.
- Ruff lint passed. Ruff format passed for 9 files; test_app_composition.py retains an unrelated pre-existing formatter suggestion outside the one-line approved route addition.
- Strict mypy comparison against HEAD-source shadows found no new errors; both runs report the same 5 existing router diagnostics.

## HỢP ĐỒNG CHO UI

```http
GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles
Authorization: Bearer <adult-session-token>
```

Response tổng hợp khớp response model và test synthetic:

```json
{
  "contract": "Be1PilotProfileListV1",
  "items": [
    {"child_id": "synthetic-child-0000000000000000000000000", "display_name": "Synthetic Child"}
  ]
}
```

Danh sách chỉ trả `child_id` và `display_name`; có thể là `items: []`. UI không được suy ra consent/eligibility từ item và không fallback sang route class-wide legal-only để lấy synthetic profile. Item chỉ là candidate cho admission tiếp theo; không tự cấp grant/admission.

| HTTP | Tình huống | Thứ tự/ghi chú |
|---|---|---|
| 401 | Adult auth thiếu hoặc không hợp lệ | Auth chặn trước route. |
| 404 | Organization/session không tìm thấy | Session lookup chạy trước assignment check. |
| 403 | Role hoặc class assignment không được phép | Sau khi session được tìm thấy, assignment được kiểm trước các điều kiện route 409. Teacher chỉ được assignment lớp khác sẽ bị từ chối. |
| 409 | Pilot tắt/không ở local-test hoặc session không ở lobby | Chỉ xét sau assignment; mã là `PILOT_PROFILE_LOOKUP_UNAVAILABLE` hoặc `SESSION_NOT_IN_LOBBY`. |
| 422 | Path/request validation không hợp lệ | Framework validation boundary; không trả candidate list. |

No Teacher UI code was changed; L6 and visual AC20 remain DEFERRED-BY-OWNER / NOT RUN.

### R4 bổ sung kết quả kiểm

- R0 trước review đã ghi 267 passed, 4 skipped và 31 passed cho module PostgreSQL. R4 chạy lại hiện tại: CPU/offline **294 passed, 4 skipped**; PostgreSQL synthetic-pilot **48 passed**. HEAD archive tương ứng: 227/4 và 4 PG pass.
- Full contract suite hiện tại: **1,381 passed**. HEAD archive: 1,378 passed, 1 failure trong `test_sketch_review_contracts.py` vì archive `git archive` không có `.git`; `test_openapi_contract_catalog.py` pass tại HEAD và catalog hiện tại pass sau khi allowlist chính xác một pilot-only route.
- Không thay đổi profile/proof issuance hoặc revoke, admission, migration, provider, Modal/GPU, hay dữ liệu trẻ thật.

## G1 closeout

- Group validators: HARNESS_VALID; REPOSITORY_SECURITY_VALID; ARCHITECTURE_VALID; `git diff --check` clean. See `status/PILOT_GOAL_LEDGER_20261101.md` for the recorded commands and full G1 summary.
- Local ignored snapshot: `.claude/handoff/snapshots/G1_20261101T115654/`.

# Claude review rev2 → rev3 — 2026-10-29

Owner cung cấp review rev2, verdict NEEDS_REVISION, 0 P1, 1 P2. Phần đầu ghi 5 P3 nhưng phần findings liệt kê **sáu** mục P3-1–P3-6; xử lý tất cả sáu. Rev2 được review có SHA-256 `F321EE9FECF0870D52CC25B50F51B510F8046938A6D9AB99F188534DB9C7290F`, snapshot nguyên bytes tại `PLAN_REV2_REVIEWED_20261029.md`. Active rev3 plan SHA-256 `53573E2A35CECCE08889F3C0C62072B1E92935353D79153574CF04774CD115BC`.

| Finding | Disposition rev3 |
| --- | --- |
| P2-1 restore ledger | Witness atomic/durable, độc lập DB/backup, dùng chung worker; claim witness trước DB reserve và outbound. Mọi crash/ambiguous sau claim đốt lượt; không rollback/refund. M3 blocked nếu independence chưa chứng minh. Receipt chỉ sau DB commit có cửa sổ crash, không đủ. |
| P3-1 deadline | Pin attempt budget tính elapsed pre-send + enforced HTTP wall deadline + completion margin; kiểm tra timeout Modal riêng. `urlopen(timeout)` chưa chứng minh wall-clock limit. Sweep/late response fail-closed và UNKNOWN sau possible-send. |
| P3-2 UNKNOWN | Projection hiển thị chưa rõ/chờ operator, không nút retry hoặc resubmit; tách A1 accounting, test lost reply/reload và permissions. |
| P3-3 guard ownership | T6 contract InvocationGuardPort, T7c implement ledger/witness, T8 wire outbound; fail-closed và counting tests, không bypass C1/C2. |
| P3-4 inventory | Canvas guard callers, artifact download consent, START consent_ready và core_foundation được bổ sung; download chưa chắc là route preview pilot, caller ngoài lifecycle phải xác minh T0. |
| P3-5 UoW methods | T0 inventory theo từng method, mutation cần durable/atomic, pure read có contract đúng; unsupported fail-closed, không no-op. Không nhận full BE2 scope. |
| P3-6 status lifetime | OD-3/T0 chốt lifetime sau turn/pause/session finish với expiry/revoke; chưa quyết thay owner. |

Hai reviewer độc lập đã kiểm tra scope P2/deadline và source locators/guard/UoW. Nhận xét được tích hợp; chưa có Claude PASS cho rev3. Không chạy runtime, DB, app, GPU hay provider; không sửa approval hoặc source. OD-1–OD-4 vẫn mở.

## Checks

`validate_skeleton.py`: SKELETON_VALID. `validate_repository_security.py`: REPOSITORY_SECURITY_VALID (5705 publishable files tại thời điểm quét). `git diff --check`: exit 0. Active plan hash và approval hash khớp record; approval chưa sửa. Harness không chạy lại cho delta tài liệu này; kết quả rev2 vẫn HARNESS_INVALID do các evidence paths ở FEAT-043/063 như record rev2, không khẳng định trạng thái hiện tại đã được kiểm tra lại. Không có runtime/DB/provider tests.

# Review rev3 → rev4 — 2026-10-29

Claude review đúng rev3 hash `53573E2A35CECCE08889F3C0C62072B1E92935353D79153574CF04774CD115BC`: NEEDS_REVISION, 1 P2 / 2 P3. Snapshot nguyên bytes tại `PLAN_REV3_REVIEWED_20261029.md`. Active plan rev4 SHA-256 `E109585296D9A937319C16EE2A0B7305D8577FE3E6A42B593A9877FE42385E7A`.

| Finding | Disposition |
| --- | --- |
| P2-1′ | AC18, run/preflight và contract đều yêu cầu witness; T0 chỉ đặc tả test plan, T7c/T12 sau approval thử bằng witness/run throwaway, M3 yêu cầu evidence, witness live chỉ tạo sau T12 + live approval. |
| P3-A | UNUSED phải hiện hữu/xác minh, consume atomic; missing/unreadable/mismatch/rollback không chắc đóng. Single-host local witness chỉ là phương án OD-3 nếu độc lập DB backup và các bảo đảm được chứng minh, không mặc định rename/file đủ. |
| P3-B | Worker thua có NOT_SENT_CAP_CLOSED chỉ khi xác minh consumed; unavailable/mismatch là NOT_SENT_CAP_UNAVAILABLE. Crash trước claim chỉ để cap mở nếu chứng minh zero-send và cả hai còn UNUSED; không auto retry. Possible-send 5xx/URLError/reset/timeout hoặc response mơ hồ là UNKNOWN. Typed failure không đủ chứng minh non-execution; không mặc định status 401/403/404/422 là known, cần contract xác thực. Runtime boundary phải bảo toàn provenance cần thiết hoặc default UNKNOWN. |

Một reviewer độc lập đối chiếu thêm các nuance witness và adapter. Đây là cập nhật tài liệu, chưa có Claude PASS rev4 hoặc owner approval; chưa thử witness, DB, backend hay Modal. OD-1–OD-4 vẫn mở. Approval file không đổi.

## Static checks

`validate_skeleton.py`: SKELETON_VALID. `validate_repository_security.py`: REPOSITORY_SECURITY_VALID, 5707 publishable files lúc quét. `git diff --check`: exit 0. Plan hash khớp record; approval hash `71514E7F2BDA2AAE96374135FE6DE450F15816567191DBBF74B4F23EAA0B5A8B` không đổi. Harness không chạy lại ở rev4; rev2 có HARNESS_INVALID do evidence paths FEAT-043/063, không suy ra kết quả hiện tại. Không có runtime/DB/provider tests.

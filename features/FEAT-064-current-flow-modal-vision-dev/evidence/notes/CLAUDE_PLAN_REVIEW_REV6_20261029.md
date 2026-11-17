# Claude review rev5 → rev6 — 2026-10-29

Chủ task cung cấp Claude review rev5 `PLAN_REVIEW_PASS` kèm P3 cần sửa trước approval. Rev5 SHA-256 `D457DC5DC2E75890E8ACC0BB59DA6C0F354BA118E196D0A1CFC46B677E85BF6B`; snapshot nguyên bytes `PLAN_REV5_REVIEWED_20261029.md`. Rev6 active SHA-256 `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`.

Khôi phục các tiêu chí của rev4 vào acceptance của T0 (từng consent call site/profile fields, DB/run identity, approval đúng revision/task), T6 (guard C1/C2 và missing/refuse/error không send), T8 (không bypass transport, max_attempts=1, UNKNOWN không attempt mới) và T13 (đúng nguồn/provenance, Teacher pending); vẫn giữ các yêu cầu mới của rev5.

Ghi chú restore: T0 đặc tả nguồn evidence và operator ghi lịch sử restore trong manifest; lời khai đơn thuần không chứng minh DB chưa rollback. Thiếu bằng chứng đáng tin cậy mặc định UNKNOWN/cap đóng. Không thay quyết định OD-3=B hoặc approval.

Rev6 DRAFT/NOT_STARTED, chưa được Claude review; approval AWAITING_APPROVAL không đổi. Không thực thi source/DB/witness/Modal.

## Static checks

`validate_skeleton.py`: SKELETON_VALID. `validate_repository_security.py`: REPOSITORY_SECURITY_VALID, 5712 publishable files lúc quét. `git diff --check`: exit 0. Hash active plan/snapshot rev5 khớp record; approval giữ SHA-256 `71514E7F2BDA2AAE96374135FE6DE450F15816567191DBBF74B4F23EAA0B5A8B`. Không chạy harness, application/DB/provider tests.

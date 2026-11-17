# Plan Rev50A — đồng bộ backlog lịch sử với roadmap — 2026-11-03

## Mục tiêu

Áp dụng phần N7 của review vòng 2 vào bảng disposition B0–B13 trong backlog lịch sử. Roadmap sáu mốc là mapping điều phối hiện hành; backlog vẫn là DRAFT, không phải goal hay approval triển khai.

## Baseline

- Branch/HEAD/index: `feature/feat063-be-foundation` / `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9` / rỗng.
- Backlog: `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md`, SHA-256 `2CAB64B6F45F2B1851F0B3AFD11ADD623A3D6BFD125D70908EF9617E74B62118`.
- Roadmap hiện hành: `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md`, đang được cập nhật theo Plan Rev50.

## Phạm vi duy nhất

- Trong bảng “Disposition sau khi chuyển sang StoryRun-lite”, chỉ sửa hàng B4b, B10 và B13 để đồng bộ với roadmap hiện hành: B4b chờ OI-05..08 và từ chối `REAL`/`LEGACY_UNCLASSIFIED` trước khi consent gate đạt; B10 chia M2 job/idempotency, M5 Parent quota/usage/compute admission, M6 commerce và Teacher/school expansion; B13 phản ánh Q146 đã answered nhưng lịch/model/safety gates vẫn cần quyết định và M6 giữ Teacher/org/roster/capacity.
- Thêm một dòng ở phần điều phối đầu bảng trỏ rõ về roadmap sáu mốc mới nhất.
- Giữ nguyên mọi hàng khác và phần backlog lịch sử.

Không sửa B0–B13 redistribution plan/report, SRS, DTR, source, test, migration hoặc file nào khác. Không DB, Modal/provider/network, Git history/index/remote, test/validator suite, stage/commit/push/merge.

## Tiêu chí chấp nhận

- Backlog gọi đúng đây là lịch sử/DRAFT; current milestone mapping trỏ về roadmap.
- B4b, B10, B13 không mâu thuẫn với roadmap; không cấp consent, quota, model hoặc implementation approval.
- Chỉ đúng file backlog đổi; `git diff --check` sạch và index/HEAD giữ nguyên.

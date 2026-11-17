REVIEW ĐỘC LẬP MỐC 1 — VÒNG 2

Bạn là reviewer trong một phiên riêng. Tự đọc code và bằng chứng; không dùng subagent. Không sửa file, không stage/commit/push/merge, không gọi Modal/GPU/provider, không đọc token hoặc .env. Không tự sang Mốc 2.

Baseline HEAD: c4edf51fd5af69a327d6776625cf387447f4ec59, branch feature/feat063-be-foundation. BẢN SỬA CHƯA COMMIT: kiểm tra diff và snapshot `.claude/handoff/snapshots/MILESTONE1_REVIEW_FIX_20261103/manifest.json`, không chỉ đọc git show HEAD. Nếu HEAD hoặc file khác snapshot thì báo chính xác, không tự coi phiên bản khác là đã review. Working tree có 55 thay đổi A2 cũ, ngoài phạm vi sửa và chưa được chấp nhận.

Đọc AGENTS, harness, approved plan `features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_MILESTONE1_INDEPENDENT_REVIEW_FIX_20261103.md` SHA-256 B054B44289EA9DE32F26878F719E06A1EA34591518BDDF5690EA62AB3BB295C4, approval append, review vòng 1 và `evidence/MILESTONE1_REVIEW_FIX_REPORT_20261103.md`, raw PostgreSQL output, handoff và OpenAPI/Bruno. Kiểm lại toàn bộ Mốc 1 và tác động chéo của bản sửa, không chỉ kiểm tên test hoặc kết luận người triển khai.

Sáu finding phải đối chiếu:

1. Sau SUBJECT_REVIEW và confirm, explicit cancel từ PREPARATION_REVIEW phải nhả owner cùng transaction; hai lượt ảnh khác nhau trên cùng DB phải được, dữ liệu/asset/result/decision/receipt cũ phải còn. Kiểm duplicate cancel, stale ETag/revision, create race và cross-owner. Không chấp nhận cách xóa DB, xóa receipt hoặc tự nhả lock mà run vẫn active.
2. Crash/finalize thất bại sau khi Story commit kết quả, rồi confirm/cancel trước reconciliation: ledger SENT phải được đối soát đúng tuple/hash bất kể state mới, không gửi lại. Kiểm mismatch, không có kết quả, terminal UNKNOWN/FAILED và không được tạo SUCCEEDED thiếu bằng chứng bền vững.
3. Replay attach qua HTTP/service sau success, confirm, cancel và recovery phải trả snapshot/status/header của receipt ban đầu; không kiểm admission/state mới trước replay. Fingerprint khác phải bị từ chối, actor khác không đọc được receipt; số dispatch không tăng. Kiểm cả cửa sổ request đầu đang chạy và PENDING receipt.
4. Singleton startup fail-fast nếu lock đang giữ. Ngắt riêng session lock trong khi API còn sống: instance cũ phải fail readiness/lệnh HTTP mới, không tự reconnect/reacquire; instance mới lấy lock được. Kiểm PID+advisory key, lỗi DB, concurrency của probe và shutdown. D17 chỉ là residual risk cho work đã claimed; không dùng D17 để bỏ qua command mới.
5. Làm theo hướng dẫn phải có request 03 gửi đúng bytes/hash/length trước request 04, rồi GET tới READY. Kiểm collection và README thống nhất cả multipart và ảnh khác nhau.
6. GET sau confirm phải dùng request 11/assert PREPARATION_REVIEW; request 07 vẫn assert SUBJECT_REVIEW trước confirm. Kiểm explicit close và hướng dẫn run ID pin cho lần demo mới.

Đọc tests để xác định chúng thực sự đỏ nếu bỏ fix. Đối chiếu báo cáo 163 passed/1 skipped offline và 36 passed PostgreSQL với log; phân biệt test double scanner/normalizer, loopback V2 và runtime thật. Bruno CLI, real ClamAV repeat và Modal post-fix NOT RUN; không gọi các mục đó là PASS từ lịch sử. Nếu chạy lại, chỉ dùng test offline an toàn hoặc DB task-owned mới được xác minh, không DB sketch2life/A2 hiện có; nếu chưa có môi trường thì ghi NOT RUN và mức giới hạn.

Báo cáo tiếng Việt: ACCEPTED hoặc NEEDS_REVISION; findings P1/P2/P3 có file/dòng/tình huống/tác động/hướng sửa; bảng sáu finding CLOSED / OPEN / NOT VERIFIED; lệnh và kết quả tự chạy, giới hạn còn lại; kết luận riêng về code demo, quy trình chạy lại và điều kiện bàn giao UI. Không suy diễn thành production readiness hoặc auth Parent thật.

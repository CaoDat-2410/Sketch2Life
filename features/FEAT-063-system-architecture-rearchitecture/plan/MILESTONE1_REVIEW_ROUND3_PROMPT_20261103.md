# Prompt review độc lập vòng 3 — StoryRun-lite Mốc 1

Bạn là reviewer độc lập trong một chat Codex riêng. Đây là review chỉ đọc; không dùng subagent. Không sửa file, không chạy test, không kết nối/chạy/reset database, không gọi Bruno, ClamAV, Modal, GPU, provider hoặc mạng ngoài; không stage, commit, push hay merge.

## Cổng hash và checkout

Trước khi review, tính lại và đối chiếu:

- Plan được duyệt: `plan/STORYRUN_LITE_MILESTONE1_INDEPENDENT_REVIEW_FIX_20261103.md`, SHA-256 `B054B44289EA9DE32F26878F719E06A1EA34591518BDDF5690EA62AB3BB295C4`.
- Báo cáo round 2: `evidence/MILESTONE1_REVIEW_ROUND2_FIX_REPORT_20261103.md`, SHA-256 `3924764318499A58A51101B56E5C26D698999A784B7B5C77E62F41A89DE38AE2`.
- Snapshot bổ sung: `.claude/handoff/snapshots/MILESTONE1_REVIEW_ROUND2_CLOSEOUT_20261103/manifest.json`, SHA-256 `0E5096FB7A7AF169EB35115209DB271A3F7F58DA809166DCCF7087DC7B1B024D`; kiểm từng path trong `hashes.csv` với bytes hiện tại.
- HEAD dự kiến: `c4edf51fd5af69a327d6776625cf387447f4ec59`, branch `feature/feat063-be-foundation`, index rỗng lúc closeout.

Nếu bất kỳ hash hoặc checkout gate nào lệch, dừng và báo cụ thể. Review working tree hiện tại cùng snapshot; HEAD một mình không chứa các sửa đổi chưa commit. Bản review vòng 2 gốc đã chuẩn hóa nằm ở `evidence/MILESTONE1_INDEPENDENT_REVIEW_ROUND2_20261103.md`, SHA-256 `CB3B6E0DCF1789BCF22D0E6D7C52952DF9E0EA02BF15DEC9DEB74EACE4BA20C8`; review vòng 1 và báo cáo round 1 cũng được giữ trong `evidence/`. Snapshot `hashes.csv` SHA-256 là `7B412A4B04E04E3B931AEA00B08072470C51B77905CDFC0D38155062FBB796E0`.

## Phạm vi review

Đối chiếu đủ sáu finding vòng 1 và hai P2 mới của round 2. Kiểm tra source, PostgreSQL/HTTP tests, contract/OpenAPI, README/Bruno và evidence; không chỉ dựa vào báo cáo.

1. **P1 — chạy demo lượt tiếp theo sau confirm.** Xác minh PREPARATION_REVIEW có thể đóng bằng cancel hiện có, DELETE_PENDING và nhả active owner atomically; dữ liệu result, asset, receipt vẫn được giữ. Xem race cancel/create theo cả hai thứ tự, duplicate cancel, stale version/revision và hai lượt ảnh synthetic khác nhau trên cùng DB.
2. **P2 — reconcile ledger sau khi Story đã commit.** Kiểm tra identity run/job/attempt, revision và canonical/raw hashes; chỉ finalize ledger phù hợp khi SENT; kết quả còn được nhận diện khi state chuyển qua confirm/cancel; mismatch không finalize và không dispatch lại.
3. **P2 — attach replay, gồm TOCTOU vòng 2.** Xác minh scope actor/run/key/fingerprint, replay trả snapshot receipt gốc; khi lần lookup đầu miss rồi mutable target/admission check thất bại, durable recheck có serialization đúng và không dispatch thêm. Kiểm tra cả final receipt và PENDING recovery hold qua HTTP/PostgreSQL concurrency test; actor hoặc fingerprint khác không được lộ receipt.
4. **P2 — singleton và public readiness.** Xác minh startup lock không chờ; probe kiểm tra đúng backend session và advisory lock; mất lock phải latch unready và không reacquire. GET `/v1/story-runs/readiness` phải gọi runtime probe, trả 503 sau khi terminate session lock thật; `/health` vẫn chỉ là liveness. Kiểm tra probe concurrency và instance mới lấy được lock sau khi instance cũ mất session.
5. **P2 — Bruno upload bytes.** Đối chiếu README và request 03: gửi đúng bytes, kiểm tra content length/hash trước request complete, không chỉ upload một metadata stub. Đánh giá hai lần Bruno được ghi nhận và phân biệt stub Vision với provider thật.
6. **P3 — GET sau confirm.** Request 07 vẫn kiểm SUBJECT_REVIEW trước confirm; request 11 riêng phải kiểm PREPARATION_REVIEW sau 202. Kiểm trạng thái đó trong cả hai lượt Bruno.

## Bằng chứng cần phân loại chính xác

- Offline: 170 passed, 1 PostgreSQL-dependent skip; raw output đã chuẩn hóa ở `evidence/MILESTONE1_REVIEW_ROUND2_OFFLINE_20261103.log`.
- PostgreSQL 17.11 task-owned: 46 passed, không skip/timeout; raw output ở `evidence/MILESTONE1_REVIEW_ROUND2_POSTGRES_20261103.log`.
- Bruno: hai lượt, mỗi lượt 11/11 requests/tests; ClamAV thật và Windows Job Object image normalizer; Vision là HTTP loopback stub. Bảng status code đã khử định danh ở `evidence/MILESTONE1_REVIEW_ROUND2_BRUNO_SUMMARY_20261103.json`.
- Mypy chỉ được xác nhận sạch cho năm production source modules trong report; không suy rộng ra toàn repo hoặc test modules.
- Modal/GPU/provider không chạy sau fixes. Smoke Modal thành công trước đó là bằng chứng lịch sử, không phải kiểm chứng post-fix.
- 55 đường dẫn local A2 trước đó được so hash và khớp 55/55. Mốc 2 và A2 không thuộc scope này.

## Đầu ra review

Trả một trong hai verdict: **ACCEPTED** hoặc **NEEDS_REVISION**. Với mỗi finding còn mở, nêu severity, file/line hiện tại, tình huống cụ thể, vì sao test/evidence chưa chứng minh, và tiêu chí đóng. Nếu chấp nhận, ghi rõ sáu finding vòng 1 và hai finding round 2 đã được review trên working tree và snapshot cụ thể. Không tự sửa hoặc nới scope.

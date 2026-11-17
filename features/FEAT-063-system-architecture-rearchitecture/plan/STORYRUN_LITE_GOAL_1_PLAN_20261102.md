# Goal 1 — StoryRun-lite API contract và Parent synthetic với Vision giả

Ngày 2026-11-02. **DRAFT / AWAITING_APPROVAL cho implementation.** Đây là plan để giao cho phiên implementer, không phải approval record hay bằng chứng test. Owner yêu cầu xử lý review V11 một lượt, không mở thêm vòng review M0, rồi chuẩn bị goal. Kết luận reviewer cho V11 là NEEDS_REVISION; bản sửa V12 chưa được review lại và không được gọi là ACCEPTED.

## Mục tiêu và nguồn ghim

Hoàn thành một lát cắt BE để người khác ghép UI: một Parent synthetic tạo run → chọn và upload ảnh synthetic JPEG/PNG/WebP khác nhau mỗi lần → scanner → admission/normalize → fake Vision → xem subject → CONFIRM hoặc cancel, kiểm bằng OpenAPI và Bruno. Không gọi provider. Goal 2 mới nối photo bridge A1 và test loopback; Modal live là bước riêng sau readiness và approval riêng.

- Nhánh lúc soạn: `feature/feat063-be-foundation`; HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`.
- Bản thiết kế áp dụng: `plan/STORYRUN_LITE_VISION_M0_V12_FINAL_DRAFT_20261102.md`, SHA-256 `D0560C4B7821EA76A50780D00161DE1D1AC9917168B9C975547077C457FB448B`; §10 là quyết định owner mới nhất, thay các dòng lịch sử fixture-only; §9 áp dụng khi không trái §10. Tính lại hash trước chạy, lệch thì dừng.
- Báo cáo review V11 `evidence/STORYRUN_LITE_VISION_M0_V11_INDEPENDENT_REVIEW_20261102.md`, SHA-256 `755FF00669104900B1F728C35107ABEE123BC31B65D258900508A7CA3C51F1A5`; handling `evidence/STORYRUN_LITE_VISION_M0_V11_CHANGES_20261102.md`. Đọc AGENTS, harness, FEAT-063 context/decisions/source register/approval, SRS và DTR liên quan.
- A2 đang tạm dừng, working tree có file A2/baseline chưa commit. Bảo toàn nguyên vẹn, kể cả snapshot `.claude/handoff/snapshots/CLAUDE_A2_PAUSE_20261102T121212`. Không dùng/dọn DB A2. Không coi toàn bộ thay đổi local là của Goal 1.

## Giới hạn demo và cổng trước implementation

Owner xác nhận người demo được chọn nhiều ảnh synthetic khác nhau ở UI, định dạng JPEG/PNG/WebP. Không áp dụng allowlist hash fixture cho ảnh đầu vào; fixture có hash chỉ dùng trong kiểm thử. Mục tiêu ảnh gốc ≤20 MiB/40 MP, chia tối đa 5 part 4 MiB theo SRS; nếu môi trường chưa chứng minh được thì báo giới hạn thực và blocker. Không nhận dữ liệu trẻ thật. Scanner thật phải CLEAN trước parser/model; metadata/decode/normalize phải chạy worker process có thể kill và có OS resource limit. FEAT-018 hiện dùng PyAV in-process, chưa có bảo đảm đó; profile ảnh mới phải additive và không phá behavior canvas cũ.

Owner đã chọn phạm vi nhiều ảnh synthetic và yêu cầu tiếp tục goal. Trước khi sửa source/migration, implementer lập plan hẹp với file allowlist thực tế, scanner thật, worker isolation và enforcement, ảnh synthetic test, DTR/migration, disposable DB và acceptance; ghi approval đúng nguồn/scope trong `approvals/TASK_APPROVAL.md` theo AGENTS/harness. Nếu chưa có approval cụ thể hoặc không được phép ghi record, dừng phần implementation phụ thuộc. Không thêm vòng review M0 theo chỉ thị owner. A1 shared bridge không thuộc Goal 1; Q3-B+ overlap vẫn được ghi rõ, không coi nhiều ảnh là duyệt xử lý dữ liệu trẻ thật hay gọi Modal.

## Kết quả, phụ thuộc và acceptance

| ID | Việc | Phụ thuộc | Kết quả và điều kiện hoàn tất | Cỡ / rủi ro |
|---|---|---|---|---|
| G1-0 | Baseline | Không | Xác nhận HEAD/index/branch, hash các nguồn, snapshot file sẽ chạm; khoanh A2. Xử lý path đích trùng hoặc source drift bằng cách dừng/báo. Tạo môi trường cô lập hoặc snapshot đầy đủ; không overwrite file local. | Nhỏ; working tree bẩn. |
| G1-1 | Contract đầu tiên | G1-0 | Trước code, xuất OpenAPI `StoryRunLite-v1` và collection Bruno skeleton/examples theo V12 10 operation để người ghép UI bắt đầu. Contract chứa giới hạn server, errors, state, idempotency, cancel và UNKNOWN. Đánh dấu draft cho tới khi contract được freeze; không chứa secret. | Vừa; thay đổi contract. |
| G1-2 | Khảo sát môi trường + plan implementation | G1-0/1 | Xác định scanner thật, Windows Job Object hoặc container có giới hạn hiệu lực, WebP và disposable PG; ghi VERIFIED/NOT VERIFIED/BLOCKED. Chuẩn bị nhiều ảnh test synthetic khác nhau có provenance/hash; đầu vào sản phẩm không bị ghim hash. Liệt kê file cụ thể, migration/DTR, giới hạn runtime và acceptance; hash plan và ghi approval trước implementation. | Lớn; khả năng môi trường chưa có scanner/isolation. |
| G1-3 | DTR/migration và storage | G1-2 + approval | Amend DTR đầy đủ theo V12 §9.6, hai receipt authority; typed owner scope và compatibility/trigger theo §9.3; migration chỉ trong DB disposable riêng được duyệt. Tránh org giả, no runtime backfill, bảo toàn legacy. | Lớn; schema/writer compatibility. |
| G1-4 | Upload và admission | G1-3 | 5 upload operations, 1..5 part ≤4 MiB, tổng ≤20 MiB, aggregate SHA/receipts và cùng snapshot; scanner thật CLEAN trước parser, worker cô lập giới hạn OS cho metadata/decode/normalize, JPEG/PNG/WebP ≤40 MP; scanner fail → FAILED/session mới. Giữ original, derived hash/lineage; abort/expiry cleanup best-effort. Core recovery §9.4. | Lớn; scan, resource isolation và crash/race. |
| G1-5 | Story API + fake Vision | G1-3/4 | 5 Story operations gồm create/attach/GET/CONFIRM/cancel; fake Vision, receipt, Story UoW, revision/CAS, UNKNOWN hold không auto resend; Story crash recovery §9.4. Không thêm A1 hook hay gửi HTTP provider. | Lớn; receipt và cancel race. |
| G1-6 | Bruno, checks và bàn giao | G1-4/5 | Chạy acceptance bên dưới, các test phù hợp và validators theo plan, ghi số thật và snapshot; bàn giao `XONG-CHƯA REVIEW` Goal 1. Không tự chạy Goal 2. | Vừa; môi trường disposable. |

Critical path: G1-0 → G1-1 → G1-2 → G1-3 → G1-4 → G1-5 → G1-6. Người ghép UI có thể dùng OpenAPI/Bruno sau G1-1 để bắt đầu, nhưng phải theo dõi contract freeze và trạng thái môi trường scanner/worker. Không chạy các bước sửa cùng file song song.

Ước lượng rất thô sau khi mở phạm vi nhiều ảnh: Goal 1 khoảng **3–6 ngày làm việc**, Goal 2 khoảng **2–4 ngày**, trước review/fix và thời gian chờ. Có thể tăng thêm 30–100% do review/fix; đây không phải benchmark hay cam kết, đặc biệt phụ thuộc ClamAV, worker isolation trên máy đích, migration và disposable DB. Mốc cũ của V12 §6.2 tính cho fixture-only và không còn là ước lượng hiện hành.

## Acceptance bắt buộc

1. OpenAPI và Bruno nêu đủ 10 operations và versioned DTO/status/error/header; client nhận `max_total_bytes`, `part_size_bytes`, `max_parts` từ server, các format JPEG/PNG/WebP, 20 MiB/40 MP và ví dụ happy/error.
2. Nhận nhiều ảnh synthetic khác hash; dùng cùng immutable snapshot cho hash/scan/decode. Test một, hai và năm part, continuity, part retry/conflict/thiếu part, aggregate SHA và 20.971.520/20.971.521 bytes tại upload layer; byte giả để test giới hạn không đi tới decoder/Modal. Hash fixture test không trở thành allowlist sản phẩm.
3. Scanner thật CLEAN trước parser/model; fail/timeout/unavailable/infected → FAILED, không decode/asset/Vision; thử lại bằng session mới. Unit dùng stub để test nhánh; live readiness phải có bằng chứng scanner thật. Không dùng synthetic attestation để thay quét với ảnh được chọn tùy ý. Không dữ liệu trẻ thật.
4. Receipt Story/Core theo V12 §9.7: same identity/key/fingerprint replay nguyên snapshot; cùng identity/key với fingerprint khác → 400; key khác không mặc định conflict. PUT part dùng natural key/digest; stale revision 409.
5. Core crash trước ack/FINAL và sau FINAL 202 trước gate: recovery FAILED, replay 409 hoặc nguyên 202 đúng trường hợp, không dispatch lại, worker cũ bị CAS chặn asset. Story attach hai cửa sổ tương tự ra hold + stable replay, không tự dispatch lại. Test concurrency/race theo §9.4.
6. Bruno: create → upload/admission → fake Vision → SUBJECT_REVIEW → CONFIRM 202 → GET PREPARATION_REVIEW; same-key replay nguyên 202 không tạo decision/attempt thứ hai; revision cũ 409; decision và receipt cùng UoW.
7. Cancel từ INPUT_PROCESSING và mô phỏng UNKNOWN/AWAITING_RECONCILIATION: transaction DELETE_PENDING + nhả lock; late fake result không cập nhật head; giữ nguyên ledger khi ledger đã tồn tại; không auto retry/đổi UNKNOWN thành FAILED. Goal 1 fake path không tự tuyên bố đã tích hợp A1 ledger; proof qua A1 thật thuộc Goal 2.
8. Legacy Organization row đọc/update hợp lệ, insert shape cũ bị chặn; writer mới, Parent và các trường hợp NULL không hợp lệ được test disposable PG; không backfill runtime và không org giả.
9. Chạy worker thật trên runtime mục tiêu: malformed/ảnh cắt/quá pixel/nhiều frame/unsupported MIME/hung/timeout/quá memory; chứng minh OS limit và kill/fail-closed, zero provider. Giữ FEAT-018/canvas behavior cũ; lưu original và derived asset có hash/lineage; test JPEG/PNG/WebP khác nội dung. Nếu chưa xác minh resource enforcement, báo NOT VERIFIED và readiness fail.
10. Offline test chặn external network; PG/Alembic chỉ trên DB disposable riêng được tạo và dọn có bằng chứng trong scope owner duyệt, không dùng DB A2. Ghi PASS/FAIL/SKIP/NOT RUN thật, không suy từ các phiên trước. Run lint/type/three validators/diff-check theo plan; không stage/commit/push/merge.

## Bàn giao và hard stop

Ghi evidence dưới feature, hash plan/test artifacts, kết quả test, điểm lệch SRS còn lại và snapshot file thực sự sửa; báo `XONG-CHƯA REVIEW` hoặc `BLOCKED` cùng lý do. Owner yêu cầu không review lại M0; việc review implementation Goal 1 là bước riêng trước Goal 2. Không nhận dữ liệu trẻ thật, Teacher, UI, story/video/audio, full AiJobService, durable purge, shared A1 hook/transport hay Modal/GPU/provider. Khi cần sửa file ngoài allowlist, dùng DB không chứng minh disposable, thiếu approval hoặc môi trường không đủ, dừng phần phụ thuộc và báo chính xác.

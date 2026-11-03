## Findings

1. **P1 — Không thể bắt đầu lượt demo thứ hai sau khi xác nhận thành công**
   **Lỗi code.** [repository.py](../../../backend/src/sketch2life/infrastructure/story_run_lite/repository.py:1839) chuyển run sang `PREPARATION_REVIEW` nhưng giữ active-owner lock. [Cùng file](../../../backend/src/sketch2life/infrastructure/story_run_lite/repository.py:1939) từ chối cancel tại trạng thái này; tạo run mới vì thế trả `ACTIVE_RUN_EXISTS` theo [kiểm tra active owner](../../../backend/src/sketch2life/infrastructure/story_run_lite/repository.py:324). Không thấy đường complete hoặc closeout tương ứng trong lát cắt này. Điều này chặn việc chạy lại trên cùng DB sau happy path, dù M0 yêu cầu có đường an toàn giải phóng lock và hướng dẫn nói tạo run mới cho ảnh khác.
   **Hướng sửa:** bổ sung lifecycle được duyệt để đóng hoặc hủy run sau xác nhận và nhả lock nguyên tử, giữ dữ liệu và receipt; kiểm thử chạy hai lượt thành công liên tiếp trên cùng DB.

2. **P2 — Recovery có thể bỏ sót ledger đã `SENT` sau khi Story đã lưu kết quả**
   **Lỗi code, cửa sổ race.** [photo_bridge.py](../../../backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py:203) commit kết quả Story trước khi finalize ledger tại dòng 223. Trong khoảng đó, request khác có thể confirm và đưa run sang `PREPARATION_REVIEW`; nếu process chết hoặc finalize thất bại, [truy vấn reconciliation](../../../backend/src/sketch2life/infrastructure/story_run_lite/repository.py:1590) chỉ chọn `SUBJECT_REVIEW`, nên bỏ sót kết quả đã xác nhận. Cancel trong cùng cửa sổ cũng có thể đổi trạng thái khỏi tập được chọn. Ledger có thể còn `SENT` sau restart dù Story đã có kết quả.
   **Hướng sửa:** đối soát dựa trên receipt kết quả bất biến và tuple ledger, kể cả sau chuyển trạng thái hoặc cancel; thêm test điều khiển race và crash giữa commit Story, confirm/cancel và finalize. Không tự gửi lại inference.

3. **P2 — Replay chính xác lệnh attach không luôn trả receipt ban đầu**
   **Lỗi code.** [story_run_lite.py](../../../backend/src/sketch2life/application/services/story_run_lite.py:311) kiểm tra target trước khi tra receipt. [Kiểm tra target](../../../backend/src/sketch2life/infrastructure/story_run_lite/repository.py:269) chỉ chấp nhận `INPUT_PROCESSING`. Vì vậy, sau khi Vision thành công và run sang `SUBJECT_REVIEW`, gửi lại đúng key, fingerprint và ETag của attach nhận `404` thay vì snapshot `202` đã lưu. Test replay hiện có ở tầng repository không đi qua kiểm tra này của service.
   **Hướng sửa:** kiểm tra authority của owner và tra receipt cùng fingerprint trước các điều kiện chỉ áp dụng cho lệnh mới; kiểm thử replay qua HTTP sau thành công, recovery và cancel, đồng thời bảo đảm không dispatch lại.

4. **P2 — Mất kết nối giữ singleton lock không làm runtime ngừng nhận lệnh**
   **Lỗi code.** [repository.py](../../../backend/src/sketch2life/infrastructure/story_run_lite/repository.py:50) giữ advisory lock bằng một connection, nhưng chỉ kiểm tra biến connection tồn tại; các command không kiểm tra lock còn được giữ. Nếu PostgreSQL ngắt riêng session đó mà process API vẫn sống, instance khác có thể lấy lock và recovery trong khi instance cũ tiếp tục nhận lệnh. Ngoài ra, `pg_advisory_lock` chờ thay vì fail-fast khi instance thứ hai khởi động. Đây khác với giới hạn D17 đã ghi: D17 thừa nhận claimant cũ có thể gửi sau mất lock, nhưng vẫn yêu cầu readiness fail và từ chối command mới.
   **Hướng sửa:** dùng cơ chế phát hiện mất lock và fail-closed cho readiness/command mới; dùng phép thử lock không chờ khi startup. Kiểm thử bằng cách ngắt session lock, giữ process cũ sống và khởi động instance mới.

5. **P2 — Hướng dẫn Bruno bỏ qua bước gửi bytes ảnh**
   **Lỗi handoff.** [README.md](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/README.md:10) chuyển từ request `02-create-upload` thẳng sang `04-complete-upload`, không hướng dẫn chạy `03-upload-part`. Người làm theo các bước thủ công sẽ complete session chưa có part và không tới `READY`. Lệnh CLI phía dưới có request 03, nhưng hướng dẫn setup Modal lại chỉ người dùng chạy 01–05 theo README.
   **Hướng sửa:** thêm bước 03 rõ ràng trước complete và kiểm tra lại toàn bộ quy trình thủ công từ DB hợp lệ mới.

6. **P3 — Request GET mẫu sau confirm có assertion cho trạng thái trước confirm**
   **Lỗi handoff.** [Hướng dẫn Modal](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/MODAL_BE_UI_SETUP_20261103.md:159) yêu cầu GET run lần nữa sau request 08, nhưng [request 07](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/07-get-run.bru:23) luôn assert `SUBJECT_REVIEW`. Dùng lại request này sau confirm sẽ báo test thất bại khi API trả đúng `PREPARATION_REVIEW`.
   **Hướng sửa:** cung cấp GET riêng với assertion `PREPARATION_REVIEW`, hoặc hướng dẫn kiểm tra response không dùng assertion cũ.

## Kết luận: NEEDS_REVISION

Có thể bàn giao OpenAPI và collection làm tài liệu để UI bắt đầu tích hợp **trong phạm vi synthetic, local**, nhưng chưa nên gọi Mốc 1 là hoàn tất hoặc bàn giao quy trình demo có thể chạy lại. P1 chặn lượt thành công thứ hai trên cùng DB; các P2 ảnh hưởng receipt, recovery, kiểm soát một instance và thao tác upload.

Đây là review theo bằng chứng mã và tài liệu, không phải chứng minh toàn bộ tổ hợp runtime. Những giới hạn có chủ đích gồm identity Parent giả lập, một actor/run, loopback, không có auth/consent thật, chưa có full AiJobService và không bảo đảm provider dừng khi cancel. Không dùng các giới hạn đó làm bằng chứng sẵn sàng production.

## Evidence và kiểm tra

- HEAD đúng `c4edf51fd5af69a327d6776625cf387447f4ec59`, nhánh `feature/feat063-be-foundation`; merge có hai parent `b6853d5…` và `c98701b…`. `git status --porcelain` đếm **55 thay đổi local**. Mã và tài liệu để đưa finding được đọc bằng `git show`/`git grep` tại commit đích.
- [Evidence main BE](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/STORYRUN_LITE_MAIN_BE_INTEGRATION_20261103.md:1) ghi lượt trước merge: ClamAV CLEAN, upload READY, một POST Modal HTTP 200, ledger `SUCCEEDED`, rồi `PREPARATION_REVIEW`. [MODAL_LIVE_SUCCESS](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/STORYRUN_LITE_MODAL_LIVE_SUCCESS_20261103.md:1) ghi một lượt live riêng trước đó. Đây là **báo cáo và evidence lịch sử**, không phải lượt Modal tôi tự chạy; một HTTP POST cũng không chứng minh chỉ có một generation nội bộ.
- Evidence migration báo bốn tình huống PG17 có điều kiện: cài mới, Lesson trước, StoryRun trước và từ chối schema lạ; có báo cáo bảo toàn rows/FK và regression Lesson. Tôi đã đọc đường compatibility và log được nêu, nhưng **không tự chạy migration hoặc xác minh DB**. Không suy rộng kết quả sang mọi schema lịch sử.
- Đã đọc [bản ghi chuẩn hóa whitespace](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md:1). Hash SHA-256 của README, review V11 và log fresh recovery trong Git object khớp **hash sau chuẩn hóa** trong bảng. Hash lịch sử tương ứng với bytes gốc không nằm trong commit; tôi không coi sự khác biệt đó tự nó là lỗi evidence.
- Tôi chưa tìm thấy bản ghi `81 passed` sau merge trong evidence đã tìm tại commit, nên giữ đây là thông tin bạn cung cấp, **chưa xác minh độc lập**. Modal sau merge: **NOT RUN** trong lượt review này.

Tôi chạy `git status`, `git rev-parse`, `git log`, `git show`, `git diff`, `git grep` và tính SHA-256 từ Git object. Với các file domain/migration-compat không có diff local, tôi chạy pytest bằng Python trong `backend/.venv`, tắt bytecode, pytest cache và plugin autoload, gỡ hai DB URL khỏi process và chặn socket: **16 passed**. Lần thử lệnh đầu bị lỗi quoting Python trước khi pytest chạy; lệnh sửa lại thành công. Test PostgreSQL, scanner thật, worker runtime, Bruno, network và Modal: **NOT RUN** trong lượt này.

Không sửa file, không dùng subagent, không đọc `.env`/token, không dùng DB hiện có và không stage, commit, push hoặc merge.

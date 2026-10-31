**Kết luận: NEEDS_REVISION.** V11 có hướng thiết kế đủ để tiếp tục thảo luận với owner, nhưng còn các điểm ảnh hưởng đến quyết định về rủi ro, recovery và acceptance. Tôi ghi nhận **7 finding P2 và 2 finding P3**, không thấy P0/P1 trong phạm vi review tĩnh này.

Hash V11 tự tính là `31217D7C1870D4DEA132B472B917890ABA86CCAE92970BD1EE8AB3CCE506883F`, khớp yêu cầu. Hash V10, báo cáo handling và Owner Decisions V4 cũng khớp các giá trị được ghim.

### Findings

1. **P2 — Q3-B+ chưa mô tả khả năng các invocation của những run khác nhau chồng lấn.**<br>
   **Vị trí:** [V11 D17](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:71>), [sổ độ lệch](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:186>).<br>
   **Tình huống và tác động:** Worker cũ đã `CLAIMED` có thể mất session lock rồi vẫn tới `SENT`. Process mới có thể lấy lock, còn cancel giải phóng owner lock để tạo run mới; UNIQUE của A1 chỉ ngăn claim lại cùng tuple, không ngăn một tuple của run mới. Một invocation đã `SENT` hoặc `UNKNOWN` cũng có thể vẫn chạy phía provider khi run mới được xử lý. Do đó rủi ro không chỉ là một call bị phí: các call khác run có thể cùng tồn tại, dù CAS ngăn kết quả cũ cập nhật head. Đây là suy luận từ thiết kế và mã A1, chưa phải kết quả runtime.<br>
   **Sửa tối thiểu:** Ghi rõ hai trường hợp overlap và giới hạn của capacity=1 theo từng process. Nêu Q3-C cần review race tại `mark_sent`; bản thân fence trước `SENT` không dừng invocation đã gửi hoặc chứng minh provider không còn chạy. Giữ điều kiện nâng cấp trước multi-process, dữ liệu thật hoặc yêu cầu zero-send.

2. **P2 — Fixture gate chưa có đầu vào được ghim và chưa ràng buộc cùng snapshot tới decoder.**<br>
   **Vị trí:** [V11 D4](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:58>), [luồng admission](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:80>), [acceptance](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:139>).<br>
   **Tình huống và tác động:** V11 yêu cầu server pin hash nhưng chưa chỉ định fixture, provenance, path/hash hoặc hard stop khi chúng chưa có. Hơn nữa, `Feat018ImageAdmission` tại A1 tự mở path và đọc snapshot riêng; nếu lớp ngoài hash một lần rồi FEAT-018 đọc lại bytes đã thay đổi, câu “hash trước decode” chưa đủ chứng minh decoder chỉ nhận fixture đã duyệt.<br>
   **Sửa tối thiểu:** Trước implementation admission, yêu cầu xác định và review fixture cùng SHA-256, fail closed khi thiếu hoặc lệch; ràng buộc hash và decode trên **cùng snapshot bất biến**, hoặc chứng minh cơ chế tương đương. Chỉ rõ fixture nào phục vụ acceptance một và hai part, và cách kiểm ranh giới 5 MB mà không nới allowlist.

3. **P2 — Quy tắc chuyển tiếp owner scope chưa đủ để triển khai an toàn cho legacy.**<br>
   **Vị trí:** [V11 D5](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:59>), [DTR amendment](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:197>).<br>
   **Tình huống và tác động:** A1 khai báo `organization_id NOT NULL`. V11 đúng khi đề xuất cho Parent dùng `NULL` và legacy Organization đọc fallback, nhưng chỉ nói “CHECK/index và rule legacy tạm”, chưa định nghĩa đầy đủ tổ hợp hợp lệ hoặc cách phân biệt legacy null-ref với Organization write mới. CHECK yêu cầu mọi org ref bằng `organization_id` mà không có ngoại lệ phù hợp có thể làm legacy rows không hợp lệ; ngược lại, ngoại lệ quá rộng có thể cho phép writer mới tiếp tục tạo null-ref. SQL `CHECK` cũng phải xử lý rõ `NULL`.<br>
   **Sửa tối thiểu:** Ghi biểu thức chuyển tiếp rõ ba trường hợp: Parent có ref và org null; Organization có org và ref khớp; legacy Organization có org và ref null. Quy định cơ chế chặn **write mới** dùng ngoại lệ legacy, fallback và index, cùng acceptance cho row cũ, writer cũ/mới và Parent. Không cần tạo org giả hoặc runtime backfill.

4. **P2 — Chưa định nghĩa kết cục receipt `PENDING` khi dispatcher mất.**<br>
   **Vị trí:** [V11 D14–D18](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:68>), [crosswalk V8 P2-3](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:274>).<br>
   **Tình huống và tác động:** V11 giữ receipt `PENDING/FINAL` và exact replay, nhưng không nêu khi process chết sau commit `PENDING`, trước queue acknowledgement hoặc `FINAL`, retry cùng key nhận gì. Hoãn quarantine retry là lựa chọn có thể chấp nhận cho demo, nhưng không tự giải quyết receipt mồ côi: client có thể chờ mãi hoặc implementation vô tình dispatch lại. V10 từng quy định rõ cả trường hợp `PENDING` và `FINAL 202` trước gate-open.<br>
   **Sửa tối thiểu:** Chọn recovery tối giản phù hợp `FAILED + session mới`: chốt `PENDING` thành snapshot ổn định, không dispatch lại; giữ nguyên snapshot đã `FINAL`; dùng state/version CAS để worker cũ không tạo asset. Thêm hai crash acceptance tương ứng cho Core và quy định tương tự hoặc hold rõ cho Story attach.

5. **P2 — Acceptance `CONFIRM` bị rút mất chi tiết đã xử lý finding V8.**<br>
   **Vị trí:** [Goal 1 acceptance](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:141>), [V11 disposition V8 P2-4](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:275>).<br>
   **Tình huống và tác động:** Goal 1 nhắc `CONFIRM` và Bruno happy/error path, nhưng không còn yêu cầu cụ thể kiểm `202`, GET `PREPARATION_REVIEW`, replay cùng key không tạo decision hoặc Vision attempt thứ hai, và revision cũ trả `409`. Một implementation có thể được coi là đạt acceptance chung mà chưa chứng minh lại behavior của V8 P2-4.<br>
   **Sửa tối thiểu:** Khôi phục kịch bản acceptance/Bruno đầy đủ đó từ V10; ghi cùng Story UoW cho receipt và decision như disposition V11 đã nêu.

6. **P2 — Danh sách amendment DTR chưa bao hết các vị trí số đếm và quan hệ hiện hành.**<br>
   **Vị trí:** [V11 §6.1](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:189>), [dòng amendment](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:197>).<br>
   **Tình huống và tác động:** Hai phép tính V11 đúng, nhưng danh sách chỉ nêu §5.1, §5.6, §14.1 và §14.4. DTR còn tổng và phân rã hiện hành tại §1, §2.1, §5–§7 và §11; chỉ sửa các mục được liệt kê sẽ để register tự mâu thuẫn.<br>
   **Sửa tối thiểu:** Liệt kê thêm các vị trí tổng, ownership, relationship và invariant cần cập nhật; giữ các mốc Q135 lịch sử là lịch sử. Đặc tả hai receipt table và unique/shape cần thiết trước migration.

7. **P2 — Contract idempotency chưa đủ rõ về authority và phạm vi key.**<br>
   **Vị trí:** [V11 contract](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:126>).<br>
   **Tình huống và tác động:** Câu “canonical receipt” ở dạng số ít và “key/fingerprint khác trả 400” có thể bị đọc thành một receipt chung hoặc key khác cũng bị lỗi. D14/D16 thực tế chọn hai authority theo owner; cùng key **trong cùng identity/scope** nhưng khác fingerprint mới là conflict. V11 cũng không còn ghi rõ collection scope cho create và fingerprint đầy đủ như V10. Điều này có thể gây replay sai hoặc đụng key giữa Story và Core.<br>
   **Sửa tối thiểu:** Nêu riêng `story.command_receipts` và `core.upload_command_receipts`, identity gồm actor/operation/server-defined scope/key hash; xác định collection scope trước khi resource tồn tại, fingerprint của từng command và quy tắc “cùng identity/key, fingerprint khác → 400”. PUT part tiếp tục dùng natural key/digest riêng.

8. **P3 — Phần mở đầu còn nói một goal gộp.**<br>
   **Vị trí:** [V11 dòng 13](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:13>) so với [Q5](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:174>).<br>
   **Tình huống và tác động:** “Goal gộp S1+S2” mâu thuẫn với hướng draft hai goal tuần tự, dễ làm owner hiểu sai đơn vị approval.<br>
   **Sửa tối thiểu:** Đổi thành mỗi goal có plan/approval riêng, Goal 2 chỉ sau review Goal 1; giữ live Modal là cổng riêng.

9. **P3 — Ghi chú smoke và baseline còn mang ngữ cảnh V10.**<br>
   **Vị trí:** [V11 dòng 26](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:26>) và [dòng 35](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V11_DRAFT_20261102.md:35>).<br>
   **Tình huống và tác động:** “V10 là draft mới” và “lượt lập V10 này” được giữ trong V11, làm mờ tác giả/lượt nào đã kiểm chứng smoke.<br>
   **Sửa tối thiểu:** Đánh dấu đó là ghi chú lịch sử của lượt V10, hoặc cập nhật riêng mức kiểm chứng của lượt V11 mà không nâng mức chứng cứ.

### Các điểm đã đối chiếu

- **Upload và contract:** V11 liệt kê đủ 5 upload operations và tổng cộng 10 operations. Phép tính `5.000.000 = 4.194.304 + 805.696`, giới hạn hai part, continuity và SHA trên bytes ghép đúng thứ tự được mô tả đúng. Quảng bá limits giúp giữ route/DTO khi tăng giới hạn, với điều kiện UI thực sự đọc limits và xử lý state tương lai; không thể xác minh UI consumer trong lượt này.
- **Cancel:** [SRS UC-11](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1422>) cho hủy mọi run chưa thuộc các trạng thái loại trừ, do đó bao gồm `INPUT_PROCESSING`. Áp dụng cho job `AWAITING_RECONCILIATION` là **suy luận** từ state của run vẫn chưa terminal, không phải UC-11 gọi tên riêng trạng thái job đó. V11 nêu `DELETE_PENDING` và nhả lock cùng transaction, giữ ledger UNKNOWN và loại cập nhật head muộn bằng CAS; purge bền đầy đủ được ghi là hoãn.
- **Decoder/scanner:** Mã A1 gọi PyAV trong process; module decoder được đọc không thiết lập subprocess timeout 3 giây hay hard memory cap. V11 phân biệt attestation với scanner `CLEAN`, và để ClamAV phụ thuộc xác nhận của owner. Tính an toàn thực tế của fixture gate còn phụ thuộc finding 2.
- **DTR:** Các phép cộng **53/91/139** và **56/94/142** đúng theo hai baseline sau thêm `core.upload_command_receipts` và `story.command_receipts`. `89` là source-declared mappings, không phải số bảng DB live. Cột DB là `part_number`; `{part_no}` là tham số route.
- **Goal và evidence:** Q5, ngoài câu cũ tại dòng 13, đề xuất Goal 1 rồi Goal 2, ước lượng cơ sở 4–8 ngày, cộng review/fix thành 5,2–16 ngày với độ tin cậy thấp. Owner Decisions V4 giới hạn chiến lược hai lần gọi cho T13; không tự mở rộng cho StoryRun-lite. V11 giữ approval Modal live riêng. Bảng smoke phân biệt báo cáo 29/10, tự thuật 01/11 và `/health`; không chứng minh A1 đã gọi Modal live.
- **Crosswalk:** V11 giữ finding V8 và C1–C8, đồng thời nói rõ disposition mới là draft, không tuyên bố review cũ đã accept. Tuy nhiên, các finding 4–6 cho thấy một số nội dung từng được V10 mô tả đầy đủ chưa còn đủ cụ thể trong acceptance/amendment V11.

Review này chỉ dựa trên tài liệu và mã A1 đọc bằng `git show` tại commit được yêu cầu. Tôi không chạy test/validator, truy cập database, gọi provider hay sửa file. Không có bằng chứng runtime mới được tạo; kết luận review M0 cũng không phải owner approval cho implementation hoặc mở goal.

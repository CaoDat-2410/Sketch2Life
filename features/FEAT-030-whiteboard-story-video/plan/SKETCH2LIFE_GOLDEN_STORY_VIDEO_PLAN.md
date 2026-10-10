# Golden Story Video — đề xuất ba cảnh, chưa triển khai

Trạng thái: **PROPOSED / AWAITING_OWNER_APPROVAL**. Đây là kế hoạch sau benchmark, không phải báo cáo đã tạo story video. V2 vẫn OFF; không thực hiện motion, audio, transition hoặc paid inference trong tác vụ hiện tại.

## Mục tiêu và giới hạn

Một video thử nghiệm duy nhất, ba cảnh, dự kiến **52 giây: 18 + 18 + 16**; mỗi cảnh 5–20 giây, tổng 40–60 giây. Dùng đúng tranh gia đình gốc và stable IDs, giữ màu/texture/nhận dạng. Không lặp lại việc vẽ toàn bộ tranh ở mỗi cảnh. Không tráo nhân vật bằng hình học, không tái sinh tranh gốc.

Đích là sản phẩm kể chuyện có chuyển động 2D và audio được duyệt, không tự gọi dịch chuyển ảnh cắt là chuyển động đi bộ thật. Chỉ một clip đã được người dùng xem trực tiếp và chấp nhận mới là Golden; test PASS hoặc final fidelity không thay thế nghiệm thu.

**Blocker đầu tiên:** vòng pencil hiện tại chưa cải thiện đáng kể, VISUAL_QA_NOT_PASSED. Không tiếp tục chọn ngưỡng rồi chạy lặp. Trước story cần quyết định có chấp nhận lối trình bày whiteboard cách điệu với các nét chọn lọc hay cần vẽ/tô đầy đủ như người thật. Full raster-pencil reveal trong thời gian ngắn không đạt tốc độ tự nhiên với đường đi hiện tại. Hai phương án để owner chọn sau, chưa triển khai:

1. Ưu tiên Golden kể chuyện 52 giây: dùng nền nguồn đã chuẩn bị, vẽ các nét có ý nghĩa theo narration bằng path được kiểm tra/thủ công, rồi giữ tranh hoàn thiện cho motion. Không fade toàn ảnh hoặc gọi nguồn nền tĩnh là đã được AI vẽ tự nhiên. Cần owner duyệt mẫu style/timing trước.
2. Nếu bắt buộc thể hiện toàn bộ tô chì: thay cách lập đường đi để giảm trùng lặp và có path ngữ nghĩa được review; nếu vẫn không vừa thời lượng, trả lỗi timing hoặc xin đổi yêu cầu. Không tự tăng thời lượng ra ngoài 40–60 giây hay thay tranh.

## Nội dung: bắt buộc lấy lời kể thật và adult approval

Hiện chưa có ba đoạn lời kể thật đã được server duyệt cho Golden. Trước tiên xin bé/người lớn xác nhận: ai trong tranh, chuyện xảy ra theo thứ tự nào, bé muốn kể thêm hành động gì và có đồ vật mới nào. Nội dung dưới đây chỉ là **chủ đề gợi ý, chưa approved**, không giả làm lời bé đã nói:

| Cảnh | Thời lượng dự kiến | Nội dung cần bé/người lớn xác nhận | Hình ảnh/chuyển động đề xuất |
| --- | ---: | --- | --- |
| 1 — Giới thiệu | 18 s | Giới thiệu các thành viên, ngôi nhà, cây/vườn theo lời thật | Dựng tranh theo thứ tự đã được owner đánh giá tốt; đường vẽ chọn lọc, không ép hàng nghìn nét chạy dưới một frame. Kết thúc bằng composition nguồn hoàn chỉnh. |
| 2 — Cùng nhau ngoài vườn | 18 s | Ví dụ bé kể gia đình cùng ngắm hoa; phải được xác nhận, không suy từ tranh rồi mặc định duyệt | Motion 2D giới hạn: di chuyển cả nhóm gia đình như một composite giữ liên kết tay, hoặc cử động nhỏ đã rig/review. Chuyển camera hướng vườn nếu narration cho phép. Không gọi translation là đi bộ có chân/khớp. |
| 3 — Điều bé muốn kể thêm | 16 s | Một hành động mới do bé kể và người lớn duyệt; ví dụ muốn chăm sóc/tưới hoa, chỉ là lựa chọn nháp | Nếu có bình tưới/vật mới: asset mới có provenance riêng và được duyệt trước. Nếu cần tay/chân thao tác thật: cần rig/pose asset và motion review, không ép chín mask tĩnh thành động tác. Kết thúc giữ frame để nghe hết narration. |

Nếu bé kể câu chuyện khác, thay cả ba beat theo lời đã duyệt; không cố ép vào đề tài chăm sóc hoa. Nếu không có nội dung thêm đã duyệt, dừng ở draft hoặc dùng ba beat chỉ với sự kiện được xác nhận; không bịa thêm event để đủ ba cảnh.

## Gate, identity và assets trước khi chạy

- Approved StoryScriptSegment cho từng cảnh, stable event IDs truy về segment/fact/anchor. Chi tiết/hành động mới: NEEDS_APPROVAL. Consent benchmark và `review_ref` caller không xác thực Gate A/B.
- Server-managed approval record bind session/package/script/source hashes bất biến; edit narration invalidates approval. Gate A/B hiện tại giữ nguyên ý nghĩa; không tự mở endpoint V2.
- Chín mask hiện tại chỉ đủ static reveal. Motion cần review shared hands, silhouette, identity, joint/rig nếu cần; thiếu/sai mask trả NEEDS_MASK_REVIEW. Không thay mask thật bằng bbox.
- Giữ original asset pixel/hash; dùng group composite không làm mất stable ID/provenance của mẹ/bố/bé. New asset không được gắn provenance nguồn giả.
- Background bị nhân vật che khuất là chưa biết. Di chuyển có thể để lộ vùng trống: cần background layer bổ sung được người lớn duyệt và provenance NEW/DERIVED rõ ràng, hoặc hạn chế motion/camera để không lộ vùng chưa có. Placeholder trắng hiện tại không được coi là background hoàn chỉnh.
- Action chưa hỗ trợ: UNSUPPORTED_ACTION. Không silent fallback V1 rồi ghi nhận V2 thành công.

## Transition và audio — chỉ thiết kế

- Cảnh 1→2: giữ scene state/identity, tiếp nối tranh đã vẽ; chuyển camera hoặc cut có chủ đích, không vẽ lại cùng tranh.
- Cảnh 2→3: transition ngắn chỉ khi state và narration hợp lệ. Nếu thêm asset, vẽ asset mới sau khi đã duyệt, không biến đồ vật cũ thành đồ mới.
- Các transition tính trong thời lượng cảnh, không cộng ngoài 52 giây; exact duration phải chốt sau khi đo narration, tránh double-count audio/crossfade.
- Audio: ưu tiên lời bé được phép sử dụng hoặc TTS đọc **đúng văn bản đã duyệt**. Chốt voice với owner; không clone giọng tự động. Nhạc/SFX chỉ khi có quyền sử dụng và approval, không che narration.
- Timing theo audio thực; thoại dài/ngắn không khả thi trả lỗi cấu trúc và lý do. Không âm thầm kéo 20 giây/cảnh, lặp audio, tăng tốc giọng hoặc giữ màn hình trống để đủ tổng thời gian.

## Trình tự triển khai sau khi được duyệt riêng

1. Chốt style/timing sample và narration/approval binding; tạo storyboard ba beat, contact sheet/state table để owner duyệt trước render tốn phí.
2. Motion-readiness review và chuẩn bị source/durable assets/occlusion assets; action execution pilot riêng. Không coi full rig tự động là đã có.
3. Chạy Golden đúng ba cảnh với approved events/assets/audio; cache theo input hashes để không gen lại phần không đổi. Retry giới hạn và chỉ sửa phần lỗi, không regeneration vô hạn.
4. Local technical checks trước, sau đó Real Runtime Acceptance riêng trên LightningAI với artifacts thực và ảnh được phép. Không báo Level 2 PASS trước khi chạy/đánh giá LightningAI.
5. Owner xem MP4 đầy đủ: continuity, nghĩa câu chuyện, vẽ/tô, motion, chuyển cảnh, audio. Chỉ sau review mới cân nhắc nối BE; không tự deploy.

## Điều kiện nghiệm thu và artifact

Ba cảnh đúng narration/approved events, stable identities và state continuity; giữ source fidelity ở các asset; motion không lộ nền giả/trắng, không gọi sliding là walking. Nhịp bút/path được nhìn thấy thay vì phần lớn nét chạy dưới một frame; coloring có direction/texture nguồn, không rectangle/fade coverup. Audio không lặp, khớp câu/cảnh, video 40–60 giây. Nếu còn bất kỳ lỗi quan trọng nào: VISUAL_QA_NOT_PASSED, nêu blocker và dừng.

Bàn giao khi thực sự triển khai: approved storyboard/scripts và hashes, source/new registry, scene/event/state plans, từng scene MP4, final MP4 có audio, contact sheets/chuyển cảnh, source-fidelity/motion/timing checks, logs/cache/retry evidence và đánh giá người dùng. Hiện tất cả mục này là yêu cầu tương lai, **chưa có Golden Story Video**.

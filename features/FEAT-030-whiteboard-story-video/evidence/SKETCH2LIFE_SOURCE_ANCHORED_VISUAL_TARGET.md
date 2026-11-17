# SOURCE-ANCHORED WHITEBOARD STORYTELLING — Visual Target Review
Revision30 — 2026-10-10

## Kết quả và trạng thái

Đã tạo visual target từ đúng tranh gia đình gốc. Bản minh họa đơn giản hóa Revision29 bị đánh dấu VISUAL_FIDELITY_NOT_PASSED và không được dùng làm baseline Golden Story. Code và artifact thử nghiệm vẫn được giữ nguyên, không xóa hay viết lại.

Trạng thái hiện tại: SOURCE_CONTENT_PRESERVED / OWNER_VISUAL_REVIEW_PENDING / STORY_RENDER_NOT_RUN.
Chưa tự tuyên bố Visual QA PASS. Dừng ở visual target theo yêu cầu mới nhất.

Mode vẽ sát nguồn Revision28 được chốt là TECHNICAL PROOF / OPTIONAL ORIGINAL-DRAWING MODE. Thời gian bướm23.2586s và nhà106.7572s không phù hợp mục tiêu story slice ngắn; Visual QA vẫn NOT_PASSED. Không tiếp tục ép timing bằng refinement. Giữ artwork nguồn trong hướng mới không đồng nghĩa tái sử dụng yêu cầu ngòi bút đi qua toàn bộ pixel của mode cũ.

## Artifact để duyệt

Thư mục riêng ngoài Git:
D:/Codex/Sketch2Life/source_anchored_target_2026-10-10/

- ABCD-visual-fidelity-comparison.png: bốn panel có nhãn và giới hạn.
- A-original-decoded.png: ảnh JPEG gốc giải mã sang PNG.
- B-source-anchored-native.png: target artwork native, RGB không đổi.
- B-enhanced-presentation-2x.png: phóng Lanczos2× từ594×336 lên1188×672.
- C-whiteboard-target.png: artwork đầy đủ trên vùng trình bày trắng,1348×832; không cắt nội dung.
- D-scene-target-no-unapproved-assets.png: cùng target, chưa thêm artwork mới chưa duyệt.
- identity-and-context-detail-sheet.png: cận cảnh kiểm tra từng nhân vật, nhà, cây và vườn.
- storyboard-framing-preview.png:4 preview trọng tâm.
- beat-1/2/3/4-framing-preview.png: từng khung hình riêng.
- drawing-control-guides-PROPOSAL-overlay.png:15 đường hướng dẫn minh họa lớp điều khiển riêng.
- drawing-control-proposal.json: tọa độ source-space, đối tượng/phase và các điều kiện còn thiếu.
- scene-plan.draft.json: lời kể mô phỏng và camera crop đề xuất.
- asset-manifest.json:9 source assets,source SHA và mask SHA,provenance.
- source-assets/:9 PNG RGBA dùng đúng master masks,giữ màu nguồn.
- validation.json và artifact-sha256.json:kiểm tra và checksum.

A,B,C,D giống nhau về artwork là lựa chọn có chủ đích. “Enhanced” ở bước này chỉ là nâng kích thước trình bày; KHÔNG có AI super-resolution, tái sinh chi tiết, làm đẹp mặt, thay nét, recolor hoặc sửa cấu trúc. Không gọi phóng ảnh là cải thiện chất lượng nét. Đây là target bảo toàn nhận diện để duyệt trước khi thiết kế draw control.

Bướm trước đây chỉ được duyệt concept/technical proof, chưa duyệt artwork cuối. Không đưa bướm vào D hay target chính. Có thể khôi phục câu chuyện bướm và đặt candidate sau khi artwork được duyệt; không coi việc bỏ bướm ở preview này là hoàn thành yêu cầu thêm asset mới của slice trước.

## Chi tiết được giữ

| Thành phần | Chi tiết giữ từ nguồn |
|---|---|
| Bố | Mặt, tóc đen, kính, áo cam/viền xanh, quần xám có nét chì, giày xanh, vị trí tay |
| Mẹ | Mặt, tóc nâu, cổ/viền xanh, áo cam, váy đỏ, đai xanh, túi tím, giày và tỷ lệ |
| Bé | Tóc, nét mặt, áo xanh và túi cam, quần tím, giày xanh, chân nâng, tay nắm bố mẹ |
| Nhà | Hai tầng, hai phần mái đỏ, viền vàng, tường hồng, cửa/cửa sổ xanh, cấu trúc và tỷ lệ gốc |
| Cây | Tán xanh lớn, thân/cành và khoảng trống giữa cành, vòng vàng dưới gốc |
| Bối cảnh | Hàng rào, trời xanh, đường đào/cam nhạt, cỏ, bố cục và các bông hoa trong nguồn |
| Phong cách | Hạt/nét chì màu, đường viền không đều và tỷ lệ tranh thiếu nhi |

Artwork toàn cảnh không dịch chuyển, bóp méo hoặc thay tỷ lệ tương đối của các đối tượng. Hình đã bị cắt ở rìa trong JPEG gốc vẫn giữ đúng mức đó; không bịa phần ngoài khung.

## Chỉnh sửa và lý do

1. JPEG -> PNG lossless sau giải mã: thuận tiện kiểm tra pixel/alpha; không khôi phục chất lượng JPEG đã mất.
2. Phóng2× để đọc chi tiết: Lanczos, không suy diễn nội dung.
3. Viền trắng ngoài artwork: phục vụ trình bày target whiteboard, không xóa trời/đường/cây.
4. Cận cảnh và camera crop: đổi trọng tâm lời kể; không sửa scene state gốc. Crop gia đình giữ đủ túi, hai bàn tay, chân/giày.
5.9 source assets alpha: mask nguồn bất biến; phục vụ lựa chọn đối tượng về sau. Dùng toàn cảnh nguồn làm target tránh phụ thuộc lỗi ngữ nghĩa ở đường biên mask. Việc9masks phủ kín không chứng minh từng mask là segmentation hoàn hảo.
6. Đường màu hồng/xanh trên overlay chỉ là chú thích kỹ thuật, không thuộc artwork cuối.

Không sửa mặt/pose, đổi quần áo/phụ kiện, biến nhà hai tầng thành nhà một tầng, xóa cây, thay hoa bằng icon hay thay ảnh bằng flat-vector.

## Artwork và drawing control tách biệt

Artwork là nguồn pixel/chất liệu độc lập. Control layer chỉ quyết định đường đi bút,phase,thời điểm và vùng được phép hiện; không quyết định hình dạng cuối bằng cách thay nhân vật bằng primitive.

Đề xuất control:
- OUTLINE: đường quan trọng theo silhouette/mái/thân cây/tay/chân. Admit một dải ink matte cục bộ dọc đường bút; matte phải được review để không lộ màu trước.
- DETAIL: các điểm nhận diện gồm kính/mắt/miệng/túi/giày/cửa sổ/cành/thân hoa. Dùng đường dẫn có nghĩa và local matte, không truy mọi texture thành micro-path.
- COLOR: brush trajectory liên tục, với footprint có diện tích, clip vào mask vùng được phép; pixel màu/texture lấy từ artwork. Không đòi tâm bút ghé từng pixel.
- Tách vùng màu áo/váy/tường/mái/lá khỏi master object mask bằng derived region masks; không sửa9 master masks.
- Bút debug dùng đúng đường đang mở matte. Pen-up không mở pigment. Giữ artwork đã vẽ qua các beat.
- Không whole-image fade,full-region pop,rectangle wipe hay final snap. Chỗ thiếu coverage phải báo review, không tự bật phần dư.

15guidepaths trong JSON/overlay chỉ minh họa cách tách lớp: chưa đủ toàn bộ contour/detail/color, chưa tính coverage hoặc timing, có tọa độ manual cần chỉnh cục bộ. Chúng không phải đường đã được duyệt, không được đưa thẳng vào render hoặc gọi là đường nét chính xác. Lớp ink/brush matte đầy đủ chưa triển khai trong lượt này theo giới hạn visual gate.

## Story preview

Lời kể bên dưới là đề xuất mô phỏng mới, không phải narration của bé hay phê duyệt Gate A/B.

| Beat | Text đề xuất | Trọng tâm và scene state |
|---|---|---|
|1|Đây là nhà của em. Bên nhà có một cây xanh lớn.|Toàn cảnh;nhà hai tầng/cây/bối cảnh|
|2|Em nắm tay bố mẹ. Cả nhà ở bên nhau thật vui.|Pan/zoom nhẹ vào gia đình;giữ canvas trước đó|
|3|Em nhìn những bông hoa nhiều màu bên đường đi.|Focus vườn hoa và mép đường;không thay vị trí hoa|
|4|Em yêu khu vườn và ngôi nhà của gia đình mình.|Quay về toàn cảnh;asset mới chưa duyệt không xuất hiện|

Storyboard dùng tranh hoàn chỉnh để kiểm tra framing/fidelity. KHÔNG mô tả hình xuất hiện ngay toàn bộ ở đầu video. Các trạng thái vẽ dở sẽ chỉ được xây sau visual review. Không thực thi camera animation ở lượt này. Không chuyển trang vì các beat cùng địa điểm. Không yêu cầu rig/walk cycle.

Duration chưa gán. Mục tiêu15–25s trước đây còn là mong muốn sản phẩm; static preview không chứng minh timing. Khi có audio được phép, cần đo speech cues; hiện không gọi TTS.

## Kiểm tra thực tế

Ảnh gốc: ${PRIVATE_SOURCE_DIR}/familly.jpg, alias benchmark family1.jpg.
SHA256:52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3.
Native target RGB equality:true;MAE0.
Master masks9:đúng hash,0 overlap,0 unassigned pixels.
11 file được bảo vệ (source,manifest,9masks):không đổi hash sau preparation.
Preview A/B/C/D,detail sheet,storyboard đã được mở và kiểm tra trực quan. Khuôn mặt/đặc điểm nguồn được giữ vì không repaint.
Không MP4,model call,TTS,network upload hoặc GPU.
Không chạy pytest hồi quy renderer vì lượt này không sửa source code runtime; kiểm tra artifact thực tế và bất biến thay vì báo test PASS không liên quan.

HEAD93668ffdaa7f2890fe9498596c670006a87eba4a;branch codex/feat-018-contract-plan;index trống.
Snapshot trước: D:/Codex/Sketch2Life/source_anchored_git_before_2026-10-10.json.
345 file Python backend/tools trước lượt này giữ nguyên; digest:
b3820e289ef084d817ea9cf951438346e4796a9db16ca7c7c5f20009959b3c5d.
Không commit,push,deploy;V1 production default,V2 flag OFF.

## File thay đổi và điểm dừng

Chỉ cập nhật feature approval/plan/context/decisions/status/evidence index và báo cáo này. Preparation script và tất cả source-derived PNG/JSON nằm riêng ngoài Git:
D:/Codex/Sketch2Life/prepare_source_anchored_target_2026-10-10.py.

Revision29 interrupted code vẫn tồn tại để tham khảo, chưa kiểm thử/hoàn thiện cho production; không được gọi làm baseline hình mới.

Chờ người dùng review visual target. Các vấn đề còn mở:chất lượng vẽ động,timing15–25s,derived phase masks,brush coverage,artifact mới và audio sync. Không tự chuyển visual fidelity thành animation PASS.

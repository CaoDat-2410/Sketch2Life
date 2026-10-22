# Bàn giao FEAT-048 cho phiên Codex trên máy khác

Cập nhật ngày 2026-10-23 cho Khoa. Đây là trạng thái hiện tại để phiên mới tiếp tục đúng nhánh, đúng SRS và biết phần nào đã làm, phần nào còn cần kiểm tra.

## Mục tiêu và nguồn chuẩn

Khoa được phân công ba diagram: ERD, System Architecture và Package Diagram. Nội dung phải theo SRS v3.1 hiện hành, lưu thành Draw.io chỉnh sửa được và có mã Mermaid tương ứng trong repository.

- SRS chuẩn: [Sketch2Life_Master_SRS.md](../../FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md), source register ID collaborative-srs-v3-20261010.
- Các vùng SRS đã dùng: B7/B7.1 và B21/B21.5 cho ERD; B8 cùng các phần nền tảng/phân ranh hệ thống cho Architecture và Package.
- SRS vẫn là nguồn quyết định. Các nhóm domain, schema logic, database, queue, storage, realtime và AI provider chưa được chọn đều phải giữ nhãn PROPOSED, CANDIDATE hoặc TBD.
- Không sửa SRS chuẩn, schema/runtime, không suy ra quyết định triển khai AWS hay nhà cung cấp từ bản vẽ.

## Nhánh và cách tiếp tục trên máy khác

FEAT-048 nằm riêng trên branch feature/feat048-srs-diagram-pack, được tạo từ origin/dev tại f220781876472950093856e97bbdaaec5170a7c1. Khoa đã yêu cầu push để tiếp tục ở máy khác; branch hiện có trên origin và không được merge vào dev nếu chưa có yêu cầu riêng.

Trên clone mới:

    git fetch origin
    git switch --track -c feature/feat048-srs-diagram-pack origin/feature/feat048-srs-diagram-pack

Nếu branch đã checkout rồi:

    git switch feature/feat048-srs-diagram-pack
    git pull --ff-only

Hai commit gốc của gói diagram và hồ sơ bàn giao là d3b0f8fe và e00f98e2; sau bản cập nhật handoff này hãy dùng git log --oneline -3 để xem các commit mới nhất. Nhánh được push lên GitHub: https://github.com/CaoDat-2410/Sketch2Life/tree/feature/feat048-srs-diagram-pack.

Ở máy hiện tại, checkout gốc D:/GitHub/Sketch2Life vẫn đang ở branch FEAT-018. Hãy làm trong worktree FEAT-048 hoặc clone riêng; đừng chuyển đổi hay ghi file FEAT-018 để tiếp tục phần diagram.

## File Draw.io và các trang

Artifact chính: [Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio](artifacts/Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio). Một file gồm bốn trang:

1. **ERD** — logical/conceptual ERD dùng ký hiệu Chen: entity là hình chữ nhật, relationship là hình thoi, attribute là oval, key được gạch chân. Trang có ví dụ ký hiệu/cardinality và ghi chú phạm vi. Có 17 entity: 16 entity trong B7.1 cộng OrganizationScope. Cardinality Enrollment vẫn TBD; membershipId* là khóa episode đề xuất cho GroupMembership; purposes của ConsentRecord là thuộc tính đa trị; CanvasDocument chỉ có một chế độ owner (group XOR participant); contributorRef là tùy chọn. Đây là mô hình logic đề xuất, không phải physical schema hay SQL migration.
2. **System Architecture** — trang tổng quan gốc, có ba nhóm actor/client, backend/application/domain và boundaries ngoài. B8 được thể hiện thành chín nhóm context đề xuất; các vùng port/adapter và luồng runtime được phân biệt. Layout đã được giãn lại để tránh đường nối chồng nhau; không dùng icon.
3. **Package Diagram** — góc nhìn package/module: presentation, inbound adapters, application, domain và infrastructure adapters. Mũi tên HTTPS/WebSocket là liên kết giao thức runtime; dependency code hướng vào trong; adapter hiện thực port do application sở hữu.
4. **System Architecture v2** — trang so sánh được thêm riêng, không thay trang 2. Dùng shape Draw.io có thể sửa, bố cục kỹ thuật gọn, nhãn trạng thái bằng chữ và icon Lucide nét đơn sắc cho một số vai trò chính. Đây là cách trình bày lấy cảm hứng từ diagram cloud/AWS; không biểu thị dự án triển khai trên AWS.

Trạng thái công nghệ trên bản vẽ: Android + React Native/TypeScript và FastAPI/Python là CONFIRMED; Teacher Desktop và Super Admin là các surface đã xác nhận nhưng framework TBD. PostgreSQL, S3-compatible storage và Redis/RQ là CANDIDATE, chưa được chọn. WebSocket là PROPOSED. Firebase chỉ được thể hiện ở ranh giới Authentication cho adult identity; AI provider và payload còn TBD. Mobile không mang credential/endpoint của provider.

## Mermaid và quy tắc vẽ

- ERD: [logical-erd.mmd](src/diagrams/logical-erd.mmd)
- System Architecture trang 2: [system-overview.mmd](src/diagrams/system-overview.mmd)
- Package Diagram: [package-diagram.mmd](src/diagrams/package-diagram.mmd)
- Mermaid cho trang 4: [system-architecture-v2.mmd](src/diagrams/system-architecture-v2.mmd)
- Quy tắc status, icon, connector và cách đọc mũi tên: [ARCHITECTURE_DRAWING_RULES.md](ARCHITECTURE_DRAWING_RULES.md)
- Script tạo artifact và sửa trang v2: [build_drawio.py](src/build_drawio.py), [add_system_architecture_v2.py](src/add_system_architecture_v2.py)
- Icon nguồn và thông tin license: assets/icons/lucide-v1.61.0/.

Preview catalog icon, preview kiến trúc theo phong cách AWS trung lập và các bản preview trước nằm trong evidence/rendered/. Chúng là tài liệu xem trước; artifact chính là file Draw.io phía trên.

## Những gì đã làm ở các lượt tạo diagram trước

- Đọc SRS chuẩn trên baseline dev và dựng ba diagram được giao cùng Mermaid sources.
- Rà soát và chỉnh ERD theo ký hiệu Chen; sửa ba quan hệ bị đứt và chiều cardinality authorizes; thêm một số liên kết/ràng buộc chọn lọc từ B21.5; làm legend bằng hình thật.
- Sắp xếp lại System Architecture để tách actor, application/domain, ports/adapters và ranh giới dịch vụ; giữ các lựa chọn hạ tầng chưa chốt ở trạng thái đề xuất/candidate.
- Tạo trang System Architecture v2 kèm Mermaid, drawing rules và bộ icon Lucide v1.61.0. Cùng file Drive được cập nhật tại chỗ, giữ nguyên ID và ba trang gốc.
- Sửa lỗi icon bị hiện broken-image: Draw.io tách style bằng dấu chấm phẩy, nên URI data:image/svg+xml;base64,... bị cắt ở ;base64. Builder hiện percent-encode SVG thành data:image/svg+xml,<payload>, rồi decode và parse XML để kiểm tra.
- Build/readback gần nhất: bốn trang; ERD 168 cells, System Architecture 36, Package Diagram 38, v2 107 cells (81 vertices, 24 edges, hai root). Trang v2 có 20 image cells dùng 16 loại icon; 20/20 URI giải mã thành SVG XML, không có URI base64 sai kiểu; 24 connector có endpoint hợp lệ; fingerprint ba trang gốc không đổi.
- Hai commit gốc đã tạo và push riêng trên branch FEAT-048. Không merge vào dev, không sửa FEAT-018.

## Việc đã làm trong lượt handoff hiện tại

- Mở rộng HANDOFF_FOR_NEW_SESSION.md thành tài liệu tiếng Việt độc lập, ghi nguồn SRS, nhánh/base, bốn trang Draw.io, bốn nguồn Mermaid, trạng thái công nghệ, công việc đã xong, Drive và các bước tiếp theo cho máy khác.
- Đồng bộ HANDOFF.md, CONTEXT.md, status/STATUS.md và status/FINAL_STATUS.md với trạng thái thật: branch đã được push, visual QA còn pending, checkout gốc ở FEAT-018.
- Khi rà lại Mermaid và Draw.io để mô tả chính xác, phát hiện chênh lệch ERD 22 dòng Mermaid so với 21 hình thoi có tên trên Draw.io; handoff đánh dấu đây là việc cần đối chiếu, chưa tự ý sửa diagram.
- Repository security và architecture validation đạt; harness vẫn chỉ báo thiếu evidence/screenshots và evidence/metrics ở FEAT-045/046/047. Diff check đạt, có cảnh báo line ending tự đổi CRLF/LF trên Windows.

## Điểm phải đối chiếu trước khi gọi bản Mermaid là tương ứng hoàn toàn

Có một chênh lệch đã phát hiện trong hồ sơ: Draw.io ERD hiện có 21 hình thoi quan hệ được đặt tên (16 quan hệ B7.1 + 5 liên kết B21.5) và một hình thoi minh họa trong legend. Mermaid logical-erd.mmd hiện có 22 dòng quan hệ vì thêm AdultAccount — TeacherReview: reviewer_ref. Ghi chú ERD trước đó xem reviewerRef là reference attribute, không phải relationship diamond riêng trên trang Draw.io. Phiên mới cần mở hai nguồn, đối chiếu B21.5 và quyết định đồng bộ representation; đừng khẳng định hai bản tương đương hoàn toàn trước khi xử lý.

Các caveat khác vẫn cần giữ: cardinality Enrollment TBD; khóa membershipId* chỉ là đề xuất; B7.1 là subset, không phải toàn bộ 34 entity của B7; TeacherReview có target_kind tổng quát hơn SketchProposal.

## Trạng thái kiểm tra và phần cần làm tiếp

Kiểm tra cấu trúc XML, endpoint, icon URI và Drive raw readback đã đạt. Repository security và architecture validation đạt. Harness toàn repository hiện còn báo thiếu evidence/screenshots và evidence/metrics ở FEAT-045, FEAT-046, FEAT-047; FEAT-048 không có lỗi harness.

Chưa hoàn tất visual QA của artifact trong diagrams.net. Không có renderer/editor diagrams.net trong phiên trước nên chưa có screenshot chứng minh trang v2 hiển thị icon ở mức zoom bình thường. Mermaid render comparison cũng còn pending.

Thứ tự tiếp tục:

1. Pull branch mới nhất và đọc file này, CONTEXT.md, HANDOFF.md, status/STATUS.md cùng các review notes dưới evidence/notes/.
2. Mở artifact Draw.io trên diagrams.net, kiểm tra cả bốn trang ở zoom đọc được; đặc biệt refresh trang System Architecture v2 để xác nhận 20 icon không còn broken-image và connector không chồng/đứt. Lưu screenshot vào evidence/screenshots/.
3. Đối chiếu/fix discrepancy ERD Mermaid 22 quan hệ với 21 hình thoi có tên trong Draw.io, rồi cập nhật review evidence/metrics nếu kết luận thay đổi.
4. Render Mermaid và so ngữ nghĩa với các trang Draw.io; cập nhật status/evidence theo kết quả thật.
5. Nếu cần sửa Drive, đọc phiên bản Drive hiện tại trước, giữ cùng file ID/folder và owner edits, sau đó readback xác nhận.
6. Trước commit/push, chạy python tools/validate_repository_security.py theo AGENTS.md. Ghi kết quả kiểm tra; không sửa các feature FEAT-045–047 trong task này.

## Google Drive

- Draw.io đang nằm trong folder người dùng chỉ định: 18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0.
- File ID: 1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x.
- [Mở file Draw.io trên Drive](https://drive.google.com/file/d/1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x/view).
- Readback gần nhất ghi nhận 134,056 bytes và modified 2026-10-22T17:14:24.595Z. Đây là xác minh raw/XML, chưa phải xác nhận bằng ảnh render trong diagrams.net.

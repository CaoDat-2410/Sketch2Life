# Bàn giao FEAT-048 cho phiên Codex trên máy khác

## Trạng thái hiện tại — ERD đã rà soát và vẽ lại, 2026-10-23

- Plan 25 / approval 25: rà lại B7.1/B21.5 không thấy relationship/cardinality lỗi mới. Draw.io giữ 17 entity/21 relationship/37 thuộc tính được chọn; đã ghi rõ không phải full schema, chuyển ConsentRecord khỏi `id` của PortfolioEntry và route `protected` qua khoảng riêng. Render cuối không có shape chồng, cạnh treo hay vertex vượt trang; Mermaid 12.2.0 render 17/21/37.
- Draw.io hiện có 4 tab theo thứ tự owner: ERD / System Architecture / System Architecture v2 / Package Diagram. Bản local 154,082 bytes, SHA-256 `b5b33a5f55ccdf88971f686e7d572537f6268620e23dd042238447b2562aa040`. Ba tab ngoài ERD giữ nguyên.
- Render screenshot local: `evidence/screenshots/erd_final_refinement_20261023_r2.png` (3372×1987); metadata, ảnh, SVG và helper không đưa lên GitHub. Metrics/chi tiết audit: `evidence/notes/ERD_FINAL_AUDIT_AND_LAYOUT_20261023.md`, `evidence/metrics/ERD_FINAL_REFINEMENT_VALIDATION_20261023.json`.
- Mermaid chuẩn: `src/diagrams/logical-erd.mmd` (17/21/37) và `src/diagrams/system-architecture-v2.mmd` (14/19). Branch hiện có các commit `2432fd0e`, `197048d7`, `632a9b4c`; cập nhật ERD hiện tại sẽ được publish riêng trên `feature/feat048-srs-diagram-pack`. PNG/SVG render, script tạo/render, SVG icon rời, wrapper trùng và file baseline/readback Drive không được đưa lên.
- Same-ID Drive update bị automatic approval review từ chối; Drive vẫn ở bản cũ 153,149 bytes, modified `2026-10-23T05:11:21.479Z`. Không thử đường upload khác; cần owner xác nhận rõ trước lần thay file Drive tiếp theo. Xem `evidence/notes/ERD_REPAIR_20261023.md` và `evidence/metrics/ERD_REPAIR_VALIDATION_20261023.json`.
- Các mục dưới tiêu đề “lịch sử” ghi trạng thái tại thời điểm đó; nếu khác phần này thì dùng phần hiện tại.

## Lịch sử — ERD recheck trước khi sửa — 2026-10-23

- Plan 22 / approval 23: review hoàn tất, ERD vẫn NOT_READY. Sáu diamond rời đầu nối (12 target chưa gắn), ba cardinality đảo và một số đường đi xuyên sau khối khác/trùng nhau.
- Đã kiểm tra bản Drive mới nhất và render ERD thực tế 3401×1987; file/source/Drive giữ nguyên. Mermaid hiện render được, khớp 17 entity/21 quan hệ/37 thuộc tính; lỗi cú pháp và reviewerRef đã hết.
- Chi tiết ID, dòng SRS, cách đọc cardinality và thứ tự sửa: evidence/notes/ERD_RECHECK_20261023.md; metrics và screenshot trong evidence/. Chưa thực hiện sửa ERD trong lượt review này.


## Cập nhật sau cùng — logo chính chủ và hai mã Mermaid, 2026-10-23

- Plan 21 / approval 22 hoàn tất: v2 có logo chính chủ FastAPI, Firebase, React Native, PostgreSQL, Redis và giữ chín icon AWS cho các vai trò còn lại. Chỉ năm ô ảnh thay đổi; 14 component, 19 luồng, nhãn/trạng thái/bố cục và ba tab khác giữ nguyên.
- Đã render/review v2 thực tế ở 3168×1692; ảnh và metadata render được giữ làm evidence local, loại khỏi GitHub. Provenance/hashes/usage terms dạng text của SVG gốc nằm trong các manifest và NOTICE; SVG rời bị loại.
- Hai file nguồn Mermaid chuẩn: src/diagrams/logical-erd.mmd (17 entity, 21 quan hệ, 37 thuộc tính hiển thị) và src/diagrams/system-architecture-v2.mmd (14/19). Cả hai render Mermaid 12.2.0 thành công; wrapper gộp bị loại vì trùng nội dung.
- ERD Mermaid đã hết lỗi cú pháp và thống nhất reviewerRef là thuộc tính. Ba cardinality bị đảo vẫn được giữ để khớp bản vẽ, sáu quan hệ rời đầu nối được mô tả theo ý định; đã ghi rõ hạn chế. Chưa sửa mô hình/connector ERD trong Draw.io.
- Drive cùng ID đã cập nhật/readback: 153.149 bytes, modified 2026-10-23T05:11:21.479Z, SHA-256 4d5e2f54e0066b8f9e95108ce593ad426ba221c6d89bd43860679ccad3a4ac39, khớp artifact/render. Chưa commit/push; SRS/runtime/schema không đổi.
- Evidence: evidence/notes/TECHNOLOGY_LOGOS_AND_MERMAID_20261023.md và ERD_MERMAID_EXPORT_20261023.md; metrics và raw readback trong evidence/.

## Checkpoint trước — bỏ note thừa và vẽ gọn v2, 2026-10-23

- Plan 20 / approval 21: đã bỏ tám cell note/legend/subtitle/footer thừa, dùng nền trắng, khung mảnh, nhãn ngắn và đường nối rõ; giữ 14 component, 19 luồng và 14 SVG AWS gốc.
- Canvas 3200×1740; ảnh render diagrams.net thực tế 3168×1692. Diagram-architect và senior-architect đều PASS. Giữ thứ tự tab mới của owner: ERD / System Architecture / System Architecture v2 / Package Diagram; ba tab còn lại giữ nguyên fingerprint.
- Cùng file Drive đã cập nhật/readback 154.128 bytes, modified 2026-10-23T04:50:38.358Z; SHA-256 81d34b919b98b03990044b159accba0e9a424c05637f553a98a08f3156007378, giống artifact đã review. Ảnh: evidence/screenshots/system_architecture_v2_clean_20261023.png.
- Nguồn, provenance AWS và các lưu ý bảo mật/async/CRDT chuyển vào evidence/notes/SYSTEM_ARCHITECTURE_V2_CLEAN_REVIEW_20261023.md. Các lỗi ERD cũ vẫn mở; chưa commit/push.

## Checkpoint trước — nới rộng v2 và review, 2026-10-23

- Plan 19 / approval 20: đã nới canvas v2 lên 3200×2000, tăng gutter, chiều cao hàng, cỡ chữ và icon. Giữ nguyên 14 component, 19 luồng và SVG AWS General/Category gốc.
- Đã review bằng diagram-architect và senior-architect sau render diagrams.net thực tế; không còn finding chặn trong phạm vi kiến trúc logic/bố cục v2. Nội dung và chữ ký 19 quan hệ giống bản Drive mới đọc; ba tab gốc giữ nguyên.
- Cùng file Drive đã cập nhật và readback: 158.482 bytes, modified 2026-10-23T04:26:02.598Z, SHA-256 790d2e3981d4c1736bba0b6ad7cb097432aea0e3b6dfe3e0a7bdcbaf8509d614. Ảnh mới: evidence/screenshots/system_architecture_v2_wide_20261023.png.
- Review/evidence: evidence/notes/SYSTEM_ARCHITECTURE_V2_SPACING_REVIEW_20261023.md. Các lỗi ERD đã ghi trước vẫn cần lượt sửa riêng; chưa commit/push.

## Cập nhật mới nhất — AWS v2 và rà soát hai diagram, 2026-10-23

- Plan 18 / approval 19: đã dùng diagram-architect, database-architect và senior-architect để rà file thực tế theo SRS B3/B7/B7.1/B8/B21.5.
- Tab System Architecture v2 đã đổi từ Lucide sang SVG gốc trong gói AWS Architecture Icons 2026-07-31 (General Light / Category). Có 14 component chính, 14 icon, 19 connector; render diagrams.net và Mermaid đã đạt, không còn broken-image. Đây là kiến trúc logic; chưa chọn dịch vụ/deployment AWS.
- Đã cập nhật cùng file Drive ID 1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x, giữ folder cũ. Readback 158.272 bytes, modified 2026-10-23T04:09:01.423Z; SHA-256 f39862a42fc6da9ead34225b707419d8d4b0c66d662770072f3071cc73dc21e9, giống hệt local.
- Ba tab gốc được giữ nguyên theo fingerprint của bản Drive mới đọc. Tuy nhiên ERD hiện NOT_READY: sáu hình thoi chưa được gắn connector (12 đầu target rời), ba cardinality ownership/contributor bị đảo, Mermaid ERD lỗi parse 12.2.0 và còn chênh representation reviewer_ref. Chưa sửa ERD trong lượt phân tích này.
- Chi tiết: evidence/notes/DUAL_DIAGRAM_REVIEW_20261023.md; ảnh kiểm tra thật trong evidence/screenshots/. Các kết luận cũ về ERD zero-dangling và v2 còn dùng Lucide bên dưới là lịch sử, không phải trạng thái hiện tại.
- Checkout hiện tại đã ở branch FEAT-048 tại repository root; FEAT-018 ở worktree riêng. Phần AWS/redraw/review mới chưa commit/push. Không merge dev.

## Bản bàn giao trước — lưu lịch sử

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

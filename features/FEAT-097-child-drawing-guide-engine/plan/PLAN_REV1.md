# FEAT-097 Plan Rev 1: hướng dẫn vẽ trẻ theo được

- **Trạng thái:** `AWAITING_APPROVAL`. Chưa được triển khai.
- **Ngày:** 2026-11-27. **Cơ sở:** [bối cảnh](../CONTEXT.md), [nghiên cứu](../research/SVG_GUIDE_RESEARCH.md),
  ảnh hiện trạng và mẫu thử trong `../evidence/baseline/`.

## 1. Mục tiêu

Trẻ 3–10 tuổi nhìn điện thoại phụ huynh và **vẽ theo được ra giấy**: mỗi bước ít nét, biết đặt bút ở đâu và đi hướng
nào, vẽ xong nhận ra đúng con vật hay đồ vật. Chủ thể hay gặp luôn có sẵn; chủ thể lạ có bản nháp AI do người lớn duyệt.

## 2. Đã chốt và đề xuất

| # | Nội dung | Nguồn |
|---|---|---|
| Q1 | Hai mức: `beginner` (3–5 tuổi) và `simple` (6–10) | chủ sở hữu |
| Q2 | Mức nhỏ ghép hình khối (A), mức lớn nét viền đơn giản (B) | chủ sở hữu |
| Q3 | Chấm bắt đầu + mũi tên; hình động từng nét; không giọng đọc, không đồ ngón tay | chủ sở hữu |
| D1 | Chủ thể hay gặp: **thư viện công thức soạn tay**. Chủ thể lạ: **AI soạn công thức**, không sinh SVG tự do | đề xuất |
| D2 | Đợt đầu 40 chủ thể, đúng danh sách 40 thẻ kiến thức của FEAT-094, mỗi chủ thể hai mức (80 công thức) | đề xuất |
| D3 | Bỏ Openclipart, OpenMoji, Arcadia khỏi luồng Parent (giữ tệp và ghi công, không dùng làm nguồn) | đề xuất |
| D4 | Chủ sở hữu duyệt công thức, trừ khi chỉ định giáo viên | đề xuất |

## 3. Thiết kế

### 3.1 Công thức vẽ (`DrawingRecipeV1`, dữ liệu, không phải SVG)

Lưới 0–100. Mỗi bước: tên bộ phận, câu hướng dẫn, vài nét. Nét thuộc bộ từ vựng đóng: `circle`, `oval`, `arc`,
`curve`, `line`, `polyline`, `triangle`, `dot`; mỗi nét có điểm bắt đầu và chiều vẽ.

```json
{"subject": "con gà", "level": "beginner",
 "steps": [{"part": "thân", "instruction_vi": "Vẽ một hình tròn to làm thân.",
            "strokes": [{"shape": "circle", "center": [45, 62], "radius": 22, "start": "top"}]}]}
```

Bộ dựng bằng code đổi công thức thành đúng hợp đồng hiện có `SvgTopicStrokeGuideV1` + `SvgDocumentV1` (chỉ lệnh
`M L C Q Z`). Hợp đồng HTTP không đổi; app cũ vẫn đọc được.

### 3.2 Luật theo mức (số đề xuất, chỉnh ở giai đoạn 1)

| Luật | Mức nhỏ | Mức lớn |
|---|---|---|
| Số bước (SRS: 4–8) | 4–6 | 5–8 |
| Nét mới mỗi bước | ≤ 2 (chân, mắt tính theo cặp) | ≤ 3 |
| Tổng số nét | ≤ 12 | ≤ 20 |
| Hình được dùng | tròn, bầu dục, đoạn thẳng, chấm, tam giác, cung | tất cả |
| Hình nhỏ nhất | 8% khung (trừ chấm mắt) | 5% |
| Thứ tự | phần to trước, chi tiết sau | như trên |

Cổng code cho mọi công thức (tay hay AI): nằm trong khung; nét mới chạm hoặc gần hình đã có; không nét trùng; đủ số
bước và số nét; câu hướng dẫn ≤ 12 tiếng và nêu đúng tên bộ phận của bước.

### 3.3 Hiển thị trên app

Nét cũ liền, nét mới **đứt và nổi màu** (đúng SRS 6.2.1; hiện đang vẽ liền). Chấm xanh ở điểm đặt bút, mũi tên theo
hướng đi, tính từ đường nét. Các nét của một bước **chạy lần lượt**, có nút "Xem lại". Hình hoàn chỉnh xem được cạnh
bên. Nét dày, nền trắng. Mức chọn theo tuổi hồ sơ nhưng chỉ gửi `difficulty` (không gửi tuổi, đúng FR-AI-15); phụ
huynh đổi mức được.

### 3.4 AI cho chủ thể lạ

1. Worker Qwen (vLLM đang chạy) nhận **chỉ chủ đề và mức**, trả công thức theo JSON schema; ví dụ mẫu lấy từ thư viện
   cùng nhóm (bốn chân, chim, xe…).
2. Soạn 2–3 bản; loại bản trượt cổng code.
3. Dựng hình, hỏi Qwen "hình này là gì?" mà không cho biết chủ đề; giữ bản được nhận đúng.
4. Người lớn thấy bản nháp có nhãn "AI soạn, hãy xem trước", chọn dùng hoặc làm lại.
5. Bản được chấp nhận vào hàng chờ duyệt của thư viện; **không tự công bố**.
6. Tắt, lỗi hoặc không bản nào đạt: báo rõ và vẫn chụp tranh được (BR-46).

Không dùng FLUX. Không nhận SVG hay HTML từ model.

## 4. Giai đoạn

| GĐ | Nội dung | Xong khi | GPU |
|---|---|---|---|
| 0 | Công thức, bộ dựng, cổng kiểm; 4 chủ thể (gà, bướm, rùa, chó) × 2 mức | test qua; có bảng ảnh từng bước | không |
| 1 | Màn hiển thị: chấm, mũi tên, nét đứt, chạy lần lượt, xem lại; dùng công thức mới thay clipart | bạn xem trên giả lập và chấm 4 chủ thể; chốt số ở 3.2 | không |
| 2 | Soạn 36 chủ thể còn lại, duyệt theo đợt nhóm (vật nuôi, chim, côn trùng, biển, xe, cây hoa) | bạn duyệt từng bảng ảnh | không |
| 3a | Thử AI: 20 chủ đề lạ × 3 bản, đo tỉ lệ qua cổng, tỉ lệ nhận đúng và bạn chấm | ≥ 14/20 chủ đề có ít nhất một bản bạn chấp nhận; nếu không đạt thì dừng, hỏi lại | Qwen khoảng 20–30 phút (ước tính) |
| 3b | Đưa luồng AI vào app (worker, API, màn duyệt) | test và một lượt thật | Qwen, ít |

Giai đoạn 0–2 không tốn GPU. 3a cần bạn đồng ý riêng trước khi chạy.

## 5. Tiêu chí nghiệm thu

| # | Tiêu chí |
|---|---|
| A1 | 100% công thức trong thư viện qua cổng kiểm (test tự động) |
| A2 | Mức nhỏ: mọi hướng dẫn ≤ 12 nét, mỗi bước ≤ 2 nét mới (hoặc 1 cặp) |
| A3 | Mọi bước: câu hướng dẫn nói đúng phần đang tô (người duyệt xác nhận trên bảng ảnh) |
| A4 | Người duyệt nhận ra chủ thể ở hình hoàn chỉnh của mọi công thức được duyệt |
| A5 | App hiện chấm bắt đầu, mũi tên, nét đứt cho bước mới, chạy lần lượt, xem lại được |
| A6 | Cả 40 chủ thể và tên gọi thường gặp (có hoặc không có "con", không dấu) tìm ra hướng dẫn |
| A7 | Chủ đề lạ: bản nháp AI có nhãn; hỏng thì không chặn chụp tranh |
| A8 | Dữ liệu gửi model chỉ gồm chủ đề và mức (test tự động) |

## 6. Không làm

Giọng đọc, đồ ngón tay, chấm điểm tranh của trẻ, guide của Teacher, đổi catalog Openclipart trên Modal, huấn luyện
hoặc thêm model mới. **Không đo được** trẻ vẽ tốt hơn hay không: muốn biết cần cho trẻ thật dùng thử, phải xin phép
riêng.

## 7. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Hình ghép khối trông đơn điệu hoặc khó nhận ra với vài con vật | duyệt bằng mắt từng đợt; thêm hình vào bộ từ vựng |
| Soạn 80 công thức mất công | bắt đầu 4, đo thời gian một công thức rồi mới làm đại trà |
| Qwen soạn công thức kém | giai đoạn 3a có ngưỡng dừng; thư viện vẫn dùng độc lập |
| Số luật theo mức chưa dựa trên bằng chứng | ghi là đề xuất, chỉnh sau khi bạn xem |
| Quyết định D3 bỏ clipart làm mất 0 chủ thể nhưng đổi nguồn đã duyệt trong SRS "catalog" | công thức được duyệt chính là catalog; nếu bạn muốn sửa lời SRS thì cần duyệt riêng |

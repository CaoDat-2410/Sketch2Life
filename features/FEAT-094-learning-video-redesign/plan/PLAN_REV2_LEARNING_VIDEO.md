# FEAT-094, Plan Rev 2: video học tập bằng LTX-2.5 (nội dung, chất lượng, tốc độ)

- **Trạng thái:** `AWAITING_APPROVAL`. Chưa được triển khai.
- **Ngày:** 2026-11-26. Thay Rev 1 theo góp ý của chủ sở hữu: nâng giới hạn từ; không chạy nhiều L40S để render song song;
  kiến thức ưu tiên chủ thể chính; các mục còn lại chủ sở hữu không có ý kiến.
- **Cơ sở:** SRS FEAT-063 v2.7-draft (chưa ký); hai lần chạy thật của FEAT-093; [nghiên cứu chất lượng](../research/LTX25_QUALITY_RESEARCH.md);
  [ghi chú tốc độ](../research/LTX25_SPEED_NOTES.md); câu trả lời của chủ sở hữu ngày 2026-11-26.

## 1. Mục tiêu

Sau khi xem một video, trẻ biết thêm vài điều **đúng** về sự vật mình vẽ: nó là gì, cấu tạo ra sao, dùng để làm gì.
Video là **một câu chuyện** lồng kiến thức, hợp tuổi và sở thích của trẻ, giữ nhận ra được tranh gốc, không thêm người
hay vật lạ, và phụ huynh không phải chờ quá lâu.

### 1.1 Quyết định đã chốt

| # | Quyết định | Nguồn |
|---|---|---|
| Q1 | LTX-2.5 dựng **mọi** cảnh (giữ đúng BR-45; không làm hướng cắt giấy 2D) | chủ sở hữu |
| Q2 | Kiến thức lấy từ **kho đã duyệt, AI bổ sung** khi kho không có | chủ sở hữu |
| Q3 | Cấu trúc là **truyện có lồng kiến thức** | chủ sở hữu |
| Q4 | **Không** có câu hỏi hay tương tác; chỉ một câu chuyện cung cấp kiến thức | chủ sở hữu |
| Q5 | **Phải tối ưu tốc độ** sinh video | chủ sở hữu |
| Q6 | **Nâng giới hạn từ** mỗi cảnh so với Rev 1 | chủ sở hữu |
| Q7 | **Không** chạy nhiều L40S để render cảnh song song | chủ sở hữu |
| Q8 | Kiến thức **ưu tiên chủ thể chính** của bức tranh | chủ sở hữu |
| D1 | Có nhãn tên bộ phận và mũi tên (8.2) | đề xuất, chủ sở hữu không có ý kiến |
| D2 | Cảnh vẫn lỗi sau 2 lần sinh lại thì báo lỗi cả video (đúng FR-AI-06) | như trên |
| D3 | Chủ sở hữu là người duyệt thẻ kiến thức, trừ khi chỉ định người khác | như trên |

### 1.2 Không làm

Câu hỏi/quiz trong video; hoạt hình cắt giấy hoặc PixiJS; đổi model video; nhạc nền (BR-24); dùng dữ liệu trẻ thật
(BR-27); đổi sang model/API video trả phí.

## 2. Hiện trạng và vì sao cần làm lại

| # | Vấn đề | Bằng chứng |
|---|---|---|
| P1 | Video gần như không dạy gì. Trẻ 3–5 tuổi: 5 cảnh, mỗi câu tối đa **7 từ**, tổng khoảng 35 từ | `age_profile.py`; phụ đề Run 1: "Bé nhìn kỹ chiếc xe." |
| P2 | Phụ huynh xác nhận một văn bản, video đọc **văn bản khác**: truyện được sinh, rồi một lượt model thứ hai viết lại lời cho video | Run 1: truyện và phụ đề khác nhau |
| P3 | Không có nguồn kiến thức: model tự viết, có câu vô nghĩa ("bộ phận… giúp dễ nhìn đường") | benchmark M12 |
| P4 | Không dùng sở thích của trẻ khi viết truyện (ADR-0024 loại ra) | ADR-0024 mục 3 |
| P5 | Người không có trong tranh xuất hiện ở cảnh 5. Khung đầu cảnh sạch, nên LTX tự vẽ thêm | khung 24,0 giây của Run 1 |
| P6 | Prompt LTX chủ yếu là lệnh cấm, có câu "thêm đạo cụ được nêu tên"; không neo khung cuối; không kiểm tra hình | nghiên cứu F1–F3, F7 |
| P7 | Video có dải trắng 24 px trên/dưới, không đúng 16:9 | nghiên cứu F5 |
| P8 | Tranh cắt còn mảng giấy trắng giữa nan hoa; vật lơ lửng (đã sửa, chưa kiểm chứng) | khung đầu cảnh 5 |
| P9 | Chậm: Run 1 mất **14 phút** cho video 30 giây | bảng ở mục 9.1 |
| P10 | Run 2 dừng ở bước hoạt động: backend loại cả danh sách hai lần (`EXPLORATION_NOT_EXPLICIT`) | log API 2026-11-26 |

## 3. Luồng mới

```
Tranh ─► nhận diện vật + bộ phận nhìn thấy ─► phụ huynh xác nhận chủ thể
                                              │
Hồ sơ (tuổi, thẻ sở thích đã duyệt) ──────────┤
Kho kiến thức / bài học đã ghim / AI soạn ────┤
Hoạt động đã chọn ────────────────────────────┘
                                              ▼
                      MỘT "kịch bản học" (truyện + kiến thức + chỉ dẫn hình)
                      ─► cổng kiểm tra ─► phụ huynh đọc và xác nhận ĐÚNG văn bản này
                                              ▼
      mỗi cảnh: ghép tranh + nền ─► kiểm khung ─► LTX-2.5 ─► kiểm video ─► (lỗi: sinh lại, tối đa 2 lần)
                                              ▼
                      giọng đọc + phụ đề + (nhãn bộ phận) ─► ghép ─► kiểm cuối ─► phát
```

Thay đổi lớn nhất: **bỏ lượt viết lại lời cho video**. Văn bản phụ huynh xác nhận chính là lời đọc.

## 4. Kiến thức

### 4.1 Thứ tự nguồn

1. Bài học giáo viên đã ghim vào buổi (`subject_learning_notes`, đúng phiên bản và hash), đúng UC-02.
2. **Thẻ kiến thức đã duyệt** trong kho.
3. **AI soạn nháp** khi hai nguồn trên không có; gắn nhãn *chưa kiểm chứng*.

### 4.2 Thẻ kiến thức

```json
{
  "card_id": "vi.transport.bicycle", "version": 1, "status": "APPROVED",
  "subject_labels": ["xe đạp"], "topic_ids": ["transport"],
  "facts": [
    {"id": "what", "kind": "WHAT_IT_IS", "min_age_months": 36,
     "text": "Xe đạp là phương tiện đi lại bằng cách đạp chân.", "key_terms": ["xe đạp", "đạp"]},
    {"id": "wheel", "kind": "PART", "part": "bánh xe", "min_age_months": 36,
     "text": "Hai bánh xe lăn giúp xe tiến về phía trước.", "key_terms": ["bánh xe", "lăn"]},
    {"id": "use", "kind": "USE", "min_age_months": 36, "text": "Người ta đi xe đạp để đến trường hoặc đi dạo.", "key_terms": ["đi"]}
  ],
  "motion_hints": ["bánh xe lăn", "xe tiến nhẹ"], "setting": "đường nhỏ trong công viên",
  "sources": [{"title": "...", "url": "...", "checked_on": "2026-..-.."}],
  "reviewed_by": "...", "reviewed_on": "..."
}
```

Kiến thức chỉ viết cho **chủ thể chính** mà phụ huynh đã xác nhận. Vật phụ được xuất hiện trong hình và trong truyện
nhưng không có sự thật riêng.

Quy tắc: mỗi sự thật một ý, có từ khóa, có độ tuổi tối thiểu, có nguồn. Thẻ đã duyệt là bất biến; sửa thì tăng phiên
bản. Buổi học lưu `card_id`, `version`, hash để truy vết.

### 4.3 Phạm vi ban đầu

Danh mục hiện có 18 chủ đề, 162 chủ thể. Đợt 1: **40 thẻ** cho các chủ thể **hay là chủ thể chính** của tranh (động
vật, phương tiện, chim, côn trùng, biển, cây và hoa). Vật thường chỉ làm nền như mặt trời, cỏ để sau. Đợt 2: đủ 162. AI được dùng để soạn nháp thẻ; **chỉ người duyệt** mới chuyển sang `APPROVED`.

### 4.4 AI soạn khi không có thẻ

Qwen sinh đúng cấu trúc thẻ (không có nguồn). Cổng kiểm: tiếng Việt, không y tế/nguy hiểm, mỗi câu ngắn và đủ ý, một
lượt Qwen thứ hai đóng vai người kiểm chỉ ra câu đáng ngờ để bỏ. Màn xác nhận kịch bản hiện rõ nhãn
"Thông tin do AI soạn, hãy kiểm tra". Thẻ nháp không tự vào kho. Rủi ro còn lại: vẫn có thể sai.

## 5. Cá nhân hóa theo hồ sơ trẻ

| Dữ liệu | Dùng để | Giới hạn |
|---|---|---|
| Tuổi theo tháng | số cảnh, độ dài câu, số sự thật, độ khó từ | bắt buộc |
| Sở thích (chỉ **thẻ trong danh sách cho phép**, đã nằm trong snapshot phụ huynh duyệt) | bối cảnh, cách mở truyện, ví von | không đổi sự thật; không gửi tên hay chữ tự do |
| Ý tưởng của gia đình | hướng truyện | là dữ liệu, không phải lệnh |
| Lịch sử, thành tích, ghi chú sức khỏe | **không dùng** trong đợt này | BR-20, BR-21 |

Cần ADR mới thay mục 3 của ADR-0024 (đang cấm gửi sở thích cho bước viết truyện). Nếu không có sở thích hợp lệ, truyện
vẫn viết bình thường.

## 6. Kịch bản học (một văn bản duy nhất)

### 6.1 Mạch truyện

Nhân vật chính là chính sự vật trong tranh. Mỗi cảnh đẩy truyện một bước và mang **đúng một sự thật**.

| Cảnh | Vai trò | Kiến thức |
|---|---|---|
| 1 | Mở truyện bằng chi tiết thấy trong tranh | Nó là gì (gọi tên) |
| 2…n−2 | Nhân vật làm một việc, bộ phận liên quan hoạt động | Mỗi cảnh một bộ phận: tên và việc nó làm |
| n−1 | Sự việc được giải quyết nhờ công dụng của vật | Nó dùng để làm gì |
| n | Kết ấm áp, nhắc lại tên và các bộ phận trong một câu | Ôn lại, không hỏi |

### 6.2 Bảng tuổi

| Tuổi | Cảnh × giây | Tổng | Từ tối đa mỗi cảnh | Từ cả video | Sự thật |
|---|---|---|---|---|---|
| 3–5 | 5 × 10 | 50 s | **18** | 90 | 3 |
| 6–8 | 6 × 10 | 60 s | **22** | 132 | 4 |
| 9–10 | 7 × 10 | 70 s | **24** | 168 | 5 |

So sánh với trẻ 3–5 tuổi: hiện tại 7 từ mỗi cảnh (35 cả video), Rev 1 đề xuất 12, nay 18.

- Mỗi cảnh viết thành **1–2 câu ngắn**; với trẻ 3–5 tuổi mỗi câu không quá 10 từ, giữa hai câu có quãng nghỉ.
- Một giọng đọc, bỏ lời thoại. Cảnh dài 10 s để câu dài nhất vẫn đọc kịp ở tốc độ hiện có; test tính lại bảng này.
- Nằm trong 30–90 s và 5–15 cảnh (BR-24, BR-45); một cảnh LTX dài tối đa khoảng 19,7 s.
- Giữ ít cảnh vì mọi cảnh render lần lượt trên một máy (Q7).

### 6.3 Đầu ra của model (JSON)

`title`, `learning_points[] {fact_id, key_terms}`, `scenes[] {index, fact_id|null, narration, key_term, part|null,
action_en, setting_en, camera: "static"}`.

- `action_en`: một chuyển động vật lý của **vật đã vẽ**, bằng tiếng Anh, không người, không đạo cụ mới.
- `setting_en`: nền, không nhân vật.
- Truyện hiển thị cho phụ huynh được ghép từ `narration` của các cảnh.

### 6.4 Cổng kiểm tra (tự sinh lại, tối đa 3 lượt)

1. Mỗi sự thật được chọn xuất hiện đúng cảnh, đủ `key_terms`.
2. Không có khẳng định kiến thức ngoài danh sách (một lượt Qwen kiểm đối chiếu).
3. Tên sự vật lặp ít nhất 3 lần; mỗi câu trọn ý, đúng giới hạn tuổi.
4. Nhân vật chính là sự vật; không chuyển sang "bé".
5. `action_en`, `setting_en` không chứa người hay vật ngoài tranh (đã có bộ lọc, dùng làm lớp chặn).
6. An toàn nội dung theo chính sách hiện có.

Lưu ý: cổng 1, 3, 5 là kiểm tra chắc chắn bằng code; cổng 2 dựa vào model nên không tuyệt đối. Người lớn xác nhận là
lớp cuối.

### 6.5 Hỗ trợ ghi nhớ

Áp dụng: chia nhỏ mỗi cảnh một ý; lời và chuyển động cùng nói về một bộ phận; lặp tên; ôn ở cảnh cuối; bỏ chi tiết
thừa. Nên thêm **nhãn tên bộ phận** hiện khi cảnh nói tới (xem 8.2).

Mức bằng chứng: các nguyên tắc đa phương tiện và chia đoạn có tổng quan nghiên cứu nhưng chủ yếu ở người lớn hoặc nhiều
lứa tuổi; bằng chứng riêng cho 3–6 tuổi mà tôi tìm được còn mỏng. Demo chỉ dùng dữ liệu tổng hợp nên **không đo được**
trẻ có nhớ lâu hơn hay không; muốn đo cần một nghiên cứu được phép, ngoài phạm vi này.

## 7. Chất lượng hình

### 7.1 Khung đầu và khung cuối

| Việc | Chi tiết |
|---|---|
| Sửa khung hình | Dùng 1280×720 xuyên suốt (render 1280×768 rồi cắt, không chèn dải trắng); sửa bộ ghép và bộ kiểm |
| Cắt tranh sạch | Trong mask, điểm gần màu giấy được trả về nền (hết mảng trắng giữa nan hoa); giữ viền nét |
| Đặt vật | Đứng trên mặt đất (đã sửa), thêm bóng tiếp đất nhẹ; vật bay/bơi giữ độ cao |
| Nền | Prompt nền lấy từ `setting_en` và thẻ kiến thức, hợp với truyện, không người |
| Cỡ và bố cục | Vật chính đủ lớn để thấy bộ phận đang nói tới; cảnh nói về một bộ phận thì khung gần hơn |
| Kiểm khung | Qwen nhìn khung ghép: có người/vật lạ không, vật chính còn nhận ra không; lỗi thì sinh nền khác |

### 7.2 Gọi LTX-2.5

| Việc | Chi tiết | Thử nghiệm |
|---|---|---|
| Prompt mới | Một đoạn, dưới 200 từ, mở đầu bằng hành động, chỉ tả chuyển động, "The camera remains static throughout"; bỏ mọi câu cấm và câu thêm đạo cụ | E1 |
| Neo khung cuối | Khung cuối do hệ thống ghép, dạng `guide`, độ mạnh 0,7 và 0,9 | E2 |
| Nén ảnh đầu vào | CRF 0 / 18 / 33, chọn theo độ rõ nét bút sáp | E3 |
| Độ phân giải tầng 1 | So tầng 1 640×384 (hiện tại) với mức cao hơn nếu nét mảnh bị nhòe | E5 |
| `DFRPipeline` | So chất lượng và thời gian | E6 |
| Hạt ngẫu nhiên | Mỗi lần sinh lại dùng hạt mới, vẫn lưu để truy vết | code |

### 7.3 Kiểm tra video sinh ra (thay `VIDEO_VISION_CHECKS_PENDING`)

Lấy khung đầu, giữa, cuối và 2 khung ngẫu nhiên mỗi cảnh; Qwen so với khung đầu:
(a) có người/con vật/đồ vật mới; (b) vật chính biến dạng, đổi màu hoặc mất; (c) đổi phong cách; (d) chữ, logo, khung lồng.
Kèm kiểm tra bằng code (chênh lệch ảnh bất thường, khung đen).
Lỗi → sinh lại với hạt mới, tối đa 2 lần mỗi cảnh (FR-AI-06). Hết lượt → báo lỗi an toàn (theo SRS), kịch bản giữ lại để
phụ huynh thử lại. Đo tỷ lệ bắt đúng và bắt nhầm trên bộ đánh giá trước khi cho chặn thật.

## 8. Âm thanh, phụ đề, nhãn

1. Giọng đọc tiếng Việt hiện có; thêm quãng nghỉ ngắn trước tên bộ phận; chuẩn hóa âm lượng.
2. **Đề xuất, cần bạn duyệt:** nhãn chữ tên bộ phận và mũi tên, ghép bằng ffmpeg lên video (không phải LTX vẽ, nên chữ
   không méo). Vị trí lấy từ ô bộ phận do bước nhận diện trả về; chỉ hiện khi vật gần như đứng yên ở đầu cảnh.
3. Phụ đề giữ quy tắc đọc được cho trẻ (đã sửa trong FEAT-093).

## 9. Tốc độ

### 9.1 Số đo hiện tại (Run 1, video 30 s, 5 cảnh)

| Đoạn | Thời gian |
|---|---|
| Lập kịch bản video | 31 s (sẽ bỏ vì gộp vào kịch bản học) |
| Chuẩn bị cảnh (FLUX + SAM) | khởi động khoảng 40 s, mỗi cảnh khoảng 12 s, chạy song song với render |
| Chờ cấp máy L40S cho LTX | khoảng 3,5 phút |
| Làm ấm LTX | 50 s |
| Mỗi cảnh 6 s | khoảng 115 s, trong đó suy luận 96–110 s; kiểm checkpoint 8 s (đã bỏ, chưa đo lại) |
| Ghép và kiểm | vài giây |
| **Tổng** | **14 phút** |

Video mới dài hơn (5–7 cảnh × 10 s) và render **lần lượt trên một L40S** (Q7). Quy theo số khung hình, một cảnh 10 s mất
khoảng 3 phút, tức **15–21 phút** phần render nếu không tối ưu. Đây là ước tính, S0 sẽ đo.

### 9.2 Hạng mục, theo thứ tự làm

| # | Việc | Tác dụng mong đợi | Giá | Chắc chắn |
|---|---|---|---|---|
| S0 | Đo tách từng đoạn trong một cảnh (nạp, mã hóa prompt, tầng 1, tầng 2, giải mã, chuyển CPU↔GPU) | biết đúng chỗ chậm | ~10 phút GPU | cao |
| S1 | `OffloadMode.NONE` thay `CPU` | bỏ chuyển trọng số mỗi cảnh | có thể thiếu VRAM; mã nguồn ghi khoảng 28 GB cho LTX-2, 2.5 chưa rõ | chưa đo |
| S2 | Mã hóa prompt của mọi cảnh một lần rồi giải phóng Gemma | giải quyết thiếu VRAM cho S1 | sửa cách gọi pipeline | chưa đo |
| S3 | `torch.compile` | tài liệu bên thứ ba nói nhanh hơn 15–25% | khởi động thêm 1–2 phút; cần giữ container | chưa đo |
| S4 | Backend attention (FlashAttention/Sage nếu pipeline hỗ trợ) | nhanh hơn | thêm gói, kiểm tương thích | chưa kiểm |
| S5 | ~~Render song song trên nhiều container~~ | **không làm** (Q7) | — | — |
| S6 | Làm ấm LTX và nền khi phụ huynh mở màn **xác nhận kịch bản** | giấu 3–4 phút chờ cấp máy | trả tiền nếu phụ huynh bỏ | cao |
| S7 | Chuẩn bị khung ghép ngay khi kịch bản qua cổng, trước khi xác nhận | bớt chờ sau khi bấm tạo | bỏ phí khi viết lại | cao |
| S8 | Ít khung hơn: render 16 fps rồi nội suy lên 24, hoặc bộ nâng thời gian của LTX | giảm thời gian theo số khung | rủi ro chuyển động xấu | chỉ thử |
| S9 | Một GPU lớn hơn (ví dụ H100) thay L40S cho cảnh | nhanh hơn nhiều khi không phải offload | đơn giá cao hơn; **chỉ đổi nếu bạn đồng ý sau khi có số đo** | chưa đo |
| S10 | Kiểm video bằng Qwen chạy song song với render cảnh sau | kiểm tra không cộng dồn thời gian | — | cao |

`fp8-cast` đang dùng; `fp8-scaled-mm` không dành cho L40S theo tài liệu; không có cờ tắt âm thanh. vLLM, MTP, KV cache
không áp dụng cho model video. Với phần chữ, vLLM đã đưa truyện xuống khoảng 10–25 s.

### 9.3 Mục tiêu và chi phí

| Mốc | Chờ từ lúc bấm tạo đến có video 50–70 s (máy đã ấm) |
|---|---|
| Chấp nhận được | ≤ 15 phút |
| Mục tiêu | ≤ 10 phút |
| Mong muốn | ≤ 8 phút |

Với một máy L40S, đạt mục tiêu cần S1–S4 (và có thể S8) giúp mỗi cảnh nhanh hơn khoảng **35–50%**. Chưa có số đo nào
chứng minh mức đó; nếu sau giai đoạn 2 không đạt, tôi báo số thật và đưa lựa chọn: giảm độ dài, giảm khung hình (S8)
hoặc GPU lớn hơn (S9).

Chi phí: khoảng 15–21 phút L40S cho mỗi video khi chưa tối ưu, chưa kể sinh lại. Đo bằng `modal billing report` ở S0.

### 9.4 Số máy L40S

Hôm nay luồng video có thể bật **tới 3 L40S cùng lúc**, mỗi máy một việc: Qwen, chuẩn bị cảnh (FLUX và SAM), LTX. Đây
là sai lệch so với kế hoạch hai container của FEAT-093 và chưa được bạn chấp nhận.

| Phương án | Số L40S tối đa | Thời gian | Công việc |
|---|---|---|---|
| A (đề xuất) | **2**: Qwen, và một máy làm lần lượt chuẩn bị toàn bộ khung rồi LTX | thêm khoảng 2–3 phút (ước tính: chuẩn bị không còn chạy gối với render, đổi model) | gộp image chuẩn bị cảnh vào app video |
| B | 3 như hiện nay, chỉ bỏ ý tưởng render song song | không đổi | không |

Cả hai phương án đều không thêm máy để render song song.

## 10. Thay đổi hệ thống

| Phần | Thay đổi |
|---|---|
| Hợp đồng | `story-revision.v2` (cảnh có `fact_id`, `narration`, `action_en`, `setting_en`); giữ đọc được v1 |
| CSDL | Lưu thẻ kiến thức đã dùng (id, phiên bản, hash, trạng thái), trường cảnh mới; migration chỉ thêm |
| Worker Qwen | Prompt và schema kịch bản học; AI soạn thẻ; kiểm đối chiếu; kiểm hình; bỏ `video.timeline.generate` khỏi luồng Parent |
| Pipeline video | Nhận kịch bản đã xác nhận; khung đầu/cuối; kiểm cảnh; hạt mới khi sinh lại; thứ tự chạy theo 9.4 |
| App | Màn kịch bản hiện "Con sẽ học được" và nguồn/nhãn chưa kiểm chứng; thời gian chờ ước tính cập nhật |
| ADR | Mới: dùng thẻ sở thích; kho kiến thức; cấu hình LTX và số máy GPU |

## 11. Đánh giá và tiêu chí chấp nhận

**Bộ đánh giá:** 30 tranh tổng hợp (bút sáp, nét hở, vật chồng nhau, vật bay, vật lạ), 3 nhóm tuổi; gộp với bộ đánh giá
nhận diện còn thiếu của FEAT-093.

| # | Tiêu chí | Ngưỡng |
|---|---|---|
| A1 | Lời đọc trong video trùng văn bản đã xác nhận | 100% |
| A2 | Sự thật đã chọn xuất hiện đủ, đúng cảnh | 100% trên bộ đánh giá |
| A3 | Câu kiến thức sai (người chấm), nguồn thẻ đã duyệt | 0 |
| A4 | Như trên, nguồn AI soạn | đo và báo cáo; ngưỡng chốt sau khi đo |
| A5 | Video có người/vật không có trong tranh | 0 sau khâu kiểm, trên bộ đánh giá |
| A6 | Vật chính nhận ra được ở mọi cảnh (người chấm) | ≥ 90% cảnh |
| A7 | Video 1280×720, không dải viền | 100% |
| A8 | Ra được video không lỗi | ≥ 27/30 |
| A9 | Thời gian chờ trung vị, máy ấm | ≤ 15 phút; mục tiêu ≤ 10 |
| A10 | Dữ liệu gửi model chỉ gồm trường cho phép | test tự động |

Phiếu chấm người: đúng kiến thức, dễ hiểu theo tuổi, truyện mạch lạc, giữ nét tranh, chuyển động có ý nghĩa.

## 12. Lộ trình

Mỗi giai đoạn: viết test trước, test offline xong mới tốn GPU, lưu bằng chứng trong `evidence/`.

| GĐ | Nội dung | Xong khi | GPU (ước tính) |
|---|---|---|---|
| 0 | Dọn nợ: lỗi hoạt động `EXPLORATION_NOT_EXPLICIT` (lọc từng gợi ý thay vì loại cả danh sách), 720p, lịch sử trống khi mở lần đầu, nút "Xác nhận chủ thể" bị cắt chữ; chạy một video xác nhận bản sửa đất/người lạ; commit | một lượt app end-to-end ra video | ~30 phút |
| 1 | Thử nghiệm LTX E1–E3 và đo S0 | bảng so sánh và video để bạn xem, chọn cấu hình | ~60 phút |
| 2 | Tốc độ S1–S4, S6, S7 (và S8 nếu cần); số máy theo 9.4 | số đo trước/sau; đạt ≤ 15 phút, hướng tới ≤ 10 | ~120 phút |
| 3 | Kho kiến thức: cấu trúc, 40 thẻ, công cụ duyệt, AI soạn | thẻ được duyệt, test chọn thẻ | nhỏ |
| 4 | Kịch bản học v2, hồ sơ trẻ, cổng kiểm, app xác nhận | A1, A2, A10 đạt offline và trên 10 tranh | ~40 phút |
| 5 | Chất lượng hình: khung cuối, mask, nền, kiểm video, sinh lại | A5–A7 trên 10 tranh | ~120 phút |
| 6 | Đánh giá 30 tranh, chỉnh ngưỡng, cập nhật SRS/ADR/STATUS | bảng A1–A10, bạn nghiệm thu | ~8–10 giờ nếu render đủ 30 video; có thể giảm còn 15 |

GPU ước tính tổng khoảng 14–18 giờ L40S, phần lớn ở giai đoạn 6. Sẽ dừng hỏi lại nếu vượt 20%.

Thứ tự đề xuất: 0 → 1 → 2 → 3/4 → 5 → 6. Giai đoạn 3 (soạn và duyệt thẻ) chạy song song được vì không cần GPU.

## 13. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| LTX vẫn méo nét hoặc thêm vật dù đã sửa | khung cuối, kiểm video, sinh lại; nếu tỷ lệ vẫn cao, báo lại để bạn xét hướng khác |
| Chuyển động không minh họa đúng bộ phận đang nói | hành động đơn giản theo gợi ý trong thẻ; khung gần bộ phận; nhãn chữ |
| Neo khung cuối làm cảnh đứng yên | thử nhiều độ mạnh (E2) |
| Thiếu VRAM khi bỏ offload | S2, hoặc giữ offload một phần, hoặc GPU lớn hơn |
| AI soạn kiến thức sai | nhãn, kiểm đối chiếu, phụ huynh xác nhận, ưu tiên kho |
| Duyệt thẻ chậm | đợt 1 chỉ 40 thẻ |
| Video dài hơn, render lần lượt nên chờ lâu | S1–S4, S6, S7; báo số đo và đề nghị giảm độ dài nếu không đạt |
| Câu dài hơn khó theo với trẻ nhỏ | tách 1–2 câu ngắn, người lớn chấm độ dễ hiểu trên bộ đánh giá |
| Hết lượt sinh lại làm hỏng cả video | đo tỷ lệ; xem quyết định D2 |

## 14. Cần bạn quyết khi duyệt

Đã chốt từ Rev 1: render song song (không, Q7); nhãn bộ phận (D1); cảnh lỗi (D2); người duyệt thẻ (D3); ưu tiên chủ thể
chính (Q8). Bảng tuổi, mục tiêu thời gian và ngân sách GPU đã đổi theo góp ý, được duyệt cùng plan.

Còn một câu: **số máy L40S theo 9.4, phương án A (tối đa 2, đề xuất) hay B (giữ 3 như hiện nay)?**

## 15. Tài liệu tham khảo

- [Mã và tài liệu LTX-2](https://github.com/Lightricks/LTX-2); chi tiết nguồn trong hai file `research/`.
- [Tổng quan thiết kế đa phương tiện (Noetel và cộng sự)](https://journals.sagepub.com/stoken/default+domain/PU8EQQCTDRBZ2SADDIRW/full): thấy qua tóm tắt tìm kiếm, không riêng trẻ nhỏ.
- [Tổng quan thiết kế video giảng dạy (AJET)](https://ajet.org.au/index.php/AJET/article/download/7296/1915/27086): thấy qua tóm tắt tìm kiếm.

# FEAT-018 activity pilot matrix

This matrix makes the pilot complete across the reviewed golden set. It does not promote production eligibility. Every row requires explicit adult context, Gate A confirmation, and Gate B approval of both activity and objective versions.

## Pilot rules

- `golden` rows are the full 20-activity device/integration pilot.
- Each golden row needs valid, ambiguous, blocked, cache-hit, cache-miss, and renderer-fallback cases.
- A real image is only a source observation. It cannot infer age, readiness, materials, supervision, or psychological traits.
- The current hardcoded `ACT-0004`/`OBJ_MOVEMENT_COORDINATION` fixture must be corrected before this matrix is wired.

## Golden 20 — full pilot

| ID | Version | Activity | Age | Area | Primary objective | Secondary objective | Pilot observation/input | Gate B expectation |
|---|---:|---|---|---|---|---|---|---|
| ACT-0004 | 2 | Tìm đồ vật dưới khăn | 0-3 | sensorial | OBJ_OBJECT_PERMANENCE | OBJ_RECEPTIVE_LANGUAGE | partly covered familiar object / cloth | approve exact activity/objective versions |
| ACT-0016 | 2 | Chuyển đồ vật lớn giữa hai bát | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | OBJ_MOVEMENT_COORDINATION | large objects and two bowls | approve exact activity/objective versions |
| ACT-0019 | 2 | Chuỗi rửa tay | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | OBJ_PRACTICAL_LIFE_SEQUENCE | handwashing materials / sink | approve exact activity/objective versions |
| ACT-0020 | 2 | Lau vết nước nhỏ | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | OBJ_ORDER_GRACE_COURTESY | small water spill and cloth | approve exact activity/objective versions |
| ACT-0023 | 2 | Tưới cây nhỏ | 0-3 | practical_life | OBJ_ORDER_GRACE_COURTESY | OBJ_INDEPENDENCE_SELF_CARE | small plant and watering can | approve exact activity/objective versions |
| ACT-0026 | 2 | Rót hạt khô | 3-6 | practical_life | OBJ_PRACTICAL_LIFE_SEQUENCE | OBJ_INDEPENDENCE_SELF_CARE | dry grains and pouring vessels | approve exact activity/objective versions |
| ACT-0030 | 2 | Khung cài nút | 3-6 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | OBJ_MOVEMENT_COORDINATION | button frame | approve exact activity/objective versions |
| ACT-0033 | 2 | Sắp bàn cho một người | 3-6 | practical_life | OBJ_ORDER_GRACE_COURTESY | OBJ_PRACTICAL_LIFE_SEQUENCE | table setting objects | approve exact activity/objective versions |
| ACT-0039 | 2 | Phân cấp bảng màu | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | OBJ_ORDER_GRACE_COURTESY | graded color boards | approve exact activity/objective versions |
| ACT-0046 | 2 | Khung kim loại luyện nét | 3-6 | language | OBJ_EARLY_WRITING | OBJ_SENSORIAL_DISCRIMINATION | metal insets / tracing frame | approve exact activity/objective versions |
| ACT-0055 | 2 | Quan sát các bộ phận của cây | 6-9 | science | OBJ_SCIENTIFIC_OBSERVATION | OBJ_COSMIC_INTERCONNECTION | plant parts | approve exact activity/objective versions |
| ACT-0058 | 2 | Mô hình vòng tuần hoàn nước | 6-9 | science | OBJ_SCIENTIFIC_OBSERVATION | OBJ_COSMIC_INTERCONNECTION | water cycle model | approve exact activity/objective versions |
| ACT-0061 | 2 | Nhân với trò chơi tem | 6-9 | mathematics | OBJ_MATHEMATICAL_REASONING | OBJ_NUMBER_QUANTITY_PLACE_VALUE | stamp game / multiplication material | approve exact activity/objective versions |
| ACT-0067 | 2 | Phân tích từ loại bằng ký hiệu | 6-9 | language | OBJ_LANGUAGE_ANALYSIS | OBJ_COMMUNICATION_ARGUMENTATION | word-class symbols and text | approve exact activity/objective versions |
| ACT-0074 | 2 | Lập kế hoạch công việc tuần | 6-9 | practical_life | OBJ_SOCIAL_RESPONSIBILITY | OBJ_PROJECT_SERVICE_LEADERSHIP | weekly planning materials | approve exact activity/objective versions |
| ACT-0085 | 2 | Khảo sát và mô tả dữ liệu | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | OBJ_COMMUNICATION_ARGUMENTATION | data table or chart | approve exact activity/objective versions |
| ACT-0087 | 2 | Xây khóa phân loại | 9-12 | science | OBJ_SCIENTIFIC_INQUIRY | OBJ_HUMANITIES_RESEARCH | classification key materials | approve exact activity/objective versions |
| ACT-0091 | 2 | Mô hình pha Mặt Trăng | 9-12 | science | OBJ_COSMIC_INTERCONNECTION | OBJ_SCIENTIFIC_INQUIRY | moon phase model | approve exact activity/objective versions |
| ACT-0097 | 2 | Viết lập luận dựa trên bằng chứng | 9-12 | language | OBJ_COMMUNICATION_ARGUMENTATION | OBJ_HUMANITIES_RESEARCH | source packet and argument organizer | approve exact activity/objective versions |
| ACT-0099 | 2 | Dự án nghiên cứu độc lập | 9-12 | language | OBJ_PROJECT_SERVICE_LEADERSHIP | OBJ_COMMUNICATION_ARGUMENTATION, OBJ_HUMANITIES_RESEARCH | project planner and source log | approve exact activity/objective versions |

## MVP 100 — catalog coverage

These rows are catalog coverage, not all device E2E. Person 1 must validate every row and every objective reference. The 20 golden rows above are the initial full-flow pilot set; the remaining MVP rows need schema, rule, provenance, and no-eligible coverage before promotion.

| ID | Version | Activity | Age | Area | Objective IDs | Catalog status |
|---|---:|---|---|---|---|---|
| ACT-0001 | 1 | Theo dõi vật chuyển động chậm | 0-3 | movement | OBJ_MOVEMENT_COORDINATION | ACTIVE_FIXTURE |
| ACT-0002 | 1 | Cầm và chuyển vòng lớn | 0-3 | movement | OBJ_MOVEMENT_COORDINATION | ACTIVE_FIXTURE |
| ACT-0003 | 1 | Đá bóng mềm có dây neo | 0-3 | movement | OBJ_MOVEMENT_COORDINATION | ACTIVE_FIXTURE |
| ACT-0004 | 1 | Tìm đồ vật dưới khăn | 0-3 | sensorial | OBJ_OBJECT_PERMANENCE | ACTIVE_FIXTURE |
| ACT-0005 | 1 | Hộp thả bóng có khay | 0-3 | sensorial | OBJ_OBJECT_PERMANENCE | ACTIVE_FIXTURE |
| ACT-0006 | 1 | Khám phá giỏ đồ vật an toàn | 0-3 | sensorial | OBJ_OBJECT_PERMANENCE | ACTIVE_FIXTURE |
| ACT-0007 | 1 | Ghép cặp chất liệu | 0-3 | sensorial | OBJ_OBJECT_PERMANENCE | ACTIVE_FIXTURE |
| ACT-0008 | 1 | Ghép cặp hộp âm thanh kín | 0-3 | sensorial | OBJ_RECEPTIVE_LANGUAGE | ACTIVE_FIXTURE |
| ACT-0009 | 1 | Gọi tên người trong ảnh gia đình | 0-3 | language | OBJ_RECEPTIVE_LANGUAGE | ACTIVE_FIXTURE |
| ACT-0010 | 1 | Gọi tên bộ phận cơ thể | 0-3 | language | OBJ_RECEPTIVE_LANGUAGE | ACTIVE_FIXTURE |
| ACT-0011 | 1 | Gọi tên mô hình động vật lớn | 0-3 | language | OBJ_RECEPTIVE_LANGUAGE | ACTIVE_FIXTURE |
| ACT-0012 | 1 | Ghép đồ vật với hình ảnh | 0-3 | language | OBJ_RECEPTIVE_LANGUAGE | ACTIVE_FIXTURE |
| ACT-0013 | 1 | Thả đĩa lớn qua khe | 0-3 | movement | OBJ_MOVEMENT_COORDINATION | ACTIVE_FIXTURE |
| ACT-0014 | 1 | Xếp cốc lồng nhau | 0-3 | sensorial | OBJ_MOVEMENT_COORDINATION | ACTIVE_FIXTURE |
| ACT-0015 | 1 | Xếp vòng lớn | 0-3 | movement | OBJ_MOVEMENT_COORDINATION | ACTIVE_FIXTURE |
| ACT-0016 | 1 | Chuyển đồ vật lớn giữa hai bát | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0017 | 1 | Dùng thìa chuyển vật lớn | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0018 | 1 | Rót lượng nước nhỏ | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0019 | 1 | Chuỗi rửa tay | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0020 | 1 | Lau vết nước nhỏ | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0021 | 1 | Tập mang tất | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0022 | 1 | Cắt chuối bằng dụng cụ an toàn | 0-3 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0023 | 1 | Tưới cây nhỏ | 0-3 | practical_life | OBJ_ORDER_GRACE_COURTESY | ACTIVE_FIXTURE |
| ACT-0024 | 1 | Mang khay thấp bằng hai tay | 0-3 | practical_life | OBJ_ORDER_GRACE_COURTESY | ACTIVE_FIXTURE |
| ACT-0025 | 1 | Chào hỏi và chờ lượt | 0-3 | practical_life | OBJ_ORDER_GRACE_COURTESY | ACTIVE_FIXTURE |
| ACT-0026 | 1 | Rót hạt khô | 3-6 | practical_life | OBJ_PRACTICAL_LIFE_SEQUENCE | ACTIVE_FIXTURE |
| ACT-0027 | 1 | Rót nước có vạch giới hạn | 3-6 | practical_life | OBJ_PRACTICAL_LIFE_SEQUENCE | ACTIVE_FIXTURE |
| ACT-0028 | 1 | Chuyển hạt bằng thìa | 3-6 | practical_life | OBJ_PRACTICAL_LIFE_SEQUENCE | ACTIVE_FIXTURE |
| ACT-0029 | 1 | Chuyển vật bằng kẹp | 3-6 | practical_life | OBJ_PRACTICAL_LIFE_SEQUENCE | ACTIVE_FIXTURE |
| ACT-0030 | 1 | Khung cài nút | 3-6 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0031 | 1 | Khung kéo khóa | 3-6 | practical_life | OBJ_INDEPENDENCE_SELF_CARE | ACTIVE_FIXTURE |
| ACT-0032 | 1 | Rửa tay theo chuỗi đầy đủ | 3-6 | practical_life | OBJ_PRACTICAL_LIFE_SEQUENCE | ACTIVE_FIXTURE |
| ACT-0033 | 1 | Sắp bàn cho một người | 3-6 | practical_life | OBJ_ORDER_GRACE_COURTESY | ACTIVE_FIXTURE |
| ACT-0034 | 1 | Cắm hoa đơn giản | 3-6 | practical_life | OBJ_ORDER_GRACE_COURTESY | ACTIVE_FIXTURE |
| ACT-0035 | 1 | Quét khu vực có đánh dấu | 3-6 | practical_life | OBJ_ORDER_GRACE_COURTESY | ACTIVE_FIXTURE |
| ACT-0036 | 1 | Tháp hồng | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | ACTIVE_FIXTURE |
| ACT-0037 | 1 | Cầu thang nâu | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | ACTIVE_FIXTURE |
| ACT-0038 | 1 | Gậy đỏ | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | ACTIVE_FIXTURE |
| ACT-0039 | 1 | Phân cấp bảng màu | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | ACTIVE_FIXTURE |
| ACT-0040 | 1 | Ghép ống âm thanh | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | ACTIVE_FIXTURE |
| ACT-0041 | 1 | Bảng nhám và mịn | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | ACTIVE_FIXTURE |
| ACT-0042 | 1 | Khối hình học | 3-6 | sensorial | OBJ_SENSORIAL_DISCRIMINATION | ACTIVE_FIXTURE |
| ACT-0043 | 1 | Chữ cái nhám | 3-6 | language | OBJ_EARLY_WRITING | ACTIVE_FIXTURE |
| ACT-0044 | 1 | Bảng chữ cái rời | 3-6 | language | OBJ_EARLY_WRITING | ACTIVE_FIXTURE |
| ACT-0045 | 1 | Hộp đồ vật đọc âm vị | 3-6 | language | OBJ_EARLY_READING | ACTIVE_FIXTURE |
| ACT-0046 | 1 | Khung kim loại luyện nét | 3-6 | language | OBJ_EARLY_WRITING | ACTIVE_FIXTURE |
| ACT-0047 | 1 | Gậy số | 3-6 | mathematics | OBJ_NUMBER_QUANTITY_PLACE_VALUE | ACTIVE_FIXTURE |
| ACT-0048 | 1 | Chữ số nhám | 3-6 | mathematics | OBJ_NUMBER_QUANTITY_PLACE_VALUE | ACTIVE_FIXTURE |
| ACT-0049 | 1 | Hộp que tính | 3-6 | mathematics | OBJ_NUMBER_QUANTITY_PLACE_VALUE | ACTIVE_FIXTURE |
| ACT-0050 | 1 | Hệ thập phân hạt vàng | 3-6 | mathematics | OBJ_NUMBER_QUANTITY_PLACE_VALUE | ACTIVE_FIXTURE |
| ACT-0051 | 1 | Câu chuyện về vũ trụ | 6-9 | cosmic_education | OBJ_COSMIC_INTERCONNECTION | ACTIVE_FIXTURE |
| ACT-0052 | 1 | Mô hình tỉ lệ Hệ Mặt Trời | 6-9 | cosmic_education | OBJ_COSMIC_INTERCONNECTION | ACTIVE_FIXTURE |
| ACT-0053 | 1 | Mô hình các lớp Trái Đất | 6-9 | science | OBJ_SCIENTIFIC_OBSERVATION | ACTIVE_FIXTURE |
| ACT-0054 | 1 | Địa hình đất và nước | 6-9 | cultural_studies | OBJ_SCIENTIFIC_OBSERVATION | ACTIVE_FIXTURE |
| ACT-0055 | 1 | Quan sát các bộ phận của cây | 6-9 | science | OBJ_SCIENTIFIC_OBSERVATION | ACTIVE_FIXTURE |
| ACT-0056 | 1 | Phân loại động vật | 6-9 | science | OBJ_SCIENTIFIC_OBSERVATION | ACTIVE_FIXTURE |
| ACT-0057 | 1 | Xây lưới thức ăn | 6-9 | science | OBJ_COSMIC_INTERCONNECTION | ACTIVE_FIXTURE |
| ACT-0058 | 1 | Mô hình vòng tuần hoàn nước | 6-9 | science | OBJ_SCIENTIFIC_OBSERVATION | ACTIVE_FIXTURE |
| ACT-0059 | 1 | So sánh ba trạng thái vật chất | 6-9 | science | OBJ_SCIENTIFIC_OBSERVATION | ACTIVE_FIXTURE |
| ACT-0060 | 1 | Khám phá máy cơ đơn giản | 6-9 | science | OBJ_MATHEMATICAL_REASONING | ACTIVE_FIXTURE |
| ACT-0061 | 1 | Nhân với trò chơi tem | 6-9 | mathematics | OBJ_MATHEMATICAL_REASONING | ACTIVE_FIXTURE |
| ACT-0062 | 1 | Chia dài bằng vật liệu | 6-9 | mathematics | OBJ_MATHEMATICAL_REASONING | ACTIVE_FIXTURE |
| ACT-0063 | 1 | Phân số tương đương | 6-9 | mathematics | OBJ_MATHEMATICAL_REASONING | ACTIVE_FIXTURE |
| ACT-0064 | 1 | Bảng số thập phân | 6-9 | mathematics | OBJ_MATHEMATICAL_REASONING | ACTIVE_FIXTURE |
| ACT-0065 | 1 | Đo và phân loại góc | 6-9 | mathematics | OBJ_MATHEMATICAL_REASONING | ACTIVE_FIXTURE |
| ACT-0066 | 1 | Khám phá diện tích tương đương | 6-9 | mathematics | OBJ_MATHEMATICAL_REASONING | ACTIVE_FIXTURE |
| ACT-0067 | 1 | Phân tích từ loại bằng ký hiệu | 6-9 | language | OBJ_LANGUAGE_ANALYSIS | ACTIVE_FIXTURE |
| ACT-0068 | 1 | Phân tích thành phần câu | 6-9 | language | OBJ_LANGUAGE_ANALYSIS | ACTIVE_FIXTURE |
| ACT-0069 | 1 | Khảo sát tiền tố và hậu tố | 6-9 | language | OBJ_LANGUAGE_ANALYSIS | ACTIVE_FIXTURE |
| ACT-0070 | 1 | Báo cáo nghiên cứu ngắn | 6-9 | language | OBJ_LANGUAGE_ANALYSIS | ACTIVE_FIXTURE |
| ACT-0071 | 1 | Dòng thời gian sự sống | 6-9 | cosmic_education | OBJ_COSMIC_INTERCONNECTION | ACTIVE_FIXTURE |
| ACT-0072 | 1 | Bản đồ châu lục và quốc gia | 6-9 | cultural_studies | OBJ_HUMANITIES_RESEARCH | ACTIVE_FIXTURE |
| ACT-0073 | 1 | Chuẩn bị phỏng vấn người làm việc cộng đồng | 6-9 | social_studies | OBJ_SOCIAL_RESPONSIBILITY | ACTIVE_FIXTURE |
| ACT-0074 | 1 | Lập kế hoạch công việc tuần | 6-9 | practical_life | OBJ_SOCIAL_RESPONSIBILITY | ACTIVE_FIXTURE |
| ACT-0075 | 1 | Vòng tròn hòa bình giải quyết xung đột | 6-9 | social_studies | OBJ_SOCIAL_RESPONSIBILITY | ACTIVE_FIXTURE |
| ACT-0076 | 1 | Lũy thừa và mẫu hình | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0077 | 1 | Căn bậc hai và căn bậc ba | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0078 | 1 | Cân bằng phương trình | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0079 | 1 | Tỉ lệ qua công thức | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0080 | 1 | Phần trăm trong ngân sách | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0081 | 1 | Chuyển đổi phân số, thập phân, phần trăm | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0082 | 1 | Dựng hình bằng compa và thước | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0083 | 1 | Khám phá định lý Pythagore | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0084 | 1 | Đo và tính thể tích | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0085 | 1 | Khảo sát và mô tả dữ liệu | 9-12 | mathematics | OBJ_ADVANCED_MATHEMATICS | ACTIVE_FIXTURE |
| ACT-0086 | 1 | Quan sát tế bào bằng kính hiển vi | 9-12 | science | OBJ_SCIENTIFIC_INQUIRY | ACTIVE_FIXTURE |
| ACT-0087 | 1 | Xây khóa phân loại | 9-12 | science | OBJ_SCIENTIFIC_INQUIRY | ACTIVE_FIXTURE |
| ACT-0088 | 1 | Khảo sát hệ sinh thái tại chỗ | 9-12 | science | OBJ_SCIENTIFIC_INQUIRY | ACTIVE_FIXTURE |
| ACT-0089 | 1 | Tách hỗn hợp an toàn | 9-12 | science | OBJ_SCIENTIFIC_INQUIRY | ACTIVE_FIXTURE |
| ACT-0090 | 1 | Theo dõi truyền năng lượng | 9-12 | science | OBJ_SCIENTIFIC_INQUIRY | ACTIVE_FIXTURE |
| ACT-0091 | 1 | Mô hình pha Mặt Trăng | 9-12 | science | OBJ_COSMIC_INTERCONNECTION | ACTIVE_FIXTURE |
| ACT-0092 | 1 | Dòng thời gian địa chất | 9-12 | cosmic_education | OBJ_HUMANITIES_RESEARCH | ACTIVE_FIXTURE |
| ACT-0093 | 1 | Nghiên cứu nền văn minh cổ | 9-12 | cultural_studies | OBJ_HUMANITIES_RESEARCH | ACTIVE_FIXTURE |
| ACT-0094 | 1 | Lập bản đồ di cư và thương mại | 9-12 | cultural_studies | OBJ_HUMANITIES_RESEARCH | ACTIVE_FIXTURE |
| ACT-0095 | 1 | Mô phỏng quyết định cộng đồng | 9-12 | social_studies | OBJ_HUMANITIES_RESEARCH | ACTIVE_FIXTURE |
| ACT-0096 | 1 | Mô phỏng doanh nghiệp lớp học | 9-12 | social_studies | OBJ_PROJECT_SERVICE_LEADERSHIP | ACTIVE_FIXTURE |
| ACT-0097 | 1 | Viết lập luận dựa trên bằng chứng | 9-12 | language | OBJ_COMMUNICATION_ARGUMENTATION | ACTIVE_FIXTURE |
| ACT-0098 | 1 | So sánh hai tác phẩm | 9-12 | language | OBJ_COMMUNICATION_ARGUMENTATION | ACTIVE_FIXTURE |
| ACT-0099 | 1 | Dự án nghiên cứu độc lập | 9-12 | language | OBJ_PROJECT_SERVICE_LEADERSHIP | ACTIVE_FIXTURE |
| ACT-0100 | 1 | Lập kế hoạch dự án phục vụ cộng đồng | 9-12 | social_studies | OBJ_PROJECT_SERVICE_LEADERSHIP | ACTIVE_FIXTURE |

## Required evidence per golden row

- source image hash and dimensions only;
- validation decision/reason;
- VLM/ASR contract status and provenance;
- candidate mapping and adult Gate A decision;
- P1 eligibility inputs and result;
- Gate B activity/objective IDs and versions;
- cache hit/miss and fallback reason;
- renderer lifecycle summary and screenshot;
- handoff and feedback completion;
- no raw image, prompt, output, token, signed URL, or personal data.

## Pilot completion rule

The pilot is complete only when all 20 golden rows have one successful full flow and one safe failure/fallback flow. The 100 MVP rows are catalog-validation coverage until the team explicitly expands device E2E.

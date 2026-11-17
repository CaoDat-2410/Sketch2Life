# B2A application report — 2026-10-31

## Giới hạn

Tài liệu ghi nhận việc áp dụng B2A đã được owner duyệt. Không có code, schema vật lý, migration, backend, DB, MinIO, Modal/GPU, runtime hay test được chạy. Không commit, push hoặc stage. Không đưa dữ liệu trẻ thật vào đây.

## Approval và rev2

- Chỉ thị: `Duyệt B2A rev2 ED75E7B53B03E01B + B1`.
- Rev2 SHA-256: `ED75E7B53B03E01B10CC2391107D1D53173176820585CBE8544E7CBC0A2148A7` (giữ nguyên).
- 45 thao tác được duyệt và áp dụng: 10 loại A, 35 loại B, 0 loại C; M001–M044 thay đúng clause được pin, M045 append một entry mới D-114. D-99 và các entry DECISIONS cũ không bị sửa.
- bản ghi phân công đã được owner thu hồi sau khi rev2 được viết; dòng 77 của rev2 không còn đúng. File phân công đã bị xóa và mục Pha 1 đã được gỡ khỏi approval; không ghi tên người viết/review trong phần mới.

## Trạng thái thao tác M001–M045

Loại B được áp dụng theo đề xuất logic trong rev2. Marker còn lại nêu chi tiết physical storage/contract/prompt implementation cần thiết kế ở bước sau; chúng không đảo ngược quyết định ordering đã duyệt.

| Thao tác | Loại rev2 | Kết quả |
|---|---|---|
| M001 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M002 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M003 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M004 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M005 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M006 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M007 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M008 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M009 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M010 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M011 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M012 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M013 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M014 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M015 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M016 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M017 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M018 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M019 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M020 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M021 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M022 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M023 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M024 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M025 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M026 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M027 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M028 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M029 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M030 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M031 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M032 | A | Đã áp dụng đúng clause trong phạm vi rev2. |
| M033 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M034 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M035 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M036 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M037 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M038 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M039 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M040 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M041 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M042 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M043 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M044 | B | Đã áp dụng theo đề xuất rev2; chi tiết thiết kế/triển khai còn mở được giữ lại. |
| M045 | A | Đã áp dụng đúng clause trong phạm vi rev2. |

## Coverage 36/36 từ B2 inventory

| Phân loại gốc | Tổng | Đã áp dụng | Giữ lịch sử |
|---|---:|---:|---:|
| PRE_VIDEO | 9 | 9 | 0 |
| AMBIGUOUS | 27 | 26 | 1 |
| Tổng | 36 | 35 | 1 |

35 dòng inventory có thao tác M### đã được áp dụng; I208 (Rev36:61) được giữ nguyên với trạng thái `KEEP_HISTORY`, do là snapshot lịch sử ngoài phạm vi. Cột nguồn giữ tham chiếu baseline như trong B2 inventory; số dòng có thể đã dịch chuyển sau khi áp dụng. Các lý do theo từng dòng được ghi dưới đây.

| Inventory B2 | Nguồn B2 baseline | Phân loại | M### | Kết quả sau áp dụng | Lý do/trạng thái |
|---|---|---|---|---|---|
| I002 | SRS:81 | PRE_VIDEO | M001 | APPLIED | M001 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I019 | SRS:339 | PRE_VIDEO | M002 | APPLIED | M002 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I021 | SRS:360 | PRE_VIDEO | M003 | APPLIED | M003 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I027 | SRS:391 | PRE_VIDEO | M004 | APPLIED | M004 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I038 | SRS:592 | PRE_VIDEO | M005 | APPLIED | M005 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I042 | SRS:718 | AMBIGUOUS | M006 | APPLIED | M006 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I043 | SRS:746 | AMBIGUOUS | M007 | APPLIED | M007 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I047 | SRS:801 | AMBIGUOUS | M008 | APPLIED | M008 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I050 | SRS:932 | AMBIGUOUS | M009 | APPLIED | M009 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I054 | SRS:1044 | AMBIGUOUS | M010 | APPLIED | M010 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I056 | SRS:1072 | PRE_VIDEO | M011 | APPLIED | M011 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I060 | SRS:1206 | AMBIGUOUS | M012 | APPLIED | M012 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I061 | SRS:1208 | AMBIGUOUS | M013 | APPLIED | M013 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I062 | SRS:1210 | AMBIGUOUS | M014 | APPLIED | M014 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I066 | SRS:1268 | AMBIGUOUS | M015 | APPLIED | M015 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I069 | SRS:1280 | AMBIGUOUS | M016 | APPLIED | M016 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I070 | SRS:1319 | AMBIGUOUS | M017 | APPLIED | M017 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I071 | SRS:1321 | PRE_VIDEO | M018, M019 | APPLIED | M018, M019 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I072 | SRS:1323 | AMBIGUOUS | M020 | APPLIED | M020 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I089 | SRS:1522 | AMBIGUOUS | M021 | APPLIED | M021 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I093 | SRS:1571 | PRE_VIDEO | M022 | APPLIED | M022 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I094 | SRS:1615 | AMBIGUOUS | M023, M024 | APPLIED | M023, M024 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I101 | SRS:1837 | AMBIGUOUS | M025 | APPLIED | M025 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I112 | SRS:2247 | AMBIGUOUS | M026 | APPLIED | M026 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I127 | SRS:2386 | AMBIGUOUS | M027, M028 | APPLIED | M027, M028 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I162 | REG:166 | AMBIGUOUS | M033 | APPLIED | M033 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I167 | REG:200 | AMBIGUOUS | M034 | APPLIED | M034 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I173 | REG:260 | AMBIGUOUS | M035 | APPLIED | M035 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I181 | REG:369 | AMBIGUOUS | M036 | APPLIED | M036 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I182 | REG:375 | AMBIGUOUS | M037 | APPLIED | M037 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I188 | REG:474 | AMBIGUOUS | M038 | APPLIED | M038 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I192 | REG:531 | AMBIGUOUS | M040, M041 | APPLIED | M040, M041 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I208 | R36:61 | AMBIGUOUS | KEEP — R36:61 lịch sử | KEEP_HISTORY | Giữ nguyên snapshot Rev36 lịch sử ngoài phạm vi B2A; không đánh dấu đã hòa giải. |
| I209 | ADR21:13 | PRE_VIDEO | M042 | APPLIED | M042 đã áp dụng; Parent không còn activity-selection prerequisite trước story/video, còn gate Teacher sample theo rev2. |
| I211 | ADR21:34 | AMBIGUOUS | M043 | APPLIED | M043 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |
| I214 | ADR21:56 | AMBIGUOUS | M044 | APPLIED | M044 đã áp dụng theo wording role/order của rev2; chi tiết vật lý/contract còn mở được ghi trong marker tương ứng. |

## Trace chính sau cập nhật

- SRS BR-08 (:215) và FR-P-05 (:455): Parent xem activity list gắn lesson sau khi video sẵn sàng; không yêu cầu chọn activity trước khi tạo video.
- UC-02 (:1314 trở đi), BR-15 (:222): Parent không có pre-video activity-selection gate; Teacher sample vẫn ghim một activity đã duyệt; cổng cuối là xác nhận script/storyboard.
- AC-05 (:1041), AC-36 (:1072), AC-52 (:2589): Parent activities hiển thị sau video; Teacher sample pin một activity; pipeline và safety/playback không bị bỏ qua.
- BR-55 (:2434) xác nhận lesson activity list sau video. Q151 giữ thứ tự hoạt động; Q155 vẫn giữ quyết định tiếng Việt trước. D-99, Rev25/v2.2 và diagram/PDF lịch sử không bị sửa.

## Hash nguồn trước/sau

| File | SHA-256 trước (approval baseline) | SHA-256 sau áp dụng |
|---|---|---|
| SRS | `7EE8CD8511AF722E33DEA08AEE4A324532A8C4A397230D74DD5632387A1B4F8B` | `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC` |
| DATA_TABLE_REGISTER | `BE34CF5475550CF3DF0A8A174E66AEB06B664D9E62FD6AE38216374A5F3BCC0A` | `0415BBF7FC2477021543C79E72F7011E11A3CE09DBCB92291C5F187907873B8F` |
| ADR-0021 | `BB4310E9EE006D2E9DDBE0FBCE1ADA138AA1010DF32C2141F2A9BF3B77BD58CA` | `FE5671336F3F836767E5CE6BF3DC26C3DEF4D30B36445D8F29220BCEE6DC3657` |
| DECISIONS | `9E7822A3567EC569747498EDEB4A50F22E340D7F869F191700396DF5FB41FBA7` | `61D266FD6E0AFCA1AFD1ABAE73606C4C53F92A368ED4E0066F7CD89722CD3092` |

## Việc còn mở

- I208/Rev36:61 vẫn là historical snapshot, chưa được hòa giải.
- C2/C3/C7: logic đã được owner chấp nhận và ghi vào nguồn; task thiết kế tiếp theo cần xác định vị trí lưu vật lý của opaque lesson-version ref, biểu diễn contract theo role và mapping prompt/stale vào implementation. Rev2 không quyết định bảng/cột/FK/schema/migration.
- SRS vẫn cần sign-off theo quy trình sản phẩm; approval này chỉ duyệt amendment/document scope.
- Chưa triển khai API/backend hoặc xác nhận luồng end-to-end.

## Kiểm tra và giới hạn

- `python tools/validate_harness.py` — exit 0; HARNESS_VALID.
- `python tools/validate_repository_security.py` — exit 0; REPOSITORY_SECURITY_VALID, 5,948 publishable files scanned, absolute machine paths absent.
- `python tools/validate_architecture.py` — exit 0; ARCHITECTURE_VALID.
- `git diff --check` — exit 0, không có output lỗi. Lệnh này không bao gồm hai file report mới; UTF-8/whitespace của chúng được kiểm riêng.
- Không chạy test, backend, DB, MinIO, Modal/GPU hay runtime.

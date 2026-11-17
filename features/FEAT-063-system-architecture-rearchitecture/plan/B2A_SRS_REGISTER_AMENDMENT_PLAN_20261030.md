# B2A — SRS/register amendment plan theo quyết định A (2026-10-30)

- **Plan status: DRAFT. Task status: AWAITING_APPROVAL. Chưa áp dụng bất kỳ dòng sửa nguồn nào.**
- Căn cứ quyết định: `evidence/B2_OWNER_DECISION_A_20261030.md`, source `owner-b2-option-a-directive-20261030`; **chỉ Q1=A đã chốt**. Q2–Q8 đều là **GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận**.
- Lượt hiện tại được owner cho phép tạo plan và bản ghi quyết định; chưa có approval sửa SRS/register/ADR/DECISIONS, không tự ghi approval.
- Thời điểm ghi nhận máy: 2026-10-30T23:59:14+07:00; tên file theo ngày scope owner 2026-10-30. Thời điểm này không thay thời điểm owner gửi chỉ thị.

## 1. Mục tiêu và phạm vi

Hòa giải các đoạn còn bắt Parent chọn/ghim activity trước story/video với A: **Parent không chọn hoạt động trước video; list lesson hiện sau video xem được; Teacher sample ghim đúng một hoạt động đã duyệt trước video mẫu.**

Phạm vi amendment tương lai chỉ gồm SRS hiện tại, register hiện tại, ba clause trong ADR-0021 và một entry DECISIONS mới nếu được duyệt. Lượt này chỉ tạo hai file mới; mọi bảng dưới đây là đề xuất có thể review, không là patch đã áp dụng. Các nội dung Q2–Q8 chỉ được dùng làm giả định để trình owner, không tự biến thành requirement đã chốt. Không nhập optional hint pre-video của C vào A.

| Nguồn dự kiến sửa (giữ nguyên hiện tại) | SHA-256 baseline |
| --- | --- |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | 7EE8CD8511AF722E33DEA08AEE4A324532A8C4A397230D74DD5632387A1B4F8B |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md | BE34CF5475550CF3DF0A8A174E66AEB06B664D9E62FD6AE38216374A5F3BCC0A |
| docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md | BB4310E9EE006D2E9DDBE0FBCE1ADA138AA1010DF32C2141F2A9BF3B77BD58CA |
| features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md | 9E7822A3567EC569747498EDEB4A50F22E340D7F869F191700396DF5FB41FBA7 |

| File | Đoạn hiện có cần sửa | Thao tác clause / append | Cách đếm |
| --- | --- | --- | --- |
| SRS | 29 | 32 | Sửa clause ở 29 dòng hiện có. |
| DATA_TABLE_REGISTER | 8 | 9 | Sửa clause ở 8 dòng; không migration/code. |
| ADR-0021 | 3 | 3 | Chỉ clause Parent/role prerequisites, giữ phần khác. |
| DECISIONS | 0 | 1 | Thêm đúng một entry mới; D-99:104 chỉ là context, không sửa. |
| Tổng | 40 | 45 | 40 đoạn hiện có + 1 entry mới; nhiều clause trong cùng một dòng được đếm riêng thao tác. |

Tổng 45 đề xuất: **3 thao tác chỉ dựa Q1** (M002, M011, M018), **42 thao tác còn chờ Q2–Q8**. Nhiều thao tác sửa hai clause khác nhau trong cùng dòng, không phải 45 dòng source độc lập. DECISIONS là một append, không đếm D-99 như đoạn sẽ sửa.

## 2. Cổng trước khi áp dụng và nguồn giữ nguyên

1. Owner ghi approval mới pin SHA-256 của chính plan này, nêu file/phạm vi/M### được duyệt. Kiểm plan hash thực tế đúng; không dùng approval B2 cũ để áp dụng B2A.
2. **Approval plan không tự xác nhận Q2–Q8.** Mỗi thao tác mang CHỜ OWNER chỉ áp dụng khi owner trả lời các Q được liệt kê và phạm vi/văn bản cuối đã được review/approval tương ứng. Còn marker chưa chốt thì giữ BLOCKED cho thao tác đó; không báo nguồn đã hòa giải hoàn toàn.
3. Trước sửa, mở lại source, kiểm hash/source bytes và mỗi clause hiện tại khớp đúng một lần tại dòng nguồn. Nếu drift, dừng thao tác liên quan để rebase/review plan; không ghi đè concurrent edits.
4. Có thể phê duyệt riêng 3 thao tác Q1 nhưng đó chỉ là hòa giải một phần, không tự mở B1. Nếu yêu cầu một bộ tài liệu thống nhất hoàn chỉnh, phải chốt mọi Q chặn trước khi áp dụng bộ đầy đủ.

Giữ nguyên: lịch sử Rev25 và Q151; mọi approval cũ; Teacher pin/checklist; Q155 vẫn là tiếng Việt trước tại SRS:2632; exact preserved v2.2; ADR-0022 đã tương thích ordering A; B0/B1/B2 và plan cũ. SRS/register vẫn draft, không tự sign-off/khóa final stack. Diagram/PDF cũ là snapshot lịch sử, không render lại hoặc coi đã phản ánh amendment. Không thay count bảng, FK, cột vật lý, migration hoặc runtime.

Ba hash B2 ghim:

| Tài liệu được giữ nguyên | SHA-256 thực tế khớp S0 |
| --- | --- |
| features/FEAT-063-system-architecture-rearchitecture/plan/B2_PARENT_ACTIVITY_ORDER_PLAN_20261030.md | AAD0459FAA7FE7BF053198FEC41CA13CB713F3D5774AC83546B3793862E47A1F |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B2_PARENT_ACTIVITY_ORDER_CROSSWALK_20261030.md | A17246115412A2413BE646F9DB8F16E8BC21B12950F792851322E913E3308514 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B2_PARENT_ACTIVITY_ORDER_INVENTORY_20261030.csv | F88D11E3F3348B646D7D1C3399A7555A5E64A3B67C71D083E3606C8C819A4A02 |

## 3. Q1–Q8 và điều kiện dùng các mặc định

| Câu | Trạng thái | Mặc định/giả định dùng khi soạn | Chờ owner / ranh giới |
| --- | --- | --- | --- |
| Q1 | ĐÃ CHỐT | A: Parent không chọn activity trước video; list lesson hiện sau video xem được; Teacher pin đúng một activity đã duyệt trước video mẫu. | Chỉ thị trực tiếp owner ngày 2026-10-30. |
| Q2 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Typed opaque lesson-version ref tùy chọn qua owner port; không dùng org/class/Teacher occurrence cho Parent. Vị trí lưu chưa chốt. Run không lesson không tự sinh list hoặc fallback catalog. | Chờ owner: có no-lesson không; lesson source/version/hash, nơi lưu ref và nghĩa câu cấm Parent lesson ref. |
| Q3 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Theo A, Parent không cần scalar activity làm tiền điều kiện; Teacher vẫn pin. Không tự xác định field removal, NULL/CHECK hoặc thời điểm/vị trí ghi ref. | Nhánh B trong S6 không áp dụng vì đã chọn A; role representation và schema contract vẫn chờ owner. |
| Q4 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Tách quyền read catalog/lesson preview với bước chọn activity làm điều kiện video; A không có bước chọn, list của run chỉ lộ hậu video. | Chờ owner xác nhận read/preview/projection; giả định này không cấp quyền mới. |
| Q5 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Dùng VIDEO_READY sau technical/safety, không cần xem hết; current video còn được phép playback. Complete giữ read hợp lệ; hide/cancel/delete thu hồi projection theo contract. | Chờ owner: exact ready/viewed/complete/replacement behavior; 'video xem được' trong Q1 không tự chốt các chi tiết này. |
| Q6 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Giữ version/lineage metadata nhưng kiểm quyền hiện hành trước nội dung; không fallback public catalog hoặc trả nội dung đã revoke. Policy media/list tách riêng. | Chờ owner: unpublish/revoke khi đang render và sau pin/playback. |
| Q7 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Role-specific input: Parent không buộc activity, Teacher đúng một approved activity. Prompt/input/stale semantics và lesson direction Parent chưa freeze. | Không nhập optional hint của C vào A. Mặc định role split là giả định; chỉ việc không có bước chọn Parent thuộc Q1 đã chốt. |
| Q8 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Lập kế hoạch/approval riêng để hòa giải nguồn, giữ history và Q155 nghĩa tiếng Việt, dùng Q151 cho ordering; cập nhật B1 cần quyền riêng. | Chỉ thị lượt này chỉ cho tạo hai tài liệu: đã cho phép lập plan nhưng chưa xác nhận toàn bộ mặc định Q8 hoặc quyền sửa nguồn/B1. |

Chi tiết Q5 không được suy ra từ từ “xem được” của Q1. Q2/Q3 không được suy ra thành schema field, quyền cross-owner hay cột nullable đã được chấp thuận. Chỉ thị tạo plan hiện tại không phê duyệt trọn gói Q8 (sửa nguồn/trace/B1).

## 4. Bảng sửa từng clause — chưa áp dụng

Nguồn:dòng đều đã mở lại trong lượt này. “Trích hiện tại” là chuỗi con nguyên văn hoặc một dòng; chỉ thay clause đó, giữ toàn bộ phần còn lại, không thay cả hàng/state spec bằng bản rút gọn. Nếu cùng dòng có hai thao tác, áp dụng tuần tự và kiểm cả hai; không đè mất nhau. Đây là text đủ cụ thể để review/apply sau approval; mọi câu gắn Q chỉ là văn bản dự kiến, **chờ owner**, không chọn thay owner.

Riêng M045: cột trích là context D-99, không phải chuỗi để replace. Chỉ APPEND một entry với ID chưa trùng được kiểm lại lúc áp dụng; `D-TBD` là marker trong plan, không được ghi nguyên vào DECISIONS. Nội dung entry cũng chờ Q8/approval. Không sửa/xóa D-99 hay attribution lịch sử của nó.

| ID | File:dòng | Trích hiện tại (đã mở) | Văn bản thay thế / append đề xuất | Gate | Lý do / giữ nguyên |
| --- | --- | --- | --- | --- | --- |
| M001 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:81 | Transcript, chủ thể, hoạt động, giáo án và context hồ sơ có bước xem xét/xác nhận riêng trước khi tạo story. | Transcript, chủ thể và context hồ sơ được xem xét/xác nhận theo role trước story. Parent không chọn hoặc xác nhận activity làm tiền điều kiện story/video. Teacher sample vẫn ghim đúng một activity đã duyệt; lesson/plan được duyệt theo luồng Teacher. | CHỜ OWNER: Q7; còn AWAITING_APPROVAL B2A | Tách prerequisite theo role; giữ script gate và mọi câu về video phía sau. |
| M002 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:339 | SUBJECT_REVIEW/PREPARATION_REVIEW → STORY_GENERATING khi chủ thể, hoạt động và snapshot context đã xác nhận | SUBJECT_REVIEW/PREPARATION_REVIEW → STORY_GENERATING khi subject và snapshot context đã xác nhận; Parent không có điều kiện activity đã chọn/xác nhận, Teacher sample còn cần đúng một activity đã duyệt | Chỉ Q1=A; vẫn CHỜ APPROVAL B2A | A loại gate Parent; không thay các state, timer, quota hay owner-lock khác. |
| M003 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:360 | 4. **Lập story:** LLM nhận một tranh, snapshot của một trẻ, ý tưởng đã duyệt, một hoạt động và (chỉ với Teacher) giáo án/hướng kể đã duyệt. Output là script có cấu trúc cùng 5–15 scene. | 4. **Lập story:** LLM nhận tranh, snapshot tối thiểu và ý tưởng đã duyệt. Parent không có bước chọn hoặc xác nhận activity trước story/video. Teacher sample bổ sung đúng một activity đã duyệt và giáo án/hướng kể theo contract. Input/prompt cụ thể và lesson direction của Parent còn chờ Q2/Q7; không tự lấy activity đầu tiên làm fallback. Output vẫn là script có cấu trúc cùng 5–15 scene. | CHỜ OWNER: Q2, Q7; còn AWAITING_APPROVAL B2A | Đầu vào chung đang ngầm buộc activity Parent. |
| M004 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:391 | dựa trên tranh, ý tưởng đã xác nhận, activity, snapshot cá nhân hóa tối thiểu; Teacher thêm hướng kể từ plan. | dựa trên tranh, ý tưởng và snapshot cá nhân hóa tối thiểu đã xác nhận; Parent không có bước chọn activity trước story/video, Teacher bổ sung đúng một activity đã duyệt và hướng kể từ plan. Input/prompt và lesson direction Parent chờ Q2/Q7. | CHỜ OWNER: Q2, Q7; còn AWAITING_APPROVAL B2A | Hòa giải stage 4 với §6.2. |
| M005 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:592 | Parent profile → ảnh/ý tưởng → subject/activity/context review → story review → video Modal → playback/delete, trên dữ liệu tổng hợp | Parent profile → ảnh/ý tưởng → subject/context review → story review → video Modal → playback → lesson activity list theo quyền → delete, trên dữ liệu tổng hợp; nguồn lesson và projection theo Q2/Q5/Q6 còn chờ owner | CHỜ OWNER: Q2, Q5, Q6; còn AWAITING_APPROVAL B2A | P1 không còn selector activity trước story; giữ host ghi hiện có, không thêm provider decision. |
| M006 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:718 | Đọc catalog Parent đã phát hành; Teacher chọn activity theo quyền | Đọc catalog đã phát hành theo quyền hiện hành; đây không phải bước chọn activity làm điều kiện Parent story/video. Teacher vẫn chọn activity theo quyền. Quyền đọc/preview Parent trước video và projection của lesson list hậu video chờ Q2/Q4/Q6. | CHỜ OWNER: Q2, Q4, Q6; còn AWAITING_APPROVAL B2A | Không suy A thành quyền đọc mới hoặc cấm toàn bộ read. |
| M007 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:746 | Story/lesson giữ version đã chọn cùng activity snapshot/hash bất biến | Learning Content giữ catalog/version được duyệt; Teacher sample ghim đúng activity version/snapshot được phép. Parent không cần ghim catalog activity trước story/video. Nguồn immutable lesson/version và ref/snapshot phục vụ list hậu video chờ Q2/Q3; không đổi owner hoặc sao chép catalog. | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Tách source catalog khỏi Parent scalar selection. |
| M008 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:801 | Một người lớn, một trẻ, một hoạt động, input và revision context/script đã duyệt | Một người lớn, một trẻ, input và revision context/script đã duyệt; Teacher sample ghim đúng một activity đã duyệt. Parent không có bước chọn activity trước video; ý nghĩa scalar theo role chưa chốt; biểu diễn theo role chờ Q3 | CHỜ OWNER: Q3; còn AWAITING_APPROVAL B2A | Cardinality mô tả không buộc selection Parent. |
| M009 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:932 | 2. Story run có một activity và một scalar lesson-occurrence ref nếu là Teacher. | 2. Story run có đúng một profile ref có kiểu. Teacher sample có đúng một activity đã duyệt và scalar lesson-occurrence ref; Parent không cần activity đã chọn trước story/video. Nguồn lesson/version Parent và biểu diễn ref theo role chờ Q2/Q3, không suy ra schema/FK/NULL policy mới. | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Không khóa schema bằng quyết định ordering. |
| M010 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1044 | Có transcript, subject, activity, lesson/context và script revision | Có transcript nếu có voice, subject, context và script revision được duyệt theo role; Teacher bổ sung lesson/plan/activity đã duyệt. Parent không chọn/xác nhận activity trước story/video; stage/input chi tiết chờ Q7 | CHỜ OWNER: Q7; còn AWAITING_APPROVAL B2A | AC-08 phân role, giữ script-only cuối. |
| M011 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1072 | Một run có ảnh của đúng một trẻ, ý tưởng đã duyệt và hoạt động hợp lệ | Một run có ảnh của đúng một trẻ và ý tưởng đã duyệt; Teacher sample bổ sung đúng một activity hợp lệ đã duyệt, Parent không có pre-video activity-selection gate | Chỉ Q1=A; vẫn CHỜ APPROVAL B2A | Chỉ đổi Given AC-36; giữ toàn pipeline, safety và output criteria. |
| M012 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1206 | Parent chỉ dùng catalog hoạt động đã duyệt; | Trace lịch sử Q08–Q20: Parent chỉ dùng catalog hoạt động đã duyệt; annotation thứ tự hiện hành B2 Q1=A: Parent không chọn activity trước video, lesson activity list hiện sau video xem được; quyền đọc và binding chờ Q2/Q4; | CHỜ OWNER: Q2, Q4; còn AWAITING_APPROVAL B2A | Giữ lời khai catalog cũ, thêm annotation hiện hành, không viết lại ý owner cũ. |
| M013 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1208 | Parent chỉ dùng catalog; | Trace lịch sử Q31–Q40: Parent chỉ dùng catalog; annotation B2 Q1=A bỏ selection làm điều kiện trước video và đặt lesson list hậu video; quyền đọc chờ Q4; | CHỜ OWNER: Q4; còn AWAITING_APPROVAL B2A | Giữ trace cũ và phân biệt ordering mới. |
| M014 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1210 | Parent dùng catalog; | Trace lịch sử: Parent dùng catalog; theo B2 Q1=A, Parent không chọn activity trước video, Teacher sample vẫn pin một activity đã duyệt; binding/quyền đọc chờ Q2/Q4; | CHỜ OWNER: Q2, Q4; còn AWAITING_APPROVAL B2A | Một child/activity của Teacher không áp cho Parent. |
| M015 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1268 | Hoạt động ngoài trời có version, được quản trị nội dung duyệt và phát hành để Parent chọn, Teacher tham khảo. | Hoạt động ngoài trời có version, được quản trị nội dung duyệt/phát hành. Không dùng định nghĩa catalog để đặt precondition Parent chọn trước story/video. Teacher sample ghim đúng một activity đã duyệt; quyền read/preview Parent và list lesson hậu video chờ Q2/Q4. | CHỜ OWNER: Q2, Q4; còn AWAITING_APPROVAL B2A | Glossary không tự tạo bước chọn. |
| M016 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1280 | review transcript giọng trẻ, subject ảnh, activity/context và script. | review transcript giọng trẻ, subject ảnh, context và script theo role; Teacher sample còn duyệt lesson/plan/activity. Parent không có activity-selection gate trước story/video; biểu diễn stage/input chờ Q7. | CHỜ OWNER: Q7; còn AWAITING_APPROVAL B2A | Giữ mọi cổng adult khác. |
| M017 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1319 | ; catalog hoạt động đã duyệt sẵn sàng | ; Parent không chọn/xác nhận activity trước story/video; catalog/lesson readiness và quyền đọc trước video còn chờ owner Q2/Q4 | CHỜ OWNER: Q2, Q4; còn AWAITING_APPROVAL B2A | Q1 bỏ selection gate; không tự quyết catalog/lesson availability. Readiness chờ Q2/Q4. |
| M018 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1321 | chọn một hoạt động trong catalog →  | (xóa đúng clause này; không xóa phần còn lại) | Chỉ Q1=A; vẫn CHỜ APPROVAL B2A | Xóa đúng một bước trước snapshot, giữ transcript/subject/context/script/video; thêm clause hậu video ở M tiếp theo. |
| M019 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1321 | Parent xem rồi kết thúc | Khi video đã xem được, ứng dụng trình bày lesson activity list theo quyền; nguồn lesson/version và behavior READY/complete/hide/revoke chờ Q2/Q5/Q6; Parent có thể xem và kết thúc | CHỜ OWNER: Q2, Q5, Q6; còn AWAITING_APPROVAL B2A | A chốt thứ tự, chi tiết projection chưa được owner chốt. |
| M020 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1323 | Run hoàn tất gắn một trẻ, một hoạt động, context hồ sơ đã ghim, | Run Parent hoàn tất gắn một trẻ và context hồ sơ đã ghim, không đòi scalar activity như điều kiện trước video; liên kết lesson/activity-list hậu video và ref theo role chờ Q2/Q3; | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Giữ provenance và private artifact phía sau. |
| M021 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1522 | Chọn hoạt động Parent | Đọc catalog theo quyền hiện hành; không là lựa chọn activity bắt buộc trước Parent video (quyền preview/projection cụ thể chờ Q4) | CHỜ OWNER: Q4; còn AWAITING_APPROVAL B2A | Đây là đề xuất Q4: phải review từng ô role/action trước khi áp dụng; không coi giữ các ô cũ là đã freeze quyền read/preview. |
| M022 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1571 | activity Parent hoặc ref occurrence/plan/activity Teacher; | Parent không có bước chọn/xác nhận activity trước story/video; Teacher dùng ref occurrence/plan/đúng một activity đã duyệt; schema field/nullable và lesson-version Parent chờ Q2/Q3; | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Create-run không đòi selection; wire payload và checks chưa freeze. |
| M023 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1615 | catalog hoạt động; rà soát context snapshot; | rà soát context snapshot; catalog read/preview nếu Q4 được xác nhận là bề mặt độc lập, không phải selector activity trước story/video; | CHỜ OWNER: Q4; còn AWAITING_APPROVAL B2A | Bỏ selector khỏi chuỗi bắt buộc nhưng không tự xóa read/preview; Q4 quyết bề mặt và quyền. |
| M024 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1615 | trình phát video; Hoàn tất/hủy run; | trình phát video; lesson activity list sau video xem được (binding/quyền/projection chờ Q2/Q4/Q5/Q6); Hoàn tất/hủy run; | CHỜ OWNER: Q2, Q4, Q5, Q6; còn AWAITING_APPROVAL B2A | Bổ sung bề mặt hậu video mà không quyết quyền preview. |
| M025 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1837 | Parent chọn catalog toàn cục đã duyệt; | Catalog toàn cục đã duyệt không tạo precondition chọn activity cho Parent story/video theo A; quyền đọc/preview và projection hậu video chờ Q2/Q4/Q6; | CHỜ OWNER: Q2, Q4, Q6; còn AWAITING_APPROVAL B2A | Giữ contract metadata/filter schema/moderation và Teacher checklist. |
| M026 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2247 | Catalog query: published versions only; deterministic filtering/order plus age/safety boundaries. AC-05. | Catalog query: published versions only; deterministic filtering/order plus age/safety boundaries. AC-05. In addition, verify the Parent flow has no pre-video activity-selection step and presents the lesson activity list after video is viewable; lesson binding, read authorization and projection/revocation cases await Q2/Q4/Q5/Q6. AC-52; B2 Q1=A. | CHỜ OWNER: Q2, Q4, Q5, Q6; còn AWAITING_APPROVAL B2A | Thêm ordering coverage, giữ nguyên published/deterministic filtering/order/age/safety criteria và AC-05. |
| M027 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2386 | Q08/Q32/Q85 activity source | Q08/Q32/Q85: historical catalog eligibility; Q151 + B2 Q1=A: Parent post-video ordering | CHỜ OWNER: Q8; còn AWAITING_APPROVAL B2A | Đính chính nguồn timing, giữ provenance cũ. |
| M028 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2386 | UC-05/14 \| learning_content.records/versions; lesson.plan_activities | UC-02/05/14; §31.5 \| learning_content.record/version; lesson.plan_activities/version_activities; Parent lesson linkage pending Q2 | CHỜ OWNER: Q2, Q8; còn AWAITING_APPROVAL B2A | Bổ sung trace Parent/lesson; không khóa bảng/ref mới. |
| M029 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:331 | revision lesson/activity và contract version | các revision lesson/activity áp dụng cho role và input đã pin, cùng contract version; Parent không bị coi là stale chỉ vì thiếu lựa chọn activity trước video, còn tập ref/hash cụ thể chờ Q2/Q3 | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Không còn validator ngầm đòi ref Parent, giữ mọi ref áp dụng. |
| M030 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1690 | StoryRun target kiểm run/input/lesson/activity; | StoryRun target kiểm run/input và các lesson/activity ref áp dụng theo role/contract đã pin; không buộc Parent có pre-video activity selection; tập ref và hash theo role chờ Q2/Q3; | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Completion không tạo lại mandatory activity qua guard chung. |
| M031 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2361 | Q151/Q155; BR-55 | Q151 + B2 Q1=A; BR-55 | CHỜ OWNER: Q8; còn AWAITING_APPROVAL B2A | Q155 giữ nghĩa tiếng Việt tại2632; chỉ sửa trace source hiện hành. |
| M032 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2434 | Q151/Q155; Parent activities | Q151 + B2 Q1=A; Parent activities | CHỜ OWNER: Q8; còn AWAITING_APPROVAL B2A | Không dùng citation Q155 cho ordering. |
| M033 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:166 | không có assignment hoạt động riêng cho nhóm/session; một hoạt động chọn được ghim trên story run | Không có assignment hoạt động riêng cho nhóm/session. Parent không chọn/ghim activity làm tiền điều kiện story/video; lesson list hiện sau video xem được. Teacher sample vẫn ghim đúng một activity đã duyệt. Nguồn lesson và biểu diễn theo role chờ Q2/Q3. | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Giữ legacy/read-only, không tạo assignment table. |
| M034 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:200 | Parent chỉ chọn version đã xuất bản và được duyệt. | Parent không chọn catalog activity làm tiền điều kiện story/video theo A; list lesson hiện sau video xem được. Catalog chỉ dùng version được duyệt ở nơi áp dụng. Binding và read/preview/projection chờ Q2/Q4/Q6. | CHỜ OWNER: Q2, Q4, Q6; còn AWAITING_APPROVAL B2A | Giữ catalog source và content review owner. |
| M035 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:260 | Parent ghim chính xác version đã xuất bản. | Parent không cần ghim catalog activity trước story/video; Teacher sample ghim đúng version/snapshot activity được phép. Parent lesson binding và biểu diễn/read/revoke chờ Q2/Q3/Q4/Q6. | CHỜ OWNER: Q2, Q3, Q4, Q6; còn AWAITING_APPROVAL B2A | Version immutable vẫn giữ, không cấp access bằng ref. |
| M036 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:369 | Parent không có tham chiếu org/class/lesson; Teacher cần lớp được phân quyền, occurrence, plan đã duyệt và đúng một trẻ. Chỉ một activity scalar. | Teacher cần lớp được phân quyền, occurrence/plan đã duyệt, đúng một trẻ và đúng một activity đã duyệt. Parent không cần chọn/xác nhận activity trước story/video. Quan hệ reusable lesson của Parent và ý nghĩa câu cấm org/class/lesson trước đây còn chờ Q2; activity_ref/version theo role, vị trí lưu, tính tùy chọn và CHECK/NULL policy chờ Q3. Chưa suy ra bảng/cột/FK mới. | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Chỉ thay cụm ràng buộc này; giữ danh sách field, XOR, timer, lock, reassignment, purge. |
| M037 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:375 | Stage gồm transcript, subject, hoạt động/context và xác nhận kịch bản. | Stage gồm transcript, subject, context và xác nhận kịch bản theo role; Teacher có prerequisite lesson/plan/activity tương ứng. Parent không có stage bắt buộc chọn/xác nhận activity trước story/video. Stage enum/record structure và trigger story còn chờ Q3/Q7. | CHỜ OWNER: Q3, Q7; còn AWAITING_APPROVAL B2A | Giữ exact target/hash và script sole human video gate; không tự thêm enum/command. |
| M038 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:474 | Parent story ghim catalog version được duyệt; Teacher plan dùng versioned ref; không sao chép catalog vào hồ sơ. | Teacher plan dùng versioned ref/snapshot activity được phép. Parent không ghim catalog làm tiền điều kiện story/video; list lesson hiện hậu video. Binding và quyền đọc chờ Q2/Q4/Q6; không sao chép catalog vào hồ sơ. | CHỜ OWNER: Q2, Q4, Q6; còn AWAITING_APPROVAL B2A | Owner graph không đồng nghĩa selection Parent. |
| M039 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:495 | không có profile dùng chung Parent/Teacher. | không có profile dùng chung Parent/Teacher. Theo A, Parent không chọn activity trước story/video, list lesson hiện sau video xem được. Linkage lesson-version/no-lesson/ref location, quyền đọc và READY/complete/replacement/revoke còn chờ Q2–Q6; input planner chờ Q7. Đây chưa là contract linkage hoàn chỉnh. | CHỜ OWNER: Q2, Q3, Q4, Q5, Q6, Q7; còn AWAITING_APPROVAL B2A | Bổ sung gap trong luồng dữ liệu, không vẽ ref chưa chốt. |
| M040 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:531 | Chọn catalog theo version đã duyệt | Activity và lesson version theo role | CHỜ OWNER: Q2, Q3; còn AWAITING_APPROVAL B2A | Tiêu chí không mang nghĩa mọi run đều chọn trước. |
| M041 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:531 | Run ghim activity ID/version/hash của catalog; module content xác minh trạng thái đã xuất bản/được duyệt | Teacher sample ghim activity ID/version/hash được phép; owner content/lesson kiểm version/checklist tương ứng. Parent không chọn activity trước story/video; binding, ref theo role và read/revoke hậu video chờ Q2/Q3/Q4/Q6. Không lấy activity đầu tiên hoặc fallback catalog. | CHỜ OWNER: Q2, Q3, Q4, Q6; còn AWAITING_APPROVAL B2A | Giữ pin Teacher; không chốt cách lưu Parent. |
| M042 | docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md:13 | Parent follows profile → optional generic-topic AI line-sketch guide → child drawing/capture → idea → post-capture subject confirmation → approved catalog activity → story. | Parent follows profile → optional generic-topic AI line-sketch guide → child drawing/capture → idea and transcript review → post-capture subject/context review → story/script confirmation → child-specific video pipeline → lesson activity list after video is viewable. Option A removes Parent activity selection/confirmation as a story/video prerequisite. Teacher still pins one approved activity before the sample video. Parent lesson binding, reference representation, catalog access, playback/replacement and planner-input contracts remain unconfirmed Q2–Q8 working assumptions. | CHỜ OWNER: Q2, Q3, Q4, Q5, Q6, Q7; còn AWAITING_APPROVAL B2A | Thay clause Parent; giữ các câu về deck/guide/privacy/Teacher projection, không quyết lại deck optional. |
| M043 | docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md:34 | - Parent activity choices come only from globally approved catalog entries. Teacher may define an occurrence-specific activity and confirm it via a safety checklist. | - Parent does not select an activity as a story/video prerequisite under option A; the lesson activity list is presented after video is viewable. Catalog read/preview, lesson source/version and current authorization await Q2/Q4/Q6. Teacher still pins one approved activity and may use an occurrence-specific activity with the safety checklist. This amendment grants no new catalog access permission. | CHỜ OWNER: Q2, Q4, Q6; còn AWAITING_APPROVAL B2A | Giữ Teacher catalog/custom checklist. |
| M044 | docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md:56 | - Transcript, subject, activity, lesson and context are confirmed at their own prerequisites. The explicit approval gate before video is the final story/script/storyboard revision confirmation. No final video approval gate exists. | - Transcript, subject and context are confirmed at applicable prerequisites. Teacher sample additionally requires the approved lesson/plan/activity; Parent has no mandatory pre-story or pre-video activity-selection gate under option A. Final script/storyboard revision confirmation remains the explicit human gate before video, without final human-video approval. Exact role-specific stage/ref/planner contracts await Q3/Q7. | CHỜ OWNER: Q3, Q7; còn AWAITING_APPROVAL B2A | Giữ script confirmation cuối, stage/Q schema chưa chốt. |
| M045 | features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:104 (chỉ context) để thêm entry mới | \| D-99 \| Parent sequence is drawing, optional line-sketch while the child draws, capture, child-specific video pipeline, then the lesson activity list. Teacher line-sketch is also generated only when enabled in session; this supersedes D-91/D-92’s assumption that the Teacher deck is a required main-flow step. Keep the Teacher occurrence/sample flow with one randomly selected eligible child and one pinned activity. \| Owner answers Q151/Q155/Q167/Q184–Q186; Q167 supersedes the Teacher-deck status in D-91/D-92 \| | \| D-TBD (kiểm ID trống khi có approval) \| Owner selects option A for ordering only: Parent does not select/confirm an activity before story/video; the lesson activity list is presented after video is viewable; Teacher sample still pins exactly one approved activity. Q2–Q8 remain unconfirmed working assumptions. Existing D-99 remains historical; its Q155 citation is not evidence of ordering (Q151 is ordering, Q155 Vietnamese-first). Preserve Rev25/Q151, old approvals, v2.2 and historical diagram/PDF snapshots. No API/schema/runtime authorization or B1 unblock is implied. \| Direct owner instruction dated 2026-10-30; B2_OWNER_DECISION_A_20261030.md; Q151/Q155. Recording timestamp from machine is not an exact chat timestamp. \| | CHỜ OWNER: Q8; còn AWAITING_APPROVAL B2A | APPEND ONLY: câu hiện tại là context D-99, không thay/xóa/sửa nó; ID mới chỉ cấp sau kiểm trùng. |

## 5. Coverage PRE_VIDEO / AMBIGUOUS và phần không sửa

| Inventory B2 | Nguồn:dòng | Phân loại tại B2 | M### hoặc giữ nguyên | Cách xử lý |
| --- | --- | --- | --- | --- |
| I002 | SRS:81 | PRE_VIDEO | M001 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I019 | SRS:339 | PRE_VIDEO | M002 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I021 | SRS:360 | PRE_VIDEO | M003 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I027 | SRS:391 | PRE_VIDEO | M004 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I038 | SRS:592 | PRE_VIDEO | M005 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I042 | SRS:718 | AMBIGUOUS | M006 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I043 | SRS:746 | AMBIGUOUS | M007 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I047 | SRS:801 | AMBIGUOUS | M008 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I050 | SRS:932 | AMBIGUOUS | M009 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I054 | SRS:1044 | AMBIGUOUS | M010 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I056 | SRS:1072 | PRE_VIDEO | M011 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I060 | SRS:1206 | AMBIGUOUS | M012 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I061 | SRS:1208 | AMBIGUOUS | M013 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I062 | SRS:1210 | AMBIGUOUS | M014 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I066 | SRS:1268 | AMBIGUOUS | M015 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I069 | SRS:1280 | AMBIGUOUS | M016 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I070 | SRS:1319 | AMBIGUOUS | M017 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I071 | SRS:1321 | PRE_VIDEO | M018, M019 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I072 | SRS:1323 | AMBIGUOUS | M020 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I089 | SRS:1522 | AMBIGUOUS | M021 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I093 | SRS:1571 | PRE_VIDEO | M022 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I094 | SRS:1615 | AMBIGUOUS | M023, M024 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I101 | SRS:1837 | AMBIGUOUS | M025 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I112 | SRS:2247 | AMBIGUOUS | M026 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I127 | SRS:2386 | AMBIGUOUS | M027, M028 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I162 | REG:166 | AMBIGUOUS | M033 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I167 | REG:200 | AMBIGUOUS | M034 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I173 | REG:260 | AMBIGUOUS | M035 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I181 | REG:369 | AMBIGUOUS | M036 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I182 | REG:375 | AMBIGUOUS | M037 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I188 | REG:474 | AMBIGUOUS | M038 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I192 | REG:531 | AMBIGUOUS | M040, M041 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I208 | R36:61 | AMBIGUOUS | KEEP — R36:61 lịch sử | Không sửa Rev36 hoặc B2 inventory; dẫn decision A và liệt kê chi tiết còn mở. |
| I209 | ADR21:13 | PRE_VIDEO | M042 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I211 | ADR21:34 | AMBIGUOUS | M043 | Đề xuất sửa; phụ thuộc ghi ở từng M### |
| I214 | ADR21:56 | AMBIGUOUS | M044 | Đề xuất sửa; phụ thuộc ghi ở từng M### |

Bao phủ **36/36** đoạn PRE_VIDEO/AMBIGUOUS: 35 có đề xuất trong bảng, R36:61 là exception có lý do. R36:60–61 mô tả trạng thái lúc plan cũ được lập; không sửa plan cũ hoặc inventory B2 để giả như nguồn đã thống nhất.

Các nguồn đã đúng ordering (BR-08/09/15, FR-P-05, FR-PL-16, AC-05/52, ADR22:41) giữ nghĩa A. Chỉ sửa trace liên quan ở SRS:2361/2434 và BR-08 trace:2386 như bảng, không sửa Q151/Q155 gốc. Mọi row POST_VIDEO/NEUTRAL/TEACHER còn lại được rà lại sau amendment để phát hiện ref đòi activity Parent qua validator chung.

Cột A S3 còn nhắc REG:495 và các trace; bảng thêm chúng cùng SRS:331/1690 (generic stale/completion checks) để không vô tình tái tạo mandatory Parent activity qua guard. SRS:1677 “chỉ khi stage cần” giữ nguyên và dùng làm điểm đối chiếu, không cấp quyền bỏ validate ref thực sự áp dụng.

## 6. Thứ tự thực hiện sau approval

| Bước | Việc dự kiến | Điều kiện hoàn tất |
| --- | --- | --- |
| A0 | Kiểm approval exact plan hash, file ownership, S0/source hashes, 8 local file, status/index; đọc lại clause | Không drift; chỉ file được duyệt; không sửa local owner |
| A1 | Owner trả lời Q2–Q8 theo thao tác và review delta văn bản dự kiến | Có câu trả lời/authority rõ; row thiếu câu trả lời còn BLOCKED |
| A2 | Áp dụng các clause SRS theo role, UC/state/pipeline/API/UI/AC | Không Parent selector trước video; Teacher pin còn; phần không liên quan giữ bytes |
| A3 | Áp dụng register và ADR-0021 theo Q đã xác nhận | Binding/ref/stage/read/projection khớp, không cột/FK/migration/code mới |
| A4 | Đồng bộ trace và append một quyết định mới nếu Q8/approval cho phép | Q151 ordering, Q155 tiếng Việt; D-99/approval/preserved giữ nguyên |
| A5 | Kiểm tĩnh toàn nguồn và đếm lại phân loại theo §7, chạy validators đã được scope | Báo số thật, residual ambiguity và blockers; không test/runtime |
| A6 | Báo owner delta, hash, kết quả và giới hạn; xin bước B1 riêng khi đủ | Không tự gỡ B2, không tự commit/push; một task chỉ một commit khi owner yêu cầu |

Plan này không thay Rev36 backend plan, không triển khai S1/S2/S3, không đổi file/migration ownership hoặc task code. Rev36:61 được cross-reference là historical unresolved-source record; A giải quyết hướng ordering, không giải quyết toàn contract. Rev36:71 và FEAT-064 ngoài Parent/StoryRun vẫn giữ nguyên; không tạo prerequisite mới cho pilot. Nếu owner muốn sửa Rev36 hoặc backend contract ngoài các clause SRS này, cần scope/approval riêng, không nhét vào amendment.

## 7. Acceptance và kiểm sau sửa (dự kiến, chưa chạy)

- Mỗi clause được duyệt có exact before/after trace và hash; 36/36 PRE/AMB được đánh dấu đã sửa hay còn chờ có lý do. Đếm lại inventory trên nguồn đã sửa trong **report mới**, không ghi đè B2 inventory lịch sử.
- Không còn đoạn có hiệu lực đòi Parent chọn/xác nhận/ghim activity trước story/video; scan UC/state/P1/API/UI/pipeline/AC và guard completion/stale theo role. Tách câu nói history v2.2/Q cũ khỏi yêu cầu hiện hành.
- Teacher sample vẫn bắt đúng một activity đã duyệt và checklist khi custom; không suy A thành bỏ pin Teacher, cấp catalog read hay bỏ các adult/safety gates.
- API/schema/state/UI/AC/pipeline dùng cùng contract đã owner chốt; ref lesson/no-lesson, Q3 representation, preview/read, ready/complete/hide/revoke và Q7 prompt đều có quyết định hoặc được ghi rõ chưa hoàn tất. Không “pass” bộ hòa giải khi còn Q chặn.
- Trace FR/BR/AC khớp: FR-P-05 ↔ UC-02 ↔ BR-08/15 ↔ AC-05/36/52; Q151 cho ordering, Q155 chỉ language, D-99 vẫn giữ. Không đổi history Rev25/v2.2/diagram snapshot.
- Kiểm hash mọi source ngoài scope, B0/B1/B2/approval/plan cũ và 8 local file; chỉ delta cho file/clause được duyệt. Không code, schema migration, test hoặc dịch vụ.
- Chạy các validators documentation: python tools/validate_harness.py; python tools/validate_repository_security.py; python tools/validate_architecture.py; git diff --check; whitespace riêng file untracked. Có output mới báo kết quả, lệnh không verdict là NOT RUN.

## 8. Rollback tài liệu và chống ghi đè

Trước amendment tương lai, lấy bản bytes/hash của file/clause được duyệt từ snapshot/commit nền đã kiểm. Nếu phát hiện đổi ngữ nghĩa ngoài scope hoặc owner không chấp nhận, dừng; lập inverse patch cho **chính clause task đã sửa**, so current bytes rồi trình owner. Không reset/revert cả file có local/concurrent edits; không stash/xóa file owner. Nếu có xung đột, yêu cầu owner chọn cách xử lý thay vì ghi đè. Entry quyết định đã ghi được hiệu chỉnh bằng lịch sử rõ ràng theo approval, không xóa provenance để che thay đổi. Không có DB/code/runtime nào trong rollback này.

## 9. Bước B1 tách riêng

16 dòng T018–T031, T046, T047 **VẪN blocked_by=B2**, E0/pilot=N. Không sửa CSV/MD B1 trong B2A. Chỉ xem xét plan/approval B1 mới sau source/contract của từng dòng nhất quán và các Q chặn được xác nhận. Mục approval B1 đang pin output hashes; không dùng approval B2A hoặc lựa chọn A để vượt nó. B3/B7/B9/B10/B11 là các cổng khác trong backlog, không tự gán vào ô B1.

## 10. Approval request — owner ghi, không tự sửa

Đề nghị owner rà plan này rồi ghi một mục approval mới, ít nhất gồm: **Status**, **Approved plan** = `plan/B2A_SRS_REGISTER_AMENDMENT_PLAN_20261030.md`, **Approved plan SHA-256** = hash bytes chính file này báo cuối, M###/file được phép áp dụng, Q2–Q8 nào đã được owner xác nhận (ghi câu trả lời/căn cứ), và scope/exclusions.

Không ghi sẵn self-hash trong chính file để tránh tự đổi hash. Owner có thể lấy lại bằng Get-FileHash -Algorithm SHA256 với đường dẫn repo-relative của plan. Nếu sửa plan sau review, hash đổi thì approval phải pin bản cuối. Chưa có approval = không áp dụng; row Q chưa xác nhận = không áp dụng row đó. B1 amendment và bất kỳ source/code/provider/DB/runtime nào ngoài scope vẫn cần approval riêng.

## 11. Kiểm của lượt tạo hai tài liệu hiện tại

| File | S0 SHA-256 (16 đầu) | Cuối task |
| --- | --- | --- |
| docs/context/SOURCE_REGISTER.md | 26990af90db093ea | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | 98040aa6871048f6 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md | c67f37133de35ded | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/DEV_REMOTE_HISTORY_COMPARISON_20261030.md | adcc6724ebc3c642 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md | 8bbfd0edaa7cd6a2 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md | b61b06074665ba71 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md | 93374e9643649b67 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/plan/S1_DECISION_CARD_20261030.md | 4d95d3031f8af163 | KHỚP (giữ nguyên) |

Kết quả thật của lượt tạo hai tài liệu:

| Lệnh | Output/verdict thật | Exit |
| --- | --- | --- |
| python tools/validate_harness.py | HARNESS_VALID; approval_gate=enabled; frontend_asset_gate=enabled | 0 |
| python tools/validate_repository_security.py | REPOSITORY_SECURITY_VALID; publishable_files_scanned=5930; absolute_machine_paths=absent | 0 |
| python tools/validate_architecture.py | ARCHITECTURE_VALID; python_dependency_direction/mobile_feature_isolation/frontend_asset_gate/mobile_ai_boundary valid; firebase_data_products=absent | 0 |
| git diff --check | stdout rỗng | 0 |

Không chép root máy từ stdout vào file. git diff --check không quét untracked; hai file mới được kiểm riêng UTF-8/LF, 0 dòng trailing whitespace, không có mẫu absolute path hoặc secret. Kiểm nguồn: 45/45 clause context khớp source đã mở; coverage 36/36 PRE/AMB (35 có đề xuất, R36:61 giữ lịch sử). 3 thao tác chỉ Q1, 42 thao tác chờ Q2–Q8; không áp dụng thao tác nào vào nguồn.

So lại baseline: **143/145 file giữ nguyên hash**; hai file hướng dẫn `AGENTS.md` và `.claude/sketch2life-harness.md` đổi trong lúc task chạy. Phiên này không ghi hai file đó; chưa xác minh tiến trình nào đã ghi. Đồng thời owner cung cấp AGENTS mới trong chat; đã đọc lại `.codex/*harness*.md` trước, rồi AGENTS và harness Claude. Không khôi phục hoặc ghi đè thay đổi bên ngoài. **8/8 local và mọi source sản phẩm/B0/B1/B2/plan/approval giữ nguyên hash.** Phiên này chỉ ghi hai đầu ra mới; working tree còn drift hướng dẫn ngoài task. Không stage/commit/push/stash hoặc test/dịch vụ. Đây là kiểm tài liệu, không nghiệm thu amendment/runtime; Q2–Q8 và approval áp dụng plan vẫn chưa được xác minh.


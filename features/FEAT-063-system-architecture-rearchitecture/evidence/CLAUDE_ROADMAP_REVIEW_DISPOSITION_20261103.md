# Disposition review cloud vòng 1–2 — roadmap BE sáu mốc — 2026-11-03

## Kết luận

Vòng 2: **NEEDS_REVISION, mức nhẹ**. Các finding N1–N7 và các ghi chú P2/P3 có căn cứ đã được đưa vào roadmap dưới dạng phạm vi, dependency hoặc cổng cần owner duyệt. Đây là sửa tài liệu; roadmap vẫn DRAFT, SRS v2.3 vẫn unsigned và không có M2–M6 nào được approval triển khai.

- Plan Rev49: `plan/ROADMAP_REVIEW_FIX_PLAN_20261103.md`, SHA-256 `BECC69238E5049649204E5F9C32D2CB9660E625B795E131C4A5553599D08901C`.
- Plan Rev50: `plan/ROADMAP_REVIEW_FIX_PLAN_REV50_20261103.md`, SHA-256 `0FFF0D9CAA01036E08A90120FC7067D38B564E80E72E4324B470D1E8E13C66DC`.
- Roadmap trước vòng 2: SHA-256 `9DF3FECF0FFF45972ADFB4D49A50E31773CBAD8832F0B5C5B625C9702CEB49CC`.
- Roadmap sau vòng 2: SHA-256 `DED4B89D6A3F66FD0570EEA11E2240840C47DE607667544708C7C394F7F49C86`.

## Finding vòng 2

| Finding | Disposition | Nội dung đã ghi vào roadmap |
|---|---|---|
| N1 — quota boundary M5/M6 | **ACCEPT** | M5 cần Parent-scope Billing grants + append-only usage, quota tháng `Asia/Ho_Chi_Minh`, included-first/FIFO, concurrency AT-06/09, cap BR-11 và AI Policy compute reservation; cùng idempotency key và đủ receipt trước accepted/dispatch. M6 làm commerce và mở rộng Teacher/school scope. |
| N2 — lesson access dependency | **ACCEPT-WITH-BOUNDARY** | SRS cho phép Parent chạy không lesson; no-lesson là phạm vi ban đầu M4/M5. Optional lesson path chỉ bật khi có current authorization/revoke/unpublish contract. Muốn kéo read permission lên sớm phải xin approval riêng. Synthetic fixture không chứng minh authorization; không fallback sang public lesson khi ref bị revoke. |
| N3 — Q146 | **ACCEPT** | Q146 đã được trả lời về sản phẩm. Scheduling Parent line-sketch và các gate model/version, license, cost, safety, retention, POC, SRS sign-off là các việc riêng. Hoãn lịch không phải chờ owner trả lời lại Q146. |
| N4 — lifecycle | **ACCEPT** | Ghi +144h tạo đúng một inbox reminder; +168h `VIDEO_READY` → `COMPLETED`, các adult-wait state khác → `ABANDONED`; mỗi mốc xử lý cancel/late result/purge hoặc ghi debt cho artifact/job của mình. Video cancellation thuộc M5; D-127 debt được nêu ở M2. |
| N5 — model gates M3/M4 | **ACCEPT** | Trước M3/M4 cần synthetic POC và owner chọn model/version cùng license/cost/safety/retention/capacity gates. Không ghi Qwen3-VL thành lựa chọn: SRS nêu NO_GO; Qwen2.5-VL-7B chỉ là candidate; Whisper và Qwen2.5-7B chưa benchmark. |
| N6 — A2 residuals at M2 entry | **ACCEPT-WITH-BOUNDARY** | A2 được closeout ACCEPTED/COMPLETE trong scope riêng, nhưng residuals không biến mất: 58 synthetic rows ở shared `sketch2life`, physical schema chưa đối soát Alembic history, một mypy baseline issue. Trước M2 migration phải có DB task-owned cô lập hoặc quyết định an toàn riêng, schema/history reconciliation, data disposition và ghi baseline type-check; không tự dọn DB dùng chung. |
| N7 — B-ID/backlog | **ACCEPT** | B10 được thống nhất: idempotency/job nền M2; Parent quota/usage/compute gate M5; commerce và Teacher/school mở rộng M6. B4b consent sau OI-05..08; M2 từ chối `REAL`/`LEGACY_UNCLASSIFIED` nếu gate chưa đạt. Backlog lịch sử trỏ về roadmap hiện hành. |
| M2/M6 breadth | **ACCEPT** | Roadmap vẫn ở mức milestone; mỗi phase plan phải chia M2/M6 thành subphase, crosswalk, AC/AT, stop gate và data/migration boundary trước launch. |
| M4 “no video before script approval” | **ACCEPT** | M4 hoàn tất story/script review; điều kiện không dispatch video trước khi có script approval thuộc M5 entry/dispatch gate, nơi kiểm chứng được. |
| Priority FEAT-064 A2→B1→B2 | **ACCEPT-WITH-BOUNDARY** | Chuỗi này là luồng điều phối riêng và có thể tạm được owner ưu tiên trước M2–M6. Trạng thái phase đang chạy phải lấy từ active implementation thread, không suy ra từ roadmap hoặc header của goal cũ. |

## Đính chính các kết luận của disposition Rev49

| Chủ đề | Kết quả kiểm tra vòng 2 | Đính chính |
|---|---|---|
| D-130 OpenAPI | **Reviewer đúng; lỗi do bản sửa Rev49.** | Rev49 chỉ quét ID trong bảng, bỏ sót heading `D-130 — Full BE API inventory source and Bruno separation`. OpenAPI Rev45 được đổi thành D-131; D-130 hiện hữu giữ nguyên. Bảng Swagger lịch sử D-114..D-119 được giữ nội dung nhưng bỏ các ID trùng vì đó là summary, không phải các quyết định mới. |
| DTR hash | **Reviewer đúng; giải thích là line ending.** | Local CRLF SHA-256 là `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22`; chuẩn hóa bytes local sang LF cho `201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2`, trùng giá trị cloud báo. Mismatch là line-ending representation, không phải nội dung khác trong phép đối chiếu này. Rev49 nói không tái hiện và phỏng đoán checkout khác là chưa đúng. |
| B0–B13 plan provenance | **Reviewer đúng; vấn đề nội dung thật.** | Plan hiện tại/LF SHA-256 `773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A`; CRLF representation SHA-256 `C50E07329B2D97496B1B7EE6D8094806FA519BFC5AC1D1560DE3478196E0A956`; report records `03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582`. Neither representation matches the report hash, so line endings do not explain it. Historical bytes are unavailable. Do not silently treat the current plan as approved; owner must confirm it or approve an addendum before it is used as authority. |
| D-114 duplicate | **Reviewer đúng.** | D-114 là quyết định Parent activity hiện hành và bị tái sử dụng trong bảng Swagger summary lịch sử. D-115..D-119 cũng là summary IDs lặp. Rev50 giữ nội dung lịch sử nhưng đổi bảng thành summary không mang decision IDs. |
| Source register | **Reviewer đúng về giới hạn quan sát.** | FEAT-063 `SOURCE_REGISTER.md` đã được cập nhật ở local trong Rev49, nhưng thay đổi chưa nằm trong ref cloud reviewer đọc. Vì vậy reviewer chỉ có thể nói chưa xác minh, không thể kết luận file không tồn tại trong local checkout. |
| M1/A2 status | **Không phải lỗi reviewer.** | M1 review round 3 có record ACCEPTED trên ref. A2 closeout local cho ACCEPTED/COMPLETE nhưng reviewer ghi rõ không xác minh thread reviewer. Roadmap trích status theo các record có sẵn và nêu đúng giới hạn; không xem đây là review mới của Claude. |
| Goal A2→B1→B2 status | **Reviewer đúng về giới hạn.** | Goal có file/plan, nhưng header DRAFT và tài liệu không xác định phase nào đang chạy. Chỉ active implementation thread mới xác nhận launch/status hiện tại. |
| “FR-PL hoàn toàn vắng mặt” | **Nuance Rev49 vẫn đúng.** | Roadmap cũ có nhắc một số capability theo nhóm; thiếu sót thật là không truy vết rõ FR-PL/BR/NFR, owner và acceptance đo được. Vòng 2 không bác bỏ nuance này. |

## Nguồn và giới hạn

- SRS v2.3-draft SHA-256 `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC`; chưa sign-off.
- DTR CRLF/LF hashes và A2 closeout được ghi ở Plan Rev50; không sửa SRS/DTR hay A2 artifacts.
- B0–B13 report SHA-256 `8061DE7447A5C1A319D318290EE529BCF78A36C8DB013A53C2C34F35691B5645`.
- A2 closeout SHA-256 `10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36`; ghi nhận rõ hạn chế 58 rows, Alembic reconciliation và mypy baseline.
- FEAT-064 sequential goal SHA-256 `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A`; không dùng để khẳng định phase launch.

Không có finding vòng 2 nào được chứng minh là reviewer sai. Reviewer đúng ở các correction D-130, D-114, B0 provenance và DTR line-ending; đúng khi giới hạn kết luận về source register và live phase status theo dữ liệu cloud. N2 là dependency/option cần phase owner duyệt, không phải căn cứ tự động kéo quyền lesson lên sớm.

## Prompt review độc lập vòng 3

> Review độc lập chỉ đọc vòng 3 cho roadmap sáu mốc. Các thay đổi hiện là local-only; nếu phiên cloud không đọc được worktree hiện tại, dùng các file owner đính kèm, không review bytes cũ từ `origin`. Trước khi review, xác minh đúng SHA-256:
>
> - Plan Rev50: `0FFF0D9CAA01036E08A90120FC7067D38B564E80E72E4324B470D1E8E13C66DC`.
> - Plan Rev50A: `27288634F301B7430C531E17B51EE15D35B0EB3735C26925767111447849661D`.
> - Roadmap: `DED4B89D6A3F66FD0570EEA11E2240840C47DE607667544708C7C394F7F49C86`.
> - Historical B0–B13 backlog after Rev50A: `380BF9F813CF809E35D9EA6F843E33A0DF892BA886E8C366AEB1C0F757A57391`.
> - DECISIONS: `374BDD4B593791618E67DA037877AF64CF876E1AA79A64782DA4DAE0770AEED6`.
> - Approval: `29E3B8C85A6565E365196C0A813A5B484D3FCE56473DB3F541DD50592A20580B`.
> - SRS v2.3-draft: `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC`.
> - DTR: working CRLF SHA `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22`; LF-normalized SHA `201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2`.
> - A2 closeout: `10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36`.
>
> Đọc thêm `approvals/TASK_APPROVAL.md`, FEAT-063 `CONTEXT.md`/`status/STATUS.md`, nguồn SRS/DTR và evidence A2. Không chạy tests/validators, không kết nối DB, không gọi Modal/provider/network, không sửa file, không subagent, không stage/commit/push/merge.
>
> Kiểm tra đặc biệt: N1 quota/compute thực sự nằm ở M5 và M6 chỉ là commerce/Teacher scope; N2 no-lesson default và authorization gate cho optional lesson; Q146 đã answered; N4 144h/168h và cancel/late result/purge ownership; N5 model POC/selection gates; N6 residual A2 không bị che khuất; N7 B10/B4b; M2/M6 subphase; điều kiện script approval nằm ở M5; ưu tiên FEAT-064 được mô tả không suy diễn thread status; D-130/D-131 không trùng; bảng Swagger historical summary không còn ID decision trùng; DTR line-ending explanation; B0 plan provenance không tự phê duyệt; cloud visibility limits được diễn đạt đúng.
>
> Trả verdict ACCEPTED hoặc NEEDS_REVISION, từng finding kèm mức độ, file/đoạn, bằng chứng và sửa tối thiểu. Không coi roadmap là SRS sign-off hoặc implementation approval.

## Giới hạn công việc

Chỉ cập nhật tài liệu trong allowlist Rev50. Không chạy test/validator suite; chỉ chạy `git diff --check` và kiểm tra hash/nội dung tài liệu. Không truy cập DB, Modal/provider, mạng hay Git remote; không stage, commit, push hoặc merge. Trước vòng review độc lập, trạng thái là **FIXED — XONG-CHƯA REVIEW**.

## Kết quả review độc lập vòng 3 — 2026-11-03

- **Verdict: ACCEPTED.** Phiên Codex độc lập `01a1a205-1441-73e0-9170-6fdc4d591472` (`gpt-6-luna`, effort `max`) xác minh đủ 12 hash ghim và review bytes local tại thời điểm kiểm tra. Không còn finding cần sửa trong phạm vi roadmap sáu mốc.
- Reviewer xác nhận các sửa đổi Rev50/Rev50A đã đóng N1–N7 cùng các điểm về M2/M6 subphase, cổng script approval, ưu tiên FEAT-064, decision IDs, B0 provenance, DTR line ending và giới hạn quan sát cloud/local.
- Các lựa chọn còn chờ owner — SRS sign-off, thứ tự Parent/Teacher, lịch và lựa chọn model cho line-sketch, phạm vi lesson, cùng xác nhận/addendum cho B0 — là quyết định owner còn mở, không phải lỗi roadmap.
- Roadmap vẫn **DRAFT**, SRS v2.3 vẫn unsigned; review này không phê duyệt M2–M6 hoặc thay thế SRS sign-off. Reviewer chỉ đọc; không chạy test/validator, truy cập DB, gọi Modal/provider/network, hay thay đổi Git.

## Owner chấp nhận baseline lập kế hoạch sau review — 2026-11-03

- Sau verdict, owner chốt dùng SRS v2.3-draft hiện có làm baseline lập kế hoạch M2–M6, giữ nguyên SRS và theo thứ tự Parent trước Teacher tại §8.1. Mỗi mốc vẫn cần plan, acceptance criteria, ranh giới dữ liệu/migration và approval triển khai riêng.
- Roadmap được cập nhật trạng thái từ DRAFT sang **OWNER-ACCEPTED FOR PLANNING** để ghi quyết định này. Hash reviewer đã chấp nhận tại thời điểm review là `DED4B89D6A3F66FD0570EEA11E2240840C47DE607667544708C7C394F7F49C86`; bytes hiện tại sau owner update là `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA`. Nội dung review không được tuyên bố là đã re-review độc lập sau cập nhật trạng thái của owner.
- SRS vẫn unsigned và không bị sửa; không có M2–M6 implementation approval. Các gate model/version, lịch Parent line-sketch, optional lesson access, B0 provenance và các quyết định liên quan vẫn mở.

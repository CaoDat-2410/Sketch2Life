# P2-T2 ASR plan — logic/constraint disambiguation review

- Evidence ID: EV-003-T2-PLAN-04
- Date: 2026-08-30
- Reviewer: Claude (document-only pass requested by the project owner, prior to Phase A approval request)
- Scope: document review and plan rewrite only. No code, dependency, model weight, GPU/provider access, or real child data was used.
- Input: `evidence/notes/P2_T2_CLAUDE_REVIEW_FINDINGS.md` (`EV-003-T2-PLAN-03`, resolved) plus a further owner-directed pass to remove remaining logic/constraint ambiguity before requesting Phase A approval.
- Updated plan: `../../plan/P2_T2_ASR_RESEARCH_PLAN.md`

## Mục tiêu

Loại bỏ mơ hồ còn lại trong contract/logic của P2-T2 trước khi xin approval Phase A: phân biệt rõ transcript rỗng (thành công vs lỗi), retry vs repair, source vs working copy, profile/language policy, và cấu trúc schema success/failure — đồng thời giữ đúng Sprint-1 allocation (`docs/adr/ADR-0006-parallel-sprint-allocation.md`, `features/FEAT-001-stack-and-team-plan/SPRINT_1_TASK_ALLOCATION.md`).

## Bảng: mơ hồ cũ → convention mới → test/evidence kiểm chứng

| # | Mơ hồ cũ | Convention mới | Vị trí trong plan | Test/evidence kiểm chứng (Phase A, R2) |
|---|---|---|---|---|
| 1 | Không rõ transcript rỗng là do model chạy thành công (im lặng) hay do lỗi provider/mapping. | `status=SUCCEEDED` + `speech_diagnostic=NO_SPEECH_SUSPECTED`/`INDETERMINATE` cho Case A (model chạy được, output ánh xạ được, chỉ là ít/không có giọng nói); `status=FAILED` + `error_code` cho Case B (provider lỗi/output không map được). Không có outcome thứ ba mơ hồ. | "Result boundary: `AsrResultV1` is a discriminated union" + "Empty-transcript determinism: Case A vs. Case B" | R2 fixtures: silence-only → `SUCCEEDED`/`NO_SPEECH_SUSPECTED`/segments rỗng; unmappable output → `FAILED`/`ASR_SCHEMA_INVALID` sau 1 repair; acceptance rule cấm Case B xuất hiện như `SUCCEEDED` và cấm Case A xuất hiện như `FAILED`/recapture. |
| 2 | "Tối đa 1 retry" không phân biệt retry inference với repair mapping cục bộ; không rõ error code nào được retry; wording gọi `attempt_number` là "model-invocation attempt", mâu thuẫn vì Phase A không có model thật. | Bảng retry/repair matrix cố định: `INPUT_NOT_VALIDATED`/`ASR_MODEL_UNAVAILABLE` không retry; `ASR_TIMEOUT` mặc định không retry (chỉ retry theo policy idempotent đã khai báo trong config hash); `ASR_PROVIDER_FAILURE` retry tối đa 1 lần chỉ khi transient; `ASR_SCHEMA_INVALID` không gọi lại inference boundary, chỉ 1 local repair. `attempt_number` giờ định nghĩa là "adapter inference attempt" (phase-agnostic) — Phase A: fake adapter mô phỏng attempt, không model invocation thật (`INPUT_NOT_VALIDATED`=0, fake outcome bình thường=1, fake retry=2); Phase B mới là provider/model invocation thật. `repair_attempted` (local repair) tách biệt trong result. | "Retry and repair matrix" + "Phase A vs. Phase B meaning of an attempt" | R2 fixtures cho từng dòng bảng: transient provider failure (1 retry rồi thành công / rồi vẫn fail), non-transient (không retry), schema-invalid (1 repair rồi vẫn fail), timeout mặc định không retry và biến thể idempotent-policy. Acceptance rule: `attempt_number`/`repair_attempted` khớp đúng bảng cho mọi fixture fake (không model thật), không vượt max. |
| 3 | `source_audio_ref`+SHA-256 required trong request/result, nhưng câu "Phase A never populates either field" đọc được như thể áp dụng luôn cho `source_audio_ref`, mâu thuẫn với required. | `source_audio_ref`+hash **luôn bắt buộc và luôn được populate ở mọi phase, kể cả Phase A** (từ synthetic audio fixture đã có P2-T1 `PASS`), luôn là bản gốc immutable. Chỉ `processing_audio_ref`/`derivation_provenance` là optional và luôn `null`/absent ở Phase A (không có working copy). | Request boundary | R2 fixture: source ref/hash được preserve y hệt qua mọi outcome (success lẫn failure); request có `processing_audio_ref` mà thiếu `derivation_provenance` bị reject; không fixture nào set `processing_audio_ref` ở Phase A. |
| 4 | `requested_profile_id` là string tự do; câu "Phase A chỉ có fake entries" mâu thuẫn với câu "Whisper candidate entries đã tồn tại trong catalog, đánh dấu NOT_APPROVED". | `requested_profile_id` tham chiếu `AsrProfileCatalogV1` đóng, versioned. **Phase A chỉ định nghĩa schema + các entry fake, deterministic** (mặc định `FAKE_DETERMINISTIC_V1`, cộng một entry fake phụ để test riêng nhánh idempotent-timeout) — không entry nào gọi model/cần dependency/Whisper runtime. **Phase A không thêm bất kỳ Whisper candidate entry nào vào catalog, kể cả dạng placeholder** — Whisper entries (ban đầu `NOT_APPROVED`) chỉ được Phase B approval tạo ra. | "Profile catalog and language policy" | R2 test: request với profile ID ngoài catalog (kể cả tên Whisper profile) bị reject deterministic; fake adapter chỉ chấp nhận các entry fake đã khai báo trong Phase A. |
| 5 | Chưa rõ điều gì xảy ra khi `requested_profile_id` không tồn tại trong `AsrProfileCatalogV1`: có nguy cơ thiếu hẳn error outcome, hoặc bị lẫn vào `AsrFailureV1`/`INPUT_NOT_VALIDATED`. | Chốt: `AsrRequestV1` chỉ được tạo sau khi `requested_profile_id` validate xong với catalog. Profile ID ngoài catalog là **request/schema-boundary validation error**, xảy ra trước khi `AsrPort` được gọi — không phải 1 trong 5 `AsrFailureV1` error code, và không phải `INPUT_NOT_VALIDATED` (code đó giả định request đã structurally valid, chỉ thiếu P2-T1 PASS). `profile_id` trong mọi result luôn đã resolved, không mơ hồ. | "Invalid `requested_profile_id` convention" (Request boundary) | R2 test: request với profile ID ngoài catalog bị reject deterministic tại construction, trước khi `AsrPort` nhận request; acceptance rule mới xác nhận `profile_id` trong mọi result luôn valid/resolved. |
| 6 | `language_hint` chưa tồn tại; nguy cơ dùng hint để "ăn gian" language-accuracy metric khi benchmark. | `language_hint` optional, có `source` + `is_ground_truth=false`; được echo lại (`language_hint_echo`), không tự động override `detected_language`. R1/R3 tách biệt metric "auto-detect" và "honor-hint", không được gộp. | "Profile catalog and language policy", R1, R3 | R2 fixture: hint được echo đúng, không override `detected_language` khi model tự detect ra kết quả khác. (Metric tách biệt là rule cho R1/R3 — Phase B, ghi nhận ở đây để test khi Phase B chạy.) |
| 7 | `AsrResultV1` là schema phẳng với field optional mơ hồ (không rõ field nào chỉ có ở success/failure). | `AsrResultV1 = AsrSuccessV1 \| AsrFailureV1`, discriminated theo `status`. Envelope chung (`contract_version`, `correlation_id`, `executed_at`, `source_audio_ref`+hash, `profile_id`, `attempt_number`, `repair_attempted`) tách khỏi field chỉ-success (`transcript_raw`, `speech_diagnostic`, segments, language, VAD, model provenance, `quality_metadata`) và field chỉ-failure (`error_code`, `retryable`, `error_detail`). | "Result boundary: `AsrResultV1` is a discriminated union" | R2 acceptance rule: `AsrFailureV1` không bao giờ mang `transcript_raw`/field chỉ-success; schema round-trip test cho cả hai nhánh riêng. |
| 8 | Ranh giới P2-T2 vs P2-T5 (ai sở hữu benchmark ~20 fixture) và nguy cơ dùng task ID không có trong allocation. | Xác nhận theo `SPRINT_1_TASK_ALLOCATION.md`: P2-T2 sở hữu contract + fake + Whisper adapter thật; P2-T5 sở hữu CLI và báo cáo end-to-end ~20 fixture (WER/CER, entity/action F1, conflict metrics). R3 của P2-T2 chỉ là benchmark hẹp phục vụ chọn profile ASR, không thay thế/trùng lặp P2-T5. Không dùng tên task nào ngoài `P2-T1`..`P2-T5`. | "In scope and explicit non-goals", "Phase A vs. Phase B scope", R3, R5 | Không có test code (đây là ranh giới tài liệu); kiểm chứng bằng việc plan không định nghĩa CLI/report engine nào, chỉ định nghĩa benchmark measurement cho ASR. |

## Tự kiểm tra mâu thuẫn (theo yêu cầu)

- **P2-T1 PASS/RECAPTURE vs T2 no-speech:** không mâu thuẫn — mục "Boundary with P2-T1" (giữ từ revision trước) + `speech_diagnostic` mới đều nói rõ diagnostics không override P2-T1, và Case A không tự thành recapture.
- **`SUCCEEDED` transcript rỗng vs `FAILED` output lỗi:** không mâu thuẫn — được phân tách bằng discriminated union + rule Case A/Case B tường minh, không còn trường hợp thứ ba.
- **Retry/repair/error code:** không mâu thuẫn — bảng retry/repair matrix duy nhất, mọi error code có đúng một hàng, `attempt_number`/`repair_attempted` không chồng lấn ý nghĩa.
- **Original source vs processing working copy:** không mâu thuẫn — `source_audio_ref` không đổi nghĩa; `processing_audio_ref` là field mới, optional, Phase A luôn null, có ràng buộc `derivation_provenance` khi dùng sau này.
- **Profile/language hint vs benchmark fairness:** không mâu thuẫn — catalog đóng ngăn free-form profile; hint có provenance và benchmark tách auto-detect/honor-hint tường minh.
- **P2-T2/P2-T5/Integration Sprint ownership:** không mâu thuẫn — xác nhận lại theo `SPRINT_1_TASK_ALLOCATION.md`; không có coupling session/UI/orchestration mới nào được thêm vào P2-T2.

Không phát hiện mâu thuẫn logic mới sau khi rewrite. Không có finding ở mức BLOCKER/HIGH còn tồn đọng.

## Addendum (2026-08-30): wording-consistency pass

Sau khi note này đã kết luận `READY_FOR_APPROVAL` lần đầu, một review tiếp theo của owner phát hiện 2 câu chữ trong `plan/P2_T2_ASR_RESEARCH_PLAN.md` (mục Request boundary và Profile catalog) đọc được như mâu thuẫn dù ý định ban đầu đã đúng (xem finding #3, #4 đã cập nhật ở bảng trên). Đã sửa cả hai:

1. Request boundary: tách rõ hai câu — `source_audio_ref`/hash luôn required/luôn populated (mọi phase); `processing_audio_ref`/`derivation_provenance` mới là phần luôn `null` ở Phase A. Không còn câu nào đọc được là "Phase A không populate source_audio_ref".
2. Profile catalog: xoá câu ngụ ý Whisper candidate entries đã tồn tại trong catalog ở Phase A; thay bằng câu tường minh "Phase A không thêm bất kỳ Whisper candidate entry nào, kể cả placeholder".

Đã đồng bộ wording tương ứng trong `plan/PLAN.md` (không đổi, đã đúng từ trước), `DECISIONS.md` (sửa 1 bullet), `CONTEXT.md` (thêm 1 bullet), và bảng ở trên. Không có thay đổi convention mới — chỉ là làm rõ chữ nghĩa của convention đã chốt ở lần review trước.

## Addendum 2 (2026-08-30): 3 lỗi logic còn lại

Một review tiếp theo của owner phát hiện 3 vấn đề còn sót lại sau Addendum 1, trước khi có thể xin approval Phase A:

1. **Exit criteria wording về `source_audio_ref`:** dòng exit-criteria "Phase A always leaves both `null`/absent" dùng từ "both" mơ hồ (có thể đọc nhầm là gồm cả `source_audio_ref`). Đã viết lại thành 2 câu tách bạch: `source_audio_ref`+hash không bao giờ `null`, kể cả Phase A; chỉ `processing_audio_ref`/`derivation_provenance` mới luôn `null` ở Phase A.
2. **`attempt_number` gọi là "model-invocation attempt":** mâu thuẫn vì Phase A không có model thật. Đã đổi thành "adapter inference attempt" (phase-agnostic), thêm mục mới "Phase A vs. Phase B meaning of an attempt" định nghĩa cụ thể: Phase A = fake adapter mô phỏng (`INPUT_NOT_VALIDATED`=0, fake outcome bình thường=1, fake retry=2), Phase B = model/provider invocation thật. Đồng bộ trong retry matrix, result schema, R2 test description, và `DECISIONS.md`.
3. **Profile ID ngoài catalog thiếu convention:** trước đây plan không nói rõ chuyện gì xảy ra khi `requested_profile_id` không có trong `AsrProfileCatalogV1`. Đã thêm convention mới: đây là request/schema-boundary validation error tại construction (trước khi gọi `AsrPort`), không phải `AsrFailureV1`, không phải `INPUT_NOT_VALIDATED`. Thêm R2 test + acceptance rule tương ứng, và một dòng quyết định mới trong `DECISIONS.md`.

Đã đồng bộ trong `plan/P2_T2_ASR_RESEARCH_PLAN.md` (nhiều mục), `DECISIONS.md` (2 bullet sửa/thêm), `CONTEXT.md` (thêm 1 bullet), `evidence/README.md`, và bảng ở trên (row #2 sửa, row #5 mới — các row sau đó đánh số lại). `plan/PLAN.md` không cần sửa (đã đúng từ trước, không có wording tương tự).

## Trạng thái approval

- Đây vẫn chỉ là thay đổi tài liệu/plan. `approvals/TASK_APPROVAL.md` không bị chỉnh sửa trong lần review này.
- Phase A (contract discriminated union, `AsrProfileCatalogV1` schema + fake entries only — không Whisper placeholder, `AsrPort`, fixture fake adapter, R2 contract test suite) là scope đủ điều kiện để xin approval implementation, theo review này.
- Phase B (Whisper adapter thật, R1 profile comparison, R3 live ASR-only benchmark, R4 live execution, R5 recommendation) và P2-T5 (CLI + end-to-end ~20-fixture report) vẫn ngoài phạm vi approval hiện tại và cần xin duyệt riêng.

## Kết luận

`READY_FOR_APPROVAL` — cho scope Phase A như định nghĩa ở trên. Xem `plan/P2_T2_ASR_RESEARCH_PLAN.md` mục "Phase A vs. Phase B scope" cho định nghĩa chính xác.

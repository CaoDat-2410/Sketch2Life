# P2-T2 ASR research plan — independent review findings

- Evidence ID: EV-003-T2-PLAN-03
- Date: 2026-08-30
- Reviewer: Claude (independent double-check requested by the project owner)
- Reviewed brief: `P2_T2_CLAUDE_REVIEW_BRIEF.md`
- Reviewed plan: `../../plan/P2_T2_ASR_RESEARCH_PLAN.md` (and `plan/PLAN.md`, `CONTEXT.md`, `DECISIONS.md`, P2-T1 evidence for consistency)
- Scope: document review only. No code, model, dependency, or live inference was run.

## Findings

| Mức độ | Vị trí | Vấn đề/rủi ro | Đề xuất thay đổi cụ thể | Lý do |
|---|---|---|---|---|
| HIGH | `AsrResultV1` diagnostics (`no_speech_prob`) vs P2-T1 `RECAPTURE` (Q3) | Chưa có quy tắc tường minh ngăn T2's `no_speech_prob` mâu thuẫn với T1's `AUDIO_NO_SPEECH_SIGNAL` proxy trên cùng audio đã `PASS`. | Ghi rõ trong contract: segment diagnostics chỉ là ASR model diagnostic, không bao giờ kích hoạt recapture hay override quyết định `PASS` của T1. Nếu no-speech trung bình cao trên audio đã PASS, đó là tín hiệu uncertainty phải đẩy sang P2-T4 làm conflict object, không phải quyết định ở T2. | DECISIONS.md: "Conflicts and uncertainty are preserved, not silently overwritten" — hiện chưa có cơ chế thực thi nguyên tắc này giữa T1/T2. |
| HIGH | Fixture dataset / WER-CER (R3, Q6) | Fixture chỉ yêu cầu "synthetic/licensed" nhưng sản phẩm nhắm narration trẻ em; plan không nêu slice code-switching, giọng vùng miền, và không ghi nhận rằng giọng TTS/synthetic không đại diện đặc điểm âm học giọng trẻ em. | Bổ sung slice cụ thể (code-switching, silence-only, giọng vùng miền nếu khả thi) và thêm dòng "known limitation" tường minh: benchmark chỉ đo trên giọng synthetic, chưa có bằng chứng về giọng trẻ em thật; nêu điều kiện approval riêng cần trước khi dùng cho audio trẻ em thật. | Thiếu representativeness dễ gây overconfidence khi duyệt model cho use case chưa từng đo. |
| MEDIUM-HIGH | `AsrResultV1` — duration sau VAD (Q4) | Field bắt buộc nhưng không rõ giá trị khi VAD tắt (bằng duration gốc? null? 0?); không có field `vad_enabled` tường minh. | Thêm boolean `vad_enabled`; cho `duration_after_vad` nullable (null khi VAD tắt) để phân biệt "VAD chạy và không cắt gì" khỏi "VAD không chạy". | Cần cho benchmark R3 so sánh VAD on/off không nhầm lẫn, khớp quy tắc `NOT_MEASURED` ≠ `0`. |
| MEDIUM | Retry/error catalog (R4, Q5) | "Tối đa 1 retry" nhưng không có field ghi số lần retry đã dùng; ranh giới `ASR_TIMEOUT`/`ASR_MODEL_UNAVAILABLE`/`ASR_PROVIDER_FAILURE` chưa có bảng map exception → code. | Thêm `retry_count`/`attempt_number` vào result để audit; viết bảng mapping loại lỗi provider cụ thể → error code trước khi implement; ghi rõ retry được enforce bên trong adapter, không phải ở caller. | Cần để test/verify invariant "chỉ 1 retry", tránh double-retry nếu Integration Sprint tự thêm retry riêng. |
| MEDIUM | `INPUT_NOT_VALIDATED` convention (Q2) | Câu hỏi mở: là `AsrResultV1` failure hay request-validation error riêng? | Giữ trong `AsrResultV1` (nhất quán với pattern PASS/RECAPTURE không-exception của T1, giữ `AsrPort` có một kiểu trả về duy nhất) — nhưng ghi rõ đây là lớp bảo vệ phòng thủ thứ hai; orchestrator gọi `AsrPort` chịu trách nhiệm gate bằng T1 PASS trước. | Không ghi rõ dễ tạo hiểu nhầm T2 tự chịu trách nhiệm kiểm tra T1, gây coupling ẩn (liên quan Q9). |
| MEDIUM | Experiment design, 5 biến số trên ~20 fixture (Q7) | Ma trận tổ hợp lớn so với tập held-out nhỏ; chưa có acceptance threshold/decision rubric ngoài "reproducible + reviewer decision". | Cố định baseline cho phần lớn biến, sweep từng biến một (one-variable-at-a-time) trong vòng đầu; ghi rõ R5 dùng so sánh tương đối (Pareto), không có ngưỡng tuyệt đối. | 20 fixture là nhỏ; so sánh 5 biến độc lập cùng lúc dễ confounding/kết luận giả. |
| LOW-MEDIUM | `quality_metadata` shape (Q1) | Mô tả như một "bag" đo lường được, không có danh sách field đóng — khác cách P2-T3 xử lý ("reject/mask unsupported fields"). | Định nghĩa `quality_metadata` như schema đóng, liệt kê field cho phép (`retry_count`, `cold_start_flag`, `vad_enabled`, link id/hash tới `MediaValidationResultV1`...) thay vì free-form dict. | Tránh field trôi dạt hoặc vô tình lọt field nhạy cảm/prohibited qua field tự do. |
| LOW-MEDIUM | Ownership chọn profile runtime (Q9) | `requested profile ID` tồn tại nhưng chưa rõ ai quyết định profile mặc định khi chạy thật — rủi ro Integration Sprint tự hardcode khác khuyến nghị R5. | Ghi rõ: T2 sở hữu định nghĩa candidate profile + khuyến nghị R5; chọn default profile cho runtime là một ADR riêng tham chiếu khuyến nghị đó. | Tránh khác biệt ẩn giữa cái đã benchmark và cái thực sự chạy. |
| LOW | Result-level traceability | `AsrResultV1` không echo `correlation_id` của request, không có `executed_at`. | Echo `correlation_id` vào result; thêm `executed_at` (có thể trong `quality_metadata`). | Cần cho "Evidence có trace" khi audit nhiều lần chạy trên cùng input. |
| LOW | Evidence-storage policy cho transcript thật (Q8) | Privacy/logging đã khá đầy đủ, nhưng plan T2 không tự nhắc lại rằng transcript/audio thật (nếu có sau này) không được vào `evidence/`. | Thêm dòng tường minh trong T2 plan, mirror tuyên bố đã có ở P2-T1 evidence. | Rõ ràng hơn tại điểm dễ vi phạm nhất — nơi evidence thật sự được ghi ra đĩa. |
| LOW | ADR trước khi freeze (Q10) | Plan chưa liệt kê nội dung ADR bắt buộc trước khi đóng băng model/runtime. | Thêm ADR tối thiểu gồm: model revision + provenance, language-detect default, VAD default + tham số, timestamp granularity default, compute/precision + timeout, Vietnamese normalizer/tokenizer version, và giới hạn "chỉ bằng chứng synthetic, chưa có giọng trẻ em thật". | Khớp exit criteria hiện có nhưng chưa nêu rõ nội dung ADR. |

Không có finding ở mức `BLOCKER`. Các nguyên tắc cốt lõi (immutable source, không canonical meaning trước Gate A, không real child data, không psychological inference) đều được giữ vững trong plan hiện tại.

## Kết luận

`CHANGES_REQUIRED`

Thay đổi tối thiểu trước khi xin approval implementation:

1. Quy tắc tường minh: ASR no-speech diagnostics không override T1 PASS/RECAPTURE.
2. Nêu rõ giới hạn "chỉ synthetic, chưa có giọng trẻ em thật" + slice code-switching/silence trong fixture design.
3. `vad_enabled` boolean + `duration_after_vad` nullable.
4. `retry_count` field + bảng mapping lỗi provider → error code.
5. Ghi rõ convention cho `INPUT_NOT_VALIDATED` (giữ trong `AsrResultV1`, vai trò phòng thủ thứ hai).

Các mục còn lại (quality_metadata schema đóng, ownership chọn profile, traceability field, evidence-storage note, nội dung ADR) là cải thiện được khuyến nghị nhưng không bắt buộc để chặn approval.

## Resolution (2026-08-30)

5 finding bắt buộc đã được fold vào `plan/P2_T2_ASR_RESEARCH_PLAN.md` (và phản ánh tóm tắt ở `plan/PLAN.md`, `DECISIONS.md`, `CONTEXT.md`):

1. Boundary P2-T1 ↔ P2-T2 (no_speech_prob/diagnostics không override PASS/RECAPTURE) — mục "Boundary with P2-T1" trong contract section.
2. Fixture representativeness (code-switching, silence-only, noise variation, giới hạn synthetic-only/không có bằng chứng giọng trẻ em thật) — R3.
3. VAD contract (`vad_enabled`, `duration_after_vad` nullable) — Result boundary.
4. Retry/error mapping (`retry_count`, bảng mapping lỗi provider → error code, retry enforced trong adapter) — Result boundary + R4.
5. `INPUT_NOT_VALIDATED` convention (typed failure trong `AsrResultV1`, defensive second check, không coupling Integration Sprint) — Request boundary.

Các cải thiện khuyến nghị (quality_metadata closed schema, correlation_id/executed_at echo, profile-selection ownership, evidence-storage note, ADR content list) cũng đã được đưa vào cùng revision.

Trạng thái sau khi fold (tại thời điểm review): các finding bắt buộc đã được xử lý ở mức tài liệu/plan. P2-T2 khi đó **vẫn `CHANGES_REQUIRED`/chưa `READY_FOR_APPROVAL`** cho implementation, vì đây là thay đổi plan chưa được review lại bởi approver và implementation vẫn ngoài phạm vi approval hiện tại (chỉ P2-T1 được duyệt).

Trạng thái hiện tại: Phase A và Phase B đã được project owner phê duyệt trong
`approvals/TASK_APPROVAL.md`. Phase B approval đã bao gồm controlled live Round-1; readiness
execution vẫn chờ duy nhất quyết định source synthetic/TTS hoặc licensed và payload/reference
hashes compliant.

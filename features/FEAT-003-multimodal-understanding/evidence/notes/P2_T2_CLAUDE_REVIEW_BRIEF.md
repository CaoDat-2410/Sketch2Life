# Brief để Claude double-check — P2-T2 ASR

## Yêu cầu review

Hãy review độc lập plan P2-T2 dưới đây. Mục tiêu là tìm thiếu sót về kiến trúc, contract, benchmark, privacy, failure handling và ranh giới Sprint 1 **trước khi** xin duyệt implementation. Đây là tài liệu plan; không phải yêu cầu viết code, cài model, tải weights, gọi API hay dùng audio thật.

Plan gốc: `../../plan/P2_T2_ASR_RESEARCH_PLAN.md`
Nguồn nghiên cứu: `P2_T2_ASR_RESEARCH_SOURCES.md`

## Bối cảnh dự án tối thiểu

Sketch2Life nhận bắt buộc một ảnh vẽ và narration. Luồng P2 hiện tại là:

```text
drawing.png + narration.wav
  -> P2-T1: MediaValidationResultV1 (PASS | RECAPTURE)
  -> P2-T2: AsrResultV1
  -> P2-T3: VisionUnderstandingResultV1
  -> P2-T4: RawUnderstandingResultV1 (giữ conflict/uncertainty)
  -> Integration Sprint: Gate A xác nhận với người dùng
```

P2-T1 đã hoàn thành trên nhánh base. P2-T2 là nhánh `plan/person-2-asr-research`, base từ P2-T1. Tại thời điểm brief này, P2-T2 **chưa được duyệt implementation**. Chỉ P2-T1 được phê duyệt; do đó review không được xem là ủy quyền cho live model/provider, GPU, dependency, API integration, hay real child data. Trạng thái hiện tại của approval được ghi tại `approvals/TASK_APPROVAL.md`; Phase B approval đã bao gồm controlled live Round-1, còn fixture-source selection và payload/reference hashes vẫn là `DECISION_REQUIRED`.

## Mục tiêu P2-T2

Đánh giá candidate baseline Whisper `large-v3-turbo` qua `faster-whisper`, sau đó (nếu có evidence và approval) cung cấp adapter ASR độc lập, provider-neutral. Output phục vụ fusion ở P2-T4; không được trở thành “sự thật” về bức vẽ, canonical meaning hay quyết định Gate A.

T2 phải preserve transcript/language/timestamps/diagnostics/provenance của audio gốc, đồng thời không để provider SDK object hoặc raw provider response đi ra ngoài infrastructure.

## Ranh giới bắt buộc

### In scope

- Thiết kế contract versioned cho request/result/error.
- Fixture fake adapter để test schema không cần model.
- Thiết kế benchmark và metric trên khoảng 20 fixture synthetic/licensed.
- Tích hợp và benchmark adapter thật chỉ sau khi có approval riêng.
- Evidence có trace: manifest hash, model/config hash, command/environment, result và interpretation.

### Ngoài scope

- Capture UI, API route, queue, database/object storage, mobile app, Gate A UI, session/job state.
- Tự recapture hoặc tự fallback sang ảnh/modality khác. P2-T1 là nơi quyết định media có dùng được hay không.
- Translation, diarization, speaker/age/emotion/personality/psychological inference.
- Raw audio, transcript, credentials, endpoint hoặc raw provider payload trong ordinary logs.
- Real child data.

## Contract đề xuất để review

### `AsrRequestV1`

Chỉ nhận:

- `source_audio_ref` và SHA-256 immutable;
- link/provenance tới `MediaValidationResultV1` có `decision=PASS`;
- correlation ID và requested profile ID không chứa audio/text.

Nếu không có P2-T1 PASS thì trả typed failure `INPUT_NOT_VALIDATED`. Adapter không được overwrite, normalize âm thầm hoặc thay thế source audio. Nếu cần working copy sau này phải có reference/derivation provenance riêng.

### `AsrResultV1`

Success cần có:

- `status=SUCCEEDED`, `contract_version`;
- `source_audio_ref` và hash y hệt request;
- `transcript_raw` (chỉ là ASR proposal);
- detected language và language probability, được nhãn là diagnostic chứ không phải truth;
- segment có index, `start/end`, text, optional `avg_logprob`, `compression_ratio`, `no_speech_prob`, optional word timings/probabilities;
- input duration, duration after VAD, profile ID, model/revision, adapter/library/runtime version và normalized config hash;
- `quality_metadata` đo được và link tới validation provenance.

Failure cần schema-valid và một trong các error code:

- `INPUT_NOT_VALIDATED`
- `ASR_TIMEOUT`
- `ASR_MODEL_UNAVAILABLE`
- `ASR_PROVIDER_FAILURE`
- `ASR_SCHEMA_INVALID`

Raw provider response/SDK objects không được trở thành public contract.

## Candidate configuration cần benchmark, chưa được chốt

| Biến số | So sánh có kiểm soát | Bằng chứng cần có |
|---|---|---|
| Language | Auto-detect vs fixture language declared | Language accuracy, Vietnamese/non-Vietnamese WER/CER |
| Decode | Các beam-size/documented decoding profile | Quality-latency trade-off với fixture split giống nhau |
| VAD | Off vs on, parameters ghi tường minh | Missing/omitted speech, segmentation, duration-after-VAD, WER/CER, latency |
| Timestamp | Segment-only vs word timestamps | Schema validity, timing completeness, latency, alignment failures |
| Runtime | CPU/GPU precision profile hỗ trợ | p50/p95, cold start, memory/runtime availability, same-quality comparison |

Không được so sánh benchmark giữa các profile có setting khác mà không ghi rõ; cold-start phải tách khỏi latency xử lý từng audio.

## Dataset và metric yêu cầu

Fixture set khoảng 20 audio synthetic/licensed. Mỗi fixture có ID, audio hash, declared language, human reference transcript, expected speech presence, noise/recording condition, duration band, split membership. Development và held-out không được lẫn.

Metric:

- schema-valid rate và typed failure count theo error code;
- WER/CER với Vietnamese text normalizer/tokenizer có version;
- language accuracy và calibration slices;
- timestamp ordering/completeness;
- p50/p95 theo stage/profile, cold start riêng;
- input duration so với duration-after-VAD và observation về omission;
- memory/runtime availability nếu môi trường được phê duyệt cung cấp.

Metric không đo được phải báo `NOT_MEASURED`, không dùng `0`.

## Failure, retry và privacy cần giữ

- Chỉ cho phép tối đa một retry cho lỗi adapter/serialization đã biết là repairable.
- Timeout, model unavailable, provider failure phải trả typed failure; không loop vô hạn và không giả success bằng transcript rỗng.
- Mapping sang UI/session state là phần Integration Sprint, không phải P2-T2.
- Observability chỉ có correlation ID, config/profile hash, duration bucket, status/error code, latency. Không ghi raw media/transcript/credential/endpoint/provider payload.

## Điều cần Claude phản biện cụ thể

1. Contract có thiếu field nào cần thiết cho P2-T4 fusion, audit/reproducibility hoặc future integration không? Field nào thừa/rủi ro privacy?
2. `INPUT_NOT_VALIDATED` có nên là `AsrResultV1` failure hay một request-validation error riêng? Hãy đề xuất một convention duy nhất.
3. Có cần tách `no_speech` thành business outcome/quality diagnostic riêng với P2-T1 `RECAPTURE` không? Tránh hai component đưa quyết định mâu thuẫn.
4. Timestamps, VAD duration và word probabilities nên optional/required thế nào để contract bền khi đổi provider?
5. Error catalog, retry limit và timeout boundary đã đủ deterministic/testable chưa?
6. Fixture design và WER/CER normalization có đủ đặc biệt cho tiếng Việt không? Thiếu slice nào (giọng nói, noise, code-switching, silence) nhưng vẫn synthetic/licensed?
7. Profile benchmark có biến số nào gây confounding hoặc còn thiếu baseline/acceptance threshold?
8. Privacy/logging/provenance đã phù hợp cho narration của trẻ và policy “source immutable” chưa?
9. Ranh giới T1/T2/T4/Integration Sprint có chỗ nào sai ownership hoặc coupling ẩn không?
10. Nên tạo ADR nào trước khi freeze model/runtime/provider và nội dung quyết định cần ghi là gì?

## Format phản hồi mong muốn

Với mỗi finding, ghi:

| Mức độ (`BLOCKER`/`HIGH`/`MEDIUM`/`LOW`) | Vị trí | Vấn đề/rủi ro | Đề xuất thay đổi cụ thể | Lý do |
|---|---|---|---|---|

Kết thúc bằng một kết luận duy nhất:

- `READY_FOR_APPROVAL`: chỉ khi plan đủ để xin approval implementation; hoặc
- `CHANGES_REQUIRED`: kèm danh sách thay đổi tối thiểu trước khi xin approval.

Không đánh giá bằng giả định rằng benchmark/live inference đã diễn ra; hiện chưa có model result để kết luận chất lượng.

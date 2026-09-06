# P2-T2 Phase B — approval-request package (historical dossier; approval recorded)

- Evidence ID: EV-003-T2-PLAN-05
- Date: 2026-08-30
- Tác giả: Claude (document-only review/drafting, theo yêu cầu project owner)
- Scope: tài liệu/approval-dossier only. Không code, không cài `faster-whisper`/CTranslate2, không tải model weights, không gọi GPU/cloud, không real child data.
- Input: `plan/P2_T2_ASR_RESEARCH_PLAN.md` (mục "Phase B approval request"), `evidence/notes/P2_T2_LOGIC_CONSTRAINT_REVIEW.md`, và 3 review pass hội thoại không tạo file riêng — (1) phản biện plan triển khai Phase B ban đầu, (2) final consistency check đối chiếu trực tiếp với code Phase A đã implement (`backend/src/sketch2life/contracts/schemas/asr.py`, `infrastructure/config/settings.py`, `infrastructure/ai/fake_asr.py`, `backend/tests/unit/test_asr_phase_a.py`) và upstream `faster-whisper` source, (3) một rebuttal được ACCEPT làm hẹp lại correction #4 của (2).

Note này là **bản tóm tắt đã được dùng để xin duyệt**. Project owner đã duyệt Phase B vào ngày 2026-08-30; record chính thức là `approvals/TASK_APPROVAL.md`, hiện ghi P2-T1, P2-T2 Phase A và P2-T2 Phase B là approved.

## Scope được xin duyệt (Phase B)

1. **Additive contract change** trong `backend/src/sketch2life/contracts/schemas/asr.py` (không đổi giá trị/hành vi fake Phase A hiện có):
   - mở rộng `AsrProfileId` enum với Whisper candidates; the Round-1 readiness contract plans exactly Turbo INT8 auto and Turbo FP16 auto, not large-v3;
   - mở rộng `AsrProfileV1.adapter_kind` (hiện `Literal["DETERMINISTIC_FAKE"]`) và `compute_profile` (hiện `Literal["NONE"]`) để chấp nhận giá trị Whisper thật;
   - thêm field mới vào `AsrProfileV1`: `model_identifier`, `model_revision`, converted-weight provenance + license, `adapter_version`, `runtime_version` (các field khác — beam, language_mode, VAD/timestamp, timeout, retry policy — đã có sẵn từ Phase A, không đổi);
   - thay `phase_a_profile_catalog()` bằng MỘT hàm catalog tĩnh, versioned, phase-agnostic (vd `asr_profile_catalog()`) gồm cả Phase A fake entries lẫn Phase B candidates; `AsrRequestV1` validator tiếp tục resolve qua đúng một hàm này — **không** dùng per-request dynamic catalog injection vào Pydantic validation.

2. **`config_hash`**: giữ nguyên cơ chế SHA-256 trên canonical JSON (`sort_keys=True`, compact separators) đã có; input Phase B bắt buộc gồm: model ID/revision, converted-weight provenance + license, adapter/runtime version, compute, beam, language mode, VAD/timestamp config, timeout, retry policy. Không hard-code local path trong source/plan/evidence — chỉ ghi tên env var `SKETCH2LIFE_ASR_MODEL_CACHE_DIR`, không default path.

3. **Runtime config**: `FasterWhisperRuntimeConfig` định nghĩa riêng trong `infrastructure/ai`, inject vào adapter/test runner (theo đúng pattern constructor-injection `DeterministicFixtureAsrAdapter.__init__` đã dùng). Tuyệt đối không mở rộng `infrastructure/config/settings.py` (`Settings` dùng chung, có validator khoá production-Runpod); không HTTP/API/provider wiring.

4. **Round 1 benchmark**: chỉ profile `AUTO_DETECT`; the readiness contract compares exactly Turbo INT8 auto and Turbo FP16 auto, not large-v3; VAD tắt, beam=5, word timestamps tắt; báo cáo ghi VAD/beam/word-timestamp alternatives là `NOT_MEASURED`; không freeze/không chọn runtime default từ round này; kết quả chỉ là directional synthetic evidence.

5. **Forced-language (`HONOR_HINT`) convention cho vòng sau**: xác nhận qua upstream source (`SYSTRAN/faster-whisper`, `faster_whisper/transcribe.py`) — `language=None` chạy detection thật (`language_probability` đo được); `language="vi"` bỏ qua detection, `language_probability` hardcode = 1 (sentinel). Convention: `language_hint_applied=true`, `language_probability=1.0` được ghi nhận là sentinel chứ không phải confidence, profile đó bị loại khỏi language-detection accuracy/calibration metric, không được trình bày forced "vi" như auto-detected. **Không thêm validator vào `AsrSuccessV1`** — shared contract giữ provider-neutral; invariant này được enforce ở test/evidence riêng của adapter `faster-whisper`, giống cách `attempt_number`/retry correlation hiện tại được test ở `DeterministicFixtureAsrAdapter` chứ không phải một validator schema chung.

6. **GPU preflight**: phải qua đúng code path adapter thật (model load + 1 synthetic transcription), không chỉ check CLI/driver riêng lẻ; lỗi load/runtime map đúng thành `ASR_MODEL_UNAVAILABLE` (dùng `AsrErrorDetail.MODEL_LOAD_FAILED`/`DEVICE_UNAVAILABLE` đã có sẵn). `faster-whisper`/`CTranslate2` phải exact-pin trong `backend/pyproject.toml` trước khi install — ngoại lệ có chủ đích so với range-pin convention hiện tại của repo, lý do ghi trong ADR.

7. **Evidence/report**: có cả success path và mọi typed-failure path kèm `attempt_number`/`repair_attempted`; tuân thủ privacy rule R4 (không raw audio/transcript/credential/endpoint trong log hay `evidence/`); ghi weight provenance/license; ghi version Vietnamese normalizer/tokenizer dùng cho WER/CER; ghi rõ giới hạn synthetic-only (chưa validate giọng trẻ em thật); kết quả ~20 fixture gắn nhãn directional, không phải kết luận thống kê vững.

## Explicit non-goals (nhắc lại, không đổi)

- Không P2-T5 (CLI/end-to-end ~20-fixture report) — vẫn thuộc sở hữu riêng của P2-T5.
- Không cloud/provider deployment (Lightning/Runpod) — Phase B chỉ chạy local GPU dev (RTX 4060), không production endpoint.
- Không API/UI/queue/session/job orchestration — vẫn ngoài phạm vi Sprint 1 P2 workstream, thuộc Integration Sprint.
- Không real child data — chỉ synthetic/licensed fixture.
- Không runtime-default profile selection — R5 chỉ đưa recommendation table; chọn default cho runtime là quyết định Integration Sprint/ADR riêng.
- Không sửa `approvals/TASK_APPROVAL.md` bằng note này.

## Acceptance evidence kỳ vọng (khi Phase B thực sự chạy, sau khi chọn source và cung cấp payload refs/hashes)

Phase B approval already covers the controlled live Round-1 execution. The remaining gate is
the `DECISION_REQUIRED` choice of synthetic/TTS or licensed source and the supply of compliant
local payload/reference-transcript refs and hashes.

- Contract test suite cho additive change (B1) pass, không đổi hành vi Phase A fake entries hiện có.
- `config_hash` tái lập được từ đúng field list ở mục 2.
- Round 1 report: schema-valid rate, WER/CER (kèm version normalizer/tokenizer), latency p50/p95 + cold-start riêng, VAD/beam/word-timestamp ghi `NOT_MEASURED`, không blend auto-detect với honor-hint (round này không có honor-hint).
- GPU preflight log: GPU/driver, model revision, `config_hash`, peak VRAM, cold-start, inference latency; lỗi map đúng `ASR_MODEL_UNAVAILABLE` nếu preflight fail.
- ADR/`DECISIONS.md` entry mới trước khi freeze bất kỳ profile nào: model revision + weight provenance/license, language-detection policy default, VAD default, timestamp granularity default, compute/precision + timeout budget, exact-pin rationale, giới hạn synthetic-only.
- Evidence không chứa raw audio/transcript/absolute local path — chỉ hash, config, số liệu tổng hợp.

## Kết luận

Package này đã được project owner dùng để duyệt Phase B (`APPROVED`); scope thực thi chính thức là toàn bộ 7 mục trên như được ghi tại `approvals/TASK_APPROVAL.md`. Note này vẫn là evidence/approval dossier, không thay thế approval record.

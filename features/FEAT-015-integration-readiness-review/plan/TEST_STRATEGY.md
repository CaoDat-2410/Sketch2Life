# Chiến lược test luồng tích hợp

- Status: PROPOSED; chưa viết test mới hoặc code runtime trong review này.
- Revision: 1, 2026-09-05.
- Tất cả fixture synthetic, manifest có version/hash, expected output được review trước khi đo.
- Mỗi run ghi commit cả bốn stream, schema/config versions, OS/runtime/device, command, inputs/hashes, outputs, timestamp, reviewer, skip/failure reason và interpretation trong evidence của feature sở hữu hành vi. Bộ orchestration/E2E có feature riêng và link evidence stream, không dump chung.

## Tầng test và điều kiện qua gate

| Tầng | Cách test | Điều kiện đạt |
|---|---|---|
| 0. Regression từng stream | P1 validators; P2 pytest/Ruff; P3 typecheck/Vitest/build; P4 pytest + FFmpeg integration | Không còn failure không giải thích; skip rõ điều kiện, không đánh dấu pass |
| 1. Contract producer/consumer | Cùng fixture qua Python schema và TypeScript/bridge validator; identity mapping round-trip | ID/version/provenance được giữ, unknown/stale schema bị reject hoặc adapter rõ ràng |
| 2. Offline vertical slice | In-memory application ports + fake providers + command Gate A/B + composer | Truy vết từ source tới handoff/feedback; không gọi mạng/GPU |
| 3. HTTP/job/storage integration | Test adapters local và worker completion; simulated delays/retries/restart | Idempotency, stale-version rejection, authorization, immutable outputs, cleanup đúng |
| 4. Android/browser | WebView bridge, lifecycle, playback, fallback; screenshot/video và frame timing | Đúng visual/preservation, không event cũ chuyển state, không mất handoff |
| 5. Live provider benchmark | Pin model/revision/config, held-out fixtures, GPU preflight và failure injection | Quality/latency/cost theo ngưỡng review trước; ghi NOT_MEASURED khi thiếu |

Phase 1 không bị chặn bởi GPU: mock dùng kiểm tra luồng, không chứng minh chất lượng model. Render build thành công cũng không phải bằng chứng visual hoặc FPS.

## Bộ fixture tối thiểu đề xuất cho vertical slice

1. Happy path: media PASS -> ASR/vision đồng thuận -> Gate A -> P1 valid -> Gate B -> P3 reveal + P4 cache HIT -> handoff -> feedback. Assert generator không được gọi trên HIT bằng spy/counter.
2. Media corrupt/silent: RECAPTURE, không gọi ASR/vision tiếp; source hash không đổi.
3. ASR/vision disagreement: giữ hai claims/support refs; chưa Gate A thì không recommendation/generation.
4. Nhãn chưa mapping/khác ngôn ngữ: giữ raw text và provenance, không tự đoán ID hoạt động.
5. Gate A correction: version mới làm kết quả cũ stale, mọi downstream dùng meaning đã xác nhận.
6. Rule rejection: tuổi/readiness/material/prerequisite/supervision không hợp lệ -> NO_VALID_ACTIVITY; không gọi selector/generator để lách rule.
7. Gate B: sai objective/activity version hoặc chưa được duyệt -> không compile/render/generate.
8. P1/P4 ID mismatch: objective uppercase/integer-version, brief lệch ID/version, generated result lệch objective -> mapping đã review hoặc reject trước phát media.
9. Cache MISS -> mock generation PASS: identity thống nhất xuyên request/brief/artifact/experience.
10. Generator raise/timeout, sampler/model exception: typed terminal result, retry bounded, fallback chỉ dùng asset hợp lệ cùng objective; không treo phiên.
11. Unsafe media BLOCK: không phát asset bị chặn; safe fallback hoặc yêu cầu review theo policy, không tự mất activity handoff.
12. P3 extraction/asset load fail: whole-drawing/still fallback; không dùng art được AI vẽ lại.
13. Duplicate/out-of-order worker completion hoặc double-submit Gate: chỉ một transition hợp lệ; expected_session_version cũ bị reject.
14. Renderer event từ instance/plan/session cũ hoặc PLAYBACK_COMPLETED lặp: không mở handoff sai hoặc ghi feedback hai lần.
15. Hai generation jobs cùng objective, khác session/config: khác artifact identity/output, không overwrite nguyên bản hoặc kết quả nhau.
16. Một media branch fail/chậm: composer có readiness/fallback rõ, không chờ vô hạn, không phát partial unsafe media.

## Test riêng cần bổ sung theo phát hiện review

- P4: sửa test đường dẫn theo platform hoặc chạy thêm Linux target; giữ Win/Linux portability rõ ràng. Cài FFmpeg/ffprobe trong môi trường test riêng và chạy test thật đang skip. Thử video corrupt, duration sai, frame sampling lỗi, missing fallback.
- P4: unit/contract tests cho exception ở generator, sampler, validator; mismatch giữa objective/brief/output; cùng objective nhiều jobs. Real-model content inspection phải có evidence riêng vì current demos dùng mock.
- P3: protocol round-trip và schema-negative tests giữa backend/mobile/renderer; hash/content kiểm tra thật; screenshot normal/fallback, sai crop/mask, asset mất; Android app background/resume và WebView reload. Ghi startup/p50/p95, FPS/dropped frames, memory hoặc NOT_MEASURED cùng thiết bị thực.
- P2: fusion conflict fixtures và deterministic output/provenance; tách contract V1/V2; benchmark synthetic held-out không dùng kết quả mock làm quality. Review hồi quy hardening của nhánh local 1419f75 trước tích hợp.
- P1: dùng 74 Golden cases làm oracle hồi quy; unknown/cross-activity IDs, inactive/provisional handling và activity/objective version locks. Không đổi production eligibility để làm test dễ pass.

## Điều kiện nghiệm thu một integration PR

- Plan, allocation, acceptance và approval đúng scope/revision; implementation state hợp lệ theo harness.
- Tất cả regression liên quan pass, mọi skip nêu lý do và gate tương ứng chưa được claim đạt.
- Trace synthetic session chứng minh cả hai Gates, hard-rule order, immutable original, fallback và handoff/feedback.
- Unknown/stale/duplicate/mismatched inputs không thay đổi state trái phép.
- Evidence được lưu cùng feature; không raw provider errors/transcripts/secrets/real child data trong logs.
- Validate harness, architecture, team allocation và repository security theo checklist repo. Trước mọi commit/push phải chạy python tools/validate_repository_security.py.
- Visual asset được áp dụng chỉ sau approval riêng; device performance chỉ kết luận khi đã đo.

## Owner choices applied — 2026-09-05

The happy-path test uses P1 canonical IDs/versions, mandatory Gate A, explicit disagreement confirmation, additional-context retry when no activity is eligible, P3 asset manifest/hash validation, P3 DRAW_REVEAL, P4 cache HIT, and activity handoff.

Additional P3 asset tests: manifest round-trip, source hash preservation, changed bytes, invalid crop/mask provenance, loader rejection, whole-drawing fallback, and visual approval records before any app application.

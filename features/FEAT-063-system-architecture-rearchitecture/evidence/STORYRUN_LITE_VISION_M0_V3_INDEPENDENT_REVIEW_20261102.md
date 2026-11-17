<!-- Captured from Codex thread 01a19ace-ea77-7cd2-a630-ca55fdb2b5f7, turn 01a19ace-f2a1-7571-b9b1-889f76d9e77b; read-only independent review. -->

# Kết luận: **CHƯA ACCEPTED**

Hai SHA-256 trong yêu cầu đều khớp. Review này chỉ đọc; tôi không sửa file, chạy test, truy cập PostgreSQL hay gọi Modal/provider. Không có finding P0; có **5 finding P1** và **4 finding P2**.

## Findings

### P1 — Thứ tự ghi Story trước ledger không khớp A1 và có thể làm mất kết quả

M0 V3 đề xuất lưu kết quả Story rồi mới `ledger.complete` tại [M0 V3, dòng 21](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V3_DRAFT_20261102.md:21) và [V2, dòng 64](/D:/GitHub/Sketch2Life/.claude/handoff/STORYRUN_LITE_VISION_DECISIONS_V2_DRAFT_20261102.md:64).

Trong A1, `HttpJsonTransport` gọi claim và mark-sent trước POST tại [transport.py, dòng 236](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/transport.py:236) và [dòng 253](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/transport.py:253). Bridge trả outcome; sau đó `InvocationGuardedVisionObservationPort.observe()` gọi `finalize()` **trước khi trả outcome cho application/worker** tại [invocation_guard.py, dòng 204](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py:204) và [dòng 253](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py:253). Ledger chỉ lưu `result_sha256`, không lưu payload kết quả, tại [ledger.py, dòng 103](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/ledger.py:103).

**Tình huống:** provider trả kết quả hợp lệ, decorator ghi `SUCCEEDED`, rồi tiến trình chết trước khi worker ghi revision Story. Sau restart, ledger không đủ dữ liệu tái tạo chủ thể/entities để API trả lại. Kết quả có thể mất dù ledger báo thành công.

**Hướng xử lý:** muốn Story-first thì phải thay đổi rõ ranh giới finalize của A1; không thể chỉ đảo thứ tự trong worker mà vẫn giữ decorator hiện tại. Cần quy tắc đối soát khi Story đã ghi nhưng `ledger.complete` thất bại, và khi ledger terminal nhưng Story chưa có payload.

### P1 — Sweeper có thể coi nhầm `CLAIMED` là an toàn để gọi lượt mới

V2 đề xuất coi crash giữa claim và mark-sent là `NOT_SENT`, cho phép lượt mới tại [V2, dòng 68](/D:/GitHub/Sketch2Life/.claude/handoff/STORYRUN_LITE_VISION_DECISIONS_V2_DRAFT_20261102.md:68) và [dòng 71](/D:/GitHub/Sketch2Life/.claude/handoff/STORYRUN_LITE_VISION_DECISIONS_V2_DRAFT_20261102.md:71). Nhưng ledger chỉ cho `mark_sent` chuyển từ `CLAIMED` sang `SENT` theo identity của attempt; nó không kiểm tra Story revision hay worker fence tại [ledger.py, dòng 82](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/ledger.py:82).

**Tình huống:** worker còn sống nhưng bị pause sau claim; sweeper đặt Story về trạng thái cho phép thử lại, request mới tạo attempt khác, rồi worker cũ tiếp tục và gọi provider. `owner_instance_id` khác instance hiện tại cũng không chứng minh worker cũ đã chết nếu có process/replica khác.

**Tác động:** có thể gửi hai lời gọi cho cùng run, tốn GPU hoặc làm kết quả đến muộn bị vứt bỏ. Thời gian chờ không thay thế fence.

**Hướng xử lý:** không cho reanalyze chỉ vì thấy `CLAIMED` cũ hoặc khác instance. Phải có lease/fence làm `mark_sent` thất bại nếu Story attempt đã mất quyền, hoặc giới hạn và cưỡng chế cấu hình demo chỉ một process/worker. Nếu chưa chứng minh được worker đã quiesce, giữ trạng thái hold/unknown.

### P1 — Cooldown 170 giây không đủ căn cứ để gọi lại sau `UNKNOWN`

V2 nói không tự retry, nhưng vẫn cho lệnh `reanalyze` sau `sent_at + 170s` tại [V2, dòng 74](/D:/GitHub/Sketch2Life/.claude/handoff/STORYRUN_LITE_VISION_DECISIONS_V2_DRAFT_20261102.md:74). M0 V3 cũng ghi đúng rằng 170/190 giây không chứng minh GPU đã dừng tại [M0 V3, dòng 27](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V3_DRAFT_20261102.md:27).

**Tình huống:** request đã tới Modal nhưng backend mất response; sau 170 giây UI gửi lại trong khi invocation cũ vẫn chạy hoặc đã chạy xong nhưng response thất lạc.

**Tác động:** gọi trùng và có thể phát sinh chi phí trùng. A1 cũng chỉ có trạng thái/hash, không cung cấp cách tra cứu response provider đã mất.

**Hướng xử lý:** với bước Modal thật riêng, không cho phép gọi lại chỉ dựa vào cooldown. `UNKNOWN` cần dừng và yêu cầu đối soát/owner quyết định; lần gọi live đầu nên one-shot. Goal fake/loopback có thể thử lại theo hành vi xác định của stub, nhưng không dùng kết quả đó để tuyên bố live retry an toàn.

### P1 — Phương án Core Asset đề xuất không đáp ứng owner scope và lineage của Parent

D2 đề xuất dùng `CoreAssetMetadataModel`, `organization_id` và `source_refs=["story-run:<id>"]` tại [M0 V3, dòng 36](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V3_DRAFT_20261102.md:36) và [V2, dòng 44](/D:/GitHub/Sketch2Life/.claude/handoff/STORYRUN_LITE_VISION_DECISIONS_V2_DRAFT_20261102.md:44).

Register yêu cầu Parent dùng scope `PARENT_ACCOUNT`, không tạo tổ chức giả, và lineage mới đi qua `core.asset_lineage`; `source_refs` chỉ đọc cho dữ liệu legacy tại [DATA_TABLE_REGISTER, dòng 71](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:71) và [dòng 306](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:306). Model hiện tại chỉ có `organization_id`, hash, media type và `source_refs` tại [core_models.py, dòng 143](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/persistence/core_models.py:143); [LocalArtifactStore](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/storage/persistent_local_artifacts.py:13) không tự thực thi tenant scope.

**Tình huống:** dùng `org_story_lite_synth` làm scope Story/asset Parent hoặc ghi lineage mới vào `source_refs`.

**Tác động:** dữ liệu Parent bị biểu diễn thành dữ liệu tổ chức; việc gắn bản gốc với ảnh chuẩn hóa và kiểm quyền/xóa asset không theo mô hình đích.

**Hướng xử lý:** tách `organization_id` namespace cần cho A1 ledger khỏi owner scope Story. Chốt owner scope có kiểu và quan hệ asset gốc/chuẩn hóa bằng lineage; nếu cần schema tạm khác register, ghi rõ sai lệch và duyệt trước khi migration.

### P1 — Sáu route hiện là danh sách ý tưởng, chưa đủ làm contract ghép UI

D1 liệt kê sáu route và một số state, nhưng chưa định nghĩa đầy đủ DTO, status code, lỗi an toàn, hành vi polling, idempotency replay và ví dụ response tại [M0 V3, dòng 33](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V3_DRAFT_20261102.md:33). SRS hiện nêu `/assets` và `/subject-confirmation`, còn draft chọn `/drawing` và `/subject-review` tại [SRS §21.2, dòng 1571](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1571), [dòng 1572](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1572) và [dòng 1574](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1574).

Catalog Rev37 có baseline 124 operation; test catalog đang sửa trong working tree chỉ khai báo một operation pilot riêng tại [test_openapi_contract_catalog.py, dòng 31](/D:/GitHub/Sketch2Life/backend/tests/contract/test_openapi_contract_catalog.py:31) và [dòng 122](/D:/GitHub/Sketch2Life/backend/tests/contract/test_openapi_contract_catalog.py:122).

**Tình huống:** người ghép UI chỉ có tên route, không biết upload trả `202` hay chờ đồng bộ, state nào có result, xử lý `UNKNOWN` ra sao, hoặc retry cùng idempotency key trả gì.

**Tác động:** API có thể chạy nhưng chưa đáp ứng mục tiêu “đủ contract để người khác ghép UI”; test catalog cũng chưa có baseline được chốt cho sáu operation mới.

**Hướng xử lý:** đặt OpenAPI versioned cho pilot làm deliverable/acceptance gate trước khi handoff UI; chốt route names hoặc ghi deviation so với SRS. Giữ phép đếm Rev37 riêng với operation pilot, không âm thầm biến route pilot thành catalog Rev37.

### P2 — Photo binding phải tránh kéo giả checkpoint hoặc làm hỏng payload A1 cũ

`ObservationRequest.render` hiện được khai báo là `RenderBinding` tại [vision_analysis.py, dòng 168](/D:/GitHub/Sketch2Life/backend/src/sketch2life/application/ports/vision_analysis.py:168). `RenderBinding` bắt buộc checkpoint fields tại [domain/vision_analysis.py, dòng 195](/D:/GitHub/Sketch2Life/backend/src/sketch2life/domain/vision_analysis.py:195), còn `SourceSnapshot` và `verify_source()` ràng buộc ảnh render với checkpoint canvas tại [domain/vision_analysis.py, dòng 233](/D:/GitHub/Sketch2Life/backend/src/sketch2life/domain/vision_analysis.py:233) và [dòng 275](/D:/GitHub/Sketch2Life/backend/src/sketch2life/domain/vision_analysis.py:275). Codec từ chối dataclass có tập field khác tại [codec.py, dòng 110](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/codec.py:110).

P2 trong D3 — `RenderSource`/`PhotoInput` riêng — là hướng phù hợp để không bịa checkpoint. Nhưng khi làm phải giữ `RenderBinding` canvas và payload codec nguyên trạng; không đưa flow Story qua `SourceSnapshot`/`verify_source()` như thể ảnh chụp là render canvas.

### P2 — `narration_context` chưa đủ làm hợp đồng sửa chủ thể theo SRS

Adapter cũ nhận `narration_context` như một chuỗi tối đa 2.000 ký tự tại [lightning_vision_v2.py, dòng 69](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py:69), và prompt Modal chỉ coi đó là mô tả người lớn để hỗ trợ phân biệt nét vẽ, không phải bằng chứng tại [lightning_vision_v2_server.py, dòng 258](/D:/GitHub/Sketch2Life/tools/lightning_vision_v2_server.py:258). Nhưng bridge hiện tại chỉ hỗ trợ `IMAGE_ONLY` và từ chối typed context tại [legacy_v2.py, dòng 145](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py:145) và [dòng 157](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py:157). Test hiện có còn khẳng định bridge không gửi `narration_context` tại [test_vision_analysis_legacy_bridge.py, dòng 344](/D:/GitHub/Sketch2Life/backend/tests/unit/test_vision_analysis_legacy_bridge.py:344).

SRS yêu cầu sửa chủ thể tạo revision/VLM job mới trên cùng image hash tại [SRS AT-14, dòng 1100](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1100). `narration_context` hiện có thể là **hint**, nhưng chưa bảo đảm ngữ nghĩa “subject correction”, revision mới hay model đổi kết quả. Cần chọn: bỏ sửa khỏi M0/giới hạn xác nhận; ghi correction thủ công và nêu rõ lệch SRS; hoặc thêm contract/context có kiểu, bridge support, lưu revision cùng hash và kiểm chứng bằng fixture. FEAT-061 smoke dùng `Narration NONE`, nên không chứng minh việc này.

### P2 — Chính sách admission/chuẩn hóa ảnh còn hai baseline khác nhau

Admission FEAT-018 hiện giới hạn 5.000.000 byte, 4 triệu pixel, cạnh 4096, PNG/JPEG tại [image_admission.py, dòng 76](/D:/GitHub/Sketch2Life/backend/src/sketch2life/domain/understanding/image_admission.py:76). SRS §24.2 lại đề xuất cho demo 20 MiB, 40 MP và JPEG/PNG/WebP tại [SRS, dòng 1850](/D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1850).

FEAT-061 chỉ chứng minh một ảnh synthetic 1254×1254, 2.444.928 byte, `IDENTITY_V1` tại [smoke report, dòng 28](/D:/GitHub/Sketch2Life/features/FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md:28) và [admission evidence, dòng 13](/D:/GitHub/Sketch2Life/features/FEAT-061-modal-qwen-vl-endpoint/evidence/backend-demo-smoke-20261029-v1/admission.json:13). Không có bằng chứng ảnh điện thoại 12 MP được chấp nhận. D8 đã nhận ra đây là quyết định mở; trước khi đóng contract cần chốt client hay server chuẩn hóa, hash nào được receipt ràng buộc, và UI phải làm gì với `PROCESSING_FAILURE` khác `RECAPTURE`.

### P2 — `X-Actor-Ref` chỉ là stand-in, không phải authorization

D5 đề xuất kiểm cross-run bằng actor ref nhưng cũng thừa nhận header do client đặt dễ giả tại [V2, dòng 78](/D:/GitHub/Sketch2Life/.claude/handoff/STORYRUN_LITE_VISION_DECISIONS_V2_DRAFT_20261102.md:78). Điều này chấp nhận được trong local/test chỉ có synthetic data nếu API bị giới hạn đúng môi trường. Không nên mô tả đó là BOLA protection hoặc Parent/Teacher authentication. Owner cần chốt demo là một identity cố định trên loopback hay nhiều synthetic actor với identity giả được server phát hành.

## Trình tự A1 được xác nhận khi đọc source

Application/worker gọi `InvocationGuardedVisionObservationPort.observe()`; **worker không tự claim, mark-sent hay finalize**. Bridge gọi adapter; transport gọi `guard.claim()`, rồi `guard.mark_sent()` sau khi kết nối/TLS mở và ngay trước `connection.request("POST", ...)`. Decorator finalize sau khi bridge trả kết quả đã kiểm tra, trước khi outcome quay lại worker. Ledger thực hiện các chuyển trạng thái; `complete()` chỉ chuyển từ `SENT` sang terminal tại [ledger.py, dòng 128](/D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/ledger.py:128).

A1 test chứng minh bằng HTTP loopback với `MemoryInvocationLedger` rằng request thấy trạng thái `SENT` và kết quả có thể kết thúc `SUCCEEDED` tại [test_invocation_guard_transport_ga1.py, dòng 350](/D:/GitHub/Sketch2Life/backend/tests/unit/test_invocation_guard_transport_ga1.py:350). Đây không phải bằng chứng PostgreSQL ledger hoặc A1 chạy qua Modal thật.

## Baseline và mức chứng cứ

- A2 pause report ghi `HEAD=a88de875`, index rỗng, A2 vẫn **TẠM DỪNG / XONG-CHƯA REVIEW** tại [A2 pause report, dòng 3](/D:/GitHub/Sketch2Life/features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REVIEW_FIX_PAUSE_REPORT_GA2_20261102.md:3) và [dòng 7](/D:/GitHub/Sketch2Life/features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REVIEW_FIX_PAUSE_REPORT_GA2_20261102.md:7). Báo cáo ghi focused PG cases có 4 pass nhưng teardown lỗi FK và có thể còn hàng synthetic tại [dòng 42](/D:/GitHub/Sketch2Life/features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REVIEW_FIX_PAUSE_REPORT_GA2_20261102.md:42) và [dòng 44](/D:/GitHub/Sketch2Life/features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REVIEW_FIX_PAUSE_REPORT_GA2_20261102.md:44). Vì vậy các kết quả 396 offline/68 PG pass ở checkpoint trước không chứng minh DB hiện sạch. Tôi không truy cập DB theo yêu cầu.
- Working tree hiện có A2 thay đổi chưa commit và test catalog local đã sửa. Không nên coi `HEAD` đơn lẻ hoặc catalog local là baseline đã chốt. Trước test PG của goal sau, cần pin snapshot/source baseline chính xác và dùng disposable DB sạch; không tiếp tục ghi vào `be1_acceptance` trước khi có thủ tục cleanup được duyệt.
- FEAT-061 chứng minh một lượt qua đường `demo_main` cũ với ảnh synthetic tại [smoke report, dòng 25](/D:/GitHub/Sketch2Life/features/FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md:25) và [dòng 32](/D:/GitHub/Sketch2Life/features/FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md:32). Báo cáo nói rõ nó không kiểm tra A1 đầy đủ hoặc chất lượng model tại [dòng 84](/D:/GitHub/Sketch2Life/features/FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md:84). Không chứng minh A1 guard/ledger/transport thật qua Modal, cold start, xử lý correction, hay contract StoryRun mới.

## Bắt buộc cho demo an toàn và nợ có thể hoãn

**Bắt buộc trước khi handoff UI hoặc chạy goal S1+S2:** contract/OpenAPI versioned và ví dụ state/error; binding ảnh riêng không giả checkpoint; hash/receipt ràng buộc đúng byte gửi Vision; scope Parent được biểu diễn riêng với namespace ledger; idempotency fingerprint/replay và concurrency; lưu payload kết quả trong Story; fence/sweeper không mở đường gọi trùng; giới hạn synthetic/local-test; baseline và DB test sạch được pin. A1 chưa từng chạy với Modal thật, nên lần gọi Modal thật vẫn phải là bước riêng sau readiness.

**Có thể hoãn có ghi nhận:** full `AiJobService` với deadline 6 giờ/outbox/multi-stage retry, orchestration đa worker, Teacher authentication/assignment thật, consent dữ liệu thật, video/story generation, UI và production. Có thể bỏ `AiJobService` khỏi demo một stage nếu vẫn lưu được trạng thái/kết quả cần cho UI và giữ recovery an toàn; nếu dùng process đơn thì phải cưỡng chế điều đó, không giả định. Không hoãn xử lý `UNKNOWN` và không cho retry live dựa riêng vào thời gian.

## Các quyết định owner thực sự cần chọn

1. Chốt contract route/OpenAPI cho UI, gồm `/drawing` hay `/assets`, tên subject review, DTO, polling, errors và idempotency.
2. Chọn binding `PhotoInput`/Protocol; khuyến nghị giữ nguyên `RenderBinding` và codec canvas.
3. Chốt storage, migration và command receipt; đặc biệt scope Parent và lineage. Quyết định có chấp nhận nợ `AiJobService` cho một stage hay không.
4. Chọn client/server normalization và giới hạn admission mà demo sẽ công bố.
5. Chọn subject correction: chỉ xác nhận, correction thủ công có ghi lệch SRS, hay VLM rerun với contract/context mới.
6. Chốt worker topology/sweeper, quy tắc `CLAIMED`, `UNKNOWN`, retry cap và live-call limit. Khuyến nghị không tự gọi lại sau `UNKNOWN`.
7. Pin baseline A2/catalog và quyết định DB disposable nào sẽ dùng sau này; không dùng DB có cleanup chưa xác nhận.

**Kết luận cuối:** M0 V3 đã sửa đúng các dữ kiện quan trọng về A1 và tách Modal thật khỏi goal fake/loopback, nhưng các finding P1 về thứ tự finalize, fence/retry, owner scope và contract API còn chặn mục tiêu demo. SRS và Data Table Register vẫn là draft; review này không phải approval triển khai.
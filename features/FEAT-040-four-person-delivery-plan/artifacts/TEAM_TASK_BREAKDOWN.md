# Phân công task cho 4 người — Sketch2Life scope mới

Bản này chia công việc theo task, không gắn ngày, thời lượng hoặc lịch sprint. Vai trò do bạn xác nhận: **1 FE, 2 BE, 1 người nối tất cả các phần**. Chưa có tên thành viên nên dùng P1–P4. Tổng cộng **57 task**, bao phủ 14 module của SRS v3.1; số task không phải thước đo khối lượng bằng nhau.

Nguồn yêu cầu: [Master SRS v3.1](../../FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md), [reuse/architecture audit](../../FEAT-039-collaborative-learning-scope/artifacts/REUSE_AND_ARCHITECTURE.md), [quyết định phân công mới](../../../docs/adr/ADR-0015-four-person-role-and-integration-allocation.md). Bản phân công chi tiết là backlog đề xuất để nhận việc và lập feature implementation; yêu cầu chia vai trò đã được xác nhận, các task runtime chưa được phê duyệt triển khai.

## 1. Ai chịu trách nhiệm phần nào

| Người | Vai trò | Primary ownership | Số task |
|---|---|---|---|
| P1 — Người 1 | FE | React Native Android cho Child; UI Teacher/Admin; canvas/input/UX và component tests | 15 |
| P2 — Người 2 | BE1: hệ thống lõi | Auth/scope; trường/lớp/hồ sơ/consent; session/group/canvas/sync; gallery; assessment/portfolio; core persistence/privacy | 16 |
| P3 — Người 3 | BE2: AI và nội dung | Vision/Sketch; async jobs; knowledge/video; exact-content review; activities/content/preset/AI policy; provider adapters/copies | 14 |
| P4 — Người 4 | Tổng hợp kỹ thuật | Contract registry; composition/API connectors; nối FE–BE/worker; luồng xuyên module; môi trường chung; phối hợp E2E, đo và bàn giao | 12 |

P4 có trách nhiệm tích hợp code và tạo bản chạy chung, bao gồm các connector/entrypoint/wiring cần thiết. Lỗi logic/canvas/provider/durable adapter vẫn do owner P1/P2/P3 sửa. P4 điều phối suite xuyên hệ thống; mỗi người phải bàn giao component tests/evidence của mình. Chọn framework Teacher/Admin, DB/queue/canvas/model/provider phải theo ADR phù hợp; P4 không tự chốt stack để lấp chỗ thiếu.

Một FE sở hữu cả Android và Teacher/Admin là điểm nghẽn thực tế. Nên nhận từng tập giao diện có luồng hoàn chỉnh để nối sớm; không mở cả 34 UI responsibilities đồng thời. Các card lớn như canvas, core storage và media có thể tách subtask khi lập feature, giữ nguyên primary owner và truy vết. Độ khó của real Sketch/video/authorization không tương đương một màn hình CRUD.

## 2. Những gì đã chốt và những gate còn mở

- Giữ **FastAPI, React Native, Android tablet/điện thoại**. Pilot một trường, một lớp đồng thời tối đa 40 trẻ là mục tiêu kiểm thử. Độ tuổi 36–155 tháng đủ; hồ sơ do giáo viên quản lý, QR/mã phiên, không child login riêng.
- Nhà trường thu consent; người có thẩm quyền ghi nhận/xác minh evidence và purpose. Teacher duyệt từng Sketch trước Child access. Tablet chung chọn active child theo lượt; selected contributor không thay thế identity xác thực.
- Video đang generating phải chờ. Hết retries được phép: Teacher chọn retry/skip/end, có history; không tự fallback/skip. Mặc định session/artwork giữ 90 ngày sau session end; portfolio/profile/audit/provider/backup/device copies có policy riêng.
- OD07/08/09/10/11/14/15/16/17/18 và phần còn mở của consent/retention/capacity cần quyết định tương ứng: quay lại stage, advanced tools/imports, rubric, screen-time values, admission/offline, RN runtime/canvas/sync, models/media/retry budget, privacy jurisdiction, automatic grouping. Giữ đúng trạng thái CONFIRMED/PROPOSED/TBD của từng FR trong bảng truy vết.
- Firebase chỉ Authentication. Domain độc lập framework/provider/storage/queue/UI; cross-module qua versioned ports/contracts. Mobile không chứa credentials/endpoints S3/Lightning/Runpod. Original artwork và provenance luôn giữ riêng với derivatives.

Không đưa billing, Parent portal, social/chat, thời lượng video hoặc model cũ trở lại làm prerequisite. Replay/advanced-age UX và automatic grouping Phase 2 vẫn có task/owner; import/text/sticker TBD vẫn có refinement gate. Chưa làm extension không được ghi requirement đã hoàn thành chỉ vì feature flag tắt.

## 3. Bắt đầu độc lập, rồi nối theo đầu ra

| Người | Task có thể bắt đầu độc lập | Bàn giao đầu tiên |
|---|---|---|
| P1 | FE-01 | UI/canvas fixture runner, state/error/operation examples, Android prototype/benchmark plan |
| P2 | BE1-01 | Core domain/command/permission fixtures, ports, standalone validation runner |
| P3 | BE2-01 | AI/job/review/media fixtures, state machine và fake provider runner |
| P4 | INTG-01 | Contract/fixture registry, fake-boundary integration runner, compatibility/error map |

Bốn runner dùng synthetic data và tự chạy khi không có backend/database/provider thật hoặc output của người khác. Sau đó review chéo payload/error/version/hash, ghi những candidate được adopt và unresolved gaps. Việc review là checkpoint đầu ra, không là lịch sprint hoặc prerequisite khiến ba người phải chờ P4. Đây là nguyên tắc độc lập của ADR-0006; phân vai mới theo ADR-0015 thay nhãn discipline lịch sử.

Khi đủ các output cần cho một luồng, P4 nối ngay luồng đó theo task tích hợp tương ứng. Không phải chờ xong cả 57 task mới bắt đầu nối. Đường kỹ thuật chính: lớp/consent/join → canvas/control/recovery → gallery/knowledge/video → off-screen/reflection/portfolio. **Trợ giúp Sketch là nhánh tùy chọn**; gallery/video vẫn chạy khi trẻ không yêu cầu Sketch, với meaning được Teacher xác nhận. Admin/data lifecycle đi kèm các phạm vi tương ứng trước khi tuyên bố pilot hoàn chỉnh.

Task ID INTG-01–12 thuộc backlog này; SRS INT-01–12 là scenario kiểm thử khác. H-* là sổ bàn giao bên dưới, không phải endpoint mới hoặc một task thứ 58.

## 4. Danh mục task để nhận việc

Tất cả task cards có trạng thái **PROPOSED / NOT_STARTED (runtime)**. Bộ tài liệu phân công được hoàn thành không làm các cards thành DONE. Khi nhận card, tạo hoặc dùng owning feature, chốt plan/acceptance/approval và lưu evidence tại feature đó.

### P1 — FE

| Task | Công việc |
|---|---|
| FE-01 | Nền tảng UI chạy độc lập và prototype canvas Android |
| FE-02 | Child join, admission, Lobby và chọn lượt |
| FE-03 | Teacher lớp, tạo phiên, Lobby và preset |
| FE-04 | Canvas, cộng tác, turn attribution và recovery |
| FE-05 | Teacher live dashboard và group workspace |
| FE-06 | AI request, Teacher review queue và Child agency |
| FE-07 | Gallery và trình bày tác phẩm |
| FE-08 | Knowledge/video review, wait và failure disposition |
| FE-09 | Activity assignment và off-screen handoff |
| FE-10 | Reflection, observations và assessment |
| FE-11 | Portfolio, learning reports và scoped exports |
| FE-12 | Teacher authoring và Admin content governance |
| FE-13 | Admin overview, adult accounts và school/class configuration |
| FE-14 | Admin AI policy, monitoring/incident và audit |
| FE-15 | Admin consent/data requests và lifecycle policy |

### P2 — BE1 lõi

| Task | Công việc |
|---|---|
| BE1-01 | Đặc tả domain và bộ fixture backend lõi độc lập |
| BE1-02 | Durable core adapters, migrations và transaction/outbox |
| BE1-03 | Adult authentication, assignments và device-grant lifecycle |
| BE1-04 | Class, managed child profiles và enrollment |
| BE1-05 | School-mediated consent và purpose enforcement |
| BE1-06 | Session configuration, preset snapshot, lobby và explicit Start |
| BE1-07 | QR/mã phiên, pending device và Teacher admission |
| BE1-08 | Manual groups, progress/help, move và leave |
| BE1-09 | Turn attribution và authorized canvas operation log |
| BE1-10 | Canvas sync, checkpoints, restore và reconnect recovery |
| BE1-11 | Teacher control, phase transitions và durable finish |
| BE1-12 | Scoped read models và mediated artifact delivery |
| BE1-13 | Gallery snapshots, trình bày và chú thích |
| BE1-14 | Observation, reflection, assessment và portfolio |
| BE1-15 | Retention 90 ngày, export/delete và copy-purge workflow |
| BE1-16 | Automatic grouping proposal và Teacher commit (Phase 2) |

### P3 — BE2 AI/nội dung

| Task | Công việc |
|---|---|
| BE2-01 | AI/job contract foundation và harness độc lập |
| BE2-02 | Tái sử dụng Vision và correction có provenance |
| BE2-03 | Assistance request, cancel, dedup và budget orchestration |
| BE2-04 | Pipeline tạo Sketch thật và output tách tranh gốc |
| BE2-05 | Moderation và Teacher duyệt từng Sketch |
| BE2-06 | Child view/hide/decline và tiếp tục vẽ |
| BE2-07 | Knowledge có nguồn và script versioning |
| BE2-08 | Library resolution và pipeline video generation thật |
| BE2-09 | Final video review và authorized playback |
| BE2-10 | Video exhausted failure: Teacher retry/skip/end |
| BE2-11 | Activity discovery, adaptation và execution |
| BE2-12 | Content authoring, publication review và recall |
| BE2-13 | Preset versioning, conditional automation và Teacher override |
| BE2-14 | System AI configuration, limits và kill switch |

### P4 — tích hợp

| Task | Công việc |
|---|---|
| INTG-01 | Bộ fixture tích hợp và sổ contract dùng chung |
| INTG-02 | Composition root và điểm vào backend/worker |
| INTG-03 | Kết nối Child Android, Teacher và Admin với API |
| INTG-04 | Nối canvas realtime, lượt vẽ và recovery |
| INTG-05 | Nối snapshot → Vision → Sketch → Teacher review → Child |
| INTG-06 | Nối gallery → knowledge → video → playback và failure controls |
| INTG-07 | Nối hoạt động, reflection, assessment, portfolio và kết thúc phiên |
| INTG-08 | Nối Admin, consent, content recall và data lifecycle xuyên hệ thống |
| INTG-09 | Bộ kiểm thử tích hợp chín bước và quản lý lỗi theo owner |
| INTG-10 | Môi trường chạy chung, config và quan sát hệ thống |
| INTG-11 | Xác nhận hệ thống ở tải pilot và tổng hợp device/model evidence |
| INTG-12 | Bàn giao hệ thống, demo và hồ sơ kỹ thuật |

## 5. Sổ bàn giao H-*

Handoff gồm schema/port **candidate có version**, closed payload/errors, synthetic fixtures/hash, scope/purpose/provenance, conformance results và release note. Chỉ version đã adopt trong owning feature/ADR được dùng runtime. P4 giữ registry; producer sở hữu semantics và adapters; consumer không đọc DB producer. Contract fixtures có thể bàn giao trước live implementation, tránh vòng chờ giữa BE.

| Handoff | Producer tasks | Payload/ownership boundary | Consumers |
|---|---|---|---|
| H-IDENTITY | BE1-03, BE1-04 | DATA-01/04/12/35; CMD-07/17/18/51/52/53; verified adult + scoped device context | FE-02/03/13; BE2-03/05/09; INTG-03 |
| H-CLASS-CONSENT | BE1-04, BE1-05 | DATA-02–05; CMD-01–09/54–56; age, enrollment, purpose eligibility/revoke | FE-03/15; BE2-02/03/04/08/14; INTG-03/08 |
| H-SESSION-ADMISSION | BE1-06, BE1-07, BE1-03, BE1-08 | DATA-06–14; CMD-10/12–19/24–27; pending/admit/grant/turn scope | FE-02/03/04; INTG-03/04 |
| H-CANVAS-SYNC | BE1-09, BE1-10, BE1-02 | DATA-14–20; CMD-27–31/61; operation receipt, checkpoint, snapshot, epoch | FE-01/04/05/06; BE2-02/03/07; INTG-04/05 |
| H-SESSION-CONTROL | BE1-06, BE1-08, BE1-11 | DATA-06/07/08/19; CMD-19–26/66; scoped transition/finish + clock/warning/policy events | FE-05/08/09; BE2-03/10/11/13; INTG-04/06/07/11 |
| H-AI-REVIEW | BE2-02, BE2-03, BE2-04, BE2-05, BE2-06 | DATA-21–24; CMD-32–36; source/context/meaning/proposal/exact review/child response | FE-06/14; BE1-11/12/14; BE2-09/12 shared DATA-24 contract only; INTG-05 |
| H-GALLERY | BE1-13, BE1-10 | DATA-20/32; CMD-37/65; pinned artwork/meaning/contributor/audience | FE-07; BE2-07; INTG-06 |
| H-KNOWLEDGE-VIDEO | BE2-07, BE2-08, BE2-09, BE2-10 | DATA-24/26–28; CMD-38–43; source/script/job/review/play/disposition | FE-08; BE1-11/12; INTG-06 |
| H-ACTIVITY | BE2-11, BE2-12 | DATA-29/33; CMD-45/48; published discovery/assignment/preparation/evidence refs | FE-09; BE1-11/14; INTG-07 |
| H-ASSESSMENT-PORTFOLIO | BE1-14 | DATA-30/31; CMD-46/47/62/64; observation/reflection/judgement/progress/source expiry | FE-10/11; INTG-07 |
| H-CONTENT-PRESET | BE2-12, BE2-13 | DATA-24/33; CMD-48 typed content/preset branches; publication/recall/effective version | FE-03/12; BE1-06/11/12; INTG-08 |
| H-ADMIN-POLICY | BE1-15, BE2-14, BE2-12 | DATA-33 envelope maintained by BE2-12; CMD-48 sole dispatcher. Core policy implementation BE1-15; AI policy implementation BE2-14 | FE-14/15; BE1-06/12; BE2-03/04/08; INTG-08/10 |
| H-OPERATIONS | BE2-01, BE2-03, BE2-14, BE1-02, BE1-03, BE1-11, BE1-12 | P3 job/policy projections DATA-25/33 CMD-44; P2 durable audit/session/auth projections DATA-07/35 CMD-11/59. Gateway BE1-12 calls producer ports | FE-05/14; INTG-05/10/11 |
| H-DATA-REQUEST | BE1-15, BE2-14, BE2-04, BE2-08 | DATA-34 lifecycle authority/export/core-copy purge BE1-15; ProviderCopyLifecycle schema BE2-14, provider hooks BE2-04/08; CMD-49/50/63 sole P2 | FE-11/15; INTG-08; BE1-15 consumes provider receipts; BE2-14/04/08 consume scoped authority/cancel-purge commands |

CMD-48 chỉ có một router/closed union primary ở BE2-12; content → BE2-12, preset → BE2-13, AI policy → BE2-14, non-AI organization/purpose/retention policy → BE1-15 qua versioned application port. DATA-33 envelope schema do BE2-12 duy trì, không trao quyền ghi DB của policy owner khác. CMD-59/60 primary BE1-12: query/delivery gateway gọi P3 projection/exact-review eligibility ports, không sao chép review rules hoặc truy cập DB P3. Provider-copy outcomes chưa có verified receipt phải Pending/Exception/Unsupported theo contract, không reported Deleted.

## 6. Phụ thuộc để nghiệm thu implementation

Bảng này ghi dependency nội bộ của **chặng runtime đầy đủ**, không bắt các fixture đầu tiên chờ runtime. Cross-role producer outputs ở sổ H-* là điều kiện riêng để nối thật; UI/domain có thể dùng fake port trước đó. Gate ADR/authority/model/policy trong từng card vẫn áp dụng. Shared DATA-24 schema/review fixtures BE2-05 có từ foundation: BE2-09/12 chỉ cần phần contract này, không phụ thuộc real Sketch BE2-04/05. ProviderCopyLifecycle schema BE2-14 được review từ foundation, không phải đợi policy activation rồi mới viết adapters.

<!-- DEPENDENCIES-BEGIN -->
| Task | Task runtime nội bộ cần trước |
|---|---|
| FE-01 | Không; foundation độc lập |
| FE-02 | FE-01 |
| FE-03 | FE-01 |
| FE-04 | FE-01, FE-02 |
| FE-05 | FE-03, FE-04 |
| FE-06 | FE-04, FE-05 |
| FE-07 | FE-04, FE-05 |
| FE-08 | FE-05, FE-07 |
| FE-09 | FE-05, FE-08 |
| FE-10 | FE-09 |
| FE-11 | FE-07, FE-10 |
| FE-12 | FE-01 |
| FE-13 | FE-01 |
| FE-14 | FE-01 |
| FE-15 | FE-01 |
| BE1-01 | Không; foundation độc lập |
| BE1-02 | BE1-01 |
| BE1-03 | BE1-01, BE1-02 |
| BE1-04 | BE1-01, BE1-02, BE1-03 |
| BE1-05 | BE1-02, BE1-03, BE1-04 |
| BE1-06 | BE1-02, BE1-03, BE1-04, BE1-05 |
| BE1-07 | BE1-03, BE1-04, BE1-05, BE1-06 |
| BE1-08 | BE1-03, BE1-06, BE1-07 |
| BE1-09 | BE1-01, BE1-02, BE1-03, BE1-05, BE1-08 |
| BE1-10 | BE1-02, BE1-03, BE1-09 |
| BE1-11 | BE1-06, BE1-08, BE1-10 |
| BE1-12 | BE1-02, BE1-03, BE1-05, BE1-06 |
| BE1-13 | BE1-05, BE1-09, BE1-10, BE1-12 |
| BE1-14 | BE1-03, BE1-05, BE1-10, BE1-11, BE1-13 |
| BE1-15 | BE1-02, BE1-03, BE1-05, BE1-10, BE1-13, BE1-14 |
| BE1-16 | BE1-04, BE1-06, BE1-08 |
| BE2-01 | Không; foundation độc lập |
| BE2-02 | BE2-01 |
| BE2-03 | BE2-01, BE2-02 |
| BE2-04 | BE2-01, BE2-02, BE2-03 |
| BE2-05 | BE2-01, BE2-04 |
| BE2-06 | BE2-05 |
| BE2-07 | BE2-01 |
| BE2-08 | BE2-01, BE2-07 |
| BE2-09 | BE2-08 |
| BE2-10 | BE2-01, BE2-08 |
| BE2-11 | BE2-01, BE2-12 |
| BE2-12 | BE2-01 |
| BE2-13 | BE2-01, BE2-12 |
| BE2-14 | BE2-01, BE2-12 |
| INTG-01 | Không; foundation độc lập |
| INTG-02 | INTG-01 |
| INTG-03 | INTG-02 |
| INTG-04 | INTG-03 |
| INTG-05 | INTG-04 |
| INTG-06 | INTG-03, INTG-04 |
| INTG-07 | INTG-06 |
| INTG-08 | INTG-03, INTG-05, INTG-07 |
| INTG-09 | INTG-04, INTG-05, INTG-06, INTG-07, INTG-08 |
| INTG-10 | INTG-02 |
| INTG-11 | INTG-09, INTG-10 |
| INTG-12 | INTG-09, INTG-10, INTG-11 |
<!-- DEPENDENCIES-END -->

## 7. Task cards chi tiết

### P1 — FE

#### FE-01 — Nền tảng UI chạy độc lập và prototype canvas Android

- **Chủ trì / review:** P1; P2 review command/operation shape, P4 review runner/handoff. Đầu ra nền tảng độc lập, chưa nối API thật.
- **Phạm vi / bàn giao:** RN fixture runner với navigation/state adapter, component status/alias/help và command/result envelopes; một canvas prototype dùng nét synthetic có local tentative/accepted/rejected state. So sánh các candidate editor/runtime trong ADR OD15 bằng thao tác input/render, own-undo, turn context và interrupted-draft fixtures; chọn candidate thử nghiệm không tự freeze stack. Teacher/Admin UI wireframes/state fixtures không khóa web framework. Bàn giao manifest fixture/version, runner instructions, operation examples và benchmark plan/raw evidence nếu benchmark được duyệt.
- **Prerequisites / gate:** không phụ thuộc live service hoặc task BE/INT; đọc B19–B23 và reuse audit. Benchmark on-device/package additions theo feature approval; OD08/OD15 trước production editor. H-CANVAS-SYNC là handoff sẽ consume, không prerequisite chạy fixture.
- **SRS:** UC-013/015/016; FR014–021, FR060/063/066; NFR01/05/06/10; UI IDs là cross-cutting, primary ownership ở các card sau; P-NFR-01/14, GATE-02.
- **Nghiệm thu dương:** Given fixture contract hợp lệ và backend không chạy, When mở runner, join state và vẽ synthetic stroke, Then UI hoạt động độc lập, cho thấy đúng tentative/accepted states và xuất manifest không cần secret/provider.
- **Nghiệm thu âm:** Given fixture event version unsupported hoặc stroke bị reject, When runner nhận outcome, Then hiện typed error/recovery draft, không đổi thành saved và không sửa nét accepted của peer.
- **Evidence / DoD riêng:** runner execution log, screenshot các state synthetic, input/render trace được gắn device manifest nếu đã đo, comparison/decision note; số đo chưa có ghi chưa đo. P2/P4 đọc được contract fixtures và chạy lại được cùng kịch bản.

#### FE-02 — Child join, admission, Lobby và chọn lượt

- **Chủ trì / review:** P1; P2 review admission/grant/turn, P4 review integration seams.
- **Phạm vi / bàn giao:** C01/C02, QR scan + nhập mã fallback, pending admission, hiển thị nhóm/alias chỉ sau authorization; chọn active contributor theo lượt trên thiết bị chung; không tạo child login account. UI và adapter không coi QR/code là quyền đọc roster/canvas. Gate đổi lượt cuối cùng được nối với canvas trong FE-04.
- **Prerequisites / gate:** FE-01; H-IDENTITY và H-SESSION-ADMISSION; camera permission chỉ cho QR scan, không xin camera để chụp evidence lớp mặc định.
- **SRS:** FR002/003/005/066; UC-007/008; C01/C02; CMD-13–18/27; FIX-UX-01/02.
- **Nghiệm thu dương:** Given mã hợp lệ và Teacher đã admit device/profile, When trẻ chọn contributor trong tập được bind, Then hiện đúng group/turn policy; rejoin/retry không tạo participant trùng.
- **Nghiệm thu âm:** Given camera permission bị từ chối hoặc mã expired/chưa admit, When scan/join hay mở canvas, Then nhập mã còn dùng được, chưa có quyền thì không hiện roster/artwork và UI giữ safe pending/error state.
- **Evidence / DoD riêng:** fixture screen states và test kết nối admitted/pending/revoked; sanitize QR/token trước lưu evidence; adapter mapping admission/device grant/turn được P2 review.

#### FE-03 — Teacher lớp, tạo phiên, Lobby và preset

- **Chủ trì / review:** P1; P2 review classroom/session, P3 review preset semantics; P4 nối acceptance.
- **Phạm vi / bàn giao:** T01/T02/T03/T04/T14: lớp được assignment, profiles/enrollment/consent summary, builder topic/tuổi/tools/canvas/groups, Lobby admit/reject/device binding, explicit Start, preset version/overrides. Consent evidence thao tác sâu ở FE-15, không tự suy consent từ enrollment. Manual grouping là core; auto-grouping UI giữ extension backlog/feature gate OD18.
- **Prerequisites / gate:** FE-01; H-IDENTITY, H-CLASS-CONSENT, H-SESSION-ADMISSION, H-CONTENT-PRESET. Desktop web framework và auth adapter cần ADR; feature branch fixture có thể chạy riêng. OD07/11/14/18 áp dụng cho controls còn chưa chốt.
- **SRS:** FR004/006–008/010/015/052/053/065; UC-002–006/007/033; T01/T02/T03/T04/T14; CMD-01–06/10/12–16/19/24/48/57/58; FIX-GOV-01.
- **Nghiệm thu dương:** Given roster đủ tuổi/consent trong một lớp ≤40 trẻ, When Teacher lưu config/preset pinned version, admit và explicit Start, Then hiển thị Active chỉ sau server acceptance và retry không start lần hai.
- **Nghiệm thu âm:** Given tuổi 35/156 tháng, thiếu consent, preset stale hoặc roster vượt40, When mở/start phiên, Then hiện từng safe validation finding, giữ trạng thái hợp lệ cũ; preset không bypass per-Sketch/video review.
- **Evidence / DoD riêng:** core setup click path, state/conflict fixture outcomes, field validation/role checks, manual grouping và planned auto-grouping extension label. Các 36–155 tháng/40 trẻ là policy/target, không load-test claim.

#### FE-04 — Canvas, cộng tác, turn attribution và recovery

- **Chủ trì / review:** P1; P2 review operations/auth/recovery; P4 review reconnect handoff.
- **Phạm vi / bàn giao:** C03/C05/C10: editor cá nhân/nhóm, tool/region theo participant, active child rõ, scoped own-undo và process replay khi operation extension adopted; status on-device/sending/accepted/rejected; pending draft queue/checkpoint watermark, resync/dedupe/gap/permission conflicts. AI overlay chỉ renderer slot riêng, dataflow ở FE-06. Shapes/layers/transform/import/text là extension task con của card này sau contract/tool gates, không biến flag thành support giả.
- **Prerequisites / gate:** FE-01/FE-02; H-CANVAS-SYNC, H-SESSION-ADMISSION, H-SESSION-CONTROL. OD08/09/14/15 và local retention policy trước editor production/offline authoring; advanced tools giữ backlog đến có payload/permission/causality/replay contracts.
- **SRS:** FR014–021/060/063/066; UC-008/013–017; C03/C05/C10; CMD-27–31/61; AT-CS-001–007, FIX-UX-02/03, P-NFR-01/02/04/05.
- **Nghiệm thu dương:** Given hai authorized devices cùng group và A→B turn switch đã ack, When vẽ, duplicate delivery rồi reconnect, Then mỗi accepted stroke hiện một lần, nét mới gắn B, nét cũ vẫn A; accepted checkpoint/hash phục hồi đúng.
- **Nghiệm thu âm:** Given teacher lock/revoke/group move sau local draft, When reconnect/replay hoặc own-undo cố tác động nét peer, Then adapter nhận reject, hiện draft/disposition cần hỗ trợ, không replay trái quyền hoặc báo saved.
- **Evidence / DoD riêng:** synthetic two-device operation set/hash, reconnect/turn/undo outcomes, save-state screenshots và approved-device input/render traces khi đã chạy. Chưa có benchmark thì không báo đạt 40 children/touch responsiveness.

#### FE-05 — Teacher live dashboard và group workspace

- **Chủ trì / review:** P1; P2 review state machine, region/group operations; P4 review combined view.
- **Phạm vi / bàn giao:** T05/T06, group progress độc lập, help queue, admitted device/turn status, authorized thumbnails, pause/resume/advance/draft/end, move member/lock/restore/contribution correction. Controller command được confirm bằng current server version; restore/correction giữ provenance. Consume H-SESSION-CONTROL từ BE1-11 cho clock/elapsed, pause/resume, policy version và warning/Teacher override events; hiển thị cảnh báo theo config đã adopt. Session elapsed không được gắn nhãn thời gian từng trẻ thực sự nhìn màn hình.
- **Prerequisites / gate:** FE-03/FE-04; H-SESSION-CONTROL, H-CANVAS-SYNC. OD07/11/14 trước rewind/hard timer/co-teacher/teacher-offline controls; không thêm các quyền này bằng UI.
- **SRS:** FR008–013/016–018/051/054/060/063/066; UC-009–012/014–016/032; NFR12; T05/T06; CMD-19–31/61/66; AT-CS-005/006/007/014, P-NFR-16/17.
- **Nghiệm thu dương:** Given group A ready còn B đang vẽ, When Teacher pause rồi resume bằng current revision, Then cả lớp giữ stage đến explicit advance, pending/accepted control rõ; progress A/B vẫn độc lập. Given adopted warning config, When backend phát warning/elapsed rồi Teacher override có receipt, Then UI hiển thị đúng policy version, clock/pause state và override outcome; không suy individual screen exposure từ session clock.
- **Nghiệm thu âm:** Given session revision stale hoặc child đã chuyển group, When controller/membership command conflict, Then UI reload safe context, không optimistic success/mất history, binding cũ không được vẽ tiếp. Given threshold/hard-stop OD11 chưa adopt hoặc warning version stale, When UI nhận clock/warning, Then không hardcode phút, tự end hay phạt trẻ; stale status được reload/đánh dấu, không áp policy cũ ngầm.
- **Evidence / DoD riêng:** control conflict/independent-group test outputs, visible pending/error/health states và review confirmation UX cho restore/end; fake-clock pause/resume/warning/override traces gắn effective policy version và labels phân biệt session elapsed với individual exposure; P2 đối chiếu state-machine outcomes.

#### FE-06 — AI request, Teacher review queue và Child agency

- **Chủ trì / review:** P1; P3 review understanding/Sketch/moderation, P2 review source/scope; P4 review end-to-end seam.
- **Phạm vi / bàn giao:** C04/T07: Vision meaning correction, request/debounce/rate feedback, source snapshot/hash/support level, per-item approve/reject/regenerate, Child view/hide/decline, overlay tách strokes; queue/status tuổi request. Không preview/download raw pending proposal cho Child.
- **Prerequisites / gate:** FE-04/FE-05; H-AI-REVIEW, H-CANVAS-SYNC. OD16 model/output và applicable consent/limits trước provider execution; fixture queue trước không cần GPU.
- **SRS:** FR019/022–030/051/054/061; UC-017–021/032; C04/T07; CMD-32–36/44; FIX-UX-04, AT-CS-008/009, P-NFR-08/09/16.
- **Nghiệm thu dương:** Given proposal đúng context/version đã Teacher approve, When Child mở rồi hide/decline, Then chỉ overlay thay visibility/agency state, original strokes không đổi và proposal đó không bị automation bật lại.
- **Nghiệm thu âm:** Given unsafe/pending/stale proposal hoặc consent revoke giữa job, When Child mở trợ giúp/Teacher approve bản cũ, Then không deliver artifact, queue giữ typed outcome và không có preset approve-all bypass.
- **Evidence / DoD riêng:** source/review/version/visibility fixtures, delayed/duplicate completion probes, safe queue screenshots; xác minh không model prompt/credentials xuất hiện trong mobile/UI logs.

#### FE-07 — Gallery và trình bày tác phẩm

- **Chủ trì / review:** P1; P2 review snapshot/gallery scope, P3 review derivative/provenance; P4 review display.
- **Phạm vi / bàn giao:** C06/T08, preview immutable artwork, original vs AI overlay, Teacher select/order/annotate/publish/present/withdraw; declared group contributions hiển thị khi evidence đủ. Không public social/share link mặc định, không tự thêm recording mic/camera.
- **Prerequisites / gate:** FE-04/FE-05; H-GALLERY. OD09/16 trước audio/text explanation collection; versioned media authorization.
- **SRS:** FR019/021/031–033; UC-017/022; C06/T08; CMD-37/65; FIX-PRIV-03, FIX-UX-07, P-NFR-11.
- **Nghiệm thu dương:** Given snapshots cùng phiên đã được phép chia sẻ, When Teacher chọn/sắp xếp/annotate rồi present, Then gallery đúng thứ tự, annotation riêng và source hashes không đổi.
- **Nghiệm thu âm:** Given revoke/cross-class snapshot hoặc group artwork chưa có individual attribution, When preview/publish, Then media unauthorized không mở; UI không gán tranh nhóm cho một trẻ hoặc public share.
- **Evidence / DoD riêng:** empty/gallery/display/source split screenshots, authorize/revoke test outcomes và snapshot checksum provenance.

#### FE-08 — Knowledge/video review, wait và failure disposition

- **Chủ trì / review:** P1; P3 review jobs/script/artifact/approval, P2 review session stages; P4 review playback chain.
- **Phạm vi / bàn giao:** C07/T09, Teacher knowledge/script source editing, library select/generate, attempts/status, exact video version/hash review/playback. Generating phải chờ; exhausted failure cho Teacher explicit retry/skip/end; playback error khác render failure. Caption/TTS/audio language còn gate, không nhập thời lượng cũ.
- **Prerequisites / gate:** FE-05/FE-07; H-KNOWLEDGE-VIDEO, H-SESSION-CONTROL. OD16 retry/model/encoding/library profile trước real generation/playback acceptance; fixture states không claim generated video.
- **SRS:** FR034–040; UC-023–026; C07/T09; CMD-38–44; FIX-UX-05, AT-CS-010/011, P-NFR-10.
- **Nghiệm thu dương:** Given exact artifact Teacher đã approve, When Teacher phát cho audience được grant, Then Child xem đúng approved hash; exhausted-failure fixture cho Teacher chọn disposition và lưu outcome đó.
- **Nghiệm thu âm:** Given đang Generating hoặc script/artifact đã đổi sau review, When Child/automation cố skip/play, Then không tự skip/fallback/play bản stale; Teacher UI yêu cầu review mới, không gọi skipped là successfully generated.
- **Evidence / DoD riêng:** generating/review/failure/playback state matrix, request retry/idempotency results và approved hash; actual codec/device playback evidence tách stub generation evidence.

#### FE-09 — Activity assignment và off-screen handoff

- **Chủ trì / review:** P1; P3 review catalog/activity versions, P2 review class/group assignment; P4 review stage handoff.
- **Phạm vi / bàn giao:** C08/T10, discovery/library recommendation, nguyên bản/Teacher edits, material/safety/preparation, assignment theo class/group, off-screen instructions/help/ready signals; Child done signal tách Teacher observation. Hoạt động reviewed assets được dùng theo visual/provenance rules.
- **Prerequisites / gate:** FE-05/FE-08; H-ACTIVITY, H-SESSION-CONTROL. Adopt catalog discovery semantics/pedagogical/material policy trước production selection; OD10/11 phần liên quan.
- **SRS:** FR041–044; UC-027/028; C08/T10; CMD-45/48/59; FIX-UX-06, P-NFR-17.
- **Nghiệm thu dương:** Given activity version được phép và Teacher xác nhận chuẩn bị, When assign cho một group và start off-screen, Then chỉ đúng nhóm nhận chỉ dẫn, Teacher edit có lineage và help/xong là signal riêng.
- **Nghiệm thu âm:** Given thiếu vật liệu/safety hoặc Child tự mark done, When start/advance, Then UI dẫn về Teacher chuẩn bị/chọn lại; không tự xác nhận assessment hoặc chuyển cả lớp.
- **Evidence / DoD riêng:** assignment/preparation fixtures, original/edit diff, Child instructions/help screenshots; không thu camera evidence mặc định.

#### FE-10 — Reflection, observations và assessment

- **Chủ trì / review:** P1; P2 review evidence/assessment, P3 review AI suggestion separation; P4 review learning-result assembly.
- **Phạm vi / bàn giao:** C09/T11, reflection tương tác theo tuổi, save draft/submit duplicate-safe, Teacher evidence/NOT_OBSERVED/descriptive observation, AI draft riêng, confirm/correction version. Không peer ranking/psychological inference; không thu mic/text chưa duyệt.
- **Prerequisites / gate:** FE-09; H-ASSESSMENT-PORTFOLIO. OD10 rubric/OD09 input and relevant purpose policy trước final form; reviewed synthetic rubric fixtures được label candidate.
- **SRS:** FR044/045/049/050; UC-028/029; C09/T11; CMD-46/62; FIX-UX-06, GATE-05.
- **Nghiệm thu dương:** Given evidence đủ và rubric version adopted, When Teacher lưu/chốt observation rồi correction, Then child reflection/Teacher result/AI draft tách loại, correction append revision và retry không duplicate.
- **Nghiệm thu âm:** Given chưa quan sát hoặc thiếu individual attribution, When form confirm, Then lưu NOT_OBSERVED/group context phù hợp; AI suggestion không tự thành Teacher-confirmed assessment và partial save không hiện completed.
- **Evidence / DoD riêng:** evidence association/draft/confirmation/correction fixtures, age UI states và consent/output minimization checks.

#### FE-11 — Portfolio, learning reports và scoped exports

- **Chủ trì / review:** P1; P2 review portfolio/report/export authorization, P4 review report assembly.
- **Phạm vi / bàn giao:** T12/A07, timeline/evidence/contribution quality, own progress/descriptive reports, export request/status/download có permission revalidation; separate school aggregate operational reports với learning report purposes. Không leaderboard.
- **Prerequisites / gate:** FE-07/FE-10; H-ASSESSMENT-PORTFOLIO, H-DATA-REQUEST. Portfolio/profile/audit TTL và aggregate suppression policy chưa chốt không tự lấy TTL90 cho mọi thứ.
- **SRS:** FR011/046–050/057–059; UC-011/030/031/038; T12/A07; CMD-23/47/49/50/64; FIX-PRIV-03, P-NFR-12.
- **Nghiệm thu dương:** Given Teacher đang có assignment/purpose và own-progress entries hợp lệ, When filter report/export, Then hiện đúng evidence provenance và download chỉ sau artifact authorized/current status.
- **Nghiệm thu âm:** Given assignment revoke giữa export hoặc group artwork chứa peer data, When xem/download, Then không trả peer raw media trái phép/không dùng role Admin như raw-read grant; partial export không báo complete.
- **Evidence / DoD riêng:** report definitions/state screenshots, privilege/revoke/peer-data fixtures và export result/hash liên kết request.

#### FE-12 — Teacher authoring và Admin content governance

- **Chủ trì / review:** P1; P3 review content/publish/recall/version, P4 review usage impact view.
- **Phạm vi / bàn giao:** T13/A04, draft author/source/topic/age/material/safety, request review/change/publish/recall, version history và affected usage summaries; Teacher author không tự có global publish grant. Preset UI đã ở FE-03/T14.
- **Prerequisites / gate:** FE-01; H-CONTENT-PRESET. Content reviewer/recall active-playback policy refinement và reviewed assets/visual approval trước apply.
- **SRS:** FR040–042/052/056/062; UC-027/033/035; T13/A04; CMD-48; FIX-GOV-01, GATE-05.
- **Nghiệm thu dương:** Given draft đủ source/audience/review và publisher scope, When publish version mới, Then active content pin version/hash và published version cũ không bị sửa trực tiếp.
- **Nghiệm thu âm:** Given Teacher chỉ là author hoặc source/review thiếu, When publish/recall trái grant, Then UI báo denied/findings, không phát nội dung chưa duyệt; library edit không tự đổi active session.
- **Evidence / DoD riêng:** draft/review/recall state transitions, role/policy negative probes và lineage display examples.

#### FE-13 — Admin overview, adult accounts và school/class configuration

- **Chủ trì / review:** P1; P2 review identity/assignment/class scope, P4 review bootstrap integration.
- **Phạm vi / bàn giao:** A01/A02/A03, operational metadata overview có freshness, adult account/status/roles/grants, class/archive/Teacher assignment. Chuẩn bị organization keys cho mở rộng nhưng pilot một trường; không tạo child accounts và không thêm production multi-tenant UX chưa yêu cầu.
- **Prerequisites / gate:** FE-01; H-IDENTITY, H-CLASS-CONSENT, H-ADMIN-POLICY. Bootstrap/provisioning/recovery/dual approval cần policy trước thao tác quyền production.
- **SRS:** FR001/004/005/055/058; UC-001/002/034; A01/A02/A03; CMD-01/07/18/51–53/56; P-NFR-06/07.
- **Nghiệm thu dương:** Given authorized Admin grant đúng trường, When archive class hoặc revoke Teacher assignment, Then metadata/version được cập nhật, history giữ nguyên và access revocation hiển thị rõ.
- **Nghiệm thu âm:** Given caller tự đề nghị nâng scope/role hoặc Admin không có raw-art grant, When sửa quyền/xem media, Then denied, không lộ child artwork/guardian evidence và không sửa identity claims từ UI.
- **Evidence / DoD riêng:** loading/empty/stale/revoked screens, assignment/account fixtures và scoped history; không seed account/credentials thật.

#### FE-14 — Admin AI policy, monitoring/incident và audit

- **Chủ trì / review:** P1; P3 review AI/job/policy, P2 review durable audit/access, P4 review telemetry contract.
- **Phạm vi / bàn giao:** A05/A06/A09, candidate policy draft/activate/revoke, job aggregate status/queue controls theo grant, redacted incidents/metrics/audit filters/history. Không sửa DB row/job trực tiếp hoặc hiển thị credentials/provider internals cho Child; metrics timestamp phân biệt stale/zero.
- **Prerequisites / gate:** FE-01; H-OPERATIONS, H-ADMIN-POLICY, H-AI-REVIEW. AI policy/model activation cần OD16 evaluation/ADR; audit retention và exceptional access vẫn gated.
- **SRS:** FR029/030/054/056–059/064; UC-036/037/038; A05/A06/A09; CMD-11/44/48/50/59/60/63; FIX-NFR-02/03, P-NFR-13/16.
- **Nghiệm thu dương:** Given redacted operational data và scoped operator, When xem lag/status/incident và gửi permitted queue command, Then có freshness/correlation và outcome/history qua versioned application command.
- **Nghiệm thu âm:** Given log chứa synthetic sensitive sentinel hoặc policy muốn bypass Teacher review, When render/activate, Then không hiện raw child/token/prompt/QR; config bị reject, audit không cho UI sửa/xóa event cũ.
- **Evidence / DoD riêng:** redaction sentinel probes, incident/status fixtures và stale/retry command outcomes; không lấy screenshot chứa token/signed URL.

#### FE-15 — Admin consent/data requests và lifecycle policy

- **Chủ trì / review:** P1; P2 review purposes/data lifecycle/revocation, P3 review provider/artifact copy states; P4 review shared-work purge results.
- **Phạm vi / bàn giao:** A08/A10, evidence metadata theo quyền, consent verify/revoke/correct, export/delete authority/scope review, per-store pending/exception/results; policy draft/diff/validate/activate/version với confirmed session/artwork TTL90 và data classes khác riêng. Evidence bytes cần grant riêng; không nút purge bỏ authority/shared-work/backups review.
- **Prerequisites / gate:** FE-01; H-CLASS-CONSENT, H-DATA-REQUEST, H-ADMIN-POLICY. OD04/05/17/legal authority/verification/other data TTL cần policy adoption; UI không declare legal compliance.
- **SRS:** FR006/055–059/064; UC-003/034/038; A08/A10; CMD-08/09/49/50/54/55/63; FIX-PRIV-01–05, P-NFR-07/12.
- **Nghiệm thu dương:** Given school evidence đã được authorized verifier kiểm tra đúng purpose, When ghi/thu hồi và theo dõi data request, Then status/scope/version thể hiện riêng với enrollment, policy raw-session TTL90 tính từ session end và per-copy results được hiển thị.
- **Nghiệm thu âm:** Given evidence chưa xác minh, quyền guardian request chưa kiểm hoặc purge còn external/backup exception, When bật purpose/complete request/activate TTL chung, Then không tự grant consent/không báo completed, portfolio/profile/audit không thừa hưởng90 ngày vô điều kiện.
- **Evidence / DoD riêng:** consent purpose matrix, data-request incomplete/exception state screenshots, policy diff/validation results và role/evidence isolation probes; chỉ dùng synthetic evidence metadata.

### P2 — BE1 lõi

#### BE1-01 — Đặc tả domain và bộ fixture backend lõi độc lập

- **Đầu ra:** domain model/ports và schema fixtures cho authorization, lớp/hồ sơ/consent, session/group/admission, turn/canvas, gallery/portfolio/data request; closed command envelopes, errors/CAS/idempotency conventions và standalone runner. Manifest ghi exact contract version và owner; initial fixtures dùng synthetic data, in-memory test adapters.
- **Phụ thuộc/gate:** không phụ thuộc live service, không DB/provider thật. Đọc SRS v3.1 B19–B26; chốt những chi tiết PROPOSED cần áp dụng trong feature approval. Không tự khóa cả stack hoặc biến TBD thành default.
- **Truy vết:** M01–M05/M07/M10/M12–M14; FR001–018, FR021, FR031–033, FR045–050, FR055, FR057–060, FR063–066; UC-001–016, UC-022, UC-029–034, UC-037–038; DATA ownership ở trên, API-CS-01–03.
- **Nghiệm thu:** positive: runner độc lập tải fixture request/state/result của các handoff core và kiểm tra pass bằng domain/application, không cần service khác. Negative: unknown fields/invalid scope, forged role, age 35/156, stale revision và duplicate key khác payload trả đúng typed failures; không reset state để test pass.
- **Evidence/reviewer:** schema/fixture manifest, runner command+output, contract review và source-vs-target gaps trong feature evidence; P4 review contract, P3 review AI/content boundary, P1 review child-facing projections.

#### BE1-02 — Durable core adapters, migrations và transaction/outbox

- **Đầu ra:** approved storage adapter cho core repositories, unit-of-work/CAS/idempotency, durable canvas operation/checkpoint metadata, asset metadata/lineage, audit append và outbox; migrations core có forward/restore strategy, synthetic seed fixture không credentials. Tách durable authoritative truth khỏi optional cache/presence/pub-sub. Không triển khai AI model/job rules trong task này.
- **Phụ thuộc/gate:** BE1-01; ADR chọn DB/object store/runtime mechanism trước adapter thật. Backend-only object access; Firebase Authentication-only, cấm Firebase Storage/Firestore/Realtime Database. Credential đi qua ignored runtime secrets.
- **Truy vết:** FR011, FR017, FR047, FR059–060, FR064; B19.3/B19.8/B22.3; DATA-07, DATA-17–DATA-20, DATA-31, DATA-34–DATA-35; P-NFR-04/11/13.
- **Nghiệm thu:** positive: restart process sau durable commit giữ accepted operation/receipt/audit và outbox replay không nhân đôi side effect. Negative: transaction thất bại không phát durable ack hoặc Completed; duplicate delivery không tạo record mới, logging sentinel không lộ child data/token.
- **Evidence/reviewer:** migration matrix, actual adapter integration results, crash-point receipts/checksums và redacted logs; P3 review generic ports/outbox use, P4 review composition/migration contract. Chỉ simulated/in-memory pass chưa hoàn thành adapter thật.

#### BE1-03 — Adult authentication, assignments và device-grant lifecycle

- **Đầu ra:** backend adult-token verifier adapter, local scoped role/capability resolver, account commands, Teacher assignment/revoke và admitted-device grant refresh/revoke. Không dùng X-Actor-Ref/demo actor làm production authorization; Child không có login riêng. Có fixture verifier để test độc lập.
- **Phụ thuộc/gate:** BE1-01; adapter persisted cần BE1-02. Policy account provisioning/last Admin/device proof/key store phải được adopt, không hardcode user/credential. H-IDENTITY cho FE và P3.
- **Truy vết:** FR001, FR005, FR055, FR058–059; UC-001/034; DATA-01, DATA-04, DATA-12, DATA-35; **CMD-07, CMD-17, CMD-18, CMD-51, CMD-52, CMD-53**.
- **Nghiệm thu:** positive: Teacher assigned đúng lớp có context tối thiểu; grant refresh còn hợp lệ tạo replacement và revoke làm future reads/writes/subscriptions bị deny. Negative: giả role/header, expired token, self-elevation, revoke assignment rồi refresh, Admin chỉ monitoring xin raw child data đều bị chặn; lịch sử contribution không bị xóa.
- **Evidence/reviewer:** permission matrix, verifier/expiry/revoke race tests, redacted request/result và audit; P4 review auth wiring, P1 review login/revoke UX, P3 review worker/completion authorization.

#### BE1-04 — Class, managed child profiles và enrollment

- **Đầu ra:** class create/list/edit/archive; roster/profile create/update theo assignment, atomic profile+enrollment và enrollment end; versioned age computation context, minimized roster projections. Android nhận label/tool policy cần thiết, không mặc định nhận DOB/evidence riêng tư.
- **Phụ thuộc/gate:** BE1-01/03; persisted cần BE1-02. Age endpoints đã chốt 36–155; chốt age-date calculation/mixed-age details trước eligibility implementation liên quan. Một trường có organization scope server-derived, chuẩn bị mở rộng không claim multi-school ready.
- **Truy vết:** FR004, FR012, FR055, FR059; UC-002/012/034; DATA-02–DATA-04; **CMD-01, CMD-02, CMD-03, CMD-04, CMD-05, CMD-06, CMD-56**.
- **Nghiệm thu:** positive: tuổi 36/155 eligible đúng ngày tham chiếu đã adopt, edit tăng age-context revision và enrollment end chặn participation mới nhưng giữ lịch sử. Negative: tuổi 35/156 hoặc unknown age không join protected session; age sources conflict, stale profile patch, class khác scope và duplicate active enrollment bị reject; không suy tuổi từ tranh/AI.
- **Evidence/reviewer:** age boundary/date fixtures, CRUD/assignment/minimization tests, enrollment invalidation history; P1 review roster DTO/labels, P4 review scope migration, P3 review age-context pinning.

#### BE1-05 — School-mediated consent và purpose enforcement

- **Đầu ra:** consent record/evidence reference, verification riêng, amendment/revoke theo purpose; eligibility query port cho drawing/AI/sharing/portfolio và invalidation event. Consent authority workflow không đồng nhất với Teacher role/enrollment; evidence không gửi provider tùy tiện.
- **Phụ thuộc/gate:** BE1-03/04; BE1-02 cho persistence. Purpose taxonomy, authority verification và permissions cần privacy decision; school collection đã chốt, không hỏi lại hoặc tạo Parent portal. H-CLASS-CONSENT có verified/non-effective/revoked fixtures.
- **Truy vết:** FR006, FR029, FR059, FR064; UC-003/038; DATA-05, DATA-35; **CMD-08, CMD-09, CMD-54, CMD-55**; FIX-PRIV-01/02.
- **Nghiệm thu:** positive: recorder tạo pending, delegated verifier xác minh evidence/purpose đúng thẩm quyền rồi effective; revoke một purpose chặn work/access tương ứng và giữ history. Negative: create với verified=true/self-approval, role/enrollment-only, expired consent, AI completion sau revoke không phát artifact; purpose mới qua amendment chưa verified không effective.
- **Evidence/reviewer:** record→verify→amend→revoke transition tests, purpose denial và revoke race receipts; P3 review AI completion contract, P4 review privacy scope, P1 review safe consent status display.

#### BE1-06 — Session configuration, preset snapshot, lobby và explicit Start

- **Đầu ra:** create draft, validate/edit effective config, pinned preset/policy versions, open lobby và Teacher Start. Validate topic/roster/age/tools/groups/consent theo approved policy; giới hạn pilot một lớp tối đa 40 trẻ, phân biệt count trẻ và count thiết bị.
- **Phụ thuộc/gate:** BE1-03/04/05; BE1-02 persistence. H-CONTENT-PRESET cho preset/policy resolve từ P3, fixture thay service thật ở standalone. Chốt tools/mixed-age/phase policy liên quan; preset không preapprove Sketch/video.
- **Truy vết:** FR007, FR010, FR015, FR052–053; UC-004/033; DATA-06, DATA-07, tham chiếu DATA-33 của P3; **CMD-10, CMD-12, CMD-13, CMD-19**.
- **Nghiệm thu:** positive: draft resolve preset thành immutable effective config; Teacher đúng scope explicit Start khi ready, preset update sau đó không sửa active session. Negative: 41 trẻ, lớp đồng thời thứ hai trong pilot policy, unresolved tool/mixed-age hoặc thiếu consent, stale config/start đều blocked; một group ready không Start/advance lớp tự động.
- **Evidence/reviewer:** ready/not-ready fixture matrix, pinned refs/CAS/idempotency results và capacity policy checks; P1 review T03/T04, P3 review preset eligibility, P4 review session lifecycle handoff. Guard count không chứng minh load 40 đã đạt.

#### BE1-07 — QR/mã phiên, pending device và Teacher admission

- **Đầu ra:** possession-bound pending join bootstrap, own pending status, Teacher review/admit/deny; admission transaction bind đúng participants/group/grant/context. QR short-lived locator không chứa identity roster, adult token hoặc durable device grant.
- **Phụ thuộc/gate:** BE1-03/04/05/06; device proof/bootstrap policy adopt qua ADR. H-SESSION-ADMISSION fixture chứa pending/admitted/denied/expired/scope-change.
- **Truy vết:** FR001–003, FR005–006; UC-007/008; DATA-09–DATA-13; **CMD-14, CMD-15, CMD-16**; CS-007/008, FIX-UX-01.
- **Nghiệm thu:** positive: join code hợp lệ chỉ tạo pending; Teacher chọn profiles được phép và admit rồi grant scope mới mở đúng canvas. Negative: pending query roster/canvas/artifact, expired/rate-limited code, stale admission hoặc thiếu consent bị deny; request không chứa child_id/role để tự bind quyền.
- **Evidence/reviewer:** bootstrap/admission/expiry/replay tests, scoped response specimens và audit; P1 review waiting/admission UX, P4 review proof/grant plumbing, P3 review admitted context for AI requests.

#### BE1-08 — Manual groups, progress/help, move và leave

- **Đầu ra:** manual group creation, per-group progress/help updates, transactional participant move/leave; replace/revoke membership/turn grants đúng ảnh hưởng, giữ artwork/contribution lịch sử và quyền những trẻ còn dùng chung thiết bị. Participant leave khác enrollment end.
- **Phụ thuộc/gate:** BE1-06/07/03; future canvas interface H-CANVAS-SYNC fixture cho invalidation; tích hợp canvas thật sau BE1-09/10. Quy tắc move disposition và group limits được adopt trong feature.
- **Truy vết:** FR008–009, FR012, FR016, FR066; UC-005/009/012/014; DATA-08, DATA-12–DATA-14; **CMD-24, CMD-25, CMD-26, CMD-66**.
- **Nghiệm thu:** positive: move tăng membership/grant revisions, nét cũ giữ tác giả; leave một trẻ không revoke toàn tablet làm mất quyền peers; group ready chỉ đổi progress. Negative: source/target stale revision, foreign group/participant, Child advance class hoặc access canvas nhóm cũ sau move bị chặn.
- **Evidence/reviewer:** membership atomicity/race fixtures, before/after grant+contribution set và help/progress state; P1 review T06/C05, P4 review session/group invariants.

#### BE1-09 — Turn attribution và authorized canvas operation log

- **Đầu ra:** canvas metadata, age/Teacher tool policy, active-turn binding, bounded operation validation, dedup/sequence/durable receipts, region locks và append-only attribution correction. Selected contributor không trở thành security principal; own undo/hide dùng compensating operations bảo toàn peer strokes. Các erase/redo/layer/import extensions chưa có closed payload không được enable chỉ bằng tool flag.
- **Phụ thuộc/gate:** BE1-01/02/03/05/08; H-CANVAS-SYNC thống nhất với P1; ADR canvas/sync và closed operation union/undo/region policy cần adopt. Không ép mọi nét phải If-Match document head; control aggregate/turn CAS và operation IDs/epochs riêng.
- **Truy vết:** FR003, FR014–016, FR018–021, FR028, FR066; UC-008/013/014/015/017; DATA-14–DATA-18, DATA-20; **CMD-27, CMD-29, CMD-30, CMD-61**; AT-CS-001–006.
- **Nghiệm thu:** positive: hai valid authors append không mất nét; identical operation retry trả cùng receipt/sequence, đổi lượt chỉ ảnh hưởng nét mới; correction append giữ original source. Negative: foreign contributor/region, old grant/turn/policy epoch, duplicate ID khác payload, points NaN/out-of-range, undo peer hoặc unsafe chunk bị reject mà không ack_saved; AI overlay không biến thành child stroke.
- **Evidence/reviewer:** operation boundary/duplicate/concurrency/turn-switch tests, accepted sequence/hash and immutable lineage, rejected batch receipt; P1 review canvas serialization/render integration, P4 review consistency, P3 review snapshot vs child-layer semantics.

#### BE1-10 — Canvas sync, checkpoints, restore và reconnect recovery

- **Đầu ra:** authorized checkpoint+delta sync, durable checkpoint/snapshot references, controlled restore sang epoch mới giữ provenance, gap replay/dedup và realtime transport adapter nếu ADR chọn. Local unaccepted drafts khác accepted state; presence không thay participant truth.
- **Phụ thuộc/gate:** BE1-02/03/09; H-CANVAS-SYNC version chốt với P1. Offline duration/Teacher-offline và transport details còn gate; standalone dùng clock/network/crash fixtures, runtime phải có persisted adapter.
- **Truy vết:** FR017, FR021, FR060, FR063; UC-014/015/016; DATA-17–DATA-20; **CMD-28, CMD-31**; B19.8/9, API-CS-02; P-NFR-04/05/06.
- **Nghiệm thu:** positive: reconnect fetch checkpoint+delta khôi phục accepted set/hash, gap/delivery duplicate không vẽ thêm; restore tạo epoch mới và preserved lineage. Negative: old-epoch queued ops không auto merge, revoked reader/subscriber không lấy canvas/presence, history-window expiry yêu cầu snapshot; process crash không mất op đã durable ack và không nói pending local đã saved.
- **Evidence/reviewer:** disconnected/out-of-order/gap/restart logs, watermark+checksum before/after và scope-denial matrix; P1 review recovery statuses/transport, P4 review durable/realtime wiring. Đo latency/device profile riêng sau integration, không kết luận SLO từ fixture.

#### BE1-11 — Teacher control, phase transitions và durable finish

- **Đầu ra:** pause/resume/advance/finish handlers với checkpoints, group dispositions, approval refs và truthful saving/recovery_required/completed/ended_early outcomes; manual override thắng stale automation. Kết thúc pin ended_at và retention anchor, không báo completed trước durable save.
- **Session clock application contract:** P2 giao monotonic elapsed-time clock port, durable accumulated intervals/checkpoints và pause/resume/stage accounting theo approved policy/version. Tách session elapsed, stage elapsed và screen-time accounting theo policy; session duration không tự là thời gian từng trẻ nhìn màn hình. UTC started_at/ended_at phục vụ timeline/retention, không lấy client wall clock làm nguồn authoritative cho elapsed. Monotonic clock trong một process kết hợp persisted accumulators khi restart; khoảng thời gian chưa biết do crash/offline phải có explicit uncertainty/recovery disposition theo policy, không reset về 0 hoặc bịa exposure. Emit versioned warning/threshold/Teacher override events và safe clock state qua H-SESSION-CONTROL, dùng projection CMD-11/CMD-59 và existing control routes, không thêm CMD. Proposed clock payload/extension DATA-07 phải adopt trong contract registry, không tự sửa SRS/schema trong task planning này. Consumer là FE-05 và INTG-04/INTG-11.
- **Phụ thuộc/gate:** BE1-06/08/10; H-AI-REVIEW/H-KNOWLEDGE-VIDEO/H-ACTIVITY/H-CONTENT-PRESET cung cấp eligibility/decision refs qua P3 fixtures, runtime sau modules P3 được nối. Return-stage/Teacher-offline/co-teacher details cần gate, không mở ngầm bằng UI back.
- **Clock policy gate:** NFR12 xác nhận screen time phù hợp tuổi và có off-screen; số phút theo band, thời gian pause có tính vào budget nào, visibility/exposure signals, warning cadence và hard-stop đều phải chốt OD11/adopted policy. Clock fixtures dùng named synthetic policies riêng, không hardcode 10 phút hoặc thời lượng video cũ; chưa chốt limit không mặc định vô hạn, tự fail trẻ hoặc auto kết thúc phiên.
- **Truy vết:** FR009–013, FR038–039, FR044, FR052, FR060, FR063; UC-009–011/025–026/028/033; DATA-07, DATA-08, DATA-19; **CMD-20, CMD-21, CMD-22, CMD-23**; AT-CS-005/011/014.
- **Truy vết clock:** NFR12/P-NFR-17, B23.6, OD11; UC-010/028/033; shared DATA-07 effective policy/state và API-CS-03 warning/control events; H-SESSION-CONTROL consumer FE-05, INTG-04, INTG-11.
- **Nghiệm thu:** positive: pause/resume giữ current stage/art, explicit advance cần group dispositions/review; finish retry idempotent tạo terminal durable outcome và anchor end+90 ngày. Negative: video đang generating không auto fallback/skip, unapproved media không advance/play, unfinished group không giả completed; checkpoint failure giữ recovery_required và stale automation không ghi đè Teacher decision.
- **Nghiệm thu clock:** positive: deterministic clock fixture qua draw→pause→resume→video→off-screen tính elapsed/budget đúng named policy, warning có exact policy/version và duplicate delivery không double-count; restart giữ durable elapsed/checkpoint và Teacher override traceable. Negative: chỉnh client UTC/ngày giờ, repeat pause/resume, stale policy/event hoặc process monotonic reset không giảm/tăng sai accumulator; unknown crash/offline exposure hiện unresolved/uncertain; threshold warning không auto stop/fail hoặc đổi stage khi OD11 chưa authorise hành vi đó. Video skip vẫn dẫn tới off-screen nếu phiên tiếp tục hoặc recorded early-end theo P-NFR-17.
- **Evidence/reviewer:** transition/failure/idempotency/automation race tests, terminal save receipts và phase timeline; P3 review media/activity handoffs, P1 review controls/save UX, P4 review cross-module orchestration. Failure disposition endpoint do P3 sở hữu; P2 chỉ consume authorized outcome.
- **Evidence/reviewer clock:** fake-clock transition table, accumulated interval/checkpoint receipts, restart/wall-clock-jump/duplicate-warning traces và consumer payload fixtures; P1 review FE-05 clock/warning/uncertainty display, P4 review INTG-04/INTG-11 measurement/wiring, P3 review media/off-screen accounting boundaries. Không suy màn hình thực tế của trẻ hoặc compliance từ fixture clock.

#### BE1-12 — Scoped read models và mediated artifact delivery

- **Đầu ra:** role-minimized session view, allowlisted read-model gateway, artifact access-ticket application/adapter với exact version/hash/purpose/audience/review/consent revalidation; dashboard/gallery/audit metadata có unavailable/freshness rõ. P3 cung cấp read/eligibility ports cho pending AI/video/jobs/content/catalog/preset; không expose arbitrary queries hoặc raw DB joins.
- **Phụ thuộc/gate:** BE1-03/05/06/02; H-OPERATIONS/H-ADMIN-POLICY và relevant P3 handoff contract fixtures. Runtime media delivery sau actual P3 exact-review port được nối; ticket lifetime/storage delivery mechanism cần ADR/policy.
- **Truy vết:** FR001, FR009, FR019, FR026, FR033, FR036, FR051, FR054, FR057–059, FR063; UC-017/020/024/032/034/037; DATA-01, DATA-07, DATA-20, DATA-35 + delegated P3 data; **CMD-11, CMD-59, CMD-60**; P-NFR-06/07/08/13/16.
- **Nghiệm thu:** positive: Teacher đúng scope có dashboard/group/help/review metadata; admitted Child chỉ lấy eligible approved exact artifact qua backend-mediated handle. Negative: unknown query/filter, pending device roster, Admin monitoring raw content, revoked grant/consent, stale/recalled/unapproved artifact và alternate thumbnail/download bypass đều denied; response/logs không chứa provider/bucket secrets.
- **Evidence/reviewer:** read/subscribe/thumbnail/artifact scope matrix, revoke-between-ticket-and-delivery race, projection contract and redaction tests; P3 review producer eligibility ports, P1 review query states, P4 review gateway composition. P2 là sole owner route; P3 own source projections.

#### BE1-13 — Gallery snapshots, trình bày và chú thích

- **Đầu ra:** gallery publish/order/annotation/present/unpublish trên immutable snapshots, contributor refs và AI-overlay marker; class/session sharing/audience checks cho item, thumbnail và delivery. Child explanation format theo approved policy, không tự bật mic/camera.
- **Phụ thuộc/gate:** BE1-05/09/10/12; H-GALLERY cho P1/P3. Chốt sharing/minimization/age explanation policy; activity/video không thuộc gallery module.
- **Truy vết:** FR019, FR031–033, FR047, FR059; UC-017/022/030; DATA-20, DATA-32; **CMD-37, CMD-65**; FIX-PRIV-03, FIX-UX-07.
- **Nghiệm thu:** positive: Teacher chọn snapshot exact revision, reorder atomic giữ unique published sequence; annotation không sửa art gốc, history cho biết có AI layer. Negative: sharing consent bị revoke, foreign snapshot/audience, stale gallery revision hoặc muốn presenting chưa authorized bị chặn; no private peer data leak.
- **Evidence/reviewer:** snapshot/hash/order/version fixtures và sharing access/consent tests; P1 review C06/T08, P3 review gallery snapshot consumption cho knowledge, P4 review mediated presentation.

#### BE1-14 — Observation, reflection, assessment và portfolio

- **Đầu ra:** Teacher observation/Child own reflection, append corrections/withdrawals, descriptive assessment policy adapter, portfolio compose/annotation/redaction và scoped longitudinal read. Evidence type phân biệt child contribution/direct evidence, Teacher judgement và AI inference; group artifact không tự chứng minh năng lực cá nhân. No ranking/psychology/intelligence inference.
- **Phụ thuộc/gate:** BE1-03/05/10/11/13; H-ACTIVITY/H-AI-REVIEW source refs từ P3; rubric/portfolio retention/source-expiry policy cần adopt. H-ASSESSMENT-PORTFOLIO cho FE; export bundle do BE1-15.
- **Truy vết:** FR011, FR044–050, FR058–060; UC-011/028–031; DATA-19, DATA-20, DATA-30, DATA-31; **CMD-46, CMD-47, CMD-62, CMD-64**; FIX-UX-06, FIX-PRIV-03.
- **Nghiệm thu:** positive: portfolio nối session/process/art/activity/reflection/observation refs có provenance và own-child progress; correction giữ original + reason, chưa quan sát là explicit trạng thái. Negative: Child ghi judgement Teacher/peer reflection, AI tự confirmed assessment, foreign portfolio và report rank peers bị từ chối; source expiry không silently giữ raw copy vô hạn hoặc tạo broken ref mà không disposition.
- **Evidence/reviewer:** evidence taxonomy/permission/correction/source-expiry fixtures, sample synthetic within-child report and cross-child denial; P1 review T11/T12/C09, P3 review AI/activity evidence boundary, P4 review portfolio session-completion wiring.

#### BE1-15 — Retention 90 ngày, export/delete và copy-purge workflow

- **Đầu ra:** lifecycle-request create/status/review actions, authority/scope verification, discovery manifest/lineage, export minimization, inaccessible expiry→purge workflow và per-copy receipts/exceptions. Session/artwork anchor end+90 ngày; portfolio/profile/audit/device/provider/backups có policy riêng. P3 cung cấp provider-copy discovery/purge and stale-job cancel ports; P2 own lifecycle application and core storage purge.
- **Subtask có ranh giới — policy quản trị ngoài AI:** P2 giao domain/application adapter cho organization/purpose/retention policy draft→review→activate/disable/rollback, effective-version query và append-only change audit. H-ADMIN-POLICY core gồm proposed `CorePrivacyPolicyChangeV1Candidate`/policy snapshot, positive/negative fixtures và safe metadata cho A10. Map vào typed policy branch DATA-33/CMD-48: P3 giữ sole router/schema dispatcher, gọi P2 versioned policy port; P3 không ghi policy DB của P2, P2 không tạo route CMD mới. Non-AI policy activation cần đúng capability và review, rollback tạo effective-version decision mới, không sửa provenance hoặc reset ended_at/retention anchor. Default raw session/artwork 90 ngày đã owner-confirmed, không tự rollback thành vô hạn hoặc đổi default; thay quyết định owner cần approval riêng. Portfolio/profile/audit/copy TTL mở chỉ effective sau policy decision, không default theo 90 ngày.
- **Phụ thuộc/gate:** BE1-02/03/05/10/13/14; H-DATA-REQUEST cùng P3/P4. Shared-art deletion, backup/copy retention, authority/exception/request delivery policies phải adopt trước actual purge/pilot; chưa chốt thì policy_review/blocked scope, không xóa peers theo tiện lợi. Test synthetic destructive fixture riêng.
- **Truy vết:** FR006, FR048, FR057–059, FR064; UC-003/031/037/038; DATA-05, DATA-20, DATA-31–DATA-32, DATA-34–DATA-35; **CMD-49, CMD-50, CMD-63**; FIX-PRIV-01–05, P-NFR-12/13.
- **Truy vết policy subtask:** B23 A10, B24, FR059/064; UC-038; shared DATA-33 governance envelope và DATA-35 audit; CMD-48 typed dispatch do P3 primary; H-ADMIN-POLICY core. Cấu hình ngoài AI là phần refinement PROPOSED cần adopt, không mở rộng route catalogue hoặc giao AI policy của BE2-14 cho P2.
- **Nghiệm thu:** positive: verified request chỉ export/delete subject scope, due_at giữ đúng end+90 sau restart; manifest truy tới copies, completed chỉ theo receipts và approved policy. Negative: thiếu authority, peer-owned shared strokes, provider/backup purge pending không báo all-copies-deleted; consent/grant revoke trong export job chặn download; restore không làm dữ liệu đã purge xuất hiện lại.
- **Nghiệm thu policy subtask:** positive: authorized draft/review/activate pin effective version và runtime resolver nhận bản đó; approved rollback giữ prior versions/audit và không reset raw retention anchor. Negative: monitoring-only Admin, author self-activate, unreviewed/unknown policy fields, unresolved copy TTL hoặc version stale bị reject; AI policy branch không được P2 port xử lý và raw90 default không bị client payload tự ghi đè.
- **Evidence/reviewer:** clock-boundary fixtures, authorized export manifest, shared-canvas policy cases, per-store/provider stub+actual receipts được phân biệt, no-resurrection tests; P3 review provider-copy ports, P4 review retention/restore integration, P1 review authority/pending/exception UI. Fake provider purge chỉ chứng minh contract, không completion thật.
- **Evidence/reviewer cho policy:** change/version/activate/rollback fixture traces và CMD-48 dispatch-to-core consumer checks; P3 review typed dispatcher/schema compatibility, P1 review A10 policy states, P4 review effective runtime policy wiring.

#### BE1-16 — Automatic grouping proposal và Teacher commit (Phase 2)

- **Đầu ra:** approved grouping criteria/version, immutable proposal/job result, Teacher review/overrides và atomic commit memberships/current revisions. Thuật toán có explainable bounded inputs được duyệt; không suy tâm lý/năng lực từ tranh và không tự đổi nhóm lúc chưa Teacher commit.
- **Phụ thuộc/gate:** BE1-06/08/03; decision OD18 trước algorithm selection/implementation. Có fixture deterministic ngay khi independent stream; actual automatic grouping là Phase 2 confirmed capability, không gắn status done vào manual grouping pilot.
- **Truy vết:** FR008, FR065; UC-006; DATA-06, DATA-08, DATA-13; **CMD-57, CMD-58**; AT-UC-006-P/N.
- **Nghiệm thu:** positive: proposal dùng pinned roster/criteria, Teacher sửa rồi commit atomic, scopes/grants cập nhật giống manual membership semantics. Negative: child absent/duplicate, stale roster/group revision, unauthorized actor hoặc proposal tự commit bị reject; failed commit không nửa lớp ở nhóm mới/nửa ở nhóm cũ.
- **Evidence/reviewer:** proposal/override/criteria provenance fixtures, stale+atomicity tests và manual parity comparison; P1 review T03/T06, P4 review grouping allocation, P3 review job interface nếu asynchronous.

### P3 — BE2 AI/nội dung

#### BE2-01 — AI/job contract foundation và harness độc lập

- **Reviewer:** P2 review authorization/persistence/outbox boundaries; P1 review job status/error payload; P4 review composition và completion wiring.
- **Phạm vi:** dựng domain job lifecycle và standalone runner cho AI/media; fake clock/provider/queue/artifact/authorization để chạy thành công, lỗi, timeout, cancel và stale result. Đây là đầu ra độc lập đầu tiên của P3, không cần live P2.
- **Giao:** chặng độc lập đầu tiên có schema/payload fixtures DATA-21–29/33, DATA-25 validator, bounded job/attempt state machine, scoped polling handler CMD-44, backend-only completion port, queue/job repository ports và fake adapters; fake provider-copy discovery/purge/receipt fixtures cùng repository port cho BE2-14. **Chặng runtime riêng sau approval** do P3 giao durable DATA-25 job repositories/migrations, attempt/request CAS, dispatch/completion receipts và transactional outbox/queue adapter; job state của P3 không chuyển sang P2/P4 làm thay. Chặng này cần runtime/storage decision và core generic persistence contracts được adopt, không chặn runner độc lập ban đầu hoặc coi fake store là persistent store.
- **Điều kiện trước:** SRS/feature approval; không có dependency live. Numeric retry/budget/progress policy chưa adopt dùng named fixture policy và ghi rõ PROPOSED.
- **Handoff:** `H-OPERATIONS` gồm `JobStatusV1`, typed failure/public message, polling hints, cancellation/completion fixtures; `H-DATA-REQUEST` có provider-copy fake receipt/unsupported/Pending/Exception cases từ contract BE2-14. P4 nhận composition contract; P1 nhận queued/running/retryable/exhausted/cancelled/unknown-progress states.
- **Truy vết:** FR029, FR030, FR037, FR051, FR054; UC-019/025/032; DATA-25; CMD-44; B19.10, B22.3, P-NFR-16.
- **Nghiệm thu dương:** retry cùng semantic request trả một job; job success có exact result refs nhưng không tự thành Teacher approval hoặc session complete; unknown progress giữ unknown. Chặng durable riêng restart sau commit vẫn giữ job/attempt/receipt, outbox dispatch retry không tạo semantic attempt mới và CAS chặn concurrent completion.
- **Nghiệm thu âm:** completion sai attempt/request/context hoặc sau revoke bị stale/rejected; job ngoài scope không lộ artifact/provider internals; cancel không bị late success mở lại.
- **Evidence:** runner command/result, schema fixture report, state-transition table, duplicate/cancellation fault traces đã redaction, adapter contract test. Chặng durable riêng có migration report, actual restart/attempt-CAS/outbox/dispatch fault receipts và adapter tests; fake provider purge chỉ chứng minh contract, chưa chứng minh actual copy deletion.

#### BE2-02 — Tái sử dụng Vision và correction có provenance

- **Reviewer:** P2 review snapshot/consent/version; P1 review meaning/correction projections; P4 review adapter/provider wiring.
- **Phạm vi:** bọc Vision/Qwen transport hiện có vào canvas snapshot + topic + age/context contract mới; nhận object candidates/uncertainty, lưu Teacher/Child correction riêng. Không coi SAM/animation là Sketch generator.
- **Giao:** Vision application port/adapter mapping; source snapshot/version/hash validation; DATA-22 persistence port; CMD-34 correction use case và handler; fake provider cases wrong recognition/low confidence/malformed response.
- **Điều kiện trước:** BE2-01; snapshot/context và authority fixtures từ `H-CANVAS-SYNC`/`H-CLASS-CONSENT`. Adapter thật cần model/profile/serving/license/budget decision và feature approval; chất lượng adapter cũ phải đo lại trên context mới.
- **Handoff:** `H-AI-REVIEW` analysis/correction refs, uncertainty nullable confidence, source revisions và invalidation notice. P1 có projection đúng tuổi; P4 nối provider credentials backend-only.
- **Truy vết:** FR022, FR023, FR061; UC-018; DATA-22; CMD-34; AT-CS-008.
- **Nghiệm thu dương:** snapshot hợp lệ sinh candidate; Teacher/Child đúng scope sửa ý định, original inference và correction/author/reason đều truy vết được.
- **Nghiệm thu âm:** đổi context/snapshot làm result cũ không được authoritative; model không suy tuổi hoặc psychology/intelligence; malformed output thành typed failure, không bịa confidence.
- **Evidence:** synthetic snapshot-to-result/correction fixtures, revision-conflict tests, sanitized provider mapping; real inference report có model revision/profile/input hash khi được duyệt.

#### BE2-03 — Assistance request, cancel, dedup và budget orchestration

- **Reviewer:** P2 review target/turn/purpose scope; P1 review request/cancel/rate feedback; P4 review scheduling/status/completion boundaries.
- **Phạm vi:** Child/Teacher yêu cầu trợ giúp cho cá nhân/nhóm/vùng; current turn và audience validation; queue Vision/Sketch job, debounce/cache/budget, cancel và stale completion.
- **Giao:** DATA-21 command/application service; CMD-32/33 handlers; request repository/idempotency ports; bounded scheduling/budget policy adapter do P3 sở hữu; audit/cancellation events. Idempotency khác payload phải conflict.
- **Điều kiện trước:** BE2-01/02; `H-CLASS-CONSENT`, `H-SESSION-CONTROL`, `H-CANVAS-SYNC` schemas. Real budget/rate/retry parameters phải được adopt; fixture không khóa giá trị production.
- **Handoff:** `H-AI-REVIEW` request status/context/target; `H-OPERATIONS` job/queue/budget status. Nhóm mixed-age kiểm từng audience member, không lấy tuổi trung bình.
- **Truy vết:** FR024, FR025, FR028, FR029, FR030, FR054; UC-019/032; DATA-21/25; CMD-32/33; FIX-UX-04, FIX-NFR-02.
- **Nghiệm thu dương:** request đúng grant/purpose/context tạo một job và Child tiếp tục vẽ; cancel đúng actor lưu outcome, retry duplicate không tăng chi phí semantic.
- **Nghiệm thu âm:** idle riêng lẻ không tạo kết luận thiếu kiến thức/request tự động; request vượt scope/budget hoặc consent thiếu không gọi provider; cache hit/cancel late result không bypass Teacher review.
- **Evidence:** request/cancel/duplicate/cache/stale tests, bounded queue fixture và budget accounting traces; scoped read-model examples cho CMD-59 owner.

#### BE2-04 — Pipeline tạo Sketch thật và output tách tranh gốc

- **Reviewer:** P2 review artifact/source/consent lineage; P1 review output shape/overlay separation; P4 review worker/provider activation and lifecycle hooks.
- **Phạm vi:** năng lực mới tạo reference/question/line-sketch/overlay theo support policy đã chọn. Giữ port độc lập model; fake provider phục vụ contract first, nhưng fake hoặc Vision classifier không đủ nghiệm thu generation thật.
- **Giao:** DATA-23 producer; SketchGenerator port, fake/real adapters, own worker/timeout/cancel handling; output media admission/provenance; separate AI overlay reference và support-level revision. Vision/Sketch provider adapters implement BE2-14 `ProviderCopyLifecycle` hooks: discover input/output/job/cached copies được biết, scoped cancel/purge request, verify receipt/status và unsupported/pending/exception outcome. Output không là command sửa child strokes.
- **Điều kiện trước:** BE2-01/02/03; taxonomy/support modes/output shape và model/profile/license/cost/quality gate được quyết định qua ADR/feature approval. BE2-14 policy ref có thể dùng fixture trước live; không chọn model hoặc SAM bắt buộc trong card.
- **Handoff:** `H-AI-REVIEW` proposal/version/hash/source/context/producer; asset admission dùng `ArtifactReferenceV1` port của P2. `H-DATA-REQUEST` có scoped provider-copy refs và actual/fake-marked lifecycle receipts; P1 chỉ nhận asset/text khi review gate cho phép.
- **Truy vết:** FR019, FR025, FR028, FR029, FR030; UC-017/019; DATA-23, shared DATA-20; backend-only worker port; FIX-UX-04, P-NFR-08.
- **Nghiệm thu dương:** approved real profile tạo được Sketch asset đúng shape từ synthetic source, có provenance và immutable source; result chờ moderation/Teacher review.
- **Nghiệm thu âm:** không thay nét/gán contribution AI cho trẻ; stale/unsafe/malformed/cancelled output không child exposure; quá timeout/budget ghi typed outcome, không loop vô hạn.
- **Evidence:** fake contract report riêng; sau approval có actual generated asset/hash, sanitized provider request/result metadata, decoding/safety/quality review và latency/cost/memory profile; provider-copy lifecycle tests/actual receipt hoặc explicit Unsupported/Pending/Exception. Không đánh dấu real generation hoặc actual purge DONE bằng fixture pass.

#### BE2-05 — Moderation và Teacher duyệt từng Sketch

- **Reviewer:** P2 review eligibility/consent/asset access; P1 review Teacher queue và approved-only Child payload; P4 review gate/invalidation races.
- **Phạm vi:** moderation trước phát nội dung, review queue eligibility; Teacher approve/reject/request_changes đúng từng item/version/hash/audience. Sửa output/support level tạo version mới.
- **Giao:** DATA-24 primary schema/ExactContentReview port; CMD-35; review repository/current-eligibility service; approved-only child projection; review invalidation events; metadata cho P2 artifact-ticket và read-model dispatchers.
- **Điều kiện trước:** BE2-01/04; teaching authority/context fixtures; approved moderation/reviewer policy (BE2-14 cung cấp versioned config). Không đòi live P2 cho fixture tests.
- **Handoff:** `H-AI-REVIEW` review queue item, safe preview cho Teacher, exact approval/ref/state và availability. Các video/library reviews dùng shared DATA-24, không tạo schema khác.
- **Truy vết:** FR026, FR029, FR061; UC-020; DATA-23/24; CMD-35; AT-CS-009.
- **Nghiệm thu dương:** safe exact item được Teacher đúng scope approve, chỉ approved audience nhận được; duplicate approve có một semantic review.
- **Nghiệm thu âm:** pending/rejected/blocked/edited/stale proposal không có child content; preset/system admin không tự approve; Teacher không bypass unsafe gate; If-Match cũ conflict.
- **Evidence:** positive/negative exact-hash review tests, pending-content leakage test qua fetch/cache/subscription/ticket port, invalidation race fixtures, review audit sample.

#### BE2-06 — Child view/hide/decline và tiếp tục vẽ

- **Reviewer:** P2 review bound turn/attribution/revoke; P1 review child agency; P4 review response/artifact integration.
- **Phạm vi:** ghi response theo participant/turn cho approved Sketch; hỗ trợ hide/decline mà giữ child drawing và review history.
- **Giao:** CMD-36 command handler; DATA-23 child-response projection; response idempotency/attribution port; Teacher response event. P1 thực hiện UX/overlay display; P3 chịu authority/domain invariants.
- **Điều kiện trước:** BE2-05; current turn/grant fixtures từ P2. Chính sách xem lại item đã decline nếu muốn cần refinement riêng, không tự refresh gợi ý.
- **Handoff:** `H-AI-REVIEW` available/viewed/hidden/declined payload và projection; explicit overlay visibility state tách canvas operations.
- **Truy vết:** FR019, FR027, FR028; UC-017/021; shared DATA-23/24; CMD-36; P-NFR-08.
- **Nghiệm thu dương:** Child đúng lượt xem rồi hide/decline, response lưu đúng version/author; vẽ tiếp không bị đổi stroke hoặc trừ đánh giá.
- **Nghiệm thu âm:** review/grant bị revoke chặn URL/ref cũ; child response không approve AI sửa tranh; retry không nhân records, decline không ép gọi lại model.
- **Evidence:** turn/revocation/idempotency tests, before/after source hash, UI-facing response fixtures và Teacher event contract checks.

#### BE2-07 — Knowledge có nguồn và script versioning

- **Reviewer:** P2 review audience/source/context refs; P1 review Teacher script/source UI; P4 review downstream version invalidation.
- **Phạm vi:** resolve confirmed topic/meaning, tìm reviewed knowledge, gắn factual claims với nguồn; tách yếu tố tưởng tượng và Teacher corrections; edit script invalidates downstream exact review/results.
- **Giao:** DATA-26; CMD-38/39 handlers; knowledge-source/library ports; bundle version/hash/provenance; source-validation fixtures, script edit and downstream invalidation events.
- **Điều kiện trước:** BE2-01; confirmed context fixtures từ BE2-02/P2; source/content policy refs. Pre-render script approval là proposal cần adopt nếu dùng, không thay mandatory final video approval.
- **Handoff:** `H-KNOWLEDGE-VIDEO` bundle/version/hash/audience/claims/source refs và generation-ready or needs-content-action outcome.
- **Truy vết:** FR034, FR035, FR040; UC-023; DATA-26; CMD-38/39; FIX-GOV-01, AT-CS-010.
- **Nghiệm thu dương:** concept hợp lệ tạo bundle có claim/source/version; Teacher correction tạo phiên bản mới và downstream cũ mất eligibility đúng contract.
- **Nghiệm thu âm:** fantasy không thành science fact; thiếu nguồn trả Teacher content action, không model self-verification; generic content không bị ép fabricated child consent và child-derived content không né purpose checks.
- **Evidence:** claim-source mapping/review report trên synthetic cases, edit/stale tests, imagined/factual separation fixtures, bounded-text validation.

#### BE2-08 — Library resolution và pipeline video generation thật

- **Reviewer:** P2 review artifact storage/consent/source version; P1 review waiting/progress/media shape; P4 review queue/worker/provider/lifecycle wiring.
- **Phạm vi:** reviewed_library/generate/compose_library strategies, exact bundle/audience/profile refs; job/media validation và immutable final artifact. Path generate thật phải có trong backlog, không chỉ DeferredVideo/placeholder.
- **Giao:** DATA-27 producer; CMD-40; VideoGenerator/LibraryResolver/MediaValidator ports; P3 queue/worker/backend provider adapters, cancellation/progress/attempt handling; storage/artifact integration qua P2 port; safe final asset chờ review. Video và optional TTS/media provider adapters implement BE2-14 `ProviderCopyLifecycle` hooks cho input/script/output/cache/job copies, scoped cancel/purge dispatch và actual receipt/verification hoặc explicit Unsupported/Pending/Exception. Narration/TTS chỉ conditional nếu được chọn.
- **Điều kiện trước:** BE2-01/07; adopt policy/rights/content/profile/encoding/audience và final Teacher review cho strategy đã chọn. Model/provider/license/budget/render timeout/retry gates chỉ áp dụng generate hoặc composition có gọi generation/provider. Path reviewed_library không phải chờ generation model decision, vẫn kiểm publication/usage rights, content/profile/encoding/audience và Teacher duyệt exact video trong phiên. Done của toàn card vẫn cần evidence library và real-generation path đã chọn trong scope; fake/placeholder hoặc riêng library pass không hoàn tất nghĩa vụ real generation. Không mặc định Wan, 40–60 giây, L4, narration hoặc một cloud từ lịch sử.
- **Handoff:** `H-KNOWLEDGE-VIDEO` independent generation/review/playback axes; `H-OPERATIONS` truthful progress/job/attempts/public errors; `H-DATA-REQUEST` provider copy refs, scoped cancellation/purge and per-copy receipt/status. P4 nối worker/service config; P3 giao adapters và runner thực hiện.
- **Truy vết:** FR034, FR037, FR038, FR040; UC-023/025; DATA-25/27, shared DATA-20; CMD-40; FIX-UX-05, AT-CS-011.
- **Nghiệm thu dương:** valid generation request tạo actual decodable video có source/profile/hash; library hit cũng chờ per-session Teacher review; queued/running vẫn ở waiting stage.
- **Nghiệm thu âm:** placeholder hoặc fixture không được báo generated; unsafe/stale/recalled result bị chặn; timeout không auto fallback/skip/play; progress unknown không bịa percentage.
- **Evidence:** fake path tests riêng; sau approval có sanitized actual render/decoder/quality record và cost/latency/profile; worker retry/cancel/restart evidence khi durable adapters đã implement; lifecycle per-copy actual receipt/verification hoặc outstanding status. Stub deletion không được coi actual provider purge complete.

#### BE2-09 — Final video review và authorized playback

- **Reviewer:** P2 review session/audience/mediated asset authority; P1 review review/playback states; P4 review exact-hash delivery chain.
- **Phạm vi:** Teacher kiểm/chỉnh/reject final artifact đúng exact version/hash và audience; playback chỉ với effective review + current session/grant/consent/content eligibility.
- **Giao:** CMD-41/42; DATA-24 session_content review integration; DATA-27 playback lifecycle, capability validation và metadata cho mediated access port. Library publication review không thay Teacher approval trong phiên.
- **Điều kiện trước:** BE2-08 và **shared DATA-24 exact-content review contract/schema fixtures của BE2-05**, không cần real Sketch generation hoặc live Sketch-review service. Reviewed-library video có thể được triển khai/verify độc lập path Sketch. Session advance/access port contract của P2; video content/profile review policy. Chỉnh script/media tạo version mới và render/review lại theo scope.
- **Handoff:** `H-KNOWLEDGE-VIDEO` ready_for_review/approved/playing/rejected/stale fixtures, playback intent/result và exact review refs. Không phát bucket/provider credentials hoặc raw permanent URL.
- **Truy vết:** FR035, FR036, FR040; UC-024; DATA-24/27; CMD-41/42; AT-CS-010.
- **Nghiệm thu dương:** Teacher approve final exact artifact rồi start playback cho authorized audience; review revision khác run/job/session revisions được kiểm đúng.
- **Nghiệm thu âm:** generic published video vẫn không play khi chưa session Teacher review; edit/audience/context/revoke làm review không còn hiệu lực; stale ETag hoặc URL cũ không bypass gate.
- **Evidence:** final-hash/review-axis tests, library-vs-session review fixtures, unauthorized/stale playback tests qua access port, public playback error samples.

#### BE2-10 — Video exhausted failure: Teacher retry/skip/end

- **Reviewer:** P2 review stage/finish/checkpoint outcomes; P1 review Teacher disposition UI; P4 review cross-module receipts/atomicity.
- **Phạm vi:** sau các automatic retries được phép thất bại, Teacher explicit disposition; history giữ prior failure và budget decision. Khi còn queued/running vẫn chờ.
- **Giao:** DATA-28; CMD-43; disposition repository/service; retry-new-run command và session-end/skip port invocation cho P2, durable outcome events; bounded manual-retry authorization.
- **Điều kiện trước:** BE2-01/08; adopted retry/budget policy và versioned session command port. Không gọi trực tiếp session DB; orchestration phối hợp receipt/outbox/idempotency theo integration decision.
- **Handoff:** `H-KNOWLEDGE-VIDEO` failed_exhausted + permitted Teacher actions; `H-SESSION-CONTROL` explicit skipped_by_teacher/session_ended_early intent/result, không giả stage success.
- **Truy vết:** FR038, FR039; UC-025/026; DATA-25/27/28; CMD-43; AT-CS-011.
- **Nghiệm thu dương:** Teacher chọn retry tạo bounded new attempt/run, skip ghi disposition, end ghi early outcome và đòi checkpoint receipt; duplicate action không lặp side effect.
- **Nghiệm thu âm:** Child không disposition; running job trả VIDEO_NOT_EXHAUSTED; skip không generated/succeeded; retry không tạo human approval hoặc vô hạn budget.
- **Evidence:** all-three-actions tests, lifecycle/race/duplicate fixtures, cross-module failure-compensation receipt tests và disposition audit record.

#### BE2-11 — Activity discovery, adaptation và execution

- **Reviewer:** P2 review session/portfolio/source handoff; P1 review activity preparation/instructions; P4 review off-screen assignment/result wiring.
- **Phạm vi:** reviewed activity library/recommendation candidate, Teacher select/adapt cho lớp/nhóm; age/safety/preparation trước execution; select/confirm_ready/start/finish/skip/interrupt lifecycle.
- **Giao:** DATA-29; CMD-45; catalog/recommendation adapter mapping reuse existing full topic/exact-age discovery as **candidate**; immutable effective assignment snapshot; objective/source versions, reason and evidence refs; event để P2 nối reflection/portfolio.
- **Điều kiện trước:** BE2-01; catalog/content fixtures và publication lifecycle BE2-12; adopt age-compatibility/safety/material/prerequisite policy khi triển khai. Existing preference-ranking/no-readiness-filter policy không tự trở thành confirmed new scope.
- **Handoff:** `H-ACTIVITY` scoped catalog/recommendation projection provider cho CMD-59, assignment/actions/feasibility state và off-screen outcome refs. P2 primary CMD-46/47 giữ observation/reflection/portfolio; P3 không tự ghi các tables đó.
- **Truy vết:** FR041, FR042, FR043; shared FR044; UC-027/028; DATA-29, shared DATA-33; CMD-45; FIX-UX-06.
- **Nghiệm thu dương:** Teacher chọn rồi chỉnh local assignment, xác nhận khả thi/an toàn theo policy, start/finish đúng version và gửi result refs; không sửa master catalog ngầm.
- **Nghiệm thu âm:** mixed-age eligibility kiểm từng audience theo approved policy, hazardous/unprepared assignment không start; discovery không thêm readiness/history/material hard filters chưa adopt; reflected result không giả Teacher observation.
- **Evidence:** catalog parity/adaptation/age/safety/preparation tests, action-state matrix và immutable-source hashes; cross-module observation handoff fixture.

#### BE2-12 — Content authoring, publication review và recall

- **Reviewer:** P2 review authority/consent/recall eligibility; P1 review author/reviewer/publisher states; P4 review dispatcher/publication/consumer boundaries.
- **Phạm vi:** generic library content/activity/video draft→submit→changes/review→publish→recall/archive. P3 primary CMD-48 closed-union dispatcher và DATA-33 shared schema; preset/policy branches do BE2-13/14 giao use case adapters.
- **Giao:** content version repository/port, CMD-48 router/typed action validator; exact safety/pedagogical generic_library review integration DATA-24; independent author/reviewer/publisher authority checks; recall eligibility event/cancellation notice và consumer fixtures.
- **Điều kiện trước:** BE2-01/05 schema contracts; publication/reviewer separation/recall policy phải adopt trước runtime. BE2-05 implementation không phụ thuộc BE2-12 live; sử dụng DATA-24 fixture để tránh integration cycle.
- **Handoff:** `H-CONTENT-PRESET` immutable published record/ref/hash/review set/recall event; `H-CLASS-CONSENT` eligibility query khi child-derived content; new-session resolver blocking cho P2/P3.
- **Truy vết:** FR056, FR062; UC-035; DATA-33, shared DATA-24/35; CMD-48; FIX-GOV-01.
- **Nghiệm thu dương:** generic authored content có safety/pedagogical approvals đúng exact version và publisher capability mới publish; recall chặn phiên mới, history còn provenance.
- **Nghiệm thu âm:** author không tự publish, edit không giữ approval cũ; generic library review không yêu cầu fabricated session/child consent, child-derived classification không né policy. Active-copy deletion/replacement không tự invent khi OD05 còn mở.
- **Evidence:** full action union tests, author/reviewer/publisher separation fixtures, generic-vs-session review cases, recall/new-session tests và version/audit history.

#### BE2-13 — Preset versioning, conditional automation và Teacher override

- **Reviewer:** P2 review current session/config command guards; P1 review preset/override UI; P4 review automation intent/receipt wiring.
- **Phạm vi:** preset library versions và pinned session config; conditional automation suggestions/commands revalidated trước effect; Teacher override wins trong authority hợp lệ. P2 owns effective session/config mutation; P3 không có session DB access.
- **Giao:** preset branch use cases cho CMD-48 dispatcher BE2-12; DATA-33 preset validation; automation evaluator/scheduler port, versioned command intents/receipt/stale outcomes, queue priority policy adapter nếu được adopt.
- **Điều kiện trước:** BE2-01/12; `H-SESSION-CONTROL` command/config contract; adopt preset field/condition/priority/override rules. Fixture stream dùng fake command handler, không chờ live orchestration.
- **Handoff:** `H-CONTENT-PRESET` pinned preset snapshots và automation/override records; `H-SESSION-CONTROL` scoped intent có observed config/stage versions; `H-OPERATIONS` deferral/overload/public status.
- **Truy vết:** FR052, FR053, FR054; UC-032/033; DATA-33, shared DATA-06/35; CMD-48 typed preset branch; P2 CMD-12/59 integration; FIX-GOV-01, P-NFR-16.
- **Nghiệm thu dương:** draft session dùng pinned preset; Teacher override/disable thay effective config qua P2 port và queued old-version action bị stale, có reason/audit.
- **Nghiệm thu âm:** edit preset library không đổi active session; automation không bỏ per-Sketch/final video approval, consent/safety hoặc auto-complete/purge; queue overflow không autoapprove/drop silent.
- **Evidence:** policy-condition fixtures, override/cancellation race tests, command receipt/dedup checks, config-pin hash và consumer contract examples.

#### BE2-14 — System AI configuration, limits và kill switch

- **Reviewer:** P2 review data-lifecycle authority/copy manifest; P1 review scoped Admin/exception status; P4 review policy/provider-copy wiring and receipts.
- **Phạm vi:** authorized Super Admin draft/validate/publish/disable allowlisted policy/model-profile refs, moderation/retry/budget/concurrency; pinned request/attempt provenance; emergency block/cancel/revalidate.
- **Giao:** AI-policy branch adapter cho CMD-48/BE2-12; DATA-33 policy validation/version repository; policy eligibility/budget port; backend-only provider profile resolution, kill-switch cancellation events; redacted health/queue/cost projections qua H-OPERATIONS. P3 primary owner versioned **`ProviderCopyLifecycle`** contract/registry: scoped discovery, cancel, purge dispatch, receipt verification, per-copy status và Unsupported/Pending/Exception reasons; request/receipt idempotency, current authority/source-expiry checks và no-late-result exposure. BE2-01 giao fake/repository support; BE2-04/08 giao provider-specific hooks. P2 giữ lifecycle application/request authority và core-storage purge; P4 nối ports, không làm thay provider adapters.
- **Điều kiện trước:** BE2-01/12; Admin capability contract; provider/model/queue/deployment/config values phải có ADR/evidence và approved feature trước activation. Card không nâng dependencies/cloud hoặc chọn provider tự động.
- **Handoff:** `H-ADMIN-POLICY` allowlisted effective version/config metadata; `H-OPERATIONS` safe metrics/log/trace contract cho P4 wiring/CMD-59 projection; **`H-DATA-REQUEST`** copy discovery manifest/cancel-purge command/receipt/status/exception cho BE1-15 và INTG-08. Tokens, keys, endpoint secrets ở runtime backend, không policy DTO/mobile/logs.
- **Truy vết:** FR029, FR030, FR054, FR056; UC-036/037; DATA-33/25, shared DATA-35; CMD-48 typed policy branch; FIX-GOV-01, P-NFR-13.
- **Nghiệm thu dương:** publish policy v2 làm new requests pin phiên bản mới; prior requests giữ source version và check current eligibility; disable chặn work mới và disposition pending jobs traceable. Authorized lifecycle request discover được known provider copies, dispatch cancel/purge idempotent và trả exact per-copy receipts để P2 cập nhật manifest.
- **Nghiệm thu âm:** config bypass mandatory Teacher review/consent/unsafe gates bị reject; secret hoặc unallowlisted profile không vào public payload; role Admin không tự teaching approval/raw-child access. Provider không hỗ trợ purge/receipt chưa verify/ongoing copies phải Unsupported/Pending/Exception, không fake Deleted/complete; late completion sau revoke/expiry không resurrect artifact.
- **Evidence:** policy compatibility/allowlist/kill-switch tests, redaction samples, request-version/cancellation faults; ProviderCopyLifecycle conformance/discovery/duplicate/cancel/purge/unsupported/exception/no-resurrection fixtures; actual provider receipts tách riêng fake results. Real cost/load/provider reports chỉ khi approved measurement profile đã chạy; fake purge pass chưa là actual deletion completion.

### P4 — tích hợp

#### INTG-01 — Bộ fixture tích hợp và sổ contract dùng chung

- **Owner/reviewer:** P4; P2/P3 review payload/domain, P1 review UI states.
- **Đầu ra:** registry contract candidate và version; fixture manifest synthetic/hash; sơ đồ request/event/error; fake adapters và runner kiểm tra đường nối bằng dữ liệu giả; trace SRS→task→evidence.
- **Phụ thuộc:** không phụ thuộc live service hoặc task của người khác. Dùng SRS/fixture tự tạo có provenance; sau đó đối chiếu output FE-01/BE1-01/BE2-01 ở checkpoint review, không làm ba task đó phải chờ P4.
- **SRS:** B19/B21/B22/B26, NFR04/10/11; source AC01–18.
- **Đạt:** fixture hợp lệ đi qua fake boundaries với đúng IDs/hash/version và hiển thị đúng state; fixture payload sai/unknown fields/stale review bị reject tại boundary tương ứng. Runner chạy độc lập trên máy local, không cần Firebase/provider/database thật.
- **Evidence:** manifest, runner command/results, compatibility diff và danh sách contract còn PROPOSED. Lỗi fixture không được gọi là chất lượng model hoặc tải pilot.

#### INTG-02 — Composition root và điểm vào backend/worker

- **Owner/reviewer:** P4; P2/P3 review dependency direction và adapter ownership.
- **Đầu ra:** wiring ở composition root đã được feature approve; API routes/app use cases/repository/auth/queue/artifact/provider adapters được inject qua ports; worker entrypoints; health/readiness có semantics.
- **Phụ thuộc:** INTG-01; foundation contract packs FE-01/BE1-01/BE2-01 được cross-review; runtime/adapters cần dùng do P2/P3 bàn giao; ADR cho các lựa chọn bắt buộc đã được chốt.
- **SRS:** B3/B8/B19.3/B22.3; FR001/005/017/030/059/060; NFR10.
- **Đạt:** request/job fixture vào đúng use case/port, worker completion đi qua application guards, startup thiếu cấu hình bắt buộc báo rõ; không import FastAPI/ORM/provider SDK vào domain. Missing durable adapter không được báo production-ready bằng fake/in-memory adapter.
- **Evidence:** composition diagram, startup commands, architecture check, adapter/config manifest với placeholders. P2/P3 sửa logic/adapters thiếu; P4 nối và xác nhận hợp đồng.

#### INTG-03 — Kết nối Child Android, Teacher và Admin với API

- **Owner/reviewer:** P4; P1 review UI lifecycle, P2 review auth/resource scope.
- **Đầu ra:** transport/API client connectors dùng contract đã adopt; authenticated identity context; join/admission/refresh; error mapping và cancellation/loading states; cấu hình backend address runtime.
- **Phụ thuộc:** INTG-02; H-IDENTITY, H-CLASS-CONSENT, H-SESSION-ADMISSION; các UI corresponding từ P1. UI development vẫn dùng local fixtures trước handoff.
- **SRS:** FR001–007/055/058/066; C01/C02/T01/T02/T03/T04/A02/A03; UC-001–004/007/008/034.
- **Đạt:** Teacher login rồi mở đúng lớp, tablet pending được admit rồi mới nhận projection/grant; sai lớp/mã hết hạn/suspended user/revoked grant không mở roster/media. Không dùng X-Actor-Ref demo làm xác thực thật; mobile không chứa provider/bucket credentials/endpoints.
- **Evidence:** request/response redacted traces, join/token lifecycle test, fixture-vs-authenticated mode manifest.

#### INTG-04 — Nối canvas realtime, lượt vẽ và recovery

- **Owner/reviewer:** P4; P1 về renderer/input, P2 về authorization/log/checkpoint.
- **Đầu ra:** connector giữa canvas editor và accepted-operation API/stream; subscription/delta/checkpoint; turn/pause/region-policy propagation; local-draft reconciliation và reconnect.
- **Subtask Phase 2 có gate:** sau OD18/grouping policy được adopt và BE1-16 bàn giao, nối proposal → Teacher xem/override → commit group memberships/CAS → FE roster/grant refresh; chưa có decision không bật automatic grouping. Không sửa membership bằng direct DB; manual grouping path của pilot chạy riêng trước extension.
- **Phụ thuộc:** INTG-03; H-CANVAS-SYNC, H-SESSION-CONTROL; P1 canvas implementation/P2 drawing adapters; OD08/15 và recovery policies được adopt.
- **SRS:** FR003/009/010/014–019/021/060/063/066; UC-008–010/013–017; AT-CS-001–007.
- **Đạt:** hai client giữ đủ authorized accepted strokes và original contributor; retry ack mất không nhân đôi, switch không relabel stroke cũ; lock/revoke/restore epoch khi offline không bị buffered replay bypass. UI phân biệt on-device/sending/accepted/rejected.
- **Đạt Phase 2:** Teacher commit đúng reviewed proposal và current roster revisions tạo một atomic membership outcome; duplicate commit không chia lại nhóm, stale roster/unauthorized override bị reject không áp proposal nửa chừng. Nối thực sau feature approval, không gọi extension complete bằng flag tắt.
- **Evidence:** operation IDs/sequence/checksum, disconnect/crash/replay logs và device input traces. Bugs engine thuộc P1, bugs domain/persistence thuộc P2.

#### INTG-05 — Nối snapshot → Vision → Sketch → Teacher review → Child

- **Owner/reviewer:** P4; P3 về job/model/review, P2 về source/purpose/scope, P1 về child agency.
- **Đầu ra:** snapshot/provenance handoff, source/context versions, async status/review queue, artifact delivery và child responses; cancellation/stale-result wiring.
- **Phụ thuộc:** INTG-04; H-AI-REVIEW, H-OPERATIONS; P3 assistance/review adapters; P1 C04/T07.
- **SRS:** FR019/022–030/061; UC-017–021; AT-CS-008/009/012.
- **Đạt:** proposal đúng snapshot/context, Teacher duyệt từng item trước Child access; trẻ hide/decline vẫn giữ nét. Pending/unsafe/stale/revoked result không tải được bằng direct artifact ID; cancellation không bị delayed completion resurrect.
- **Evidence:** graph source/result/review/version/hash; positive/negative delivery probes; worker attempts và purpose decisions. Real Sketch chất lượng phải có P3 benchmark riêng, không chỉ mock screenshot.

#### INTG-06 — Nối gallery → knowledge → video → playback và failure controls

- **Owner/reviewer:** P4; P3 media/content, P2 session/gallery, P1 T08/T09/C06/C07.
- **Đầu ra:** pinned gallery snapshots/meaning → knowledge bundle → library/render → safety/Teacher review → authorized playback; wait/progress/failure choice và session-stage wiring.
- **Phụ thuộc:** INTG-03/INTG-04; H-GALLERY, H-KNOWLEDGE-VIDEO, H-SESSION-CONTROL; exact-review/audience và confirmed-meaning contracts. Chỉ consume shared review/snapshot contracts của nhánh AI khi cần; INTG-05 và actual Sketch generation không là prerequisite để gallery/video chạy. Teacher có thể xác nhận meaning mà trẻ không yêu cầu Sketch.
- **SRS:** FR031–040; UC-022–026; AT-CS-010/011.
- **Đạt:** chạy được cả path không yêu cầu Sketch lẫn path có Sketch đã duyệt; chỉ exact approved artifact/version/audience được chiếu; generating phải chờ, hết retries chỉ Teacher retry/skip/end; skip ghi disposition và phiên tiếp tục vẫn đi off-screen. Edited script/video/library version hoặc revoked consent không được approval cũ authorize.
- **Evidence:** job/video/review/session histories, bytes hash/playback traces, slow/failure fixtures; model-generated clip riêng và reviewed-library fixture riêng. Placeholder không là real generation.

#### INTG-07 — Nối hoạt động, reflection, assessment, portfolio và kết thúc phiên

- **Owner/reviewer:** P4; P3 activity/content, P2 learning records/finish, P1 C08/C09/T10–T12.
- **Đầu ra:** class/group activity assignment, preparation checks, off-screen signals, observation/reflection, durable completion/portfolio handoff và UI kết quả.
- **Phụ thuộc:** INTG-06; H-ACTIVITY, H-ASSESSMENT-PORTFOLIO; P2/P3 module outcomes; age/rubric/portfolio policy decisions cần cho scope được adopt.
- **SRS:** FR009–013/041–050; UC-009–012/027–031; AT-CS-014.
- **Đạt:** nhóm tiến độ riêng và assessment có attribution/evidence; group note không tự thành judgement từng trẻ; finish chỉ completed khi records durable. Missing material/safety confirmation hoặc save partially fails giữ state/recovery rõ; không rank/diagnose trẻ, NOT_OBSERVED không thành thiếu năng lực.
- **Evidence:** full outcome graph/history/portfolio IDs/hash, incomplete-group/save-failure tests. P4 wire event/port, không tự ghi DB module khác để ghép kết quả.

#### INTG-08 — Nối Admin, consent, content recall và data lifecycle xuyên hệ thống

- **Owner/reviewer:** P4; P2 privacy/auth/data lifecycle, P3 content/provider copies, P1 Admin/consent UI.
- **Đầu ra:** consent/revoke propagation tới UI/subscriptions/queue/artifact delivery; library publication vs teaching review; export/delete discovery, device/provider/backup-copy statuses và no-resurrection probes.
- **Phụ thuộc:** INTG-03/05/07; H-CLASS-CONSENT, H-CONTENT-PRESET, H-ADMIN-POLICY, H-DATA-REQUEST; policies/authority và provider-copy contracts của scope tương ứng.
- **SRS:** FR006/052–059/061/062/064; UC-003/033–038; FIX-PRIV-01–05/FIX-GOV-01.
- **Đạt:** recorder tạo pending consent, delegated verifier mới quyết định; expiry 90 ngày session/art không được portfolio link kéo dài raw source. Sai authority/shared export/partial provider purge không báo hoàn tất hoặc leak peer data; restore áp deletion ledger trước exposure.
- **Evidence:** synthetic copy discovery manifests/per-copy outcomes, redacted access/audit traces, expired/recalled/late-completion tests. Portfolio/profile/audit TTL chưa chốt vẫn là decision gate.

#### INTG-09 — Bộ kiểm thử tích hợp chín bước và quản lý lỗi theo owner

- **Owner/reviewer:** P4 điều phối suite; P1/P2/P3 sở hữu kiểm thử/sửa lỗi component.
- **Đầu ra:** runnable integrated synthetic E2E nine-step flow và SRS INT-01–12 fault variants; failure triage theo module/contract/UI; reusable setup/cleanup.
- **Phụ thuộc:** INTG-04–08, module tests của P1/P2/P3; approved integrated fixtures/contracts.
- **SRS:** AC01–18, B26.4, NFR02–05/07/10.
- **Đạt:** complete path có và không có yêu cầu Sketch, plus shared-device/group-speed/network/unsafe/stale/video-failure/revoke/save-failure/copy-purge branches; failed checks có reproducible fixture và owner fix. Không báo video/AI/device quality đạt vì stub provider pass; không dùng screenshot làm bằng chứng server permission.
- **Đạt Phase 2 sau OD18:** integrated grouping proposal/review/override/atomic-commit probes với duplicate request, stale roster và grant-refresh fault; không làm Phase 2 thành prerequisite của manual grouping pilot. Evidence extension tách riêng để deferred criteria không bị báo verified.
- **Evidence:** run ID/config/fixture hashes/result matrix, failure traces, regression after owner fix. Test evidence lưu ở owning integration feature, component evidence giữ ở feature component.

#### INTG-10 — Môi trường chạy chung, config và quan sát hệ thống

- **Owner/reviewer:** P4 wiring; P2 data/auth/storage adapters, P3 AI/worker/provider adapters.
- **Đầu ra:** reproducible local/integration startup và process wiring cho chosen stack; environment schema với placeholders; readiness; redacted logs/metrics/trace correlation và queue/save/permission failure visibility.
- **Phụ thuộc:** INTG-02; H-OPERATIONS/H-ADMIN-POLICY; accepted runtime/DB/queue/storage/model/web decisions và các adapters P2/P3.
- **SRS:** FR030/054/057/059; NFR08–11; B8/B22/B24.
- **Đạt:** clean environment chạy theo README với secrets cung cấp ở ignored/runtime store, thiếu adapter/secret báo an toàn; telemetry không chứa names/raw media/prompt/token/QR/signed URL. Firebase Authentication-only, mọi AI/storage qua backend ports.
- **Evidence:** config/runbook/health checks/sentinel redaction results và architecture/security checks. Provision/deploy thật cần authorization riêng; P4 không tự chọn cloud/DB/queue để lấp gate.

#### INTG-11 — Xác nhận hệ thống ở tải pilot và tổng hợp device/model evidence

- **Owner/reviewer:** P4 test orchestration/report; P1 Android/UI, P2 load/durability/security, P3 model/jobs/media evidence.
- **Đầu ra:** measured integrated profile một lớp tối đa 40 participant; phân biệt device connections/group/job load; aggregate device/model/network/run manifests; candidate NFR outcomes/deviations.
- **Phụ thuộc:** INTG-09/10; adopted device/model/network/quality thresholds; per-component benchmarks từ đúng owner.
- **SRS:** owner pilot target, B25 MP-01–05/P-NFR-01–17; NFR01–12.
- **Đạt:** report sample counts/percentiles/errors/actual versions/network/resources; accepted data set còn nguyên khi process restart. Fake provider result không lẫn real GPU latency/cost/quality; target 40 trẻ chưa chứng minh nếu chỉ 40 idle logins.
- **Evidence:** load/operation traces/checksums, pinned Android/model/provider evidence, capacity bottlenecks và owner remediation list. Real classroom/child data vẫn cần school consent/process approval riêng.

#### INTG-12 — Bàn giao hệ thống, demo và hồ sơ kỹ thuật

- **Owner/reviewer:** P4 tổng hợp; cả P1/P2/P3 xác nhận phần sở hữu.
- **Đầu ra:** build/run instructions, approved contract/ADR list, architecture/ER/API docs synchronized with actual code, integrated demo script và verification report; APK/test artifact theo approved release plan nếu scope có.
- **Phụ thuộc:** INTG-09–11; completeness của module backlog và decision register; approved distribution/visual/content/security gates.
- **SRS:** full M01–14/FR001–066, B15/B26; repo governance.
- **Đạt:** người khác chạy được theo tài liệu và thấy đầy đủ learning loop; chỉ đánh dấu requirements VERIFIED khi evidence thực tế có. Deferred/PROPOSED/TBD chưa được gọi là complete; toàn bộ confirmed modules vẫn visible trong backlog. Không đưa secrets/real child data/external originals vào repo hoặc release bundle.
- **Evidence:** handover checklist/module ownership sign-off/traceability/report, security/harness results, artifact hashes và release deviations. Commit/push/deployment không được task planning này cấp phép.

## 8. Ownership API, logical data và UI

Các CMD/DATA/UI dưới đây là logical contract/responsibility IDs của SRS, không khẳng định đã có physical endpoint/table/screen. Mỗi ID có **một primary maintainer**; task khác consume/version-review behavior.

### 8.1. 66 CMD — primary route owner

<!-- CMD-OWNERS-BEGIN -->
| CMD | Primary task | Người |
|---|---|---|
| CMD-01 | BE1-04 | P2 |
| CMD-02 | BE1-04 | P2 |
| CMD-03 | BE1-04 | P2 |
| CMD-04 | BE1-04 | P2 |
| CMD-05 | BE1-04 | P2 |
| CMD-06 | BE1-04 | P2 |
| CMD-07 | BE1-03 | P2 |
| CMD-08 | BE1-05 | P2 |
| CMD-09 | BE1-05 | P2 |
| CMD-10 | BE1-06 | P2 |
| CMD-11 | BE1-12 | P2 |
| CMD-12 | BE1-06 | P2 |
| CMD-13 | BE1-06 | P2 |
| CMD-14 | BE1-07 | P2 |
| CMD-15 | BE1-07 | P2 |
| CMD-16 | BE1-07 | P2 |
| CMD-17 | BE1-03 | P2 |
| CMD-18 | BE1-03 | P2 |
| CMD-19 | BE1-06 | P2 |
| CMD-20 | BE1-11 | P2 |
| CMD-21 | BE1-11 | P2 |
| CMD-22 | BE1-11 | P2 |
| CMD-23 | BE1-11 | P2 |
| CMD-24 | BE1-08 | P2 |
| CMD-25 | BE1-08 | P2 |
| CMD-26 | BE1-08 | P2 |
| CMD-27 | BE1-09 | P2 |
| CMD-28 | BE1-10 | P2 |
| CMD-29 | BE1-09 | P2 |
| CMD-30 | BE1-09 | P2 |
| CMD-31 | BE1-10 | P2 |
| CMD-32 | BE2-03 | P3 |
| CMD-33 | BE2-03 | P3 |
| CMD-34 | BE2-02 | P3 |
| CMD-35 | BE2-05 | P3 |
| CMD-36 | BE2-06 | P3 |
| CMD-37 | BE1-13 | P2 |
| CMD-38 | BE2-07 | P3 |
| CMD-39 | BE2-07 | P3 |
| CMD-40 | BE2-08 | P3 |
| CMD-41 | BE2-09 | P3 |
| CMD-42 | BE2-09 | P3 |
| CMD-43 | BE2-10 | P3 |
| CMD-44 | BE2-01 | P3 |
| CMD-45 | BE2-11 | P3 |
| CMD-46 | BE1-14 | P2 |
| CMD-47 | BE1-14 | P2 |
| CMD-48 | BE2-12 | P3 |
| CMD-49 | BE1-15 | P2 |
| CMD-50 | BE1-15 | P2 |
| CMD-51 | BE1-03 | P2 |
| CMD-52 | BE1-03 | P2 |
| CMD-53 | BE1-03 | P2 |
| CMD-54 | BE1-05 | P2 |
| CMD-55 | BE1-05 | P2 |
| CMD-56 | BE1-04 | P2 |
| CMD-57 | BE1-16 | P2 |
| CMD-58 | BE1-16 | P2 |
| CMD-59 | BE1-12 | P2 |
| CMD-60 | BE1-12 | P2 |
| CMD-61 | BE1-09 | P2 |
| CMD-62 | BE1-14 | P2 |
| CMD-63 | BE1-15 | P2 |
| CMD-64 | BE1-14 | P2 |
| CMD-65 | BE1-13 | P2 |
| CMD-66 | BE1-08 | P2 |
<!-- CMD-OWNERS-END -->

### 8.2. 35 DATA — primary schema/semantics maintainer

DATA-04 assignment behavior thuộc BE1-03 nhưng schema BE1-04; DATA-07 lifecycle BE1-11 nhưng schema BE1-06; DATA-12 admission producer BE1-07 nhưng schema BE1-03. DATA-20 generic asset/snapshot schema BE1-10, core storage adapter BE1-02; P3 giữ derived-artifact provenance/eligibility. DATA-24 BE2-05 là shared exact review contract, publication/teaching có purpose riêng. DATA-25 durable AI jobs/adapters BE2-01 do P3 giao, không đẩy sang P2/P4. DATA-35 audit schema BE1-03, append persistence BE1-02; mọi producer emit qua versioned port.

<!-- DATA-OWNERS-BEGIN -->
| DATA | Primary task | Người |
|---|---|---|
| DATA-01 | BE1-03 | P2 |
| DATA-02 | BE1-04 | P2 |
| DATA-03 | BE1-04 | P2 |
| DATA-04 | BE1-04 | P2 |
| DATA-05 | BE1-05 | P2 |
| DATA-06 | BE1-06 | P2 |
| DATA-07 | BE1-06 | P2 |
| DATA-08 | BE1-08 | P2 |
| DATA-09 | BE1-07 | P2 |
| DATA-10 | BE1-07 | P2 |
| DATA-11 | BE1-07 | P2 |
| DATA-12 | BE1-03 | P2 |
| DATA-13 | BE1-08 | P2 |
| DATA-14 | BE1-09 | P2 |
| DATA-15 | BE1-09 | P2 |
| DATA-16 | BE1-09 | P2 |
| DATA-17 | BE1-09 | P2 |
| DATA-18 | BE1-09 | P2 |
| DATA-19 | BE1-10 | P2 |
| DATA-20 | BE1-10 | P2 |
| DATA-21 | BE2-03 | P3 |
| DATA-22 | BE2-02 | P3 |
| DATA-23 | BE2-04 | P3 |
| DATA-24 | BE2-05 | P3 |
| DATA-25 | BE2-01 | P3 |
| DATA-26 | BE2-07 | P3 |
| DATA-27 | BE2-08 | P3 |
| DATA-28 | BE2-10 | P3 |
| DATA-29 | BE2-11 | P3 |
| DATA-30 | BE1-14 | P2 |
| DATA-31 | BE1-14 | P2 |
| DATA-32 | BE1-13 | P2 |
| DATA-33 | BE2-12 | P3 |
| DATA-34 | BE1-15 | P2 |
| DATA-35 | BE1-03 | P2 |
<!-- DATA-OWNERS-END -->

### 8.3. 34 UI responsibilities — P1 primary

C03/C05/C10 có thể là states của cùng workspace; 34 IDs không bắt buộc 34 routes độc lập. P4 nối connector nhưng P1 vẫn sở hữu UI/component behavior.

<!-- UI-OWNERS-BEGIN -->
| UI | Primary task |
|---|---|
| A01 | FE-13 |
| A02 | FE-13 |
| A03 | FE-13 |
| A04 | FE-12 |
| A05 | FE-14 |
| A06 | FE-14 |
| A07 | FE-11 |
| A08 | FE-15 |
| A09 | FE-14 |
| A10 | FE-15 |
| C01 | FE-02 |
| C02 | FE-02 |
| C03 | FE-04 |
| C04 | FE-06 |
| C05 | FE-04 |
| C06 | FE-07 |
| C07 | FE-08 |
| C08 | FE-09 |
| C09 | FE-10 |
| C10 | FE-04 |
| T01 | FE-03 |
| T02 | FE-03 |
| T03 | FE-03 |
| T04 | FE-03 |
| T05 | FE-05 |
| T06 | FE-05 |
| T07 | FE-06 |
| T08 | FE-07 |
| T09 | FE-08 |
| T10 | FE-09 |
| T11 | FE-10 |
| T12 | FE-11 |
| T13 | FE-12 |
| T14 | FE-03 |
<!-- UI-OWNERS-END -->

## 9. Truy vết toàn scope

### 9.1. 14 module

<!-- MODULE-TRACE-BEGIN -->
| Module | Tên | FE | BE | Tích hợp |
|---|---|---|---|---|
| M01 | Identity, Roles & Permissions | FE-02/03/13 | BE1-03/07/12 | INTG-03/08 |
| M02 | Class & Student Management | FE-03/13 | BE1-04/05 | INTG-03 |
| M03 | Session Lifecycle & Orchestration | FE-03/05/08/09 | BE1-06/11; BE2-10 | INTG-03/04/06/07 |
| M04 | Group Management | FE-03/04/05 | BE1-08/16 | INTG-04/09 |
| M05 | Collaborative Drawing Canvas | FE-01/04 | BE1-09/10/02 | INTG-04 |
| M06 | AI Vision & Adaptive Sketch | FE-06 | BE2-02/03/04/05/06 | INTG-05 |
| M07 | Artwork Gallery & Sharing | FE-07 | BE1-13 | INTG-06 |
| M08 | Knowledge & Video Generation | FE-08 | BE2-07/08/09/10 | INTG-06 |
| M09 | Off-screen Activity Library | FE-09/12 | BE2-11/12 | INTG-07 |
| M10 | Assessment & Learning Portfolio | FE-10/11 | BE1-14/15 | INTG-07 |
| M11 | Teacher Dashboard & Automation | FE-03/05/06 | BE1-11/12; BE2-01/03/13 | INTG-04/05/10 |
| M12 | Super Admin Console | FE-12/13/14/15 | BE1-03/04/12/15; BE2-12/14 | INTG-08/10 |
| M13 | Privacy, Consent & Audit | FE-11/14/15 | BE1-02/03/05/12/15; BE2-14 | INTG-08/09 |
| M14 | Recovery & Exception Handling | FE-02/04/05/06/08/15 | BE1-03/10/11/15; BE2-01/03/10/14 | INTG-04/05/06/08/09 |
<!-- MODULE-TRACE-END -->

### 9.2. 66 FR

Giữ nguyên trạng thái yêu cầu từ SRS. FE/BE tasks trong bảng được truy từ CMD/UI mapping B26.2 và semantic participants đã review, là implementation participants; cards foundation/durable/policy bổ trợ vẫn áp dụng. Truy vết không cấp approval cho FR PROPOSED/TBD. Nghiệm thu theo UC/AT cụ thể ở SRS và positive/negative trong card; tích hợp chung INTG-09/12 không thay component evidence.

<!-- FR-TRACE-BEGIN -->
| FR | Yêu cầu | Trạng thái SRS | FE | BE | Tích hợp |
|---|---|---|---|---|---|
| FR001 | Thực thi Child/Teacher/Super Admin permissions theo scope | CONFIRMED | FE-02, FE-03, FE-13 | BE1-03, BE1-04, BE1-12 | INTG-03/08 |
| FR002 | Join qua QR/mã hoặc hồ sơ, Teacher kiểm tra admission | CONFIRMED | FE-02, FE-03 | BE1-06, BE1-07 | INTG-03/08 |
| FR003 | Hỗ trợ một/nhiều trẻ cùng thiết bị, giữ participant/group context | CONFIRMED | FE-02, FE-03, FE-04 | BE1-07, BE1-09 | INTG-03/08 |
| FR004 | Teacher quản lý class/student/profile được cấp quyền | CONFIRMED | FE-03, FE-13 | BE1-04 | INTG-03/08 |
| FR005 | Adult Firebase verification, scoped participant capability, account provisioning/revoke | PROPOSED | FE-02, FE-03, FE-13 | BE1-03 | INTG-03/08 |
| FR006 | Xử lý consent theo purpose trước các thao tác thu thập/AI bị policy giới hạn | CONFIRMED | FE-03, FE-15 | BE1-05 | INTG-03/08 |
| FR007 | Teacher tạo/cấu hình topic, độ tuổi, tools, group, preset | CONFIRMED | FE-03 | BE1-06 | INTG-03/08 |
| FR008 | Tạo/chia/quản lý nhóm và thành viên trong session | CONFIRMED | FE-05 | BE1-08 | INTG-04/07 |
| FR009 | Theo dõi groups tiến độ khác nhau; không tự chuyển lớp vì group ready | CONFIRMED | FE-04, FE-05 | BE1-08, BE1-12 | INTG-04/07 |
| FR010 | Teacher pause/intervene/continue/save draft/advance/end early | CONFIRMED | FE-04, FE-05 | BE1-06, BE1-11 | INTG-04/07 |
| FR011 | Hoàn thành lưu products/process/comments/portfolio; thể hiện save/recovery | CONFIRMED | FE-10, FE-11 | BE1-11, BE1-14 | INTG-04/07 |
| FR012 | Di chuyển trẻ/rời nhóm bảo toàn artwork và contribution đã ghi | CONFIRMED | FE-04, FE-05 | BE1-03, BE1-08 | INTG-04/07 |
| FR013 | Quay lại stage cũ sau video/off-screen | TBD | FE-05 | BE1-11 | INTG-04/07 |
| FR014 | Canvas cá nhân và cộng tác; shared free canvas hoặc vùng riêng | CONFIRMED | FE-04 | BE1-09, BE1-10 | INTG-04/07 |
| FR015 | Tools phù hợp nhóm tuổi; Teacher bật/tắt/cấu hình | CONFIRMED | FE-03, FE-04, FE-05 | BE1-06, BE1-09 | INTG-04/07 |
| FR016 | Hiển thị participants/help request; bảo vệ vùng, lock/unlock/restore | CONFIRMED | FE-04, FE-05 | BE1-08, BE1-09, BE1-10 | INTG-04/07 |
| FR017 | Lưu state và reconnect tiếp tục; xử lý conflict giữ contribution | CONFIRMED | FE-04, FE-05 | BE1-09, BE1-10 | INTG-04/07 |
| FR018 | Per-author operation history, scoped undo, cảnh báo xóa nội dung người khác | PROPOSED | FE-04, FE-05 | BE1-09 | INTG-04/07 |
| FR019 | Gợi ý AI tách nét trẻ; có chế độ xem sản phẩm không AI overlay | CONFIRMED tách nội dung; PROPOSED chế độ xem | FE-04, FE-06, FE-07 | BE1-10, BE2-04, BE2-06 | INTG-04/07 |
| FR020 | Import ảnh/sticker/text/mẫu có sẵn | TBD | FE-03, FE-04 | BE1-09 | INTG-04/07 |
| FR021 | Replay quá trình và công cụ layer nâng cao phù hợp 9–12 | CONFIRMED về UX nâng cao/review; chi tiết PROPOSED | FE-04, FE-07, FE-10 | BE1-10 | INTG-04/07 |
| FR022 | Vision nhận canvas/vùng snapshot, topic, tuổi, yêu cầu, thao tác và Teacher feedback | CONFIRMED | FE-04, FE-06 | BE2-02, BE2-03 | INTG-05 |
| FR023 | Trả object candidates/context/uncertainty; Child intent và Teacher correction được ghi nhận | CONFIRMED | FE-06 | BE2-02 | INTG-05 |
| FR024 | Nhận signal/yêu cầu hỗ trợ; Teacher kích hoạt thủ công hoặc hủy | CONFIRMED | FE-04, FE-06 | BE2-03 | INTG-05 |
| FR025 | Hỗ trợ nhiều mức, sketch tham khảo bên cạnh hoặc overlay | CONFIRMED khả năng | FE-06 | BE2-03, BE2-04, BE2-05 | INTG-05 |
| FR026 | Teacher duyệt từng gợi ý cho pilot, sửa mức hoặc từ chối trước phát cho trẻ | OWNER_CONFIRMED + CONFIRMED | FE-06 | BE2-05 | INTG-05 |
| FR027 | Child yêu cầu, xem, ẩn hoặc từ chối gợi ý; tiếp tục vẽ tự do | CONFIRMED | FE-06 | BE2-06 | INTG-05 |
| FR028 | AI không tự thay nét, không suy thiếu kiến thức từ dừng vẽ; bounded analysis/config | CONFIRMED | FE-04, FE-06 | BE1-09, BE2-04, BE2-06 | INTG-05 |
| FR029 | Chặn unsafe output, typed failure, log và notify Teacher phù hợp | CONFIRMED | FE-06, FE-14 | BE2-01, BE2-03, BE2-05 | INTG-05 |
| FR030 | Dedup/cache/budget/debounce và stale-snapshot checks | PROPOSED | FE-06, FE-14 | BE2-01, BE2-03 | INTG-05 |
| FR031 | Teacher mở gallery/chọn/sắp xếp/trình chiếu/chú thích tranh | CONFIRMED | FE-07 | BE1-13 | INTG-06 |
| FR032 | Child preview sản phẩm, trình bày/giải thích ý tưởng theo format phù hợp | CONFIRMED | FE-07 | BE1-13 | INTG-06 |
| FR033 | Sharing giới hạn session/class và quyền; version snapshot và AI content rõ | PROPOSED cụ thể | FE-07 | BE1-12, BE1-13 | INTG-06 |
| FR034 | Tạo video mới hoặc kết hợp library, ưu tiên lớp, bổ sung riêng trẻ | CONFIRMED | FE-08 | BE2-07, BE2-08 | INTG-06 |
| FR035 | Knowledge phù hợp tuổi, kiểm chứng được; imagined details không trở thành science facts | CONFIRMED | FE-08 | BE2-07, BE2-09 | INTG-06 |
| FR036 | Teacher kiểm tra/chỉnh sửa/phê duyệt đúng video trước trình chiếu | CONFIRMED | FE-08 | BE2-09 | INTG-06 |
| FR037 | Generating/ReadyForReview/Approved/Playing/Failed và progress/status rõ | CONFIRMED | FE-08 | BE2-01, BE2-08 | INTG-06 |
| FR038 | Chờ video hoàn thành; không tự fallback/bỏ stage khi đang tạo | CONFIRMED | FE-08 | BE2-01, BE2-08 | INTG-06 |
| FR039 | Sau video thất bại hết retries được phép, GV explicit retry/skip/end; ghi disposition, không tự skip | OWNER_CONFIRMED; retry budget TBD | FE-05, FE-08 | BE2-10 | INTG-06 |
| FR040 | Source-grounded knowledge/script version, independent TTS nếu có narration, approval invalidation sau edit | PROPOSED | FE-08, FE-12 | BE2-07, BE2-08, BE2-09 | INTG-06 |
| FR041 | Library và AI recommendations; Teacher chọn/chỉnh cho lớp hoặc từng nhóm | CONFIRMED | FE-09, FE-12 | BE1-12, BE2-11, BE2-12 | INTG-07/08 |
| FR042 | Activity có topic/objective/age/materials/instructions/duration/safety/form/observation | PROPOSED field detail | FE-09, FE-12 | BE2-11, BE2-12 | INTG-07/08 |
| FR043 | Teacher xác nhận khả thi với materials thực tế trước bắt đầu | PROPOSED | FE-09 | BE2-11 | INTG-07/08 |
| FR044 | Lưu activity/reflection/off-screen evidence trong kết quả session | CONFIRMED | FE-09, FE-10 | BE1-14, BE2-11 | INTG-07/08 |
| FR045 | Assessment theo tuổi, Teacher observation, AI suggestions và tiến bộ chính trẻ | CONFIRMED | FE-10 | BE1-14 | INTG-07/08 |
| FR046 | Không score/rank trẻ với nhau; portfolio và reports tiến bộ thời gian | CONFIRMED | FE-11 | BE1-14, BE1-15 | INTG-07/08 |
| FR047 | Lưu session history, art/contribution khi xác định được, process/AI/content/comments/activity/reflection | CONFIRMED | FE-10, FE-11 | BE1-11, BE1-14 | INTG-07/08 |
| FR048 | Báo cáo/export theo quyền, phân biệt direct evidence/Teacher judgement/AI inference | CONFIRMED quyền; PROPOSED taxonomy evidence | FE-11 | BE1-14, BE1-15 | INTG-07/08 |
| FR049 | Rubric exploration/cooperation/expression/creativity/skills/application, descriptive levels | PROPOSED | FE-10, FE-11 | BE1-14 | INTG-07/08 |
| FR050 | Không coi “chưa quan sát” là thiếu năng lực; không suy psychology/intelligence từ tranh | PROPOSED report semantics + REPO_CONSTRAINT prohibited inference | FE-10, FE-11 | BE1-14 | INTG-07/08 |
| FR051 | Dashboard toàn lớp, group previews/status/help, review queue và controls | CONFIRMED | FE-05, FE-06 | BE1-12, BE2-01 | INTG-04/05/10 |
| FR052 | Tạo/tái sử dụng preset và automation có điều kiện, Teacher override bất kỳ lúc | CONFIRMED | FE-03, FE-05 | BE1-06, BE1-11, BE2-12, BE2-13 | INTG-04/05/10 |
| FR053 | Preset version chứa tuổi/topic/tools/canvas/AI/mốc/thông báo/video/activity/assessment | PROPOSED chi tiết | FE-03 | BE1-06, BE2-12, BE2-13 | INTG-04/05/10 |
| FR054 | Queue priority/help overload control và audit mọi automated action/override | PROPOSED | FE-05, FE-06, FE-14 | BE1-11, BE1-12, BE2-01, BE2-03, BE2-13, BE2-14 | INTG-04/05/10 |
| FR055 | Overview users/classes/sessions và role/account administration | CONFIRMED | FE-13 | BE1-03 | INTG-03/08 |
| FR056 | Author/review/publish/recall learning content và system AI policies/limits | CONFIRMED | FE-12, FE-14, FE-15 | BE1-15, BE2-12, BE2-13, BE2-14 | INTG-08/10 |
| FR057 | Session monitoring, authorized learning reports, consent/audit/incidents | CONFIRMED | FE-11, FE-14, FE-15 | BE1-12, BE1-15 | INTG-08/10 |
| FR058 | Không mặc định xem mọi child raw content; purpose-scoped audited access | PROPOSED access detail | FE-11, FE-13, FE-14 | BE1-12, BE1-14, BE1-15 | INTG-08/10 |
| FR059 | Access control, consent, retention policy, export/delete, audit | CONFIRMED | FE-11, FE-14, FE-15 | BE1-05, BE1-15 | INTG-08/10 |
| FR060 | Session/artwork recoverable, lưu drafts/checkpoints và safe error feedback | CONFIRMED | FE-04, FE-05 | BE1-10, BE1-11 | INTG-04/07 |
| FR061 | Wrong recognition correction, unsafe blocking, pending review never displayed | CONFIRMED | FE-06 | BE2-02, BE2-05, BE2-06 | INTG-05 |
| FR062 | Recalled content không dùng cho phiên mới | CONFIRMED | FE-12 | BE2-12 | INTG-08/10 |
| FR063 | Teacher offline: permitted drawing tiếp tục, actions cần approval đợi | PROPOSED | FE-04, FE-05 | BE1-10, BE1-12 | INTG-04/07 |
| FR064 | Backup/provider-copy purge, mixed shared-canvas deletion và retained audit minimization | PROPOSED; policy TBD | FE-14, FE-15 | BE1-15, BE2-04, BE2-08, BE2-14 | INTG-08/10 |
| FR065 | Chia nhóm tự động trong Phase 2; Teacher kiểm soát/override kết quả, tiêu chí/thuật toán TBD | CONFIRMED khả năng; chi tiết PROPOSED/TBD | FE-03, FE-05 | BE1-08, BE1-16 | INTG-04/09; Phase 2 allocation |
| FR066 | Thiết bị chung chọn active child theo lượt; lưu selected contributor/turn context cho nét mới, không đổi tác giả nét cũ khi switch | OWNER_CONFIRMED nguyên tắc; UX/schema chi tiết PROPOSED | FE-04, FE-05 | BE1-09 | INTG-04/07 |
<!-- FR-TRACE-END -->

## 10. Quy tắc bàn giao và Done

Mỗi owner giao source/contract revision, versioned payload/error examples, fixture manifest/hash, hướng dẫn chạy, component positive/negative tests và evidence có thể chạy lại. Các thao tác write/retry phải có observed revision/idempotency semantics phù hợp; reject do scope/consent/stale không được UI coi là success. P4 review kết nối và đưa lỗi về đúng owner.

Các mức hoàn thành phải tách rõ: (1) contract/fixture ready; (2) component runtime verified; (3) integrated verified; (4) measured/pilot evidence theo profile được adopt. Một runner pass, screenshot hoặc stub video không chứng minh durable saves, permissions, real generation hoặc tải 40 trẻ. Chỉ ghi FR VERIFIED khi đủ evidence của chính FR đó; feature/policy còn TBD không được tuyên bố toàn bộ sản phẩm complete.

Mỗi card cần plan/acceptance và task approval trong owning feature trước implementation. Visual assets mới phải qua generated → provenance/review/approval → approved/applied. Dùng synthetic data; không commit child data thật, .env, credentials, seed users, external handbook/workbook originals hoặc rendered extracts. Trước commit/push phải chạy repository security validator; kế hoạch này không yêu cầu hoặc cấp phép commit/push/deploy.

Đầu ra cuối của P4 là bản chạy nối được các module đã bàn giao, hồ sơ contract/architecture/API khớp code và verification report. Các component owner xác nhận phần mình; pending policy/module/adapter vẫn hiển thị trong báo cáo. Các blockers ngoài feature được ghi riêng, không dùng để hạ tiêu chí nghiệm thu task đang nhận.

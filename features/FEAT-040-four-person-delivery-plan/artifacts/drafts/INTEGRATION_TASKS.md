# Task người 4 — Tổng hợp kỹ thuật và tích hợp

Vai trò P4 được owner xác nhận là nối tất cả các phần. P4 chịu trách nhiệm composition, wiring, giao tiếp FE–BE, luồng xuyên module, môi trường chạy chung và bằng chứng tích hợp. P1/P2/P3 vẫn sở hữu logic/component/adapters, tests và sửa lỗi của phần mình. P4 không viết lại toàn bộ backend hoặc trở thành người duy nhất kiểm thử sản phẩm.

Các task dưới đây là backlog implementation đề xuất, không cấp approval chạy code/provider/deploy. Không gắn ngày, thời lượng, giờ công hoặc lịch sprint.

## INTG-01 — Bộ fixture tích hợp và sổ contract dùng chung

- **Owner/reviewer:** P4; P2/P3 review payload/domain, P1 review UI states.
- **Đầu ra:** registry contract candidate và version; fixture manifest synthetic/hash; sơ đồ request/event/error; fake adapters và runner kiểm tra đường nối bằng dữ liệu giả; trace SRS→task→evidence.
- **Phụ thuộc:** không phụ thuộc live service hoặc task của người khác. Dùng SRS/fixture tự tạo có provenance; sau đó đối chiếu output FE-01/BE1-01/BE2-01 ở checkpoint review, không làm ba task đó phải chờ P4.
- **SRS:** B19/B21/B22/B26, NFR04/10/11; source AC01–18.
- **Đạt:** fixture hợp lệ đi qua fake boundaries với đúng IDs/hash/version và hiển thị đúng state; fixture payload sai/unknown fields/stale review bị reject tại boundary tương ứng. Runner chạy độc lập trên máy local, không cần Firebase/provider/database thật.
- **Evidence:** manifest, runner command/results, compatibility diff và danh sách contract còn PROPOSED. Lỗi fixture không được gọi là chất lượng model hoặc tải pilot.

## INTG-02 — Composition root và điểm vào backend/worker

- **Owner/reviewer:** P4; P2/P3 review dependency direction và adapter ownership.
- **Đầu ra:** wiring ở composition root đã được feature approve; API routes/app use cases/repository/auth/queue/artifact/provider adapters được inject qua ports; worker entrypoints; health/readiness có semantics.
- **Phụ thuộc:** INTG-01; foundation contract packs FE-01/BE1-01/BE2-01 được cross-review; runtime/adapters cần dùng do P2/P3 bàn giao; ADR cho các lựa chọn bắt buộc đã được chốt.
- **SRS:** B3/B8/B19.3/B22.3; FR001/005/017/030/059/060; NFR10.
- **Đạt:** request/job fixture vào đúng use case/port, worker completion đi qua application guards, startup thiếu cấu hình bắt buộc báo rõ; không import FastAPI/ORM/provider SDK vào domain. Missing durable adapter không được báo production-ready bằng fake/in-memory adapter.
- **Evidence:** composition diagram, startup commands, architecture check, adapter/config manifest với placeholders. P2/P3 sửa logic/adapters thiếu; P4 nối và xác nhận hợp đồng.

## INTG-03 — Kết nối Child Android, Teacher và Admin với API

- **Owner/reviewer:** P4; P1 review UI lifecycle, P2 review auth/resource scope.
- **Đầu ra:** transport/API client connectors dùng contract đã adopt; authenticated identity context; join/admission/refresh; error mapping và cancellation/loading states; cấu hình backend address runtime.
- **Phụ thuộc:** INTG-02; H-IDENTITY, H-CLASS-CONSENT, H-SESSION-ADMISSION; các UI corresponding từ P1. UI development vẫn dùng local fixtures trước handoff.
- **SRS:** FR001–007/055/058/066; C01/C02/T01/T02/T03/T04/A02/A03; UC-001–004/007/008/034.
- **Đạt:** Teacher login rồi mở đúng lớp, tablet pending được admit rồi mới nhận projection/grant; sai lớp/mã hết hạn/suspended user/revoked grant không mở roster/media. Không dùng X-Actor-Ref demo làm xác thực thật; mobile không chứa provider/bucket credentials/endpoints.
- **Evidence:** request/response redacted traces, join/token lifecycle test, fixture-vs-authenticated mode manifest.

## INTG-04 — Nối canvas realtime, lượt vẽ và recovery

- **Owner/reviewer:** P4; P1 về renderer/input, P2 về authorization/log/checkpoint.
- **Đầu ra:** connector giữa canvas editor và accepted-operation API/stream; subscription/delta/checkpoint; turn/pause/region-policy propagation; local-draft reconciliation và reconnect.
- **Subtask Phase 2 có gate:** sau OD18/grouping policy được adopt và BE1-16 bàn giao, nối proposal → Teacher xem/override → commit group memberships/CAS → FE roster/grant refresh; chưa có decision không bật automatic grouping. Không sửa membership bằng direct DB; manual grouping path của pilot chạy riêng trước extension.
- **Phụ thuộc:** INTG-03; H-CANVAS-SYNC, H-SESSION-CONTROL; P1 canvas implementation/P2 drawing adapters; OD08/15 và recovery policies được adopt.
- **SRS:** FR003/009/010/014–019/021/060/063/066; UC-008–010/013–017; AT-CS-001–007.
- **Đạt:** hai client giữ đủ authorized accepted strokes và original contributor; retry ack mất không nhân đôi, switch không relabel stroke cũ; lock/revoke/restore epoch khi offline không bị buffered replay bypass. UI phân biệt on-device/sending/accepted/rejected.
- **Đạt Phase 2:** Teacher commit đúng reviewed proposal và current roster revisions tạo một atomic membership outcome; duplicate commit không chia lại nhóm, stale roster/unauthorized override bị reject không áp proposal nửa chừng. Nối thực sau feature approval, không gọi extension complete bằng flag tắt.
- **Evidence:** operation IDs/sequence/checksum, disconnect/crash/replay logs và device input traces. Bugs engine thuộc P1, bugs domain/persistence thuộc P2.

## INTG-05 — Nối snapshot → Vision → Sketch → Teacher review → Child

- **Owner/reviewer:** P4; P3 về job/model/review, P2 về source/purpose/scope, P1 về child agency.
- **Đầu ra:** snapshot/provenance handoff, source/context versions, async status/review queue, artifact delivery và child responses; cancellation/stale-result wiring.
- **Phụ thuộc:** INTG-04; H-AI-REVIEW, H-OPERATIONS; P3 assistance/review adapters; P1 C04/T07.
- **SRS:** FR019/022–030/061; UC-017–021; AT-CS-008/009/012.
- **Đạt:** proposal đúng snapshot/context, Teacher duyệt từng item trước Child access; trẻ hide/decline vẫn giữ nét. Pending/unsafe/stale/revoked result không tải được bằng direct artifact ID; cancellation không bị delayed completion resurrect.
- **Evidence:** graph source/result/review/version/hash; positive/negative delivery probes; worker attempts và purpose decisions. Real Sketch chất lượng phải có P3 benchmark riêng, không chỉ mock screenshot.

## INTG-06 — Nối gallery → knowledge → video → playback và failure controls

- **Owner/reviewer:** P4; P3 media/content, P2 session/gallery, P1 T08/T09/C06/C07.
- **Đầu ra:** pinned gallery snapshots/meaning → knowledge bundle → library/render → safety/Teacher review → authorized playback; wait/progress/failure choice và session-stage wiring.
- **Phụ thuộc:** INTG-03/INTG-04; H-GALLERY, H-KNOWLEDGE-VIDEO, H-SESSION-CONTROL; exact-review/audience và confirmed-meaning contracts. Chỉ consume shared review/snapshot contracts của nhánh AI khi cần; INTG-05 và actual Sketch generation không là prerequisite để gallery/video chạy. Teacher có thể xác nhận meaning mà trẻ không yêu cầu Sketch.
- **SRS:** FR031–040; UC-022–026; AT-CS-010/011.
- **Đạt:** chạy được cả path không yêu cầu Sketch lẫn path có Sketch đã duyệt; chỉ exact approved artifact/version/audience được chiếu; generating phải chờ, hết retries chỉ Teacher retry/skip/end; skip ghi disposition và phiên tiếp tục vẫn đi off-screen. Edited script/video/library version hoặc revoked consent không được approval cũ authorize.
- **Evidence:** job/video/review/session histories, bytes hash/playback traces, slow/failure fixtures; model-generated clip riêng và reviewed-library fixture riêng. Placeholder không là real generation.

## INTG-07 — Nối hoạt động, reflection, assessment, portfolio và kết thúc phiên

- **Owner/reviewer:** P4; P3 activity/content, P2 learning records/finish, P1 C08/C09/T10–T12.
- **Đầu ra:** class/group activity assignment, preparation checks, off-screen signals, observation/reflection, durable completion/portfolio handoff và UI kết quả.
- **Phụ thuộc:** INTG-06; H-ACTIVITY, H-ASSESSMENT-PORTFOLIO; P2/P3 module outcomes; age/rubric/portfolio policy decisions cần cho scope được adopt.
- **SRS:** FR009–013/041–050; UC-009–012/027–031; AT-CS-014.
- **Đạt:** nhóm tiến độ riêng và assessment có attribution/evidence; group note không tự thành judgement từng trẻ; finish chỉ completed khi records durable. Missing material/safety confirmation hoặc save partially fails giữ state/recovery rõ; không rank/diagnose trẻ, NOT_OBSERVED không thành thiếu năng lực.
- **Evidence:** full outcome graph/history/portfolio IDs/hash, incomplete-group/save-failure tests. P4 wire event/port, không tự ghi DB module khác để ghép kết quả.

## INTG-08 — Nối Admin, consent, content recall và data lifecycle xuyên hệ thống

- **Owner/reviewer:** P4; P2 privacy/auth/data lifecycle, P3 content/provider copies, P1 Admin/consent UI.
- **Đầu ra:** consent/revoke propagation tới UI/subscriptions/queue/artifact delivery; library publication vs teaching review; export/delete discovery, device/provider/backup-copy statuses và no-resurrection probes.
- **Phụ thuộc:** INTG-03/05/07; H-CLASS-CONSENT, H-CONTENT-PRESET, H-ADMIN-POLICY, H-DATA-REQUEST; policies/authority và provider-copy contracts của scope tương ứng.
- **SRS:** FR006/052–059/061/062/064; UC-003/033–038; FIX-PRIV-01–05/FIX-GOV-01.
- **Đạt:** recorder tạo pending consent, delegated verifier mới quyết định; expiry 90 ngày session/art không được portfolio link kéo dài raw source. Sai authority/shared export/partial provider purge không báo hoàn tất hoặc leak peer data; restore áp deletion ledger trước exposure.
- **Evidence:** synthetic copy discovery manifests/per-copy outcomes, redacted access/audit traces, expired/recalled/late-completion tests. Portfolio/profile/audit TTL chưa chốt vẫn là decision gate.

## INTG-09 — Bộ kiểm thử tích hợp chín bước và quản lý lỗi theo owner

- **Owner/reviewer:** P4 điều phối suite; P1/P2/P3 sở hữu kiểm thử/sửa lỗi component.
- **Đầu ra:** runnable integrated synthetic E2E nine-step flow và SRS INT-01–12 fault variants; failure triage theo module/contract/UI; reusable setup/cleanup.
- **Phụ thuộc:** INTG-04–08, module tests của P1/P2/P3; approved integrated fixtures/contracts.
- **SRS:** AC01–18, B26.4, NFR02–05/07/10.
- **Đạt:** complete path có và không có yêu cầu Sketch, plus shared-device/group-speed/network/unsafe/stale/video-failure/revoke/save-failure/copy-purge branches; failed checks có reproducible fixture và owner fix. Không báo video/AI/device quality đạt vì stub provider pass; không dùng screenshot làm bằng chứng server permission.
- **Đạt Phase 2 sau OD18:** integrated grouping proposal/review/override/atomic-commit probes với duplicate request, stale roster và grant-refresh fault; không làm Phase 2 thành prerequisite của manual grouping pilot. Evidence extension tách riêng để deferred criteria không bị báo verified.
- **Evidence:** run ID/config/fixture hashes/result matrix, failure traces, regression after owner fix. Test evidence lưu ở owning integration feature, component evidence giữ ở feature component.

## INTG-10 — Môi trường chạy chung, config và quan sát hệ thống

- **Owner/reviewer:** P4 wiring; P2 data/auth/storage adapters, P3 AI/worker/provider adapters.
- **Đầu ra:** reproducible local/integration startup và process wiring cho chosen stack; environment schema với placeholders; readiness; redacted logs/metrics/trace correlation và queue/save/permission failure visibility.
- **Phụ thuộc:** INTG-02; H-OPERATIONS/H-ADMIN-POLICY; accepted runtime/DB/queue/storage/model/web decisions và các adapters P2/P3.
- **SRS:** FR030/054/057/059; NFR08–11; B8/B22/B24.
- **Đạt:** clean environment chạy theo README với secrets cung cấp ở ignored/runtime store, thiếu adapter/secret báo an toàn; telemetry không chứa names/raw media/prompt/token/QR/signed URL. Firebase Authentication-only, mọi AI/storage qua backend ports.
- **Evidence:** config/runbook/health checks/sentinel redaction results và architecture/security checks. Provision/deploy thật cần authorization riêng; P4 không tự chọn cloud/DB/queue để lấp gate.

## INTG-11 — Xác nhận hệ thống ở tải pilot và tổng hợp device/model evidence

- **Owner/reviewer:** P4 test orchestration/report; P1 Android/UI, P2 load/durability/security, P3 model/jobs/media evidence.
- **Đầu ra:** measured integrated profile một lớp tối đa 40 participant; phân biệt device connections/group/job load; aggregate device/model/network/run manifests; candidate NFR outcomes/deviations.
- **Phụ thuộc:** INTG-09/10; adopted device/model/network/quality thresholds; per-component benchmarks từ đúng owner.
- **SRS:** owner pilot target, B25 MP-01–05/P-NFR-01–17; NFR01–12.
- **Đạt:** report sample counts/percentiles/errors/actual versions/network/resources; accepted data set còn nguyên khi process restart. Fake provider result không lẫn real GPU latency/cost/quality; target 40 trẻ chưa chứng minh nếu chỉ 40 idle logins.
- **Evidence:** load/operation traces/checksums, pinned Android/model/provider evidence, capacity bottlenecks và owner remediation list. Real classroom/child data vẫn cần school consent/process approval riêng.

## INTG-12 — Bàn giao hệ thống, demo và hồ sơ kỹ thuật

- **Owner/reviewer:** P4 tổng hợp; cả P1/P2/P3 xác nhận phần sở hữu.
- **Đầu ra:** build/run instructions, approved contract/ADR list, architecture/ER/API docs synchronized with actual code, integrated demo script và verification report; APK/test artifact theo approved release plan nếu scope có.
- **Phụ thuộc:** INTG-09–11; completeness của module backlog và decision register; approved distribution/visual/content/security gates.
- **SRS:** full M01–14/FR001–066, B15/B26; repo governance.
- **Đạt:** người khác chạy được theo tài liệu và thấy đầy đủ learning loop; chỉ đánh dấu requirements VERIFIED khi evidence thực tế có. Deferred/PROPOSED/TBD chưa được gọi là complete; toàn bộ confirmed modules vẫn visible trong backlog. Không đưa secrets/real child data/external originals vào repo hoặc release bundle.
- **Evidence:** handover checklist/module ownership sign-off/traceability/report, security/harness results, artifact hashes và release deviations. Commit/push/deployment không được task planning này cấp phép.

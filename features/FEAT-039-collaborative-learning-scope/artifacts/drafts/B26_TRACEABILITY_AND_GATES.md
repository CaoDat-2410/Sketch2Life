## B26. Truy vết, kế hoạch nghiệm thu và kiểm soát thay đổi

### B26.1 Cách dùng baseline cho toàn đội

B10 giữ registry 66 FR và trạng thái yêu cầu; B20 giữ 38 use case chi tiết. B26 nối yêu cầu với logical data/interface, surface và bằng chứng cần thu. Các ID DATA/CMD chỉ chỉ tới **đề xuất** B21–B22, không hàm ý endpoint đã tồn tại. Một FR confirmed có thể cần nhiều command; API catalogue không phải danh sách toàn bộ implementation tasks.

Mỗi feature implementation phải khai báo: FR/UC/contract version áp dụng; quyết định đã đóng và phần còn chặn; plan/acceptance được duyệt; fixtures nguồn/hash; nguyên tắc quyền và lỗi; evidence ở chính feature đó. Không copy một đoạn SRS thành permission triển khai khi feature chưa được duyệt. Workstreams fixture/contract Sprint 1 và kế hoạch tích hợp là hai allocation riêng theo ADR-0006.

Các thuật ngữ cần giữ cùng nghĩa:

| Thuật ngữ | Nghĩa dùng trong SRS |
|---|---|
| Security principal | Identity/capability đã được backend xác minh; authorize action hiện hành |
| Selected contributor | Trẻ được chọn đang vẽ theo lượt; attribution do UI khai báo, không bằng chứng ai cầm thiết bị |
| Accepted/durable | Operation/record đã commit qua persistence boundary; có receipt/version/server sequence |
| Local draft | Nội dung chỉ đang ở thiết bị hoặc chưa được accept; có recovery state, không báo backend đã lưu |
| Review | Quyết định về exact artifact/version/hash/audience; khác publication và khác permission đọc lớp |
| Correction | Record/version mới liên kết dữ liệu trước; không sửa im lặng original/accepted attribution |
| Portfolio | Learning record longitudinal đã được chọn/xác nhận; không là quyền giữ mọi raw session vô hạn |
| Revoke / delete / recall | Dừng quyền xử lý mới / purge theo quy trình / ngừng sử dụng nội dung; ba lifecycle riêng |

### B26.2 Ma trận FR → use case → dữ liệu/interface → verification

Mỗi dòng kế thừa positive và negative acceptance của UC được chỉ ra: ví dụ UC-001 có AT-UC-001-P và AT-UC-001-N. Cột probe bổ sung kiểm tra chéo/race/privacy, hoặc decision gate nếu hành vi vẫn TBD. Một dòng PROPOSED/TBD chỉ trở thành implementation acceptance khi refinement tương ứng được adopt; không báo “pass” vì chưa bật chức năng.

Trong cột data/interface, DATA-* là DTO; CMD-* là route proposal. Common authorization/envelope/WS/event contracts B22 luôn áp dụng. Chức năng còn thiếu route riêng phải có contract refinement trước implementation; B22 catalogue bổ sung và B26.5 nêu ranh giới này, không cho phép tùy ý ghi DB trực tiếp.

| Requirement | Detailed UC / AT-P,N | Logical data | Interface proposal | Surface | Probe / decision gate |
|---|---|---|---|---|---|
| `FR001` | UC-001 | DATA-01, DATA-04 | CMD-01, CMD-51, CMD-59, CMD-60 | C01, T01, A02 | P-NFR-06 |
| `FR002` | UC-007 | DATA-09, DATA-10, DATA-11, DATA-12, DATA-13 | CMD-13, CMD-14, CMD-15, CMD-16 | C01, C02, T04 | FIX-UX-01 |
| `FR003` | UC-008 | DATA-12, DATA-13, DATA-14 | CMD-16, CMD-27 | C02, C03, C05, T04 | FIX-UX-02 |
| `FR004` | UC-002 | DATA-02, DATA-03, DATA-04 | CMD-01, CMD-02, CMD-03, CMD-04, CMD-05, CMD-06, CMD-56 | T02, A03 | FIX-PRIV-01 |
| `FR005` | UC-001 | DATA-01, DATA-12 | CMD-17, CMD-18, CMD-51, CMD-52, CMD-53 | C01, T01, A02 | P-NFR-06 |
| `FR006` | UC-003 | DATA-05 | CMD-08, CMD-09, CMD-54, CMD-55 | T02, A08 | FIX-PRIV-01, FIX-PRIV-02 |
| `FR007` | UC-004 | DATA-06, DATA-07, DATA-33 | CMD-10, CMD-12, CMD-13, CMD-19 | T03, T14 | FIX-GOV-01 |
| `FR008` | UC-005 | DATA-08, DATA-13 | CMD-24, CMD-25 | T06 | AT-CS-005 |
| `FR009` | UC-009 | DATA-07, DATA-08 | CMD-11, CMD-26 | C05, T05, T06 | FIX-NFR-01 |
| `FR010` | UC-010, UC-004 | DATA-07, DATA-19 | CMD-19, CMD-20, CMD-21, CMD-22, CMD-23 | C03, C10, T05 | AT-CS-005, AT-CS-014 |
| `FR011` | UC-011 | DATA-07, DATA-19, DATA-31 | CMD-23, CMD-47, CMD-64 | T11, T12 | AT-CS-014 |
| `FR012` | UC-012 | DATA-08, DATA-12, DATA-13 | CMD-18, CMD-25, CMD-66 | C05, T06 | FIX-UX-03 |
| `FR013` | UC-010 | DATA-07, DATA-08 | CMD-22 | T05 | OD07 |
| `FR014` | UC-013 | DATA-15, DATA-16, DATA-17, DATA-18 | CMD-28, CMD-29 | C03, C05 | AT-CS-001, AT-CS-002, AT-CS-003 |
| `FR015` | UC-013 | DATA-06, DATA-15, DATA-16 | CMD-12, CMD-29, CMD-30 | C03, T03, T05 | FIX-UX-02 |
| `FR016` | UC-014 | DATA-16, DATA-19 | CMD-26, CMD-30, CMD-31 | C03, C05, T05, T06 | AT-CS-005, AT-CS-006 |
| `FR017` | UC-016 | DATA-17, DATA-18, DATA-19 | CMD-28, CMD-29, CMD-31 | C03, C10, T05 | AT-CS-007 |
| `FR018` | UC-015 | DATA-14, DATA-17, DATA-18 | CMD-27, CMD-29 | C03, C05, T06 | FIX-UX-02 |
| `FR019` | UC-017 | DATA-20, DATA-23 | CMD-28, CMD-36 | C03, C04, C06 | P-NFR-08 |
| `FR020` | UC-013 | DATA-15, DATA-20 | CMD-29 | C03, T03 | OD09 |
| `FR021` | UC-015 | DATA-17, DATA-19 | CMD-28 | C03, C06, T11 | FIX-UX-02 |
| `FR022` | UC-018 | DATA-20, DATA-21, DATA-22 | CMD-32, CMD-34 | C03, C04, T07 | AT-CS-008 |
| `FR023` | UC-018 | DATA-22 | CMD-34 | C04, T07 | AT-CS-008 |
| `FR024` | UC-019 | DATA-21, DATA-25 | CMD-32, CMD-33 | C04, C05, T07 | FIX-UX-04 |
| `FR025` | UC-019 | DATA-21, DATA-23 | CMD-32, CMD-35 | C04, T07 | FIX-UX-04 |
| `FR026` | UC-020 | DATA-23, DATA-24 | CMD-35 | C04, T07 | AT-CS-009 |
| `FR027` | UC-021 | DATA-23, DATA-24 | CMD-36 | C04 | P-NFR-08 |
| `FR028` | UC-017 | DATA-15, DATA-20, DATA-23 | CMD-29, CMD-36 | C03, C04 | P-NFR-08 |
| `FR029` | UC-020 | DATA-23, DATA-25, DATA-35 | CMD-32, CMD-35, CMD-44 | C04, T07, A05 | FIX-NFR-02 |
| `FR030` | UC-019 | DATA-21, DATA-25 | CMD-32, CMD-33, CMD-44 | C04, T07, A05 | FIX-NFR-02 |
| `FR031` | UC-022 | DATA-20, DATA-32 | CMD-37, CMD-65 | C06, T08 | FIX-PRIV-03 |
| `FR032` | UC-022 | DATA-32 | CMD-37, CMD-65 | C06, T08 | FIX-UX-07 |
| `FR033` | UC-022 | DATA-20, DATA-32 | CMD-37, CMD-60, CMD-65 | C06, T08 | FIX-PRIV-03 |
| `FR034` | UC-023 | DATA-26, DATA-27 | CMD-38, CMD-40 | C07, T09 | FIX-UX-05 |
| `FR035` | UC-023 | DATA-26, DATA-24 | CMD-38, CMD-39, CMD-41 | C07, T09 | FIX-GOV-01 |
| `FR036` | UC-024 | DATA-24, DATA-27 | CMD-41, CMD-42 | C07, T09 | AT-CS-010 |
| `FR037` | UC-025 | DATA-25, DATA-27 | CMD-40, CMD-44 | C07, T09 | FIX-UX-05 |
| `FR038` | UC-025 | DATA-27 | CMD-40, CMD-44 | C07, T09 | AT-CS-011 |
| `FR039` | UC-026 | DATA-25, DATA-27, DATA-28 | CMD-43 | C07, T09, T05 | AT-CS-011 |
| `FR040` | UC-023 | DATA-20, DATA-24, DATA-26, DATA-27 | CMD-39, CMD-40, CMD-41 | T09, A04 | AT-CS-010 |
| `FR041` | UC-027 | DATA-29, DATA-33 | CMD-45, CMD-48, CMD-59 | C08, T10, T13 | FIX-UX-06 |
| `FR042` | UC-027 | DATA-29, DATA-33 | CMD-45, CMD-48 | T10, T13 | FIX-UX-06 |
| `FR043` | UC-027 | DATA-29 | CMD-45 | C08, T10 | FIX-UX-06 |
| `FR044` | UC-028 | DATA-29, DATA-30, DATA-31 | CMD-45, CMD-46, CMD-47 | C08, C09, T11 | FIX-UX-06 |
| `FR045` | UC-029 | DATA-30 | CMD-46, CMD-62 | T11 | FIX-UX-06 |
| `FR046` | UC-031 | DATA-30, DATA-31 | CMD-47, CMD-49 | T12, A07 | FIX-PRIV-03 |
| `FR047` | UC-030 | DATA-19, DATA-20, DATA-30, DATA-31 | CMD-23, CMD-46, CMD-47, CMD-64 | T11, T12 | AT-CS-014 |
| `FR048` | UC-031 | DATA-31, DATA-34 | CMD-47, CMD-49, CMD-50 | T12, A07 | FIX-PRIV-03 |
| `FR049` | UC-029 | DATA-30 | CMD-46 | T11, T12 | FIX-UX-06 |
| `FR050` | UC-029 | DATA-30, DATA-31 | CMD-46, CMD-47 | T11, T12 | FIX-UX-06 |
| `FR051` | UC-032 | DATA-07, DATA-08, DATA-23, DATA-25 | CMD-11, CMD-44, CMD-59 | T05, T07 | P-NFR-16 |
| `FR052` | UC-033 | DATA-06, DATA-33, DATA-35 | CMD-12, CMD-48 | T03, T05, T14 | FIX-GOV-01 |
| `FR053` | UC-033 | DATA-06, DATA-33 | CMD-12, CMD-48 | T14 | FIX-GOV-01 |
| `FR054` | UC-032 | DATA-21, DATA-23, DATA-25, DATA-35 | CMD-11, CMD-44, CMD-59 | T05, T07, A06 | P-NFR-16 |
| `FR055` | UC-034 | DATA-01, DATA-04, DATA-35 | CMD-07, CMD-18, CMD-52, CMD-53 | A01, A02, A03 | P-NFR-06 |
| `FR056` | UC-035, UC-036 | DATA-24, DATA-33, DATA-35 | CMD-48 | T13, A04, A05, A10 | FIX-GOV-01 |
| `FR057` | UC-037 | DATA-05, DATA-07, DATA-35 | CMD-11, CMD-50, CMD-59 | A06, A07, A08, A09 | P-NFR-13 |
| `FR058` | UC-034 | DATA-01, DATA-35 | CMD-11, CMD-47, CMD-50, CMD-59, CMD-60 | A02, A07, A09 | P-NFR-06 |
| `FR059` | UC-038 | DATA-05, DATA-34, DATA-35 | CMD-08, CMD-09, CMD-49, CMD-50, CMD-54, CMD-55, CMD-63 | T12, A08, A09 | FIX-PRIV-01, FIX-PRIV-03, FIX-PRIV-04 |
| `FR060` | UC-016 | DATA-07, DATA-18, DATA-19 | CMD-21, CMD-28, CMD-31 | C10, T05 | AT-CS-007, AT-CS-014 |
| `FR061` | UC-020 | DATA-22, DATA-23, DATA-24 | CMD-34, CMD-35, CMD-36 | C04, T07 | AT-CS-009 |
| `FR062` | UC-035 | DATA-24, DATA-33 | CMD-48 | T13, A04 | FIX-GOV-01 |
| `FR063` | UC-016 | DATA-07, DATA-12, DATA-19 | CMD-11, CMD-28 | C03, C10, T05 | OD14, FIX-UX-03 |
| `FR064` | UC-038 | DATA-20, DATA-34, DATA-35 | CMD-49, CMD-50, CMD-63 | A08, A09 | FIX-PRIV-04, FIX-PRIV-05 |
| `FR065` | UC-006 | DATA-06, DATA-08, DATA-13 | CMD-24, CMD-57, CMD-58 | T03, T06 | OD18 |
| `FR066` | UC-008 | DATA-12, DATA-14, DATA-17, DATA-18 | CMD-27, CMD-29, CMD-61 | C03, C05, T06 | AT-CS-004 |

### B26.3 Traceability NFR và bằng chứng nghiệm thu

| Requirement | Measurement / fixture | Evidence của feature triển khai |
|---|---|---|
| `NFR01` | P-NFR-01/14, MP-05, FIX-UX-02/07 | Device/age/tool matrix, render trace, labels/focus và consent-approved usability nếu có |
| `NFR02` | P-NFR-06/07, FIX-PRIV-02/03 | Denied read/write/subscribe/media/export probes; revocation race và safe outputs |
| `NFR03` | P-NFR-08/09/10, FIX-UX-04/05, FIX-NFR-02 | Exact review/hash/version, blocked content, child agency, queue/model evidence tách biệt |
| `NFR04` | P-NFR-11, AT-CS-006/010 | Original/derivative graph, hashes, restored lineage và approval invalidation |
| `NFR05` | P-NFR-04/05, MP-04, FIX-NFR-03 | Accepted watermark/checksum sau crash, reconnect/replay, missing draft disposition |
| `NFR06` | P-NFR-01/02/03/05/15/16, MP-01/02 | Pinned load/device/network manifest, sample counts/percentiles/errors/resources |
| `NFR07` | P-NFR-07/12, FIX-PRIV-01–05 | Purpose decisions, discovery manifest, per-copy purge/exception và no-resurrection probes |
| `NFR08` | P-NFR-13/16, FIX-NFR-03 | Redaction sentinel checks, durable audit vs telemetry, dashboard freshness |
| `NFR09` | P-NFR-03/09/11, B19.2 limits, B22 errors | Rate/size/retry/idempotency boundaries, budget/config provenance |
| `NFR10` | P-NFR-11, contract compatibility checks B22.7 | Adopted contract fixtures, old/new namespace separation, architecture checks |
| `NFR11` | P-NFR-13, repository security validator | Synthetic manifest, no real child data/secret, actual validator outcome |
| `NFR12` | P-NFR-17, FIX-UX-06 | Off-screen/reflection/disposition history, age screen-time policy once approved |

Nguồn AC01–AC18 tiếp tục ở B14.3; không đổi tên AC nguồn thành test đã chạy. Các AT/FIX/P-NFR là kế hoạch verification. Kết quả thực tế phải có run ID/date, exact revisions, fixtures/hash và evidence link từ feature implementation.

### B26.4 Kịch bản tích hợp chín bước và fault variants

**INT-01 Happy classroom loop, PROPOSED:** Teacher login đúng lớp → chọn topic/age/tool/preset/nhóm và lưu draft → mở Lobby → pending devices được admit theo hồ sơ/consent → start → personal/shared drawing với lượt contributor đúng → Vision correction và từng Sketch review → trẻ xem/ẩn/từ chối → Teacher mở gallery đúng audience → tạo/chọn knowledge video và review exact version → playback → chọn/chỉnh hoạt động, ghi preparation → off-screen → reflection/observations → complete/save và portfolio. Chín bước sản phẩm có thể chứa nhiều lệnh và hoạt động trợ giúp xen kẽ; không ép stage thành màn hình tuần tự cố định.

| Variant ID | Thay đổi trong INT-01 | Expected end / evidence |
|---|---|---|
| INT-02 | Một tablet cho ba admitted profiles, switch khi có chunk chưa ack | Historical contributor giữ nguyên; không relabel draft, scope grant tách turn |
| INT-03 | Hai nhóm tiến độ khác nhau, một nhóm chưa xong khi Teacher advance | Explicit group disposition; chưa hoàn tất không trở thành completed |
| INT-04 | Disconnect, duplicate op, gap và restore trong lúc offline | Accepted operation set không nhân đôi/mất; stale epoch có recovery action |
| INT-05 | Consent purpose bị revoke khi assistance/video/export đang chờ | Không phát new restricted result; copy-purge status traceable |
| INT-06 | Pending/unsafe Sketch rồi Teacher chỉnh output | No Child delivery; version/hash review mới cần thiết, child strokes bất biến |
| INT-07 | Video tạo chậm rồi hết retries; thử từng retry/skip/end branch | Wait trong generating; chỉ Teacher explicit disposition, skip không báo video thành công |
| INT-08 | Teacher pause/disconnect/reconnect | Paused behavior theo approved policy; drawing quyền hiện hành, approval chờ; không tự reset phiên |
| INT-09 | Completed save hoặc worker outbox fail/crash | Terminal chỉ khi durable outcomes; retries deduped, no fake completion |
| INT-10 | Export/delete một profile trong shared canvas và backup restore | Không leak/xóa nhầm peer content; exceptions/manifest rõ, deletion ledger chống phục hồi bị cấm |
| INT-11 | Library/preset/AI policy recall hoặc changed sau session create | Source versions giữ; safety tightened không bị preset override; active-use policy cần quyết định |
| INT-12 | Cross-class/organization route, WS subscription, signed asset access và receipt replay | Current authorization deny dù ID/token cũ hợp lệ; không raw payload/PII trong audit |

Trước real-model run, INT-01–12 dùng deterministic provider fixtures; sau đó chỉ chạy model/media benchmark riêng đã được authorize. Trước classroom pilot với dữ liệu thật, cần school process/consent/privacy release gate. Không dùng task tài liệu này làm school deployment approval.

### B26.5 Decision-to-delivery gates

| Gate | Quyết định/evidence cần có | Có thể chuẩn bị trước | Chưa được claim hoàn thành |
|---|---|---|---|
| GATE-01 Product identity/age | OD04/06/13/14, consent authority, exact age computation và school scope | Logical fixtures, authorization matrix và managed profile contracts | Production auth/admission/guardian verification |
| GATE-02 Canvas Android | OD08/09/14/15, chosen runtime/editor/sync, stylus/phone/tablet evidence, turn/recovery policy | Renderer/input comparison, bounded-op/checkpoint fixture, tools UX proposal | Native collaborative editor production-ready |
| GATE-03 AI assistance/media | OD01/02/12/16, output types/quality, retry/budget/provider profile, human-gate contracts | Mock jobs/review/stale/cancel fixtures; source snapshot/provenance design | Real Sketch/video quality or generation SLA |
| GATE-04 Session/classroom | OD07/11/12/14/18, stage rewind, screen-time, capacity/teacher-offline/co-teacher/grouping | Transition and fault fixtures, independent group progress | Successful 40-child classroom or automatic grouping criteria |
| GATE-05 Learning/portfolio | OD10, pedagogical content/rubric review, evidence attribution, longitudinal policy | Descriptive observation/NOT_OBSERVED/report fixtures | Validated learning improvement; suy tâm lý/diagnosis từ tranh bị cấm ở mọi mức readiness |
| GATE-06 Privacy/data lifecycle | OD05/17, every data-class TTL/authority/backup/provider-copy/shared deletion policy | Synthetic discovery/export/redaction/purge/restore fixtures | Legal compliance, real purge guarantee or retained-data deadline |
| GATE-07 Runtime contract adoption | B21/B22 exact schemas/errors/asset/download/jobs/admin/query contracts, compatibility ADR | DTO fixtures and contract tests, inward-dependency audit | Deployed routes or backward compatibility |
| GATE-08 Team integration/release | Approved feature plans, integration allocation, security/harness/evidence and rollout gate | ADR-0006 independent fixture workstreams, dependency roadmap | Deployment/publication, automatic reassignment of people |

API refinement phải bao phủ queries cho dashboards/catalog/gallery/review/audit, consent verification/correction, account/assignment lifecycle, automatic grouping preview/commit, observation correction và data-request authority/approval/cancel. Các route candidates bổ sung trong B22 là logical design cùng trạng thái PROPOSED; cơ chế asset delivery chính xác vẫn phải kiểm tra từng resource/audience/review/purpose. Không kết nối client trực tiếp provider/bucket chỉ để lấp thiếu endpoint.

### B26.6 Change control và định nghĩa “đủ nền tảng”

SRS này đủ làm baseline phân rã feature, thiết kế contracts và xây kế hoạch QA: mọi module/yêu cầu có trace, actor/input/guard/outcome/error và proposed evidence. Nó chưa thay accepted implementation contracts, stack ADR, luật/quy trình trường hoặc device/model/load evidence. Các chi tiết còn PROPOSED/TBD phải được đóng ở feature liên quan, không giữ toàn bộ đội chờ mọi quyết định xa tương lai.

Thay đổi yêu cầu cần: nêu trigger và affected FR/UC/DATA/CMD/UI/NFR; xác định source/owner và compatibility/privacy impacts; cập nhật decision/ADR, version và acceptance; preserve source/hash; review theo governance rồi mới implementation. Bổ sung FR mới dùng ID tiếp theo, không tái dùng FR cũ cho nghĩa khác. Removing confirmed scope cần owner decision có evidence.

Một requirement có thể ở `NOT_STARTED`, `FIXTURE_VALIDATED`, `IMPLEMENTED`, `VERIFIED` hoặc `DEFERRED_BY_APPROVED_PLAN` trong bảng thực thi của feature; SRS không tự đổi status đó. `VERIFIED` cần evidence thực tế cả positive và negative scenarios liên quan; `PROPOSED` không tự được coi là passed. Khi release, giữ bảng deviations/open risks/rollback và quyền approval riêng.

Documentation checks của lần mở rộng này chỉ xác nhận coverage/links/hashes/authority và review consistency. Kết quả nằm trong evidence FEAT-039; chúng không là test pass cho runtime mới.

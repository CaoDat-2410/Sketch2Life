# Eligibility guard inventory — DRAFT rev3

Baseline dev `529cbef9`; read-only source locators, không phải quyền sửa. T0 phải rà lại `consent_is_effective`, `deny_pending_consent`, state effective và mọi caller/gate liên quan; bảng này là inventory khởi đầu, chưa chứng minh positive path.

Mỗi site cần owner, lifecycle step, exact hunk/version, disposition và test: **nhận synthetic proof riêng**, **giữ nguyên/đã dùng owner helper được duyệt**, hoặc **ngoài lifecycle chọn và vẫn deny**. Không ghi PASS trước test. Không đánh đồng synthetic proof với legal consent hoặc dùng real child data.

| Baseline source | Vai trò / điều kiện cần chốt | Disposition |
| --- | --- | --- |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py:117–118,147` | Profile consent refs NOT NULL; consent state chỉ pending/revoked. Chốt representation/conditional schema synthetic riêng, giữ real constraints | T0/OD-2 chưa chốt |
| `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:276,329–347,414–449` | list_profiles consent check, create_profile cần effective record, record_consent tạo pending. Không fake row/ref/boolean để seed positive path | T0/OD-2 chưa chốt |
| `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py:748` | Session transition / Start và eligibility của audience | T0 chưa chốt |
| Cùng file `:1309` | Admit device sau join trong lobby, trước Start | T0 chưa chốt |
| Cùng file `:1588` | Assign member to group | T0 chưa chốt |
| Cùng file `:1752,1817` | Progress / help: xác định UI pilot có gọi không; nếu ngoài scope vẫn giữ deny, không để ngầm chặn lifecycle | T0 chưa chốt |
| Cùng file `:1948` | Start Child turn | T0 chưa chốt |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py:143–227` | Verified device/shared write guard: session/group/turn + consent. Status-own cần read authority riêng, không blanket-relax write | T0 chưa chốt |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py:213–258` | Shared consent_is_effective/deny_pending_consent và caller inventory | T0 chưa chốt |
| `backend/src/sketch2life/interfaces/http/routers/be1_records.py:51–71` | Contributor consent helper và caller inventory | T0 chưa chốt |
| `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py:110,182,208–264,287,416,468,592` | Group consent helper/call sites, checkpoint/accepted operations và export source authority; mỗi caller cần disposition | T0 chưa chốt |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py:77–175,179–232` | Artifact ingress và download route (adult/assignment/contributor consent tại :216); route preview/Teacher của pilot chưa thiết kế, T0 quyết định có reuse hay không | T0 chưa chốt |
| `backend/src/sketch2life/application/services/be1_runtime.py:75–89` | Transition START dùng `consent_ready`; proof riêng cần được chốt ở domain/application boundary | T0 chưa chốt |
| `backend/src/sketch2life/domain/core_foundation.py:181`, `application/services/core_foundation.py:91,117` | Chưa thấy HTTP caller trong baseline được rà; T0 kiểm tra lại trước khi phân loại ngoài lifecycle, không blanket bypass | T0 chưa chốt |
| `backend/src/sketch2life/domain/assistance.py:358–381`, `application/ports/vision_analysis.py` | BE2 MemberFact/audience và ContextDecision eligibility amendments/version, không forge consent_effective | T0 chưa chốt |

Các cột consent refs hiện là chuỗi NOT NULL, không khai foreign key tại các dòng trên. Yêu cầu có effective legal record đến từ API/gates; không diễn giải NOT NULL thành bằng chứng DB đã có legal consent. Cách tạo profile synthetic hợp lệ là quyết định representation/schema/API của OD-2, chưa được chọn hoặc triển khai.

Acceptance T1: chứng minh create profile/enrollment → join → admit → Start/group/turn → accepted strokes/export/artifact → BE2 qua route/owner port thật; tests âm cho real/unclassified/pending/revoked, không seeded grant/consent bypass. Nếu một route UI còn gọi nằm ngoài pilot, ghi hành vi refusal/UI rõ trước positive test.

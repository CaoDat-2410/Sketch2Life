# Owner path map — DRAFT, không phải execution manifest

Baseline `529cbef9`. Bảng chỉ nêu vùng cần review, không cho sửa toàn file. T0 phải freeze exact path/hunk/hash/contract và owner approval theo task; file mới chốt sau ADR. Không dùng wildcard như quyền sửa cả card.

| Boundary | Existing source cần review | Delta dự kiến |
| --- | --- | --- |
| BE1 wire | `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | Versioned stroke/profile/export; không tin generic payload |
| BE1 identity/eligibility | `backend/src/sketch2life/interfaces/http/be1_runtime.py` | Proof/capability đúng scope; tách status-read/write, giữ legal-deny |
| BE1 registry/session lifecycle | `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`, `be1_sessions.py` cùng thư mục | Synthetic profile representation và inventory profile/join/admit/Start/group/turn/progress/help; tick từng guard, không blanket bypass |
| BE1 shared consent/records | `backend/src/sketch2life/interfaces/http/routers/be1_common.py`, `be1_records.py` cùng thư mục | Owner-approved synthetic proof disposition; giữ legal consent, rà các helper caller |
| BE1 canvas | `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` | Consistent export, group/currentness; không rewrite snapshot cũ |
| BE1 artifacts | `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | Private derivation/admission binding |
| BE1 persistence | `backend/src/sketch2life/infrastructure/persistence/be1_models.py`, `core_store.py` cùng thư mục | Required consent refs/representation nếu duyệt, consistent export; owner migration, không nới real constraint |
| BE2 domain/ports | `backend/src/sketch2life/domain/vision_analysis.py`, `domain/assistance.py`, `application/ports/vision_analysis.py`, `application/ports/assistance.py` | Distinct eligibility/live evidence, analysis-only continuation và owner fence |
| BE2 services | `backend/src/sketch2life/application/services/vision_analysis.py`, `assistance.py` | New scoped eligibility/completion, không auto Sketch; giữ A1 cũ |
| BE2 contracts | `backend/src/sketch2life/contracts/schemas/analysis_results.py`, `analysis_context_results.py`, `assistance_requests.py` | Compatibility review; version runtime mới được chốt, không widen frozen enum ngầm |
| Existing transport | `backend/src/sketch2life/infrastructure/ai/lightning_client.py`, `lightning_vision_v2.py` | Tái sử dụng; map retryable/possible-send trong pilot boundary, không đổi provider/prompt hoặc retry policy job khác |
| Offline bridges | `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py`, `context_adapter.py` | Giữ HTTP restrictions; runtime adapter tách biệt, không né guard |
| Composition/settings | `backend/src/sketch2life/interfaces/http/app.py`, `router_composition.py`, `infrastructure/config/settings.py` | Opt-in pilot trong classroom profile, không demo/combined; không giả baseline có Rev33 classroom fence; một integration owner |
| Retry/recovery | `backend/src/sketch2life/application/services/ai_jobs.py`, `domain/ai_jobs/model.py`, `infrastructure/ai_jobs/worker.py` | Pin pilot policy max_attempts=1; timeout sweep/recovery không gọi lại; giữ A1 accounting riêng |
| Persistence hiện có | `backend/src/sketch2life/infrastructure/assistance/fakes.py`, `vision_analysis/fakes.py`, `ai_jobs/sql/owner_fence_fixture.py` cùng infrastructure | Chỉ review in-memory/test-only gaps, không wire fixture vào live |
| Durable runtime T7a/b/c | Exact selected assistance/analysis store, schema/migration, owner-fence/UoW, run ledger và witness local paths do owners freeze tại T0 | T0 đặc tả witness Windows, host/DB boundary, failure model, test plan và bản chấp nhận rủi ro dư; T7c/T12 thử throwaway sau approval; minimal selected state, không full BE2/Parent adoption |
| Child UI | `apps/child-ui/app/index.tsx`, `src/services/sessionClient.ts`, `src/services/apiClient.ts`, `src/hooks/useReviewStatus.ts` | White synthetic profile/geometry/preview, explicit request/status thật, không timer approve |
| Teacher UI | `apps/teacher-ui/src/pages/AiSuggestionReviewPage.tsx` chỉ làm reference; `apps/teacher-ui/src/services/apiClient.ts`; panel/route mới chốt exact path ở T0 | Panel analysis read-only riêng; không sửa prototype Sketch approve/correct thành pending-analysis |

New source materializer, CPU renderer, admission mapping, runtime observation, owner adapters và gateway có thể cần file mới; tên/path/schema/API chưa được phê duyệt. Chốt chính xác trong execution manifest, không coi chúng đã tồn tại.

## Phối hợp và quyền

- Owner allocation do chủ task chốt; không mặc định P4 làm backend/E2E hay P3 làm toàn Android.
- FEAT-063 Rev33 còn chờ duyệt; overlap models/guards/settings/router/job scope phải có một người tích hợp và migration order rõ. Không sửa hoặc thực hiện Parent foundation/Rev33 qua plan này.
- Không sửa cùng shared file đồng thời. T3 phải xong geometry trong Child `app/index.tsx` trước T10; result enums, services và `app.py` cũng cần thứ tự.
- Không tự merge Alembic heads, apply migrations hoặc kết nối DB khi chỉ được giao planning.
- T0 inventory từng call site ở `ELIGIBILITY_GUARD_INVENTORY_DRAFT.md`, rà lại helper callers; NOT NULL không tự chứng minh consent hợp lệ, API profile creation cũng cần scoped disposition.
- T3/T10/T11 dự kiến không thêm asset mới, dùng components/style có sẵn. Nếu phát sinh frontend asset/visual mới, theo AGENTS mục 6: generated + provenance, visual approval, approved/applied trước khi dùng; task approval không thay visual approval.
- Approval/component acceptance cũ giữ nguyên. Delta runtime/source/contract/DB phải được nêu và duyệt theo đúng owner.

Execution record sau này phải có exact paths/source hashes/versions, selected tasks, owner, tests/commands allowed, DB/provider scope, exclusions và plan revision/hash. Approval template hiện chưa cấp quyền đó.

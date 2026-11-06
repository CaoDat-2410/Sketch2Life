# EV-063-55 — Rà soát SRS Rev45 theo hướng hệ thống và code hiện hành

- Feature: FEAT-063 — Thiết kế lại kiến trúc toàn repository.
- Ngày review: 2026-11-06.
- Trạng thái: REVIEW; SRS v2.5-draft chưa được owner sign-off.
- Kế hoạch: `plan/PLAN_REV45_SRS_SYSTEM_CODE_ALIGNMENT_20261106.md`.
- Plan SHA-256 lúc phê duyệt: `AD0554469128DD3DF13484DD7A78BAB42B99CB026C5D433D61D7D48E26950F1A`.
- Scope addendum hash hiện hành: `1B8A1AD64F80A70D5BDA553311629787936900571B92BBB94433F83191C43175`; các addendum chỉ bổ sung pointer authority, sửa mô tả snapshot DB đã có bằng chứng Rev43 và lập chỉ mục evidence mới.
- Final reviewed Plan Rev45 SHA-256 after lifecycle close-out: `880EC6A2B3DB0B3FBC23A0386589EE2E1E3863E9295F3F1169D9BE7469752F46`.
- Published evidence ID: EV-063-55; the original local identifier EV-063-34 is already assigned to a different artifact on `origin/dev`. The published filename and heading use the unique repository ID.
- Nguồn SRS đầu vào: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.4-draft; Data Table Register v2.4-draft.

## Mục đích và cách rà soát

Rà soát tập trung vào tính nhất quán giữa yêu cầu đích, owner directions đã được ghi nhận, source code và evidence as-built. Dùng SRS v2.4-draft là baseline duy nhất cho yêu cầu sản phẩm. Đọc `AGENTS.md`, SRS authority/source register, FEAT-063 context/decisions/status, ADR-0016–0022, API inventory/catalog Rev31–Rev37, EV-063-33, backend app/router composition, media upload implementation, Docker/Compose manifests và app package/README files.

Các file code/Compose có thay đổi trong working tree được đọc ở trạng thái hiện tại bằng diff/source review. Không sửa code và không coi source-only change là hành vi đã chạy.

## Phát hiện và cách xử lý

| ID | Phát hiện | Bằng chứng | Cập nhật |
|---|---|---|---|
| F1 | Owner đã chọn FLUX.3 làm development direction cho line-sketch/lesson visuals (Q158, §31.12), nhưng §6.2.1 và OI-19 vẫn nói model chưa chọn; các model direction khác được ghi rải rác giữa §2, §6, §9, §31. | Canonical SRS v2.4 §§2.1, 6.2.1–6.3, 9.3, 31.1/31.12; Rev43 authority record. | SRS v2.5 thống nhất các model role: Qwen3.5-VL, FLUX.3, Whisper, optional SAM 2.1; exact checkpoint, license, benchmark, serving và production remain gates. |
| F2 | LTX-2.5/Modal L40S là video target theo Q144. Dashboard dev có WAN worker candidate; đây không phải bằng chứng đã thay mục tiêu hoặc có end-to-end video. | SRS §§6.2.2, 6.3, 32.2; owner direction screenshot/evidence summarized in EV-063-33. | Giữ LTX-2.5 là target và ghi WAN riêng là candidate. Mọi thay thế cần owner decision/ADR mới. |
| F3 | `backend/src/sketch2life/interfaces/http/router_composition.py` mount BE1, demo flow và Lesson Library. AI Jobs source có mặt nhưng không mount vào main app composition theo Rev43. API route count OpenAPI 111/124 là ảnh chụp Rev43, không được chạy lại trong task này. | Router composition source; API Contract Catalog Rev37; SRS §32.1–32.3; EV-063-33. | Bổ sung §32.5 phân biệt source, mounted route, local runtime và accepted product flow. Thêm OI-20 để phân loại lifecycle cho từng BE1/classroom/demo operation so với target single-child. |
| F4 | `apps/mobile` pin React Native 0.87 nhưng README mô tả fixture-only UI harness. `apps/ui-mobile` là Expo/RN demo/reference với flow FEAT-018/030 và Lightning integration; `apps/parent-web` ghi inactive; `apps/teacher-ui` là React/Vite web surface. | `apps/mobile/README.md`, app package manifests, `apps/ui-mobile/BACKEND_INTEGRATION.md`, `apps/parent-web/README.md`, `apps/teacher-ui/package.json`. | Ghi rõ target vẫn là Parent Android + Teacher web, nhưng các client/API flows chưa được coi là hoàn tất chỉ từ package hoặc README. |
| F5 | Working-tree source có thay đổi middleware image/audio upload, `413` response schema và Docker build context. Các response upload demo dùng `MobileWorkflowResultV1` với `UPLOAD_TOO_LARGE`/`AUDIO_TOO_LARGE`; storage-example path dùng `REQUEST_TOO_LARGE`. Compose chuyển sang root context và copy catalog/visual/render bundles. | Current source diff: `backend/src/sketch2life/interfaces/http/middleware/bounded_image_upload.py`, `routers/images.py`, `backend/Dockerfile`, `compose.yaml`; service limits trong `routers/images.py` / `application/services/live_image_demo.py`. | Ghi ở §32.5 là source-only working-tree state; không tuyên bố build/run pass. Nêu rõ demo upload không thay contract resumable/quarantine/AV của target. |
| F6 | Rev43 đã đọc local DB read-only nhưng Data Table Register §1 vẫn ghi chưa kiểm tra trực tiếp database. | EV-063-33; Data Table Register §14.5 và current header. | Sửa register để nói rõ snapshot local `20261028_ll_0001`, 41 application tables; production inventory và migration rehearsal vẫn mở. Không sửa target schema/counts. |
| F7 | Các phép đếm thuộc ba scope khác nhau và có thể bị hiểu nhầm là một số liệu. | SRS §§1.1, 32.1; Data Table Register §§1, 14.4–14.5. | Giữ rõ: v2.3 design 89 active + 48 legacy = 137; Rev31 source crosswalk 92 + 48 = 140; local Rev43 DB 41 application tables. Không coi 137/140 là DB result. |
| F8 | Một số architecture guide/feature docs cũ còn nhắc Lightning/Runpod, còn code có Lightning-prefixed adapters; authority product hiện tại ghi Modal development direction. | `docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md`, current adapter source, `AGENTS.md`, SRS §§6/9/31/32. | SRS phân biệt code/development direction và production target. Không sửa guides ngoài scope; SRS authority/source register nêu rõ tài liệu nào là product authority. |
| F9 | Một số đoạn mô tả luồng/ưu tiên có thể bị đọc thành trạng thái đã triển khai thay vì yêu cầu đích. | SRS §§1–2, 31 và §32; đối chiếu source/API evidence Rev43 và Rev45. | Làm rõ §§1/2/31 là baseline đích; trạng thái triển khai chỉ được khẳng định trong §32 và theo giới hạn evidence cụ thể. |

## Tệp được cập nhật

- SRS canonical `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`: v2.5-draft, document control, summary, model target sections, OI-11/OI-19/OI-20, sources và §32.5 code-to-target crosswalk.
- Data Table Register: version metadata đồng bộ v2.5 và cập nhật mô tả local snapshot; không thay target tables, relationships hay count.
- Authority routing: root `AGENTS.md`, `docs/context/PROJECT_CONTEXT.md`, `docs/context/SRS_AUTHORITY.md`, `docs/context/SOURCE_REGISTER.md`.
- FEAT-063 tracking: `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `approvals/TASK_APPROVAL.md`, Plan Rev45 và evidence index.
- Root `approvals/TASK_APPROVAL.md` ghi nhận owner request và hai scope addenda.

## Tiêu chí review

| Plan AC | Kết quả |
|---|---|
| AC1 Authority và draft state | Đạt; v2.5-draft là canonical working baseline, chưa sign-off. |
| AC2 AI direction | Đạt; các role nhất quán và LTX/WAN được phân loại đúng. |
| AC3 Target/as-built | Đạt; §32.5 tách source, mount, local snapshot, deployment observation và product acceptance. |
| AC4 Code facts | Đạt ở mức source review; Docker/413 changes được đánh dấu unverified. |
| AC5 Data facts | Đạt; 89/137, 92/140 và 41 local tables tách biệt. |
| AC6 Traceability | Đạt; owner questions/gates chưa được trả lời giữ trạng thái mở. |
| AC7 Package consistency | Đạt sau cập nhật SRS, companion, authority pointer, context, source/status/decision/evidence records. |
| AC8 Scope safety | Đạt; không sửa code/API/schema/runtime, không chạy test/build/provider, không commit/push. |

## Lệnh/phương pháp và giới hạn

- Đọc tài liệu có phạm vi bằng PowerShell `Get-Content -Encoding UTF8` và tìm chéo bằng `rg`.
- Soi source thay đổi bằng `git diff --` trên các file Docker/upload và composition; không chạy hoặc áp patch lên code.
- Review diff tài liệu và cross-reference bằng tìm kiếm path-scoped; không thay đổi file ngoài scope đã được ghi nhận trong Plan Rev45/addenda.
- Không chạy test, build, Compose, API server, migration, DB query, security validator, AI/provider call hoặc GPU. Đây là giới hạn theo task documentation-only, không phải xác nhận runtime.
- OpenAPI 111/124 và DB 41 từ Rev43 là snapshot cũ hơn lần source review hiện tại cùng ngày; không được hiểu là đã revalidated sau các working-tree source changes.

## Trạng thái còn mở

- Main-app AI Jobs persistence/orchestration và end-to-end Modal dispatch chưa được xác nhận.
- LTX-2.5 video workflow, WAN-vs-LTX owner decision, TTS checkpoint, SAM 2.1 Modal worker, safety/license/cost/quality/latency benchmarks vẫn là gates.
- Parent Android/Teacher workflows, API lifecycle cho BE1/classroom/demo routes, production data/privacy/retention/region/cost gates cần các plan/evidence riêng.
- SRS/Data Table Register cần owner content sign-off trước diagram/PDF; Rev45 không phải approval nội dung sản phẩm cuối cùng.

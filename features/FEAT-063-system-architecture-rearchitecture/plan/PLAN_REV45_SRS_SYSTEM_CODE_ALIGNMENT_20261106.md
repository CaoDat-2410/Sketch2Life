# Plan Rev45 — Rà soát SRS theo hướng hệ thống và code hiện hành

- Feature: FEAT-063 — Thiết kế lại kiến trúc toàn repository.
- Trạng thái: REVIEW; scope tài liệu được owner phê duyệt theo approval record Rev45 và các addendum; hash lúc phê duyệt được lưu trong approval register.
- Loại công việc: rà soát và cập nhật tài liệu; không thay đổi runtime.
- Ngày lập: 2026-11-06.

## Mục tiêu

Rà soát SRS canonical hiện tại cùng bằng chứng kiến trúc và source code hiện có; sửa các chỗ mâu thuẫn hoặc thiếu phân loại giữa yêu cầu đích, hướng phát triển đã được owner xác nhận, candidate đang thử nghiệm và trạng thái đã quan sát. Giữ SRS ở trạng thái draft cho đến khi owner sign-off riêng.

## Căn cứ và ranh giới nguồn

- Tuân theo `AGENTS.md`, `docs/context/SRS_AUTHORITY.md`, `docs/context/SOURCE_REGISTER.md` và `docs/governance/WORKFLOW.md`.
- Lấy `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.4-draft làm SRS đầu vào duy nhất.
- Dùng ADR/feature evidence/code hiện hành chỉ để xác nhận quyết định owner đã ghi nhận hoặc trạng thái as-built; không nhập yêu cầu sản phẩm từ SRS cũ hoặc suy diễn quyết định từ code.
- Các kết quả OpenAPI/database/Modal trong Rev43 là bằng chứng có ngày và giới hạn riêng; không tự chạy lại runtime hay provider trong scope này.

## Phạm vi công việc

1. Rà soát các phần SRS về mục tiêu sản phẩm, AI pipeline/model direction, kiến trúc và baseline công nghệ, API/job/data boundaries, gates và as-built snapshot.
2. Đối chiếu source code hiện hành ở composition root, router registry, upload middleware/contracts, backend layers, migration declarations và app boundaries; phân biệt code có mặt, API được mount, runtime được quan sát và tính năng đã được nghiệm thu.
3. Hòa giải xuyên suốt các điểm có căn cứ: Qwen3.5-VL cho hướng phát triển vision/story/storyboard; FLUX.3 cho line-sketch/lesson visuals; Whisper cho ASR; SAM 2.1 tùy chọn; Modal là hướng hosting inference. Giữ LTX-2.5/Modal L40S là mục tiêu video đã ghi theo Q144, còn WAN là candidate development chưa thay thế quyết định đó.
4. Sửa các phát biểu model/stack mâu thuẫn; nêu rõ trạng thái target, development direction, candidate, implementation observation và gate còn mở. Không biến code hiện có thành yêu cầu mới và không khóa production stack/provider.
5. Cập nhật as-built snapshot để chỉ ghi nhận source/runtime evidence hiện có, trong đó tách source-only thay đổi chưa được build/runtime xác nhận khỏi kết quả Rev43; làm rõ API/AI Jobs composition và các giới hạn bằng chứng.
6. Phát hành SRS v2.5-draft; cập nhật metadata/reference của Data Table Register nếu cần để khớp package phiên bản, không sửa nội dung mô hình dữ liệu nếu audit không tìm thấy sai lệch có chứng cứ.
7. Đồng bộ phần mô tả snapshot DB local trong Data Table Register với bằng chứng Rev43 đã có; không thay đổi target schema, mapping hoặc count.
8. Lưu ma trận rà soát, nguồn, điều chỉnh và giới hạn tại evidence FEAT-063; cập nhật context, decisions, status, local source register, project context, root SRS authority instructions/pointer và approval records.

## Tiêu chí chấp nhận

- **AC1 — Authority:** SRS canonical vẫn là một file FEAT-063; phiên bản mới được ghi đúng là draft, chưa sign-off. Không tham chiếu SRS cũ như yêu cầu hiện hành.
- **AC2 — AI direction:** Các mục tiêu và bảng AI trong SRS nhất quán với quyết định owner hiện hành. Từng model được phân loại đúng vai trò và trạng thái; WAN không được nâng thành model video mục tiêu nếu chưa có quyết định owner mới.
- **AC3 — Target/as-built:** Kiến trúc đích và snapshot triển khai được tách rõ. Route/API presence, source adapter, Modal dashboard deployment và end-to-end flow không bị coi là cùng một mức hoàn thành.
- **AC4 — Code facts:** Các claim về app boundary, route composition, upload size/error contract, backend layer và trạng thái AI Jobs có đường dẫn source/evidence và nhãn xác minh phù hợp. Thay đổi source chưa chạy không được mô tả như runtime pass.
- **AC5 — Data facts:** 89/137 SRS design baseline, 92/140 source-derived crosswalk và 41 application tables trong DB local được giữ thành ba phép đo riêng; không suy diễn kết quả migration/production.
- **AC6 — Traceability:** Requirement/decision IDs hiện có được bảo toàn. Những điều không có câu trả lời hoặc bằng chứng đủ mạnh vẫn được giữ là open/gate; không tự chốt age bands, video-model replacement, production stack hay provider compliance.
- **AC7 — Package consistency:** Document control, table of contents, source/authority records, feature status/context/decisions và evidence chỉ tới đúng revision/hash, ngày quan sát và phạm vi.
- **AC8 — Scope safety:** Không sửa code, test, build, database, migration, provider/Modal, secrets, deployment, Git stage/commit/push hoặc SRS sign-off.

## Tệp dự kiến

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` (chỉ metadata/reference nếu cần)
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-55_SRS_SYSTEM_CODE_ALIGNMENT_REV45_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md` (evidence index)
- `features/FEAT-063-system-architecture-rearchitecture/{CONTEXT.md,DECISIONS.md,SOURCE_REGISTER.md,status/STATUS.md,approvals/TASK_APPROVAL.md}`
- `docs/context/{SRS_AUTHORITY.md,SOURCE_REGISTER.md}`
- `docs/context/PROJECT_CONTEXT.md` (canonical SRS version pointer only)
- `AGENTS.md` (canonical SRS version pointer only)
- `approvals/TASK_APPROVAL.md`

## Rủi ro và cách xử lý

- Repo đang có nhiều thay đổi chưa commit. Chỉ sửa đúng manifest tệp nêu trên và giữ mọi thay đổi khác nguyên trạng.
- Một số tài liệu kiến trúc/feature cũ còn nhắc Lightning/Runpod. Không dùng chúng để thay thế authority; ghi nhận giới hạn nguồn nếu cần, không chỉnh ngoài phạm vi.
- SRS hiện có các mốc và model decisions khác mức trưởng thành. Giữ điều chưa được benchmark/owner phê duyệt trong gate thay vì trình bày như production commitment.

## Xác minh

- Rà soát diff theo path; kiểm tra heading/TOC, version, cross-reference, model terminology, source links và consistency giữa SRS với evidence.
- Không chạy test/build/runtime/security validator trong scope documentation-only; không commit/push.

## Kết quả review

- AC1–AC8 đạt theo evidence `evidence/EV-063-55_SRS_SYSTEM_CODE_ALIGNMENT_REV45_20261106.md`; SRS v2.5-draft và Data Table Register vẫn chờ owner content sign-off.
- Các thay đổi source-only hiện có được ghi nhận như quan sát mã nguồn, chưa được build hoặc xác minh runtime. Snapshot OpenAPI/database/Modal Rev43 giữ nguyên ngày và giới hạn bằng chứng ban đầu.
- Các gate về AI Jobs/Modal end-to-end, video LTX-2.5, model/checkpoint, client flows, dữ liệu production, privacy, license, cost và quality còn mở.
- Không thay đổi code/API/schema/data/migration; không chạy test/build/provider/runtime/security validator; không stage/commit/push.

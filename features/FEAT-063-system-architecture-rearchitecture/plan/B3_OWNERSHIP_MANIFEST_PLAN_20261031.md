# B3 — Kế hoạch manifest ownership, file dùng chung và thứ tự migration (DRAFT)

- Trạng thái: **DRAFT** — kế hoạch làm tài liệu, không phải approval. B3 chỉ lập **manifest và bảng đối chiếu**; **không sửa code, schema, migration, SRS, approval hay plan hiện có**. Không chạy backend/DB/MinIO/Modal/GPU, không áp dụng Alembic.
- Ngày: 2026-10-31. Nguồn mục tiêu: dòng B3 trong [backlog](BACKLOG_API_REV37_SRS23_MODAL_20261030.md).
- Vì sao B3 là task kế tiếp: B3 là **cổng của pilot FEAT-064** (T0/T1) và của Rev36 S2/S3. FEAT-064 và Rev36 cùng sửa `be1_models.py`, `settings.py`, `app.py`, `router_composition.py`, test composition, bảng/model/service AI job và migration; nếu chưa có manifest ký chung thì hai bên có nguy cơ làm trùng hoặc đè nhau (Rev36 §Coordination, OD-13/OD-14).
- Người đọc: owner, BE1 owner, BE2/integration owner, BA.
- Kết quả: một manifest cho owner xem và ký. **B3 không ký thay ai và không suy tên người thành chữ ký.**

## 1. Đầu vào phải ghim (ghi hash vào đầu tài liệu kết quả)

| Đầu vào | Dùng để |
|---|---|
| `features/FEAT-064-current-flow-modal-vision-dev/plan/PLAN.md` (§4 mốc, §5 bảng T0–T14, §6, §8) và `DECISIONS.md` (D-01, D-04–D-09) | Task T0/T1/T3/T7a-c và quyết định đã chọn |
| `FEAT-064/plan/OWNER_PATH_MANIFEST_DRAFT.md` (18 ranh giới) | Điểm xuất phát bảng owner/file |
| `FEAT-064/plan/ELIGIBILITY_GUARD_INVENTORY_DRAFT.md` | Các guard consent mà T1 sẽ chạm (nhiều file trùng) |
| `FEAT-064/plan/CONTRACT_OUTLINE_DRAFT.md` | Route/contract pilot (mới chỉ là outline) |
| `plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md` (§Coordination with FEAT-064, §Blocking open decisions OD-1–OD-14, S2/S3) | Chồng lấn với S2/S3 |
| `docs/adr/ADR-0015-four-person-role-and-integration-allocation.md` và `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md` | Vai trò P1–P4 theo ADR |
| `evidence/B1_API_CROSSWALK_20261030.csv` (dòng `pilot` = Y/MAYBE: 18 + 2) | Route nào pilot cần |
| `backend/alembic/versions/` (đọc tĩnh: `revision`, `down_revision`, `depends_on`) | Đồ thị migration hiện hành |
| `backend/src/...` các file ở §4 | Xác nhận file/hunk tồn tại |

Điểm xuất phát đã đọc (phải **xác minh lại**, không chép):
- Đồ thị Alembic: 22 revision; 9 head theo cách tính "không ai tham chiếu làm `down_revision`/`depends_on`": `20261015_ai_0001`, `20261017_lc_0001`, `20261018_ap_0009`, `20261018_kv_0001`, `20261018_vr_0001`, `20261019_ae_0001`, `20261019_pa_0001`, `20261019_vf_0001`, `20261028_ll_0001` (phụ thuộc `20261024_0005` qua `depends_on`). Rev36 nói chín head cộng head hiệu lực của BE1; hai cách đếm có thể khác nhau, B3 phải ghi cách đếm.
- Vai trò: ADR-0015 = P1 FE, **P2 BE1**, **P3 BE2**, P4 tích hợp (composition, connector, wiring). FEAT-064 D-07/D-08 = owner BE1 `CaoDat-2410`; owner BE2, integration owner và operator live là Person 2 (`AnhKhoaa157`). Hai cách gán này **lệch nhau** (Rev36 §Coordination nói rõ không được tự đánh đồng).
- Chồng lấn: FEAT-064 T1 (biểu diễn synthetic: profile nullable/CHECK theo origin, proof riêng, BE2 `eligibility_basis`) và Rev36 S2 (`data_origin` ∈ SYNTHETIC_TEST/REAL/LEGACY_UNCLASSIFIED, consent nullable có CHECK). Có thể là **cùng một thay đổi** hai lần (OD-13).

## 2. Nguyên tắc

1. **Không ký thay, không chọn thay.** Mọi cột "đồng ký" ghi `CHƯA KÝ`. Tên người chỉ là phân công đã ghi trong nguồn, không phải chữ ký.
2. **Không đánh đồng nhãn vai trò.** "Person 2/BE2" (D-08) khác "P2/BE1" (ADR-0015): ghi hai bảng riêng và một câu hỏi owner.
3. **Một file dùng chung = một người viết tại một thời điểm.** Mỗi file ở §4 có đúng một owner ghi, một owner review.
4. **Không tự gộp Alembic head, không áp migration.** Chỉ mô tả thứ tự đề xuất và điều kiện.
5. **Không nhân đôi task.** B3 không tạo task thực thi mới; T0–T14 của FEAT-064 và S1–S3 của Rev36 giữ nguyên.
6. **Thiếu thông tin thì ghi `NEEDS_OWNER` + câu hỏi cụ thể**, không đoán.

## 3. Các bước

| Bước | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| S0 | Preflight: `AGENTS.md`, `.codex/sketch2life-harness.md`; `git status`/`git log -3`; hash đầu vào; kiểm approval B3 nếu có | Khối preflight | Hash khớp; không file bảo vệ nào đổi |
| S1 | **Bảng owner/ranh giới:** mở lại từng ranh giới trong `OWNER_PATH_MANIFEST_DRAFT` (18 hàng); với mỗi hàng ghi file/hunk xác minh được, task liên quan (T-N), chủ ghi đề xuất, người review, người đồng ký cần có (OwnerFenceV1, ...) và trạng thái `CHƯA KÝ` | Bảng owner (md + csv) | 17 hàng đều có file tồn tại trong cây hiện tại hoặc ghi "file mới, chưa tồn tại" |
| S2 | **Đối chiếu vai trò:** bảng ADR-0015 (P1–P4) so với D-07/D-08; chỉ ra từng chỗ lệch (BE2 là P3 hay Person 2; P4 sở hữu composition) và hậu quả cho `app.py`/`router_composition.py` | Bảng lệch + câu hỏi | Mỗi lệch có hướng giải quyết đề xuất, chưa chọn |
| S3 | **Bảng file chồng lấn FEAT-064 × Rev36:** liệt kê file mà cả hai đụng (ít nhất `be1_models.py`, `settings.py`, `app.py`, `router_composition.py`, test composition, bảng/model/service AI job, `be1_registry/sessions/canvas/artifacts/common/records`), kèm hunk/mục đích mỗi bên và quy tắc "một người viết" | Bảng chồng lấn | Mỗi file chồng lấn có một owner ghi và một thứ tự |
| S4 | **Đồ thị migration:** đọc tĩnh Alembic, dựng danh sách head, nhánh BE1 và nhánh ai_jobs, ghi cách đếm; xác định nhánh nào pilot T1/T7a và S2/S3 sẽ chạm; đề xuất thứ tự theo 3 phương án (X: pilot sở hữu migration `data_origin`, S2 tái dùng; Y: S2 sở hữu, pilot phụ thuộc; Z: tách, có điều phối rõ), nêu rủi ro mỗi phương án | Mục migration | Ghi rõ không thêm/gộp head nào; có bảng phương án |
| S5 | **Quyết định biểu diễn synthetic (data_origin/consent):** so D-05/OD-2 của FEAT-064 với S2 của Rev36; kết luận chúng trùng, trùng một phần hay khác, từng chỗ | Bảng so sánh | Nêu phần trùng, phần khác, ai phải quyết (OD-13) |
| S6 | **Bảng cổng/approval:** FEAT-064 (AWAITING), Rev36 S1/S2/S3 (AWAITING, hash plan), DB tạm (OD-7), live Modal (T13), đồng ký OwnerFenceV1; trạng thái hiện tại + ai ghi + phụ thuộc | Bảng cổng | Mỗi cổng có trạng thái đúng với `TASK_APPROVAL.md` và nguồn |
| S7 | Đề xuất **thứ tự thực hiện** manifest → T0 → T1 ... (chỉ tham chiếu), chỉ rõ điểm mà thiếu chữ ký thì dừng | Mục thứ tự | Không tạo task mới |
| S8 | Danh sách câu hỏi cho owner (tối đa 8), mỗi câu có mặc định đề xuất | Mục câu hỏi | Mỗi câu đủ ngữ cảnh để trả lời ngắn |
| S9 | Tự kiểm (§6); chạy `validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check` | Bảng kiểm | Cả bốn exit 0 hoặc ghi blocker |

## 4. Sản phẩm

- `evidence/B3_OWNERSHIP_MIGRATION_MANIFEST_20261031.md`: giới hạn, hash đầu vào, bảng owner (S1), lệch vai trò (S2), file chồng lấn (S3), migration (S4), so sánh biểu diễn synthetic (S5), cổng (S6), thứ tự (S7), câu hỏi (S8), tự kiểm (S9).
- `evidence/B3_OWNER_MATRIX_20261031.csv` (UTF-8): bảng S1 và S3 dạng máy đọc được.
- Chữ ký, approval thực thi, quyết định chọn phương án migration: **không thuộc B3**; owner ghi sau.

## 5. Ranh giới

- Không sửa: `backend/`, `apps/`, migration, SRS, register, ADR, DECISIONS, approval, FEAT-064/Rev36 plan, B0/B1/B2 và các file bảo vệ của owner.
- Không chạy dịch vụ, test, DB; không tạo/áp migration; không dùng token.
- Không gán việc cho một người cụ thể nếu nguồn chưa ghi; không suy chữ ký.
- Commit theo quy tắc owner: **một task một commit**, chỉ khi owner yêu cầu; không push tự động.

## 6. Kiểm tra bắt buộc (S9)

1. Cả 18 ranh giới của draft có hàng trong bảng owner; file hoặc ghi "file mới".
2. Mỗi hàng đồng ký ghi `CHƯA KÝ`; không chỗ nào ghi đã ký.
3. Bảng lệch vai trò nêu cả hai nguồn (ADR-0015, D-07/D-08) với dòng trích.
4. Mỗi file chồng lấn có đúng một owner ghi; mỗi owner có tên theo nguồn hoặc `NEEDS_OWNER`.
5. Đếm head Alembic khớp lệnh đọc tĩnh, ghi cách đếm, không đề xuất gộp head.
6. Bảng cổng khớp `approvals/TASK_APPROVAL.md` (không ghi APPROVED cho FEAT-064 hay Rev36).
7. Không file nguồn nào bị sửa (git status + hash); không đường dẫn tuyệt đối local, token, dữ liệu trẻ.

## 7. Giả định (owner có thể đổi)

| Giả định | Lý do |
|---|---|
| B3 là tài liệu thuần túy, owner ghi một mục approval documentation-only như B1/B2 | Theo nếp trước |
| Phương án X (pilot T1 sở hữu migration `data_origin`, S2 tái dùng) là điểm xuất phát đề xuất, không phải quyết định | Tránh làm hai lần cùng một thay đổi, nhưng owner mới quyết |
| P4 được mời review `app.py`/`router_composition.py` theo Rev36 §Coordination | ADR-0015 giao composition cho P4; không giao toàn bộ BE |

## 8. Câu hỏi cho owner sau khi B3 xong

1. Vai trò: BE2 là P3 (ADR-0015) hay Person 2 (D-08)? Có ghi ngoại lệ ADR-0015 không?
2. Ai là người ghi duy nhất cho từng file chồng lấn?
3. Chọn phương án migration X, Y hay Z, và ai sở hữu `data_origin`?
4. Ai đồng ký `OwnerFenceV1` (BE1 và BE2) và khi nào?
5. Có mời P4 review composition không?
6. Pilot hay S2 đi trước trên các file chung?
7. Cho phép DB tạm để nghiệm thu migration không (OD-7)?
8. Khi nào ghi approval cho FEAT-064 T0?

## 9. Chi tiết từng bước (làm đúng như sau)

### S0 — Preflight
1. Đọc `AGENTS.md` và `.codex/sketch2life-harness.md`.
2. `git status --short`, `git log -3 --oneline`. Chỉ được có 8 thay đổi local của owner (3 file đã sửa: `SOURCE_REGISTER.md`, `CONTEXT.md`, `STATUS.md`; 5 file chưa theo dõi). Có thay đổi khác thì dừng và hỏi.
3. Ghi SHA-256 đầy đủ của từng đầu vào ở §1 vào đầu tài liệu kết quả. Nếu thiếu mục approval B3 trong `approvals/TASK_APPROVAL.md` khớp hash của plan này thì **dừng, không tạo file**.

### S1 — Bảng owner (18 ranh giới)
1. Mở `FEAT-064/plan/OWNER_PATH_MANIFEST_DRAFT.md`, lấy 18 hàng của bảng "Boundary / Existing source / Delta dự kiến", đặt mã `O01`–`O18` theo thứ tự trong file.
2. Với mỗi hàng, tách các đường dẫn trong cột 2 thành từng file; kiểm bằng `Test-Path`/`ls` rằng file tồn tại; ghi `Y`, `N` hoặc `NEW` (file mới chưa tồn tại, theo ghi chú "file mới chốt sau ADR").
3. Gán task theo bảng T0–T14 của `FEAT-064/plan/PLAN.md` §5 (gợi ý ban đầu, phải xác minh): wire/canvas → T3, T4; identity/eligibility, registry/session, consent/records → T1, T2; artifacts → T5; BE2 domain/ports/contracts/transport/bridges → T6, T8; persistence và runtime bền → T7a, T7b, T7c; composition/settings → T9 và tích hợp; retry/recovery → T6, T8; Child UI → T3, T10; Teacher UI → T11.
4. Cột chủ ghi (`writer`): chỉ điền khi nguồn đã ghi (D-07/D-08 hoặc ADR-0015); còn lại `NEEDS_OWNER`. Cột `reviewer` tương tự. Cột `cosign_required` lấy từ FEAT-064 (OwnerFenceV1, owner BE1, owner BE2, integration owner). Cột `cosign_status` luôn `CHƯA KÝ`.
5. Cột `rev36_overlap`: `S1`, `S2`, `S3` hoặc `none`, dựa trên Rev36 và `REV36_S1_EXECUTION_SCOPE_DRAFT`.
6. Cột sản phẩm (csv): `id, boundary, files, file_state, tasks, pilot_delta, rev36_overlap, writer, reviewer, cosign_required, cosign_status, shared_file, conflict_id, notes`.
- Xong khi: 18 hàng, mỗi file có `file_state`, không ô trống (dùng `NEEDS_OWNER` hoặc `none`).

### S2 — Đối chiếu vai trò
1. Lập hai bảng riêng: (a) ADR-0015 mục 1, 3, 4 (P1 FE, P2 BE1, P3 BE2, P4 tích hợp, P4 sở hữu composition/connector/wiring); (b) FEAT-064 D-07, D-08, D-09 (owner BE1 = `CaoDat-2410`; BE2 = integration owner = operator live = Person 2 `AnhKhoaa157`).
2. Bảng lệch: mỗi dòng nêu vai trò, nguồn A nói gì, nguồn B nói gì, hậu quả cho file nào (đặc biệt `app.py`, `router_composition.py`), hướng giải quyết đề xuất.
3. Ghi chỗ Rev36 §Coordination yêu cầu "không đánh đồng nhãn" và mời P4 review composition.
- Xong khi: mọi lệch có hai trích dẫn kèm dòng; không dòng nào tự chọn bên đúng.

### S3 — File chồng lấn FEAT-064 × Rev36
1. Từ S1 lấy danh sách file; từ Rev36 (S1 bảng "Runtime/test paths", S2, S3, §Coordination với FEAT-064) lấy danh sách file mà S1/S2/S3 sẽ đụng. Giao hai tập, ghi mỗi file chồng lấn.
2. Với mỗi file chồng lấn: mục đích của pilot, mục đích của S1/S2/S3, rủi ro đè nhau, đề xuất "một người ghi" (nguồn hoặc `NEEDS_OWNER`) và thứ tự (ai trước).
3. Bắt buộc xét tối thiểu: `be1_models.py`, `settings.py`, `app.py`, `router_composition.py`, `test_app_composition.py`, `ai_jobs/sql/tables.py`, `domain/ai_jobs/model.py`, `application/services/ai_jobs.py`, `be1_registry.py`, `be1_sessions.py`, `be1_common.py`, `be1_canvas.py`, `be1_artifacts.py`, `be1_records.py`.
- Xong khi: mỗi file chồng lấn có đúng một writer (hoặc `NEEDS_OWNER`), không file nào có hai writer.

### S4 — Đồ thị migration (đọc tĩnh)
1. Dùng đọc tệp (không DB): với mọi file `backend/alembic/versions/*.py`, trích `revision`, `down_revision`, `depends_on`. Ghi bảng 22 dòng.
2. Tính head theo **hai cách** và ghi rõ: (a) revision không là `down_revision` của ai; (b) như (a) nhưng coi `depends_on` cũng là tham chiếu. Đối chiếu với câu "chín head cộng head hiệu lực BE1" của Rev36.
3. Nhận diện nhánh BE1 (`20261014_0001` → … → `20261024_0005`) và nhánh `ai_jobs` (`20261015_ai_0001`); nêu revision nào mà T1/T7a (pilot) và S2/S3 (Rev36) sẽ làm con.
4. Bảng 3 phương án: **X** pilot T1 sở hữu migration biểu diễn synthetic, S2 tái dùng; **Y** S2 sở hữu, pilot phụ thuộc; **Z** tách hai migration có điều phối. Mỗi phương án: thứ tự, điều kiện, rủi ro (chồng lấn, downgrade, DB tạm), việc cần owner quyết. **Không chọn** phương án nào, không đề xuất gộp head, không tạo revision.
- Xong khi: số head theo hai cách khớp kết quả đọc; mỗi phương án có tối thiểu 3 rủi ro.

### S5 — So sánh biểu diễn synthetic
1. Bảng hai cột: FEAT-064 (D-05, OD-2, T1, `ELIGIBILITY_GUARD_INVENTORY_DRAFT`) so với Rev36 S2 (`data_origin`, nullable consent, CHECK, `LEGACY_UNCLASSIFIED`).
2. Với mỗi thuộc tính (cột lưu, giá trị, ràng buộc, ai tạo, ai đọc, tác động guard consent, tác động BE2 `eligibility_basis`): ghi `GIỐNG`, `GIỐNG MỘT PHẦN` hoặc `KHÁC`, kèm trích dẫn.
3. Kết luận có điều kiện: có thể là cùng một thay đổi hay không; ai quyết (OD-13).
- Xong khi: mọi thuộc tính có nhãn và trích dẫn.

### S6 — Bảng cổng/approval
Liệt kê: FEAT-064 plan (trạng thái trong `FEAT-064/approvals/TASK_APPROVAL.md`), Rev36 S1/S2/S3 (hash `8DD19899…`, trạng thái trong `TASK_APPROVAL.md`), DB tạm (Rev36 OD-7), live Modal (T13), đồng ký `OwnerFenceV1`, đồng ký manifest. Mỗi cổng: trạng thái hiện tại, ai ghi, phụ thuộc. Khớp đúng nội dung hai file `TASK_APPROVAL.md`.

### S7 — Thứ tự đề xuất
Chuỗi B3 → T0 → T1 (và S2/S3) chỉ tham chiếu, nêu điểm mà thiếu chữ ký thì dừng phần phụ thuộc (D-07). Không tạo task mới.

### S8 — Câu hỏi owner
Tối đa 8 câu theo §8, mỗi câu có mặc định đề xuất và các file bị ảnh hưởng.

### S9 — Tự kiểm và kiểm tra repo
Thực hiện §6; chạy `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, `git diff --check`; kiểm whitespace riêng hai file mới.

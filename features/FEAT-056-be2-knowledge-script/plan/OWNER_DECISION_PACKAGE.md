# BE2-07 — Gói duyệt plan offline

Status: AWAITING_OWNER_PLAN_APPROVAL. Đây là đề xuất, chưa là quyết định đã được user chọn.

- Plan revision1: PLAN.md, SHA256 `6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36`.
- Base:23acf9e83e181305edfeb345be9a8e7eb9dbef88; nhánh feature/be2-07-knowledge-script.
- Component: KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE; code/tests chưa triển khai.

Khuyến nghị duyệt cùng gói OD01–08 trong §11: FEAT056/WIP1, trusted context fixtures,
reviewed catalog + source-mapped Teacher corrections, fact text derive từ claims, own
coordinated atomicmemoryUoW, strictcandidateexport và deterministic synchronous/noLLM scope.
Missing-source draft báo Teacher content action; real source/BE1/consumer integration deferred.

Lựa chọn có tradeoff cần đọc kỹ: OD03 cho Teacher-attested sourced claims generation-ready
theo namedfixturepolicy, ghi rõ accountable attestation không semantic verification. Có thể
chọn chỉ catalog-reviewed ready; khi đó sửa readiness/tests trước freeze. Không mặc định coi
owner đã chọn phương án nào. Duyệt plan theo khuyến nghị sẽ adopt phương án đầu cho offline.

Sau khi duyệt revision/hash và các OD: freeze approved bytes, ghi TASK_APPROVAL APPROVED
với nguyên văn chỉ thị, mở ACTIVE07/WIP1, làm K1–K7offline, review/fix rồi owner nghiệm thu.
Commit/push/PR vào nhánh gộp có publication plan riêng sau acceptance. Runtime01–07 được
chuẩn bị ở BE2_01_07_RUNTIME_CAMPAIGN_PLAN.md, cần missingimplementations/profile/approval
trước execution; chưa chốt model/provider hoặc dựng môi trường trong lượt planning.

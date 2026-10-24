# Task approval

## SRS classroom integration amendment — 2026-10-23

- Status: APPROVED for a documentation-only SRS amendment.
- Approver: Project owner; direct instruction: “ghi lại vào srs những điểm sửa đổi luôn nhé”.
- Plan revision: 4 — `plan/PLAN_REV4_SRS_CLASSROOM_INTEGRATION_AMENDMENT_20261023.md`.
- Approved scope: preserve the exact v3.1 SRS, record the clarified shared six-digit room-code behavior and add traceable proposed contract clarifications for classroom stage persistence and session outcomes. Keep the current canonical SRS copies synchronized and update feature/source records.
- Authority boundary: this approves editing requirements documentation and the narrow SRS generation/checker paths needed to preserve v3.1 and target v3.2. It does not approve product code, API/schema adoption, application tests, migrations, deployment, Modal execution, publication, or interpreting unanswered behavior as confirmed.
- Owner-confirmed for this amendment: both QR/deep-link and the shared six-digit code stop accepting new join requests when the Teacher starts the class; the product must distinguish full completion from a Teacher stopping early.
- Remaining contract work: define pending-request disposition at the start boundary, response/error behavior, completion guards/receipt, and the required reason/evidence for early stop. These technical details require FEAT-060/BE1 review and are not adopted by the SRS edit.

- Status: APPROVED
- Approver: Project owner, direct request in this conversation
- Approved scope: analyze the current system, list reusable technologies, propose architecture, revise SRS for the attached collaborative creative learning scope and ask technology questions if needed.
- Plan revision: 3
- Approved at: 2026-10-10 (Asia/Saigon; exact request time unavailable)
- Approval evidence: owner request "phân tích hệ thống hiện tại ... list các công nghệ có thể tái sử dụng ... bố trí lại kiến trúc ... sửa đổi srs ... có thể hỏi ... techstack".
- Notes: approval applies to documentation and read-only analysis only. No runtime implementation, full stack freeze, provider execution, data collection, deployment or commit/push.

## Owner answers — 2026-10-10

- "Thay thế scope hiện tại": replace current product scope and canonical Master SRS after preserving the existing working-copy v2.0.
- "Tablet/điện thoại Android": child client targets Android tablets and phones.
- "giữ fastapi, reactnative": retain FastAPI and React Native. Other technologies, versions, tenant/capacity and AI budget remain unconfirmed.
- Revision 2 records these direct answers. Documentation replacement is authorized; runtime migration is not.

## Additional owner refinement answers — 2026-10-10

- AI Sketch: "Duyệt từng gợi ý trước" — Teacher reviews each suggestion before child access for pilot; preset preapproval is not the chosen policy.
- Shared tablet: "Chọn trẻ đang vẽ theo lượt" — explicit active-child turn selection for contributor attribution; device grant still authorizes each operation.
- Exhausted video failure: "Giáo viên chọn thử lại, bỏ qua hoặc kết thúc" — only Teacher chooses retry, skip or end after permitted retries fail. Video generating still waits; no automatic fallback/skip. Retry budget remains TBD.
- These answers authorize documenting the selected behavior in SRS/context/ADR; runtime implementation remains excluded.

## SRS foundation expansion — revision 3, 2026-10-10

- Status: APPROVED for documentation-only expansion by direct owner request.
- Owner instruction: "làm chi tiết hơn nữa, có thể hỏi 1 vài câu, đây sẽ dùng làm nền tảng cho cả cái hệ thống".
- Authorized: preserve current v3.0; expand canonical SRS and feature artifact to v3.1 with detailed use cases, logical fields/constraints, command/query/realtime contracts, state/permissions/recovery, screens, NFR verification, traceability and decision records; ask focused questions and incorporate answers.
- Logical schemas/contracts, library/model/cloud selections and unconfirmed policy/value proposals remain unadopted. No runtime/provider/cloud/visual application or commit/push is authorized.
- Acceptance: plan revision 3 AC-D01–AC-D14; root integrates independently drafted sections and records review/validation.

## Foundation owner answers — 2026-10-10

- Organization: "Một trường trước, chuẩn bị khả năng mở rộng" — one-school pilot; organization scoping prepares later expansion, not a full multi-tenant launch.
- Child identity: "Hồ sơ + QR/mã phiên, không tài khoản riêng" — teacher-managed profiles and session admission, no independent child login account.
- Consent: "Nhà trường thu consent, GV/Admin ghi nhận bằng chứng và phạm vi" — school collects legal-representative consent; authorized Teacher/Admin record evidence and allowed purposes. Enrollment/adult role does not itself constitute consent.
- Documentation only. Exact verification workflow, data retention, jurisdiction and policy parameters remain to be refined unless subsequently answered.

## Foundation boundary/capacity/retention answers — 2026-10-10

- Age: “Có, từ đủ 3 đến trước 13 tuổi” — inclusive 36–155 completed months; 35 and 156 are outside target. Age computation/reference date and mixed-age curriculum details remain contract/pedagogical refinement.
- Pilot: “1 lớp, tối đa 40 trẻ” — owner target for simultaneous pilot capacity, not evidence the current runtime can serve that load. Device/network/topology/AI budget and performance metrics remain proposed or TBD.
- Retention: “90 ngày sau khi phiên kết thúc” — default session/artwork duration starts at session end. Portfolio, child profile and audit have separate policies; derivative classification, school authority, provider/backup/device copies, exceptions and purge proof need refinement. No silent raw-source extension by portfolio links.
- These answers update documentation and ADR only; no runtime/provider/real-data/deployment or commit/push approval.

## SRS owner-decision amendment — Plan Rev5, 2026-10-24

- **Status:** APPROVED for the exact documentation scope below.
- **Approver:** Project owner, direct instruction to record the clarified decisions in the SRS, followed by six explicit answers on 2026-10-24.
- **Plan:** `plan/PLAN_REV5_SRS_OWNER_DECISIONS_20261024.md`.
- **Approved plan SHA-256:** `39268EB1CEA557E55DB952268FB8DF92B3539BE2AD5107DF6EF9D22200069B77`.
- **Approved scope:** preserve v3.2 byte-for-byte; issue additive SRS v3.3/B28; record the six owner decisions; reconcile the directly affected transition, OD07, join, group-disposition, and early-stop rules; update contract proposals, source/decision/evidence records, and the documentation checker.
- **Owner-confirmed:** pending requests are atomically revoked on successful start; approved shared room-code control package (including persistent throttle threshold); next-stage-only progression with interleaved/`not_needed` assistance; rewind remains disabled until OD07 is resolved; unfinished group work requires `save_draft`; early stop requires a reason category and permits an optional note.
- **Still gated:** BE1-owned endpoint/schema/guard/security implementation review and migration root/order; FEAT-057 card-owner approvals; Modal profile/live call; deployment, production data, and Git publication. This approval authorizes documentation updates only, not new runtime routes, DB schema, or migration.

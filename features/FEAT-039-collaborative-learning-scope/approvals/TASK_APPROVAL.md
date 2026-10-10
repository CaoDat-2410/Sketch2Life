# Task approval

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

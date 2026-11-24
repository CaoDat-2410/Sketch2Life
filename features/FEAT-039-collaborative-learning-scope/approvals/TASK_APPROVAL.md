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

## Owner-approved proposed billing addendum B29 — 2026-10-25

- Status: APPROVED FOR DOCUMENTATION ONLY by direct owner request.
- The owner selected Teacher Web as the purchase surface and Free Trial + Plus subscription + quota top-ups as the proposal structure; MoMo, VNPay and VietQR are requested alternatives. Price/quota research is authorized, but all values must remain pending the owner's decision.
- Authorized: add a segregated `B29 — Proposed Teacher Web Billing Change Request` to both byte-identical current SRS copies; retain current v3.3/B28 policy as the approved baseline; preserve its exact original bytes at `artifacts/Collaborative_Learning_SRS_v3.3_B28_preserved_20261025.md`; add proposed FR/NFR/business rules/exceptions/architecture/technology and source-based legal/platform/privacy review; update context, decision, status and evidence records.
- The owner's English project positioning is “Sketch2Life is a collaborative creative learning platform for children aged 3–12, inspired by Montessori, Reggio Emilia, and social constructivist learning.” It is a descriptive statement and does not supersede the current supported-runtime age target or imply implementation.
- No payment code, migration, provider/merchant onboarding, credentials, sandbox/live API calls, transaction, app test, deployment, release, tag, commit, push or compliance certification is authorized.
- Plan: `features/FEAT-029-master-srs/plan/PLAN_B29_TEACHER_WEB_BILLING_CHANGE_REQUEST_20261025.md`; the broader Rev13 dossier and Draw.io work is governed by FEAT-058 Plan Rev13.

## Owner clarification — existing portals and school-level billing (2026-10-25)

- Reuse the existing Teacher Desktop and Super Admin Portal; do not add a role or standalone UI.
- Propose `billing:manage` as a permission on existing Teacher accounts. Teachers without it have read-only plan/usage visibility. Super Admin manages billing catalog and school subscriptions through the current portal.
- Attach subscription, payment, add-on and shared credit records to `school_id`, not to the individual purchasing Teacher. The 10 classes / 500 credits example is illustrative, pending selection of price/quota option.
- Prepare owner-review pricing options before final PDF export. No billing price, term or quota is approved by this clarification.
- Owner price selection — 2026-10-25: record Option B at 999,000 VND/month (up to 10 classes / 500 school-shared credits) as the selected document proposal. Additional class/Teacher/AI-credit prices and trial terms remain candidate recommendations awaiting review before final PDF export.
- Owner pricing-status clarification — 2026-10-25: keep the full package and add-on pricing/quota table in the segregated B29 SRS addendum, with every Sketch2Life amount and quota labeled PROPOSED. The 999,000 VND/month Plus amount is a proposal candidate only. The Registration form may mention proposed billing/payment but must not contain prices or quota amounts. No baseline adoption or implementation is authorized.
- Owner scope amendment — 2026-10-26: the owner supplied the “School plans and billing” image and requested that package values be revised. Plan `../FEAT-029-master-srs/plan/PLAN_B29_SCHOOL_PACKAGE_UPDATE_SRS_V3_5_20261026.md` authorizes synchronized SRS v3.5 values: Free Trial 14 days/1 active class/3 shared AI credits/no payment method; Plus 5 active classes/10 Teacher seats/100 shared AI credits; 15/45/80-credit one-time school-shared packs. Monetary amounts remain PROPOSED; no registration prices or runtime billing changes are included. Preserve v3.4 and all historical sources.

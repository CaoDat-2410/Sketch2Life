# Task approval

- Status: APPROVED
- Approver: Project owner
- Plan revision: 2 (current)
- Approved at: 2026-11-20
- Approved scope: Complete the Platform Admin APIs first, then make each corresponding Admin UI screen production-quality.
- Source instruction: “mục tiêu là làm đầy đủ api cho role admin xong sao đó làm UI thật đẹp cho từng phần đó”.
- Constraints retained from the active session: test billing flow only with real payments off; configured email provider; preserve current data; no generated Markdown/PNG reports beyond repository-required governance records.

## Revision 2 — three additional Platform Admin slices

- **Status:** APPROVED_FOR_IMPLEMENTATION for the exact additions in Plan Rev2.
- **Approver:** Project owner, direct instruction in the current conversation (2026-11-20): implement **Giám sát vận hành**, **Sửa trạng thái/thông tin trường**, and **Lưu giữ audit**, then polish the corresponding Admin web UI; defer real payments.
- **Scope:** Add these three API capabilities and their existing Admin web panels. Preserve current local data, use an indefinite audit-retention default until configured, make any purge preview-first and explicit, and retain the existing no-real-payment boundary.
- **Exclusions:** Real-payment provider/webhook integration, mobile-app UI, inferred account/class cascades when a school changes state, child profile/media access, commit, and push.

## Revision 3 — quota commerce and provider integration

- **Status:** APPROVED_FOR_IMPLEMENTATION for the exact scope in Plan Rev3.
- **Approver:** Project owner, direct instruction “duyệt” in the current conversation (2026-11-22), approving the five-step sequence from quota policy reconciliation through APIs, MoMo/VNPay integration, web UI, and later video-generation hookup.
- **Scope:** Implement the SRS §31.20 quota decisions, server-side offers/prices, purchase scopes, school Teacher allocations, MoMo/VNPay payment flows, and the supported Platform Admin/School Manager web UI. Keep real payment dispatch disabled until merchant configuration is supplied and validated. Parent purchase API is included; mobile UI and video-generation hookup are deferred.
- **Constraints:** Preserve school-capacity billing; no fabricated successful payment; no production prices invented; no secrets in source/chat; do not implement unresolved SRS policies without an owner decision; no commit/push.


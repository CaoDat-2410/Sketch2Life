# FEAT-029 Master SRS source register

Updated: 2026-10-26 (Asia/Saigon), SRS v3.5 school package/quota update.

> **Historical source register:** the authority labels and “current” wording below describe the FEAT-029/039 baseline as of 2026-10-26. For all current product requirements and target architecture, use only `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft. The older v3.5 copies remain historical; see `docs/context/SRS_AUTHORITY.md`.

## Product and project authority

| Source | Location | Use and authority |
|---|---|---|
| Historical FEAT-029 SRS | `artifacts/Sketch2Life_Master_SRS.md` | Was the FEAT-029 local v3.5 master on 2026-10-26, including its then-current B29 package wording; superseded for current product intent by FEAT-063 v2.3-draft. |
| Historical synchronized copy | `features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.5.md` | Was synchronized to the local v3.5 master on 2026-10-26; retained for history, not current authority. |
| Preserved SRS v3.4 | `artifacts/Sketch2Life_Master_SRS_v3.4_preserved_20261026.md` and FEAT-039 `Collaborative_Learning_SRS_v3.4.md` | Exact prior v3.4 bytes preserved; SHA-256 `07ee7d5bb4ac7fe1a3aa0d35050b60cd6efd3ae09234fcea6205f92a18012090`. |
| Historical SRS v3.3/B28 | `features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.3_B28_preserved_20261025.md` | Exact preserved pre-billing baseline (SHA-256 `f7f401829955c26a793c94d468c74502dc0ed465f9f35084e364b728c243c646`). |
| Historical B29 proposal | `artifacts/B29_TEACHER_WEB_BILLING_PROPOSAL.md` and FEAT-039 `Collaborative_Learning_SRS_v3.3.md` | Preserves prior proposal-only state and owner decisions before v3.4 promotion. |
| Registration v1.2 | `[Downloads]/Phieu_FA26SE225_v1.2.docx` | Original registered project scope. Kept unchanged; derived Review 2 form may mention billing/payment scope update but contains no prices. |
| Owner scope/price direction | Current conversation, 2026-10-25 and 2026-10-26 | Promotes payment to baseline; latest owner image updates baseline quantities; only monetary amounts remain PROPOSED. |
| Current implementation evidence | Repository source and FEAT records referenced by FEAT-058 Rev14 | Billing UI/API/schema/provider integrations are not present; payment remains NOT IMPLEMENTED. |

## Policy and provider references checked 2026-10-25

| Source | URL | Use and limitation |
|---|---|---|
| Google Play Payments policy | <https://support.google.com/googleplay/android-developer/answer/9858738?hl=en> | Primary platform policy. Review exact adult-web purchase and Android-consumed digital-entitlement model before enablement. |
| MoMo IPN documentation | <https://developers.momo.vn/v3/docs/payment/api/result-handling/notification/> | Provider integration reference for notification signature and transaction matching; no merchant readiness inferred. |
| VNPay secure-hash/IPN documentation | <https://sandbox.vnpayment.vn/apis/docs/chuyen-doi-thuat-toan/changeTypeHash.html> | Provider integration reference; exact current merchant contract/sandbox must be confirmed. |
| NAPAS VietQRPay | <https://developer.napas.com.vn/vi/product/introduce/viet-qr-pay> | Primary participant-bank/acquirer product reference; a QR image alone is not payment verification. |
| UNICEF Guidance on AI and Children v3.0 | <https://www.unicef.org/innocenti/reports/policy-guidance-ai-children> | Non-binding child-centred AI guidance; not a legal compliance certificate. |
| Vietnam Personal Data Protection Law 91/2025/QH15 | <https://vanban.chinhphu.vn/?docid=214590&pageid=27160> | Official Government legal record; counsel must assess applicability to actual child-data/payment flows. |
| Vietnam AI Law 134/2025/QH15 | <https://vanban.chinhphu.vn/?classid=1&docid=216334&pageid=27160> | Official Government legal record; applicability review remains open. |
| Vietnam E-commerce Law 122/2025/QH15 | <https://vanban.chinhphu.vn/?classid=1&docid=216503&orggroupid=1&pageid=27160> | Official Government legal record; applicability review remains open. |
| Consumer Protection consolidated text 47/VBHN-VPQH | <https://vanban.chinhphu.vn/?classid=2629&docid=217232&pageid=27160> | Official Government legal record; applicability review remains open. |

These references support requirements and gates, not a claim of legal/platform compliance, commercial pricing validity, provider integration, or current implementation.

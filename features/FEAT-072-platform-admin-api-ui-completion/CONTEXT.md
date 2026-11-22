# FEAT-072 Platform Admin API and UI completion

- Status: IN_PROGRESS
- Owner: Project owner
- Goal: Complete the server-authoritative Platform Admin API surface, then finish each Admin UI screen against those APIs.
- UI scope: Web dashboard only; no mobile app or mobile-specific flows.
- Product source: `docs/context/SRS_AUTHORITY.md` and the canonical FEAT-063 v2.7-draft SRS.

## Boundaries

- Content Admin remains a permission of Platform Admin, not a separate role.
- Platform Admin and Content Admin permission do not grant child profile, media, story, or signed asset access.
- Video-quota purchasing and MoMo/VNPay integration are now owner-approved implementation scope under Plan Rev3. Keep real payment dispatch disabled by default; use provider sandbox credentials for integration until merchant configuration and callback validation are complete. Do not change the separate school-capacity billing flow.
- Email uses the configured provider; action links and credentials are never persisted in audit/evidence.
- Resolved quota purchasing, school allocation, payment-method, renewal-option, and no-refund decisions follow the canonical SRS §31.20. Remaining open owner policies stay open and are not invented by this feature.
- Existing local data is preserved; tests use isolated or disposable data.

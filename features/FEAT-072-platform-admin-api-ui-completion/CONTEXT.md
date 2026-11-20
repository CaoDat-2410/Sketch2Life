# FEAT-072 Platform Admin API and UI completion

- Status: IN_PROGRESS
- Owner: Project owner
- Goal: Complete the server-authoritative Platform Admin API surface, then finish each Admin UI screen against those APIs.
- UI scope: Web dashboard only; no mobile app or mobile-specific flows.
- Product source: `docs/context/SRS_AUTHORITY.md` and the canonical FEAT-063 v2.7-draft SRS.

## Boundaries

- Content Admin remains a permission of Platform Admin, not a separate role.
- Platform Admin and Content Admin permission do not grant child profile, media, story, or signed asset access.
- Real payment processing remains disabled. Billing, quota, and capacity are local/test sandbox flows until commercial policy and provider configuration are approved.
- Email uses the configured provider; action links and credentials are never persisted in audit/evidence.
- Open owner policies in the SRS stay open and are not invented by this feature.
- Existing local data is preserved; tests use isolated or disposable data.


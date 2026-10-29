# FEAT-065 — Repair CI dependency and harness inputs

Owner: Person 2 (`AnhKhoaa157`). Date: 2026-10-29, Asia/Saigon.
Baseline: `feature/modal-vision-dev` at `07abfb321373678c3e81c195e5d278f576d5634b`.

CI run 40875382264 fails repository harness, backend dependency install and Admin/Teacher UI checks; Child UI succeeds. Source inspection confirms five missing evidence directories, a backend lockfile missing three declared dependencies and Node 22.13.0 below jsdom/undici locked engine requirements. Full archived logs are unavailable (GitHub HTTP 403), so UI engine mismatch is a confirmed configuration defect, not a confirmed exclusive cause of UI exit 1.

The owner authorized repair and publication: “ok v sửa đi nào thấy ok thì đẩy lên”. Existing branch only; preserve other feature plans/approvals and all local-only handoffs. No Modal, new branch, product-flow work, database/service or real-child data operation. Prior no-install preference remains: dependency resolution/lock metadata updates are permitted; do not install packages or replace existing virtualenvs.

- Status: DRAFT
- Owner:
- Goal:
- Scope:
- Non-goals:
- Dependencies:
- Risks:

## Context snapshot

Record the relevant product, user, technical, safety, and source context here. Link to global context and cite source IDs from `docs/context/SOURCE_REGISTER.md`.

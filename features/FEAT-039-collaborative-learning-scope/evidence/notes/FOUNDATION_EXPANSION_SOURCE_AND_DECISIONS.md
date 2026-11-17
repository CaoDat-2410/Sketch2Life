# System-foundation SRS expansion — source and authority

- Date: 2026-10-10, Asia/Saigon.
- Feature: FEAT-039, plan/task approval revision 3, documentation only.
- Owner request: “làm chi tiết hơn nữa, có thể hỏi 1 vài câu, đây sẽ dùng làm nền tảng cho cả cái hệ thống”.
- Source baseline: canonical Master SRS v3.0 and Product Scope v1.0 already reviewed in SOURCE_REVIEW.md. No new external handbook/workbook copy is introduced.

## Preservation

- Exact v2.0 working-copy preservation remains `artifacts/Sketch2Life_Master_SRS_v2.0_preserved_20261010.md`, SHA-256 `28eb8b890d8e950fec6aa0df87f9b29851a7e41aa871c3dd6eb4205cd807801e`.
- Exact v3.0 preservation is `artifacts/Sketch2Life_Master_SRS_v3.0_preserved_20261010.md`, SHA-256 `c69fd96ba9e5cd0ec85fcaa516c67ad73aafa02a45768dc2d93e29b7a756e2cf`.
- Original delivery `artifacts/Collaborative_Learning_SRS_v3.0.md` remains history. Current canonical will advance to v3.1 with an identical consolidated feature artifact.

## Direct owner answers for this expansion

1. “Một trường trước, chuẩn bị khả năng mở rộng”: one-school pilot; resource organization scope prepares expansion. This is not authorization for a full multi-tenant launch or a selected SaaS tenancy topology.
2. “Hồ sơ + QR/mã phiên, không tài khoản riêng”: managed profiles with session admission; no independent child login account. Pending device admission and scoped capability contracts are proposed implementation details, not verified child identity.
3. “Nhà trường thu consent, GV/Admin ghi nhận bằng chứng và phạm vi”: school collects legal-representative consent; authorized Teacher/Admin record evidence and purposes. Enrollment or adult role alone is not consent. Legal jurisdiction, representative verification details and data-request authority remain decision gates.

Follow-up direct answers received in the same task:

4. “Có, từ đủ 3 đến trước 13 tuổi”: 36–155 completed months inclusive. Exact date/timezone/leap-day calculations and mixed-age curriculum remain refinement.
5. “1 lớp, tối đa 40 trẻ”: simultaneous pilot target of one class and at most 40 children; no benchmark result implied. Devices/groups/network/AI concurrency are separate proposed load profiles.
6. “90 ngày sau khi phiên kết thúc”: default session/artwork retention 90 days after end. Profile/portfolio/audit/library/consent evidence and provider/backup/device-copy policies remain separate; raw-source retention cannot silently extend through a portfolio link.

## Technical reference verification

Primary references checked during drafting on 2026-10-10:

- [RFC 9110, If-Match](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-match): conditional HTTP mutation semantics; proposed aggregate commands use a strong version precondition and 412 on failed precondition. Canvas stroke append instead uses document/policy epochs and per-operation identity, so unrelated concurrent strokes do not need a shared head CAS.
- [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html): origin/auth/message authorization, size/rate controls and redacted logging inform the proposed transport contract. No live WebSocket implementation or security test was executed.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): deny by default and resource authorization on each operation inform scope and revocation probes. This source does not decide school/legal consent policy.

Technology references from the prior increment remain in SOURCE_REVIEW.md and REUSE_AND_ARCHITECTURE.md. No current dependency upgrade, model choice, cloud provisioning or performance claim follows from these references.

## Draft ownership and integration

- Root: B19 behavior/policy/state/concurrency/recovery, B26 verification/change gates and integration.
- Independent draft: B20 detailed use cases.
- Independent draft: B21 logical fields and B22 interfaces.
- Independent draft: B23 UX, B24 privacy and B25 quality measurement.
- Agents edit separate draft fragments; root integrates canonical and records cross-section QA. Draft fragments are working inputs, not additional independently authoritative SRS baselines.

## Validation boundary

This task validates documentation coverage, references, preserved hashes, approval and relevant repository architecture/security checks. It does not execute proposed acceptance cases against product runtime, train/test models, benchmark devices, handle real child data or establish legal compliance. Existing unrelated working-tree changes are preserved.

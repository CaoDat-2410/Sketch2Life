# MGR-1 owner disposition — School Manager API gaps

Date: 2026-11-17 (Asia/Saigon)

## Scope and source pins

This note records the owner's MGR-1 choices and separates them from technical contract work. It does not authorize API, persistence, UI, schema, migration, test, or runtime changes.

- MGR plan: `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT1_20261117.md`, pre-update 16,127 bytes, SHA-256 `4FC762ED54AF2422D1066CB40B40573D55B5191A3FC0CCFB9AB47C3D1DE50F00`.
- MGR plan after recording MGR-1: 18,974 bytes, SHA-256 `5E7CDB0AF03A27FF0DABFE949E41F7230D1BE7453EF56274E8CED388F6F196ED`.
- Owner-selected SRS review input: `D:\Zalo Received\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`. The header identifies Rev69, but the revision-history table ends at Rev68. The document is unsigned.
- Repository `docs/context/SRS_AUTHORITY.md` continues to identify the in-repository Rev60 as canonical. This task-specific owner-selected input does not update that authority pointer or replace the canonical file.

## Owner decisions — D-066-62

1. **Manager-to-Parent group discovery/invitation:** Do not enable it in the current Manager API closure. Keep it unavailable until a separately approved tenant-scoped discovery and invitation contract defines verified recipient binding, minimum visible fields, authority, acceptance, expiry, revocation, and audit. Do not guess identity references.
2. **Staff-created consent:** School Manager and Teacher cannot create or revoke effective Parent consent on the Parent's behalf. Parent remains the actor for Parent-profile sharing consent/grants. A staff-origin `pending` record is not effective Parent consent. A separate school-managed consent flow remains open and needs its own policy/contract approval.
3. **Teacher assignment candidates:** Only a verified Teacher principal belonging to the same organization is eligible. BE1 remains authoritative for organization, role, and current assignment facts; the server must validate scope and eligibility at assignment time. Candidate-read API shape and fields remain contract work.

## SRS disposition and remaining technical work

- **Class capacity:** Billing owns effective entitlement/capacity. SRS §21.2 calls for a transactional capacity check and `201` or `CLASS_CAPACITY_REACHED`. Do not create a class unless capacity is verified; exact retriable status/code when Billing cannot be read remains a MGR-2 contract detail.
- **Manager profile creation:** The current SRS explicitly identifies Teacher as the profile-creation actor and does not specify a Manager create flow. Keep it outside the present Manager closure unless a separate requirement is approved.
- **Membership:** Tenant-scoped membership/grant revocation is a target. The read fields, revision/ETag, stale behavior, and revoke replay contract remain for MGR-4.
- **Lesson review:** School Manager approval is required before Teacher-authored content becomes PUBLIC, and review must bind to the exact immutable version/hash. Exact-version read and review/publish event contracts remain for MGR-6.
- **Follow-on APIs:** Quota/billing, school feedback, and inbox/notifications remain separate MGR-10 slices. Q193 remains OPEN for video-quota purchase/allocation authority.

## Roadmap checkpoint

- MGR-0 source/evidence inventory: complete; no fresh runtime verification was claimed.
- MGR-1 owner-policy disposition: complete with this note and D-066-62.
- Next: MGR-2 contract design for Billing-owned class capacity, then MGR-3 to MGR-6 contract work as dependencies permit.
- MGR-7 must produce a separately approved implementation allowlist and Task Approval before any code or schema implementation. MGR-8 implementation and MGR-9 FE integration remain gated.

No tests, builds, validators, backend/runtime, database, Docker, provider, network, or Modal command was run for this disposition. No approval record, SRS, source code, or FE worktree was changed.

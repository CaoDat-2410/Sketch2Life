# FEAT-066 L1 — Seed data design — Draft 1

- **Status:** DRAFT / NOT APPROVED. Design only (Phase A of `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`). No script, database or command is authorized by this draft.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2 (lane L1 is the owner's own work).
- **Owner choice (O-SEED, 2026-11-18):** scope = all four roles as listed in Draft 4 L1.
- **SRS basis:** adopted working SRS (701,157 bytes, `B9B1F42D...`, D-209). Relevant rule: §24.1 — child media "demo chỉ dữ liệu tổng hợp"; synthetic profiles carry `data_origin` synthetic and no fake consent (§9.7 table row on consent).

## 1. Goal

One reproducible, idempotent synthetic seed that loads a disposable local database with enough data for every role flow in the FE, every Bruno request (lane L5) and manual demos. It does not replace the fixtures that PostgreSQL integration tests create for themselves (those tests require a database name containing `be1_acceptance` and set up their own rows).

## 2. Hard rules

1. Synthetic only. No real child, parent or school data. Child profiles use `SYNTHETIC_DEV` and ages 36–120 months (D-171 items 6 and 9).
2. No secret in Git: no password, Firebase credential, ID token or API key in the script, fixtures or Bruno environments. Adult identities are seeded by issuer + subject reference; signing in uses the existing local/synthetic verifier or the owner's local setup outside Git.
3. Target database guard: the script refuses to run unless the database name contains `seed` and the host is loopback; it never runs against `sketch2life_m2_s1a`, any `be1_acceptance` database used by tests, or a shared database. The URL comes from an environment variable and is never printed.
4. Every seeded row carries a seed marker (a fixed synthetic prefix on IDs or display names, plus the existing synthetic markers where the schema has them), so rows can be counted and, with separate approval, removed.
5. Idempotent: a second run on the same database changes nothing (upsert by stable seed keys) and reports zero new rows.
6. Writes go through existing repository/service code where it exists (so constraints and receipts behave as in the product); direct SQL only for tables with no write path, and each such case is listed in the implementation plan.
7. Schema is created by the normal Alembic upgrade to the pinned heads before seeding; the seed never alters schema.

## 3. Data set (per role)

| Area | Tables (current source) | Seed content |
|---|---|---|
| Platform Admin | `be1_adult_identities` (role Platform Admin) | 1 Platform Admin |
| Organizations | `be1_organizations` | 2 organizations (A, B) to exercise tenant isolation |
| School Manager | `be1_adult_identities`, `be1_organization_assignments` (`school_admin`) | 1 per organization |
| Teachers | same tables (role Teacher) | org A: 3 Teachers (2 assigned to classes, 1 verified but unassigned — the MGR-3 candidate case); org B: 1 Teacher; 1 Teacher account with no organization assignment (UC-13 gap case) |
| Classes | `be1_classrooms`, assignments | org A: 4 active classes (one with no Teacher); org B: 1 class. Later, with L2: classes up to the effective capacity and a suspended (read-only) class |
| Class profiles | `be1_managed_profiles`, `be1_enrollments` | 3–5 synthetic child profiles per class, ages spread across 36, 71, 72, 107, 108, 120 months; one enrollment active each |
| Parents | `be1_adult_identities` (role Parent) | 3 Parents (one with no child profile) |
| Parent child profiles | `parent.child_profiles`, `parent.profile_revisions`, `parent.command_receipts` | 1–2 per Parent, with one PATCH revision each; one profile in delete-pending state |
| Parent groups | `lesson.parent_groups`, `lesson.parent_group_members` | org A: 2 groups, members in active and revoked states (read paths only; invitation stays excluded) |
| Lessons | `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities`, `lesson.library_source_documents`, `lesson.library_document_revisions` | org A: 3 Teacher-authored lessons; one with 2 versions (for the superseded case of MGR-6); one PRIVATE, one SCHOOL, one awaiting PUBLIC review |
| Access grants | `lesson.access_grants` | pending, approved, revoked grants; one pending grant on a superseded version |
| StoryRuns | `story.runs`, `story.run_inputs`, related receipts | per Parent: one COMPLETED, one FAILED, one DELETE_PENDING, and at most one active run (`INPUT_PROCESSING` or `PREPARATION_REVIEW`) — respecting the one-active-run rule |
| Consent records | `be1_consent_records` | none (staff consent writes are excluded; Parent consent is not modelled) |
| Quota and subscription | Billing tables (do not exist yet) | added when L2 defines them: subscription ACTIVE / GRACE / RESTRICTED organizations; video-quota grants and usage for a Parent and an organization |
| Classroom/demo sessions | `be1_sessions` and related | out of scope unless the L3 audit shows an FE flow that needs them |

## 4. Deliverables of the later implementation task (not authorized here)

- One seed script (new file, location fixed in its Task Approval, for example under `backend/scripts/` or `tools/`), a small data module with the seed keys, and a unit test for the guard and idempotency logic.
- A short runbook: create the disposable seed database, run the Alembic upgrade, run the seed (one command), check row counts by marker.
- Optional: a Bruno environment file with placeholder IDs that match the seed keys (no tokens).

## 5. Acceptance (for the later task)

Guard refuses a wrong database; first run creates the documented row set; second run creates nothing; counts by marker match the table above; each role can open its main FE screen with data; no secret in the diff (security validator and a manual search).

## 6. Open points

- Seed write path per table (product service versus direct SQL) — settled in the implementation plan after reading each repository.
- Exact counts for capacity cases wait for the L2 capacity contract.
- Authentication for seeded adults in the local FE (existing synthetic verifier versus local Firebase emulator) — owner choice; no credential in Git either way.

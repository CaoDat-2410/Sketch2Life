# FEAT-066 L1 — Seed data design — Draft 2

- **Status:** DRAFT / NOT APPROVED / NOT REVIEWED. This is a design only. It authorizes no script, database or command.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Predecessor, unchanged:** Draft 1 (6,343 bytes, `E0EE5BED…`), not reviewed.
- **Why Draft 2:** Draft 1 left two things open: the Billing rows ("added when L2 defines them") and the capacity counts ("wait for the L2 capacity contract"). The Billing contract now defines them. Draft 2 fills them in and splits the seed into three stages that follow the Billing slices. It also links the A-1 register decisions that affect seed scope.
- **Inputs:**
  - Roadmap Draft 4 (`plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, `63710A9F…`), lane L1.
  - Billing contract Draft 7 (`plan/PLAN_L2_BILLING_CONTRACT_DRAFT7_20261118.md`, 49,498 bytes, `216B33D7B146E97DD2E0E99F13B034FC852A42E0933C9B30E520FF58DAB12BD0`). It is not independently reviewed, by owner instruction.
  - The Phase A register (`tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT1_20261118.md`, unreviewed).
  - Owner choice O-SEED (2026-11-18): all four roles.
- **SRS basis:** the adopted working SRS (701,157 bytes, `B9B1F42D…`, D-209), unsigned.
  - §24.1 requires synthetic demo data only.
  - Synthetic profiles carry a synthetic `data_origin` and no fake consent (the §9.7 consent row).
  - §23.1 says 10 base class slots plus paid add-ons.
  - §23.5 covers the video quota.

## 1. Goal

One reproducible, idempotent, synthetic seed for a disposable local database. It must give enough data for:
- every role flow in the FE;
- every Bruno request (lane L5);
- manual demos.

It does not replace the fixtures that PostgreSQL integration tests create for themselves. Those tests use a database whose name contains `be1_acceptance` and set up their own rows.

## 2. Hard rules

1. **Synthetic only.** No real child, parent or school data. Child profiles use `SYNTHETIC_DEV` and ages from 36 to 120 months (D-171 items 6 and 9).
2. **No secret in Git.** No password, Firebase credential, ID token or API key goes into the script, the fixtures or the Bruno environments. Adult identities are seeded by issuer and subject reference. Signing in uses the existing local or synthetic verifier, or the owner's local setup outside Git.
3. **Target database guard.** The script refuses to run unless:
   - the database name contains `seed`;
   - the host is loopback.
   It never runs against `sketch2life_m2_s1a`, any `be1_acceptance` database (including the P1 database `s2l_be1_acceptance`) or a shared database. It reads the URL from an environment variable and never prints it. A separate database such as `s2l_seed` on a disposable local server is enough.
4. **Seed marker.** Every seeded row carries one: a fixed synthetic prefix on IDs or display names, plus the existing synthetic markers where the schema has them. Rows can then be counted and, with separate approval, removed.
5. **Idempotent.** A second run on the same database changes nothing (upsert by stable seed keys) and reports zero new rows.
6. **Product write paths first.** Writes go through existing repository or service code where it exists, so constraints and receipts behave as in the product. Direct SQL is used only for tables that have no write path, and each such case is listed in the implementation plan.
7. **No cross-module writes into Billing.** Billing rows are created only through Billing's own commands and ports (Billing contract §7): `open_subscription`, Billing's environment-guarded price-version seed step, `VideoQuotaPortV1`, and the payment-fulfilment commands once the payment side supplies receipts. Nothing writes the `billing` schema directly. This mirrors the contract's "no cross-module table access" acceptance rule.
8. **Schema comes from Alembic.** The normal Alembic upgrade to the pinned heads (`upgrade heads`; the environment has several module branches) creates the schema before seeding. The seed never alters schema.

## 3. Stages (each stage needs the BE slices named; each runs only after its slices are verified)

| Stage | Needs | Content |
|---|---|---|
| **S1 — Core data** | Current schema on `dev` (no new slice) | Identities, organizations, assignments, classes, class profiles, Parents and Parent profiles, Parent groups, lessons and versions, access grants, StoryRuns (§4.1) |
| **S2 — Capacity basics** | Billing B-1, then B-2 | Local price version; one subscription per organization; an organization at capacity; the null-stamp path (§4.2) |
| **S3 — Lifecycle and payment-dependent states** | Billing B-4 (payment interface, agreed with the payment teammate), B-5, and a way to advance billing time locally (O-SEED-CLOCK) | Add-on slots, a scheduled downgrade, a suspended class, GRACE and RESTRICTED organizations (§4.3) |
| **S4 — Video quota** | Billing B-3 | Included monthly grant, usage, one exhausted scope (§4.4) |

S1 can be implemented as soon as its Task Approval exists. S2 to S4 are extensions of the same script, approved separately.

## 4. Data set

### 4.1 S1 — core data (per role)

| Area | Tables (current source) | Seed content |
|---|---|---|
| Platform Admin | `be1_adult_identities` (Platform Admin role) | 1 Platform Admin |
| Organizations | `be1_organizations` | **3 organizations:** A (main), B (tenant isolation), C (capacity case in S2); all `active` |
| School Manager | `be1_adult_identities`, `be1_organization_assignments` (`school_admin`) | 1 per organization |
| Teachers | same tables (Teacher role) | Org A: 3 Teachers. 2 are assigned to classes; 1 is verified but unassigned, which is the MGR-3 candidate case.<br>Org B: 1 Teacher.<br>Org C: 1 Teacher.<br>Plus 1 Teacher account with no organization assignment (the UC-13 gap case). |
| Classes | `be1_classrooms`, assignments | Org A: 4 active classes, one of them with no Teacher.<br>Org B: 1 class.<br>Org C: 10 active classes, exactly the base capacity (used in S2). Created through the product class-create path where it exists (after B-2: with an idempotency key, so receipts and the stamp behave as in the product). |
| Class profiles | `be1_managed_profiles`, `be1_enrollments` | 3–5 synthetic child profiles per class in org A, aged 36, 71, 72, 107, 108 and 120 months; one active enrollment each. Org B and org C: 1 profile per class. |
| Parents | `be1_adult_identities` (Parent role) | 3 Parents, one of them with no child profile |
| Parent child profiles | `parent.child_profiles`, `parent.profile_revisions`, `parent.command_receipts` | 1–2 per Parent, each with one PATCH revision; one profile in delete-pending state |
| Parent groups | `lesson.parent_groups`, `lesson.parent_group_members` | Org A: 2 groups, with members in active and revoked states. Read paths only; invitation stays excluded (MGR-4). |
| Lessons | `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities`, `lesson.library_source_documents`, `lesson.library_document_revisions` | Org A: 3 Teacher-authored lessons — one with 2 versions (the superseded case of MGR-6), one PRIVATE, one SCHOOL, one awaiting PUBLIC review |
| Access grants | `lesson.access_grants` | Pending, approved and revoked grants; one pending grant on a superseded version |
| StoryRuns | `story.runs`, `story.run_inputs`, related receipts | Per Parent: one COMPLETED, one FAILED, one DELETE_PENDING and at most one active run (`INPUT_PROCESSING` or `PREPARATION_REVIEW`), respecting the one-active-run rule |
| Consent records | `be1_consent_records` | None. Staff consent writes are excluded (MGR-5), and Parent consent has no contract yet (O-PCONSENT) |
| Classroom and device sessions | `be1_sessions` and related | Out of scope until O-L3SCOPE decides whether the 44 classroom/device operations are in scope |

### 4.2 S2 — capacity basics (after Billing B-1 and B-2)

| Item | Created through | Seed content |
|---|---|---|
| Price version | Billing's own seed step (contract §2, guarded by `env in {local, test}`) | One temporary version: `included_class_slots=10`, VND placeholders, the temporary monthly video units of Q-L2-5, `approved_by='seed-local'`. The seed script only triggers that step and never inserts the row itself |
| Subscriptions | `SubscriptionAdminPortV1.open_subscription`, or `open_subscriptions_for_existing_organizations()` | One `ACTIVE` subscription per organization (A, B, C), first period 10 + 0 |
| At capacity | Org C has 10 active classes against capacity 10 | The next create in org C returns 409 `CLASS_CAPACITY_REACHED` (a Bruno negative case) |
| Below capacity | Org A has 4 of 10 | Creates succeed |
| Stamp | `be1_organizations.capacity_version_seen` | Not written by the seed. It stays null (unknown) until the first product create, which exercises the null-stamp path of contract §4 step 3. The seed never writes the column (contract §4 rule 7d) |

### 4.3 S3 — lifecycle and payment-dependent states (after B-4 and B-5)

| Case | Needs | Proposed seed path |
|---|---|---|
| Add-on slots (org A: 10 + 2) | `activate_add_on_slots`, which requires a provider event receipt written by the payment side first | A local/test-only synthetic receipt path from the payment teammate (O-SEED-PAY) |
| Scheduled downgrade (org A: 10 + 2 down to 10 + 0, with 2 selected classes) | Add-on slots first; the BE1 downgrade use case through its internal command (contract §7.3; no public route) | After the add-on case: 6 active classes, 2 selected, so active − selected ≤ 10 |
| Suspended class | A downgrade that has taken effect at a period boundary (`settle_due_transitions`) | Needs billing time to pass the boundary: O-SEED-CLOCK |
| GRACE and RESTRICTED organizations | `record_renewal_outcome` with `FAILURE`, then the grace expiry | Needs O-SEED-PAY (receipts) and O-SEED-CLOCK (grace expiry) |
| Provider cancellation | `record_renewal_outcome` with `CANCELED_BY_PROVIDER` | Only after B-5, because the command is enabled only with its consumer (contract §6) |

### 4.4 S4 — video quota (after Billing B-3)

| Item | Created through | Seed content |
|---|---|---|
| Quota scopes and monthly grants | `VideoQuotaPortV1.admit_video_request` (a lazy grant on first use) | One Parent scope and the org A organization scope, each with this month's included grant |
| Usage | `admit_video_request` with synthetic request refs and stable keys (a replay returns the same usage) | Parent scope partly used; org A partly used |
| Exhausted scope | Repeated admissions up to the included units | One Parent scope at 0 available, so the next request returns 409 `VIDEO_QUOTA_EXCEEDED` (a Bruno negative case) |
| Top-up purchase | `issue_top_up_grant` (payment side) | Not seeded until O-SEED-PAY |

## 5. Deliverables of the later implementation task (not authorized here)

- One seed script (a new file whose location is fixed in its Task Approval), a small data module with the seed keys, and a unit test for the guard and idempotency logic.
- A short runbook:
  1. Create the disposable seed database.
  2. Run `upgrade heads`.
  3. Run the seed (one command per stage).
  4. Check row counts by marker.
- Optional: a Bruno environment file with placeholder IDs that match the seed keys (no tokens). It is written only after the owner has resolved O-TOKEN for `local.bru`.

## 6. Acceptance (for each stage's later task)

- The guard refuses a wrong database, including a `be1_acceptance` database.
- The first run creates the documented row set; the second run creates nothing.
- Counts by marker match the tables above.
- Each role can open its main FE screen with data.
- No secret appears in the diff (security validator plus a manual search).
- S2 and S4 only: the at-capacity and exhausted-scope cases return their 409 codes through the product path.

## 7. Open points

| ID | Question | Blocks |
|---|---|---|
| O-SEED-PAY | Will the payment teammate supply a local/test-only way to create provider event receipts, so the seed can call `activate_add_on_slots`, `record_renewal_outcome` and `issue_top_up_grant`? | S3 add-on, downgrade, GRACE, RESTRICTED; S4 top-up |
| O-SEED-CLOCK | How is billing time advanced locally: a test-only clock in Billing, or seeding with past period dates through a Billing command? Without one, suspended and GRACE/RESTRICTED cases cannot be produced by product paths | S3 suspended, GRACE, RESTRICTED |
| O-L3SCOPE | Whether classroom and device sessions are in scope (A-1 register §4) | Session seed data |
| O-PCONSENT | Parent consent contract | Consent seed data |
| — | Write path per table (product service versus direct SQL), settled in the implementation plan after reading each repository | S1 |
| — | Authentication for seeded adults in the local FE (existing synthetic verifier or a local Firebase emulator) — owner choice; no credential in Git either way | All stages |

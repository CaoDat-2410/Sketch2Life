# FEAT-066 L1 — Seed data design — Draft 3

- **Status:** DRAFT / NOT APPROVED / NOT RE-REVIEWED. Design only. It authorizes no script, database or command.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Predecessors, unchanged:**
  - Draft 2: 12,975 bytes, `0AF7B3655B9F69A26C4A839587AFE063E6E0489FD40DCF9E735E1397689FB629`. Its cold review (Sonnet 5.5 high, round 1) was NOT READY, 0 P1 / 5 P2 / 7 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT2_COLD_REVIEW_20261118.md`, 6,595 bytes, `6B99D395F9293C8A…`.
  - Draft 1: `E0EE5BED…`.
  - §9 records the disposition of S2-01 to S2-12.
- **Inputs:**
  - Roadmap Draft 4 lane L1: `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, `63710A9F…`.
  - Billing contract Draft 7: `plan/PLAN_L2_BILLING_CONTRACT_DRAFT7_20261118.md`, 49,498 bytes, `216B33D7…`. Not independently reviewed, by owner instruction.
  - Owner choice O-SEED (2026-11-18): all four roles.
  - Existing seed sources, cited as patterns and not reused as they are:
    - `features/FEAT-048-be2-content-publication/src/bootstrap_local_pg.py`;
    - the synthetic-pilot fixtures of `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`.
- **SRS basis:** adopted working SRS, 701,157 bytes, `B9B1F42D…` (D-209), unsigned. Clauses used:
  - §24.1: synthetic demo data only.
  - §9.7 consent row: synthetic profiles carry no fake consent. The SRS row names `data_origin=SYNTHETIC_TEST`, while the BE check constraint (`be1_models.py`, `data_origin IN ('REAL', 'SYNTHETIC_DEV', 'LEGACY_UNCLASSIFIED')`) and D-171 use `SYNTHETIC_DEV`. The seed follows the code value; the naming difference is left for SRS reconciliation (S2-10).
  - §23.1: 10 base class slots plus paid add-ons.
  - §23.3–§23.5.

## 1. Goal

One reproducible synthetic seed for a disposable local database. It gives every role flow in the FE, every Bruno request (L5) and manual demos the data they need. It does not replace the fixtures that PostgreSQL integration tests create for themselves.

## 2. Hard rules

1. **Synthetic only.** No real child, parent or school data. Child profiles use `data_origin = SYNTHETIC_DEV` with no consent and ages from 36 to 120 months.
2. **No secret in Git.** No password, Firebase credential, ID token or API key in the script, fixtures or Bruno environments. Adults are seeded by issuer and subject reference. Signing in uses the existing local or synthetic verifier, or the owner's setup outside Git.
3. **Target database guard (S2-05).** The seed reads one variable, `S2L_SEED_DATABASE_URL`, which is distinct from `BE1_TEST_DATABASE_URL` and from `SKETCH2LIFE_DATABASE_URL`. Before any write it requires all of the following:
   - (a) the database name contains `seed` and contains neither `be1_acceptance` nor `m2_s1a`;
   - (b) the host is loopback;
   - (c) `SKETCH2LIFE_ENV` is `local` or `test`.

   It then sets `SKETCH2LIFE_DATABASE_URL` for its own process to exactly that URL. A process environment variable overrides the root `.env` in the settings loader. After creating each engine — BE1's and Billing's own pool — it checks that the engine's database name and host equal the guarded values, and it aborts on any difference. It never prints the URL. Alembic is not run by the seed: the runbook runs it separately with the same variable.
4. **Seed marker, defined per table (S2-06):**
   - **Text-ID tables:** a `seed-` prefix on the stable ID (for example `seed-org-a`).
   - **Tables with a display name:** a `[SEED]` prefix on the name.
   - **UUID-ID tables:** deterministic UUIDv5 values from one fixed seed namespace and the seed key, so the same key always gives the same ID.
   - **Hash and receipt tables:** counted by tracing their foreign keys to seeded roots.
   - **Billing rows:** never written by the seed. They are counted through the seeded organization and scope refs.

   The implementation plan includes one count query per table.
5. **Idempotent, within one billing month (S2-08).** A second run in the same month changes nothing and reports zero new rows. Direct SQL upserts on the stable IDs; Billing and product commands use stable idempotency keys (`seed:<stage>:<case>`).
   Seeded state decays: monthly grants expire at month end, and local roll-over applies due transitions. The re-seed procedure is therefore: drop and recreate the disposable seed database, run `upgrade heads`, then run the stages again. Bruno negative cases that depend on quota or period state are marked time-sensitive in L5.
6. **Write paths (S2-11).**
   - **S1 is direct SQL** into BE1, Parent, Lesson Library and Story tables, with the stable IDs above. The existing bootstrap scripts (`be1_bootstrap.py`, `bootstrap_platform_admin.py`) are not used: they need a token or e-mail and are single-shot. Class and profile creation today are HTTP route functions with random IDs, and the profile route needs local/test plus `synthetic_pilot_enabled`.
   - **S2 onward** use only product and Billing commands; §4 lists each one.
7. **No writes into the `billing` schema.** Billing rows come only from Billing's commands and ports (contract §7) and its env-guarded price-version step.
8. **Schema from Alembic.** `upgrade heads` (several module branches) creates the schema before seeding. The seed never alters schema.

## 3. Stages and their dependencies (S2-02, S2-07)

| Stage | Needs (all verified and on the seed's base) | Content |
|---|---|---|
| **S1 — core data, direct SQL** | Current `dev` schema | Identities, all organizations, assignments, classes, class profiles, Parents and Parent profiles, Parent groups, lessons and versions, grants, StoryRuns (§4.1) |
| **S2 — capacity basics** | Billing B-1 and B-2; S1 | Billing's local price-version step; `open_subscriptions_for_existing_organizations()`; **one real product class create** in org A with the stable key `seed:s2:orgA:create-1`, which exercises the null-stamp path (§4.2) |
| **S3 — lifecycle states** | Billing B-4 (payment interface) and B-5; S2; **O-SEED-PAY** (local/test receipts); **O-SEED-CLOCK** (advancing billing time); for the suspended class, also the outbox publisher or sweep runner and the BE1 suspension consumer (Billing §7.6; runner still open) | Add-on, scheduled downgrade, applied downgrade with suspended classes, GRACE, RESTRICTED, provider-canceled (§4.3) |
| **S4 — video quota** | Billing B-1 (price version gives the units), B-3, and S2 (an organization scope needs a subscription; contract §7.2) | Grants, usage, an exhausted scope (§4.4) |

**Stage order:** S1, then S2. S3 and S4 come after S2 and are independent of each other.
- **Before B-2 exists,** S1 classes are written by direct SQL, so they need neither a subscription nor a key.
- **After B-2,** the product create path is used only for the one S2 create and for the S3 creates.

## 4. Data set

### 4.1 S1 — core data

**Organizations and their cases (S2-03).** S1 creates all of them, `active`, with the class counts below. The Billing states come in S2 and S3.

| Org | Purpose | Classes in S1 | Billing state reached in |
|---|---|---:|---|
| A | Main demo; below capacity | 4 (one with no Teacher) | S2: ACTIVE 10 + 0 |
| B | Tenant isolation | 1 | S2: ACTIVE |
| C | At capacity | 10 | S2: ACTIVE 10 + 0, so the next create gives 409 `CLASS_CAPACITY_REACHED` |
| D | Add-on, then scheduled downgrade | 10 | S3: add-on to 10 + 2, two more classes by product create (12 active); downgrade to 10 + 0 with 2 selected classes |
| E | Applied downgrade with suspended classes | 10 | S3: same steps as D, then the period boundary passes: 2 classes suspended, 10 active |
| F | GRACE | 2 | S3: renewal FAILURE, period end passed |
| G | RESTRICTED | 2 | S3: FAILURE with a period that ended at least 7 days ago (the grace length, Billing §6) |
| H | Provider-canceled | 2 | S3 (after B-5): `CANCELED_BY_PROVIDER` |

**Other S1 content:**

| Area | Tables (current source) | Seed content |
|---|---|---|
| Platform Admin | `be1_adult_identities` | 1 |
| School Manager | `be1_adult_identities`, `be1_organization_assignments` (`school_admin`) | 1 per organization |
| Teachers | same tables | Org A: 3 (2 assigned; 1 verified but unassigned — the MGR-3 candidate case). Orgs B–H: 1 each. Plus 1 Teacher with no organization (the UC-13 gap case) |
| Classes | `be1_classrooms` and assignments | as in the organization table; IDs `seed-org-<x>-class-<n>` |
| Class profiles | `be1_managed_profiles`, `be1_enrollments` | Org A: 3–5 per class, aged 36, 54, 78, 96 and 120 months. The ages spread across the 3–10 year range without claiming any age-band boundary, because D-171 item 6 and Q-05 leave the bands open (S2-09). Orgs B–H: 1 per class |
| Parents and their profiles (S2-09) | `be1_adult_identities`; `parent.child_profiles`, `parent.profile_revisions`, `parent.command_receipts` | P1 with K1 (active, one PATCH revision) and K2 (delete-pending). P2 with K3 (active, one PATCH revision). P3 with no profile |
| Parent groups (S2-01) | **`be1_parent_groups`, `be1_parent_group_members`** (default schema; migration `20261028_ll_0001`) | Org A: 2 groups; members in `ACTIVE` and `REVOKED` states. Read paths only; invitation stays excluded (MGR-4) |
| Lessons | `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities`, `lesson.library_source_documents`, `lesson.library_document_revisions` | Org A: 3 Teacher-authored lessons. L1 has 2 versions; `current_version_id` points to the second, which creates the superseded case for MGR-6. L2 is PRIVATE; L3 is SCHOOL with `review_state = PENDING_REVIEW` for PUBLIC |
| Access grants (S2-09) | `lesson.access_grants` | One grant each in `PENDING_REVIEW`, `ACTIVE` and `REVOKED`. "Superseded" is not a stored state: it is the `PENDING_REVIEW` grant on L1's first version, whose version is no longer `current_version_id` |
| StoryRuns (S2-09) | `story.runs`, `story.run_inputs`, related receipts | P1/K1: one COMPLETED, one FAILED, one DELETE_PENDING and one active (`INPUT_PROCESSING`). P2/K3: one COMPLETED and one active (`PREPARATION_REVIEW`). K2 (delete-pending) and P3 (no profile) have no runs. This respects the one-active-run rule (`uq_story_run_active_parent`) |
| Consent records | `be1_consent_records` | None: MGR-5 is excluded and O-PCONSENT is open |
| Classroom and device sessions | `be1_sessions` and related | Out of scope until O-L3SCOPE is decided |

### 4.2 S2 — capacity basics (after Billing B-1 and B-2)

| Item | Created through | Result |
|---|---|---|
| Price version | Billing's env-guarded seed step (contract §2) | `included_class_slots = 10`, VND placeholders, temporary video units of Q-L2-5, `approved_by = 'seed-local'` |
| Subscriptions | `open_subscriptions_for_existing_organizations()` | Orgs A–H ACTIVE, 10 + 0 |
| Null-stamp path | One product class create in org A, key `seed:s2:orgA:create-1` | Org A gets 5 classes, and its `capacity_version_seen` is set by the product path (rule 7a). Orgs B–H keep null, so both stamp states exist. The seed never writes the column itself |
| At capacity | Org C: 10 of 10 | Bruno negative: the next create gives 409 |

### 4.3 S3 — lifecycle (after B-4 and B-5, O-SEED-PAY, O-SEED-CLOCK)

| Org | Steps (all through Billing or BE1 commands with stable keys) |
|---|---|
| D | `activate_add_on_slots` (+2; payment-side synthetic receipt), giving capacity 12. Two product creates (12 active). Downgrade use case through its internal command: target 10 + 0, 2 selected. The check active − selected = 10 ≤ 10 passes; admission capacity = min(12, 10 + 2) = 12, so the organization is full |
| E | The same as D, then billing time passes the period boundary (O-SEED-CLOCK), `settle_due_transitions` runs, the publisher delivers the suspension event, and BE1 suspends the 2 selected classes: 10 active + 2 suspended against capacity 10 |
| F | `record_renewal_outcome(FAILURE)` with a synthetic receipt; period end passed, so GRACE |
| G | As F, with the period ended at least 7 days earlier, so RESTRICTED: a create gives 409 `SUBSCRIPTION_RESTRICTED` |
| H | `record_renewal_outcome(CANCELED_BY_PROVIDER)` (only after B-5) |

### 4.4 S4 — video quota (after B-1, B-3 and S2)

| Item | Created through | Result |
|---|---|---|
| Grants | `admit_video_request` (lazy monthly grant) | A P1 scope and an org A scope, each with this month's included grant |
| Usage | `admit_video_request` with keys `seed:s4:<scope>:<n>` | Partly used |
| Exhausted | Admissions up to the included units for P2's scope | The next request gives 409 `VIDEO_QUOTA_EXCEEDED` (time-sensitive) |
| Top-up | `issue_top_up_grant` | Only with O-SEED-PAY |

## 5. Deliverables of the later implementation task (not authorized here)

- One seed script per stage, or one script with a stage argument. The location is fixed in the Task Approval.
- A data module holding the seed keys and the UUIDv5 namespace.
- A unit test for the guard, the marker rules and idempotency.
- A runbook covering the database, `upgrade heads`, the stages, the count queries and the re-seed procedure.
- Optional: a Bruno environment with placeholder IDs, written only after the owner has resolved O-TOKEN.

## 6. Acceptance (for each stage's later task)

- The guard refuses each of these: a wrong database name, a `be1_acceptance` or `m2_s1a` database, a non-loopback host, an env outside local/test, and a mismatched engine URL.
- The first run creates the documented rows; a second run in the same month creates none.
- The counts per table match.
- Each role can open its main FE screen with data.
- The diff contains no secret (security validator plus a manual search).
- **S2–S4 only:** the 409 cases return their codes through the product path.

## 7. Open points

| ID | Question | Blocks |
|---|---|---|
| O-SEED-PAY | A local/test-only way to create provider event receipts, supplied by the payment teammate | S3 D, E, F, G, H; S4 top-up |
| O-SEED-CLOCK | How billing time is advanced locally: a test-only clock in Billing, or period dates set through a Billing command | S3 E, F, G |
| Outbox publisher / sweep runner | Billing §6/§7.6, owner choice | S3 E (suspension) |
| O-L3SCOPE | Classroom and device sessions in scope? | Session seed data |
| O-PCONSENT | Parent consent contract | Consent seed data |
| SRS naming | `SYNTHETIC_TEST` (SRS §9.7) versus `SYNTHETIC_DEV` (code) | none; SRS reconciliation note |
| Local FE authentication for seeded adults | Synthetic verifier or a local Firebase emulator; no credential in Git | All stages |

## 8. Not verified

- Whether direct Story inserts need asset or metadata rows. This is checked in the implementation plan.
- The Q-L2-5 unit value.
- The exact wording of D-171 item 9.
- Every FE screen.

## 9. Disposition of the Draft 2 review (not re-reviewed)

| ID | Disposition |
|---|---|
| S2-01 | §4.1 Parent groups: `be1_parent_groups`, `be1_parent_group_members` |
| S2-02 | §2 rule 6 and §3: S1 classes by direct SQL; one product create in S2 with a stable key for the null-stamp path; §4.2 stamp wording corrected |
| S2-03 | §4.1 organization-to-case table A–H |
| S2-04 | Org A stays below capacity (4, then 5); the downgrade cases move to D and E with 12 active on 10 + 2 and 2 selected |
| S2-05 | §2 rule 3: named variable, resolved-URL check on every engine, env local/test, no Alembic from the seed |
| S2-06 | §2 rule 4: marker per table kind, count query per table |
| S2-07 | §3 Needs: S4 needs B-1 and S2; suspension needs the publisher and the consumer; RESTRICTED needs 7 days; cancellation needs receipts |
| S2-08 | §2 rule 5: idempotent within one month; re-seed procedure; time-sensitive Bruno negatives |
| S2-09 | §4.1: Parent/profile pairs; grant code states; superseded derived; age rationale |
| S2-10 | Header SRS basis: `SYNTHETIC_TEST` vs `SYNTHETIC_DEV` noted |
| S2-11 | §2 rule 6: S1 direct SQL; bootstrap scripts not used; existing sources cited |
| S2-12 | §7: publisher/sweep runner added; guard URL source settled in §2 rule 3 |

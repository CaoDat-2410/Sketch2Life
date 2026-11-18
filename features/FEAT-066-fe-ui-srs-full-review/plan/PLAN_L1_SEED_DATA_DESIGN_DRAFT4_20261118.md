# FEAT-066 L1 — Seed data design — Draft 4

- **Status:** DRAFT / NOT APPROVED / NOT RE-REVIEWED. Design only. It authorizes no script, database or command.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Predecessors, unchanged:**
  - Draft 3: 16,100 bytes, `FDF40929A431CDC01B7376D96BA6FBC5CB2096FD1D87796E3F8E5CC3A5F0CE7E`. Its cold review (Sonnet 5.5, effort set to high by the caller, round 2) was NOT READY, 0 P1 / 2 P2 / 6 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT3_COLD_REVIEW_20261118.md`, 6,316 bytes, `F460971A01C6D8E2…`.
  - Draft 2: 12,975 bytes, `0AF7B365…`. Its round-1 review was NOT READY, 0 P1 / 5 P2 / 7 P3, record `6B99D395…`.
  - Draft 1: `E0EE5BED…`.
  - §9 records the disposition of S3-01 to S3-08 and of S2-01 to S2-12.
- **Inputs:**
  - Roadmap Draft 4 lane L1: `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, `63710A9F…`.
  - Billing contract Draft 7: `plan/PLAN_L2_BILLING_CONTRACT_DRAFT7_20261118.md`, 49,498 bytes, `216B33D7…`. It is not independently reviewed, by owner instruction.
  - Owner choice O-SEED (2026-11-18): all four roles.
  - Existing seed sources, used as patterns only:
    - `features/FEAT-048-be2-content-publication/src/bootstrap_local_pg.py`;
    - the synthetic-pilot fixtures of `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`.
- **SRS basis:** the adopted working SRS, 701,157 bytes, `B9B1F42D…` (D-209), unsigned. Clauses used:
  - §24.1: demos use synthetic data only.
  - §9.7 consent row: synthetic profiles carry no fake consent. The SRS row names `data_origin=SYNTHETIC_TEST`, but the BE check constraint (`be1_models.py`) and D-171 use `SYNTHETIC_DEV`. The seed follows the code, and the name difference is left for SRS reconciliation.
  - §23.1: 10 base class slots plus paid add-ons.
  - §23.3–§23.5.

## 1. Goal

One reproducible synthetic seed for a disposable local database. It gives every FE role flow, every Bruno request (L5) and manual demos the data they need. It does not replace the fixtures that PostgreSQL integration tests create for themselves.

## 2. Hard rules

1. **Synthetic only.** No real child, parent or school data. Child profiles use `data_origin = SYNTHETIC_DEV` with no consent and ages from 36 to 120 months.
2. **No secret in Git.** No password, Firebase credential, ID token or API key goes into the script, the fixtures or the Bruno environments. Adults are seeded by issuer and subject reference.
3. **Target database guard (S2-05, S3-03).** The seed reads one variable, `S2L_SEED_DATABASE_URL`. It is distinct from `BE1_TEST_DATABASE_URL` and from `SKETCH2LIFE_DATABASE_URL`.

   **Checks before any settings are read.** These run before the seed imports or calls anything that reads settings. All must pass:
   - (a) The database name contains `seed`, and contains neither `be1_acceptance` nor `m2_s1a`.
   - (b) The URL has an explicit loopback host (`127.0.0.1`, `::1` or `localhost`) and an explicit port. The seed refuses:
     - a missing host;
     - a `host` or `hostaddr` query parameter;
     - any of `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGSERVICE` set in the environment.
   - (c) `S1A_P_ALEMBIC_DATABASE_URL` and `STORYRUN_LITE_DATABASE_URL` are unset, or equal to the guarded URL.

   **Then:**
   - It sets `SKETCH2LIFE_DATABASE_URL` for its own process to exactly the guarded URL.
   - It clears the `lru_cache` of `get_settings()` and `get_core_database_settings()`.
   - It requires the **resolved** `settings.env` to be `local` or `test`. An unset variable resolves to local; that is accepted only together with (a) and (b).
   - Every engine it uses, including Billing's own pool, is created with the explicit URL (`create_core_engine(database_url)`).
   - Before any write, it compares each engine's database name, host and port with the guarded values, and aborts on any difference.
   - It never prints the URL.

   **The seed never creates, drops or migrates a database.** Alembic `upgrade heads` and the drop and recreate of rule 5 are runbook steps that the owner runs with the same URL, with `S1A_P_ALEMBIC_DATABASE_URL` unset.
4. **Seed marker, defined per table (S2-06, S3-07):**
   - **Text-ID tables:** a `seed-` prefix on the stable ID, kept within 36 characters, because several primary keys are `String(36)`. Example: `seed-org-a`.
   - **Tables with a display name:** a `[SEED]` prefix on the name.
   - **UUID columns:** deterministic UUIDv5 values from one fixed seed namespace and the seed key. This includes the unique, non-primary-key `be1_adult_identities.account_id`.
   - **Hash and receipt tables:** counted by tracing their foreign keys to seeded roots. `parent.command_receipts` has no foreign key, so it is counted by the seeded principal.
   - **Rows created by product commands:** these have random IDs and carry only the `[SEED]` name marker. They are counted per seeded organization.
   - **Billing rows:** never written by the seed. They are counted through the seeded organization and scope refs.

   **Column rules from source:**
   - `parent.profile_revisions.revision_hash` is computed with the domain snapshot function, not typed in.
   - Managed profiles use `age_source = SYNTHETIC_FIXTURE`.
   - The time-limited `be1_synthetic_eligibility_proofs` are **not seeded**: they expire, and the synthetic-pilot flow creates its own.

   The implementation plan includes one count query per table.
5. **Idempotent within one subscription period and one calendar month (`Asia/Ho_Chi_Minh`) (S2-08, S3-06).**
   - A second run inside both windows, and before any billing-time advance, changes nothing and reports zero new rows.
   - Direct SQL upserts on the stable IDs.
   - Billing and product commands use stable idempotency keys (§4.5). Change group refs derive from (organization, principal, key), so they are stable too.
   - Payment-side receipts used by the seed carry deterministic IDs `seed-receipt-<org>-<case>`.
   - `settle_due_transitions` runs at the start of every Billing command. A run after a period or month boundary is therefore a **re-seed**, not a replay.

   **Re-seed procedure (owner, runbook):** drop and recreate the disposable seed database, run `upgrade heads`, then run the stages again. Bruno negative cases that depend on quota or period state are marked time-sensitive in L5.
6. **Write paths (S2-11, S3-05).**
   - **S1 is direct SQL** into BE1, Parent, Lesson Library and Story tables, with the stable IDs above. The existing bootstrap scripts are not used: they need a token or an e-mail, and they run only once.
   - **S2 onward** use only product and Billing commands; §4 lists each one.
   - **Actor for product commands:** the seed calls the BE1 application commands in-process, as the organization's seeded School Manager (issuer and subject from the seed data). It does not go through HTTP and needs no token.
     - If a command exists only as an HTTP route function, the implementation plan does one of two things:
       - extracts the application command, in the slice that owns it; or
       - uses the existing local/synthetic verifier path.
     - In either case, no credential goes into Git.
7. **No writes into the `billing` schema.** Billing rows come only from Billing's commands and ports (contract §7) and from its env-guarded price-version step.
8. **Schema from Alembic.** `upgrade heads` creates the schema before seeding; the environment has several module branches. The seed never alters schema.

## 3. Stages and their dependencies

| Stage | Needs (all verified and on the seed's base) | Content |
|---|---|---|
| **S1 — core data, direct SQL** | Current `dev` schema | Identities, all organizations, assignments, classes, class profiles, Parents and Parent profiles, Parent groups, lessons and versions, grants, StoryRuns (§4.1) |
| **S2 — capacity basics** | Billing B-1 and B-2; S1 | Billing's local price-version step; `open_subscriptions_for_existing_organizations()`; one real product class create in org A, which exercises the null-stamp path (§4.2) |
| **S3 — lifecycle states** | Billing B-4 (payment interface) and B-5; S2; **O-SEED-PAY** (local/test receipts); **O-SEED-CLOCK — a hard dependency** (§7); for the suspended class, also the outbox publisher or sweep runner and the BE1 suspension consumer (Billing §7.6; the runner is still open) | Add-on, scheduled downgrade, applied downgrade with suspended classes, GRACE, RESTRICTED, provider-canceled (§4.3) |
| **S4 — video quota** | Billing B-1 (the price version gives the units), B-3; S2 (an organization scope needs a subscription); **after S3** | Grants, usage, an exhausted scope (§4.4) |

**Stage order (S3-02):** S1, then S2, then S3, then S4.
- **S4 runs last**, because advancing billing time also expires the monthly grants.
- **With per-organization billing time control** (the preferred O-SEED-CLOCK answer), the order inside S3 is free.
- **With only a global test clock**, S3 runs in this fixed order:
  1. Set up E (add-on, creates, downgrade) and G (renewal FAILURE).
  2. Advance billing time once, past E's period end and past G's `grace_until`. Run `settle_due_transitions` for E and G, and let the publisher and the BE1 consumer apply E's suspension.
  3. Only then set up D (a scheduled downgrade, which must not reach its boundary), F (a FAILURE that stays in GRACE) and H (provider cancellation).
  4. The advance also rolls over A, B and C (local auto-renew). Their capacity does not change; this is accepted.
- **Before B-2 exists,** S1 classes are written by direct SQL and need neither a subscription nor a key. **After B-2,** the product create path is used only for the S2 create and the S3 creates.

## 4. Data set

### 4.1 S1 — core data

**Organizations and their cases.** S1 creates all of them as `active`, with the class counts below. The Billing states come in S2 and S3.

| Org | Purpose | Classes in S1 | Billing state reached in |
|---|---|---:|---|
| A | Main demo, below capacity | 4 (one with no Teacher) | S2: ACTIVE 10 + 0 |
| B | Tenant isolation | 1 | S2: ACTIVE |
| C | At capacity | 10 | S2: ACTIVE 10 + 0. The next create returns 409 `CLASS_CAPACITY_REACHED` |
| D | Add-on, then scheduled downgrade | 10 | S3: add-on to 10 + 2; two product creates (12 active); downgrade to 10 + 0 with 2 selected |
| E | Applied downgrade with suspended classes | 10 | S3: the same as D; then billing time passes the period boundary, leaving 2 suspended and 10 active |
| F | GRACE | 2 | S3: renewal FAILURE recorded while ACTIVE. No time advance is needed, because grace starts at the failure time |
| G | RESTRICTED | 2 | S3: renewal FAILURE recorded while ACTIVE; then billing time advances past `grace_until` = max(failure time, period end) + 7 days (Billing §6); then `settle_due_transitions` (S3-01) |
| H | Provider-canceled | 2 | S3 (after B-5): `CANCELED_BY_PROVIDER` |

**Other S1 content:**

| Area | Tables (current source) | Seed content |
|---|---|---|
| Platform Admin | `be1_adult_identities` | 1 |
| School Manager | `be1_adult_identities`, `be1_organization_assignments` (`school_admin`) | 1 per organization |
| Teachers | same tables | Org A: 3 — 2 assigned, and 1 verified but unassigned (the MGR-3 candidate case). Orgs B–H: 1 each. Plus 1 Teacher with no organization (the UC-13 gap case) |
| Classes | `be1_classrooms` and assignments | Per the organization table. IDs are `seed-org-<x>-class-<n>` |
| Class profiles | `be1_managed_profiles`, `be1_enrollments` | Org A: 3–5 per class, aged 36, 54, 78, 96 and 120 months, with `age_source = SYNTHETIC_FIXTURE`. These ages spread across 3–10 years without claiming any age-band boundary; D-171 item 6 and Q-05 leave the bands open. Orgs B–H: 1 per class |
| Parents and their profiles | `be1_adult_identities`; `parent.child_profiles`, `parent.profile_revisions`, `parent.command_receipts` | P1 with K1 (active, one PATCH revision) and K2 (delete-pending). P2 with K3 (active, one PATCH revision). P3 with no profile |
| Parent groups (S3-04) | `be1_parent_groups`, `be1_parent_group_members` (default schema; migration `20261028_ll_0001`) | Org A: 2 groups in state `active`. Members in states `active` and `revoked` (lowercase code values), each with the required `expires_at`. Read paths only; invitation stays excluded (MGR-4) |
| Lessons (S3-08) | `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities`, `lesson.library_source_documents`, `lesson.library_document_revisions` | Org A: 3 Teacher-authored lessons:<br>- L1 has 2 versions, and `current_version_id` points to the second. This creates the superseded case for MGR-6.<br>- L2 has visibility PRIVATE.<br>- L3 has visibility SCHOOL, and its latest `library_versions` row has `review_state = PENDING_REVIEW`, the request for PUBLIC.<br>Visibility and `review_state` are separate columns on different tables. |
| Access grants | `lesson.access_grants` | One grant each in `PENDING_REVIEW`, `ACTIVE` and `REVOKED`. "Superseded" is not a stored state: it is the `PENDING_REVIEW` grant on L1's first version, which is no longer `current_version_id` |
| StoryRuns | `story.runs`, `story.run_inputs`, related receipts | P1/K1: one COMPLETED, one FAILED, one DELETE_PENDING and one active run (`INPUT_PROCESSING`). P2/K3: one COMPLETED and one active run (`PREPARATION_REVIEW`). K2 (delete-pending) and P3 (no profile) have no runs. This respects the one-active-run rule (`uq_story_run_active_parent`) |
| Consent records | `be1_consent_records` | None: MGR-5 is excluded and O-PCONSENT is open |
| Synthetic eligibility proofs | `be1_synthetic_eligibility_proofs` | Not seeded: they are time-limited, and the synthetic-pilot flow creates its own |
| Classroom and device sessions | `be1_sessions` and related | Out of scope until O-L3SCOPE is decided |

### 4.2 S2 — capacity basics (after Billing B-1 and B-2)

| Item | Created through | Result |
|---|---|---|
| Price version | Billing's env-guarded seed step (contract §2) | `included_class_slots = 10`, VND placeholders, the temporary video units of Q-L2-5, `approved_by = 'seed-local'` |
| Subscriptions | `open_subscriptions_for_existing_organizations()` | Orgs A–H become ACTIVE, 10 + 0 |
| Null-stamp path | One product class create in org A, with key `seed:s2:orgA:create-1`, run as A's seeded School Manager | Org A gets its 5th class, and its `capacity_version_seen` is set by the product path (rule 7a). Orgs B–H keep null, so both stamp states exist. The seed never writes the column itself |
| At capacity | Org C: 10 of 10 | Bruno negative: the next create returns 409 |

### 4.3 S3 — lifecycle (after B-4 and B-5, O-SEED-PAY and O-SEED-CLOCK; order per §3)

| Org | Steps (all through Billing or BE1 commands with the keys of §4.5) |
|---|---|
| D | 1. `activate_add_on_slots` (+2, receipt `seed-receipt-D-addon`) gives capacity 12.<br>2. Two product creates give 12 active.<br>3. The downgrade use case, through its internal command, targets 10 + 0 with 2 selected. Its check passes: active − selected = 10 ≤ 10.<br>4. Admission capacity = min(12, 10 + 2) = 12, so the organization is full. |
| E | 1. The same steps as D, with E's keys.<br>2. Billing time passes the period boundary.<br>3. `settle_due_transitions` runs, the publisher delivers the suspension event, and BE1 suspends the 2 selected classes.<br>4. Result: 10 active + 2 suspended against capacity 10. |
| F | `record_renewal_outcome(FAILURE)` while ACTIVE (receipt `seed-receipt-F-failure`) gives GRACE, with no time advance |
| G | 1. `record_renewal_outcome(FAILURE)` while ACTIVE (receipt `seed-receipt-G-failure`).<br>2. Billing time advances past `grace_until`.<br>3. `settle_due_transitions` gives RESTRICTED: a create returns 409 `SUBSCRIPTION_RESTRICTED`. |
| H | `record_renewal_outcome(CANCELED_BY_PROVIDER)` (receipt `seed-receipt-H-cancel`), only after B-5 |

### 4.4 S4 — video quota (after B-1, B-3, S2 and S3)

| Item | Created through | Result |
|---|---|---|
| Grants | `admit_video_request` (lazy monthly grant) | A P1 scope and an org A scope, each with this month's included grant |
| Usage | `admit_video_request` with keys `seed:s4:<scope>:<n>` | Partly used |
| Exhausted | Admissions up to the included units for P2's scope | The next request returns 409 `VIDEO_QUOTA_EXCEEDED` (time-sensitive) |
| Top-up | `issue_top_up_grant` | Only with O-SEED-PAY |

### 4.5 Idempotency keys and receipt IDs used by the seed (S3-05, S3-06)

| Stage | Key or receipt ID | Command |
|---|---|---|
| S2 | `seed:s2:orgA:create-1` | Class create, org A |
| S3 | `seed-receipt-D-addon`, `seed-receipt-E-addon` | `activate_add_on_slots` for D and E |
| S3 | `seed:s3:orgD:create-1`, `seed:s3:orgD:create-2`, `seed:s3:orgE:create-1`, `seed:s3:orgE:create-2` | Class creates after the add-on |
| S3 | `seed:s3:orgD:downgrade-1`, `seed:s3:orgE:downgrade-1` | Downgrade use case. The change group ref derives from organization, School Manager principal and key |
| S3 | `seed-receipt-F-failure`, `seed-receipt-G-failure`, `seed-receipt-H-cancel` | `record_renewal_outcome` |
| S4 | `seed:s4:<scope>:<n>` | `admit_video_request` |

## 5. Deliverables of the later implementation task (not authorized here)

- One seed script per stage, or one script that takes a stage argument. Its location is fixed in the Task Approval.
- A data module holding the seed keys, the receipt IDs and the UUIDv5 namespace.
- A unit test for the guard (every refusal case of rule 3), the marker rules and idempotency.
- A runbook covering:
  - creating the database and running `upgrade heads`, with `S1A_P_ALEMBIC_DATABASE_URL` unset;
  - the stages and the S3 order;
  - the count queries;
  - the re-seed procedure.
- Optional: a Bruno environment with placeholder IDs. It is written only after the owner has resolved O-TOKEN.

## 6. Acceptance (for each stage's later task)

- **The guard refuses each case below:**
  - a wrong database name, or a `be1_acceptance` or `m2_s1a` database;
  - a missing or non-loopback host, or a host or port given through a query parameter or a `PG*` variable;
  - a conflicting alternate URL variable;
  - an env outside local/test;
  - a mismatched engine URL.
- The first run creates the documented rows. A second run inside the rule-5 windows creates none.
- The counts per table match.
- Each role can open its main FE screen with data.
- The diff contains no secret (security validator plus a manual search).
- **S2–S4 only:** the 409 cases return their codes through the product path.

## 7. Open points

| ID | Question | Blocks |
|---|---|---|
| O-SEED-PAY | Can the payment teammate supply a local/test-only way to create provider event receipts, with deterministic IDs? | S3 D, E, F, G, H; S4 top-up |
| O-SEED-CLOCK | **Hard dependency.** How is billing time advanced locally?<br>- **Preferred:** a test-only, per-organization clock offset in Billing (local/test only).<br>- **Otherwise:** a global test clock, used with the fixed S3 order of §3.<br>- **Does not work:** setting past period dates through a command cannot produce G, because the failure time is "now". | S3 E and G. F needs no advance |
| Outbox publisher / sweep runner | Billing §6/§7.6; owner choice | S3 E (suspension) |
| O-L3SCOPE | Are classroom and device sessions in scope? | Session seed data |
| O-PCONSENT | Parent consent contract | Consent seed data |
| SRS naming | `SYNTHETIC_TEST` (SRS §9.7) versus `SYNTHETIC_DEV` (code) | Nothing; SRS reconciliation note |
| Local FE sign-in for seeded adults | Synthetic verifier or a local Firebase emulator; no credential in Git either way | All stages |

## 8. Not verified

- Whether direct Story inserts need asset or metadata rows. The implementation plan checks this.
- The Q-L2-5 unit value.
- Whether the Billing period is monthly or yearly. The Billing code does not exist yet.
- The exact wording of D-171 item 9.
- Every FE screen.

## 9. Disposition of the reviews (not re-reviewed)

**Draft 3 review (S3-01 to S3-08):**

| ID | Disposition |
|---|---|
| S3-01 | §4.1 F/G and §4.3 F/G: FAILURE is recorded while ACTIVE; G reaches RESTRICTED only by advancing billing time past `grace_until`; "period end passed" is removed |
| S3-02 | §3: O-SEED-CLOCK is a hard dependency; a per-organization clock is preferred; a fixed S3 order applies if only a global clock exists; S4 runs after S3 |
| S3-03 | §2 rule 3: checks before settings are read, cache clearing, explicit URLs, `PG*` and alternate URL variables refused, host and port compared, resolved env, and the seed never creates, drops or migrates a database |
| S3-04 | §4.1 Parent groups: lowercase states and the required `expires_at` |
| S3-05 | §2 rule 6: the in-process actor is the organization's seeded School Manager; random-ID rows are marked by name; §4.5 lists the keys |
| S3-06 | §2 rule 5: idempotency windows are the subscription period and the calendar month; receipt IDs are deterministic; change group refs are stable |
| S3-07 | §2 rule 4: column rules (UUIDv5 `account_id`, 36-character IDs, receipts counted by principal, snapshot hash, `SYNTHETIC_FIXTURE`, eligibility proofs not seeded) |
| S3-08 | §4.1 Lessons: visibility and `review_state` reworded |

**Draft 2 review (S2-01 to S2-12):** disposed in Draft 3 §9. The round-2 review found S2-01, S2-02, S2-03 (as a table), S2-04 and S2-09 to S2-12 resolved, and S2-05 to S2-08 partly resolved. The remaining parts of S2-05 to S2-08 are handled under S3-01 to S3-07 above.

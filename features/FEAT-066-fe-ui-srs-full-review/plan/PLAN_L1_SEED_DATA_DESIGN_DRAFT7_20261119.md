# FEAT-066 L1 — Seed data design — Draft 7 (system-wide coverage)

- **Status:** DRAFT / NOT APPROVED. Design only. It authorizes no script, database, storage or command. Draft 7 keeps every rule and stage of Draft 6 and adds the rest of the system: §10 maps every SRS target table group to a seed class, and §11 adds stages S5 to S10. Draft 7 is not yet reviewed.
- **Date:** 2026-11-19. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Why Draft 7:** Draft 6 covered the core data only (accounts, organizations, classes, profiles, Parent groups, Lesson Library, StoryRuns, Billing and video quota). By owner direction (2026-11-19) the seed follows the whole SRS data model: lesson occurrences and approved lesson plans (giáo án), Sketch Teaching Decks, classroom sessions, consent and data authorizations, notifications, AI jobs, story and video content, and assets. The SRS has no course entity, so none is seeded.
- **Draft 6 (direct predecessor):** 28,192 bytes, `CABC4BCA10A2442EF948D9778680A9A9FAD4491368395F037155C4C9DEB44E85`. Its rules §2, stages S1 to S4 (§3 to §4) and the SEED-1 implementation (commit `4e2f6d96`, stage S1) stay valid, except the S1 StoryRun note of §11.8.
- **Predecessors, unchanged:**
  - Draft 5: 25,609 bytes, `A549EC0B92072175315473DB8538A6A8E503470C44388F596D9B7176EA785CD3`. Its cold review (Sonnet 5.5, told high, round 4) was READY WITH NOTES, 0 P1 / 0 P2 / 4 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT5_COLD_REVIEW_20261118.md`, 4,649 bytes, `C27A83046F5D3E3A…`.
  - Draft 4: 21,576 bytes, `0C2DB27D13F72CC0AF4BE75CEBFD32C3868762B81B841F3AAD52E89F574EF109`. Its cold review (Sonnet 5.5, told high, round 3) was NOT READY, 0 P1 / 1 P2 / 6 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT4_COLD_REVIEW_20261118.md`, 5,896 bytes, `9B2220B58110E262…`. Two finding classes repeated (guard hardening, column gaps). Under D-171 item 11 the owner decided the next step: "Draft 5 + review" (2026-11-18), which is round 4 of 5.
  - Draft 3: 16,100 bytes, `FDF40929A431CDC01B7376D96BA6FBC5CB2096FD1D87796E3F8E5CC3A5F0CE7E`. Its cold review (Sonnet 5.5, effort set to high by the caller, round 2) was NOT READY, 0 P1 / 2 P2 / 6 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT3_COLD_REVIEW_20261118.md`, 6,316 bytes, `F460971A01C6D8E2…`.
  - Draft 2: 12,975 bytes, `0AF7B365…`. Its round-1 review was NOT READY, 0 P1 / 5 P2 / 7 P3, record `6B99D395…`.
  - Draft 1: `E0EE5BED…`.
  - §9 records the disposition of S5-01 to S5-04, S4-01 to S4-06, S3-01 to S3-08 and S2-01 to S2-12.
- **Inputs:**
  - Data table register `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` (171,609 bytes at base `03342207`): §4 (38 retained tables), §5 (54 new target tables), §9 (legacy read-only), §14.4 and §14.5.
  - SRS §9.9 (aggregates), §11 (owners and constraints), §11.3 (retention), §12.2 (consent by data origin).
  - The Alembic tree at base `03342207` (which target tables exist today; §10).
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

One reproducible synthetic seed for a disposable local database and a disposable local object-storage bucket. It gives every FE role flow, every Bruno request (L5) and manual demos the data they need, across the whole SRS data model (§10). It does not replace the fixtures that PostgreSQL integration tests create for themselves.

A stage whose tables do not exist yet is designed now and runs when its owning module lands (class SEED-WHEN-BUILT in §10). The design does not ask any module to change for the seed's sake, except the local/test hooks named in §7.

## 2. Hard rules

1. **Synthetic only.** No real child, parent or school data. Child profiles use `data_origin = SYNTHETIC_DEV` with no consent and ages from 36 to 120 months.
2. **No secret in Git.** No password, Firebase credential, ID token or API key goes into the script, the fixtures or the Bruno environments. Adults are seeded by issuer and subject reference.
3. **Target database guard (S2-05, S3-03).** The seed reads one variable, `S2L_SEED_DATABASE_URL`. It is distinct from `BE1_TEST_DATABASE_URL` and from `SKETCH2LIFE_DATABASE_URL`.

   **Checks before any settings are read.** These run before the seed imports or calls anything that reads settings. All must pass:
   - (a) The database name contains `seed`, and contains neither `be1_acceptance` nor `m2_s1a`.
   - (b) The URL has an explicit loopback host (`127.0.0.1`, `::1` or `localhost`) and an explicit port. The seed refuses:
     - a missing host;
     - **any query string at all**, such as `host`, `hostaddr`, `port`, `dbname`, `service` or `options` (the StoryRun guard in the repository rejects any query too);
     - any of `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGSERVICE`, `PGSERVICEFILE` or `PGOPTIONS` set in the environment. The last two follow the repository's `composition.py` guard.
   - (c) `S1A_P_ALEMBIC_DATABASE_URL` and `STORYRUN_LITE_DATABASE_URL` are unset, or equal to the guarded URL.

   **Then:**
   - It sets `SKETCH2LIFE_DATABASE_URL` for its own process to exactly the guarded URL.
   - It clears the `lru_cache` of `get_settings()` and `get_core_database_settings()`.
   - It requires the **resolved** `settings.env` to be `local` or `test`. The value can come from the process environment **or from the worktree-root `.env`**, and the resolved check covers both. An unset value resolves to local, which is accepted only together with (a) and (b).
   - Every engine it uses, including Billing's own pool, is created with the explicit URL (`create_core_engine(database_url)`).
   - Before any write, it compares each engine's database name, host and port with the guarded values. It then runs a **live server-side check** on each engine, following `verify_goal_database_owner`: `current_database()` must equal the guarded name, `inet_server_port()` the guarded port, `inet_server_addr()` must be a loopback address, and `current_user` must be the owner of that database. Any difference aborts. These checks make a tunnel to another server unlikely to pass, but they cannot prove the server's identity; the guard's purpose is to stop mistakes, not a deliberate bypass.
   - It never prints the URL.
   - It **never imports** the entry modules that call `create_app()` at import time: `main.py`, `classroom_main.py`, `demo_main.py` and `story_run_lite_app.py`. Those modules would read settings before the guard runs.

   **The seed never creates, drops or migrates a database.** Alembic `upgrade heads` and the drop and recreate of rule 5 are runbook steps that the owner runs with the same URL, with `S1A_P_ALEMBIC_DATABASE_URL` unset.
4. **Seed marker, defined per table (S2-06, S3-07):**
   - **Text-ID tables:** a `seed-` prefix on the stable ID, kept within 36 characters, because several primary keys are `String(36)`. Example: `seed-org-a`.
   - **Tables with a display name:** a `[SEED]` prefix on the name.
   - **UUID columns:** deterministic UUIDv5 values from one fixed seed namespace and the seed key. This includes the unique, non-primary-key `be1_adult_identities.account_id`.
   - **Hash and receipt tables:** counted by tracing their foreign keys to seeded roots. `parent.command_receipts` has no foreign key, so it is counted by the seeded principal.
   - **Rows created by product commands:** these have random IDs and carry only the `[SEED]` name marker. They are counted per seeded organization.
   - **Billing rows:** never written by the seed. They are counted through the seeded organization and scope refs.

   **Column rules from source:**
   - Lesson rows are written exactly as the product commands would leave them (S5-01): creating a PUBLIC grant sets the bound version's `review_state` to `PENDING_REVIEW` (`service.py`, around line 1124); `library_items.visibility` (NOT NULL; `PRIVATE`, `SCHOOL`, `SELECTED_AUDIENCE` or `PUBLIC`) is derived from the lesson's ACTIVE grants by the product rule `_recalculate_visibility` (ORGANIZATION → SCHOOL, PRINCIPAL or PARENT_GROUP → SELECTED_AUDIENCE, PUBLIC → PUBLIC), and the seed computes it with that function rather than typing it; `internal_visibility` (NOT NULL) is `PRIVATE` or `SCHOOL` (`ck_lesson_internal_visibility`); a non-PUBLIC grant needs an `APPROVED` version, a non-null `audience_ref` and a `capability` (`VIEW`, `DOWNLOAD` or `REUSE`).
   - `be1_adult_identities.account_role` is set for every seeded adult: `platform_admin`, `school_manager`, `teacher` or `parent`. `role_revision = 1` (S4-01). The role gates read these columns: `has_active_parent_role` requires `account_role == "parent"`, and `be1_common` filters assignments by role.
   - `parent.profile_revisions.revision_hash` is computed with the domain snapshot function, not typed in.
   - Managed profiles use `age_source = SYNTHETIC_FIXTURE`.
   - The time-limited `be1_synthetic_eligibility_proofs` are **not seeded**: they expire, and the synthetic-pilot flow creates its own.

   The implementation plan includes one count query per table.
5. **Idempotent within one subscription period and one calendar month (`Asia/Ho_Chi_Minh`) (S2-08, S3-06).**
   - A second run inside both windows, and before any billing-time advance, changes nothing and reports zero new rows.
   - S1 writes by direct SQL **only when the row is absent** (insert-if-absent on the stable IDs; never `ON CONFLICT DO UPDATE`), so a replay can never overwrite state that later stages changed, such as suspended classes or `capacity_version_seen`.
   - Billing and product commands use stable idempotency keys (§4.5). Change group refs derive from (organization, principal, key), so they are stable too.
   - Payment-side receipts used by the seed carry deterministic IDs `seed-receipt-<org>-<case>`.
   - `settle_due_transitions` runs at the start of every Billing command. A run after a period or month boundary is therefore a **re-seed**, not a replay.

   **Re-seed procedure (owner, runbook):** drop and recreate the disposable seed database, run `upgrade heads`, then run the stages again. Bruno negative cases that depend on quota or period state are marked time-sensitive in L5.
6. **Write paths (S2-11, S3-05).**
   - **S1 is direct SQL** into BE1, Parent, Lesson Library and Story tables, with the stable IDs above. The existing bootstrap scripts are not used: they need a token or an e-mail, and they run only once.
   - **S2 onward** use only product and Billing commands; §4 lists each one.
   - **Actor for product commands:** the seed calls the BE1 application commands in-process, as the organization's seeded School Manager (issuer and subject from the seed data). It does not go through HTTP and needs no token.
     - If a command exists only as an HTTP route function, the slice that owns it extracts the application command first. The seed waits for that; it never goes through HTTP or a verifier, and no credential goes into Git.
7. **No writes into the `billing` schema.** Billing rows come only from Billing's commands and ports (contract §7) and from its env-guarded price-version step.
8. **Schema from Alembic.** `upgrade heads` creates the schema before seeding; the environment has several module branches. The seed never alters schema.
9. **Object-storage guard (S7 to S10).** Stages that store files read one storage target: a loopback endpoint with an explicit port, a bucket whose name contains `seed`, and throwaway credentials set by the owner's runbook, never read from the local secrets directory and never written to Git. Before the first write the seed lists the bucket: it must be empty on a first run, or hold only keys under the seed's own prefixes on a replay. Any other endpoint, bucket or key aborts. The seed never creates or deletes a bucket.
10. **No provider call.** No stage calls Modal, an LLM, ASR, VLM, video, payment, e-mail or push provider, or any non-loopback host. AI-derived content (extracted text, understanding, story, scenes, deck steps, visual assets, video) enters only through the owning module's completion command, fed by a local/test fake adapter (`infrastructure/ai_jobs/fakes.py` and `infrastructure/vision_analysis/fakes.py` are the existing ones; O-SEED-AI covers the rest) with `model_profile_ref = seed-synthetic`. Provider environment variables must be unset; the seed checks that before it starts.
11. **Synthetic files only.** Every stored file is generated by the seed itself from fixed parameters: plain shapes and colours for drawings (no face, no handwriting, no text), a short generated Vietnamese text for lesson documents, a silent or tone audio clip. No downloaded, photographed or real child file. Each file's SHA-256 is fixed in the data module, so a replay can compare it.
12. **Lifecycle states come from lifecycle commands.** A state that a lifecycle consumer acts on (`DELETE_PENDING`, `DELETED`, revoked grants, ended sessions) is reached by the product command that produces it, never by direct SQL, once that command exists (§11.8).

## 3. Stages and their dependencies

| Stage | Needs (all verified and on the seed's base) | Content |
|---|---|---|
| **S1 — core data, direct SQL** | Current `dev` schema | Identities, all organizations, assignments, classes, class profiles, Parents and Parent profiles, Parent groups, lessons and versions, grants, StoryRuns (§4.1) |
| **S2 — capacity basics** | Billing B-1 and B-2; S1 | Billing's local price-version step; `open_subscriptions_for_existing_organizations()`; one real product class create in org A, which exercises the null-stamp path (§4.2) |
| **S3 — lifecycle states** | Billing B-4 (payment interface) and B-5; S2; **O-SEED-PAY** (local/test receipts); **O-SEED-CLOCK — a hard dependency** (§7); for the suspended class, also the outbox publisher or sweep runner and the BE1 suspension consumer (Billing §7.6; the runner is still open) | Add-on, scheduled downgrade, applied downgrade with suspended classes, GRACE, RESTRICTED, provider-canceled (§4.3) |
| **S4 — video quota** | Billing B-1 (the price version gives the units), B-3; S2 (an organization scope needs a subscription); **after S3** | Grants, usage, an exhausted scope (§4.4) |
| **S5 — platform catalog and policy** | S1 (Platform Admin actor); the `learning_content` and `ai_policy` commands (tables exist) | Parent activity catalog versions; AI policy activation for local/test (§11.2) |
| **S6 — classroom sessions** | S1; BE1 classroom commands callable in-process (tables exist) | Ended and active sessions, groups, learning stages, outcomes, observations, gallery snapshots, child turns, a device grant (§11.3) |
| **S7 — assets, Story content and video** | S1, S5; rule 9 storage target; O-SEED-AI; video part after S4 and the video-generation tables | Uploaded synthetic drawings and audio, run inputs, understanding, story revisions, scenes, review decisions; later video generations (§11.4) |
| **S8 — lesson occurrences, lesson plans and decks** | S1, S6 (class roster), S7 (asset path), S9 (share grants for feedback); the lesson occurrence module (tables not yet built) | Occurrences, source documents, extracted revisions, approved and draft lesson plans (giáo án), plan activities, Sketch Teaching Decks, visual assets, delivery, feedback and replies (§11.5) |
| **S9 — profile depth, sharing and data authorizations** | S1; the Parent and Teacher profile-extension tables (not yet built) | Context entries, support needs, Teacher profile revisions, profile share grants, synthetic data authorizations (§11.6) |
| **S10 — notifications** | The `notifications` module (not yet built); runs after the stages whose events trigger notices | Inbox items read and unread, IN_APP delivery attempts (§11.7) |

**Stage order (S3-02, extended in Draft 7):** S1, then S5, then S2, then S3, then S4. S6 and S9 need only S1 and may run at any point after it. S7 runs after S5; its video part runs after S4. S8 runs after S6, S7 and S9. S10 runs last. Stages whose tables are not built are skipped and reported as `NOT_BUILT`, never as passed.
- **S4 runs last**, because advancing billing time also expires the monthly grants.
- **With per-organization billing time control** (the preferred O-SEED-CLOCK answer), the order inside S3 is free.
- **With only a global test clock**, S3 runs in this fixed order:
  1. Set up E (add-on, creates, downgrade) and G (renewal FAILURE).
  2. Advance billing time once, past E's period end and past G's `grace_until`. Run `settle_due_transitions` for E and G, and let the publisher and the BE1 consumer apply E's suspension.
  3. Only then set up D (a scheduled downgrade, which must not reach its boundary), F (a FAILURE that stays in GRACE) and H (provider cancellation).
  4. The advance also rolls over every other ACTIVE subscription to its next period. A, B and C roll at the advance. D, F and H roll lazily on their first command after it. Their capacity is unchanged (10 + 0, and roll-over carries the previous slots); this is accepted.
  5. **Clock end state:** the global clock stays advanced after S3. S4 and every later use of the seed database run at that advanced time.
  6. **Billing readings this order relies on** (to confirm with the Billing author under O-SEED-CLOCK):
     - (i) Local auto roll-over applies only to ACTIVE subscriptions with no recorded renewal outcome. It never rolls a GRACE subscription; if it did, G could never reach RESTRICTED.
     - (ii) A FAILURE recorded while ACTIVE puts the subscription into GRACE immediately, with `grace_until` = max(failure time, period end) + 7 days.
- **Replayable stages (S4-03, S5-04):** only S1 and S2 are replayable under rule 5, and **only before S3 has run**. S3 and S4 are **one-shot per seed database**, because S3 advances billing time. Repeating them needs the re-seed procedure.
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
| F | GRACE | 2 | S3: renewal FAILURE recorded while ACTIVE. The subscription enters GRACE at once (reading (ii) of §3); `grace_until` = max(failure time, period end) + 7 days. No time advance is needed for F |
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
| Lessons (S3-08) | `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities`, `lesson.library_source_documents`, `lesson.library_document_revisions` | Org A: 3 Teacher-authored lessons:<br>- L1 has 2 versions, and `current_version_id` points to the second. This creates the superseded case for MGR-6.<br>- L2 has `internal_visibility` PRIVATE.<br>- L3 has `internal_visibility` SCHOOL. Its PUBLIC request is grant GR4 (below), bound to L3's current version, whose `review_state` is therefore `PENDING_REVIEW`.<br>The lesson's `internal_visibility`, its derived `visibility`, the version's `review_state` and the grants are separate columns on different tables; §2 rule 4 sets them consistently. |
| Access grants (S5-02) | `lesson.access_grants` | Four rows:<br>- **GR1:** L1 current version (APPROVED), `ORGANIZATION` = org A, `VIEW`, `ACTIVE` → L1's derived `visibility` is SCHOOL.<br>- **GR2:** L1 first version (APPROVED, no longer `current_version_id`), `PARENT_GROUP` = org A group 1, `VIEW`, `PENDING_REVIEW` — the superseded case of MGR-6 ("superseded" is derived, not stored).<br>- **GR3:** L2 version (APPROVED), `PRINCIPAL` = Parent P1, `DOWNLOAD`, `REVOKED`.<br>- **GR4:** L3 current version, `PUBLIC`, `VIEW`, `PENDING_REVIEW`.<br>L2's and L3's derived `visibility` come from the product rule with no ACTIVE grant (value NV until computed) |
| StoryRuns | `story.runs`, `story.run_inputs`, related receipts | P1/K1: one COMPLETED, one FAILED, one DELETE_PENDING and one active run (`INPUT_PROCESSING`). P2/K3: one COMPLETED and one active run (`PREPARATION_REVIEW`). K2 (delete-pending) and P3 (no profile) have no runs. This respects the one-active-run rule (`uq_story_run_active_parent`) |
| Consent records | `be1_consent_records` | None. SRS §12.2: synthetic fixtures need no consent row and no fake consent ID. Synthetic data authorizations come in S9 |
| Synthetic eligibility proofs | `be1_synthetic_eligibility_proofs` | Not seeded: they are time-limited, and the synthetic-pilot flow creates its own |
| Classroom and device sessions | `be1_sessions` and related | Not in S1; seeded by S6 through BE1 commands (§11.3) |

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
| D | 1. `activate_add_on_slots` (+2, receipt `seed-receipt-D-addon`) gives capacity 12.<br>2. Two product creates give 12 active.<br>3. The downgrade use case, through its internal command, targets 10 + 0 and selects the S1 classes `seed-org-d-class-1` and `seed-org-d-class-2`. They are chosen by stable ID; product-created classes are never selected. Its check passes: active − selected = 10 ≤ 10.<br>4. Admission capacity = min(12, 10 + 2) = 12, so the organization is full. |
| E | 1. The same steps as D, with E's keys, selecting `seed-org-e-class-1` and `seed-org-e-class-2`.<br>2. Billing time passes the period boundary.<br>3. `settle_due_transitions` runs, the publisher delivers the suspension event, and BE1 suspends the 2 selected classes.<br>4. Result: 10 active + 2 suspended against capacity 10. |
| F | `record_renewal_outcome(FAILURE)` while ACTIVE (receipt `seed-receipt-F-failure`) gives GRACE at once (reading (ii)); no time advance |
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
- The first run creates the documented rows. For S1 and S2, a second run inside the rule-5 windows creates none. S3 and S4 are one-shot per seed database (§3).
- The counts per table match.
- Each role can open its main FE screen with data.
- The diff contains no secret (security validator plus a manual search).
- **S2–S4 only:** the 409 cases return their codes through the product path.

## 7. Open points

| ID | Question | Blocks |
|---|---|---|
| O-SEED-PAY | Can the payment teammate supply a local/test-only way to create provider event receipts, with deterministic IDs? | S3 D, E, F, G, H; S4 top-up |
| O-SEED-CLOCK | **Hard dependency.** How is billing time advanced locally?<br>- **Preferred:** a test-only, per-organization clock offset in Billing (local/test only).<br>- **Otherwise:** a global test clock, used with the fixed S3 order of §3.<br>- **Does not work:** setting past period dates through a command cannot produce G, because the failure time is "now".<br>- Also confirm readings (i) and (ii) of §3 with the Billing author. | S3 E and G. F needs no advance |
| Outbox publisher / sweep runner | Billing §6/§7.6; owner choice | S3 E (suspension) |
| O-PCONSENT | Parent consent contract | S9 data authorizations beyond the synthetic flag |
| SRS naming | `SYNTHETIC_TEST` (SRS §9.7) versus `SYNTHETIC_DEV` (code) | Nothing; SRS reconciliation note |
| Local FE sign-in for seeded adults | Synthetic verifier or a local Firebase emulator; no credential in Git either way | All stages |
| O-SEED-STORAGE | Which local object store the runbook starts for the seed (S3Mock is already used by FR-C-08; MinIO images are not pullable today) and its bucket and key-prefix layout | S7, S8 |
| O-SEED-AI | Do local/test fake adapters exist, or will the owning modules provide them, for every AI stage the seed needs: lesson extraction (or the local parser), story writing, scene split, deck steps, visual assets, video scenes? No adapter means the stage stays `NOT_BUILT` | S7, S8 |
| O-SEED-VIDEO-ASSET | How the seed produces a valid short synthetic video file without a provider (a generated clip, or a tiny fixture file committed to the repository after a security check) | S7 video, S8 sample video |
| O-SEED-SESSION-TIME | Room codes and device grants expire. Confirm the TTLs and whether a test clock exists for BE1 sessions | S6 active session |
| O-L3SCOPE (unchanged) | Still decides which classroom and device API operations are audited and exposed; it no longer decides whether session data is seeded (§11.3) | S6 routes only |

## 8. Not verified

- Whether direct Story inserts need asset or metadata rows. The implementation plan checks this.
- The Q-L2-5 unit value.
- Whether the Billing period is monthly or yearly. The Billing code does not exist yet.
- The exact wording of D-171 item 9.
- Whether the BE1 class-create and downgrade application commands are callable in-process today.
- Every FE screen.
- The exact columns of the S6 session tables and whether every BE1 classroom command is callable in-process without HTTP.
- Whether the existing fake adapters cover the Story stages the seed needs.
- The column lists of every SEED-WHEN-BUILT table: they come from the register, not from code, and the owning module may change them. Each later stage task re-derives them from source.

## 9. Disposition of the reviews (not re-reviewed)

**Draft 6 to Draft 7:** a scope extension by owner direction, not a review response. §10 and §11 are new; §1, §2 rules 9 to 12, §3, §4.1 (two rows), §7 and §8 are extended. Nothing else of Draft 6 changed.

**Draft 5 review (S5-01 to S5-04), P3 only:**

| ID | Disposition |
|---|---|
| S5-01 | §2 rule 4 lesson column rule (PUBLIC grant → version `PENDING_REVIEW`; derived `visibility` by `_recalculate_visibility`; `internal_visibility` values; non-PUBLIC grant requirements); §8 value-names item removed |
| S5-02 | §4.1 grant inventory GR1–GR4 with lesson, version, audience, capability and state |
| S5-03 | §2 rule 3 live check adds `inet_server_addr()` loopback and `current_user` = database owner; the claim softened |
| S5-04 | §2 rule 5 S1 insert-if-absent; §3 S1/S2 replay only before S3 |

**Draft 4 review (S4-01 to S4-06):**

| ID | Disposition |
|---|---|
| S4-01 | §2 rule 4: `account_role` per seeded adult and `role_revision = 1` |
| S4-02 | §3 Billing readings (i) and (ii), to confirm under O-SEED-CLOCK; F reworded in §4.1 and §4.3 |
| S4-03 | §3: roll-over of D, F and H named; the clock end state stated; only S1 and S2 replayable; §6 acceptance aligned |
| S4-04 | §2 rule 3: any query string refused; `PGSERVICEFILE` and `PGOPTIONS` refused; live server-side check; entry modules never imported; `.env` named as a source |
| S4-05 | §4.1 L2/L3: `internal_visibility` named; the PUBLIC request is an `access_grants` row |
| S4-06 | §2 rule 6: verifier fallback removed (extract the command only); §4.3 D/E select stable-ID S1 classes |

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

## 10. System-wide coverage (Draft 7)

Every target table group of the data table register gets exactly one class:

- **SEED-NOW:** the table exists at the seed base; a stage writes it now.
- **SEED-WHEN-BUILT:** the table is a target that the schema does not have yet; the stage is designed here and
  runs when the owning module lands, through that module's commands.
- **SIDE-EFFECT:** written only as a consequence of seeded commands; counted, never written by the seed.
- **NOT SEEDED:** the reason is stated.

| Owner / group (register) | Tables | Class | Stage |
|---|---|---|---|
| be1 organizations and roster | `be1_organizations`, `be1_adult_identities`, `be1_organization_assignments`, `be1_classrooms`, `be1_managed_profiles`, `be1_enrollments` | SEED-NOW | S1 |
| be1 audience groups | `be1_parent_groups`, `be1_parent_group_members` | SEED-NOW | S1 |
| be1 consent | `be1_consent_records` | NOT SEEDED: synthetic data needs no consent row (SRS §12.2) | — |
| be1 lifecycle | `be1_data_lifecycle_requests` | SIDE-EFFECT of the S7 delete flow (§11.8) | S7 |
| be1 eligibility | `be1_synthetic_eligibility_proofs` | NOT SEEDED: time-limited; the pilot flow creates its own | — |
| be1 classroom sessions | `be1_sessions`, `be1_session_memberships`, `be1_session_groups`, `be1_group_drafts`, `be1_session_room_codes`, `be1_session_learning_stages`, `be1_session_learning_stage_events`, `be1_session_outcomes`, `be1_observations`, `be1_gallery_snapshots`, `be1_child_turns`, `be1_device_grants` | SEED-NOW (commands) | S6 |
| be1 session bookkeeping | `be1_session_command_receipts`, `be1_room_code_rate_limits` | SIDE-EFFECT / NOT SEEDED (rate-limit counters) | S6 |
| be1 Teacher profile extension | `be1.profile_revisions`, `be1.profile_context_entries`, `be1.profile_support_needs` | SEED-WHEN-BUILT | S9 |
| parent profiles | `parent.child_profiles`, `parent.profile_revisions`, `parent.command_receipts` | SEED-NOW | S1 |
| parent profile extension and sharing | `parent.profile_context_entries`, `parent.profile_support_needs`, `parent.profile_share_grants`, `parent.data_authorizations` | SEED-WHEN-BUILT | S9 |
| core transaction infrastructure | `core_audit_entries`, `core_outbox_events`, `core_outbox_consumer_receipts`, `core_aggregate_revisions`, `core_idempotency_receipts` | SIDE-EFFECT | all |
| core assets and uploads | `core_asset_metadata`, `core_asset_lineage`, `core_upload_sessions`, `core_upload_parts`, `core_upload_command_receipts` | SEED-NOW through the upload commands | S7 |
| core legacy canvas | `core_canvas_checkpoints`, `core_canvas_operations` | NOT SEEDED: legacy read-only (register §9) | — |
| learning_content catalog | `record`, `version`, `review`, `receipt`, `event`, `outbox` | SEED-NOW (publication commands) | S5 |
| ai_policy | governance, activation and resource tables | SEED-NOW (lifecycle commands), activation only; the provider-copy registry and `resource_receipt` NOT SEEDED (deferred to the real-data gate) | S5 |
| ai_jobs | `job`, `attempt`, `command_receipt`, `semantic_request`, `completion_receipt`, `cancellation_notice`, `outbox`, `job_events` (when built) | SIDE-EFFECT of S7 and S8 dispatch and fake completion | S7, S8 |
| lesson library | `library_items`, `library_versions`, `version_activities`, `library_source_documents`, `library_document_revisions`, `access_grants`, `command_receipts` | SEED-NOW | S1 |
| lesson library visuals | `lesson.version_visual_assets` | SEED-WHEN-BUILT | S8 |
| lesson occurrence, plan and deck | `lesson.occurrences`, `lesson.source_documents`, `lesson.document_revisions`, `lesson.plan_revisions`, `lesson.plan_activities`, `lesson.sketch_deck_revisions`, `lesson.sketch_deck_steps` | SEED-WHEN-BUILT | S8 |
| lesson delivery | `lesson.delivery_recipients`, `lesson.delivery_feedback`, `lesson.feedback_replies` | SEED-WHEN-BUILT | S8 |
| story run and content | `story.runs`, `story.run_inputs`, `story.understanding_revisions`, `story.story_revisions`, `story.story_scenes`, `story.review_decisions`, `story.story_revision_reviews`, StoryRun upload tables | runs and inputs SEED-NOW (S1); content SEED-NOW through commands (S7) | S1, S7 |
| story transcript and video | `story.transcript_revisions`, `story.video_generations`, `story.video_generation_scenes` | SEED-WHEN-BUILT | S7 |
| billing | the nine `billing.*` tables | SEED-WHEN-BUILT through Billing commands (S2 to S4); invoices, payment attempts, provider receipts and subscription events are SIDE-EFFECT | S2–S4 |
| notifications | `notifications.inbox_items`, `notifications.delivery_attempts` | SEED-WHEN-BUILT, produced by triggers | S10 |
| notifications endpoints | `notifications.push_endpoints` | NOT SEEDED: a push endpoint is a real device secret | — |
| other legacy schemas | collaboration, canvas, knowledge video, video review, video failure, activity execution, preset automation, `pilot_vision` | NOT SEEDED: legacy or pilot, read-only | — |

The implementation of each stage adds one count query per table of its rows, and the SEED-WHEN-BUILT rows are
re-checked against the Alembic tree when the stage task starts.

## 11. Stages S5 to S10 (Draft 7)

All stages keep §2 rules 1 to 12. Stable keys follow §4.5: `seed:s<n>:<scope>:<case>`; text IDs keep the
`seed-` prefix and the 36-character limit.

### 11.1 Actors

The in-process actor is always the seeded adult who would act in the product: the Platform Admin for catalog,
policy and public review; the School Manager for roster and Billing; the assigned Teacher for sessions,
occurrences, plans and decks; the Parent owner for Parent profiles, runs, sharing and feedback. No stage acts
as a role that the product would refuse.

### 11.2 S5 — platform catalog and policy (SEED-NOW)

| Item | Created through | Result |
|---|---|---|
| Parent activity catalog | `learning_content` publication commands, as the Platform Admin (pattern: FEAT-048 `bootstrap_local_pg.py`) | 6 published activity versions with `[SEED]` titles across drawing topics; 1 draft; 1 in review |
| AI policy | `ai_policy` lifecycle commands | The local/test policy versions that the Story and Lesson flows check are activated for local/test only; no provider-copy row |

S5 is replayable: every command uses a stable key.

### 11.3 S6 — classroom sessions (SEED-NOW)

Org A only, through the BE1 classroom commands in-process as the class's assigned Teacher.

| Class | Session | Content |
|---|---|---|
| `seed-org-a-class-1` | One ENDED session | 2 groups with members from the class roster, the learning stages walked to the end with their events, one outcome per group, 2 observations, 1 gallery snapshot, a few child turns |
| `seed-org-a-class-2` | One ACTIVE session | A live room code and one active device grant (time-sensitive: O-SEED-SESSION-TIME), groups formed, the first learning stage open |
| `seed-org-a-class-4` (no Teacher) | None | The no-Teacher case stays empty |

Gallery snapshots and child turns that carry a drawing reference wait for S7's asset path; until then they are
seeded without a drawing, if the command allows it, or skipped and reported. The ended session is replayable;
the active one is re-created by the re-seed procedure.

### 11.4 S7 — assets, Story content and video

1. **Assets (SEED-NOW):** synthetic drawings (rule 11) and one short audio clip uploaded through the Core upload
   commands (`core_upload_sessions`, parts, finalize) into the rule-9 bucket, as the Parent or Teacher who owns
   them. Lineage rows come from the commands.
2. **Story content for completed runs (SEED-NOW):** for the S1 COMPLETED runs of P1/K1 and P2/K3: a run input
   with the drawing asset and a typed idea, an understanding revision, a story revision with 3 scenes and the
   adult review decisions, all through the Story commands, with AI outputs from the fake adapters through the
   completion commands (rule 10). The FAILED run gets a failed job with a typed safe error code.
3. **Delete flow (SEED-NOW once FR-C-08 is merged):** see §11.8.
4. **Transcript and video (SEED-WHEN-BUILT):** after `story.transcript_revisions`, `story.video_generations` and
   `story.video_generation_scenes` exist and after S4: one INITIAL generation READY (run in `VIDEO_READY`), one
   QUALITY_REGEN, and one run at the request cap of three, each admission consuming one quota unit from S4's
   scopes. The video file is the O-SEED-VIDEO-ASSET output.

### 11.5 S8 — lesson occurrences, lesson plans (giáo án) and decks (SEED-WHEN-BUILT)

Org A, Teacher T1 (assigned to class 1), through the Lesson commands:

| Occurrence | Content |
|---|---|
| O1 — complete | Source document (a generated DOCX or PDF, rule 11) through the upload path; an extracted document revision (local parser or fake adapter) reviewed by T1; a lesson plan revision APPROVED with 2 plan activities and a confirmed safety checklist; a Sketch Teaching Deck revision READY covering both activities with 4 to 8 steps per instruction group; delivery recipients from the class 1 roster snapshot; one Parent feedback from P1 (needs S9's share grant) and one Teacher reply |
| O2 — plan in review | Source document and extraction; a plan revision not yet approved; no deck |
| O3 — stale deck | Approved plan, a READY deck, then a new approved plan revision: the deck becomes STALE |
| O4 — from the library | Created from Lesson Library L1's current version (S1), keeping the version reference and hash |

Lesson Library L1 also gets 2 `version_visual_assets` (TOPIC_REFERENCE, ACTIVITY_ILLUSTRATION). The Teacher
StoryRun on O1 with the sample-video claim waits for §11.4 item 4.

### 11.6 S9 — profile depth, sharing and data authorizations (SEED-WHEN-BUILT)

| Item | Content |
|---|---|
| Parent context | K1: one OUTSIDE_EXPERIENCE and one ACHIEVEMENT entry with short synthetic text |
| Parent support needs | K3: one entry with a synthetic encrypted note |
| Teacher profile extension | Org A class 1 profiles: a first revision each; one context entry; no support note |
| Profile share grants | K1 → org A class 1: ACTIVE; K3 → org A class 2: INVITED; K1 → org B: REVOKED |
| Data authorizations | Only rows with `synthetic_demo_flag = true`, one per seeded Parent profile, for the purposes the Story flow checks. Never a row that looks like a real consent (SRS §12.2); anything beyond that waits for O-PCONSENT |

### 11.7 S10 — notifications (SEED-WHEN-BUILT)

Inbox items come only from the triggers of earlier stages (for example GRACE for org F, quota exhausted for P2,
video ready, a feedback reply), with the IN_APP channel. The seed marks some items read through the product
command, so both read and unread items exist. Delivery attempts are SIDE-EFFECT. No e-mail or push delivery and
no push endpoint (§10).

### 11.8 StoryRun lifecycle states after FR-C-08

FR-C-08 adds the cancel command, `DELETE /v1/story-runs/{run_id}`, a lifecycle consumer and a reconciliation
command that emits the missing event for any Parent `DELETE_PENDING` run. A `DELETE_PENDING` row written by
direct SQL (Draft 6 §4.1, SEED-1) would therefore be purged by the next reconciliation. Once FR-C-08 is merged:

- the `DELETE_PENDING` run of P1/K1 is produced by the cancel command, and the seed does not run the consumer,
  so the run stays `DELETE_PENDING`;
- one more P1/K1 run reaches `DELETED` through the DELETE route and one consumer pass, which also produces the
  `be1_data_lifecycle_requests` row and the audit rows;
- the SEED-1 direct-SQL `DELETE_PENDING` row is removed from S1 in a later SEED task (not authorized here).

Until then, the SEED-1 behaviour stays, and the runbook warns not to run the FR-C-08 reconciliation command on
a seed database.

### 11.9 Acceptance additions (S5 to S10)

- The storage guard refuses a non-loopback endpoint, a bucket without `seed`, a non-empty foreign bucket and a
  key outside the seed prefixes.
- With any provider variable set, the seed refuses to start; no network call leaves loopback.
- Every stored file's hash equals the data module's value.
- A `NOT_BUILT` stage is reported as `NOT_BUILT`, never as passed.
- Each role can open its main FE screens with data. Platform Admin: catalog, public review queue, price
  versions. School Manager: roster, classes, capacity, Billing, Parent groups, library approvals. Teacher:
  classes, sessions, occurrences, lesson plans, decks, library, Teacher StoryRuns. Parent: profiles, StoryRuns,
  lesson deliveries and feedback, notifications, video quota.

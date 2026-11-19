# FEAT-066 L1 — Seed data design — Draft 8 (system-wide coverage)

- **Status:** DRAFT / NOT APPROVED. Design only. It authorizes no script, database, storage or command. Draft 8 keeps every rule and stage of Draft 6, adds the rest of the SRS data model (§10 coverage matrix, §11 stages S5 to S10) and applies the cold review of Draft 7 (round 1 of the system-wide extension: NOT READY, 1 P1 / 11 P2 / 8 P3). Draft 8 is not yet reviewed.
- **Date:** 2026-11-19. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Why the extension:** Draft 6 covered the core data only. By owner direction (2026-11-19) the seed follows the whole SRS data model: lesson occurrences and approved lesson plans (giáo án), Sketch Teaching Decks, data authorizations, notifications, AI jobs, story and video content, and assets. The SRS has no course entity, so none is seeded. The SRS keeps classroom collaboration sessions out of scope (§2.2) and the register classes their tables legacy/read-only, so they are not seeded either (§10, §11.3).
- **Draft 7 (superseded):** 47,526 bytes, `B43A1B792DF163F3D2259D3E6A92DACD40FBDDF71229122FB15080AA5220A62C`. Its cold review (Sonnet 5.5, high, R1): `tmp/seed-d7-review/SEED_DESIGN_DRAFT7_COLD_REVIEW_R1_20261119.md` (local, ignored), 25,983 bytes, `D39AB56F5B9A24A9…`. §12 records the disposition of its 20 findings.
- **Draft 6 (base text):** 28,192 bytes, `CABC4BCA10A2442EF948D9778680A9A9FAD4491368395F037155C4C9DEB44E85`. Its rules §2, stages S1 to S3 and the SEED-1 implementation (commit `4e2f6d96`, stage S1) stay valid, with the changes to S4 (§4.4) and to the S1 lifecycle rows that §2 rule 12 and §11.8 state.
- **Predecessors, unchanged:**
  - Draft 5: 25,609 bytes, `A549EC0B92072175315473DB8538A6A8E503470C44388F596D9B7176EA785CD3`. Its cold review (Sonnet 5.5, told high, round 4) was READY WITH NOTES, 0 P1 / 0 P2 / 4 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT5_COLD_REVIEW_20261118.md`, 4,649 bytes, `C27A83046F5D3E3A…`.
  - Draft 4: 21,576 bytes, `0C2DB27D13F72CC0AF4BE75CEBFD32C3868762B81B841F3AAD52E89F574EF109`. Its cold review (Sonnet 5.5, told high, round 3) was NOT READY, 0 P1 / 1 P2 / 6 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT4_COLD_REVIEW_20261118.md`, 5,896 bytes, `9B2220B58110E262…`. Two finding classes repeated (guard hardening, column gaps). Under D-171 item 11 the owner decided the next step: "Draft 5 + review" (2026-11-18), which is round 4 of 5.
  - Draft 3: 16,100 bytes, `FDF40929A431CDC01B7376D96BA6FBC5CB2096FD1D87796E3F8E5CC3A5F0CE7E`. Its cold review (Sonnet 5.5, effort set to high by the caller, round 2) was NOT READY, 0 P1 / 2 P2 / 6 P3: `evidence/notes/L1_SEED_DATA_DESIGN_DRAFT3_COLD_REVIEW_20261118.md`, 6,316 bytes, `F460971A01C6D8E2…`.
  - Draft 2: 12,975 bytes, `0AF7B365…`. Its round-1 review was NOT READY, 0 P1 / 5 P2 / 7 P3, record `6B99D395…`.
  - Draft 1: `E0EE5BED…`.
  - §9 records the disposition of S5-01 to S5-04, S4-01 to S4-06, S3-01 to S3-08 and S2-01 to S2-12.
- **Inputs:**
  - Data table register `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` (171,609 bytes at base `03342207`): §3 (source dispositions, including the legacy/read-only rows), §4 (38 retained tables), §5 (54 new target tables), §9 (legacy read-only), §14.2 to §14.5.
  - SRS §2.1 (interim video quotas), §2.2 (out of scope), §9.9 (aggregates), §11 and §11.1 (owners and constraints), §11.3 (retention), §12.2 (consent by data origin), BR-33, BR-39, FR-B-14 (notifications), FR-T-10 and FR-T-20 (Teacher run and plan edits).
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

One reproducible synthetic seed for a disposable local database and a disposable local object-storage bucket. It gives every FE role flow, every Bruno request (L5) and manual demos the data they need, across the SRS target data model (§10). It does not replace the fixtures that PostgreSQL integration tests create for themselves.

A stage whose tables or commands do not exist yet is designed now and runs when its owning module lands (class SEED-WHEN-BUILT in §10). The design asks no module to change for the seed's sake, except the local/test hooks named in §7.

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
9. **Object-storage target guard (S7, S8).** This mirrors rule 3.
   - **Checks before any settings are read.** The seed reads three variables of its own: `S2L_SEED_S3_ENDPOINT`, `S2L_SEED_S3_BUCKET` and the throwaway key pair `S2L_SEED_S3_ACCESS_KEY` / `S2L_SEED_S3_SECRET_KEY`, which the owner's runbook sets for the process; they are never read from the local secrets directory or the worktree `.env`, and never written to Git or printed. The endpoint must be `http://` with an explicit loopback host (`127.0.0.1`, `::1`, `localhost`) and an explicit port; the bucket name must contain `seed`. The seed refuses `AWS_ENDPOINT_URL`, `AWS_ENDPOINT_URL_S3`, `AWS_PROFILE`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_CONFIG_FILE` and `AWS_SHARED_CREDENTIALS_FILE` when set, and any `S3_*` application setting resolved from the process or `.env` that differs from the guarded values.
   - **Then:** every storage client the seed uses, including the one a lifecycle consumer would use, is built with the explicit endpoint and keys, never with boto's default credential chain. Before the first write the seed lists the bucket: empty on a first run, or holding only keys under the seed's own prefixes on a replay. Any other endpoint, bucket or key aborts. The seed never creates or deletes a bucket.
10. **No provider call.** No stage calls Modal, an LLM, ASR, VLM, video, payment, e-mail or push provider, or any non-loopback host.
   - Before it starts, the seed requires the resolved settings to say `ai_provider = disabled` and `auth_provider = development`, and the provider fields of `infrastructure/config/settings.py` (`firebase_project_id`, `firebase_credentials_file`, `firebase_admin_json_base64`, `lightning_ai_base_url`, `lightning_ai_token_file`, `runpod_endpoint_id`, `runpod_api_key_file`) to be empty; it also refuses `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` when set. The implementation re-derives this list from source.
   - AI-derived content (understanding, story text, scenes, deck steps, visual assets, video) enters only through the owning module's completion command, fed by a local/test adapter that returns fixed outputs. Such adapters **do not exist today** for any Story, deck, visual or video stage (O-SEED-AI). `infrastructure/ai_jobs/fakes.py` (in-memory store, scripted provider and worker for tests) and `infrastructure/vision_analysis/fakes.py` (pilot observation fake) are test doubles that may be reused as a pattern only; a stage that needs `ai_jobs` rows uses the SQL repository with a scripted provider.
11. **Synthetic files only, generated reproducibly.** Every stored file is generated by the seed from fixed parameters: plain shapes and colours for drawings (no face, handwriting or text), short generated Vietnamese text for lesson documents, a silent or tone audio clip, fixed SVG text for line sketches. No downloaded, photographed or real child file. Generation is normalized: no timestamps, random IDs or library metadata in the bytes (fixed DOCX/PPTX core properties, PDF without creation dates, PNG without text chunks), so each file's SHA-256 can be fixed in the data module. The generator libraries are named in the stage's Task Approval; a new dependency needs that approval.
12. **Lifecycle-consumer states come from commands (scope).** A state that a lifecycle consumer acts on, today the StoryRun `DELETE_PENDING` and `DELETED` of FR-C-08, is reached only by the product command that produces it once that command is merged (§11.8). Other states that S1 writes by direct SQL stay accepted exceptions because no consumer acts on them at the seed base: the `REVOKED` grant GR3, the `revoked` Parent-group members and the delete-pending Parent profile K2. Each exception is re-checked when a consumer for its state lands.

## 3. Stages and their dependencies

| Stage | Needs (each verified on the seed's base before the stage runs) | Content |
|---|---|---|
| **S1 — core data, direct SQL** | Current `dev` schema | Identities, all organizations, assignments, classes, class profiles, Parents and Parent profiles, Parent groups, lessons and versions, grants, StoryRuns (§4.1) |
| **S2 — capacity basics** | Billing B-1 and B-2; S1 | Billing's local price-version step; `open_subscriptions_for_existing_organizations()`; one real product class create in org A, which exercises the null-stamp path (§4.2) |
| **S3 — lifecycle states** | Billing B-4 (payment interface) and B-5; S2; **O-SEED-PAY** (local/test receipts); **O-SEED-CLOCK — a hard dependency** (§7); for the suspended class, also the outbox publisher or sweep runner and the BE1 suspension consumer (Billing §7.6; the runner is still open) | Add-on, scheduled downgrade, applied downgrade with suspended classes, GRACE, RESTRICTED, provider-canceled (§4.3) |
| **S4 — video quota top-up** | Billing B-1, B-3 and B-4; S2; O-SEED-PAY; **after S3** | One top-up grant only. Monthly grants, usage and the exhausted scope come from S7 (§4.4, §11.4) |
| **S5 — platform catalog, policy and compute budget** | S1 (Platform Admin actor); the `learning_content` and `ai_policy` commands (tables exist) | Parent activity catalog versions; local/test AI policy activation; a local/test compute budget (§11.2) |
| **S7 — assets, Story content and video** | S1, S5; rule 9 storage target; O-SEED-AI, O-SEED-SCAN; the video part also needs S2 to S4, the video-generation tables and O-SEED-VIDEO-ASSET | Uploaded synthetic drawings and audio, command-made Parent runs with content, video generations and quota usage (§11.4) |
| **S8 — lesson occurrences, lesson plans and decks** | S1, S5, S7 (asset path); the lesson occurrence module (tables not yet built) | Occurrences, source documents, extracted revisions, approved and edited lesson plans (giáo án), plan activities, Sketch Teaching Decks, library visual assets, delivery (§11.5) |
| **S9 — profile depth and sharing** | S1; the Parent and Teacher profile-extension tables (not yet built) | Context entries, support needs, Teacher profile revisions, a named-Teacher share grant (§11.6) |
| **S10 — notifications** | The `notifications` module (not yet built); a re-seed after it lands | SRS-defined notices, read and unread, IN_APP only (§11.7) |

**Stage order (S3-02, extended in Draft 8):** S1, then S2, then S3, then S4. S5 needs only S1 and runs before S7. S7's asset and content part runs after S5; its video part runs after S4. S8 runs after S7, S9 after S1, and S10 last. There is no S6 (§11.3). A stage whose tables, commands or adapters are missing is skipped and reported as `NOT_BUILT`, never as passed.
- **S4 and the S7 video part run after S3**, because advancing billing time also expires the monthly grants.
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
- **Draft 8 stages:** S5 is replayable at any time (stable keys, no billing time). S7 to S10 are one-shot per seed database: they consume quota, run AI completions and advance run states. Repeating them needs the re-seed procedure.
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
| Consent records | `be1_consent_records` | None. SRS §12.2: synthetic fixtures need no consent row and no fake consent ID |
| Synthetic eligibility proofs | `be1_synthetic_eligibility_proofs` | Not seeded: they are time-limited, and the synthetic-pilot flow creates its own |
| Classroom and device sessions | `be1_sessions` and related | Not seeded. SRS §2.2 keeps classroom collaboration sessions out of scope; register §3 classes the 14 session tables legacy/read-only (§10, §11.3) |

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
| Grants, usage, exhausted | Moved to S7 (Draft 8) | SRS §11.1 items 14 and 15: every usage row follows a compute reservation and belongs to one accepted full-video request, so the seed never calls `admit_video_request` on its own. Monthly grants appear lazily at S7's first admission per scope |
| Top-up | `issue_top_up_grant`, receipt `seed-receipt-P5-topup` | One PURCHASE grant for P5's scope (§11.4), only with O-SEED-PAY |

### 4.5 Idempotency keys and receipt IDs used by the seed (S3-05, S3-06)

| Stage | Key or receipt ID | Command |
|---|---|---|
| S2 | `seed:s2:orgA:create-1` | Class create, org A |
| S3 | `seed-receipt-D-addon`, `seed-receipt-E-addon` | `activate_add_on_slots` for D and E |
| S3 | `seed:s3:orgD:create-1`, `seed:s3:orgD:create-2`, `seed:s3:orgE:create-1`, `seed:s3:orgE:create-2` | Class creates after the add-on |
| S3 | `seed:s3:orgD:downgrade-1`, `seed:s3:orgE:downgrade-1` | Downgrade use case. The change group ref derives from organization, School Manager principal and key |
| S3 | `seed-receipt-F-failure`, `seed-receipt-G-failure`, `seed-receipt-H-cancel` | `record_renewal_outcome` |
| S4 | `seed-receipt-P5-topup` | `issue_top_up_grant` |
| S5, S7 to S10 | `seed:s<n>:<scope>:<case>` | The stage's product commands (§11) |

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
- The first run creates the documented rows. For S1 and S2, a second run inside the rule-5 windows creates none; S5 likewise at any time. S3, S4 and S7 to S10 are one-shot per seed database (§3).
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
| O-L3SCOPE | Whether the 44 unaudited classroom and device operations are in scope for the API work. The seed does not depend on it: SRS §2.2 and register §3 keep session data legacy/read-only, so none is seeded either way | Nothing in the seed |
| O-PCONSENT | Parent consent contract | Any data-authorization row beyond what the owning module requires for synthetic origin (§11.6) |
| SRS naming | `SYNTHETIC_TEST` (SRS §9.7) versus `SYNTHETIC_DEV` (code) | Nothing; SRS reconciliation note |
| Local FE sign-in for seeded adults | Synthetic verifier or a local Firebase emulator; no credential in Git either way | All stages |
| O-SEED-STORAGE | Which local object store the runbook starts (S3Mock is used by FR-C-08; MinIO images are not pullable today), and the key-prefix layout per owner | S7, S8 |
| O-SEED-AI | Local/test adapters that return fixed outputs for Story understanding, story writing, scene split, deck steps, library visuals and video scenes. None exists today (§2 rule 10) | S7, S8 |
| O-SEED-SCAN | A local/test scanner and media validator for upload finalize: `core_asset_lineage` needs `scanner_name`, `scanner_version` and `scanner_sha256`, and ClamAV is not available locally. The seed never writes a CLEAN verdict itself | S7, S8 |
| O-SEED-PARSE | The local DOCX/PDF/PPTX parser for lesson extraction (whether `lesson_parser.py` covers it without a provider) | S8 |
| O-SEED-VIDEO-ASSET | How the seed produces a valid short synthetic video file without a provider (a generated clip, or a tiny fixture committed after a security check) | S7 video |
| O-SEED-IDLINK | The link between a Parent profile, a managed profile and a delivery recipient (register §14.3, §14.3.1 group 02) | S8 Parent feedback and replies |
| O-SEED-KEY | The source of the throwaway encryption key for synthetic support-need notes (runbook-supplied, never in Git) | S9 support needs |
| O-SEED-NOTIFY | The local notification channel setting (IN_APP only, e-mail and push disabled) and the recipient rule per notice | S10 |
| Q-01 (SRS) | Teacher run child selection (system-random over an eligible set, Teacher confirmation) and eligibility without a seeded proof row | Teacher StoryRuns, the occurrence sample-video claim |
| FR-C-08 merge | §11.8 changes apply only after FR-C-08 is merged into the seed's base | S1 lifecycle rows, S7 delete case |

## 8. Not verified

- Whether direct Story inserts need asset or metadata rows. The implementation plan checks this.
- The Q-L2-5 unit value. The SRS gives interim values (§2.1: Parent 2 units per month, School 30); §11.4 uses them.
- Whether the Billing period is monthly or yearly. The Billing code does not exist yet.
- The exact wording of D-171 item 9.
- Whether the BE1 class-create and downgrade application commands are callable in-process today.
- Whether the `learning_content` and `ai_policy` application commands run in-process without HTTP and accept the S5 data.
- Every FE screen.
- The column lists of every SEED-WHEN-BUILT table: they come from the register, not from code, and the owning module may change them. Each later stage task re-derives them from source.
- Whether any runtime wires the FR-C-08 lifecycle consumer or an outbox sweep that could run on a seed database.

## 9. Disposition of the reviews (not re-reviewed)

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

## 10. System-wide coverage

Every table group of the data table register gets exactly one class:

- **SEED-NOW:** the table exists at the seed base; a stage writes it now (subject to its commands and hooks).
- **SEED-WHEN-BUILT:** the target table is not in the schema yet; the stage is designed here and runs when
  the owning module lands, through that module's commands.
- **SIDE-EFFECT:** written only as a consequence of seeded commands; counted, never written by the seed.
- **NOT SEEDED:** the reason is stated.

| Owner / group (register) | Tables | Class | Stage |
|---|---|---|---|
| be1 organizations and roster | `be1_organizations`, `be1_adult_identities`, `be1_organization_assignments`, `be1_classrooms`, `be1_managed_profiles`, `be1_enrollments` | SEED-NOW | S1 |
| be1 audience groups | `be1_parent_groups`, `be1_parent_group_members` | SEED-NOW | S1 |
| be1 consent | `be1_consent_records` | NOT SEEDED: synthetic data needs no consent row (SRS §12.2) | — |
| be1 lifecycle | `be1_data_lifecycle_requests` | SIDE-EFFECT of the S7 delete case (§11.8) | S7 |
| be1 eligibility | `be1_synthetic_eligibility_proofs` | NOT SEEDED: time-limited; the pilot flow creates its own | — |
| be1 classroom sessions (register §3 rows 17 to 30) | `be1_sessions`, `be1_session_memberships`, `be1_session_groups`, `be1_group_drafts`, `be1_session_room_codes`, `be1_room_code_rate_limits`, `be1_session_learning_stages`, `be1_session_learning_stage_events`, `be1_session_outcomes`, `be1_session_command_receipts`, `be1_observations`, `be1_gallery_snapshots`, `be1_child_turns`, `be1_device_grants` | NOT SEEDED: legacy/read-only (SRS §2.2, register §3 and §9) | — |
| be1 Teacher profile extension | `be1.profile_revisions`, `be1.profile_context_entries`, `be1.profile_support_needs` | SEED-WHEN-BUILT | S9 |
| parent profiles | `parent.child_profiles`, `parent.profile_revisions`, `parent.command_receipts` | SEED-NOW | S1 |
| parent profile extension and sharing | `parent.profile_context_entries`, `parent.profile_support_needs`, `parent.profile_share_grants` | SEED-WHEN-BUILT | S9 |
| parent data authorizations | `parent.data_authorizations` | SEED-WHEN-BUILT, only if the owning module requires a row for synthetic origin (§11.6) | S9 |
| core transaction infrastructure | `core_audit_entries`, `core_outbox_events`, `core_outbox_consumer_receipts`, `core_aggregate_revisions` | SIDE-EFFECT | all |
| core legacy idempotency (register §3 row 3) | `core_idempotency_receipts` | NOT SEEDED: legacy/read-only | — |
| core assets | `core_asset_metadata`, `core_asset_lineage` | SIDE-EFFECT of upload finalize | S7, S8 |
| core Lesson upload (organization-scoped, register §14.4) | `core_upload_sessions`, `core_upload_parts` | SEED-NOW through the Lesson source upload commands | S8 |
| StoryRun upload | `storyrun_upload_sessions`, `storyrun_upload_parts`, `core_upload_command_receipts` (`20261102_story_run_lite`) | SEED-NOW through the Parent run upload commands | S7 |
| core legacy canvas | `core_canvas_checkpoints`, `core_canvas_operations` | NOT SEEDED: legacy/read-only (register §9) | — |
| learning_content catalog | `learning_content.record`, `version`, `review`, `receipt`, `event`, `outbox` | SEED-NOW (publication commands) | S5 |
| ai_policy retained (12) | `record`, `version`, `review`, `receipt`, `event`, `outbox`, `effective_scope`, `scope_transition`, `resource_scope`, `budget_bucket`, `resource_reservation`, `resource_event` | SEED-NOW through the lifecycle commands: activation, one compute scope and its buckets; reservations and resource events are SIDE-EFFECT | S5, S7, S8 |
| ai_policy legacy | the 12 `ai_policy.copy_*` registries and `ai_policy.resource_receipt` | NOT SEEDED: legacy/read-only, deferred to the real-data gate | — |
| ai_jobs | `job`, `attempt`, `command_receipt`, `semantic_request`, `completion_receipt`, `cancellation_notice`, `outbox`; `job_events` when built | SIDE-EFFECT of S7 and S8 dispatch and local completion | S7, S8 |
| lesson library | `library_items`, `library_versions`, `version_activities`, `library_source_documents`, `library_document_revisions`, `access_grants`, `command_receipts` | SEED-NOW | S1 |
| lesson library visuals | `lesson.version_visual_assets` | SEED-WHEN-BUILT | S8 |
| lesson occurrence, plan and deck | `lesson.occurrences`, `lesson.source_documents`, `lesson.document_revisions`, `lesson.plan_revisions`, `lesson.plan_activities`, `lesson.sketch_deck_revisions`, `lesson.sketch_deck_steps` | SEED-WHEN-BUILT | S8 |
| lesson delivery | `lesson.delivery_recipients` | SEED-WHEN-BUILT | S8 |
| lesson feedback | `lesson.delivery_feedback`, `lesson.feedback_replies` | SEED-WHEN-BUILT, blocked by O-SEED-IDLINK | S8 |
| story run and content | `story.runs`, `story.run_inputs`, `story.understanding_revisions`, `story.story_revisions`, `story.story_scenes`, `story.review_decisions`, `story.story_revision_reviews`, `story.command_receipts` | runs and inputs SEED-NOW (S1 direct SQL; S7 commands); content SEED-NOW through commands with O-SEED-AI | S1, S7 |
| story transcript and video | `story.transcript_revisions`, `story.video_generations`, `story.video_generation_scenes` | SEED-WHEN-BUILT | S7 |
| billing | the nine `billing.*` tables | SEED-WHEN-BUILT through Billing commands (S2 to S4, S7); invoices, payment attempts, provider receipts and subscription events are SIDE-EFFECT | S2–S4, S7 |
| notifications | `notifications.inbox_items`, `notifications.delivery_attempts` | SEED-WHEN-BUILT, produced by triggers | S10 |
| notifications endpoints | `notifications.push_endpoints` | NOT SEEDED: a push endpoint is a real device secret | — |
| other legacy schemas | collaboration, canvas, knowledge video, video review, video failure, activity execution, preset automation, `pilot_vision` | NOT SEEDED: legacy or pilot, read-only | — |

**Markers and counts for the new groups (extends rule 4):**

- Rows with a display name carry the `[SEED]` prefix (catalog titles, occurrence titles, plan objectives).
- Rows without one (plan activities, deck steps, delivery recipients, share grants, inbox items, job rows)
  are counted through their internal FK to a seeded root, or, for cross-owner opaque refs, through the
  seed's stable idempotency key on the command receipt that created them.
- Parent-owned rows (runs, uploads, quota usage, share grants) are counted by the seeded Parent principal,
  because a Parent has no organization.
- The implementation adds one count query per table of each stage.

## 11. Stages S5 to S10

All stages keep §2 rules 1 to 12. Stable keys follow §4.5: `seed:s<n>:<scope>:<case>`; text IDs keep the
`seed-` prefix and the 36-character limit.

### 11.1 Actors

The in-process actor is always the seeded adult who would act in the product: the Platform Admin for catalog,
policy and public review; the School Manager for roster and Billing; the assigned Teacher for occurrences,
plans and decks; the Parent owner for Parent profiles, runs, sharing and feedback. No stage acts as a role
that the product would refuse. Where a command exists only as an HTTP route function, rule 6 applies: the
owning slice extracts the application command first, and the stage stays `NOT_BUILT` until then.

### 11.2 S5 — platform catalog, policy and compute budget (SEED-NOW)

| Item | Created through | Result |
|---|---|---|
| Parent activity catalog | `learning_content` publication commands, as the Platform Admin (pattern: FEAT-048 `bootstrap_local_pg.py`) | 6 published activity versions with `[SEED]` titles; 1 draft; 1 in review |
| AI policy | `ai_policy` lifecycle commands | The local/test policy versions that the Story and Lesson flows check, activated for local/test only; no provider-copy row |
| Compute budget | `ai_policy` resource commands | One local/test `resource_scope` with `budget_bucket` rows for Story AI, Parent video and deck generation, large enough for S7 and S8. Reservations and resource events then come from S7 and S8 as SIDE-EFFECT |

S5 is replayable: every command uses a stable key and no billing time.

### 11.3 S6 — not seeded

There is no S6. SRS §2.2 keeps classroom collaboration sessions, QR, lobby and admission and stage progress
out of scope, AC-03 expects no collaboration runtime, and register §3 rows 17 to 30 class the 14 session
tables legacy/read-only (new writes stop after cutover). The session handlers are also route functions in
`interfaces/http/routers/be1_sessions.py`, not application commands. If the owner later wants compatibility
sessions for the current FE, that needs an explicit owner decision recorded with its date, a stage labelled
`LEGACY-COMPAT` that states it does not follow the SRS target model, and extracted commands.

### 11.4 S7 — assets, Story content and video

**Parents.** The S1 runs of P1 and P2 are left as they are (P1 holds `INPUT_PROCESSING`, P2 holds
`PREPARATION_REVIEW`, so both hold the one-active-run lock). S7 needs Parents with no active run, so the SEED
task that implements S7 adds two Parents to S1's data module: **P4 with K4** and **P5 with K5** (same S1
rules: direct SQL, synthetic, stable IDs). Every S7 run is then created and driven **only by commands**, one
run at a time per Parent, so the lock is respected.

1. **Assets (SEED-NOW, needs O-SEED-SCAN):** synthetic drawings and one audio clip (rule 11) uploaded through
   the StoryRun upload commands (`storyrun_upload_sessions`, parts, `core_upload_command_receipts`, finalize)
   into the rule-9 bucket, as the owning Parent. Asset metadata and lineage, including the scanner fields,
   come from finalize with the local/test scanner.
2. **Content (SEED-NOW, needs O-SEED-AI):** P4/K4 run R1 is created, gets a run input (drawing and typed idea),
   an understanding revision, a story revision with 3 scenes and the adult review decisions, all through the
   Story commands and the completion commands fed by the local adapter. Without the video tables R1 stops at
   the last state the built commands reach and is reported as such.
3. **Video and quota (SEED-WHEN-BUILT, after S4 and the video tables).** The SRS interim units are used: a
   Parent scope gets 2 units per month (SRS §2.1). Every usage row comes from an accepted full-video request
   (SRS §11.1 items 14 and 15), after a compute reservation from S5's budget.

   | Run | Requests | Units used | End state |
   |---|---|---:|---|
   | P4/K4 R1 | INITIAL (READY), then one QUALITY_REGEN (READY) | 2 of 2 | The adult completes it: `COMPLETED`. P4's scope is exhausted: the next request returns 409 `VIDEO_QUOTA_EXCEEDED` (time-sensitive) |
   | P5/K5 R2 | INITIAL (READY) | 1 of 2 | Left in `VIDEO_READY`; it holds P5's lock |
   | P5/K5 R2, cap case | two QUALITY_REGEN more, using the rest of the monthly grant and the S4 top-up | 1 + top-up | The run reaches the three-request cap; blocked until O-SEED-PAY gives the top-up |

   The S1 `COMPLETED` runs written by direct SQL have no generation. Once the video tables exist they are
   inconsistent with SRS §11.1 item 23, so the SEED task that adds the video part replaces them with
   command-made runs or removes them; until then the runbook lists them as pre-video fixtures.
4. **Delete case:** §11.8.

The video file is the O-SEED-VIDEO-ASSET output. The 144-hour adult-wait reminder for R2 needs a test clock
(§11.7).

### 11.5 S8 — lesson occurrences, lesson plans (giáo án) and decks (SEED-WHEN-BUILT)

Org A, Teacher T1 (assigned to class 1), through the Lesson commands, with uploads through the organization-
scoped Lesson source upload path and extraction through O-SEED-PARSE:

| Occurrence | Content |
|---|---|
| O1 — complete | Source document (generated DOCX or PDF, rule 11); an extracted document revision reviewed by T1; a lesson plan revision APPROVED with 2 plan activities and a confirmed safety checklist; a Sketch Teaching Deck revision READY covering both activities with 4 to 8 steps per instruction group (SRS §9.9, BR-43, FR-AI-14); delivery recipients from the class 1 roster snapshot (S1 data) |
| O2 — plan in review | Source document and extraction; a plan revision not yet approved; no deck |
| O3 — stale deck | Approved plan and a READY deck; then T1 edits the plan, which creates a draft plan revision and turns the deck STALE (SRS FR-T-20) |
| O4 — from the library | Created from Lesson Library L1's current version (S1), keeping the version reference and hash |

- Lesson Library L1 also gets 2 `version_visual_assets` (TOPIC_REFERENCE, ACTIVITY_ILLUSTRATION).
- The register gives 3 to 5 steps per instruction group (§5.5); the SRS and this design use 4 to 8. The
  conflict is noted for register reconciliation.
- **Blocked:** Parent feedback and Teacher replies on O1 wait for O-SEED-IDLINK. The Teacher StoryRun on O1,
  the occurrence sample-video claim (SRS §11.1 item 6) and the per-occurrence projection confirmation (item 19)
  wait for Q-01 and the video tables; they are a later task, not part of S8.

### 11.6 S9 — profile depth and sharing (SEED-WHEN-BUILT)

| Item | Content |
|---|---|
| Parent context | K1: one OUTSIDE_EXPERIENCE and one ACHIEVEMENT entry with short synthetic text |
| Parent support needs | K3: one entry; the note is encrypted with the O-SEED-KEY throwaway key |
| Teacher profile extension | Org A class 1 profiles: a first revision each; one context entry; no support note |
| Profile share grant | K1 → Teacher T1 of org A as a named-Teacher invitation, accepted by T1's command: ACTIVE (register §5.3, §14.2 item 4). Class- and school-scope grants are blocked: their acceptor is OPEN (register §14.3) |
| Data authorizations | None, unless the owning module's command requires a row for synthetic origin; then only the module's synthetic state and `source_kind`. Never a row that looks like a real consent (SRS §12.2). Anything more waits for O-PCONSENT |

### 11.7 S10 — notifications (SEED-WHEN-BUILT)

- **Triggers: only those the SRS defines** (BR-33, BR-39, FR-B-14):
  - billing notices for org F (GRACE: payment failure, end of grace), to the organization's billing admin
    only (the seeded School Manager);
  - the 144-hour adult-wait reminder for P5's R2, through a test clock;
  - job updates for the P4 and P5 videos.
- **Channel:** IN_APP only, through the O-SEED-NOTIFY local setting; no e-mail or push delivery and no push
  endpoint.
- **Replay path:** inbox items come from outbox events. Events published before the notifications module
  existed are not backfilled, so S10 runs as part of a re-seed after the module lands.
- **Read state:** some items are marked read through the product command, so both states exist. Delivery
  attempts are SIDE-EFFECT.

### 11.8 StoryRun lifecycle states after FR-C-08

FR-C-08 (implemented, not yet merged into the seed's base) adds the cancel command, the DELETE route, a
lifecycle consumer that purges and finalizes `DELETED`, and a reconciliation command that **inserts the
missing outbox event** for any Parent `DELETE_PENDING` run that has none. The purge itself happens only when the
consumer processes that event. A `DELETE_PENDING` row written by direct SQL (Draft 6 §4.1, SEED-1) is therefore
purged after a reconciliation run followed by any consumer run.

Once FR-C-08 is merged, the SEED task that applies this section:

1. removes the direct-SQL `DELETE_PENDING` run of P1/K1 from S1 (and any reconciliation must not have run before);
2. deletes the S1 P1/K1 `FAILED` run through the DELETE route and runs the consumer until that run is
   `DELETED`. This also produces the `be1_data_lifecycle_requests` row and the audit rows. The `FAILED` run has
   no S7 content, so nothing else is purged;
3. then cancels the S1 P1/K1 active run (`INPUT_PROCESSING`) through the cancel command, which leaves it
   `DELETE_PENDING` with an unprocessed event and releases P1's lock;
4. never runs the consumer, an outbox publisher or a sweep on the seed database again.

**Runbook warning (from now on):** on a seed database, never run the FR-C-08 reconciliation command, its
lifecycle consumer, an outbox publisher or a sweep runner, unless the runbook step names it.

### 11.9 Clocks

- **Billing:** the billing time control of O-SEED-CLOCK (§3) drives S3 and stays advanced for S4 and S7.
- **Story idle deadlines (the 144-hour reminder):** need their own test clock, owned by the Story module.
- **Upload session expiry:** owned by its upload module.
- **Notification dedupe windows:** owned by the notifications module.

Each stage's Task Approval names the clock it relies on and how the seed sets it. Without a test clock, the
time-based cases are marked time-sensitive and are not asserted.

### 11.10 Acceptance additions (S5 to S10)

- The storage guard refuses each case of rule 9: a missing or non-loopback endpoint, a bucket without `seed`,
  a non-empty foreign bucket, a key outside the seed prefixes, any `AWS_*` variable or credential file, and an
  application `S3_*` value that differs from the guarded one.
- With `ai_provider` other than `disabled`, `auth_provider` other than `development`, or any provider field or
  Modal variable of rule 10 set, the seed refuses to start; no network call leaves loopback.
- Every stored file's hash equals the data module's value.
- Every notification `safe_parameters` payload carries no child name, story text or media reference.
- A `NOT_BUILT` stage is reported as `NOT_BUILT`, never as passed.
- Each role can open its main FE screens with data:
  - Platform Admin: catalog, public review queue, price versions.
  - School Manager: roster, classes, capacity, Billing, Parent groups, library approvals.
  - Teacher: classes, occurrences, lesson plans, decks, library.
  - Parent: profiles, StoryRuns, videos, video quota, notifications.

  Teacher StoryRuns and Parent lesson feedback are excluded until their blocks (§11.5) clear.

## 12. Disposition of the Draft 7 cold review (R1)

| ID | Disposition |
|---|---|
| P1-1 | §10: the 14 session tables and `core_idempotency_receipts` are NOT SEEDED (legacy/read-only); S6 removed (§11.3); §1, §3, §4.1, §7 (O-L3SCOPE), rule 12 and §11.10 aligned |
| P2-1 | Rule 12 scoped to lifecycle-consumer states; GR3, revoked members and K2 listed as accepted exceptions with the reason |
| P2-2 | §11.4: P4 and P5 added for command-made runs; each video case names its run; the S1 `COMPLETED` rows are flagged and replaced in the video task |
| P2-3 | §11.4 per-scope arithmetic with the SRS interim units; S4 keeps only the top-up (§4.4); usage comes only from S7 requests; S5 adds the compute scope and buckets |
| P2-4 | §10 and §11.4: StoryRun upload tables for Parent media, Lesson source upload for S8; O-SEED-SCAN added |
| P2-5 | Rule 10 reworded: no adapter exists; the fakes are patterns; provider fields and variables listed |
| P2-6 | Rule 9 rewritten to mirror rule 3, including the consumer's client and the credential chain |
| P2-7 | §11.6: no authorization row unless the module requires one; the ACTIVE grant is a named-Teacher invitation accepted by command; class and school scope blocked |
| P2-8 | O-SEED-IDLINK added; feedback and replies blocked (§10, §11.5) |
| P2-9 | Teacher StoryRuns and the sample claim moved out of S8 to a later task, blocked by Q-01; §11.10 updated |
| P2-10 | §11.8: reconciliation wording corrected; the sequence respects the lock and uses the FAILED run for deletion; the warning covers the consumer, publisher and sweep |
| P2-11 | §11.7: SRS triggers only, recipient, channel and replay path stated; §11.10 asserts no child content |
| P3-1 | §3 header, the replay note and §6 updated |
| P3-2 | §10 lists `story.command_receipts`, the StoryRun upload tables, the 12 ai_policy names and the legacy ai_policy row separately |
| P3-3 | §10 marker and count rules for the new groups |
| P3-4 | Rule 11 requires normalized generation, names SVG and PPTX, and puts generator libraries under the Task Approval |
| P3-5 | §11.5: register conflict noted; O3 uses the FR-T-20 edit path |
| P3-6 | §7: O-SEED-SCAN, O-SEED-PARSE, O-SEED-IDLINK, O-SEED-KEY, O-SEED-NOTIFY, Q-01 and the FR-C-08 merge dependency added; O-L3SCOPE relabelled |
| P3-7 | Rule 10 names the provider settings and variables; §11.9 names the clock owner per stage |
| P3-8 | §3: S8 no longer depends on a session stage; S5 runs any time after S1 and before S7; the sample claim is a later task |

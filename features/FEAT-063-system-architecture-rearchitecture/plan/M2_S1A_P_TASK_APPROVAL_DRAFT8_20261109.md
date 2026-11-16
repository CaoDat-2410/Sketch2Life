# M2 S1a-P Task Approval — Draft 8 (2026-11-09)

**Status: DRAFT — NOT APPROVED, NOT LAUNCHED.** This document proposes a bounded Parent-profile implementation and two separate owner-run gates. It is not an approval, does not launch S1a-P, and grants no database write or command execution.

**Owner decision record:** D-171 through D-179 have been read from the M2 decisions block. D-171 through D-175 provide the product, scope, identity, receipt, and inventory directions; D-176 closes the Ruff-baseline disposition; D-177 resolves S1AP-Q1 and D-178 records the owner's reaffirmation; D-179 resolves S1AP-Q2 and the M2 decision-citation convention. These decisions do not approve S1a-P implementation or database operations. S1AP-Q1 and S1AP-Q2 are resolved. S1a-P remains pending a fresh independent review and separate owner approval. For any future citation of a duplicated D-135–D-149 identifier, use the explicit `(M2)` or `(dev)` lineage label required by D-179; do not infer lineage from number or position.

**Owner-question status:** S1AP-Q1 is resolved by D-177 and reaffirmed by D-178. S1AP-Q2 is resolved by D-179 option A: the exact historical route-baseline fixture is an R input, and the fixture-dependent compatibility comparison and Parent composition assertions remain in scope. The fixture itself is not editable. These decisions do not approve implementation or database operations; a fresh independent review and separate owner approval remain required.

## 1. Baseline, authority, and provenance

| Item | Current value | Use and limitation |
|---|---|---|
| Branch / HEAD / index | feature/feat063-m2-parent-teacher-foundation / 4b7f07cc283721f01f64e41ff2d81f135f63ad29 / empty | Recheck immediately before review and approval. |
| S1a-T phase | Accepted by the M2 S1a-T Closure Acceptance — 2026-11-09 entry in the pinned approval record | The closure report is source evidence; owner acceptance is evidenced by the approval entry. |
| DECISIONS.md | Current SHA-256 is pinned in §5; includes D-171 through D-179 | Any later appended decision changes the pin and requires this draft to be reconciled and reviewed again. |
| TASK_APPROVAL.md | Current SHA-256 is pinned in §5; no S1a-P entry exists in this draft state | The later approval entry, if authorized after review, must be append-only and the final heading with the S1a-P approval prefix before Gate A. |
| SRS | v2.7-draft Rev57; SHA-256 in §5 | Canonical working requirements, still unsigned. It is not final product sign-off. |
| Data Table Register | Current SHA-256 in §5 | D-173 adds parent.command_receipts as an M2 amendment; do not edit the register in S1a-P. |
| Physical Data Dictionary | Rev57 draft; SHA-256 in §5 | Target design only. It does not approve physical SQL types, nullability, keys, constraints, or indexes. |
| S1a-T inventory | inventory.post.json, SHA-256 710F4A42FA817FA2EC27DC154BF6023F35FD51C012BBACA39782320357D8737E; 117 tables, 29 rows | Recorded owner-run artifact; not a live database query in this drafting session. D-175 makes this Gate A’s exact pre-migration baseline. |
| Migration graph | Static source parse: 28 current revisions, 12 raw down_revision heads, 9 dependency-resolved heads | Source-derived counts only. No Alembic CLI or live graph was inspected in this session. |
| Current Parent database state | NOT VERIFIED in this session | No PostgreSQL connection was made. Gate A must establish identity and inventory before any write. |

The first-gate check was performed against the current worktree: branch and HEAD match the values above; index is empty; DECISIONS.md has the expected base-blob prefix and appended M2 decision rows through D-179; known local changes are the decision rows and plan drafts listed in the progress report. The prior Draft 4 pin for `tmp/m2-progress/NOTES_S1A_P.md` differed from the actual file because that note had already been appended; the current file was read and its actual SHA-256 is pinned in §5. No other unexpected source-path drift was found.

## 2. Phase scope and owner directions

### 2.1 Included behavior

S1a-P implements only the Parent-owned profile foundation on the existing task database sketch2life_m2_s1a:

1. POST /v1/parent/profiles creates one synthetic Parent profile for any verified principal, as the explicit owner direction in D-156 R4; this self-create contract controls this M2 route even though SRS §21.2 labels the actor Parent. Ownership is immediately bound to the verified issuer and subject, and every later read/update is owner-only. The server issues profile_id, initial revision number 1, revision hash, age-band fields, and author metadata. The request contains display_name and age_months; interests_summary is optional and nullable. Unknown input fields are rejected. New rows use state=ACTIVE, deleted_at=NULL, and data_origin=SYNTHETIC_DEV.
2. GET /v1/parent/profiles/{profile_id} returns the owner’s current profile projection and revision.
3. PATCH /v1/parent/profiles/{profile_id} is the next full snapshot with expected_revision. Under D-177 and D-178, omitted nullable interests_summary is normalized to JSON null, exactly like explicit null. Acceptance must exercise both request forms from equivalent starting state and assert the same normalized payload and revision_hash when all other values match. On success PATCH appends an immutable revision and advances the current-revision pointer atomically. A stale revision returns 409 STALE_REVISION with the current version, without overwriting the current revision.
4. Both mutating routes require Idempotency-Key, scoped by verified issuer, subject, operation, and resource. A repeated key and same canonical payload returns the stored original status/body. A repeated key with a different payload returns 400 INVALID_IDEMPOTENCY_KEY and does not overwrite the first receipt.
5. Ownership requires both verified issuer and subject. A missing profile, a profile owned by a different subject, and a same-subject profile from a different issuer return the same 404 PROFILE_NOT_FOUND code and generic message. No owner, issuer, or existence detail is returned.
6. Parent synthetic HTTP creation follows the M2 synthetic gate: only settings.env in {local, test} with synthetic_pilot_enabled=true; fail closed otherwise. The request cannot select data_origin, consent fields, age-source fields, or identifiers. No consent or age-source columns are added.

### 2.2 Excluded behavior and claims

- **S2 entry condition (D-171 (M2), D-151 (M2); not an S1a-P route or implementation):** Before S2 approval, its Task Approval must name the StoryRun application-service boundary `StoryRunLiteService.create_run` and require it to resolve the selected profile age from trusted profile storage, not the client-supplied `child_age_months`, and reject ages 121–155 before any run row is written. S2 acceptance must prove the rejection and absence of a persisted run. S1a-P does not modify StoryRun code or test StoryRun creation.

- No profile list, delete, share/grant, consent, invitation, context, support-needs, data-authorization, Teacher, StoryRun, job, asset, or organization route.
- No S1b, S2, S3, M3–M6 implementation. S1b remains DEFERRED. OWNER_MODAL_CALL_APPROVED=NO.
- No update to the SRS, Data Table Register, Physical Data Dictionary, legacy BE1/Core/Story schema, or existing migration chain. parent.command_receipts is a recorded DTR amendment for later incorporation by its owner.
- Q-05 remains unresolved upstream. age_band_ref and age_band_version remain NULL in S1a-P. This phase does not claim AC-65 or NFR-38 is fully satisfied.
- S1a-P does not repair K3 or stamp/upgrade the Story/Core/BE1 graph. Existing 20261103_story_upload_compat / 20261104_story_revisions discrepancy remains outside scope.
- Platform Admin, Operator, and content-admin negative cases are NOT RUN because the current identity model has no such distinct principals/permissions in this acceptance surface.
- No cleanup, reset, truncate, downgrade, database replacement, or removal of the 29 S1a-T rows.

## 3. Contract and acceptance crosswalk

| Requirement / decision | Route or invariant | Table(s) | Owner | M2-AT | Evidence |
|---|---|---|---|---|---|
| SRS Rev57 §21.2; D-171 item 9; D-174 | `POST /v1/parent/profiles`; 201 profile reference + revision | `parent.child_profiles`, `parent.profile_revisions` | Parent | M2-AT-01, M2-AT-11 | Route contract and Gate B PostgreSQL test |
| SRS Rev57 §21.2; D-174 | `GET /v1/parent/profiles/{profile_id}`; owner projection; generic 404 for missing/non-owner/different issuer | `parent.child_profiles`, `parent.profile_revisions` | Parent | M2-AT-01 | IDOR cases; same status/code/message shape |
| SRS Rev57 §21.2/§21.4; D-171 item 9; D-177/D-178 | `PATCH /v1/parent/profiles/{profile_id}`; full snapshot, `expected_revision`, omitted nullable field normalized to null, append immutable revision, same-key replay | `parent.profile_revisions`, `parent.command_receipts` | Parent | M2-AT-01, M2-AT-10 persistence portion | Paired omission/explicit-null acceptance cases assert identical normalized payload and hash; revision/replay checks; Gate B persistence test |
| SRS Rev57 §21.4; D-173 | Same key/payload replays; same key/different payload returns `INVALID_IDEMPOTENCY_KEY` | `parent.command_receipts` | Parent | M2-AT-01, M2-AT-10 persistence portion | Gate B mutation/replay and no-extra-write checks |
| D-171 Q-11/Q-05; D-174; PDD Rev57 | Ages 36–120 for new Parent values; preserve existing BE1 36–155 reads and CHECK; no age-source | `parent.profile_revisions` | Parent | M2-AT-03 | Parent bounds and existing BE1 reader regression tests; no BE1 source or DB change |
| D-171 item 9; D-174; D-156 R8 | Synthetic-only `SYNTHETIC_DEV`; local/test + feature gate; no user-controlled origin | `parent.child_profiles` | Parent | M2-AT-11 | Enabled creation and fail-closed disabled-gate cases; disabled case has no Parent writes |
| D-173; DTR §5.3 | Parent-owned receipt table; no cross-owner FK or reuse of legacy/AI Jobs receipts | `parent.command_receipts` | Parent | M2-AT-01, M2-AT-10 persistence portion | Migration static test, Gate A inventory, Gate B marker counts |
| SRS Rev57 §21.2; Draft 11 §4.2 | Exactly three Parent operations; no additional `/v1/me`, list, or delete routes | N/A — route composition | HTTP application / Parent | M2-AT-01, M2-AT-11 | Composition, SRS projection, catalog exact-set and route-count tests |

AT coverage is intentionally narrow: M2-AT-01 covers Parent creation/read/IDOR/idempotency/revision behavior; M2-AT-03 covers Parent age validation; M2-AT-10 covers persistence/readback of Parent profile revisions only (not StoryRun creation); M2-AT-11 covers synthetic-only creation. AT-05/06/07 remain NOT RUN/DEFERRED under S1b. No phase-level PASS can be inferred from static planning or from unit/contract results alone.

The S2 age-eligibility condition above is a precondition for a later S2 approval and acceptance map; it does not expand S1a-P or assign an M2-AT number.

## 4. Proposed physical schema and service design

All details in this section are technical proposals under D-172 item 2. The reviewer must check physical integrity, graph behavior, ownership, replay semantics, and every stop guard. These proposals are not deployed facts.

### 4.1 parent.child_profiles

- parent_profile_id UUID PRIMARY KEY (server generated).
- owner_issuer TEXT NOT NULL, owner_subject TEXT NOT NULL; preserve exact values from the verified principal; no principal FK exists and none is invented.
- state VARCHAR(16) NOT NULL DEFAULT 'ACTIVE'; new route writes ACTIVE; deleted_at TIMESTAMPTZ NULL is NULL on create and remains unchanged because no delete route exists.
- created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, stored in UTC.
- current_revision_no BIGINT NOT NULL CHECK (current_revision_no > 0).
- data_origin VARCHAR(32) NOT NULL CHECK (data_origin = 'SYNTHETIC_DEV'). This is the single D-155/D-171 accepted deviation from the register. Do not add age_source, consent references, or another column.
- No extra unique key is needed on child_profiles because parent_profile_id is its primary key. The deferred FK target key is UNIQUE(parent_profile_id, revision_no) on profile_revisions.

### 4.2 parent.profile_revisions

- profile_revision_id UUID PRIMARY KEY, parent_profile_id UUID NOT NULL with an internal FK to parent.child_profiles(parent_profile_id) ON DELETE RESTRICT.
- revision_no BIGINT NOT NULL CHECK (revision_no > 0) and UNIQUE(parent_profile_id, revision_no).
- age_months SMALLINT NOT NULL CHECK (age_months BETWEEN 36 AND 120); strict integer validation in the request schema, excluding booleans.
- age_band_ref TEXT NULL, age_band_version TEXT NULL, with a pair-consistency check; both are NULL for every S1a-P write because Q-05 has no configured catalog.
- display_name VARCHAR(120) NOT NULL; reject empty/whitespace-only input and values over 120 Unicode code points; preserve the accepted string rather than silently truncating it.
- interests_summary VARCHAR(2000) NULL; reject values over 2,000 Unicode code points. POST omission maps to JSON null. For PATCH, omission and explicit null both normalize to JSON null before canonicalization; add acceptance cases proving identical normalized payload and revision_hash when all other fields are equal.
- authored_by_issuer TEXT NOT NULL, authored_by_subject TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, revision_hash CHAR(64) NOT NULL with lowercase-hex validation.
- Enforce revision immutability in PostgreSQL with a BEFORE UPDATE OR DELETE trigger that raises a fixed integrity exception. The application never updates or deletes a revision.
- Normalize optional nullable fields before hashing: omitted interests_summary becomes JSON null. Compute revision_hash as SHA-256 lowercase hex over UTF-8 JSON of the canonical revision fields age_band_ref, age_band_version, age_months, display_name, and interests_summary, with keys sorted, compact separators, ensure_ascii=False, and allow_nan=False. Exclude ids, timestamps, authorship, expected revision, and request metadata.

### 4.3 Current-revision cycle

Create `parent.child_profiles` first with no current-revision foreign key, then create `parent.profile_revisions` with its internal profile FK and UNIQUE(parent_profile_id, revision_no), then add named constraint `fk_parent_child_profiles_current_revision` from child_profiles(parent_profile_id, current_revision_no) to profile_revisions(parent_profile_id, revision_no) as DEFERRABLE INITIALLY DEFERRED. Both sides are Parent-owned; no cross-owner FK is used. In the create transaction, insert profile at revision number 1, insert revision 1, then commit so the deferred constraint checks the complete pair. For PATCH, lock the owned profile row, compare expected_revision, insert revision n+1, update only the profile pointer and updated_at, and commit atomically. The migration must add the composite FK after both tables exist and drop it before dropping either table. The rejected alternatives are an unconstrained pointer or an immediate constraint that prevents the first profile/revision pair.

The migration downgrade function must be defined in reverse dependency order: drop `parent.command_receipts`; drop trigger `trg_parent_profile_revisions_immutable`; drop function `parent.reject_profile_revision_mutation()`; drop constraint `fk_parent_child_profiles_current_revision`; drop `parent.profile_revisions`; drop `parent.child_profiles`; then drop schema `parent`. Indexes and table-local constraints are removed with their tables. This is a source-design requirement only: neither owner-run gate authorizes executing downgrade, and no downgrade may run against a database containing S1a-P data.

### 4.4 parent.command_receipts

- Parent-owned receipt_id UUID PRIMARY KEY; verified principal_issuer TEXT NOT NULL, principal_subject TEXT NOT NULL; operation_scope TEXT NOT NULL; stable non-null resource_scope TEXT NOT NULL; key_hash BYTEA NOT NULL with named CHECK `ck_parent_command_receipts_key_hash_len` requiring octet_length(key_hash)=32; request_fingerprint BYTEA NOT NULL with named CHECK `ck_parent_command_receipts_fingerprint_len` requiring octet_length(request_fingerprint)=32; response_status SMALLINT NOT NULL; response_body JSONB NOT NULL; created_at TIMESTAMPTZ NOT NULL.
- Unique (principal_issuer, principal_subject, operation_scope, resource_scope, key_hash). POST uses a stable collection scope because the profile id is not known before first execution; PATCH uses the target profile id. No FK to a non-Parent owner, no reuse of core_idempotency_receipts or ai_jobs.command_receipt, no raw key/token storage, no expiry or cleanup in this phase.
- Hash the key and canonical request independently with SHA-256. Proposed key validation is 1–128 visible ASCII characters with no whitespace; malformed key is a request error before lookup. Serialize concurrent same-key requests with a transaction-scoped PostgreSQL advisory lock derived from the full scope/key hash, then use the unique constraint as the durable backstop. For each successful mutation, profile/revision changes and the receipt commit in the same database transaction; a crash must not commit one without the other. A concurrent same-key/same-payload pair returns the same original status/body and creates one logical mutation and one receipt; a concurrent or later same-key/different-payload request returns `INVALID_IDEMPOTENCY_KEY` without an extra receipt or profile/revision write.
- Record the terminal response snapshot for a syntactically valid, authenticated mutation after the idempotency scope is established; replay returns its original status/body. A reused key with a different fingerprint returns INVALID_IDEMPOTENCY_KEY and does not replace the original receipt. Invalid unauthenticated or schema-invalid requests do not create receipts. This behavior is a technical proposal for the reviewer to challenge, not a new product decision.
- Index (principal_issuer, principal_subject, created_at) for owner-scoped lookup/inspection. Retention and cleanup beyond this synthetic-only phase are NOT COVERED.

### 4.5 Stable PostgreSQL object names

Every proposed constraint, index, trigger, and trigger function has an explicit stable name below; migration code must declare these names rather than rely on dialect-generated defaults.

| Object | Kind | Stable name |
|---|---|---|
| `parent.child_profiles` | Primary key | `pk_parent_child_profiles` |
| `parent.child_profiles.current_revision_no` | CHECK (> 0) | `ck_parent_child_profiles_current_revision_no_positive` |
| `parent.child_profiles.data_origin` | CHECK (= 'SYNTHETIC_DEV') | `ck_parent_child_profiles_data_origin_synthetic_dev` |
| `parent.profile_revisions` | Primary key | `pk_parent_profile_revisions` |
| `parent.profile_revisions.parent_profile_id` | Internal FK to child profile, ON DELETE RESTRICT | `fk_parent_profile_revisions_parent_profile` |
| `parent.profile_revisions.revision_no` | CHECK (> 0) | `ck_parent_profile_revisions_revision_no_positive` |
| `(parent_profile_id, revision_no)` on `parent.profile_revisions` | UNIQUE target key for current-revision FK | `uq_parent_profile_revisions_parent_revision_no` |
| `parent.profile_revisions.age_months` | CHECK (36–120) | `ck_parent_profile_revisions_age_months_36_120` |
| `parent.profile_revisions.age_band_ref`, `age_band_version` | Pair-consistency CHECK | `ck_parent_profile_revisions_age_band_pair` |
| `parent.profile_revisions.revision_hash` | Lowercase 64-hex CHECK | `ck_parent_profile_revisions_revision_hash_sha256` |
| `parent.child_profiles(parent_profile_id, current_revision_no)` | DEFERRABLE INITIALLY DEFERRED composite FK | `fk_parent_child_profiles_current_revision` |
| `parent.profile_revisions` | BEFORE UPDATE OR DELETE trigger function | `parent.reject_profile_revision_mutation()` |
| `parent.profile_revisions` | BEFORE UPDATE OR DELETE trigger | `trg_parent_profile_revisions_immutable` |
| `parent.command_receipts` | Primary key | `pk_parent_command_receipts` |
| `parent.command_receipts.key_hash` | CHECK (octet_length = 32) | `ck_parent_command_receipts_key_hash_len` |
| `parent.command_receipts.request_fingerprint` | CHECK (octet_length = 32) | `ck_parent_command_receipts_fingerprint_len` |
| Receipt scope, principal, and key hash tuple | UNIQUE | `uq_parent_command_receipts_scope_key` |
| `(principal_issuer, principal_subject, created_at)` on `parent.command_receipts` | Index | `ix_parent_command_receipts_owner_created_at` |

## 5. Pinned inputs and exact allowlist

The following baseline hashes are computed from the current worktree after recording D-179, appending the progress update, and preparing Draft 7 from the reviewed Draft 6. Existing candidates are pinned before any edit; new paths must be absent. R is read-only, R/E is readable and an existing edit candidate, H is historical read-only, and N is a new-path candidate. No wildcard or implied directory permission exists. The approval entry and this draft are governance/control-plane records, not implementation allowlist paths. Any changed pin or additional path requires a stop and a revised review.

### 5.1 Read-only inputs (R)

| Mode | Repository-relative path | SHA-256 |
|---|---|---|
| R | `.claude/handoff/logs/M2_S1A_T_20261107/f7fe88273c7f4dd89b3913efeac6f8fb/inventory.post.json` | 710F4A42FA817FA2EC27DC154BF6023F35FD51C012BBACA39782320357D8737E |
| R | `.codex/sketch2life-harness.md` | 0364DD280483D7AB56EAAF7F0B2CEF56A86D627393CA9996FC88A14E3318E12F |
| R | `AGENTS.md` | 89ACC84AA4D838730205A03917B40DEB37E9622AAF7092E982476D934EC29A61 |
| R | `backend/alembic.ini` | 702FE3BDE96CAA64DB94B0C7EE6EB47F1F51D49713EFF94F3C48C33AACF892C9 |
| E | `backend/alembic/env.py` | FABE5736CC7A49CC3C3D36112B4780248113DEEA3DE9A3DA4D2C2CB85E937447 |
| R | `backend/alembic/versions/20261014_0001_core_persistence.py` | 55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C |
| R | `backend/alembic/versions/20261014_0002_be1_runtime.py` | 08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520 |
| R | `backend/alembic/versions/20261014_0003_canvas_payload.py` | 194A831C661CA84C796557CCCF762715F6C0CC0E747521D588D1F30E1A5BB9E5 |
| R | `backend/alembic/versions/20261014_0004_be1_constraint_names.py` | AB15DFCE0738D994B14B337A03B34F7365BBBC67AFFE3BB01F24901F87BAFFFD |
| R | `backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py` | D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714 |
| R | `backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py` | 81F84E9B3C4C7929018EB0A82ABED1DC2581811BB178EC6097E3134BBD8D765A |
| R | `backend/alembic/versions/20261017_ap_0002_effective_scope.py` | 35DBAA33A4F41EC69A01E03D688AF9B9238145EE0006D54CA67C115D0987CDE7 |
| R | `backend/alembic/versions/20261017_ap_0003_resource_ledger.py` | FEE3A90E27691B90B1D45E6DE7D14C3DB77311EBE86414051B55C75D02AB1924 |
| R | `backend/alembic/versions/20261017_ap_0004_copy_inventory.py` | 3EC8747A198941C9C4B36C4FDD0E08986355F0B2334589951EEA99BBF20AC2E7 |
| R | `backend/alembic/versions/20261017_ap_0005_copy_evidence.py` | 9E364BF938C2D6B6714FDE8C2A2527AAB84D3DD378C1AE16C0578FD86B9B8C12 |
| R | `backend/alembic/versions/20261017_lc_0001_content_publication.py` | DA2B372442A7CF234B8C1FC0FC7472B5A068FE8F832B6465C1BC1E4D2FE2F498 |
| R | `backend/alembic/versions/20261018_ap_0006_copy_operations.py` | B266744B3792E0E68347FA674B374A54D14CC33E4776106ADE91E2E407C447F7 |
| R | `backend/alembic/versions/20261018_ap_0007_copy_delivery.py` | 3BF400A165F5D681017FFE1AADEEAEB724BFFF5992289FB21331F5247C479E52 |
| R | `backend/alembic/versions/20261018_ap_0008_delivery_authority.py` | 9D8171F8B00C603FD350E32B6D6412B049A504F47B4D4F92355D654C86B71E05 |
| R | `backend/alembic/versions/20261018_ap_0009_copy_resolution.py` | 465A3421BC54895D2969AE95B1E3A9425689D1ED38B1CD6BCD8FE29D9B961A44 |
| R | `backend/alembic/versions/20261018_kv_0001_knowledge_video.py` | E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87 |
| R | `backend/alembic/versions/20261018_vr_0001_video_review.py` | 3E489443949C0934B414E4A69C6BD01B09782F4653042803C79291D66B415FC7 |
| R | `backend/alembic/versions/20261019_ae_0001_activity_execution.py` | 56993DC8CE1507D471ED3E3052F99A3A05B9D26C64E979822198946CD9EF9C30 |
| R | `backend/alembic/versions/20261019_pa_0001_preset_automation.py` | D2A8B958D6BD9411D040E3358F5568E2C728C1095D5395D55532916ACC5182E8 |
| R | `backend/alembic/versions/20261019_vf_0001_video_failure.py` | 0520CB0EB850D1BB4A267571F30937677908E505B77E221D1F0C90EE806FD178 |
| R | `backend/alembic/versions/20261024_0005_classroom_srs_contracts.py` | E533FC15447222C334A82CD162DC01FEB7B94221B402552D774CBD11E7D7289C |
| R | `backend/alembic/versions/20261028_ll_0001_lesson_library.py` | 733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83 |
| R | `backend/alembic/versions/20261031_be1_synthetic_eligibility.py` | 421F695FE49193C4A2EDCAC66B4461D8AFCB47B825813918E0083B21BC1483FC |
| R | `backend/alembic/versions/20261101_be1_age_provenance.py` | 2A634DC4DDF00326AFEF4079F7795A185D458DE2DB65BA6FD3C40291BBA5614E |
| R | `backend/alembic/versions/20261102_pilot_vision.py` | 6335AD224708AEC8251447A296458854B663FC7DD763EFB184E4AFF156E86BD9 |
| R | `backend/alembic/versions/20261102_story_run_lite.py` | D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143 |
| R | `backend/alembic/versions/20261103_story_upload_compat.py` | F16346F5D0D320B22AF0767F387FE066ED3683D57DDD380804424B5A837CA166 |
| R | `backend/alembic/versions/20261104_story_revisions.py` | 3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8 |
| R | `backend/pyproject.toml` | 2B8EF44141D0BC4702B73C414AE77325DA547F45B1EDBF37008114E9BCD46C1A |
| R | `backend/src/sketch2life/application/ports/identity.py` | 1065A42D44766BE16103AA463E2243DC2FF4EF8AA2A793FDF3F3A8944BA80E47 |
| R | `backend/src/sketch2life/application/services/be1_runtime.py` | BD1D57B2E69ABB71F6FB933BF66CC499F36CA8F79D1FE03F6CE99FFD6AEBC3E4 |
| R | `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | 7B3C7FD2F767D3E0062CC6B2217A5DDE39FCE5D9566EA4A4C350CC7C35FA31E1 |
| R | `backend/src/sketch2life/domain/child_age.py` | C4A1288A41D6EC52087A9BB83F7F8590D1084C367A41BD512D65ACA917A2838C |
| R | `backend/src/sketch2life/domain/core_foundation.py` | EDBAF8AF58962E1EEA411B981565A352034D50D02A13812DCDD79DC2EB25A884 |
| R | `backend/src/sketch2life/infrastructure/config/settings.py` | DB1A5FB6E4F7C800F00B4AD1F9386D20AEE7F41DBD35BA54C7F13426D7CDD387 |
| R | `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py` | 0B2DEF14F43F80C311F4D0DBC71DD29F90C2E1FC0BA6032DB20B999CAE8287FD |
| R | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | 6859CC8313482C70828176B4E12209B485B7D582C6831340AE0D451659219C1E |
| R | `backend/src/sketch2life/infrastructure/persistence/core_models.py` | 47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A |
| R | `backend/src/sketch2life/infrastructure/persistence/core_store.py` | AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94 |
| R | `backend/src/sketch2life/infrastructure/persistence/database.py` | C37F51CE9BE25C66F98065A68516E549E94B99219FF24CF846BE1755616194FF |
| E | `backend/src/sketch2life/interfaces/http/app.py` | D9DCBDC5BF3B71840C98BEB50A80D5A7BC1D800C3F93FFBB05DD021E99A995C0 |
| R | `backend/src/sketch2life/interfaces/http/be1_runtime.py` | 62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85 |
| E | `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 2AF19D4CFEBA4C4EBF85D3C48F1735748FFAE3ADE00F50B5BAD7DBFAE6269EC8 |
| E | `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | B0230E5E9820CEA221DBE00934FFC1C90B6BA04E5CD81B5A5DB9D2B0EF9D8AE1 |
| E | `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | A7EA951459965EB57D54D42C36F7900B8CB72E6604D7F69B4A87A82B0E355168 |
| E | `backend/src/sketch2life/interfaces/http/router_composition.py` | E06A158B3616583DF8ABBA21D52C62E769AFA6A9E7C75359D28D424AB15849CC |
| R | `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | 40DDE6F9B2AC91A78FE2A2F65B15EFCB1B76D132D49BB5580338710B12B9C45C |
| R | `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` | B090F30C4F87FB53D8A85A83C53391AD77F086AF83F0A1E202EACB0F1C0375FE |
| R | `backend/tests/conftest.py` | D4D18732D1C4F5518A1AAA36A9FACD98926F13BF8C10504FC0C866DABFC1A7E5 |
| E | `backend/tests/contract/test_app_composition.py` | 78A29EE6DE0D42AE6933AE9CE9DDA469920BEF3E3ED99A62C83967338C496B56 |
| R | `backend/tests/contract/test_be1_fact_reader_contract.py` | E401756730F74883A16AF0703162E501F407AD1F5F57F10C868154E6CD48F95A |
| R | `backend/tests/contract/test_be1_synthetic_pilot.py` | E9ADBAA52EEF29AF852FFCCE81D46F19226D5C1EB8D2A23E3D51B060744C7863 |
| R | `backend/tests/contract/test_m2_s1a_teacher_routes.py` | A3BE759D8031FA0EC80A697E2D6226D739EA4D772811376F91EA6A8600D8B003 |
| E | `backend/tests/contract/test_openapi_contract_catalog.py` | C5808E63CD4E9DA8C987C8301565DB0ECDD3E0C9DDAC13A9F75A2D2EDC4EE998 |
| H | `backend/tests/integration/ai_jobs/test_migrations.py` | BF1D51D21262C3E76206C9A0FD01EBD3B3FE7006AA0B00DC28109A81C0A9238E |
| R | `backend/tests/integration/test_m2_s1a_teacher_postgres.py` | 93EEBFFD8E51ADE58F63D19AF707A56F8F0E859BE0648D38B3D15CE2DA9EDDEB |
| R | `backend/tests/unit/test_age_provenance_columns.py` | 119BA4D87CB4EDA84322BBF42F71FD822E6C6E8286E733DDAA800B96C2AA65FC |
| R | `backend/tests/unit/test_be1_fact_reader.py` | F234E7056F0FAFD0479519AB419271E3EE19552E1AF55A17E5A09CD387F5F815 |
| R | `backend/tests/unit/test_m2_s1a_teacher_service.py` | BC07B8682C1A0E27930C366812B58EA9DDB77CEB62752FB3FEB046ABA99466FC |
| R | `backend/tests/unit/test_profile_age_invariant.py` | B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB |
| E | `backend/tests/unit/test_synthetic_eligibility.py` | B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1 |
| R | `docs/context/SOURCE_REGISTER.md` | 42E8C8BA0DCF0128D64F719F38F99C569B657E707BB3BBE1402F42115629412E |
| R | `docs/context/SRS_AUTHORITY.md` | E47A55EC904DF5D27DC3D271DD313496397F15DBEDCD23AEC272FC37BF97B342 |
| R | `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | A0CB85E214E80BED8EE9AEEF665CC9979F579553BD9117D0D8D682DF641AD8F5 |
| R | `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | 6EF3DC2FF50BE508D38C5D25C841072EAFA4EAD826A6BD6BE88AF2ED23D8964A |
| R | `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 4F34316C7F5E7872DDDB1B8D9E0768544BB3C1F4E33DE789F68BA6A44A96A19C |
| R | `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` | 63A24EB5E5A777E657FCDE13D421D866F0205A50AED16D9FB8061914C74EBE9D |
| R | `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 64A6ADD63B3E6B340A42EC4A73CE61965074DD84C0113E3BB4D00F0D70D87DA8 |
| R | `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` | 7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2 |
| R | `features/FEAT-063-system-architecture-rearchitecture/artifacts/DECISION_REGISTER_REV57_20261109.md` | 2E54FD8AEEDA6785056A07017CEFE1780B927E429B06998D93DAA37C16C27903 |
| R | `features/FEAT-063-system-architecture-rearchitecture/artifacts/PHYSICAL_DATA_DICTIONARY_DRAFT_REV57_20261109.md` | DDBF2E7D9748AF1C9DD74C427E1C8A9D598921D7C213381EC8F0DCECC5B111CF |
| R | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5 |
| R | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_CLOSURE_RECORD_20261109.md` | D2ACD33F03E28C961F30270F310F27913257D39A28CEC8281D29ADAE5D285FDE |
| R | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md` | AF3CFFABA7B1C5D199DB4EC5CD123BA92C5D338647EB0A794C78E431DB3B028E |
| R | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md` | 7CC1D51D4091FF95CEF0A5863C559DDB8C73B8C9A9DB197A2AD796035F523998 |
| R | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_t_owner_run_20261107_r7.py` | D4016330DA42D38035F1ED14C95A51026C81AEFF31F9F72F1FA364028370DFB3 |
| R | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_CLOSURE_RECORD_20261108.md` | 65588C6876F653F3A0B17E227B8845E63EA2F6C77FB78756A91925DEBA9626D6 |
| R | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_GOAL_V2_FOR_CODEX_20261109.md` | FACC7DD92B548E43326317448EFDF0DE2ABCE1F1508F2015CD099CE33DC2E986 |
| R | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md` | 6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68 |
| R | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_PROGRESS_REPORT_FOR_CODEX_20261109.md` | 9B4B2FCF43F0AAD359412B192794A6C04A3974ECBAD55856BBD67DA4839948B8 |
| H | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_TASK_APPROVAL_DRAFT3_20261107.md` | 635689889C24C429B1440D62D8562D85ADC0477679BF1F364916576BB07C6BF5 |
| R | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R7.md` | D79EB097CBFC775F0FD411F94A743B8E2074EAE289BC60316E10CF263DC16E59 |
| R | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R7.md` | 395D43DE5C14559D8E6333CCCA853A0BDAA9D5954EB5332BD74AA2B1B415F200 |
| R | `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md` | 0A3C759D40FEE77DD2D1FDDCFE8FC1F7814244AABC098C1E5FCA405AA62D6B5C |
| R | `tmp/m2-progress/NOTES_S1A_P.md` | 5491C90283D4BE8A557430CD88AB0B69A1B86214E99ABD5704A1A1E566C5835B |
| R | `tmp/m2-review-s2s3/REVIEW_S2_S3_20261109.md` | 2709BDEE0B0A93446EA9721F442C7AF3199D966B03D06004FDF10B1F97A77D00 |
| R | `tools/validate_architecture.py` | FA236C8D389B608251153D601FC370EFE3F3E2479446CA4A56A3D395F892E0B5 |
| R | `tools/validate_harness.py` | 0804EABBAECF471F191E259760E48AA0DC2D5A4D23DA5D38336D8EDE2F09D232 |
| R | `tools/validate_repository_security.py` | EFD691DF935565D1FA148B5B4A765EF77C90D701D210FC5E869BFBD1548DD210 |
| R | `tools/validate_skeleton.py` | 464DE2DAA684970ADD58FCAC64C6EB2249E9D702EE00E6B272FD8F954DD25B6F |
| N | `backend/src/sketch2life/domain/parent_profiles.py` | ABSENT |
| N | `backend/src/sketch2life/application/ports/parent_profiles.py` | ABSENT |
| N | `backend/src/sketch2life/application/services/parent_profiles.py` | ABSENT |
| N | `backend/src/sketch2life/contracts/schemas/parent_profiles.py` | ABSENT |
| N | `backend/src/sketch2life/infrastructure/persistence/parent_models.py` | ABSENT |
| N | `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py` | ABSENT |
| N | `backend/src/sketch2life/interfaces/http/parent_runtime.py` | ABSENT |
| N | `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py` | ABSENT |
| N | `backend/alembic/versions/20261109_m2_parent_profiles.py` | ABSENT |
| N | `backend/tests/unit/test_parent_profiles.py` | ABSENT |
| N | `backend/tests/unit/test_parent_profiles_service.py` | ABSENT |
| N | `backend/tests/unit/test_parent_profiles_migration.py` | ABSENT |
| N | `backend/tests/contract/test_parent_profiles_routes.py` | ABSENT |
| N | `backend/tests/integration/test_m2_s1a_parent_postgres.py` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_gate_a_20261109.py` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_gate_b_20261109.py` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_offline_checks_20261109.py` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_GATE_A_LAUNCH_INSTRUCTION_DRAFT1_20261109.md` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_GATE_B_LAUNCH_INSTRUCTION_DRAFT1_20261109.md` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_K4_SOURCE_RECONCILIATION_20261109.md` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_IMPLEMENTATION_REPORT_20261109.md` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_CLOSURE_RECORD_20261109.md` | ABSENT |
| N | `features/FEAT-063-system-architecture-rearchitecture/plan/OWNER_CHECKLIST_S1A_P_GATE_A.md` | ABSENT |

S1AP-Q2 is resolved by D-179 option A. The exact read-only input `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` (SHA-256 `A0CB85E214E80BED8EE9AEEF665CC9979F579553BD9117D0D8D682DF641AD8F5`) is included as one R entry in §5. The fixture-dependent compatibility comparison and Parent composition assertions remain in scope. No other FEAT-059 path is permitted, and the fixture may not be edited.

## 6. Migration design and the two owner-run gates

### 6.1 Isolated Parent revision

Propose one new independent revision 20261109_m2_parent_profiles.py: revision = "20261109_m2_parent_profiles", down_revision = None, branch_labels = ("parent",), depends_on = None. Target only parent@head; do not use default heads, head, stamp, or create a second version table. The empty existing public.alembic_version is treated as no applied revision only after Gate A verifies that table exists and is empty. Alembic's own write of the new Parent revision row occurs only in owner-run Gate A. The migration source must include the reviewed downgrade order in §4.3; defining a downgrade function does not authorize invoking it.

The migration creates exactly schema parent and tables parent.child_profiles, parent.profile_revisions, and parent.command_receipts; no Core, BE1, Story, lesson, or ai_jobs DDL. Keep ParentPersistenceBase metadata separate. In the allowlisted backend/alembic/env.py change, append only ParentPersistenceBase.metadata to target_metadata and add only "parent" to _MANAGED_SCHEMAS; preserve all existing metadata and schemas. Use explicit migration operations; do not run autogenerate. Gate A must fail before context.run_migrations() if any identity, schema, version, or inventory condition differs. K3 remains unresolved and no existing revision is edited. Expected static graph after the new independent branch: 29 revisions, 13 raw heads, 10 dependency-resolved heads; these are source predictions only.

### 6.2 Gate A — owner-run Alembic migration (NOT LAUNCHED)

- Target only the same task database sketch2life_m2_s1a on the native PostgreSQL 17 instance at loopback port 5433; expected user postgres. Never connect to sketch2life or another database.
- Before any database connection or password prompt, the Gate A runner validates the approved pins and exact approval entry, verifies the ignored log root is writable, creates a unique run-id directory and exclusive preview/stdout/stderr/exit files, and stops if this preparation fails. It then performs one offline SQL preview with a no-credential placeholder value passed through S1A_P_ALEMBIC_DATABASE_URL; the preview is evidence only and must never be applied directly. The allowlisted backend/alembic/env.py change checks this variable before calling get_core_database_settings(): when present, it uses the value directly and bypasses both configured env_file paths; when absent, it preserves existing behavior for other migration commands. The owner inspects the complete preview; if the artifact is incomplete, contains unexpected DDL, or the owner declines, the runner stops without connecting. Only then does the owner enter the password through a hidden prompt. The runner constructs the DSN in memory and passes it only to the online Alembic child as S1A_P_ALEMBIC_DATABASE_URL; no DSN/password is printed, written to a file, or placed on the command line. The runner clears the variable from its own environment after the child exits. No .env read or fallback is permitted on this Gate A path.
- Read-only preflight verifies current_database(), host(inet_server_addr()), inet_server_port(), current_user, PostgreSQL major version, all schema/table row counts, public.alembic_version present and empty, and parent schema absent. Server IP is emitted as text via host(inet_server_addr()), never inet_server_addr()::text.
- Compare the pre-migration database-state projection with the pinned S1a-T artifact whose full file SHA-256 is 710F4A42FA817FA2EC27DC154BF6023F35FD51C012BBACA39782320357D8737E: compare `read_only`, sorted `table_rows`, sorted `marker_rows`, `marker_total`, `total_rows`, and `unmatched_tables`; exclude only capture field `run_id` and derived field `status`, while separately requiring `read_only=true` and `status=MARKER_COUNTS_MATCH`. Also require 117 tables, 29 rows, the exact 29 S1a-T marker rows, `public.alembic_version` present with zero rows, and no `parent` schema. Any state difference is a hard stop before Alembic. The full pinned artifact hash verifies which baseline file is being used; it is not compared to a newly captured file hash whose run metadata necessarily differs.
- After that one preflight, invoke exactly once backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini upgrade parent@head, through the Gate A script. Do not retry, stamp, upgrade other heads, or downgrade; the migration downgrade function is not invoked by this gate.
- A second read-only inventory must show exactly 120 tables and 30 rows: the original 117 tables and 29 rows unchanged, three empty Parent tables added, and exactly one `public.alembic_version` value `20261109_m2_parent_profiles` in the existing version table. Any other delta is a stop. Save this post-migration inventory as a new unique log artifact and report its SHA-256. Gate B must pin this complete artifact hash in a later approval addendum, then compare a deterministic state projection that excludes only the new capture `run_id` and derived `status` while comparing identity, all sorted per-table counts, marker counts, total, unmatched tables, and exact Alembic version values.
- The migration can be considered only after the owner sends the log. Codex reconciles the log, writes the Gate A closure record, and waits for explicit owner ACCEPTED. No Gate B launch is permitted before that.

### 6.3 Gate B — owner-run PostgreSQL route/persistence test (NOT LAUNCHED; BLOCKED ON GATE A)

- A separate approval addendum must pin the accepted Gate A post-migration inventory SHA-256 before Gate B. Until then the Gate B command is unusable.
- The runner creates the unique log directory and exclusive output files before any password prompt, verifies the same DB identity, and compares its read-only pre-run database-state projection with the projection in the pinned Gate A post-inventory artifact. Exclude only capture `run_id` and derived `status`; compare identity, every sorted table count, marker counts, total, unmatched tables, and exact Alembic version values. Require all three Parent tables empty, the original 29 S1a-T rows unchanged, and exactly the Parent revision row before invoking only `backend/tests/integration/test_m2_s1a_parent_postgres.py` once.
- The integration test uses one unique run id in the verified principal subject; generated UUIDs are not markers. It exercises (a) two concurrent identical POSTs with one key and one payload, returning the same original status/body and creating one profile/revision/receipt; (b) same-key/different-payload rejection with no extra writes; (c) owner GET; (d) missing-profile, non-owner, and same-subject/different-issuer GET and PATCH, each with the same 404 code/message and no mutation to any Parent table; (e) PATCH success and same-key replay; and (f) a valid stale-revision response and replay. Omission and explicit-null normalization/hash equality are also asserted in route/service contract tests. Replays and denied/rejected requests must not add rows except the single stored receipt for a valid idempotent terminal response as explicitly described in §4.4.
- Proposed final marker delta: parent.child_profiles 1 row, parent.profile_revisions 2 rows, parent.command_receipts 3 rows (successful create, successful patch, and the valid stale-revision command); total database rows 36 from the 30-row Gate A baseline, 120 tables, all other pre-existing table counts unchanged. This is an expected result, not observed evidence. The test must prove marker counts by exact principal/owner equality and joins; it must not use unescaped LIKE wildcards. No cleanup is performed.
| Test action | Allowed table effect | Marker and no-write assertion |
|---|---|---|
| Initial Parent POST succeeds | `parent.child_profiles` +1; `parent.profile_revisions` +1; `parent.command_receipts` +1 | Exact issuer/subject plus S1a-P run id in verified principal subject |
| Concurrent identical POST replay | No additional rows beyond the single successful POST | Same owner/run marker; assert one profile, one revision, one receipt |
| Same key with different payload | No table writes | Assert all three Parent table counts unchanged |
| Owner GET | No table writes | Assert all three Parent table counts unchanged |
| Missing, non-owner, or different-issuer GET/PATCH | No table writes, including no receipt | Assert all three Parent table counts unchanged and identical 404 code/message |
| POST with `synthetic_pilot_enabled=False` | No Parent table writes or receipt | Assert all three Parent table counts unchanged and the Parent error envelope returns 409 `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE` |
| PATCH succeeds | `parent.profile_revisions` +1; `parent.command_receipts` +1; `parent.child_profiles` row count unchanged (pointer/update only) | Join through the exact marked profile and match verified owner issuer/subject |
| Valid stale-revision PATCH | `parent.command_receipts` +1; no profile/revision write | Exact owner/run marker; assert profile pointer and revision count unchanged |
| Replay or invalid key reuse | Replay: no new rows; invalid reuse: no writes | Assert exact marker counts before/after |

- The official pytest summary is mandatory. If missing, record NOT RUN / NO VERDICT; do not infer pass counts from progress characters and do not retry. Any preflight mismatch, extra row/table, secret exposure, process termination uncertainty, or output safety finding stops the gate. The owner, not Codex, enters the password and runs the launcher.

## 7. Application composition and OpenAPI

- Add exactly the three SRS operations to the real classroom and combined application profiles; keep Parent routes out of the demo profile. Mount a Parent-specific router/runtime without changing global BE1 authorization policy or legacy route behavior.
- Reuse the existing `VerifiedPrincipal` type and the configured runtime identity verifier, but implement a Parent-only bearer dependency in the already planned new `parent_runtime.py`; do not call `get_verified_adult`, which maps all verifier rejections to `INVALID_IDENTITY_TOKEN`. The Parent dependency must preserve the existing missing-bearer handling and inspect only the typed preserved cause on `IdentityVerificationUnavailable`: the concrete Firebase Admin SDK expired-token exception type must be verified from the exact installed SDK package before implementation; that type maps to 401 `TOKEN_EXPIRED`. Every other token rejection or unknown cause maps to 401 `INVALID_TOKEN`; explicit verifier misconfiguration or missing SDK maps to 503 `IDENTITY_PROVIDER_UNAVAILABLE`. If the concrete type cannot be verified from the installed package source, stop before implementing the classifier and return for a new review/owner decision; never guess from exception text. In the already allowlisted `backend/tests/contract/test_parent_profiles_routes.py`, add an acceptance test that imports and raises an instance of that exact SDK type through the configured `FirebaseTokenVerifier` seam, verifies that it is preserved as `IdentityVerificationUnavailable.__cause__`, and asserts the Parent response is `TOKEN_EXPIRED`. Keep separate cases for an actual other token rejection (`INVALID_TOKEN`), verifier unavailability (`IDENTITY_PROVIDER_UNAVAILABLE`), and missing bearer (`AUTH_REQUIRED`). Do not inspect provider exception messages, log causes, edit the shared verifier, or change global BE1 behavior. Parent ownership remains issuer+subject. In Gate B, router, authentication dependency, service, repository, transaction and PostgreSQL remain real; only the Firebase token verifier is replaced.
- Update the allowlisted SRS OpenAPI projection text that currently says Parent profile operations are unavailable; add the three operations to the SRS projection and catalog. Use one Parent Profiles tag. Assert the exact allowed route set, no extra Parent operation, and counts relative to the pinned baseline: current source-derived baseline 128 runtime operations, 123 catalog-mounted operations, 110 paths, 18 runtime tags; expected after S1a-P is 131 runtime, 126 catalog-mounted, 112 paths, 19 runtime tags. The SRS projection is expected to add three operations and one tag. These are source-derived expectations, not test results. Recheck after S1a-T acceptance and during implementation; a mismatch is a stop, not an invitation to update counts without source evidence.
- Parent errors must use the SRS Rev57 §9.8 envelope with `code`, `message`, `correlation_id`, `retryable`, and the D-174 `request_id`; set request_id and correlation_id to the same safe request ID (generated when a supplied ID is absent or invalid) and set the corresponding response header. Include `retry_after_seconds` or `field_errors` when applicable under the SRS contract. The current global handlers in `app.py` are scoped to `/api/...`; add a Parent-prefix path in the existing allowlisted application/error composition without changing BE1 behavior, so `/v1/parent/profiles` never falls through to Starlette's `{"detail": ...}` body. Acceptance covers missing bearer → 401 `AUTH_REQUIRED`; invalid bearer → 401 `INVALID_TOKEN`; expired bearer → 401 `TOKEN_EXPIRED`; a synthetic create with `synthetic_pilot_enabled=False` → 409 `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE` with no Parent table writes or receipt; malformed or schema-invalid request → 400 `INVALID_REQUEST`; same-key/different-payload → 400 `INVALID_IDEMPOTENCY_KEY`; stale revision → 409 `STALE_REVISION`; and missing/non-owner/different-issuer GET and PATCH → identical 404 `PROFILE_NOT_FOUND` code/message/body shape. All errors include request_id/correlation_id. Assert stable fields, retryable type, and request ID presence/equality, not a fixed ID.

## 8. Static assumptions audit and marker plan

| Assumption | Static check / chosen control | Verification state |
|---|---|---|
| Server address text | Use host(inet_server_addr()); never parse CIDR text from inet_server_addr()::text. | Source-design check; runtime NOT RUN. |
| Database identity types | Use SQL text for database/user/host/version; port and counts as integers; UUIDs canonical lowercase-hyphen strings; timestamps UTC ISO-8601; bigint base-10; JSON booleans true/false; SQL NULL as JSON null. Gate scripts validate parsed Python types before comparing. | Static specification only. |
| Row markers | Marker lives in test principal subject. Count profile by exact (issuer,subject), revision by join to marked profile plus author subject, receipt by exact principal subject and run scope. Generated UUIDs carry no marker. Seed marker-bearing values where the code generates IDs; do not assume generated UUIDs contain a marker. Use equality; if LIKE is unavoidable, escape both underscore and percent as SQL wildcards. | Static specification only. |
| Windows output | Redirected logs are CRLF; the official-summary parser accepts LF or CRLF with the end anchor `\r?$`. | Script design; no log run. |
| Error envelope | `/v1` Parent paths need their own mapping in the allowlisted application composition because current global JSON handlers cover `/api/...`; include SRS §9.8 fields plus D-174 request_id, with request_id and correlation_id equal, and never fall through to Starlette `detail`. BE1 bodies include varying request_id; compare stable code/message. | Source/design check; route not run. |
| No dotenv or secret fallback | Parent test module disables `env_file` for both settings classes before construction, uses the dedicated test DB variable, and asserts dotenv disabled. On Gate A, `env.py` checks `S1A_P_ALEMBIC_DATABASE_URL` before calling `get_core_database_settings()`; if present it uses that value directly and bypasses configured `env_file`, while absence preserves existing migration behavior. The owner runner passes the dedicated value only to the Alembic child and clears it after exit. Never read `.env`; never print a URL/password. | Static design; no credential was entered. |
| Gate B synthetic flag | The PostgreSQL test constructs an explicit `Settings(env="test", synthetic_pilot_enabled=True, _env_file=None)` object and injects it through the app settings seam before app construction; assert the composed Parent runtime sees `env="test"` and `synthetic_pilot_enabled is True` before the first request. The disabled control injects `synthetic_pilot_enabled=False`, expects the Parent envelope response 409 `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE`, and asserts all three Parent table counts remain unchanged with no receipt. This is a test-local override only; do not read `.env` or change the production default. | Proposed test harness; PostgreSQL test not run. |
| Writable logs/cache/basetemp | The `tmp/M2_*` scratch location is not writable by the current Codex sandbox; pytest does not create basetemp parents. Each runner creates a fresh unique `.claude/handoff/logs/M2_S1A_P_20261109/<run-id>/` folder and all output files, plus the pytest basetemp child, before the first command. Use `-p no:cacheprovider`; Ruff uses `--no-cache`; mypy cache is explicitly under the writable unique log folder. | Prior sandbox write failure observed for a scratch-file attempt; no runner output folder created. |
| Quiet flag / official result | Do not add -q; backend/pyproject.toml already configures quiet output. A pytest invocation without the official final summary is NOT RUN / NO VERDICT. | Source/config check; tests not run. |
| One-run feasibility | Gate A order: validate pins/approval → create unique log folder and exclusive files → offline SQL preview once → owner inspects preview → hidden password prompt → read-only identity/pre-inventory → compare deterministic database-state projection to S1a-T inventory → one online `upgrade parent@head` → post-inventory with version values. Gate B order: validate pins/approval and accepted Gate A artifact hash → create unique log folder/files and basetemp → hidden password prompt → identity/pre-inventory projection comparison → one selected PostgreSQL test → post-inventory/marker projection comparison. No cleanup or retry. All file reservations happen before any command that can reach a database; a collision stops before execution. | Proposed only; both owner gates NOT LAUNCHED. |
| Secret scanner | Scan for connection-string context, full URLs, PGPASSWORD, password=, and long bearer-token patterns; do not flag bare substrings. Never print matching values. The current draft contains no DSN or password. | Draft-only inspection. |

## 9. Command ceiling after approval

No command in this table was run while drafting. Commands use cmd.exe /d /c; the approved offline runner writes stdout, stderr, and exit status to distinct files by direct file handles, no PowerShell pipeline and no overwrite. Each command runs only in a fresh unique folder. Omit any extra -q. All ceilings below are maximum invocations over S1a-P; a retry is allowed only when explicitly described and only for the affected command.

| Command | Stage / scope | Maximum | Result rule |
|---|---|---:|---|
| Offline pytest baseline | Before S1a-P source edits: existing age/profile/eligibility, BE1 fact-reader, app-composition, and OpenAPI catalog tests; fixture-dependent compatibility comparison uses the exact D-179-approved read-only R fixture; Parent composition assertions remain in scope | 1 | Use `-p no:cacheprovider`; official summary required; if absent, NOT RUN / NO VERDICT and stop. |
| Mypy strict baseline | Before source edits: backend/.venv/Scripts/python.exe -m mypy --strict src/sketch2life tests from backend/ | 1 | Record full diagnostics as baseline; exit 1 is not PASS. |
| Offline pytest after implementation | Parent unit/schema/service/static-migration tests, existing age/profile/eligibility/fact-reader regression tests, Parent route contract, app composition, OpenAPI catalog; fixture-dependent compatibility comparison uses the exact D-179-approved read-only R fixture; Parent composition assertions remain in scope | 2 total | Use `-p no:cacheprovider`; one initial invocation and at most one fix-driven rerun of affected tests; official summary mandatory. |
| Mypy strict after implementation | Same strict source/test scope as baseline | 2 total | Compare normalized diagnostics; no new S1a-P diagnostic. Exit 1 is never PASS. |
| Ruff | ruff check --no-cache over all edited/new Python paths | 2 total | Only the exact six D-176 I001 findings, unchanged in their original regions, are recorded as exit 1 / NO PASS / zero new diagnostics and do not block; any other/new finding blocks. |
| python tools/validate_harness.py | Repository root | 2 total | Must return a verdict; NOT RUN if no verdict. |
| python tools/validate_repository_security.py | Repository root | 2 total | Must return a verdict; no absolute local paths or secrets. |
| python tools/validate_architecture.py | Repository root | 2 total | Must return a verdict. |
| python tools/validate_skeleton.py | Repository root; required because new package structure is added | 2 total | Must return a verdict. |
| git diff --check | Repository root | 2 total | Report exact output and exit; baseline warnings remain distinguishable from new whitespace errors. |
| Offline Alembic SQL preview | Gate A, before any live connection or migration; artifact only, never applied | 1 | No credential or DB connection; owner inspects the complete SQL artifact and stops if unexpected. |
| Gate A owner-run script | One target-specific Parent migration and post-inventory | 1 | Owner only; see §6.2. |
| Gate B owner-run launcher | One named Parent PostgreSQL integration test and post-inventory | 1 | Owner only; only after accepted Gate A closure and a new approval addendum pinning its post-inventory. |

The initial offline command set and exact path selection are finalized in the reviewed launch instructions. Use `-p no:cacheprovider` for every pytest invocation; the unique run directory is explicitly created before pytest as its `--basetemp` parent, so pytest does not need to create that parent. The exact fixture-dependent compatibility comparison and Parent composition assertions are included under D-179; the fixture is pinned as R and no other FEAT-059 path is permitted. The offline runner is an allowlisted N path and must be statically reviewed before use. If an environment check has no verdict, do not switch shells, commands, or tooling to obtain a result. D-176 permits the coordinator to run a command once outside the sandbox if the sandbox cannot run it; record the actual runner and use a unique log folder, without exceeding the ceilings above.

## 10. Proposed run instructions and owner-only boundaries

### Gate A instruction (new N file; NOT LAUNCHED)

Do not run Gate A until a separate reviewed Gate A addendum has been appended after implementation and independent code review; that addendum must pin the actual Gate A script and its launch instruction by full SHA-256. The pre-implementation Task Approval pins the reviewed specification, existing inputs, and planned N paths only; it cannot truthfully pin absent script bytes. After checking both approval records, branch, HEAD, index, and pins, the owner starts the Gate A script

### Gate B instruction (new N file; NOT LAUNCHED / baseline pending)

Gate B is not executable until a separate reviewed Gate B addendum pins the actual Gate B launcher and launch instruction by full SHA-256, and pins the accepted Gate A post-migration inventory.

**Owner-only:** hidden password entry, Gate A migration, Gate B PostgreSQL test, decisions about accepting either gate’s evidence, and explicit phase ACCEPTED. **Coordinator/Claude may:** static source reconciliation, offline tests and validators after approval, spec review orchestration, report/closure writing after owner logs, and append-only governance updates only as authorized by the goal. Codex never enters a password or connects to PostgreSQL/Alembic/DB.

## 11. Independent review and approval flow

1. S1AP-Q1 is resolved by D-177 and reaffirmed by D-178; S1AP-Q2 and the M2 citation convention are resolved by D-179. The progress report records all three directions; this draft includes the PATCH normalization cases and exact fixture R input.
2. Open a fresh, cold, read-only independent session for each review round; no subagent. Review all source pins, every requirement/route/table/owner/test mapping, D-171–D-179, the explicit any-verified-principal self-create direction in D-156 R4, the proposed physical schema and receipt serialization, the graph, the offline SQL preview design, the two inventory gates and deterministic state projections, the exact allowlist including only the D-179-approved fixture as R, the `(M2)`/`(dev)` citation rule for duplicated identifiers, command ceilings, static-assumption audit, action-to-table-to-marker map, error envelope, and English language. Reviewer must distinguish source facts, owner-run evidence, proposal, inference and NOT VERIFIED.
3. Maximum five rounds. Stop and return to the owner if a finding repeats in consecutive rounds, P1/P2 count fails to fall after a round, or the reviewer proposes a scope/allowlist change.
4. Only a final READY or READY WITH NOTES with 0 P1 and 0 P2 permits an append-only M2 S1a-P Approval — ... entry APPROVED / NOT LAUNCHED. That initial entry pins the final reviewed specification, launch design/instructions that exist at that point, all current R/E/H inputs, governance pins, and each planned N path by repository-relative name; it must not invent hashes for scripts that do not yet exist and authorizes implementation plus only the approved offline commands, not an owner-run gate. After implementation and independent code review, append a separate reviewed Gate A execution addendum with the actual Gate A script and launch-instruction hashes before any Gate A run. After Gate A closure is accepted, append a separate reviewed Gate B execution addendum with the actual Gate B launcher and launch-instruction hashes plus the accepted post-migration inventory hash before any Gate B run. Each addendum remains APPROVED / NOT LAUNCHED until the owner executes its own gate. The initial approval entry must be the final heading matched by the Gate A script before Gate A launch.
5. After implementation, repeat the static audit, produce the action→table→marker map, run only approved commands, and obtain a fresh independent code review. Write `OWNER_CHECKLIST_S1A_P_GATE_A.md` and stop at Gate A; before the owner runs it, the reviewed Gate A addendum described in item 4 must pin the actual script and launch instruction. After Gate A logs, write the closure record and wait for explicit owner ACCEPTED. Only then prepare and independently review a separate Gate B addendum that pins the Gate B launcher, launch instruction, and accepted post-inventory hash.

## 12. Stop gates, NOT COVERED, and current state

Stop immediately if any pin/branch/HEAD/index differs; current source contains a changed route/table not in this exact allowlist; a new owner/product/permission/scope/authority cell appears; a command can connect to a live database before its owner gate; the runner cannot prove all preconditions before its single execution; output contains a secret/credential; the baseline inventory differs; the Alembic graph or count changes beyond the stated Parent branch; an unknown table/write is found; a pytest official summary is missing; a safety check has no verdict; or a reviewer reports P1/P2 that cannot be closed within the allowed rounds.

NOT COVERED: S1b grant/consent/share, age-band catalog and AC-65/NFR-38 completion, deletion lifecycle, context/support needs, list and search, Teacher/organization behavior, StoryRun/AI Jobs and receipt migration, cleanup/retention policy, real or legacy-unclassified profile creation, role resolver and admin-specific policies absent from the identity model, K3 repair, and any provider/Modal/network activity.

OWNER_MODAL_CALL_APPROVED=NO. This is DRAFT / NOT APPROVED / NOT LAUNCHED. No PostgreSQL, Alembic, launcher, Docker, test, validator, Ruff, mypy, Modal, provider, or network command was run in this drafting session. S1AP-Q1 is resolved by D-177/D-178 and S1AP-Q2 plus the citation convention are resolved by D-179. No other product, permission, scope, or authority cell was identified in the checked sources. Technical proposals remain subject to independent review and owner approval.

## 13. Owner question disposition

S1AP-Q1 was answered with option A in D-177 and reaffirmed in D-178. For PATCH, an omitted nullable `interests_summary` is normalized to JSON null, exactly like explicit null. PATCH remains the next full snapshot; revision hashing uses the normalized canonical payload. Paired acceptance cases must show both forms produce the same normalized payload and `revision_hash` when all other values match. No database schema change is made. S1AP-Q2 is resolved by D-179 option A; no owner scope question remains identified in this draft.

## 14. Draft change record

| Change | Draft 4 treatment | Draft 5 treatment |
|---|---|---|
| Owner decision | D-171–D-179; PATCH option A in D-177/D-178 and S1AP-Q2 option A plus citation convention in D-179 | PATCH normalization cases and the exact read-only fixture disposition are explicit |
| Principal authority | Any verified principal stated without reconciliation to the SRS actor label | Explicitly follows D-156 R4 self-create direction; profile ownership binds verified issuer and subject |
| Current-revision FK | Deferred composite FK described without DDL creation order | Create both tables first, then add named DEFERRABLE INITIALLY DEFERRED composite FK; drop constraint before tables |
| Receipt integrity | 32-byte lengths described, transaction boundary and concurrency case omitted | Named 32-byte CHECKs, atomic mutation-plus-receipt transaction, same-key concurrent replay case |
| Gate inventory | Compared full artifact/hash while each run has distinct capture metadata | Pin full artifact; compare a deterministic state projection while separately validating capture metadata and exact version values |
| PostgreSQL acceptance | GET authorization cases; no explicit denied-PATCH no-mutation coverage | Missing/non-owner/different-issuer GET and PATCH share 404 shape; all denied paths assert no Parent table writes |
| Composition / error contract | `/v1` could fall through API handlers; compatibility fixture not represented in allowlist | Parent error envelope mapping specified; D-179 approves only the exact baseline fixture as R and keeps the compatibility comparison in scope |
| Test execution | Pytest cache provider not disabled | Every pytest command uses `-p no:cacheprovider`; run folder and basetemp are reserved first |
| OpenAPI projection | Route additions planned; stale “Parent unavailable” projection text not called out | Projection text update and catalog assertion required |
| Pins / audit | Pins reflect the Draft 4 snapshot; NOTES pin had become stale after prior append | DECISIONS, progress, and working-note pins refreshed to actual file hashes; all other Draft 4 path pins rechecked |
| Review status | Draft 4 independent review NEEDS_REVISION | Drafts 5 and 6 remain historical; Draft 6 review NEEDS_REVISION; Draft 7 remains DRAFT / NOT APPROVED / NOT LAUNCHED pending a fresh cold review |



## 15. Draft 5 to Draft 6 correction and review state

Draft 5 is preserved unchanged. The owner-requested continuation extended `tmp/m2-progress/NOTES_S1A_P.md` after Draft 5 was prepared, so its R-mode hash in Draft 5 no longer matched the current note. Draft 6 refreshes that single allowlist pin to `5491C90283D4BE8A557430CD88AB0B69A1B86214E99ABD5704A1A1E566C5835B`. A static audit of Draft 5's 117 allowlist entries found exactly one mismatch (the note pin); the other 116 entries matched. The pre-D-179 Draft 6 audit found 117 unique paths matching, comprising 83 R, 9 E, 2 H, and 23 N entries; this count is superseded by the D-179 reconciliation in §16.

The earlier independent Draft 5 review session received an owner stop request before returning a verdict. No Draft 5 review verdict exists. Draft 6 then remained DRAFT / NOT APPROVED / NOT LAUNCHED and received a fresh cold independent review; its NEEDS_REVISION result and the resulting Draft 7 corrections are recorded in §17. Draft 7 still requires a fresh cold independent review and separate owner approval; D-179 does not authorize implementation or database operations.

D-179 resolves the decision-reference convention: future M2 documents must label any duplicated D-135 through D-149 citation explicitly as `(M2)` or `(dev)`. Draft 6 does not infer lineage or rewrite either historical block.

## 16. D-179 reconciliation and current review state

D-179 resolves S1AP-Q2 with option A: the exact FEAT-059 `baseline_routes.json` file is an R-only input pinned in §5. The fixture-dependent legacy compatibility comparison and Parent composition assertions remain in scope. No other FEAT-059 path is permitted, and the fixture itself is not editable. D-179 also resolves M2-AUTH-Q1: future M2 citations of duplicated D-135 through D-149 identifiers must use explicit `(M2)` or `(dev)` lineage labels; do not infer lineage or rewrite history. This supersedes the earlier default described in Goal v2 §2 for duplicated identifiers.

The current §5 pins use DECISIONS.md SHA-256 `4F34316C7F5E7872DDDB1B8D9E0768544BB3C1F4E33DE789F68BA6A44A96A19C` and the progress report SHA-256 `9B4B2FCF43F0AAD359412B192794A6C04A3974ECBAD55856BBD67DA4839948B8`. The current allowlist contains 118 unique paths: 84 R, 9 E, 2 H, and 23 N. The 117-path count in §15 describes the pre-D-179 audit and is historical.

S1AP-Q1 and S1AP-Q2 are resolved; no remaining product, permission, scope or authority question was identified in the checked sources. Draft 6 received a NEEDS_REVISION review; Draft 7 makes the technical corrections in §17 and remains DRAFT / NOT APPROVED / NOT LAUNCHED until a fresh cold independent review returns READY or READY WITH NOTES with 0 P1 and 0 P2 and the owner records a separate approval. D-179 does not authorize implementation, migration, database work, or any phase. `OWNER_MODAL_CALL_APPROVED=NO`; S1b remains DEFERRED and S2, S3, M3-M6 remain closed pending their own approvals.

## 17. Draft 6 independent review and Draft 7 corrections

The fresh cold review of Draft 6 (SHA-256 `8010C64FFEC0FBD4389489C40ABD7763A50B40D5EC969620738BD011B8569F7F`) returned **NEEDS_REVISION — 0 P1, 4 P2, 1 P3**. The bridge response did not expose a reviewer session ID. The corrections below are technical proposals within the existing allowlist; they add no route, table, permission, phase, or allowlist path.

| Finding | Draft 7 correction |
|---|---|
| P2: the pre-implementation approval required hashes for Gate A/B scripts that are absent N paths | The initial approval now pins the reviewed spec, existing inputs, governance, and planned N paths by name. Actual script and launch-instruction hashes are deferred to separate independently reviewed Gate A and Gate B addenda before their respective owner-run gates. |
| P2: D-171's 121–155-month legacy StoryRun exclusion lacked a service/contract acceptance mapping | The S2 precondition names `StoryRunLiteService.create_run` and its trusted profile lookup as the application-service boundary; the later S2 approval must require rejection before run persistence and a no-run assertion. S1a-P remains limited to Parent profile foundation. |
| P2: the existing shared verifier path cannot distinguish `TOKEN_EXPIRED` from `INVALID_TOKEN` | A Parent-only dependency in the already planned N path `parent_runtime.py` uses the same configured verifier and classifies only the typed preserved expiry cause. It maps expiry and other rejection separately without changing shared BE1 authentication; tests cover both outcomes. No allowlist change is proposed. |
| P2: delegated schema objects lacked stable names | Section 4.5 now names every proposed primary/unique/check constraint, foreign key, index, trigger, and trigger function. |
| P3: Gate B did not specify enabling `synthetic_pilot_enabled` | The static audit now specifies an explicit test-local `Settings` override, injection before app construction, assertions on the composed Parent runtime, and a disabled-flag control, with dotenv disabled. |

The exact allowlist, source pins, branch, HEAD, and owner decisions remain unchanged. This record does not approve S1a-P or authorize implementation, a database operation, or either owner-run gate. `OWNER_MODAL_CALL_APPROVED=NO`; S1b remains DEFERRED and S2, S3, M3-M6 remain closed.

## 18. Draft 7 independent review R2 and Draft 8 corrections

A fresh cold, read-only review of Draft 7 (SHA-256 `1B0F38BA6C849FA1F6EF9FF29A14E3894E37C32A0AEA2E12D10602230ABD0B76`) returned **NEEDS_REVISION — 0 P1, 2 P2, 2 P3**. The review thread was `01a1c0e2-598c-77f2-b8c1-639f6536cd5b`; the reviewer reported its session identifier as unavailable. No review edits or commands that execute tests, validators, type checks, Alembic, a database, Docker, a launcher, Modal, a provider, or network operations occurred.

| Finding | Draft 8 disposition |
|---|---|
| P2: SQL string constants were unquoted in the proposed `state` default and `data_origin` CHECK | Draft 8 quotes `ACTIVE` and `SYNTHETIC_DEV` as SQL string literals, including the stable-name table description. |
| P2: the concrete Firebase Admin SDK expired-token exception class was not verifiable from available local package source | Draft 8 does not present the class name as an established fact. Before implementation, the installed package source must identify the concrete type; otherwise stop before implementing the classifier. The already allowlisted route-contract test must use an instance of that exact installed SDK type through the existing verifier seam, assert preserved `__cause__` and `TOKEN_EXPIRED`, and keep invalid-token, unavailable, and missing-bearer cases distinct. The source/type remains NOT VERIFIED in this drafting session. |
| P3: disabled synthetic-gate case was absent from the action-to-table-to-marker map | Draft 8 adds the disabled-flag action with expected 409 `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE`, no Parent writes, no receipt, and unchanged Parent counts. |
| P3: full downgrade object order was not specified | Draft 8 states reverse dependency order for receipts, trigger, function, composite FK, revisions, child profiles, and schema. It does not authorize running downgrade. |

The review also marked the five Draft 6 corrections as PASS/PARTIAL and confirmed the 118-path allowlist and all source pins. Draft 8 remains **DRAFT / NOT APPROVED / NOT LAUNCHED** pending a fresh cold independent review. No allowlist path, route, table, permission, phase, owner decision, or database action is added by these corrections. `OWNER_MODAL_CALL_APPROVED=NO`; S1b remains DEFERRED and S2, S3, M3-M6 remain closed.

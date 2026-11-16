# M2 S1a-T — Teacher / organization foundation — Final specification for owner approval R2

**Status: SPEC — NOT APPROVED, NOT LAUNCHED.** This is a complete approval specification for owner review, not permission to edit code, run commands, or write to a database.

**Owner decision record:** D-156, D-157 and D-158 are direction decisions; D-159 authorizes only the document revisions and staged approval recording described there. None of these records themselves approves execution. This specification records them without creating any additional product decision.

**Review basis:** S1a-T Draft 4 SHA-256 0EF6E6D43F2ABF1A5DDA1A67FAC33200F7D700F4CD068FF6F3DE37E3298FFCFC. Independent Draft 4 review: DRAFT_READY_FOR_OWNER_REVIEW, 0 P1 / 0 P2 / 1 P3. The P3 is wording-only and must be stated in the approval record: “31 pins: 30 source/test and 1 read-only tool”; backend/tools/be1_api_smoke.py is read-only scope inspection, not an edit or acceptance test. This R2 incorporates D-159 B3–B5 for fail-closed table inventory, missing-summary handling, and timeout termination; it does not authorize execution.

## 1. Baseline, sources, and database boundary

| Input | Pin / record |
|---|---|
| Branch / HEAD / index | feature/feat063-be-foundation / dd70685eae58aaaefea3e567f5c23d09345a8513 / empty at specification time |
| S1a-T Draft 4 | 0EF6E6D43F2ABF1A5DDA1A67FAC33200F7D700F4CD068FF6F3DE37E3298FFCFC |
| S1a-P Draft 1 | 2875C0A5F25657BDCE2645CF2733FA0B5E52E4EE9EF9544C19C6AAA697400C58 |
| M2 Draft 10 / Draft 11 | 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1 / 6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68 |
| SRS v2.3-draft / DTR v2.3 working tree | DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC / 3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22 |
| DTR LF Git blob | 201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2 |
| S0-doc evidence | 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001; closed at documentation scope under D-150 |
| DECISIONS.md with D-158 and D-159 | 07A663A5FFC4A8672C274949B5E58FC31688EDFE05FDEF57519A9791C406B7A0 |
| S0-owner-run inventory | .claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json; SHA-256 E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F |
| Baseline approval specification | M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md; SHA-256 A671DBD85B9622CB754C5CECB807BBBBA2C920CD76F0A22ABBA44F4A12DC1A18 |
| Baseline owner launch instruction R2 | M2_BASELINE_LAUNCH_INSTRUCTION_20261107_R2.md; SHA-256 C132EF91AD7C06A82EB27D09D82B0662E77CDD795B9BC2F935B281822EAA9178 |
| S1a-T owner launcher R2 | evidence/scripts/m2_s1a_t_owner_run_20261107_r2.py; SHA-256 47634E80952FA8369820E60B7349FE1713CF274B6E028F0CAC5F40E146661B1D |

D-154 is an owner-run read-only inventory on sketch2life, PostgreSQL 17.11 native localhost port 5433: 117 tables, 82 rows total, 9 public.alembic_version rows. K3 failed; K4 source comparison, K5 synthetic-only proof and K7 mypy were NOT RUN. These are historical owner-run facts, not authorization to write to the main database.

Owner reported sketch2life_m2_s1a was created from a schema-only dump, PostgreSQL 17 native localhost:5433, user postgres, 117 tables, zero rows and empty alembic_version at creation. This session did not connect to or independently verify the DB or dump. Current state must be checked by the owner at launch.

D-156 R1 requires S1a-T first, then S1a-P on the same task DB, sequentially. Recompute inventory and mypy baseline between phases. Do not run T and P in parallel. Never write, migrate, restore, drop, truncate, or clean up sketch2life. S1a-T uses only sketch2life_m2_s1a. No Alembic migration is in T.

## 2. Approved direction recorded for this specification

### 2.1. Routes and legacy behavior

Keep prefix /api/be1/v1. S1a-T covers these three operations:

| Operation | Route |
|---|---|
| Create class | POST /api/be1/v1/organizations/{organization_id}/classes |
| Assign one Teacher | POST /api/be1/v1/classes/{class_id}/assignments |
| Create Teacher profile/enrollment | POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles |

The assignment route derives organization from the server-side class. Actor must be school_admin for that organization. Its request body contains only subject (string length 1–256); client does not send role or class_id. Response is HTTP 201, contract Be1AdultAssignmentV1, with assignment_id, subject, role=teacher, class_id and active=true. Preserve AdultIdentity upsert and HTTP 409 IDENTITY_ISSUER_MISMATCH.

The existing organization-scoped assignment POST and DELETE routes are removed from the router and OpenAPI catalogue. Do not retain blocked stubs or writable aliases. Replacing/removing a Teacher has no route and remains debt. O1 consequences include removing those two operations, adding the class-scoped POST, and updating OpenAPI catalog and route-count tests.

### 2.2. Teacher cardinality, authorization, and denials

- Count only active rows with the exact class_id and role teacher. The new endpoint cannot create class_id NULL organization-wide assignments or roles other than teacher. A class may have zero active Teachers.
- Lock the classroom row and count/create in the same transaction. A second active Teacher returns HTTP 409, code CLASS_TEACHER_EXISTS, message “Class already has an active Teacher”; response must not disclose the existing person. No BE1 migration or new unique constraint.
- The Teacher-profile route requires an active class-level Teacher assignment for that exact class. An organization-wide assignment is insufficient. school_admin is denied on this route.
- For M2 routes only, missing class, class in another organization, or no assignment returns indistinguishable HTTP 403 with code SCOPE_DENIED and message “Access to this resource is not permitted”. Do not alter global authorize_adult or legacy BE1 policy.
- Record audit metadata only; no row values, child content, token or consent evidence. Test Firebase verification through app.state.be1_runtime.identity_verifier only; send normal Bearer header. Do not override the authorization dependency. Runtime identity, routing, assignment lookup, authorization, transaction and DB remain real.
- Unsupported Platform Admin, Operator and content-admin role tests are NOT RUN because the identity model does not represent those roles. Do not claim them as covered. Add an IDOR test for the Parent phase only; Parent routes are outside T.

### 2.3. Synthetic profile, age, and test-row rules

- Teacher profile creation stores only SYNTHETIC_DEV, with consent_id and consent_purpose_ref NULL. REAL and LEGACY_UNCLASSIFIED creation remain blocked. HTTP creation is permitted only when settings.env is local or test and synthetic_pilot_enabled is enabled; otherwise fail closed.
- API returns SYNTHETIC_DEV exactly as stored; document mapping to SRS SYNTHETIC_TEST without changing the enum.
- Server issues child_id as synthetic- plus secrets.token_hex(12), within the current 128-character DB column. Client does not send child_id. The same generated ID is used for profile, enrollment, audit linkage and response. display_name begins “Synthetic ” and age_source is SYNTHETIC_FIXTURE.
- For new values, shared validate_age_months and the request schema enforce 36–120. Preserve existing rows; do not clamp or rewrite 121–155. Existing BE1 database CHECK 36–155 remains unchanged. Every Teacher profile route uses the same source; do not use child_age.py.
- Before code, classify every caller of shared validate_age_months and preserve reads of existing 121–155 values. If a shared change rejects a stored-row read or alters an unrelated contract, stop for a separate owner decision. Explicit regression cases include test_assistance_domain.py, test_vision_analysis_service.py, test_vision_analysis_review_fixes.py, test_vision_context_domain.py, test_assistance_service.py, test_be1_fact_reader.py and test_vision_context_service.py. Do not change the separate learning-content 155 boundary or fixture bands without an approved amendment.
- Test-created rows use one UUID-hex run ID generated by the guarded launcher. Use these exact markers: organization IDs `synthetic-s1at-{run_id}-org...`, class IDs `synthetic-s1at-{run_id}-class...`, adult subject IDs `synthetic-s1at-{run_id}-teacher...`, profile `display_name` prefix `Synthetic S1AT {run_id} `, and proof `run_ref=s1at-run-{run_id}`. Since child_id is constrained by O4 to `synthetic-` plus `token_hex(12)`, link it to the run through the marked display name, not by changing its ID format. Before pytest, R2 counts every non-system ordinary/partitioned table in one `BEGIN READ ONLY` transaction and records a per-table total; any row anywhere stops before pytest. After pytest, R2 records per-table totals and the exact marker count for each supported marker table (enrollments through marked profiles). It never selects row values. A missing official summary writes exactly `NOT RUN: no official pytest summary` and causes no post-run database connection. If a non-marker table has rows, any per-table total differs from its marker count, or total rows differ from total marker rows, record `UNKNOWN_ROWS_FOUND`, do not pass and do not clean up. Preserve all rows. Because no cleanup is authorized, the launcher is single-use until the owner separately decides how created rows may be handled.
- Revise only the explicitly allowlisted invariants and named pending-consent test. Preserve legal-consent denials on consent-bound paths and generic invariant that synthetic data cannot carry effective legal consent.

### 2.4. OpenAPI, safety seam, and exact counts

- Baseline counts: 129 runtime operations / 124 mounted catalog operations / 111 paths / 18 tags. After removing two legacy operations and adding one class-scoped operation, expected counts are 128 / 123 / 110 / 18. Any different count is a stop gate.
- Owner selected seam A for test_app_composition.py and test_openapi_contract_catalog.py: process-level SKETCH2LIFE_ENV=test, STORYRUN_LITE_MAIN_DEMO_ENABLED=0, and a non-secret placeholder target on a closed loopback port. Process environment must override dotenv fallback. Source review says create_app creates an SQLAlchemy engine/session factory but does not explicitly connect during initialization; the main demo lifespan is not attached when the flag is 0. These two modules are after-only and have no pre-code baseline.
- Stop if either test attempts a connection to the placeholder. Do not switch to a live DB seam or dependency overrides. No .env content may be read.

## 3. Test, command, and data ceilings

- Pre-code offline pytest baseline is the separate Baseline Approval specification, one use only. It includes the 11 modules there; preserve failures as baseline facts.
- Post-code offline pytest, cwd backend, executable .venv/Scripts/python.exe, one invocation, max 1800 seconds: the same 11 modules, plus test_m2_s1a_teacher_service.py and test_m2_s1a_teacher_routes.py. In test_synthetic_eligibility.py, exclude only test_head_counts_by_both_methods_match_the_derived_expectation; it is NOT RUN, not PASS.
- Post-code composition/OpenAPI pytest, cwd backend, executable .venv/Scripts/python.exe, one invocation, max 1800 seconds: test_app_composition.py and test_openapi_contract_catalog.py, only under seam A, after code.
- PostgreSQL acceptance, cwd backend, executable .venv/Scripts/python.exe, one invocation, max 1800 seconds, only test_m2_s1a_teacher_postgres.py through the owner launcher. Dedicated S1A_T_TEST_DATABASE_URL; fixture sets SKETCH2LIFE_DATABASE_URL from it, clears cached factories and verifies identity using app.state.be1_runtime.engine before any write: current_database sketch2life_m2_s1a; current_user postgres; server port 5433; server address loopback; server major 17. A separate launcher guard is supplementary, not a substitute for the real app-engine guard.
- Before pytest, the R2 launcher records counts for every non-system table in a read-only transaction and stops if any table has rows. After pytest, it connects for post-inventory only when an official pytest summary exists. If no summary exists, it records exactly `NOT RUN: no official pytest summary`, makes no post-run DB connection and exits 2. A timeout is inventory-eligible only after the termination rule in §6 is satisfied and an official summary exists; timeout never passes.
- Post-code strict mypy, cwd backend, .venv/Scripts/mypy.exe, one package invocation, --no-incremental, new cache under ../tmp/M2_S1A_T_20261107/mypy-cache, max 900 seconds.
- Ruff, cwd backend, .venv/Scripts/ruff.exe, one check --select E,F,I,UP,B,SIM on exact approved paths, max 300 seconds; no format/autofix.
- Each of validate_harness.py, validate_repository_security.py, validate_architecture.py and git diff --check runs once, max 300 seconds. No validate_skeleton.py unless a separately approved structure change exists.
- Every command uses cmd.exe /d /c from stated cwd, executable and paths relative to cwd, direct stdout/stderr redirection into separate files, separate exit record immediately afterward. No PowerShell pipeline, Tee-Object or transcript. Logs: ../.claude/handoff/logs/M2_S1A_T_20261107/ from backend; .claude/handoff/logs/M2_S1A_T_20261107/ from repo root. Basetemp/cache only under ../tmp/M2_S1A_T_20261107/. Create both only if absent and ignored; stop rather than delete/reuse.
- No command result is implied by this specification. Setup error, missing summary, missing safety verdict, timeout, interruption or secret/URI in output means no verdict / NOT RUN, not PASS. No retry or changed selection.

## 4. K4 and acceptance

Before implementation, K4 is source-only reconciliation of D-154 inventory vs BE1/core models, routers, application policy, migration source and test expectations. Record owner-reported facts, source facts, inference and unknown separately. Do not infer live Alembic graph from source. K3 mismatch between 20261103_story_upload_compat and 20261104_story_revisions stays unresolved. Any BE1/Core/Story DDL or path outside allowlist is a hard stop.

| M2-AT | T applicability |
|---|---|
| 01 | assignment authorization, missing/revoked assignment, metadata-only audit; only role-denial cases represented in current identity model |
| 02 | server-derived organization/class scope; class-level assignment required |
| 03 | new synthetic profile accepts 36 and 120; rejects 35 and 121; no child_age.py |
| 04A | one active Teacher/class and race serialization; zero allowed; second gets 409 CLASS_TEACHER_EXISTS without identity disclosure; PARTIAL: capacity and CLASS_CAPACITY_REACHED NOT COVERED |
| 04B | atomic profile/enrollment; school_admin denied; server ID reaches existing portfolio lookup and returns 409 CONSENT_NOT_EFFECTIVE rather than 404 PROFILE_NOT_FOUND without child data; PARTIAL: expected class revision NOT COVERED |
| 10 | service/contract/persistence age projection only; no StoryRun; existing 121–155 rows not clamped |
| 11 | SYNTHETIC_DEV, NULL consent refs, synthetic markers and environment/flag gate; REAL and LEGACY_UNCLASSIFIED blocked |

AT-01/02/03/11 apply; AT-04A/04B/10 are PARTIAL as above. AT-05..09 are NOT RUN because S1b is deferred. StoryRun, profile read isolation, capacity, idempotency key, expected class revision and assignment revision in response are NOT COVERED, not PASS.

## 5. Exact allowlists and pre-change SHA-256

The 76 unique paths below are exactly the union of Draft 4 §§6.1–6.3. Modes: R=read-only; H=historical read-only; E=existing edit candidate; N=new path candidate, absent now. A path marked R/E is both readable and in the edit allowlist. A final approval and implementation must recheck all existing hashes before edits. New candidates are not created by this specification.

| Mode | Repo-relative path | SHA-256 or state |
|---|---|---|
| R | .claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json | E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F |
| R | backend/alembic/env.py | FABE5736CC7A49CC3C3D36112B4780248113DEEA3DE9A3DA4D2C2CB85E937447 |
| R | backend/alembic/versions/20261103_story_upload_compat.py | F16346F5D0D320B22AF0767F387FE066ED3683D57DDD380804424B5A837CA166 |
| R | backend/alembic/versions/20261104_story_revisions.py | 3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8 |
| R | backend/src/sketch2life/application/ports/identity.py | 1065A42D44766BE16103AA463E2243DC2FF4EF8AA2A793FDF3F3A8944BA80E47 |
| R | backend/src/sketch2life/application/services/be1_runtime.py | BD1D57B2E69ABB71F6FB933BF66CC499F36CA8F79D1FE03F6CE99FFD6AEBC3E4 |
| R | backend/src/sketch2life/application/services/vision_analysis.py | 1BCFB18F07613EF3377D34EE85091FD349EB502178F0A04F8B511A2A969E48C1 |
| E | backend/src/sketch2life/contracts/schemas/be1_runtime.py | 59A2CA1A356916816A788C77E4B03D4FA1A716ECF5CC245B515A39E146B14F11 |
| R | backend/src/sketch2life/domain/assistance.py | 1AF5211FB97C2E2175A673EC9E6A79D531187D2026DF8A53395CFD346F0A8488 |
| R | backend/src/sketch2life/domain/child_age.py | C4A1288A41D6EC52087A9BB83F7F8590D1084C367A41BD512D65ACA917A2838C |
| R/E | backend/src/sketch2life/domain/core_foundation.py | FFC7B8BBAA1AF2CB0D63479AAA598B74AFD1B4FB4DD58088A5706235A16C19B3 |
| R | backend/src/sketch2life/domain/vision_context.py | 9501F2194A2896DF121C50AF2A1DF29B7003C7F2029AF0FEBD461664886E04EB |
| R | backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py | 348E18B395A35DF0D05EC8E1DCB56F8ECBDF64C7F181250A2C3F132CA53A535E |
| R | backend/src/sketch2life/infrastructure/config/settings.py | DB1A5FB6E4F7C800F00B4AD1F9386D20AEE7F41DBD35BA54C7F13426D7CDD387 |
| R | backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py | 0B2DEF14F43F80C311F4D0DBC71DD29F90C2E1FC0BA6032DB20B999CAE8287FD |
| R | backend/src/sketch2life/infrastructure/persistence/be1_models.py | 6859CC8313482C70828176B4E12209B485B7D582C6831340AE0D451659219C1E |
| R | backend/src/sketch2life/infrastructure/persistence/core_models.py | 47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A |
| R | backend/src/sketch2life/infrastructure/persistence/core_store.py | AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94 |
| R | backend/src/sketch2life/infrastructure/persistence/database.py | C37F51CE9BE25C66F98065A68516E549E94B99219FF24CF846BE1755616194FF |
| R | backend/src/sketch2life/interfaces/http/app.py | D9DCBDC5BF3B71840C98BEB50A80D5A7BC1D800C3F93FFBB05DD021E99A995C0 |
| R | backend/src/sketch2life/interfaces/http/be1_runtime.py | 62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85 |
| E | backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py | C23BC0C8E9BE6E1989DCDA656588D498F67789EC65D0FE4967C2A64B5E0A2EFC |
| E | backend/src/sketch2life/interfaces/http/openapi_contract.py | 2A5A5DAB4B2CFAECC4F30099E1CD2D862DEBC9CFCE066D623C7CE441C5E7AA81 |
| E | backend/src/sketch2life/interfaces/http/openapi_srs_v22.py | 2D07A5D299FFBBA5264247A107065044DE215C156DC50C1431949FFAF3285B11 |
| R | backend/src/sketch2life/interfaces/http/router_composition.py | E06A158B3616583DF8ABBA21D52C62E769AFA6A9E7C75359D28D424AB15849CC |
| R | backend/src/sketch2life/interfaces/http/routers/be1_common.py | 40DDE6F9B2AC91A78FE2A2F65B15EFCB1B76D132D49BB5580338710B12B9C45C |
| R | backend/src/sketch2life/interfaces/http/routers/be1_records.py | 05A9EB9A1C1E732EB3801213798A3DEE74B96E52517545513B42886DA392D9CF |
| E | backend/src/sketch2life/interfaces/http/routers/be1_registry.py | ACB51CA040306198BA5B95F77091717BB73797E80BBA28CDE8C1DB14D97C8A54 |
| R/E | backend/tests/contract/test_app_composition.py | 2E6E9DD2E7C915F4E43EB3E0CB4682FDE6FF848D31F8714EFC7C59D9F4A1D49A |
| E | backend/tests/contract/test_be1_synthetic_pilot.py | 03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611 |
| R | backend/tests/contract/test_learning_content_commands.py | B04D8DF57E81984F219D354A7308F552259E355B602A14E7D516A0BCAB98CAF9 |
| N | backend/tests/contract/test_m2_s1a_teacher_routes.py | không tồn tại |
| R/E | backend/tests/contract/test_openapi_contract_catalog.py | 401952E5588C96415B2D275565137C1D4D0A2B795056D39A2B0E962C326B6C40 |
| R/E | backend/tests/integration/test_be1_postgres_api.py | 49F14546F4A3B6684466CAF7215CE35466548E90AF11E5F1604BE4C343033E0E |
| N | backend/tests/integration/test_m2_s1a_teacher_postgres.py | không tồn tại |
| E | backend/tests/unit/test_age_provenance_columns.py | DE1B745B83AE490C4ACAD8F1D457B3CF1E16420B06F79B19DDFF3576BE778C97 |
| R | backend/tests/unit/test_ai_policy_persistence_shape.py | D24CB7F94FFDD7BBE6DA70CCCE10000A4CD22985CC1DE41FA673DA466B24E8CA |
| R/E | backend/tests/unit/test_assistance_domain.py | AFABE3545E47EAB5101551B1642855143D71E9FD910DA0BA8F213A9B78A89DC8 |
| R/E | backend/tests/unit/test_assistance_service.py | A40BF516BD7232F7E641EF0168764F7B61ADE0E0A895C0A7B03A74B60ABFDAAC |
| R/E | backend/tests/unit/test_be1_fact_reader.py | F234E7056F0FAFD0479519AB419271E3EE19552E1AF55A17E5A09CD387F5F815 |
| N | backend/tests/unit/test_m2_s1a_teacher_service.py | không tồn tại |
| R | backend/tests/unit/test_profile_age_invariant.py | B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB |
| R | backend/tests/unit/test_synthetic_eligibility.py | B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1 |
| R | backend/tests/unit/test_t2c_digest_pin.py | E1AE9A2B3E32E30DA7348A873D1A318DDAEF6AE2AC3F9345D05790FD0968D4E7 |
| R/E | backend/tests/unit/test_vision_analysis_review_fixes.py | CC3F777F2C7D48733B9C2444FC0DC3D496FC8D914A0DF4469DAE2EABB54EBD3D |
| R/E | backend/tests/unit/test_vision_analysis_service.py | D5B5A3F23A69B6CFD8079EBF57A6BDE85AC0CBB7699A586C03B14789FC8C8CDD |
| R/E | backend/tests/unit/test_vision_context_domain.py | 4A457F16A74C0CEEA9C2C53BB85174C7D2067C2113E80558E79266F234E43F96 |
| R/E | backend/tests/unit/test_vision_context_service.py | E7E9BAAC7D54C42F45F7F56E9D8A99942290EEAB7F15620DE1B3911666D78348 |
| H | features/FEAT-047-be1-runtime-backend/artifacts/API_CONTRACT.md | DAB6A73D041B41D31EC4D5A7599BABBAB9B3EA1F25DDDCCF01470CE3F0815994 |
| H | features/FEAT-047-be1-runtime-backend/artifacts/API_MAP.md | 128BA8EFF4437CDB7D1D3E5EF77440EEF87C67926B613DBA4CE4DEEE8152A693 |
| H | features/FEAT-047-be1-runtime-backend/artifacts/openapi-v1.json | 55ED7B231B28FAF1F5A30345DE279E7E0CD05A94DFC739DCC41006A52ADA3349 |
| H | features/FEAT-058-review2-document-package/evidence/metrics/be2_route_inventory.json | 4CC2F900AE1054C527E893F31EA4FE9735845EA9E7C9E79637797584E79C77D6 |
| H | features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json | A0CB85E214E80BED8EE9AEEF665CC9979F579553BD9117D0D8D682DF641AD8F5 |
| H | features/FEAT-060-classroom-integration-and-review-remediation/evidence/notes/SRS_STAGE_API_TRACEABILITY_20261023.md | 449A054E25AAF254512DA68783231066776F40B932B5AB8718ADCF9D63360985 |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/API_INVENTORY_FEAT063_REV31_20261028.md | 985BFE1625E1C1A7A80BBFB4AF8A6E673787243ADAC7291EAB0CE3AF90AB8E81 |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md | E65582C197FCF9DC134294D140B5289C44B82E6A81AC6DB6C23C0AFE3800A881 |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/API_COVERAGE.csv | 30D9B0D0D4B51014CA71DD27D1999A5AB23E9AA5EDE190043E0F3BB2CE4E2D84 |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/organizations-classes/004-create-assignment-api-be1-v1-organizations-organization-id.bru | 3E6E9C432C9911214FA81EBD0394A32BBB1D24A80280720F4D4AEEE8BE69A76F |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/organizations-classes/005-revoke-assignment-api-be1-v1-organizations-organization-id.bru | B3025EFADB9C36DF1EE1D5B838B0E5FCFEAA081E5E107E53A1471DD67D93C8E1 |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/openapi.runtime.json | A701C5FF1E429FD74F982F614E355A375B07F85D22440FD658A5EDA7871DAB19 |
| R | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md | 3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22 |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV37_20261030.json | 764C3915BFF1795E12A70486247B76E76E6DCE077E25116D69D4E1ED312EE8A4 |
| H | features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV45_20261101.json | 352EA298525A36B046D34D90DB97D7C0057F9D026582E52DD002710A56805C05 |
| R | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC |
| R | features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md | 830672AFF1533CF2D42AEF48818967F4B2DBB110132F5B0709D66BD924FA3425 |
| H | features/FEAT-063-system-architecture-rearchitecture/evidence/B0_openapi_combined_storage-off_20261030.json | 252D318DB7F97F94FC81C6483F0B0E56E62DE87036041BEE5E0D85889304DBF1 |
| H | features/FEAT-063-system-architecture-rearchitecture/evidence/B0_openapi_combined_storage-on_20261030.json | F139B41B6EBC1EA61CDDEB99003F62D08E17C7DB42CF8BB23959DCAEB417808B |
| H | features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.csv | BA017D25C047A3B65EECF6408342D322FA54953E5C78E54100EC8A2BACE4E2FB |
| H | features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.md | E657774B1483B68A35EE8A2CF617113221F0AC43B15447E9A43335D130C17DB8 |
| N | features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md | không tồn tại |
| N | features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md | không tồn tại |
| H | features/FEAT-063-system-architecture-rearchitecture/evidence/REV34_LEGACY_ROUTE_SMOKE_20261029.csv | E5DFE58302ED396D2196AD363527902432BC58A1229F57437DE2A3D27C6980ED |
| R | features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md | 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1 |
| R | features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md | 6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68 |
| R | features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_TASK_APPROVAL_DRAFT1_20261107.md | 2875C0A5F25657BDCE2645CF2733FA0B5E52E4EE9EF9544C19C6AAA697400C58 |
| R | features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_TASK_APPROVAL_DRAFT1_20261107.md | 160511C0FF3643D7C53BDDB1AFBE974B38BF98DADBE4C8160B18943A676B7769 |

Đếm phân loại: R/H/E là các mục hiện có; N là đúng 5 ứng viên mới, đều chưa tồn tại. Historical artifacts H chỉ được đọc để giữ lịch sử; không sửa Bruno/OpenAPI artifact trong S1a-T.

## 6. Stop gates, owner fields, validity

Dừng nếu pin/HEAD/index lệch; target DB hoặc DB access xuất hiện trong baseline; module khởi tạo Settings/app/engine/socket/HTTP; command vượt trần; output ngoài hai ignored directories; secret lộ; exit/summary/safety verdict thiếu. Trước pytest, bất kỳ bảng nào có hàng đều là `PRE_RUN_ROWS_FOUND` và dừng, không chạy pytest. Sau pytest, thiếu official summary ghi đúng `NOT RUN: no official pytest summary` và không kết nối DB cho post-inventory. Khi hết timeout, chỉ coi process tree đã dừng nếu `taskkill.exe /PID <pid> /T /F` exit 0, hoặc exit 128 và tiến trình gốc đã thoát; trường hợp khác là `PROCESS_TERMINATION_UNCONFIRMED`, không inventory. Không tuyên bố đã liệt kê tiến trình con mồ côi; trạng thái đó chưa xác minh. Không retry, đổi shell, flags hay selection.

Ghi command, executable/version, cwd tương đối, stdout, stderr, exit, hash log, pytest summary và failed/error node IDs. Assertion fail có summary là baseline data; collection/import error, internal error, timeout, interruption hoặc thiếu summary là NOT RUN / không verdict. SKIP và NOT RUN không là PASS. mypy so bằng diagnostic chuẩn hóa (repo-relative path, code, message); pytest so đúng node set.

**Owner fields để trống:** xác minh pin, shell preflight kín, operator launch, thư mục output mới/ignored, thời điểm, kết quả, owner review/acceptance và baseline closure. Không tick checkbox.

Hiệu lực chỉ cho một baseline trước S1a-T; không dùng làm baseline sau T trước P. Không mở S1a-T, S1a-P, S1b, S2, S3 hoặc M3–M6. Không cho phép implementation, DB write, migration, Docker, Modal, GPU, provider hay network. OWNER_MODAL_CALL_APPROVED=NO.

**Approval basis/signature/date:** CHƯA ĐIỀN.

## Revision 2 change record

The table follows the file order in the `git diff --no-index` comparison with the prior specification. It records the changes required by D-159 B3–B5 and the R2 launcher pin.

| Order | Location | Change |
|---:|---|---|
| 1 | Title | Label this new copy as R2; leave the prior specification unchanged. |
| 2 | Owner decision record | Explicitly list D-159 as the source for the R2 revision and staged approval gates. |
| 3 | Review basis | Identify D-159 B3–B5 as the source of the inventory and timeout clarifications. |
| 4 | §1 pins | Pin the current D-159 decisions record, the Baseline Launch Instruction R2 and the S1a-T R2 launcher. |
| 5 | §2.3 test-row inventory | Require all-table pre-counts and per-table post-counts with marker comparisons; forbid the run if any pre-existing row is found; preserve rows and state the single-use constraint. |
| 6 | §3 PostgreSQL acceptance | Add the pre-run inventory gate, the exact missing-summary behavior and the timeout-summary condition. |
| 7 | §6 stop gates | State the `taskkill` exit rules, unconfirmed-termination stop, no-summary no-connection rule and unverified orphan-child enumeration. |
| 8 | Revision record | Add this change table, identified against `git diff --no-index`. |

# B3 — Ownership, shared-file and migration-order manifest

> **Scope and limits:** documentation-only inventory and proposal. This manifest is not an execution manifest, code/schema/migration approval, owner signature, provider authorization, or database permission. No code, migration, service, database, MinIO, Modal, GPU, or test operation was performed. No Alembic revision was created, merged, or applied. All proposed co-signatures remain **CHƯA KÝ**. The eight owner-local files and the B2 handoff were preserved. No staging, commit, or push was performed.

- Feature: FEAT-063; branch: feature/feat063-be-foundation.
- Approved B3 plan SHA-256: 1523AADBEB8B664D6CE5324B2E5F4D6D4085DF9EC71A4D3C72A9FC827FF26514 (verified).
- B3 approval: documentation-only scope recorded in FEAT-063 approvals/TASK_APPROVAL.md; it does not approve FEAT-064 implementation, Rev36 implementation, migrations, database rehearsal, or Modal live calls.
- Snapshot date: 2026-10-31. Hashes below identify the read inputs for this manifest; they do not imply those inputs are approved for implementation.

## 1. Input hashes and static source snapshot

SHA-256 values are of the exact repository file bytes read for this manifest. Planned files that do not exist yet are identified as NEW/TBD and have no hash.

### Planning, decision, approval, and role inputs

| Input | SHA-256 |
|---|---|
| B3 plan: features/FEAT-063-system-architecture-rearchitecture/plan/B3_OWNERSHIP_MANIFEST_PLAN_20261031.md | 1523AADBEB8B664D6CE5324B2E5F4D6D4085DF9EC71A4D3C72A9FC827FF26514 |
| FEAT-064 plan/PLAN.md | CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665 |
| FEAT-064 DECISIONS.md | FD7B9ED0943509B31C07284B2B42EA9FBA26EE203D68BAA09E512D5CD8230644 |
| FEAT-064 OWNER_PATH_MANIFEST_DRAFT.md | F5AFC985357CD0610D8A31CF4954C6F28C0A8B7B2E81D111560ACDE72F8A9EEE |
| FEAT-064 ELIGIBILITY_GUARD_INVENTORY_DRAFT.md | D3F109F99824F2CF085DD528A4BB85888AA7E3F17A335D406F6B3F5282134615 |
| FEAT-064 CONTRACT_OUTLINE_DRAFT.md | 63937D10EA9513AC74FFB4049E29FE91072E33B8CAE246409137CE46F740496E |
| FEAT-064 approvals/TASK_APPROVAL.md | 71514E7F2BDA2AAE96374135FE6DE450F15816567191DBBF74B4F23EAA0B5A8B |
| Rev36 PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md | 8DD1989926DCA4E0312ABD79032EE4AF862A9FE1AAAB786A6BC4BC6DB5389751 |
| Rev36 REV36_S1_EXECUTION_SCOPE_DRAFT_20261029.md | 64B72C49C4734BDC07353105B10607B117E032C3726F3C7C642D8965A5697A9D |
| B1_API_CROSSWALK_20261030.csv | 6D95F1FC485685BC7D615775F5F45FDBED2C2072AAD07534AC7D8FE915E586A2 |
| ADR-0015-four-person-role-and-integration-allocation.md | 714A9C4FAA192991547235B658B69EC59E3784200C6CA9583EE163621AB47B57 |
| FEAT-040 TEAM_TASK_BREAKDOWN.md | 293FCB8CFCA9A603C0EE18E745AE37D61C3C13DE80CDAA336AC648AD4F706CA9 |
| FEAT-063 approvals/TASK_APPROVAL.md | FD5F03EA5A4F78F7F1F92B9BA3848CFD8EE0D5E9D7579E4D89472F2E55A92477 |

### Existing source and test files in the owner-path / overlap inventory

| Repository path | SHA-256 |
|---|---|
| backend/src/sketch2life/contracts/schemas/be1_runtime.py | B2FD3DD60749EA64A7CE81A4B9D7523BFA48E99BCF90DBC8314E0A36AB8A1689 |
| backend/src/sketch2life/interfaces/http/be1_runtime.py | E7A990F325FECD79672E4751C287F58914FEB499276312BE6BBC0A7190372A85 |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py | 285CBEEDEFDEF30CCF9C0A35DD7014824CBC7D87F66C5C3A03BB9A58BB302B68 |
| backend/src/sketch2life/interfaces/http/routers/be1_sessions.py | A7BCA0FCA0217B19E1E0ADE0A3EB67B2FE120188617EA0DD9F3AC1A2B8A4BAAB |
| backend/src/sketch2life/interfaces/http/routers/be1_common.py | 6EF19F03AF0C74353D6723DB239C6E5059B224C2DF202F3D5BB9B3961C41F07D |
| backend/src/sketch2life/interfaces/http/routers/be1_records.py | 05A9EB9A1C1E732EB3801213798A3DEE74B96E52517545513B42886DA392D9CF |
| backend/src/sketch2life/interfaces/http/routers/be1_canvas.py | 9D68761473A3C3322E8FD36DD650C8997B9DE13E3B4000A029133AC2C5127A0E |
| backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py | CC844D9B3C1AFCDF0B09CB68AF0D0F9FDC600F72B94E0C96EFB3204222134CA9 |
| backend/src/sketch2life/infrastructure/persistence/be1_models.py | 59957310F62C188BB934E54B76999D885936A48DB8C607DDF10DDBCBC697D683 |
| backend/src/sketch2life/infrastructure/persistence/core_store.py | D32AF10E0FDD76EBE2739E2DFE6386750BEC590D631A3F614E23CFFEBF9C72A3 |
| backend/src/sketch2life/domain/vision_analysis.py | CB36B2917EC0E9061C21DCA4B1AC27316F57E329FC3CAAFBD78AD1FA41F3DFA5 |
| backend/src/sketch2life/domain/assistance.py | AB4DF2971BD403C209810FC958AC249E8B4CB5D74EBC21B2A5B82C28FB455E1C |
| backend/src/sketch2life/application/ports/vision_analysis.py | 2F36D096127930A25B60057B48F47DF726EB77E132808A20B2E5B15E7E5584AE |
| backend/src/sketch2life/application/ports/assistance.py | 5E205659F2ABBE3F3AD5E5459F05A64139D51DCE8A7DB19B60FD3426BD90E338 |
| backend/src/sketch2life/application/services/vision_analysis.py | F30CCBBB5BE5AF360D042EA3DC1D3FB1AD00E8175F60F7D65DAC11D1D7EA9212 |
| backend/src/sketch2life/application/services/assistance.py | 5BFFF0481F7D30158D7F67F57C07EDD576A4AF3499856213CD39065C31E56D34 |
| backend/src/sketch2life/contracts/schemas/analysis_results.py | 46C6F47A379832932509F3D29A4A41DE7863D28A3FA615D008AEF5806F6311AC |
| backend/src/sketch2life/contracts/schemas/analysis_context_results.py | 3844377F4FA114FDD5C48F051BDCDB2562340BBBCEAD89D9418B3BE4239A2E5D |
| backend/src/sketch2life/contracts/schemas/assistance_requests.py | 2C2DF0B574E2C5BB846C8E3C6688F1291966357F94F02AE83356886F7A5B62A2 |
| backend/src/sketch2life/infrastructure/ai/lightning_client.py | A8F0FE7BFC0B5770D5AB335B787353C42633C639DB6E0A0A9600DF3707AA4DA1 |
| backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py | D231C6EEA73B47A41A2D5C8758C1CEB0EF951FB4CB746A4D06D344B4C4F1F19F |
| backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py | B4D3F41836D8F62C2E2C8BD01D2D4149AB7B61CACEE844F42C1DA8A030DA5ADE |
| backend/src/sketch2life/infrastructure/vision_analysis/context_adapter.py | D01CF98FC5A18233B112C4ED8E8D77EFD4E46377718ABA0A1D5523D6331F683A |
| backend/src/sketch2life/interfaces/http/app.py | AAF3CCC525F8644D7EFA31AD2FC18214A073C5E4694C53F3C6A701AFB9A0132B |
| backend/src/sketch2life/interfaces/http/router_composition.py | 97FE9AE52C914C79AD13500C55809455863A95310EF6787F2F5F809C0A5F6E20 |
| backend/src/sketch2life/infrastructure/config/settings.py | C2AC5064EC9FEA4B8E3F591CE4B923C72A804DBC4F3EC5E50CFE218A905DBFB6 |
| backend/src/sketch2life/application/services/ai_jobs.py | 15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE |
| backend/src/sketch2life/domain/ai_jobs/model.py | 512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99 |
| backend/src/sketch2life/infrastructure/ai_jobs/worker.py | A54725329F8643FB0AF9D821F9861BE34980C3DA3E28E201203630EA691785F6 |
| backend/src/sketch2life/infrastructure/assistance/fakes.py | BDBB4317CFA2DC2143602CC3172B400504D7E907C0CA8AAE51AE516CE2C8B517 |
| backend/src/sketch2life/infrastructure/vision_analysis/fakes.py | 743A46897914C0457B64D77567CDB188DB94E39F9498E6A0E3CC3C3C8B0414FA |
| backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py | F12560D8F68EA31C5F76BB10E0452310CFF019C3D2DF5A90D8970889D052EC92 |
| backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py | 12F6CE1EDAB047EFDD81D495B44DF08DC6F990692860621F37FC73778006F888 |
| backend/tests/contract/test_app_composition.py | F978B3EEE2DC527C68529E23542044179F5517A010A852F02B043A1588B3D885 |
| backend/tests/unit/test_settings_security.py | D6A30DE7A8E05862DAA48B3F17326518450692B50F080AC687A26E628C18DA54 |
| apps/child-ui/app/index.tsx | 57B5ACE6E94D69655E80A74ED3E99BC0AE5F6B06C19D942D865B3206C65FAE3C |
| apps/child-ui/src/services/sessionClient.ts | B0D5C9CD89ADF29BF7A3D900BD31C9B7CCD08553A9059A1280493C54B3675830 |
| apps/child-ui/src/services/apiClient.ts | 16A14A65D05C400AF9AA0E11DDDCFBFF4F212A077859B183F90036C1FF36CB66 |
| apps/child-ui/src/hooks/useReviewStatus.ts | 60B88FFA3DECAF7F1C1633D9E95081DE28FFAEE85BC3D3EB113AA2516165B131 |
| apps/teacher-ui/src/pages/AiSuggestionReviewPage.tsx | D8735EEAE90676B20FA4BFACF79131688FCF5BB134A1CDCB240B4E294B6CD304 |
| apps/teacher-ui/src/services/apiClient.ts | AA3D980C8DC84FCE6A87644BF96963BF9D8A1E0D15EE1B1A01AE41D3AF1C7742 |
| Planned new paths in O16 and the Teacher pending-analysis panel | NEW/TBD; exact paths have not been selected |

### Static Alembic revision inputs

All 22 files under backend/alembic/versions were read as text and their literal revision metadata was inspected. The complete per-file SHA-256 inventory follows.

| Repository path | SHA-256 |
|---|---|
| backend/alembic/versions/20261014_0001_core_persistence.py | 55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C |
| backend/alembic/versions/20261014_0002_be1_runtime.py | 08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520 |
| backend/alembic/versions/20261014_0003_canvas_payload.py | 194A831C661CA84C796557CCCF762715F6C0CC0E747521D588D1F30E1A5BB9E5 |
| backend/alembic/versions/20261014_0004_be1_constraint_names.py | AB15DFCE0738D994B14B337A03B34F7365BBBC67AFFE3BB01F24901F87BAFFFD |
| backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py | D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714 |
| backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py | 81F84E9B3C4C7929018EB0A82ABED1DC2581811BB178EC6097E3134BBD8D765A |
| backend/alembic/versions/20261017_ap_0002_effective_scope.py | 35DBAA33A4F41EC69A01E03D688AF9B9238145EE0006D54CA67C115D0987CDE7 |
| backend/alembic/versions/20261017_ap_0003_resource_ledger.py | FEE3A90E27691B90B1D45E6DE7D14C3DB77311EBE86414051B55C75D02AB1924 |
| backend/alembic/versions/20261017_ap_0004_copy_inventory.py | 3EC8747A198941C9C4B36C4FDD0E08986355F0B2334589951EEA99BBF20AC2E7 |
| backend/alembic/versions/20261017_ap_0005_copy_evidence.py | 9E364BF938C2D6B6714FDE8C2A2527AAB84D3DD378C1AE16C0578FD86B9B8C12 |
| backend/alembic/versions/20261017_lc_0001_content_publication.py | DA2B372442A7CF234B8C1FC0FC7472B5A068FE8F832B6465C1BC1E4D2FE2F498 |
| backend/alembic/versions/20261018_ap_0006_copy_operations.py | B266744B3792E0E68347FA674B374A54D14CC33E4776106ADE91E2E407C447F7 |
| backend/alembic/versions/20261018_ap_0007_copy_delivery.py | 3BF400A165F5D681017FFE1AADEEAEB724BFFF5992289FB21331F5247C479E52 |
| backend/alembic/versions/20261018_ap_0008_delivery_authority.py | 9D8171F8B00C603FD350E32B6D6412B049A504F47B4D4F92355D654C86B71E05 |
| backend/alembic/versions/20261018_ap_0009_copy_resolution.py | 465A3421BC54895D2969AE95B1E3A9425689D1ED38B1CD6BCD8FE29D9B961A44 |
| backend/alembic/versions/20261018_kv_0001_knowledge_video.py | E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87 |
| backend/alembic/versions/20261018_vr_0001_video_review.py | 3E489443949C0934B414E4A69C6BD01B09782F4653042803C79291D66B415FC7 |
| backend/alembic/versions/20261019_ae_0001_activity_execution.py | 56993DC8CE1507D471ED3E3052F99A3A05B9D26C64E979822198946CD9EF9C30 |
| backend/alembic/versions/20261019_pa_0001_preset_automation.py | D2A8B958D6BD9411D040E3358F5568E2C728C1095D5395D55532916ACC5182E8 |
| backend/alembic/versions/20261019_vf_0001_video_failure.py | 0520CB0EB850D1BB4A267571F30937677908E505B77E221D1F0C90EE806FD178 |
| backend/alembic/versions/20261024_0005_classroom_srs_contracts.py | E533FC15447222C334A82CD162DC01FEB7B94221B402552D774CBD11E7D7289C |
| backend/alembic/versions/20261028_ll_0001_lesson_library.py | 98CBB1466AD9A6D672D734E2D861BB8974A947061D5F930B75CAEECEBE5D708E |

## 2. S1 — Owner matrix: 18 source boundaries

The source paths below were checked as present at this snapshot. O16 is NEW because its exact selected durable store/schema/migration/UoW/ledger/witness paths have not been frozen. O18's existing Teacher page is reference-only; the future pending-analysis panel path remains TBD and is not represented as an existing file. Writer labels marked “proposal” are role-based candidates, not task assignment or approval. NEEDS_OWNER means the named writer/reviewer or exact hunk must be assigned at T0.

| ID | Boundary and verified source paths | State | FEAT-064 tasks and pilot delta | Rev36 overlap | Writer proposal | Reviewer | Co-sign state |
|---|---|---:|---|---|---|---|---|
| O01 | BE1 wire — contracts/schemas/be1_runtime.py | Y | T3/T4; B1 T053 | none | CaoDat-2410, BE1 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O02 | BE1 identity/eligibility — interfaces/http/be1_runtime.py | Y | T1/T2/T9; B1 T054–T056 | S1 | CaoDat-2410, BE1 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O03 | BE1 registry/session — routers/be1_registry.py, be1_sessions.py | Y | T1/T2/T3; C030/C035/C037/C038/C039/C041/C045/C054/C055 | S1 | CaoDat-2410, BE1 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O04 | BE1 shared consent/records — routers/be1_common.py, be1_records.py | Y | T1/T2; synthetic evidence and consent/record gates | S1 | CaoDat-2410, BE1 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O05 | BE1 canvas — routers/be1_canvas.py | Y | T3/T4; C003/C004 and T053 export | S1 | CaoDat-2410, BE1 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O06 | BE1 artifacts — routers/be1_artifacts.py | Y | T5; C001/C002 reuse remains MAYBE | S1 | CaoDat-2410, BE1 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O07 | BE1 persistence — infrastructure/persistence/be1_models.py, core_store.py | Y | T1/T7a; synthetic profile representation | S2 | CaoDat-2410, BE1 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O08 | BE2 domain/ports — domain and application/ports vision_analysis.py, assistance.py | Y | T2/T6/T7b/T8; eligibility and continuation contracts | S2 contract dependency | AnhKhoaa157, BE2 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O09 | BE2 services — application/services/vision_analysis.py, assistance.py | Y | T6/T8; analysis-only lifecycle | none | AnhKhoaa157, BE2 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O10 | BE2 contracts — contracts/schemas/analysis_results.py, analysis_context_results.py, assistance_requests.py | Y | T6/T8/T9; versioned live-dev contracts | none | AnhKhoaa157, BE2 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O11 | Existing transport — infrastructure/ai/lightning_client.py, lightning_vision_v2.py | Y | T6/T8/T13; reuse existing Qwen Vision V2 transport only under separate live approval | none | AnhKhoaa157, BE2 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O12 | Offline bridges — infrastructure/vision_analysis/legacy_v2.py, context_adapter.py | Y | T6/T8; keep C1/C2 restrictions | none | AnhKhoaa157, BE2 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O13 | Composition/settings — interfaces/http/app.py, router_composition.py; infrastructure/config/settings.py | Y | T9/integration; classroom-only opt-in | S1 | NEEDS_OWNER; Person 2 coordinates but does not automatically write | P4 role, unnamed (review proposed) | CHƯA KÝ |
| O14 | Retry/recovery — application/services/ai_jobs.py, domain/ai_jobs/model.py, infrastructure/ai_jobs/worker.py | Y | T6/T8/T7a-c; bounded pilot retry/outcome | S3 | AnhKhoaa157, BE2 (D-08) | NEEDS_OWNER | CHƯA KÝ |
| O15 | Test-only fakes/fence fixture — infrastructure/assistance/fakes.py, vision_analysis/fakes.py, ai_jobs/sql/owner_fence_fixture.py | Y | T6/T7a/T7b; fixture remains test-only | none | NEEDS_OWNER; mixed fixture boundary | NEEDS_OWNER | CHƯA KÝ |
| O16 | Durable runtime — exact selected assistance/analysis store, schema/migration, OwnerFence/UoW, ledger and witness paths | NEW | T0/T7a/T7b/T7c; minimal selected durable state only | S2/S3 migration interaction | NEEDS_OWNER; paths/schema owner not frozen | NEEDS_OWNER | CHƯA KÝ |
| O17 | Child UI — apps/child-ui/app/index.tsx, services/sessionClient.ts, services/apiClient.ts, hooks/useReviewStatus.ts | Y | T3/T10; synthetic draw and explicit request/status | none | P1 role, unnamed (ADR-0015) | NEEDS_OWNER | CHƯA KÝ |
| O18 | Teacher UI — AiSuggestionReviewPage.tsx and services/apiClient.ts (reference only); future panel path TBD | Y | T11; read-only Teacher pending-analysis | none | P1 role, unnamed (ADR-0015) | NEEDS_OWNER | CHƯA KÝ |

Full S1 fields, including exact paths, pilot details, shared-file flags, conflict IDs, co-sign requirement and notes, are in B3_OWNER_MATRIX_20261031.csv. Across O01–O18: 17 rows are Y and one row (O16) is NEW; none is N. The complete owner draft contains 18 boundary rows; this corrects the draft plan's S1 prose typo that said 17 rows.

Rev36 overlap counts for O01–O18: none = 8; S1 only = 6; S2 only = 2; S2 and S3 = 1; S3 only = 1. Counting each overlap label separately gives S1 = 6 rows, S2 = 3 rows and S3 = 2 rows. O08 is marked S2 as a contract dependency; its listed source files are not included among exact shared-file X rows.

## 3. S2 — Role mapping and unresolved mismatch

These are separate source mappings. Role labels are not interchangeable, and neither table records a signature.

| Source | Recorded allocation | What it does not establish |
|---|---|---|
| ADR-0015 §Accepted staffing decisions, lines 16–19; TEAM_TASK_BREAKDOWN.md lines 9–16 | P1 = FE; P2 = BE1 core/classroom/data; P3 = BE2 AI/content/media; P4 = technical integrator. P4 owns composition, cross-boundary connectors and FE–BE/worker wiring; component logic remains with P1/P2/P3. Names are unspecified. | It does not name P2/P3/P4 as GitHub identities for FEAT-064; it does not sign OwnerFenceV1 or allocate each shared file. |
| FEAT-064 DECISIONS.md D-07/D-08, lines 11–12 | Person 2 / AnhKhoaa157 is BE2 owner, integration coordinator and live operator; BE1 owner is CaoDat-2410. Person 2 coordinates shared files/order and is to sign OwnerFenceV1 with named BE1/BE2 owners at T0. | It does not rewrite ADR role labels or record actual OwnerFenceV1 signatures; a coordinator/operator is not automatically the only writer/reviewer. |
| Rev36 coordination, PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md lines 69–73 | Explicitly says the Person 2/BE2 designation is FEAT-064-specific; ADR-0015 uses P2/BE1 and P3/BE2. It asks that P4 be involved in composition ownership, coordination and review of app.py/router_composition.py/wiring. | It does not authorize a reassignment or resolve who the named writer is. |

| Affected boundary | Conflict and consequence | Non-binding way to resolve |
|---|---|---|
| BE2 identity | ADR-0015 calls P3 BE2; FEAT-064 D-08 names Person 2 / AnhKhoaa157 BE2. | Owner records whether D-08 is a scoped exception to ADR-0015 and how this maps to named contributor(s); do not silently relabel P2/P3. |
| app.py and router_composition.py | ADR-0015 assigns composition ownership to P4 (unnamed); FEAT-064 makes Person 2 integration coordinator; Rev36 calls for P4 involvement/review. | Name one writer and an independent reviewer per file at T0. Proposed default: P4 role participates in composition review; actual person and any exception require owner record. |
| Settings, shared tests and migrations | Coordination is not file authorship; FEAT-064 and Rev36 both identify these as shared work. | Assign one named writer per exact file/hunk and one review owner in the signed manifest; migrations also need one canonical schema owner/order. |

## 4. S3 — FEAT-064 × Rev36 shared-file inventory

“Shared” means the plans identify a common file or an explicit migration-graph/schema coordination point. It does not mean both plans authorize changing the same lines. Rev36 says FEAT-064 rev6 and Rev36 are unapproved proposals, requires a shared ownership/migration manifest, says to reuse approved work rather than duplicate it, and keeps S1 from being an implicit pilot prerequisite; if S1 is used, its classroom flag remains enabled during pilot (Rev36 §Coordination, lines 69–73).

| ID | Shared path | FEAT-064 delta | Rev36 delta | One writer proposal | Order / guard |
|---|---|---|---|---|---|
| X01 | infrastructure/persistence/be1_models.py | T1 synthetic profile representation; consent refs nullable only under approved CHECK | S2 adds account_scope/data_origin and nullable consent refs/CHECK | CaoDat-2410 proposed by BE1 role; confirm exact author | Resolve OD-13 and choose one schema owner before either writes |
| X02 | infrastructure/config/settings.py | T9 pilot opt-in and classroom-only profile | S1 proposes backward-compatible classroom_writes_enabled/demo_flow_enabled flags default true | NEEDS_OWNER; P4 review proposed | Freeze flag names/defaults; preserve FEAT-064 pilot default-off and Rev36 S1 defaults if both proceed |
| X03 | interfaces/http/app.py | T9 selected classroom runtime composition | S1 wires per-app fence/profile behavior | NEEDS_OWNER; P4 role owns composition in ADR | One named writer, separate reviewer, exact profile and error envelope at T0 |
| X04 | interfaces/http/router_composition.py | T9 classroom pilot mount; no demo/combined widening | S1 conditionally omits combined demo routers | NEEDS_OWNER; P4 role owns composition in ADR | Freeze route/profile allowlist; do not infer profile from the other plan |
| X05 | backend/tests/contract/test_app_composition.py | T9 runtime profile acceptance | S1 default compatibility and profile matrix | NEEDS_OWNER; P4 coordinates integration tests | Agree one test owner and complete matrix before source changes |
| X06 | backend/tests/unit/test_settings_security.py | T9 pilot opt-in setting acceptance | S1 flag parsing/default regressions | NEEDS_OWNER; P4 coordinates integration tests | One test author and preserved defaults need owner approval |
| X07 | interfaces/http/be1_runtime.py | T1/T2 eligibility and separate status-read/write guard | S1 may choose middleware or router dependency for scoped legacy fences | CaoDat-2410 proposed by BE1 role; confirm hunk | Freeze operation/call-site inventory; no blanket bypass |
| X08 | interfaces/http/routers/be1_common.py | T1 shared consent helper call-site disposition | S1 proposes retired-feature error envelope for selected operations | CaoDat-2410 proposed by BE1 role | Keep consent helper semantics separate from retirement response |
| X09 | interfaces/http/routers/be1_registry.py | T1 profile/synthetic evidence and eligibility | S1 leaves registry operations outside its fence; S2 adds Parent identity/profile paths | CaoDat-2410 proposed by BE1 role | Inventory exact profile/create/revoke hunks; preserve registry exclusions |
| X10 | interfaces/http/routers/be1_sessions.py | T1 lifecycle gates; active group/admitted member/turn | S1 inventories session writes as candidates, not approved denylist | CaoDat-2410 proposed by BE1 role | Explicitly disposition finish/completion/revoke/leave/rotate and pilot paths |
| X11 | interfaces/http/routers/be1_canvas.py | T3/T4 accepted operations and consistent export | S1 inventories canvas writes as candidates | CaoDat-2410 proposed by BE1 role | Preserve originals; freeze operation-level fence decision |
| X12 | interfaces/http/routers/be1_artifacts.py | T5 private artifact/admission handoff; C001/C002 reuse remains MAYBE | S1 lists artifact upload as candidate | CaoDat-2410 proposed by BE1 role | Do not deny or depend on these routes until both path reuse and S1 disposition are chosen |
| X13 | interfaces/http/routers/be1_records.py | T1 consent/record inventory | S1 preserves privacy data-request semantics and registry exclusions | CaoDat-2410 proposed by BE1 role | Distinguish privacy lifecycle operations from collaboration writes |
| X14 | infrastructure/ai_jobs/sql/tables.py | T7a selected minimal durable pilot state | S3 adds typed owner scope and target fields on AI jobs branch | AnhKhoaa157 proposed by BE2 role; confirm exact author | Freeze minimum pilot schema vs S3 fields and a single migration owner |
| X15 | domain/ai_jobs/model.py | T6/T8 bounded attempt/outcome and analysis-only continuation | S3 extends JobScope and target tuple while preserving legacy constructors | AnhKhoaa157 proposed by BE2 role | Contract review before model edits; keep A1 accounting separate |
| X16 | application/services/ai_jobs.py | T8 bounded reconciliation and no Sketch continuation | S3 generalizes owner-notice scope matching | AnhKhoaa157 proposed by BE2 role | Define selected intersection; preserve legacy A1 behavior and no duplicate lifecycle |
| X17 | backend/alembic/versions/<new T1 or S2 revision>.py — planned, does not exist | T1 may need profile synthetic-origin/schema work | S2 proposes additive BE1 branch migration after 20261024_0005 | NEEDS_OWNER; canonical schema/migration owner absent | Decide X/Y/Z; no revision may be created or applied under B3 |
| X18 | backend/alembic/versions/<new T7a or S3 revision>.py — planned, does not exist | T7a minimal durable assistance/analysis repositories | S3 additive migration after 20261015_ai_0001 on AI jobs branch | NEEDS_OWNER; exact migration ownership/order absent | Freeze branch graph and contract dependency; separate approvals and DB scope required |

The proposed writers are role-based ownership candidates from D-08/ADR-0015; they are not signed assignments. All 18 X rows have exactly one writer proposal or NEEDS_OWNER. Every applicable cross-owner fence row lists BE1, BE2 and integration-owner co-signatures as required by the selected contract; no row is signed. The machine-readable conflict IDs and one-writer field are in the CSV.

## 5. S4 — Static Alembic graph and migration-order options

The graph was read statically from revision metadata in the 22 hashed files above. No Alembic command, database connection, upgrade, downgrade or revision generation was run.

| Revision | down_revision | depends_on | Branch / observation |
|---|---|---|---|
| 20261014_0001 | none | none | BE1 persistence root |
| 20261014_0002 | 20261014_0001 | none | BE1 runtime |
| 20261014_0003 | 20261014_0002 | none | BE1 canvas payload |
| 20261014_0004 | 20261014_0003 | none | BE1 constraint names |
| 20261024_0005 | 20261014_0004 | none | BE1 classroom SRS contracts; current BE1 effective predecessor |
| 20261028_ll_0001 | none | 20261024_0005 | Lesson Library root by down_revision with explicit BE1 depends_on |
| 20261015_ai_0001 | none | none | AI jobs branch root |
| 20261017_ap_0001 | none | none | Policy lifecycle branch root |
| 20261017_ap_0002 | 20261017_ap_0001 | none | Policy lifecycle |
| 20261017_ap_0003 | 20261017_ap_0002 | none | Resource ledger |
| 20261017_ap_0004 | 20261017_ap_0003 | none | Copy inventory |
| 20261017_ap_0005 | 20261017_ap_0004 | none | Copy evidence |
| 20261018_ap_0006 | 20261017_ap_0005 | none | Copy operations |
| 20261018_ap_0007 | 20261018_ap_0006 | none | Copy delivery |
| 20261018_ap_0008 | 20261018_ap_0007 | none | Delivery authority |
| 20261018_ap_0009 | 20261018_ap_0008 | none | Policy/copy terminal |
| 20261017_lc_0001 | none | none | Content publication branch root |
| 20261018_kv_0001 | none | none | Knowledge video branch root |
| 20261018_vr_0001 | none | none | Video review branch root |
| 20261019_ae_0001 | none | none | Activity execution branch root |
| 20261019_pa_0001 | none | none | Preset automation branch root |
| 20261019_vf_0001 | none | none | Video failure branch root |

Two explicit head counts:

1. **down_revision-only terminals: 10.** A revision is terminal if no file names it in down_revision. This count includes 20261024_0005.
2. **dependency-graph terminals: 9.** Apply the same test but also treat depends_on as a reference. This removes 20261024_0005, which is referenced by 20261028_ll_0001.

Thus the Rev36 wording “nine heads plus the effective BE1 head” is not itself an unambiguous counting rule. The static metadata yields 10 under the down-only rule and 9 under the dependency-aware rule; the BE1 chain terminates at 20261024_0005, and Lesson Library explicitly depends on it. Do not infer that Alembic runtime output was checked or that one count authorizes merging heads.

| Option | Proposed ownership/order (not selected) | Conditions | Risks that remain |
|---|---|---|---|
| X — pilot owns the profile-origin change | FEAT-064 T1 owns the canonical synthetic/profile-origin schema and guard representation on the BE1 branch after 20261024_0005; Rev36 S2 reuses the reviewed representation or narrows its schema delta. | Owner names one schema/migration writer; reconcile SYNTHETIC_DEV versus SYNTHETIC_TEST, constraints and existing-guard scope; S2 independently approved; OD-7 database permission before rehearsal. | (1) FEAT-064 proof lifecycle and Rev36 Parent profile schema may not be the same change. (2) Enum/constraint mismatch can leave the new path incompatible. (3) Rev36 S2 approval and OD-7 DB approval are absent. (4) FEAT-064 T1 guard changes could conflict with S2's rule to leave existing guards unchanged. |
| Y — Rev36 S2 owns the profile-origin schema | Rev36 S2 owns schema/migration after 20261024_0005; FEAT-064 T1 consumes that exact reviewed representation and adds only separately approved pilot proof/guard behavior. | Freeze Rev36 canonical model, proof relation and checks; keep current classroom guards unchanged under S2; approve FEAT-064 T1 changes separately; OD-7 before migration acceptance. | (1) Rev36's SYNTHETIC_TEST/REAL/LEGACY_UNCLASSIFIED differs from FEAT-064's typed SYNTHETIC_DEV decision. (2) S2 does not itself implement the pilot's current-flow eligibility and proof lifecycle. (3) No Rev36 implementation approval or DB rehearsal approval exists. (4) Pilot may wait on an independent foundation task. |
| Z — separate, explicitly coordinated migrations | One canonical profile-origin migration and one distinct selected durable-runtime migration, only where owners prove separate storage concerns and explicitly pin dependencies/order. Pilot and Rev36 each reuse the canonical representation. | Two named owners plus a signed shared manifest; no duplicate origin column/CHECK; branch parents and dependency rationale frozen; OD-7 and separate implementation approval. | (1) The two branches can create competing schemas or duplicate constraints. (2) Upgrade/downgrade order can strand references or durable state. (3) Static multi-head graph increases coordination and rollback risk. (4) No DB rehearsal authority currently exists. |

No option is chosen here. FEAT-064 T1's eventual parent is not pinned by this document; Rev36 S2 proposes the BE1 branch after 20261024_0005, and Rev36 S3 proposes the AI jobs branch after 20261015_ai_0001. FEAT-064 T7a and Rev36 S3 may be different schema concerns; the graph alone does not establish that they must share one revision.

## 6. S5 — Synthetic-origin and consent representation comparison

| Attribute | FEAT-064 D-05 / OD-2 / T1 | Rev36 S2 | Comparison and evidence |
|---|---|---|---|
| Origin representation | Server-managed synthetic proof; typed eligibility result LEGAL_CONSENT / SYNTHETIC_DEV / DENIED; proof binds org/class/child/purpose/run/expiry and supports revoke. | Profile data_origin values SYNTHETIC_TEST, REAL, LEGACY_UNCLASSIFIED; server-controlled origin; synthetic evidence separately managed. | **GIỐNG MỘT PHẦN** — both distinguish source and require server evidence, but the stored enum and proof contract are not the same. D-05; Rev36 §S2. |
| Consent references | Profile references nullable with CHECK by origin; no fake effective consent row or boolean. | Consent refs nullable; CHECK requires no refs for synthetic, both refs for REAL, legacy preserves refs without eligibility. | **GIỐNG MỘT PHẦN** — same broad intent, but exact enum/check/backfill details need one schema owner. D-05; Rev36 §S2. |
| Legacy rows | LEGACY_UNCLASSIFIED is denied. | Backfill rows to LEGACY_UNCLASSIFIED; existing refs do not grant eligibility. | **GIỐNG** at the denial intent; migration backfill details still need review. D-05; Rev36 §S2. |
| Evidence creator/lifecycle | Operator command in local/test with pilot flag; scoped proof has expiry and revocation. | Server-controlled creation flow; evidence is separately approved/managed; missing/revoked/expired evidence is denied. | **GIỐNG MỘT PHẦN** — server control and fail-closed behavior align; exact command, run linkage and persistence contract need alignment. D-05; Rev36 §S2. |
| Eligibility readers and existing guards | Every consent gate calls one typed decision. Selected pilot call sites may need explicit disposition from T1 inventory. | Existing classroom guards and denials remain unchanged in S2; all new profile/AI paths and new guards use typed eligibility and fail closed. | **KHÁC** in scope/timing — T1 may alter selected existing guards; S2 expressly does not. Separate scopes need a precise call-site list. D-05; FEAT-064 PLAN §3/T1; Rev36 §S2. |
| BE2 evidence | consent_effective=false; versioned eligibility_basis. | New profile/AI paths use typed eligibility decision; Rev36 does not pin the exact FEAT-064 field name/version in S2. | **GIỐNG MỘT PHẦN** — eligibility decision is common, exact BE2 contract remains to be frozen. D-05; Rev36 §S2. |
| Schema owner and migration | T0 chooses exact tables, field names, checks, migration and guard call sites. | OD-13 requires one canonical schema/migration owner/order across FEAT-063 and FEAT-064. | **GIỐNG MỘT PHẦN** — both require a T0/owner freeze; neither currently records that owner. |

Conditional conclusion: the profile-origin/nullable-reference portion may be one shared schema change, but the proof lifecycle, enum values, guard scope and BE2 basis are not identical by current text. Owner decision OD-13 is required before implementation; this manifest does not choose an option.

## 7. S6 — Approval and execution gates

| Gate | Observed status | Recorded by / source | Dependency and consequence |
|---|---|---|---|
| This B3 task | APPROVED for documentation-only manifest and matrix; approved plan hash matches this plan. | FEAT-063 approvals/TASK_APPROVAL.md, B3 entry | Allows only the two documentation outputs in this task. No implementation, schema, DB or runtime authority follows. |
| FEAT-064 T0/T1 and plan | AWAITING_APPROVAL; plan says implementation NOT_STARTED. | FEAT-064 approvals/TASK_APPROVAL.md and PLAN.md lines 3–8 | No code/schema change under FEAT-064 until its exact task scope and approvals are recorded. |
| Rev36 S1/S2/S3 | DRAFT / awaiting implementation approval; Rev36 plan hash is 8DD19899…5389751 and S1 scope says awaiting approval. No matching implementation approval was found in the current FEAT-063 approval record. | Rev36 plan lines 1–8; S1 scope lines 1–11; FEAT-063 approvals file | Do not implement S1/S2/S3 based on this manifest. Shared ownership and per-slice approval are still needed. |
| Throwaway PostgreSQL/Docker rehearsal (OD-7) | NOT APPROVED. | Rev36 OD-7, plan line 85 | Static review may proceed; migration acceptance remains BLOCKED until scoped DB approval and real rehearsal. |
| Modal live T13 | NOT APPROVED by FEAT-064 plan; requires T12 evidence and separate live approval/risk acceptance. | FEAT-064 PLAN.md lines 77–79 and 164–165 | No Modal call is authorized by the existing demo smoke or this B3 documentation approval. |
| OwnerFenceV1 signatures | CHƯA KÝ; no signed OwnerFenceV1 was identified in the listed planning inputs. | FEAT-064 D-07/D-08 and CONTRACT_OUTLINE_DRAFT | Dependent cross-owner persistence/invocation work stops until exact signers and accepted version are named and recorded. |
| Shared ownership manifest signatures | CHƯA KÝ. The B3 output is a proposal for owner review. | FEAT-064 D-07; Rev36 OD-13/OD-14 | No shared file or migration gains a writer from this draft alone. |

## 8. S7 — Suggested order, with explicit stop points

This is a dependency proposal, not a new task list or approved implementation sequence.

1. Review this B3 proposal; owner resolves the eight questions below and records named writers/reviewers, the canonical schema owner, migration option and branch order. Stop shared work if the required owner/cosign is missing.
2. FEAT-064 T0 freezes exact source paths/hunks/hashes, consent call sites, profile fields, OwnerFenceV1/UoW, and run/DB identity; its own approval must pin the accepted revision. This B3 approval does not approve T0 implementation.
3. Rev36 S1 may be planned separately under its own approval. Rev36 says S1 is not an implicit FEAT-064 pilot prerequisite; if included during pilot its classroom flag remains enabled. Freeze the exact shared settings/composition/test writer before either slice touches those files.
4. FEAT-064 T1 and Rev36 S2 must not both implement profile-origin schema independently. Proceed only after OD-13 chooses the canonical representation and writer; keep each plan's explicitly different existing-guard scope.
5. FEAT-064 T7a/b/c and Rev36 S3 each need their own approved contracts, owners and exact persistence scope. They may be parallel only after shared ownership and contract boundaries are frozen. Use the independent BE1 and AI-job migration branches only with a documented dependency rationale; do not create a global linear chain or merge heads by assumption.
6. Migration acceptance waits for explicit OD-7 disposable-DB permission and actual upgrade/downgrade rehearsal. T7c throwaway fault-injection is also approval-gated.
7. FEAT-064 T13 remains stopped until T12 has the required evidence and a separate live Modal approval/risk statement is recorded. No provider activity is authorized here.

## 9. S8 — Questions for owner (maximum 8)

| # | Owner question | Non-binding default to consider | Affected scope |
|---:|---|---|---|
| 1 | Does FEAT-064's Person 2 = BE2 assignment explicitly override ADR-0015's P3 = BE2 for this scope, or should the ADR role mapping be amended? | Keep both mappings distinct and record a scoped exception only if owner chooses it. | BE2 files, all shared-file assignments, integration coordination |
| 2 | Who is the one named writer and independent reviewer for every X01–X18 conflict row? | Assign one writer per exact file/hunk; involve P4 in composition review as Rev36 requests. | Shared routers, settings, app composition, tests, model and migrations |
| 3 | Choose migration option X, Y or Z, and name the single canonical owner for data_origin/consent schema. | X is the B3 plan's initial proposal only; compare proof lifecycle and enum/check differences before selecting. | FEAT-064 T1, Rev36 S2, BE1 branch after 20261024_0005 |
| 4 | Who exactly signs OwnerFenceV1, what version is accepted, and when must signatures exist? | BE1 owner + BE2 owner + integration owner named at T0; do not start dependent work before all required signatures. | T0, T7a/b/c, T8 and live gate |
| 5 | Which named P4 reviews/writes app.py and router_composition.py, and is any exception to ADR-0015 approved? | P4 participates in review; keep Person 2 as coordinator unless owner records a different allocation. | O13, X03–X05, Rev36 S1 and FEAT-064 T9 |
| 6 | Which approved slice goes first on shared guards/settings/migrations, FEAT-064 pilot or Rev36? | Freeze owners and hunks first; preserve Rev36's rule that S1 is not an implicit pilot prerequisite and classroom flag stays enabled if S1 is present. | X01–X18 and FEAT-064/Rev36 sequencing |
| 7 | Is a disposable local PostgreSQL/Docker migration rehearsal authorized under Rev36 OD-7? | No DB work until explicit scoped permission is recorded. | Rev36 S2/S3 migration acceptance |
| 8 | When will FEAT-064 T0 and later T13 receive their own approvals? | T0 approval after contracts/owners are frozen; T13 only after T12 evidence and separate live scope/risk approval. | FEAT-064 implementation and Modal |

## 10. S9 — Self-check against B3 plan §6

| Check | Result | Evidence |
|---|---|---|
| 1. All 18 OWNER_PATH_MANIFEST boundaries have rows; every source is present or marked new | PASS — 18 O rows: 17 Y, 1 NEW, 0 N. | CSV O01–O18; source existence and hashes in §1. O16 paths remain NEW/TBD. |
| 2. Every co-sign status is unsigned | PASS — 36 matrix rows (18 O + 18 X), all CHƯA KÝ. | CSV cosign_status column. |
| 3. Role discrepancy cites ADR-0015 and D-07/D-08 | PASS. | §3 cites ADR-0015 lines 16–19, TEAM_TASK_BREAKDOWN lines 9–16, DECISIONS D-07/D-08 lines 11–12 and Rev36 lines 69–73. |
| 4. Each shared file has exactly one writer proposal or NEEDS_OWNER | PASS — 18 X rows; no row has multiple writers. | §4 and CSV writer column. |
| 5. Head counts and method are stated; no head merge proposed | PASS — 10 down_revision-only terminals and 9 dependency-aware terminals; no merge proposed. | §5 revision graph and two formulas. |
| 6. Gate states match approvals and source plans | PASS — B3 is docs-only approved; FEAT-064 remains awaiting; Rev36 remains draft/unapproved; OD-7 and T13 not approved; all co-signs unsigned. | §7 cites approval/plan sources. |
| 7. Source files unchanged; no absolute machine paths, tokens, environment values or child data | PASS for this task scope at authoring time; no source-file edits were made. | Only the two B3 output files were created; final git status and owner-hash recheck reported separately. |

## 11. Limits and unresolved evidence

- Writer names are proposals derived from role labels; only Person 2 / AnhKhoaa157 and BE1 owner CaoDat-2410 are named by FEAT-064 D-07/D-08. ADR-0015 names no person for P1–P4.
- The exact T7a/b/c source paths, schema, UoW method inventory, witness implementation and canonical migration owner remain unresolved.
- No Alembic runtime command or database was used. Counts are from static revision metadata only.
- No tests, backend service, database, MinIO, Modal or GPU operations were run. The four repository validators and whitespace checks are recorded in the completion report.
- This manifest does not establish model quality, end-to-end Child UI → BE1 → BE2 → Modal → Teacher behavior, or production readiness.

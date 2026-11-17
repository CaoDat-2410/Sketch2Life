# FR-C-08 M2 baseline snapshot — 2026-11-15

**Purpose:** Pin and reconcile the dirty/partial M2 worktree as the separate D-208 coordination gate. This is a file-state snapshot; it does not claim S2 complete, authorize reuse of M2 approvals/allowlists/command ceilings, or authorize FR-C-08 implementation.

## Observation

- Observed: 2026-11-15 16:16:55 UTC.
- Worktree: `.worktrees/m2-s2`; branch `feature/feat063-m2-s2`; HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.
- `git status --short`: 60 paths (24 modified, 36 untracked).
- Staged paths: 0.
- All listed paths existed in this observation. The entries include the two coordinator planning addenda already present at the start of this snapshot.
- Any later byte/hash/status difference is **changed since observation** and requires a fresh reconciliation before a future implementation launch. Nothing was reset or repaired.

## Complete dirty-path manifest

| Status | Bytes | SHA-256 | Worktree-relative path |
|---|---:|---|---|
| M | 6601 | `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` | `backend/src/sketch2life/application/ports/parent_story_runs.py` |
| M | 7889 | `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` | `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` |
| M | 69489 | `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` | `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` |
| M | 74637 | `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` | `backend/src/sketch2life/interfaces/http/app.py` |
| M | 17501 | `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF` | `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` |
| M | 23082 | `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` | `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` |
| M | 14626 | `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` | `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` |
| M | 13507 | `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` | `backend/tests/contract/test_app_composition.py` |
| M | 7358 | `AB3D9E98A81EEBD53EF65A526FDA6BC8F65CD37A6E4E0D20F82AE90EC66C2A14` | `backend/tests/contract/test_assistance_request_contracts.py` |
| M | 10748 | `73C286AB56CD14E26DC7EEA5D2FA3D4F73946F99F4F969C08FD73EFB32DED4E4` | `backend/tests/contract/test_assistance_requests_api.py` |
| M | 18753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` | `backend/tests/contract/test_openapi_contract_catalog.py` |
| M | 12286 | `FD2634034ABE6C22536D2D7C7DA5787772B91A9F4D4AAA81420B749D67248FAA` | `backend/tests/contract/test_parent_story_run_request_contract.py` |
| M | 4581 | `145F327DB6502667C2E6FC56305EF3DE736E556BAE2AE0C37677BBBA1C4DF46E` | `backend/tests/unit/test_parent_story_run_create_service.py` |
| M | 83919 | `B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D` | `docs/context/PROJECT_CONTEXT.md` |
| M | 116802 | `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` | `docs/context/SOURCE_REGISTER.md` |
| M | 4313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` | `docs/context/SRS_AUTHORITY.md` |
| M | 3023 | `67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063` | `features/FEAT-047-be1-runtime-backend/approvals/TASK_APPROVAL.md` |
| M | 9248 | `689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5` | `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` |
| M | 114989 | `CCBB9EEFA3AD0863C7BF6992490066BCD22CB837595EB7BDCE3BE5A50BB0F56E` | `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` |
| M | 216212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` | `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` |
| M | 68089 | `D426F1EAABE82A581355A786F7C62BDE5B43AA1FC095007CCC56D0A7CAEBB15D` | `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` |
| M | 410676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` | `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` |
| M | 639948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` |
| M | 113223 | `2395CCE2FC7AE7A54DE76D656716F1FA78E0D401DDF362829D28ED4A54A3B153` | `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md` |
| ?? | 3467 | `7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC` | `backend/tests/contract/test_parent_ai_late_result_guards.py` |
| ?? | 3601 | `98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE` | `backend/tests/contract/test_parent_story_run_cancel_route.py` |
| ?? | 10111 | `A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E` | `backend/tests/unit/test_parent_story_run_cancel_repository.py` |
| ?? | 13596 | `0CF2C87996252058544D5F943967AB9F3A4E7A292D28CF1F6413620BFA6D8871` | `features/FEAT-047-be1-runtime-backend/evidence/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_EVIDENCE_20261114.md` |
| ?? | 7886 | `235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B` | `features/FEAT-047-be1-runtime-backend/plan/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_DRAFT1_20261114.md` |
| ?? | 6561 | `A53485DBC019CF2E98211DBC272A30CFA2763AF09E580109BD0AB86DA85BA05E` | `features/FEAT-063-system-architecture-rearchitecture/evidence/BE_SESSION_CHECKPOINT_20261114.md` |
| ?? | 10047 | `83270D1A6FE19FAE42CB4C405A9DDB3B2298E181261C9B740F0DA9F0F5C26658` | `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_DRAFT3_COLD_REVIEW_20261115.md` |
| ?? | 4037 | `87A9D95FDB4C57E9CD064774F39129B1256957F67D367A9068BEEB4D225C29E3` | `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_DRAFT4_COORDINATOR_REVIEW_20261115.md` |
| ?? | 3084 | `9C6A39CD071DA247C3B7F484C7536ED84BDF33CEA2D3BAE3BDCFF0C56F23118F` | `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_DRAFT4_INDEPENDENT_COLD_REVIEW_20261115.md` |
| ?? | 7496 | `96361FA0AB97D7DB9E0E1CC5F328F5FB6704B8D0580F525676F732E0D9A3CB1D` | `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_PARENT_TEACHER_CANCEL_PURGE_ALLOWLIST_DRAFT2_COLD_REVIEW_20261115.md` |
| ?? | 6430 | `11EE49B390EAEA602BBA8364161CFB68A1FB4E0068CEF92388C17A205566C309` | `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_PARENT_TEACHER_CANCEL_PURGE_ALLOWLIST_DRAFT3_COLD_REVIEW_20261115.md` |
| ?? | 25879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` |
| ?? | 3456 | `D2C84E356C45653AB9973D94DFD09E4A8DB8439EA01BE4DA2D64B0849B80E5B2` | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md` |
| ?? | 2523 | `3BE67FE600CC556B36DC6C6BDDC735EC96C4BDA32C987404815896CD53937722` | `features/FEAT-063-system-architecture-rearchitecture/evidence/M3_M6_ROADMAP_DRAFT1_INDEPENDENT_REVIEW_CAPTURE_20261115.md` |
| ?? | 2537 | `B3AFCBD77E0DCACF73633F09A9CABC927D72AF2877B95A18F7A422A7978274B2` | `features/FEAT-063-system-architecture-rearchitecture/evidence/M3_M6_ROADMAP_DRAFT2_INDEPENDENT_REVIEW_CAPTURE_20261115.md` |
| ?? | 1600 | `59714ECA1C056FB10E76D6C3168B97FC7B4E21DE671EEBF8FBC52291E0A8AC4A` | `features/FEAT-063-system-architecture-rearchitecture/evidence/M3_M6_ROADMAP_DRAFT3_INDEPENDENT_REVIEW_CAPTURE_20261115.md` |
| ?? | 15811 | `7C2FEBE0898AE93B771CE1CD2F0DD2E88C1241656F057FAD89F7E82948DFEA05` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_IMPLEMENTATION_READINESS_ADDENDUM_DRAFT1_20261115.md` |
| ?? | 44643 | `82978E82A2A07A94007E7574BC43FA45663CA3B03D72FAEFDD24C15964D01800` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261115.md` |
| ?? | 56894 | `6D0A79408446A4D72A098965CCC78E7ED9FE5E0DE8D065C0DC1BCA1B3B347E70` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT2_20261115.md` |
| ?? | 62813 | `35DC6DD54D9170F670925D290B7788914EC383DF6EDCD0A797FBB98AAD279A00` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT3_20261115.md` |
| ?? | 65130 | `F4C76422DDE39A2B34A5364BC6F7F77B3A960331F4DBA00939082FBE54E3512A` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT4_20261115.md` |
| ?? | 37626 | `963A500A8DA0C5995E200467A5935C28819BEE5EA36B75F883E14C4D0EBB61F7` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT1_20261115.md` |
| ?? | 44378 | `4C4C905B19883C94C8E60109E9731B9289B5F4C31A780020DAD9420211EB7318` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT2_20261115.md` |
| ?? | 19897 | `1D680D04D1B06ED827F0FFD71A30D5E2C2AFC09828158997276D1F8424F37313` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT3_20261115.md` |
| ?? | 20897 | `BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT4_20261115.md` |
| ?? | 22501 | `2F879E24BCD50849B2CC826D5E6F510C9173C92C1595503F6BCDA0D40F045D9C` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT1_20261115.md` |
| ?? | 24996 | `300BEC5A0716B8CFC09896E52B9752F5D6EBF499C4BB86822A71AF9D29A41310` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT2_20261115.md` |
| ?? | 13246 | `832D3653A38BAF8E3D82D75C319D7BA275B7628510074932DF726F459EB8A95E` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT3_20261115.md` |
| ?? | 13871 | `483A228C65400016964F43C4C52082E49CAF232C49B8AB8E8E6692DB6E21B385` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT4_20261115.md` |
| ?? | 45462 | `500E622667F32D80C4361E91EC216578ED716F1AC9DE1FF6F154F213E47DAF9A` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT1_20261115.md` |
| ?? | 46791 | `567B28A6C85BD3BB8608C7B48D1F60CABC36B5AEA28E25D52784A11FB2BAC712` | `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT2_20261115.md` |
| ?? | 20784 | `48B7A95133BDEAB9D14EE947BAF44D5B475ED60B99D118EAC24B51C9E0561BD6` | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT1_20261115.md` |
| ?? | 7356 | `D3287B5E7AD57DB487407B2B4179819074BBD762C7FC900455627091D3C8BE7E` | `features/FEAT-063-system-architecture-rearchitecture/plan/M3_M6_SRS_ALIGNED_ROADMAP_ADDENDUM_DRAFT1_20261115.md` |
| ?? | 12869 | `9D0133539CA336F675B4AC924E21E8CA215EF2B1DF8FBE6000FF171888669AF2` | `features/FEAT-063-system-architecture-rearchitecture/plan/M3_M6_SRS_ALIGNED_ROADMAP_DRAFT1_20261115.md` |
| ?? | 19493 | `4BB75DABD291EE2D9E2ABF2C6B80A18BEF9700F195E471DEC231366EA5CAC663` | `features/FEAT-063-system-architecture-rearchitecture/plan/M3_M6_SRS_ALIGNED_ROADMAP_DRAFT2_20261115.md` |
| ?? | 22691 | `DC6AFE31344437E97D800450AEAD0BEE56EAF05B8FB1AA20E701126C71C47D88` | `features/FEAT-063-system-architecture-rearchitecture/plan/M3_M6_SRS_ALIGNED_ROADMAP_DRAFT3_20261115.md` |

## M2 evidence disposition

The pinned `M2_S2_IMPLEMENTATION_REPORT_20261114.md` records **PARTIAL / NOT COMPLETE**. It records an owner-reported targeted test run with 82 collected, 81 passed and 1 failed; a later authorized combined run exited 1 with an OpenAPI tag mismatch and a pytest temporary-path `WinError 5`; 335 mypy errors across 63 files; and 17 Ruff diagnostics. Those are historical report contents, not commands run for this snapshot. They remain non-passing or unavailable evidence; no results were rerun or converted to passes.

This snapshot closes only the **file-state reconciliation/pinning** portion of D-208 item 8. M2 remains partial. Any future FR-C-08 launch must name the exact pinned state it relies on, preserve these existing edits, recheck selected paths and obtain separate FR-C-08 approval and command ceilings. No implementation, test, typecheck, lint, validator, backend, database, migration, provider, Modal, staging, commit or push operation occurred in this snapshot task.


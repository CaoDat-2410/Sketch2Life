# Source register and authority boundary

## owner-feat065-ci-repair-20261029

Person 2 authorized “ok v sửa đi nào thấy ok thì đẩy lên” after reviewing CI run 40875382264 and the three scoped fixes. FEAT-065 records repair of Node CI pin, backend lock metadata and five missing evidence-directory placeholders, validation and publication on existing feature/modal-vision-dev only. This does not authorize product-flow implementation, new branches, service/DB/Modal calls, package installs or changes to other feature plans/approvals.

Focused validation exposed the stale composition-test route allowlist; FEAT-065 revision2 records maintenance against already approved FEAT-063 Lesson Library method/path inventory, preserving exact assertions and changing no runtime endpoint. Results and limitations are in FEAT-065 evidence.

## FEAT-063 complete API purpose catalog - current - 2026-10-28

Plan Rev32 (`features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV32_API_PURPOSE_CATALOG_20261028.md`, SHA-256 `FD189D3E2684CE2930624AFD7412C54F9BB53339209790F7B319B534C41E087C`) is approved for documentation-only work. The linked catalog (`features/FEAT-063-system-architecture-rearchitecture/artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md`, SHA-256 `E65582C197FCF9DC134294D140B5289C44B82E6A81AC6DB6C23C0AFE3800A881`) gives a concise purpose and runtime exposure for every one of the 135 current route declarations. It changes no API or runtime behavior. EV-063-25 records the catalog; no tests, Docker, database, provider, or deployment operation was performed.

## FEAT-063 Lesson Library backend and full API inventory - current - 2026-10-28

FEAT-063 Plan Rev31 and Addendum A are approved and implemented at source level. The reconciled Lesson Library contract exposes 30 operations (SHA-256 `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`); the full static inventory records 135 backend route declarations: 121 unconditional combined-app routes, 3 conditional local storage-example routes, and 11 candidate/fixture/unmounted declarations. Existing Parent/Teacher/BE1/demo routes were preserved. See `features/FEAT-063-system-architecture-rearchitecture/artifacts/API_INVENTORY_FEAT063_REV31_20261028.md`, the Rev29 contract with Rev31 reconciliation, and EV-063-24. No tests/builds, runtime, Docker execution, security validation, live database/migration, AWS/provider, or secret-file operation was performed. SRS v2.3 remains unsigned; 92 active + 48 legacy = 140 is a repository-derived crosswalk, not a live database result.

## FEAT-063 local Docker/MinIO storage example - historical Rev30 slice, incorporated in Rev31 - 2026-10-28

FEAT-063 Plan Rev30 (`features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV30_LOCAL_DOCKER_MINIO_STORAGE_EXAMPLE_20261028.md`, SHA-256 `F6BD755CBC543374AC9091BB7603C2A9EB83DC20F2EDCA92B2A10158AB88C794`) is APPROVED and IN_PROGRESS for the exact local scope recorded in `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`. It adds Docker wiring for the existing backend and a private local MinIO bucket plus one S3-compatible upload/read/delete example. It does not approve or implement the full Rev29 Lesson Library API. EV-063-23 records the evidence limits; no tests, builds, security validation, Docker pulls, Compose startup, database change, AWS operation, or actual `.env` edit has occurred.

## FEAT-063 backend API contract - historical Rev29 baseline, implemented under Rev31 - 2026-10-28

Plan Rev29 (`features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV29_BACKEND_LESSON_API_CONTRACT_AND_ENTITY_NAMING_20261028.md`, SHA-256 `B63B5BEC21C71BFD154EEA08741C167B3B144AF1133A17695D4C63E6760BCD6A`) and linked API contract (`features/FEAT-063-system-architecture-rearchitecture/artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`, Rev29 pre-reconciliation SHA-256 `81405D5BB6FC5FBAE50E8E73796FFABBC7C2E5B898C8BA7CEEF99AA3176407A2`; current Rev31 contract SHA-256 `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`) were a contract-only draft at the time; Rev31 and Addendum A later approved and implemented them. They distinguish domain entities, persistence tables and versioned HTTP DTOs and list every method/path, purpose, actor and request/response. EV-063-22 records the naming/contract review. Rev31 and Addendum A later approved and implemented the contract; see the current entry above.

## Historical backend lesson-platform plan — Rev28, superseded — 2026-10-28

Plan Rev28 (`features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV28_BACKEND_LESSON_LIBRARY_UPLOAD_REVIEW_PARENT_READ_20261028.md`, SHA-256 `22CBC9E4360B39BDD995B683B5B9681D962D3D1C54355F929F0B1C3BE2387FE6`) is preserved and superseded by Rev29. EV-063-21 records the owner's scope choices and library-upload data ownership gap. It was not approved for implementation. Plan Rev26 remains an independent AI/Modal research proposal.

## FEAT-063 initial backend CRUD recommendation — Plan Rev27, superseded — 2026-10-28

Plan Rev27 (`features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV27_BACKEND_BASIC_LESSON_CRUD_DRAFT_20261028.md`, SHA-256 `984B54DE505A4C86B9334079D6FC9086A0E5ABC9E1736C21BC0734096454E3BD`) is preserved as the initial narrow recommendation and superseded by Rev28. EV-063-20 records its read-only repository review. It was not approved for implementation.

## FEAT-063 platform lesson library and sharing — current source — 2026-10-28

The current full product SRS is features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md v2.3-draft, with DATA_TABLE_REGISTER.md v2.3-draft. Plan Rev25 is approved for this documentation-only amendment (SHA-256 90EDB84AE60864740A64863423F7F9C72052AFE757ED7427360FC6A29D8AB621); it does not sign off the SRS/register content or authorize implementation.

Owner answers 1–49 are traced as Q147–Q195. The platform layer adds reusable Montessori lessons, school-organization tenancy, scoped/revocable roles and child-profile sharing, filtered lesson authoring, visibility/publication, Parent history/feedback and school/Teacher/Parent quota. It preserves the existing Parent and Teacher flows and video pipeline. Parent outdoor activities appear after video; Parent and Teacher line-sketch generation is opt-in during the active session. The v2.3 draft baseline is 89 active + 48 legacy = 137 physical tables. Rev31 adds three Lesson support tables, yielding a source-derived 92 active + 48 legacy = 140 implementation crosswalk; neither is a live database result.

The prior v2.2 SRS and Data Table Register are preserved under FEAT-063 artifacts with PRESERVED_20261028 filenames. ADR-0022 is proposed and does not lock a stack/provider. Remaining decisions and authority boundaries are recorded in FEAT-063 status and evidence. No product implementation, database/migration, provider call, test/build, deployment or real-child processing is authorized.

## FEAT-063 AI model and Modal flow reassessment — pending approval — 2026-10-28

The owner requested research and candidate recommendations for Modal-hosted AI flows. Evidence is `features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md` (EV-063-19). Plan Rev26 (`features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV26_MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md`, SHA-256 `ECD0A0A6435193A903313409B699574FE9DB30BAAB8498A714A3FC54C75EEABC`) awaits approval. This is a research proposal only: v2.3 remains the canonical SRS/register; no model is selected, and no SRS amendment, Modal call, model benchmark or product implementation has been authorized or performed.

## Historical FEAT-063 Parent AI line-sketch clarification — 2026-10-28

At the time of this historical entry, the full product SRS was `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.2-draft, with its matching `DATA_TABLE_REGISTER.md` v2.2-draft. Plan Rev24 is approved for the documentation amendment: Q146 records an optional Parent AI line-sketch guide using generic topic/difficulty only, temporary private output and separate sketch compute/rate caps; Q145's interim text-only interpretation is superseded. Teacher Deck was then treated as a main-flow step; Q167 in the current v2.3 SRS supersedes that status and makes generation session-opt-in. FEAT-062's former SRS questions are retired and its SRS file redirects here. The Markdown SRS/register remain unsigned; no product implementation is authorized by this record.

## FEAT-058 Review 2 Rev22 FPT cover restoration — 2026-10-26

The owner supplied `the locally retained owner-provided cover reference` as a cover reference (SHA-256 `b91be4aa3b03146988b96b3a8cc7b94af4d627ab7735c2d998f103c14bd87fe7`). Approved Plan Rev22 SHA-256 is `568395bfe8b5a8ed235154373c4d49ee4c1b45c21f7bd14bc9fc7e1d8cfc7da7`. The Review 2 package is under `features/FEAT-058-review2-document-package/artifacts/submission_r2_rev22/` (6/9/102/4 PDF pages). The official FPT lockup was restored byte-for-byte from the source; report pages 2–102 are pixel/text identical to Rev21 and three other dossier pairs are byte-identical. Report DOCX SHA-256 `59b0ddea42a2879452a77027ed4a45f7978453c945f4b6fe11f891ed38d56ec3`; PDF SHA-256 `a9f252b638644b4f9c8cc6e045ce3593c6ee46a005cca9e4b5018c1889eefa84`. Provenance and visual QA are feature-local in FEAT-058.

## Historical FEAT-058 Review 2 Rev21 pricing update — 2026-10-26

The owner supplied `the locally retained owner-provided pricing reference image` (SHA-256 `FE4D5FC34DE16B24C2540A88266421C7BC06EE82F875058B53A649C546CC53C4`) and requested a pricing/package update. Approved Plan Rev21 SHA-256: `D7C3A1292385E8D7CB785ADF160A6A61ACDB39431CB026D004AD7B50CC97E317`. Rev21 output was `features/FEAT-058-review2-document-package/artifacts/submission_r2_rev21/` with 6/9/102/4 PDF pages; three dossier pairs match Rev20 byte-for-byte. Report page 38 contains the exact image values and the five-step adult billing flow. All monetary amounts remain PROPOSED; Child Android has no checkout prompts; billing remains NOT IMPLEMENTED. Hashes and rendering/page-flow evidence are feature-local.

## FEAT-029/FEAT-039 Master SRS v3.5 — 2026-10-26

Plan `features/FEAT-029-master-srs/plan/PLAN_B29_SCHOOL_PACKAGE_UPDATE_SRS_V3_5_20261026.md` SHA-256: `BBF1CBAF2E1BAF21A260203A21908607EACAE7EEB746AD41C11116D166D95F38`. Canonical FEAT-029 SRS and FEAT-039 `Collaborative_Learning_SRS_v3.5.md` match byte-for-byte (SHA-256 `2FA7BCB91C821DABD239A4331E7A68DBC9E4740DA25805657CD7FED5E4C89FA7`). B29 baseline quantities now match the owner's package image; only monetary amounts remain PROPOSED, and implementation remains NOT IMPLEMENTED. Exact v3.4 is preserved unchanged with SHA-256 `07EE7D5BB4AC7FE1A3AA0D35050B60CD6EFD3AE09234FCEA6205F92A18012090`.

## FEAT-026 English-only SRS derivative — updated 2026-10-26

The owner requested an ASCII-named English-only SRS derivative, team members in the introduction, a centered title containing “AI for Children”, proofreading and consistent typography. The current approved Plan Rev2 SHA-256 is `E6997F69580102319E1556A2975A5DE904408457746DA9A68D96C6F1BFB39A42`; all editable runs use Arial 10 pt. Original Vietnamese source `features/FEAT-026-current-system-srs/artifacts/Sketch2Life_SRS_Form.docx` remains unchanged (SHA-256 `08f43d867cdb6a30c05440223b9f015a02f5c3f3c2adacd1ede9f29b28b151a6`). English output DOCX SHA-256 `CFAF85FA4923A0B26228EE95A2980C31BEEDAE085C167567F82CE4C2C53DF037`; PDF SHA-256 `88EE851CD8B5688C3B10EE0EC3B64E913BDCDAA430DEA17D204C938ABC559DC0` (13 pages). The footer-only page before Appendix A was removed and visual QA refreshed. The derivative is separate from the canonical FEAT-029/FEAT-039 Master SRS.

## FEAT-058 Review 2 Rev20 package remediation — 2026-10-25

Approved Plan Rev20 SHA-256: 5A1DBC7D07A40EE6D493CEB00741C6C835F09886414838A73DD68524E4D46672. The user-supplied review text is recorded at the locally retained owner-provided review text (SHA-256 3AB006819CA07AE826EC93E1EE1006B9159F8839F7A07CABD025EE7033323D4A). Rev20 restores the BM03 Record of Changes in the Registration derivative, removes report D02 C4 while retaining D01 Business Context, and repairs page flow for D24/D29/D38 (former pages 51/66/73 to Rev20 pages 54/70/77). The four local DOCX/PDF pairs are under features/FEAT-058-review2-document-package/artifacts/submission_r2_rev20/ with 6/9/102/4 pages, 121 total. The Registration source remains unchanged; three pairs are byte-identical to Rev19. Hashes and QA are in the feature source register, evidence/metrics/rev20-package-qa.json and evidence/REV20_FORMAT_AND_PAGEFLOW_QA_20261025.md.

## FEAT-026 English-only SRS derivative — 2026-10-26

The owner directly requested an ASCII-named, English-only SRS derivative, team members in the introduction, a centered title containing “AI for Children”, proofreading and consistent typography. See the refreshed FEAT-026 entry above for current plan/output hashes and page-flow QA. The four listed members and roles come from the registered project records and FEAT-058 D06: Do Cao Dat, Pham Tan Hieu, Vu Chi Bao and Ly Anh Khoa; supervisor Lam Huu Khanh Phuong. The derivative does not replace the canonical FEAT-039/FEAT-029 SRS. QA receipts and source attribution are in FEAT-026.

## FEAT-058 Review 2 Rev19 format and page-flow remediation — 2026-10-25

The owner supplied format-review text at `the locally retained owner-provided review text` (SHA-256 `3AB006819CA07AE826EC93E1EE1006B9159F8839F7A07CABD025EE7033323D4A`) and directly requested restoration of BM03 Record of Changes, removal of D02 C4 while retaining D01 Business Context, and page-flow repair around report pages 51/66/73. Approved Plan Rev19 SHA-256: `502E5CD0ADF6D6848BD632225ED07FA64FD54E753FA9A6873A2CAED310BF9104`.

Rev19 outputs: `features/FEAT-058-review2-document-package/artifacts/submission_r2_rev19/`, exactly four DOCX/PDF pairs (PDF pages 6/9/99/4; total 118). Registration BM03 was restored from the preserved pre-Rev18 derivative; source Registration v1.2 and earlier revisions were not modified. The report now uses Arial, 10 pt body, 8.5 pt data-table text and 8 pt TOC; D01 remains and D02 is absent. The full TOC precedes the report body. Original Rev18 figure pages map by content to Rev19: D24 p51→p52, D29 p66→p68, D38 p73→p75. Rendered-page inspection, audit results and output hashes are in `features/FEAT-058-review2-document-package/evidence/REV19_FORMAT_AND_PAGEFLOW_QA_20261025.md` and `evidence/metrics/rev19-package-qa.json`. All files, Registration contact data and rendered pages remain local. No application test, runtime edit or Git publication action occurred.

## FEAT-039 SRS classroom-integration amendment — 2026-10-23

Owner requested that the integration corrections be recorded in the SRS. Documentation-only FEAT-039 Plan Rev4 is approved and preserves v3.1 byte-for-byte (`features/FEAT-039-collaborative-learning-scope/artifacts/Sketch2Life_Master_SRS_v3.1_preserved_20261023.md`, SHA-256 `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9`). The SRS is now v3.2 in both current copies (FEAT-039 consolidated artifact and FEAT-029 canonical master). The owner confirmed: the shared six-digit code is reusable by the class; QR/deep-link and code both stop accepting new joins after Teacher starts; existing admitted children keep their grants; terminal outcome distinguishes full completion from Teacher stopping early. Pending requests at the start boundary and exact API/schema/guard requirements remain for BE1 review. Persisted stage/API/schema details remain unadopted. FEAT-060 Plan Rev3 remains DRAFT. No product runtime/source, database, application test, provider, Modal, deployment, or Git publication action is part of this amendment; the documentation composer/checker paths were updated for v3.2.

## FEAT-058 Review 2 documents and refreshed Child UI source — 2026-10-23

The owner directed that the newly pushed `FE_UI_Child` be fetched and merged before completing the Review 2 document package. The refreshed `origin/FE_UI_Child` source is `ca3779869dfc1385cbbc7b8ca730f780386af7b2`; merge commit `0a7ce768c153f2104cff930569c3eda6e484532c` is the final local `dev` source baseline for the report. It adds `apps/child-ui` (Expo SDK 55 / React Native 0.83.10). Its API client and session verifier are stubbed and screens use local fixtures; UI source presence does not establish service integration. The earlier `FE_UI_Child` no-op at the BE1 base is superseded.

Owner scope: create one consolidated English course report (Reports 1–5 and Project Tracking), a separate English BM01 Design Brief, and (revision 4) a standalone official-template Report 2 Project Management Plan. The registration v1.2 controls the product scope. The required `review-2` tag and Modal deployment configuration remain TBD at the owner's direction. Source evidence and outputs are in `features/FEAT-058-review2-document-package/`. No push, deployment or application test run is implied by this entry. Final DOCX/PDF outputs are locally available: consolidated report 25 pages, standalone Report 2 eight pages, and BM01 six pages total with sections 0–8 in four pages and Appendix A in two. All 39 final pages were visually reviewed; hashes/structural checks are recorded in `features/FEAT-058-review2-document-package/evidence/metrics/final_package_qa_20261023_rev4.json`. No application test was run for document authoring; FEAT-059 local checks remain separate bounded evidence.

## FEAT-058 Report 2 form and time-plan revision — 2026-10-23

The owner asked for closer adherence to the course forms and a separate Project Management Plan. The user-supplied Review 2 guide matches the previously registered input (`SWP490_R2_Huong-dan-chuan-bi-Review-2_1.pdf`, SHA256 `5c8b8c96d44edfd61336bacb0e4fe58bfec0d966e64a777ece628f9f6740bc7`); the latest registration attachment matches the prior v1.2 source (SHA256 `0c52809dfc24bacfe6d3f5e02f0f3150ba5453d999dabf739b2eadfeafbad5df`). Additional primary course references: `2_SEP490/Report2_Project Management Plan.docx` (SHA256 `f59a4ce96d99f2f772f4c0ef07828812674aee4b8795aac475d5a395a8401be5`), `2_SEP490/Report2_Sample Project Schedule.pdf` (SHA256 `6261334f3223e32f56ec34a373c98efd14ee09d7d187fce26db8897d00af9464`), and `2_SEP490/Project Weekly Report_GroupName.xlsx` (SHA256 `ac9596ed4d005766cfe04ad41754e5a2942033e9100b54f6cc3a7ac7e0d2e04b`). They remain local originals; none is modified.

Owner answers: use a relative 15-week schedule, include draft person-day estimates pending group confirmation, and describe feature-based Agile with weekly review/CI. Week numbers and the 252 person-day effort are proposals; exact course dates/capacity are not in the source forms. Reference research checked on 2026-10-23: the official [Agile Manifesto principles](https://agilemanifesto.org/principles), [Scrum Guide 2020](https://scrumguides.org/scrum-guide.html), and [GitHub Projects documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects). These sources inform process descriptions only; no formal Scrum adoption or configured GitHub Project board is claimed. The Report 2 template was restored byte-for-byte from the pristine duplicate after a Word field-refresh operation changed the supplied copy; supplied, duplicate and evidence copies now share SHA256 `f59a4ce96d99f2f772f4c0ef07828812674aee4b8795aac475d5a395a8401be5`. Revision 4 outputs and QA are complete under feature evidence.


## Owner-supplied Rev5 review result and FEAT-057 offline test request — 2026-10-21

Sources: (1) the owner-pasted separate-session Rev5 review report, PASS_WITH_NOTES with no P1/P2 and seven P3 notes; the report remains in the reviewer transcript and is not hash-pinned; (2) the owner's request to test the BE2-01–07 to BE2-08–14 offline connection. Record: FEAT-057 evidence/notes/BE2_INTERNAL_OFFLINE_TEST_RUN_20261021.md and raw JUnit under evidence/raw/be2_internal_offline_test_20261021/. Authority boundary: run existing offline tests and record their result only. The test run does not extend any card-owned execution manifest or approve new source/test/schema edits. X01 stays PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. No provider, database, server, Modal, Lightning or runtime action was taken.

## FEAT-057 re-review of revision 4 and owner request for revision 5 — 2026-10-21

Sources: (1) a read-only re-review of the revision-4 frame run in a separate session, verdict `PASS_WITH_NOTES` with four P3 notes (the report is in that session's transcript, not a repository file); (2) the owner's direct instruction in this conversation to create a successor from the exact Rev4 bytes that handles those notes, changing FEAT-057 plan and evidence only. Record: `features/FEAT-057-be2-01-14-offline-integration/plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_REV5_DRAFT_20261021.md` and its manifest `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV5_20261021.json`. Authority boundary: FEAT-057 documentation only. A note addressed in draft text does not close an owner gate, and `PASS_WITH_NOTES` approves no code. No production source, test, approval, other-card record, card status/acceptance, runtime action or Git operation is authorized; no implementation may start from this revision.

## FEAT-057 re-review of revision 3 and owner request for revision 4 — 2026-10-21

Sources: (1) a read-only re-review of the revision-3 frame, verdict `PASS_WITH_NOTES` with three P3 notes, run in the session that wrote revision 3 and reported in chat (no report file); (2) the owner's direct instruction in this conversation to create a successor from the exact Rev3 bytes that handles those notes, changing FEAT-057 plan and evidence only. Record: `features/FEAT-057-be2-01-14-offline-integration/plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_REV4_DRAFT_20261021.md` and its manifest `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV4_20261021.json`. Authority boundary: FEAT-057 documentation only. A note addressed in draft text does not close an owner gate, and `PASS_WITH_NOTES` approves no code. No production source, test, approval, other-card record, card status/acceptance, runtime action or Git operation is authorized; no implementation may start from this revision.

## FEAT-057 re-review of revision 2 and owner request for revision 3 — 2026-10-21

Sources: (1) an independent re-review of the revision-2 frame, verdict `PASS_WITH_NOTES` with nine P3 notes, as relayed in the owner's instruction (the report file is not in this worktree); (2) the owner's direct instruction in this conversation to handle those notes and prepare an approvable implementation scope table, changing FEAT-057 plan and evidence only. Record: `features/FEAT-057-be2-01-14-offline-integration/plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_REV3_DRAFT_20261021.md` and its manifest `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV3_20261021.json`. Authority boundary: FEAT-057 documentation only. A note addressed in draft text does not close an owner gate or turn into an owner decision, and `PASS_WITH_NOTES` approves no code. No production source, test, approval, other-card record, card status/acceptance, runtime action or Git operation is authorized; no implementation may start from this revision.

## FEAT-057 review 1 of the full BE2 graph plan and owner correction request — 2026-10-21

Sources: (1) an independent read-only Claude review of the revision-1 frame, verdict CHANGES_REQUIRED, preserved at `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_END_TO_END_FRAME_REVIEW1_REPORT_20261021.md`; (2) the owner's direct instruction in this conversation to resolve all 5 P2 and 8 P3 findings in a successor plan and update the FEAT-057 manifest and ledgers. Record: `features/FEAT-057-be2-01-14-offline-integration/plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_REV2_DRAFT_20261021.md` and its manifest `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV2_20261021.json`. Authority boundary: FEAT-057 documentation only. A review finding addressed in draft text does not close an owner gate. No production source, test, approval, other-card record, card status/acceptance, runtime action or Git operation is authorized; no implementation may start from this revision.

## FEAT-057 owner request: full BE2 graph plan — 2026-10-21

Source: the owner's direct request in this conversation to check the current state and prepare a complete integration frame for BE2-01–07 and BE2-08–14. Record: `features/FEAT-057-be2-01-14-offline-integration/plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_DRAFT_20261021.md`. Authority boundary: planning only; the approved FEAT-057 Rev2 offline composition scope remains governing, missing/unadopted card contracts remain blocked, no per-card scope/approval/status is changed, and no source/test/runtime or Git publication is authorized by this request.

## FEAT-057 preliminary BE1 handoff package — 2026-10-21

The owner asked Codex to prepare a preliminary handoff with current evidence and blockers. The local note `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/BE1_PRELIMINARY_HANDOFF_20261021.md` is `NOT_SENT`; exact input bytes are pinned by `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/BE1_PRELIMINARY_HANDOFF_INPUTS_20261021.json`. It permits factual status/adoption review only, not external contact, implementation approval or a claim of connected flow. X01 remains PARTIAL; X05 is NOT_IMPLEMENTED, X05d BLOCKED, X05c/CR09-02 OPEN and X09-08 NOT_IMPLEMENTED. The 296/296 Modal result is a selected offline CPU package only. Current branch tip is `1649b729`; its 143 dirty paths were not published.


## Claude D3 rereview 4 and D4 authority gate - 2026-10-21

The owner-provided independent Claude report is preserved in FEAT-057 evidence/notes/CROSS_LANE_UOW_CLAUDE_D3_REREVIEW_REPORT_20261021.md, SHA256 92BE229378A2DE06BAEED1FC6F675EA15FED338892A002A833F81F6972B44C12. It verified all 81 manifest hashes, closed the previous P2 findings in draft, and raised one new P2 plus four P3 corrections.

D3 C1-A/C2-A remain direct owner design decisions. Latest candidates are FEAT-044 foundation Rev7, budget CR Rev2 and stale CR Rev2; BE2-08/14 scopes Rev3; FEAT-057 slice Rev8. NEW-1 at completion-time BUDGET_EXCEEDED remains pending in the D4 ballot. The other P3s are clarified in drafts; hashes do not establish adoption or implementation.

No implementation approval, tests, acceptance or runtime authority is inferred. Earlier checkpoints and source entries remain historical.


## Owner D3 source and authority - 2026-10-21

owner-be20114-uow-d3-20261021 is the direct owner message selecting C1-A/C2-A with conditions preserved in FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md, SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C. It authorizes design disposition and scope/CR preparation, not source/schema/test implementation, supplemental approval, BE1 artifacts adoption, acceptance or runtime.

Latest candidates are FEAT-044 foundation Rev6 plus joint BE2-01/14 budget CR, separate BE2-01 schema CR and stale CR; BE2-08/14 scopes Rev2; FEAT-057 slice Rev7. Independent rereview is pending. Per-file hashes identify dirty checkout bytes, not integration/adoption. The BE1 packet is prepared and NOT_SENT. Budget values/max duration/deadline action remain pending.

Earlier entries below retain historical authority boundaries; only the ballot's PENDING C1/C2 design response is superseded.


## Current checkpoint: Claude rereview 3 — 2026-10-21

Source: user-pasted Claude rereview 3 preserved in FEAT-057 evidence/notes/CROSS_LANE_UOW_CLAUDE_REREVIEW3_REPORT_20261021.md, SHA256 80EB2B425A790BC4B9E8958C9ADB0576B639162458BD0153592749DEE5C5ADC0. Verdict CHANGES_REQUIRED, no P1. Source manifest Rev4 pins 30 source files and one contract-test source read, not run. The correction specification and D3 ballot are design proposals awaiting owner C1/C2 responses; they are not direct owner authority or implementation approval. D1/D2 remain authoritative within their recorded design scope.

Earlier source entries retain their original historical authority boundaries.


## FEAT-057 shared lifecycle UoW owner decision — 2026-10-21

`owner-be20114-shared-uow-d1-20261021`: direct owner decision in this
conversation, recorded in FEAT-057
`evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md`. Selects paired
A/S/B/F boundaries with BE2-01 owning each UoW and BE2-08 as a non-committing
participant on its rows; reconciliation/outbox job mutations cannot bypass the
participant; rejected finalization writes quarantine/cleanup intent in a
separate foundation reject commit; infrastructure-only rollback needs recovery;
proposed lock order is job → run → source-fence rows by stable key. Authority is
design direction and documentation/review only. S/F need independent review and
separate supplemental approvals before source changes; no implementation,
acceptance, publication, database, Modal, Lightning, provider or runtime action
is granted. X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 open; budget unit/limit not
provided. Current slice-plan revision 4 has not been amended.

## Isolated offline test environment approval — 2026-10-20

The owner separately authorized an ignored Python 3.12 venv in the FEAT-057 integration worktree using the backend [dev,image-admission] profile. Record: features/FEAT-057-be2-01-14-offline-integration/approvals/LOCAL_ENVIRONMENT_APPROVAL_20261020.md. This covered local dependencies for the BE2-08–14 offline baseline only. SQL/PostgreSQL execution, provider/HTTP, runtime, Lightning/Studio and Git publication remain outside that approval. Final result: features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/GOAL_OFFLINE_BASELINE_FINAL_20261020.json.


## BE2 primary-session handoff continuation authority — 2026-10-20

owner-be20114-handoff-sync-20261020: direct user request continuing approved
FEAT-057 offline integration. Authorizes current-versus-historical handoff
synchronization, remaining dependency-available offline checks and bounded
reproducible offline integration fixes. Request SHA256:
`8383f77304e2b4186ce602ce21cdc2990181f74dbb0803a0fb41e5bc54f1b21b`.
No Lightning/Studio/provider/app/service/HTTP/DB/Redis execution, installations,
credentials, acceptance change or Git publication. See FEAT-057's primary
session handoff and F057-H01 follow-up evidence; original card approvals remain
authoritative and unchanged.


## BE2-01–14 runtime-readiness analysis authority — 2026-10-20

owner-be20114-runtime-readiness-20261020: direct user instruction recorded in
FEAT-057 `approvals/TASK_APPROVAL.md`. Authorizes reading the 14 task records and
preparing a staged command/readiness runbook for use after Lightning is operating
normally. This step is analysis/documentation only: no Lightning/provider/service
execution, installation, database provisioning/migration, adapter implementation,
or card acceptance. Actual execution remains subject to the exact source,
environment, feature approval, and owner-adoption gates documented by each card.

## BE2-01–14 offline integration authority — 2026-10-20

owner-be20114-offline-integration-20261020: direct user instruction in this
conversation, with PR target clarified as feature/be2-01-07. Authorizes a new
candidate branch combining the published BE2-01–07 and BE2-08–14 snapshots and
offline integration/testing. Live testing is deferred until Lightning operates
normally. It does not authorize dev/main merge, deployment, runtime adoption,
or full-card acceptance.

## BE2-07 owner offline acceptance and integration — 2026-10-20

`owner-be207-offline-acceptance-20261020`: direct conditional user instruction quoted verbatim in
FEAT-056 `approvals/COMPONENT_ACCEPTANCE.md`. Once the final review passed, it authorized accepting
KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE and a normal update/push of `feature/be2-01-07` with the reviewed
BE2-07 snapshot. It does not authorize dev/main, other branches, BE2-08–14, runtime/Lightning,
deployment or full-card completion.

## BE2-07 cloud P3 follow-up authority — 2026-10-20

`owner-be207-cloud-p3-20261020`: direct "Ok làm đi" after the five-step follow-up proposal;
recorded in FEAT-056 approvals/P3_CLOUD_FOLLOWUP_APPROVAL_20261020.md. Authorizes the two P3
corrections, local checks/review and focused publication; export cleanup is conditional on
archiving actual cloud files. User-pasted cloud summary is an input; actual raw report/index
are pending receipt. Component acceptance and runtime/Lightning are not granted.

## BE2-07 publication authority — 2026-10-20

`owner-be207-publication-20261020`: direct user instruction quoted in FEAT-056
`approvals/GIT_PUBLICATION_APPROVAL_20261020.md`. Authorizes the proposed 12 commits, task branch
push and Claude cloud review session/prompt. Supersedes the previous Git restriction for this
task; does not grant component acceptance, runtime/Lightning, PR/merge or deployment authority.

## BE2-07 execution authority — 2026-10-19

owner-be207-execution-20261019: direct user instruction quoted in FEAT-056 approvals/TASK_APPROVAL.md; approved plan revision 1 SHA2566de3ed6d… and OD01–08. Scope: complete offline eight-part implementation/review/tests; no owner acceptance, publication or Lightning execution.


## BE2-07 offline-first planning — 2026-10-19

owner-be207-planning-20261019: direct user request quoted in FEAT-056 approvals/TASK_APPROVAL.md.
Authority is planning the sourced knowledge/script offline component and later01–07Lightning
campaign. Planrev1/OD choices await owner; no test/code/publication/runtime acceptance. Fresh
identifier inventory/ownbranch creation follow existing per-task workflow;056 is administrative,
not an explicit owner number or lane08–14 confirmation. Task06merge receipt records actual
mergedPR15 at23acf9e. Source artifacts and independent code/contract audits inform proposals,
not implementation authority. Preserve oldparked07draft e64d25b7 and existing01–06 evidence.


## BE2-06 owner offline acceptance — 2026-10-19

`owner-be206-offline-acceptance-20261019`: direct user instruction quoted verbatim in
FEAT-055 `approvals/COMPONENT_ACCEPTANCE.md`; accepts CHILD_RESPONSE_COMPONENT_OFFLINE on
Codex PASS_WITH_NOTES. Authority is offline component acceptance and preparation of a
publication plan for review. Card remains IN_PROGRESS / NOT_DONE; runtime/integration remain
open. No stage/commit/push/shared-branch update/merge/deploy or next-card approval inferred.
The earlier implementation review and metrics remain byte-identical historical evidence.

## BE2-06 implementation evidence — 2026-10-19

`codex-be206-offline-review-20261019`: FEAT-055 implementation evidence, metrics, independent review and35case assertion audit bind15506passingtests and the1322pass/3skip final01–06snapshot. B6-CR01P2 found and closed. Authority is verification of the approved offline scope only; not owneracceptance, Git publication or runtime/integration approval. Deferredruntimechecklist is a future gate inventory, not an executed result.

## BE2-06 execution authority — 2026-10-19

`owner-be206-execution-20261019`: direct user instruction quoted in FEAT-055 approvals/TASK_APPROVAL.md; use the prepared Rev5 prompt to implement/test offline, with deferred Lightning batch. Scope and interpretation are explicit there; no publication/runtime acceptance inferred. FEAT055 is an administrative collision adjustment after fresh054 inventory; no teammate confirmation claimed.

The files below are reference inputs. Their contents inform context and proposed architecture, but they do not override direct user instructions or grant permission to implement unapproved work.

| ID | Source | Type | Used for | Authority in this repo |
|---|---|---|---|---|
| `owner-be210-11-13-local-postgres-20261019` | Actual direct "duyêjt" after explicit proposed42 actual own SQL tests (10:14,11:17,13:11), isolated environment/scoped fixes/cleanup/report/commit; each feature approvals/LOCAL_POSTGRES_APPROVAL.md and environment plan | Separate scoped environment approval | Fresh portable PG17 cluster, three limited-owner disposable loopback DBs, exact tests/evidence/regression/cleanup and scoped commit | No shared/prod DB, global service/install/PATH, actual BE1/P4 adapters/provider/Lightning/GPU, production mounting/push/merge/deploy or full-card sign-off |
| `owner-be213-revision1-approval-20261019` | Actual direct "duyệt" following exact FEAT-054 revision1 P1–P4 presentation; approvals/TASK_APPROVAL.md | Scoped implementation approval | Complete internal13 code/local verification/handoff/scoped commit continuously | Frozen601afab8 plan; no actual SQL provisioning/provider/Lightning/teammate wiring/scheduler activation/production mount/push/merge/deploy/full-card acceptance |
| `owner-be211-revision1-approval-20261019` | Actual direct "duyệt" following FEAT-053 exact revision1 P1–P4 presentation; approvals/TASK_APPROVAL.md | Scoped implementation approval | Complete internal11 code/local verification/handoff/scoped commit continuously | Frozen09348e0f plan; no actual SQL provisioning/provider/Lightning/teammate wiring/production mount/push/merge/deploy/full-card acceptance or13 activation |
| `owner-be210-revision1-approval-20261019` | Actual direct "duyệt" after exact FEAT-052 revision1 P1–P4 presentation; approvals/TASK_APPROVAL.md | Scoped implementation approval | Finish internal10 component/code/local tests/handoff/checkpoint commits continuously | Frozen8d0162c6 plan; no actual SQL provisioning/provider/Lightning, teammate wiring, production mounting/push/merge/deploy or full-card acceptance |
| `owner-be209-local-postgres-20261018` | Actual direct chat "duyệt" after isolated temporary PG17/SQL21/fix/cleanup/report request; FEAT-051 approvals/LOCAL_POSTGRES_APPROVAL.md | Separate scoped environment approval | Own09 actual21 SQL tests, new loopback disposable cluster/limited DB, cleanup and checkpoint | No shared/prod DB, global service/install, provider/Lightning/GPU, actual teammate adapter adoption, push/merge/deploy or full-card acceptance |
| `owner-be209-revision1-approval-20261018` | Actual "duyệt" following exact FEAT-051 revision1/P1–P4 presentation; approvals/TASK_APPROVAL.md | Direct implementation approval | Owned09 P1–P4, local tests and scoped checkpoint commits | Supersedes planning-only gate; no actual provider/SQL environment, teammate wiring, push/merge/deploy or full-card acceptance |
| `owner-be209-planning-batch-20261018` | Actual chat "duyệt" after inspect09/prepare-plan-first and delayed Lightning proposal; FEAT-051 | Direct routing/planning approval |09 requirements/plan, component-first and later combined runtime checks | No approval of unseen revision1 implementation, provider/model/budget/SQL environment, push/merge/deploy or full08/09 acceptance |
| `owner-be208-local-postgres-20261018` | Actual chat "duyệt" after separate08 PostgreSQL environment request; FEAT-050 approvals/LOCAL_POSTGRES_APPROVAL.md | Direct scoped environment approval | Disposable local PG17, own11 SQL tests, exact temporary cleanup and checkpoint | No shared/prod DB, provider/GPU/model/Lightning, teammate integration, push/merge/deploy or full-card acceptance |
| `owner-receiver-be208-approval-20261018` | Actual chat "duyệt làm task 08" following revision1 presentation/scope review; FEAT-050 approvals/TASK_APPROVAL.md | Direct task approval | Revision1 P1–P4/P5 preparation, local checkpoint commits | Approved scoped implementation; actual provider/profile/provisioning/SQL environment gated separately; no push/merge/deploy or integration sign-off |
| `owner-receiver-be208-planning-20261018` | Actual chat "tiếp" following proposal to inspect07 and prepare08 plan; FEAT-050 plan/PLAN.md revision1 | Direct planning request | Dependency inventory and next-card plan on feature/be2-08-14 | Planning only, implementation NOT_STARTED; exact plan approval pending; no provider/profile/provisioning/SQL environment, push/merge/deploy or owner integration acceptance inferred |
| `owner-receiver-be214-approval-20261017` | FEAT-049 approvals/TASK_APPROVAL.md, plan revision 1 SHA256 b5e7db68; actual chat reply "duyệt" | Explicit owner acceptance following revision-1/P1–P5 approval request | BE2-14 scoped implementation, tests and checkpoint commits on feature/be2-08-14 | Card-local P1–P5 approved; no production values/provider selection, real owner sign-off, isolated PostgreSQL provisioning, push/merge/deploy inferred; supersedes preparation-only state below |
| `owner-receiver-be214-planning-20261017` | FEAT-049 approvals/TASK_APPROVAL.md, plan/PLAN.md; FEAT-048 owner integration deferral | Actual user request "tiếp tục task tiếp" after BE2-14 planning proposal | Prepare next card on feature/be2-08-14; preserve BE2-12 handoff and deferred teammate integration | Planning only; P1–P5 pending approval; no BE2-14 implementation, real integration PASS, provider/runtime activation, push/merge/deploy authority |
| `owner-be205-offline-acceptance-20261019` | `features/FEAT-052-be2-sketch-review/approvals/COMPONENT_ACCEPTANCE.md` (verbatim) + Codex re-review note/metrics | Direct user acceptance in this Codex conversation, based on PASS_WITH_NOTES | Accept `SKETCH_REVIEW_COMPONENT_OFFLINE` only | BE2-05 remains IN_PROGRESS / NOT_DONE; runtime, production, persistence/SQL, BE1, BE2-14 and integration remain open; no Git publication or next-card approval |
| `owner-be205-publication-20261019` | FEAT-052 `DECISIONS.md` (verbatim instruction) + `evidence/notes/BE205_PUBLICATION_PLAN_20261019.md` SHA256 0ad3c5a3… | Direct user authorization in this Codex conversation | Execute 20 planned commits on the task branch; fast-forward and push `feature/be2-01-07`; then prepare BE2-06 plan only | No force push; verify actual remote tip; no runtime/integration closure and no BE2-06 code approval |
| codex-be205-rereview-20261019 | FEAT-052 evidence/notes/BE205_CODEX_REREVIEW_20261019.md + metrics | Independent Codex review of the approved offline snapshot | Re-review RV-CR01–05 and verify same-scope checks | Closes code-review findings only; not owner component acceptance, publication, merge, runtime or production approval |
| `owner-be205-approval-20261019` | `features/FEAT-052-be2-sketch-review/approvals/TASK_APPROVAL.md` (verbatim); `plan/PLAN_R2_APPROVED.md` SHA256 ab295305… | Direct user approval and allocation in the Claude session | Implement BE2-05 SKETCH_REVIEW_COMPONENT_OFFLINE (K1–K7) with OD-01 A (owner-adjusted FEAT-052), OD-03/04/05/06/07 A, OD-16; one-branch-per-task workflow; ACTIVE/substitution | Offline component only; no stage/commit/push/merge, runtime/integration claim or teammate messages; FEAT-052 not confirmed by lane 08–14 |
| `owner-be2-shared-routing-publication-20261019` | FEAT-050 DECISIONS, shared-branch routing publication (verbatim user instruction) | Direct user instruction to Codex | One commit of the six pending routing documents on `feature/be2-01-07`, push with upstream, local Claude handover | Documentation publication only; no source/test, next ACTIVE card, FEAT allocation, merge, integration or runtime approval |
| `owner-be2-shared-branch-20261019` | FEAT-050 DECISIONS (shared BE2-01–07 working branch); consolidation proposal Rev3 (FEAT-049 local, e02ffafb…) with Codex PLAN_REVIEW_PASS | Direct user instruction in the Claude session | Create `feature/be2-01-07` + worktree from 6ab7abf; record shared-branch workflow (WIP1, per-card records, 01 fixes via A17 track) | Branch/worktree creation and records only; no merge/cherry-pick, push, new FEAT number, ACTIVE card or integration approval |
| `owner-be204-sk1-acceptance-20261018` | `features/FEAT-050-be2-sketch-generation/approvals/SK1_COMPONENT_ACCEPTANCE.md` (verbatim) | Direct user acceptance in the Claude session | Accept BE2-04 SKETCH_COMPONENT_OFFLINE (SK1) with F-5, partial-row, callback and N16 dispositions; request publication plan | Offline component acceptance only; BE2-04 IN_PROGRESS; no runtime/production/full-card claim; no stage/commit/push/merge/deploy or branch creation |
| `owner-be204-sk1-approval-20261018` | `features/FEAT-050-be2-sketch-generation/approvals/TASK_APPROVAL.md` (verbatim); `plan/PLAN_REV5_APPROVED.md` SHA256 461d0684… | Direct user approval | Implement BE2-04 SKETCH_COMPONENT_OFFLINE (SK1.1–SK1.5, all revision-5 acceptance) with Q1–Q6 as recommended | Offline component approval only; no real provider/runtime, production adoption, full-card acceptance or Git publication |
| `owner-be203-a1-acceptance-20261017` | `features/FEAT-049-be2-assistance-orchestration/approvals/A1_COMPONENT_ACCEPTANCE.md` (verbatim) | Direct user acceptance in the Claude session | Accept BE2-03 A1 ASSISTANCE_COMPONENT_OFFLINE on A1_CODEX_FINAL_REVIEW_20261017.md; request inventory and commit plan | Offline component acceptance only; BE2-03 IN_PROGRESS; not full-card/production/other-owner sign-off; no stage/commit/push/merge or new checkpoint |
| `owner-be203-a1-approval-20261017` | `features/FEAT-049-be2-assistance-orchestration/approvals/TASK_APPROVAL.md` (verbatim); `plan/PLAN_REV3_APPROVED.md` SHA256 e1fce645… | Direct user approval in the Claude session | Implement BE2-03 A1 ASSISTANCE_COMPONENT_OFFLINE (A1.1–A1.5, all revision-3 acceptance) with D1–D11 as recommended; park BE2-02, keep BE2-01 WAITING_STUDIO | Offline component approval only; no production adoption, full-card acceptance, real provider/runtime, dependency install or Git publication |
| `owner-be203-planning-request-20261017` | FEAT-049 CONTEXT/DECISIONS, plan/PLAN.md revision 1, evidence/notes/SOURCE_AUDIT.md | Direct user request: prepare BE2-03 offline component plan on a separate branch/worktree | ASSISTANCE_COMPONENT_OFFLINE planning on candidate branch stacked on f120c4f | Planning only; D1–D10 unapproved; no implementation, policy/runtime adoption, Git publication or BE2-01/02 closure |
| `owner-be202-c2-acceptance-20261017` | `features/FEAT-048-be2-vision-correction/approvals/C2_COMPONENT_ACCEPTANCE.md` (verbatim) | Direct user acceptance in the Claude session | Accept BE2-02 C2_TYPED_CONTEXT_OFFLINE on plan rev2 and C2_CODEX_REVIEW_20261017.md; request inventory and commit plan | Offline component acceptance only; BE2-02 IN_PROGRESS; not production adoption, BE1/P1/P4 sign-off or real provider/model/runtime evidence; no stage/commit/push/merge or next checkpoint |
| `owner-be202-c2-approval-20261017` | `features/FEAT-048-be2-vision-correction/approvals/C2_TASK_APPROVAL.md` (verbatim); `plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md` SHA256 4b339514… | Direct user approval in the Claude session | Implement BE2-02 C2_TYPED_CONTEXT_OFFLINE (C2.1–C2.5, C2-A01–A14) with Q1–Q5 as recommended | Offline component-candidate approval only; no real provider/server/prompt, production adoption, BE1/P1/P4 sign-off, full-card acceptance or Git publication |
| `owner-be202-c2-preparation-20261017` | FEAT-048 CONTEXT/DECISIONS, plan/C2_TYPED_CONTEXT_PLAN.md revision2, evidence/notes/C2_PLAN_REVIEW_20261017.md | Direct user request: prepare C2 plan and Claude prompt while Lightning unavailable | Source/code-grounded offline component plan and operator template | Planning only; Q1–Q5 unapproved; no implementation, runtime/model/adoption, Git publication or BE2-01 closure |
| `owner-be202-c1-acceptance-20261016` | `features/FEAT-048-be2-vision-correction/approvals/C1_COMPONENT_ACCEPTANCE.md` (verbatim) | Direct user acceptance in the Claude session | Accept BE2-02 C1_COMPONENT_OFFLINE on Codex reviews and C1_FINAL_VERIFICATION_20261016.md; request a commit plan | Component checkpoint acceptance only; BE2-02 IN_PROGRESS; N01/F-01/out-of-C1 integration open; no stage/commit/push/merge, C2 or other card |
| `owner-be202-c1-approval-20261016` | `features/FEAT-048-be2-vision-correction/approvals/TASK_APPROVAL.md` (verbatim); `plan/PLAN_REV1_APPROVED.md` SHA256 f4733c88… | Direct user approval in the Claude session | Implement BE2-02 C1_COMPONENT_OFFLINE (C1.1–C1.5) under D01–D11/V01–V17 | Genuine component-candidate task approval; no real provider/runtime, production adoption, BE1/P1/P4 sign-off, other cards or Git publication |
| `owner-be202-planning-request-20261016` | FEAT-048 CONTEXT/DECISIONS, planrev1 and evidence/notes/SOURCE_AUDIT.md | Direct user request for BE2-02 requirements/Claude preparation while01 waits | C1 offline component planning on separate candidate branch | Planning only until actual plan-specific approval; does not adopt real provider/profile, owner ports, new-card runtime or Git publication |
| `owner-be2-checkpoint-publication-and-split-20261016` | FEAT-044 DECISIONS125; `artifacts/BE2_08_14_TEAMMATE_HANDOFF.md` | Direct user request to split commits and push for teammate branch creation, following confirmed7/7 allocation | Publish A17 checkpoint on existing foundation feature branch; sender01–07, teammate08–14; candidate BE2-12 planning branch | Git publication and planning handoff only; no dev merge, closure, new-card implementation approval, WIP2 activation or role-owner sign-off; original approvals unchanged |
| `owner-be2-codex-takeover-20261015` | `features/FEAT-044-be2-ai-job-foundation/evidence/notes/B2_CODEX_EXECUTOR_HANDOFF_20261015.md` | Actual user reply in this Codex chat after Claude limit | Codex implements already-approved B2-R01/R02 and updates handover/package | Executor override only; Phase B rev3 scope/approvals unchanged, B2 review before B3; no install/provider/service recreation/commit/push/deploy |
| `owner-be2-phase-b-approval-20261015` | `features/FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md`; decision recordrev9/O-09 preserving accepted rev8 §13 | Direct user acceptance/approval, verbatim | Phase A candidate/fixture acceptance; component Q1–Q8 as PROJECT_OWNER_DIRECTIVE; Phase B planrev3 B1–B6 on named Studio, first B2/review before B3 | Genuine task approval; preserves Phase A approval. No P1/P2/P4 sign-off/registry/production adoption or real integration proof; other cards/provider/live route/commit/push/deploy excluded |
| `owner-be2-roadmap-control-20261014` | `features/FEAT-044-be2-ai-job-foundation/CONTEXT.md` and `plan/BE2_ROADMAP.md` revision 2 | Direct owner roadmap request + derived execution plan | Full BE2 task analysis, bounded queue/exits/change control; current slot/tracker | Documentation/workflow routing only; preserves SRS/FEAT-040 obligations and Phase A approval. No Phase B/other-card implementation or stack/model/adoption authorization |
| `owner-be2-architecture-selection-20261015` | `features/FEAT-044-be2-ai-job-foundation/plan/PHASE_B_DECISION_RECORD.md` rev4 O-01/O-02; `docs/adr/ADR-0018-be2-durable-ai-job-runtime.md` | Direct user replies in this Codex chat, with contextual interpretation recorded separately | Preferred D1–D7 architecture, fixture-first component approach/current test profile, and read-only inventory request | Scoped architecture selection; does not supply role-owner concurrence, complete Q1–Q8 answers, Phase A acceptance/test PASS, actual environment/provisioning or Phase B implementation approval |
| `owner-feat018-dev-merge-20261010` | `features/FEAT-042-feat018-contract-dev-merge/approvals/TASK_APPROVAL.md` | Direct owner request | Merge pinned existing FEAT-018 contract branch into dev | Integration/conflict/regression verification authorized; canonical SRS v3.1 remains current; no live provider/deploy authorization |
| `owner-dev-publication-20261010` | `features/FEAT-041-dev-publication/approvals/TASK_APPROVAL.md` | Direct owner push/dev request | Secure current-branch publication and dev integration | Git publication/hygiene authorized; pending historical runtime excluded by documented default, no new product/provider/deploy authorization |
| `owner-four-person-allocation-20261010` | `features/FEAT-040-four-person-delivery-plan/approvals/TASK_APPROVAL.md` | Direct owner request and two answers | One FE, two BE, one technical integrator; tasks without dates | Staffing/integration planning authorized, supersedes conflicting historical discipline labels; no runtime/provider/deploy authorization |
| `four-person-task-backlog-v1` | `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md` | Derived current allocation | 57 cards, 14 handoffs; M/FR/CMD/DATA/UI trace and dependencies | Reviewed proposed runtime backlog from SRS v3.1; documented in ADR-0015, component/fixture pass is not product completion |
| `be1-01-core-domain-foundation` | `features/FEAT-045-be1-core-domain-foundation/` | Approved feature increment | BE1-01 domain rules, ports, versioned contracts, synthetic fixture boundary | User-approved bounded core foundation; does not authorize persistence, HTTP/auth wiring, providers, deployment, or full-stack freeze |
| `be1-02-durable-core-adapters` | `features/FEAT-046-be1-durable-core-adapters/` | Approved feature increment | BE1-02 PostgreSQL/SQLAlchemy/Alembic core metadata adapter, atomic mutation transaction and outbox | Owner continuation approval applies only to plan revision 1 and its plan hash; synthetic PostgreSQL 17.11 migration, transaction, restart, and outbox evidence is recorded in FEAT-046; API/production wiring remains outside scope |
| `adr-0016-be1-02-postgresql-durable-core` | `docs/adr/ADR-0016-be1-02-postgresql-durable-core.md` | Scoped architecture decision | Relational source of truth for BE1-02 core records | Accepted for FEAT-046 only; does not freeze the full product stack or choose object storage, Redis/RQ, deployment, or identity wiring |
| `be1-real-runtime-backend` | `features/FEAT-047-be1-runtime-backend/` | Owner-approved runtime implementation | Real FastAPI BE1 request paths, PostgreSQL persistence, verified adult identity, consent gate, local persistent filesystem adapter | Task-scoped approval and ADR-0017; implements BE1-03–15 incrementally; consent stays pending, production object storage and B22 proposed routes remain unresolved, BE1-16 is Phase 2 |
| `adr-0017-be1-runtime-backend-boundaries` | `docs/adr/ADR-0017-be1-runtime-backend-boundaries.md` | Scoped architecture decision | Runtime boundaries and owner choices for FEAT-047 | Applies only to FEAT-047; does not freeze the complete production stack or approve unresolved SRS semantics |
| `collaborative-learning-scope-v1-20261010` | Owner local attachment `0a08f84b-6e68-4b59-b2a3-31d0d3390b41/Pasted text.txt` | User-supplied Product Scope v1.0 | Replacement classroom/group learning scope, M01–M14, AC01–AC18 and OD01–OD12 | Owner explicitly confirmed scope replacement; source CONFIRMED/PROPOSED/TBD retain their meaning unless later direct answers resolve them. Hash/source review in FEAT-039; original stays local |
| `owner-replacement-answers-20261010` | `features/FEAT-039-collaborative-learning-scope/approvals/TASK_APPROVAL.md` | Direct owner answers | Replace old scope, Android tablets/phones, retain FastAPI and React Native | Documentation replacement authorized; no runtime migration or full stack freeze |
| `collaborative-srs-v3-20261010` | `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` | Current v3.3 (2026-10-24); v3.1 and v3.2 preserved under FEAT-039 | Replacement product requirements and detailed system foundation: use cases, data/API/UI/privacy/NFR/verification; B27–B28 record classroom owner amendments | Exact v3.1 and v3.2 preserved under FEAT-039; v3.3 records owner-confirmed admission boundary, room-code security policy, stage/group disposition and early-stop reason rules. BE1 wire contracts/migrations remain unadopted |
| `owner-foundation-answers-20261010` | `features/FEAT-039-collaborative-learning-scope/approvals/TASK_APPROVAL.md` | Direct owner answers, revision 3 | One school, managed profiles + QR/code without child login, school consent evidence/purpose; 36–155 months; one class/40 children target; session/artwork 90 days after end | Answered choices confirmed; verification/other data-class TTL/measured capacity/admission implementation and full stack remain refinement gates |
| `handbook-v7` | `external-reference/Sketch2Life_Complete_Technical_Handbook_v7_PreImplementation_Freeze.pdf` | Architecture/product handbook | Product invariants, state machine, codebase proposal, baseline tech stack, validation expectations | Local external reference; not published in the repository; user approval and measured evidence still required |
| `user-provided-handbook-v5-revised` | `owner-local attachment Sketch2Life_Complete_Technical_Handbook_v5_Revised (1).pdf` | User-provided architecture/product handbook | FEAT-003 P2-T1 through P2-T5 planning: multimodal validation, ASR/VLM adapters, fusion, contracts, and evaluation | User-provided contextual reference; it does not supersede direct user requests, accepted repository ADRs, current source versions, or task approval |
| `sprint-task-breakdown` | `external-reference/Sketch2Life_Sprint1_4_People_Detailed_Task_Breakdown.xlsx` | Sprint task breakdown | Workstream/task examples, acceptance criteria, fixtures, evidence expectations | Local external reference; not published in the repository; no task is implementation-approved merely because it appears in the sheet |
| `android-distribution-2025-snapshot` | `https://developer.android.com/about/dashboards` | Official Android documentation | Determine whether public Android-version adoption percentages are available | Evidence source only; it redirects platform-version analysis to Android Studio/Play Console |
| `google-play-target-2026` | `https://support.google.com/googleplay/android-developer/answer/11926878` | Official Google Play policy | 2026 target API requirement | Compliance input; re-check before release |
| `react-native-087-release` | `https://reactnative.dev/blog/2026/08/11/react-native-0.87` | Official React Native release note | Node/AGP/Kotlin/compile SDK baseline | Toolchain input for FEAT-009 |
| `lightning-deployment-options` | `https://lightning.ai/docs/security/privacy/deployment-options` | Official Lightning AI security documentation | Private/BYOC/VPN deployment choices | Security input; concrete availability depends on account/plan |
| `lightning-managed-secrets` | `https://lightning.ai/docs/overview/ai-studio/managed-secrets` | Official Lightning AI documentation | Runtime secret storage behavior | Security input; backend/gateway secrets only |
| `android-app-bundle` | `https://developer.android.com/guide/app-bundle` | Official Android documentation | APK versus AAB distribution | Release input; new Play apps publish as AAB |
| `firebase-id-token-verification` | `https://firebase.google.com/docs/auth/admin/verify-id-tokens` | Official Firebase documentation | Custom-backend identity verification | Authentication input; does not authorize Firebase storage/database products |
| `runpod-serverless-endpoints` | `https://docs.runpod.io/serverless/endpoints/overview` | Official Runpod documentation | Production queue endpoint and job semantics | AI infrastructure input for future integration |
| `runpod-api-keys` | `https://docs.runpod.io/get-started/api-keys` | Official Runpod documentation | Endpoint-scoped restricted keys | Security input; backend runtime only |
| `registration-phieu-fa26se225` | `owner-local attachment Phieu_FA26SE225_updated.docx` (user-provided version 1.1; SHA-256 recorded in FEAT-037) | Capstone registration form | Registered actors, scope, products, functional/non-functional requirements, research and work packages | Preserved local source for FEAT-037 derivatives. Current v1.8 uses the extant `Phieu_FA26SE225_v1.2.docx` as its DOCX package base and preserves its 159 paragraphs and three original tables; v1.7 remains historical and derives from v1.5. v1.8 aligns form content with owner-approved collaborative scope and canonical SRS v3.1. The v1.6 evidence note references an absent DOCX. Earlier under-9/package/payment text is historical and superseded for the current product |
| `workflow-b4-b12` | User-provided B4–B12 workflow image | SRS document workflow | Required SRS progression from actors through traceability/review | User-selected documentation structure; not runtime authorization |
| `sketch2life-workflow` | User-provided Sketch2Life workflow image | Product target flow | Input, understanding, Human Gates, Montessori recommendation, animation, story, micro-video, off-screen activity and feedback | Owner-confirmed target journey; MVP/Phase 2 classification is recorded in ADR-0008 and FEAT-029 |
| `feat-029-master-srs` | `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` | Current consolidated requirements baseline, v3.2 | Actors, relationships, business rules, schemas, API/event contracts, Parent Web, logging, Grafana, retention and verification; B27 adds classroom integration decisions | Owner-confirmed product requirements remain distinct from proposed/unadopted technical contracts; not implementation authorization |
| `owner-scope-closure-20260919` | `features/FEAT-029-master-srs/evidence/notes/OWNER_SCOPE_CLOSURE_20260919.md` | Owner decision evidence | Ownership, Guide assignment, revoke, Parent Web, retention, audit and observability decisions | Feature-local evidence; supersedes duplicated historical open questions |
| `vietnam-personal-data-decree-13-2023` | `https://vbpl.moj.gov.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=161106&Keyword=` | Official Vietnamese legal source | Child consent/best-interest, deletion conditions and general deletion-response rule | Legal/privacy constraint; not a product retention-duration source |
| `whisper-large-v3-turbo-model-card` | `https://huggingface.co/openai/whisper-large-v3-turbo` | Official model card | P2-T2 ASR model capability and model-family baseline | Research input only; the exact model revision and decode profile remain subject to fixture benchmark and approval |
| `faster-whisper-transcription-api` | `https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py` | Upstream adapter source | P2-T2 segment, language, timestamp, VAD, and quality-field mapping | Research input only; provider API fields must be mapped into the versioned local contract |
| `faster-whisper-runtime-guide` | `https://github.com/SYSTRAN/faster-whisper` | Upstream project documentation | P2-T2 runtime prerequisites, compute profiles, VAD behavior, and benchmark-comparison constraints | Research input only; no dependency installation or live-model execution is authorized by this entry |
| `nvidia-l4-architecture-spec` | `https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf` | Official NVIDIA architecture specification | Confirm L4 24 GB memory boundary for FEAT-030 single-GPU planning | Hardware planning input; actual available/peak memory must be measured on the Lightning runtime |
| `meta-sam3-official` | `https://github.com/facebookresearch/sam3` | Official model repository | FEAT-030 text/visual-prompt subject and semantic-part segmentation candidate | Benchmark input only; exact revision, license review, checkpoint and L4 evidence are required before activation |
| `meta-sam21-small-official` | `https://huggingface.co/facebook/sam2.1-hiera-small` | Official model card/checkpoint | FEAT-030 lightweight point/box-prompt segmentation control and rollback candidate | Benchmark input only; no dependency installation or runtime activation is granted by this entry |
| `qwen3-vl-8b-instruct-official` | `https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct` | Official model repository | FEAT-030 current Qwen checkpoint footprint and single-L4 coexistence planning | Size is a planning input only; actual CUDA allocation/reserve/peak must be measured on Lightning |
| `meta-sam31-release` | `https://github.com/facebookresearch/sam3/blob/main/RELEASE_SAM3p1.md` | Official release notes | Determine whether SAM 3.1 optimizations apply to FEAT-030 | High-count H100 video results are not treated as evidence for single-image L4 latency |
| `expo-imagepicker-asset-metadata` | `https://docs.expo.dev/versions/latest/sdk/imagepicker/` | Official Expo documentation | Image picker returns a URI plus optional filename, size and MIME metadata; support planning must tolerate absent metadata and verify the pinned SDK/platform | Reference only; documentation resolved to latest during research, so implementation must validate against the repository's pinned Expo SDK 52 / image-picker 16 runtime |
| `expo-image-manipulator-formats` | `https://docs.expo.dev/versions/latest/sdk/imagemanipulator/` | Official Expo documentation | Candidate on-device image normalization API and output formats | Reference only; decoder input compatibility and memory/quality must be measured on the pinned app runtime before approval |
| `amshq-montessori-biology-classification` | `https://amshq.org/blog/curriculum/2022-07-20-updating-the-montessori-biology-curriculum-part-one-classifying-the-living-world/` | American Montessori Society curriculum article | Ground animal-topic coverage in age-appropriate classification, behavior and ecology rather than one activity per pictured species | Pedagogical planning input; not a substitute for qualified review of authored catalog entries |
| `montessori-foundation-scope-sequence-ages-3-12` | `https://www.montessori.org/wp-content/uploads/2021/09/Montessori-Curriculum-Scope-and-Sequence.pdf` | Montessori Foundation scope and sequence | Reference examples for observation, animal life cycles, classification and nature inquiry across ages 3–12 | One organization's scope-and-sequence reference; not a universal Montessori requirement or direct approval of this catalog |
| `ekids-public-pricing` | `https://ekidsvn.edu.vn/pricing` | Current vendor pricing page | Illustrative Vietnamese children's-learning package and monthly-price comparison for FEAT-037, checked 2026-10-06 | Dynamic competitor listing; comparison context only, not evidence of Sketch2Life cost or willingness to pay |
| `montessori-classroom-app-store-pricing` | `https://apps.apple.com/vn/app/montessori-classroom-ages-2-8/id1523888532` | Vietnam App Store listing | Illustrative Montessori-oriented app subscription-price comparison for FEAT-037, checked 2026-10-06 | Store listing may change and differs in scope; comparison context only, not evidence of Sketch2Life cost or willingness to pay |

## Reading notes

- 2026-10-14 BE1 core increment: owner requested Person 1 / BE1 core work, then asked for a new branch, task plan first, and implementation. FEAT-045 records the BE1-01 foundation and FEAT-046 records the separately approved BE1-02 adapter scope on `codex/be1-core-foundation`. FEAT-046's migration and adapter passed synthetic acceptance verification on ephemeral PostgreSQL 17.11; it is not wired into the running API. See its feature-local evidence and status.

- 2026-10-15 BE1 runtime increment: FEAT-047 continues on `codex/be1-real-backend` with proof-based device-key refresh, group lock/unlock and turn invalidation, movement/re-admission lifecycle corrections, and a uniform BE1 request-ID/error response contract. A live non-mutating smoke run against Docker PostgreSQL verified health, missing-token rejection, malformed-JSON validation, 404 routing, and 42 OpenAPI paths. Consent remains pending until an approved verification path exists; child-data paths must fail closed. Local development bytes use persistent filesystem storage; production storage remains open. See FEAT-047 and ADR-0017 for scope, decisions, implementation, and evidence.

- 2026-10-15 BE1 acceptance and API contract: FEAT-047 publishes 47 operations across 42 paths with request/response, authorization, error, and policy-gate details plus a BE1-only OpenAPI 3.1 artifact. Docker PostgreSQL integration verifies real persistence, role and revision checks, consent denial, local artifact durability, and retention worker behavior. The full backend suite collected 2,173 tests: 2,167 passed, 6 skipped, 0 failed; no live Firebase token or real child data was used.

- 2026-10-10 allocation amendment: latest owner roles FE/BE/BE/technical-integrator and no calendar supersede historical FEAT-001/012 discipline labels for the replacement scope. ADR-0006 fixture independence and roadmap/team-view separation remain. FEAT-040 records technical integration explicitly; task cards do not authorize runtime work. Canonical SRS v3.1 stays unchanged.

- 2026-10-10: Product scope replacement and SRS v3.0 supersede conflicting older product records in this table. Old sources/approvals remain history and current implementation evidence; they do not reintroduce Parent portal, payment, under-9/adult-only roles or old video policy as new target requirements. FEAT-039 preserves the exact pre-edit v2.0 working copy. New stack beyond Android/FastAPI/React Native remains proposed/TBD.

- 2026-10-10 foundation increment: canonical SRS is v3.1, FEAT-039 revision 3. Exact v3.0 is also preserved. New owner answers resolve school/profile/consent form; B19–B26 detailed refinements and proposed measurements remain unadopted unless separately confirmed. See FOUNDATION_EXPANSION_SOURCE_AND_DECISIONS.md under that feature evidence.

- 2026-10-12 registration form alignment: FEAT-037 v1.7 is the current FA26 derivative and follows SRS v3.1 plus the FEAT-039 owner answers. It reflects ages 36–155 months, class/group collaboration, Teacher control, school-mediated consent, the one-class/up-to-40-child pilot target, and the 90-day session/artwork default. It removes superseded Parent/billing/package and under-9 claims; prior form versions and their approval records remain history. The v1.6 evidence note points to an absent DOCX, so v1.7 lineage uses the extant v1.5 artifact.

- The handbook explicitly describes its stack as an implementation baseline and says exact models/providers must be frozen after evaluation.
- The spreadsheet's `Not Started` tasks are backlog candidates, not authorization to implement.
- Any future conflict is resolved in this order: direct user request, explicit approved decision/ADR, project evidence, then reference baseline.
- The registration form and supplied images are source inputs. The owner-approved FEAT-029 SRS and ADR-0008 record the current target interpretation when the sources differ.
- The legal source is used only to constrain privacy/retention requirements; production legal review remains required.
- Expo format research is a candidate only: current application dependencies remain pinned to Expo SDK 52, and latest documentation does not establish that a given source image decodes on every supported device.
- Montessori curriculum references inform topic-family coverage and age sequencing; each new or materially revised activity still needs qualified pedagogical review and project-owner approval.

- 2026-10-12 owner source correction: FA26 v1.8 uses the user-selected, extant v1.2 DOCX as its base, preserves v1.2 table shapes and form structure, and follows SRS v3.1 plus FEAT-039 owner answers. v1.7 remains preserved as a historical derivative from v1.5; v1.8 is current. See FEAT-037 plan revision 1 and evidence/notes/FORM_V1_8_ALIGNMENT_20261012.md.

## Owner-directed BE2 evidence publication — 2026-10-20

## BE2-01–14 cross-lane scaffold authority — 2026-10-20

`owner-be20114-cross-lane-scaffold-20261020`: direct owner instruction recorded
in FEAT-057 `approvals/TASK_APPROVAL.md`. Authorizes only the test-side X01–X09
edge registry, scaffold documentation, and registry-integrity tests defined in
FEAT-057 `plan/CROSS_LANE_INTEGRATION_PLAN_DRAFT_20261020.md` §11. It does not
authorize producer/consumer wiring, card-owned contract/source changes, shared
SQL/migration work, runtime/provider/Lightning, route mounting, acceptance
changes, publication, or merge. Original card approvals remain authoritative.

## BE2-01–14 offline cross-lane implementation authority — 2026-10-20

`owner-be20114-cross-lane-implementation-20261020`: direct owner instruction
recorded in FEAT-057 `approvals/TASK_APPROVAL.md`. Authorizes only FEAT-057-owned
offline composition/adapters and behavior tests under the existing
`feature/be2-backend-ai-integration` candidate, using current public candidate
contracts and actual BE2 producer/consumer services. Card-owned source/contracts,
migrations, shared SQL/database provisioning, HTTP routes, live services,
provider/Lightning, acceptance changes, publication, and deployment remain
excluded. Missing/adoption-gated edges remain `NOT_IMPLEMENTED`; see FEAT-057
`plan/CROSS_LANE_INTEGRATION_PLAN_REV2_20261020.md`.

## FEAT-057 G0 owner response — 2026-10-21

`owner-be20114-g0-contract-direction-20261021`: direct user response in the
current Codex conversation: `Chốt theo đề xuất`, with clarification that the
user owns the affected BE2 cards. Records B1–B5/B7 as `ADOPT_WITH_CHANGES` and
B6 as `BLOCKED` because no already-adopted current-source resolver/fence was
identified. This adopts contract direction only, not implementation approval,
source/test/schema authorization, acceptance, or runtime authorization. See the
FEAT-057 ballot and owning-card DECISIONS records. X05c/CR09-02 remains open and
Modal remains deferred.

## Historical FEAT-057 G0 ballot-preference state — superseded 2026-10-21

`owner-be20114-g0-ballot-preference-20261021`: direct repository-owner
response in the current Codex conversation: `Chốt theo đề xuất`. It records the
preference-only state before the user clarified direct ownership of the affected
cards. The current owner response above supersedes the pending-owner wording in
this historical entry. Per-card implementation approval, source/test change,
acceptance, or runtime authorization remain separate. X05c/CR09-02 stays open
and Modal remains deferred.

X01 implementation evidence is currently `PARTIAL` and recorded in FEAT-057
`evidence/notes/CROSS_LANE_X01_REVIEW_20261020.md` with source hashes in
`evidence/metrics/CROSS_LANE_X01_20261020.json`. It connects an exact BE2-07
export to BE2-08 media preparation only; it does not prove foundation job,
artifact, or cross-owner commit lineage.

The 2026-10-20 Modal rerun instructions use Modal's official hosted Notebook
guide (https://modal.com/docs/guide/notebooks) for uploading `.ipynb`/source
files, CPU kernel configuration, optional persistent Volumes, and the
ephemeral filesystem boundary. The FEAT-057 notebook is a scoped offline
pytest rerun only; it does not deploy or invoke a Modal Function, provider,
GPU, Lightning, or database.

The prior environment approval excluded Git publication within its own scope. A later direct user instruction authorized publishing the BE2-08–14 offline evidence by PR and merging it into the BE2 integration branch. PR #16: https://github.com/CaoDat-2410/Sketch2Life/pull/16; merge commit 4014b11a867d8030190a0789a6b03e1602fd522d; source tip 964944c93edf89e531a0895f6248d7f1ee632c20. The publication contains 35 commits and 567 paths. No force push, project dev/main merge, deployment, or task acceptance change was authorized or performed. Original card approvals remain authoritative.

`owner-provided-modal-x01-run-20261020`: Modal execution receipt, JUnit, and
pytest log supplied by the owner after running the FEAT-057 X01 notebook.
Their hashes and counts are recorded in
`features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_X01_MODAL_20261020.json`;
the artifacts are preserved in that feature's `evidence/raw/modal-x01-20261020/`.
This verifies the exact source ZIP's bounded offline test run only; it does not
establish full BE2-01–14 integration or change any card acceptance.

`owner-x02-source-review-20261020`: FEAT-057 source-contract review of the
BE2-07 `KnowledgeSupersededV1` event and BE2-09 review/playback boundaries.
Evidence is in
`features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_X02_REVIEW_20261020.md`
and `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_X02_20261020.json`.
The finding is `NOT_IMPLEMENTED`: no adopted BE2-09 invalidation receiver or
held validity fence exists in the candidate. No tests or card-owned changes
were made.

`owner-x04-x09-source-review-20261020`: FEAT-057 source-contract review of
cross-lane edges X04–X09. Findings and source hashes are recorded in
`features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_RESIDUAL_REVIEW_20261020.md`
and `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_RESIDUAL_REVIEW_20261020.json`.
All six edges remain `NOT_IMPLEMENTED` pending card-owned adoption; no behavior
tests or card-owned source changes were made.

## FEAT-057 cross-lane scope approval — 2026-10-21

`owner-be20114-cross-lane-scopes-20261021`: the owner approved the exact offline
scope hashes for BE2-01/07/08/09/14 in their official approval records. The
BE2-01 typed route is implemented and unit-verified; see
`features/FEAT-057-be2-01-14-offline-integration/evidence/notes/APPROVED_SCOPE_EXECUTION_MANIFEST_20261021.md`.
Remaining work is gated by the specific missing durable-source-fence,
foundation-UoW/recovery, public artifact-read, and worker-execution/accounting
contracts recorded there. The typed unit route alone does not prove X09-08
persisted-job composition. This supersedes only the earlier claim that those
scopes were awaiting owner approval; it does not make any edge PASS or change
card status. X01 remains PARTIAL, X05d BLOCKED, X05c/CR09-02 open, and
Modal/Lightning/provider/runtime remain unauthorized.

## FEAT-057 owner-directed shared UoW design — 2026-10-21

owner-be20114-shared-uow-design-20261021: direct owner instruction recorded in
the owning-card DECISIONS files and
features/FEAT-057-be2-01-14-offline-integration/evidence/notes/OWNER_DESIGN_DISPOSITION_FOUNDATION_UOW_20261021.md.
The proposed foundation-owned transaction boundary is captured in
features/FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_DRAFT_20261021.md
(SHA256 B456DEEDF5F892F328E7AEEFF442BC82281400A994EB5A74D791C13856FAB9B0).
The scope remains DRAFT and requires independent review, an exact minimal manifest
and supplemental implementation approval before source edits. Budget unit/limit,
reservation timing, late-result semantics, same-store source-fence feasibility,
and exact artifact read fields remain open. X01 remains PARTIAL, X05d BLOCKED,
X05c/CR09-02 OPEN, and X09-08 NOT_IMPLEMENTED; this record changes no card
acceptance or runtime gate.

## FEAT-057 shared-UoW independent review and successor drafts — 2026-10-21

Source: owner-pasted independent Claude review of the FEAT-044 foundation-UoW draft, verdict CHANGES_REQUIRED. Source review snapshot SHA manifest:
features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_20261021.json.
Disposition: features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_UOW_REVIEW_DISPOSITION_20261021.md.
Successor planning documents: FEAT-044/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV2_DRAFT_20261021.md; FEAT-057/plan/CROSS_LANE_X01_X05_PLAN_ERRATUM_20261021.md; FEAT-050/plan/CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md. These are documentation drafts only. No implementation, test, SQL/database, provider, Modal, Lightning, runtime, approval or card acceptance is implied.

## FEAT-057 UoW rereview 2 source — 2026-10-21

Source: owner-pasted Claude rereview report, preserved at features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_UOW_CLAUDE_REREVIEW_REPORT_20261021.md (SHA256 0507A53D569B34ACF9EB44549D6BE794851335F3DBB88FD89E48D17E4AA649F0). Source identity: features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_REV2_20261021.json (18 files, SHA256 01160A4876ABB97CC33AC17108ADAE6F95E876DB86A24DF84B9832EC2B4F74FC). Disposition and successor drafts are in FEAT-057 evidence; review and implementation gates remain open.

## FEAT-057 cross-lane owner D2 — 2026-10-21

owner-be20114-uow-d2-20261021: direct owner response “Chốt theo đề xuất cả 2”, recorded in FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D2_20261021.md. It selects a versioned BE2-08 stale terminal representation without artifact and binds VideoRun attempt_id only at S, clearing it on retry. Authority is design direction only; no source/schema/test or implementation approval. See FEAT-044 scope Rev5 and FEAT-057 plan Rev6 drafts for rereview.
## FEAT-057 persisted-job to VideoWorker seam review — 2026-10-22

Source: the owner's current goal to verify the offline BE2-07 to BE2-01 persisted job/run dispatch to BE2-08 VideoWorker path. Read-only review and status evidence are recorded at features/FEAT-057-be2-01-14-offline-integration/evidence/notes/BE2_01_07_TO_08_SEAM_BLOCKER_20261022.md and the factual local handoff at evidence/notes/BE1_HANDOFF_BE2_SEAM_20261022.md. The existing 330-test JUnit was verified against its recorded hash and counts. Authority boundary: documentation/evidence only while the required CR08-01 UoW/recovery and BE2-07 durable source fence remain unadopted. No source, test, schema, migration, owner approval, card status/acceptance, runtime, or Git publication was changed. No FEAT-057 PASS or BE1 integration readiness is claimed.

## FEAT-057 persisted VideoWorker seam scope proposal — 2026-10-22

Candidate contract and per-owner path manifest are recorded at `features/FEAT-057-be2-01-14-offline-integration/plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_DRAFT_20261022.md` (SHA256 `6C8A0B365B3A768FE3AC400A263714E67170530C08575091248A999D0F319733`). The owner asked for a scope/contract draft to review. It remains documentation-only and grants no source/test permission. Existing owner decisions D3 C1-A/C2-A are treated as design direction only. Open gates: CR08-01 adoption, BE2-07 durable source-fence adoption, FEAT-050 lifecycle/receipt adoption, D4 completion-time budget disposition, BE1-owned artifact adoption where needed, exact owning-card manifests/approvals, and the conflict between the no-database boundary and durable persistence acceptance. No test ran; X01 remains PARTIAL and X09-08 NOT_IMPLEMENTED.

## FEAT-057 revised persisted VideoWorker scope — 2026-10-22

Owner-directed scope Rev2 is recorded at `features/FEAT-057-be2-01-14-offline-integration/plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md`. The owner allows only a dedicated local isolated database with synthetic data for later transaction/persistence tests after approval updates. Scope excludes BE2-09/14, D4 and BE1 implementation; durable source fence is separate and X01 remains PARTIAL. CR08-01 and exact FEAT-044/050/057 approvals are still missing. No source/test/schema/migration, database or runtime work occurred.
- Scope Rev2 SHA256: `F170809FCBB71D1B588960466350D6086568EFB6384232AB0F178DF7D350C052`. The owner-authorized publication edit removes only the machine-specific Worktree locator; contract terms and §4 manifests are unchanged (previous bytes: `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`).

## FEAT-057 adopted persisted VideoWorker flow — 2026-10-22

The owner adopted `BE2-VIDEO-LIFECYCLE/1` for A/S/B and identity-failure under the same Rev2 hash. Supplemental approval records are:
`features/FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md`,
`features/FEAT-050-be2-knowledge-video/approvals/TASK_APPROVAL.md`, and
`features/FEAT-057-be2-01-14-offline-integration/approvals/TASK_APPROVAL.md`;
their exact §4 path lists were verified (7/7, 14/14, and 1/1).

The implementation is limited to those approved source/test manifests. The focused unit/contract batch passed 325 tests. PostgreSQL 17 persistence verification remains unrun because its required isolated loopback endpoint and external test-only credential file are unavailable; no database was created or contacted. Evidence is indexed at `features/FEAT-057-be2-01-14-offline-integration/evidence/README.md`. Durable BE2-07 source fencing is separately gated, X01 remains PARTIAL, and no BE1 integration readiness is claimed.

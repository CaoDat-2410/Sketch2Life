# T2B rework report — owner decision record

Date: 2026-11-01
Scope: FEAT-064 T2B rework on `feature/feat063-be-foundation`, using owner decision record `9f337aff` as authority. This report contains no connection string, token, real-child data, or absolute machine path.

## State found when resuming

| Item | State and evidence |
|---|---|
| Branch / baseline | `feature/feat063-be-foundation`; HEAD `20e87e17931ec18f4e99ddbe52ea7118b94159dc`, direct child of `9f337affdc142978f6ba5de0124bae2574528f62`; `origin...HEAD` = `0 1`; index empty; no merge/rebase/cherry-pick in progress. |
| Protected local files | All seven pinned hashes matched at resume and at closeout; values are listed in §7. |
| Plan / approvals | `plan/T2B_REWORK_TO_OWNER_RECORD_PLAN_20261101.md` already existed, SHA-256 `959C9AB6739826F6C8AB53EB4AC7C49ACAD8DBDF629E5564291A615B86657DE6`, matching the existing FEAT-064 T2B rework approval. The FEAT-063 DB-scope approval and FEAT-064 T3 B8 record were already present; no duplicate approval was added. |
| Code / tests / migration | The T2B implementation, migration, and three new tests already existed in the working tree. Therefore this continuation could not produce a trustworthy pre-change RED snapshot. |
| Divergence note / report | The divergence note was OPEN and this report did not exist. The note is now RESOLVED with the recorded reconciliation. |

## R0–R6 progress

| Phase | Result |
|---|---|
| R0 — preflight and regression reference | LÀM, with limitation: the existing recorded run occurred after the implementation was already on disk, so it is not a clean pre-change baseline. That recorded 92-file matrix was `5 failed, 2,116 passed, 119 skipped`. The failure identities are the same five listed under R6. |
| R1 — source inventory | LÀM; see §1. |
| R2 — plan and approvals | LÀM before this continuation; pinned plan hash verified. Existing approval entries were retained. |
| R3 — test-first RED | NOT DONE: the implementation was present at resume, and no reliable red-before-code evidence was available. |
| R4 — implementation | LÀM before this continuation. This continuation only made allowlisted typing/import/format fixes and updated the divergence note. |
| R5 — PostgreSQL rehearsal | PARTIAL; see §2. Migration state and tests were checked, but the downgrade gate was not met at closeout. |
| R6 — report and closeout checks | PARTIAL: the earlier 92-file selection was not preserved in the resume state. A deterministic 76-file subset was rerun; it produced the same five failure identities, but totals are not directly comparable. Lint, validators, and tracked diff checks produced the results in §5. |

## 1. R1 source inventory

| Concern | Source evidence | T2B consequence / boundary |
|---|---|---|
| Persisted age provenance and writers | `be1_models.py:101-138`; registry create `be1_registry.py:359-360`; operator create `core_store.py:509-510`. | Profiles store `age_revision` and `age_source`; registry writes `ADULT_DECLARED`/1, operator synthetic creation writes `SYNTHETIC_FIXTURE`/1. Historical rows are assigned `LEGACY_UNKNOWN`/1 by the migration, not inferred from identifiers or timestamps. No age-edit route was added. The age-write detector now requires an age update to increment the revision in the same statement. |
| Reader inputs and provenance | `be1_fact_reader.py:49-73,161-184,239-253,335-374`. | Snapshot carries the stored age source/revision; the v2 context payload includes both. The provenance reference is `be1-profile-age-v2:{age_source}:{age_revision}`. Synthetic facts keep null consent references and `consent_effective=false`; absent or invalid age provenance is denied. |
| Digest construction | `context_revision.py:15-50`. | Canonical scalar JSON and the existing domain separator produce a full SHA-256 digest. The compatibility integer is the low 31 bits of the first four bytes of the same digest. Read/evaluation time is excluded. |
| Vision freshness | `application/ports/vision_analysis.py:98-119`; `application/services/vision_analysis.py:335-406,477-484,578-581`; `domain/vision_analysis.py:870-898,995-1034`. | Optional `ContextDecision.context_digest` is validated. Service pre-provider checks, post-provider freshness, and internal analysis-head replay compare integer revision and digest; when one side has a digest, a missing or unequal peer digest fails closed. |
| Integer-only Vision claim boundary | `domain/vision_analysis.py:336-399`; public claim remains integer-only. | A digest-bearing current context cannot be represented by the existing observation claim, so the request is refused before provider invocation. No public claim field or external gateway contract was changed. |
| AI Jobs boundary | `application/ports/ai_jobs.py:95-147`; `contracts/schemas/ai_jobs.py:46,221`; `infrastructure/ai_jobs/sql/tables.py:193`. | AI Jobs stores and compares its own integer `context_revision`; no digest field was added to its API, queue, or SQL schema. This is NOT DONE pending separately approved contract work. |
| Other digest scopes | `application/services/assistance.py:926,1112,1169-1171`; `domain/vision_analysis.py:650-682`; `infrastructure/vision_analysis/context_adapter.py:133-158,273-277`; `contracts/schemas/analysis_context_results.py:52-63,108-132`. | Assistance and typed-context digests have separate meanings and remain unchanged; they are not treated as the new BE1 whole-fact digest. |
| Production BE1 fact source | `be1_fact_reader.py:89-95` defines only the `BE1FactSource` protocol; no production PostgreSQL implementation was found in the source inventory. | PostgreSQL-backed `BE1FactSource.current_facts()` and runtime/router wiring remain NOT DONE. |
| Migration graph | Static Alembic inventory and `python -m alembic -c backend/alembic.ini heads`: 24 revisions and 10 terminal heads; `be1_core` ends at `20261101_be1_age_0001`. | New revision `20261101_be1_age_0001` has sole parent `20261031_be1_se_0001`; the explicit BE1 chain test was extended. |

## 2. R5 PostgreSQL results

The local database safety checks identified PostgreSQL 17.11 on loopback and the approved disposable database name. No connection string was recorded. Alembic currently has all 10 heads recorded, including `20261101_be1_age_0001` for `be1_core`; `upgrade heads` was already current when resumed. The live database had no managed-profile rows available for a backfill spot check, so the old-row backfill is supported by the offline migration SQL test, not by an observed legacy row.

| PostgreSQL test / operation | Actual result |
|---|---|
| `test_be1_age_provenance_postgres.py` | 1 passed. It exercised operator-created `SYNTHETIC_FIXTURE`/1, no-consent invariants, and database CHECK rejection for invalid revision/source. The real registry route’s `ADULT_DECLARED` path was not exercised on PostgreSQL because the existing legal-consent schema does not provide the required effective state; the offline registry-writer test covers the assignment. |
| `test_be1_synthetic_pilot_postgres.py` | After adding the two new age fields to the allowed direct-profile fixtures: 4 passed. |
| Existing `test_be1_postgres_api.py` | 2 passed, 2 failed. The failing tests are `test_room_code_start_revocation_stage_and_early_outcome_are_durable` and `test_pending_consent_stays_pending_and_blocks_profile_admission_and_canvas`. Static inspection found direct `ManagedProfileModel` fixtures without the new non-null age fields; the exact database exception was not captured. This legacy suite was not edited. |
| Existing Lesson Library PostgreSQL suite | 5 passed, 1 failed: `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http`. The exact cause was not captured; no cause is asserted here. |
| Read-only closeout counts | 0 managed profiles, 0 synthetic proofs, 0 consent rows; 10 synthetic organization rows remain. They were not deleted because their ownership was not established. |
| `downgrade be1_core@-1` then `upgrade heads` | NOT RUN in this continuation: the prompt gates downgrade on no remaining test rows, and 10 synthetic organization rows remained. No destructive cleanup or DROP/TRUNCATE was used. |

## 3. R6 offline tests

| Run | Actual result |
|---|---|
| Recorded R0 reference | 92 files: 2,116 passed, 119 skipped, 5 failed. |
| Corrected R6 rerun | 76 unique test files: 1,735 passed, 121 skipped, 5 failed in 115.77s. This selection includes the 5 CI files and targeted synthetic/BE2/B5/T2B/T12/OpenAPI/migration files, but is smaller than the recorded 92-file R0 set; total counts must not be compared as if the selections were identical. |
| R6 failures | `test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation` still expects 23 revisions while the new migration makes 24. `test_be2_synthetic_basis.py::test_vision_accepts_single_child_synthetic_scope_and_legacy_legal_path` and three `test_vision_service_typed_context_synthetic.py` tests expect old digest-less synthetic behavior; the owner-pinned design now fails closed for synthetic contexts without a digest. These tests are outside this task’s allowlist and were not changed. The same five failure identities were in the recorded R0 result. |
| Changed-file focused runs | 127 passed, 15 skipped; after typing changes, a narrower final run was 107 passed. |
| `test_live_image_demo_api.py` | Separately: 32 passed in 10.16s. |

The first R6 invocation used an incorrect test path and ran no tests; it is not counted. The normalized rerun above removed duplicate path spellings. A previous broad selection that included `test_lightning_vision_v2_server.py` stopped at collection and is also not counted.

## 4. Hashes of created/modified files

“Before” is the blob at baseline HEAD `20e87e17931ec18f4e99ddbe52ea7118b94159dc`; it is not claimed to be the pre-task working-tree content. “New” means absent from that HEAD. The report’s own SHA-256 is supplied in the final chat response to avoid a self-referential hash.

| File | SHA-256 before | SHA-256 after |
|---|---|---|
| `backend/src/sketch2life/application/ports/vision_analysis.py` | `B0CB4A3466477B7A4394FA4E26D4EBF43A269936A22CFB189DE0B8089226FA2B` | `4C13B5443681D2C1D79B13FFF6192B87C57B26D414C64F1F852C38DB7AF84BC9` |
| `backend/src/sketch2life/application/services/vision_analysis.py` | `EF6785E18243F89A352C36C6284B5003B0165718B56E1BDCF744C8A810C431FB` | `A8349566B81B39CB03854DA5A7E4F923B200DC4B48B3CBEDDE1B3926DD72920C` |
| `backend/src/sketch2life/domain/vision_analysis.py` | `CB36B2917EC0E9061C21DCA4B1AC27316F57E329FC3CAAFBD78AD1FA41F3DFA5` | `D4A6817192521069281463B7D811E62022B814D441C26AEF9A1C5673A55C732B` |
| `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py` | `276A6ACF29D46D7550DE92A5BB4B82A27CDBBC371651AB4491B2723CE029CF3D` | `348E18B395A35DF0D05EC8E1DCB56F8ECBDF64C7F181250A2C3F132CA53A535E` |
| `backend/src/sketch2life/infrastructure/assistance/context_revision.py` | `14165D3D2B0027A090553424B88F0BB5043C6EE3261C45371FE06CC191F8E7BE` | `554641E2DA095BAC908FAB8F4B097A4711ECCFC39026F698AB7B536619781547` |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `735599B638090ABAD59CE3FBFB9630708C3A3DDB2F199994DD3C106B597E38D3` | `6859CC8313482C70828176B4E12209B485B7D582C6831340AE0D451659219C1E` |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | `7E96852E81AEBBAE9985F03E07B49F9F8A94001C220FFEA6236417C90C213FD4` | `AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94` |
| `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` | `285CBEEDEFDEF30CCF9C0A35DD7014824CBC7D87F66C5C3A03BB9A58BB302B68` | `00D60D6011AC7BA83C4862D334F3F8202595D125CC6E94DDA4DE52DF71871C08` |
| `backend/alembic/versions/20261101_be1_age_provenance.py` | New | `2A634DC4DDF00326AFEF4079F7795A185D458DE2DB65BA6FD3C40291BBA5614E` |
| `backend/tests/contract/test_be1_fact_reader_contract.py` | `DE7EEA3D101E50E018D98AB2670CC152E90246E909577A4EDA826E90D9C233BD` | `E401756730F74883A16AF0703162E501F407AD1F5F57F10C868154E6CD48F95A` |
| `backend/tests/integration/ai_jobs/test_migrations.py` | `376E416EB9F0903BA03834CA56279A0628E9490D1575A58486D9CD242FB6B138` | `BF1D51D21262C3E76206C9A0FD01EBD3B3FE7006AA0B00DC28109A81C0A9238E` |
| `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `D2104C4BFEAB75CF971F10A410A4ABD362D39BA0F600C46997F748407D38CB16` | `1E353FC668DFEB830F0C27D6D14F7F9445E27C2D99BD53130EBB0943AE43D8E3` |
| `backend/tests/unit/test_be1_fact_reader.py` | `3095A06BE51BDB9BCF57A6AFE2A803D838D0EE344B513BED95E4070B69ADFC70` | `F234E7056F0FAFD0479519AB419271E3EE19552E1AF55A17E5A09CD387F5F815` |
| `backend/tests/unit/test_context_revision.py` | `90776A36F1B0BBE7E4619A6859C7A04E97C816974A5F105B1C4B248A3F3DFCB6` | `6C22E3B539CAB67829157DADD9690696C0AA7A712163914C3602FC3E52932ABA` |
| `backend/tests/unit/test_profile_age_invariant.py` | `072B69085B5BE0695FBF47938D50E42F2F210DA8D184D2E80493442AE9845F72` | `B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB` |
| `backend/tests/unit/test_synthetic_audience_limit.py` | `F28846DBCB778D4F1C6C2A9256FFD77BFAE56DDECA0588F513FAF5AB073ADE3B` | `178F1C3CE40EC2B3AF881DB3EDA64FB1FAD6CD050DD33FDC01EF134990D6CE5A` |
| `backend/tests/unit/test_age_provenance_columns.py` | New | `DE1B745B83AE490C4ACAD8F1D457B3CF1E16420B06F79B19DDFF3576BE778C97` |
| `backend/tests/unit/test_context_digest_equality.py` | New | `6B288393BF0D2F31D53976194787D2B6290FCABB9C9A55B9C102A56D626A30B3` |
| `backend/tests/integration/test_be1_age_provenance_postgres.py` | New | `9EAF3DC5C2FC34AEBA512FEA33E05DCA4CE309F44017487CDCC3CD9F73B6CAEA` |
| `features/FEAT-064-current-flow-modal-vision-dev/plan/T2B_REWORK_TO_OWNER_RECORD_PLAN_20261101.md` | New | `959C9AB6739826F6C8AB53EB4AC7C49ACAD8DBDF629E5564291A615B86657DE6` |
| `features/FEAT-064-current-flow-modal-vision-dev/evidence/notes/T2B_DECISION_DIVERGENCE_20261101.md` | `912C39F666C855F7FBF5FB97CF0B27C774078BC99C6F00CD457A38E224E82C80` | `0BE0C019639F21C964572286B09E520B0784431E92AE124D606A14F6E395036D` |
| `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` | `0A5338523604EE030F9B83EDD1E1C757C8C9C8B7F72AD21356D3526D0D3EA143` | `85EBA2B79DE1C71FC72A2A3EE0785FF24CEB387C645F7F8C461BC8C5AD150859` |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | `1848745FE4C9DB46A8178EBCB1EC7FC88059019F87B7FEF219218334DCCA2345` | `15E157E4A805D685B2CCFF6E2B9D21391ED9C045A19F5354C3173146C248CEE9` |

## 5. Final checks

| Check | Actual result |
|---|---|
| `ruff check --no-cache --config backend/pyproject.toml` on the 19 changed/new Python paths | `All checks passed!` |
| `ruff format --check --no-cache --config backend/pyproject.toml` on the 4 new Python files | `4 files already formatted` |
| `mypy --strict` on the 19 paths | Exit 1 with 8 baseline errors only: 7 existing errors in `test_be1_fact_reader.py` and 1 existing `APIRouter.responses` typing error in `be1_registry.py`; no new errors remained. The changed portions are outside those errors. |
| `validate_harness.py` | `HARNESS_VALID`; approval gate and frontend asset gate enabled. |
| `validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; 6,001 publishable files scanned; no absolute machine paths. |
| `validate_architecture.py` | `ARCHITECTURE_VALID`; dependency direction, mobile boundary and Firebase checks valid. |
| `git diff --check` | No output; exit 0. |
| New file bytes / whitespace | The report and plan are checked separately during closeout; no CR/BOM or trailing whitespace is intended. |

## 6. Remaining boundaries

NOT DONE: production PostgreSQL `BE1FactSource`; digest transport through public Vision claims and AI Jobs; runtime/router composition; T2C; status HTTP route; Child reconnect and Teacher session routes; T3 implementation; B4b. No Modal, GPU, remote provider, or end-to-end BE1→BE2 call was run. No real-child data was used.

## 7. Protected local hashes and out-of-allowlist files

All seven protected hashes matched after work:

| File | SHA-256 prefix |
|---|---|
| `docs/context/SOURCE_REGISTER.md` | `0B43E4BA` |
| `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | `E7C8143A` |
| `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md` | `F1ADB793` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md` | `8BBFD0ED` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md` | `B61B0607` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md` | `93374E96` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/S1_DECISION_CARD_20261030.md` | `4D95D303` |

The three modified owner-local tracked files (`SOURCE_REGISTER.md`, FEAT-063 `CONTEXT.md`, and `STATUS.md`) remained outside the T2B allowlist and were not staged. The four protected ignored notes remained untouched. No other out-of-allowlist path was changed.

## Điều chỉnh sau review độc lập (T2B fixup 2026-11-01)

### Phát hiện và xử lý

| Phát hiện | Xử lý |
|---|---|
| Test đồ thị migration còn kỳ vọng 23 revision và head cũ. | Cập nhật kỳ vọng thành 24 revision; `20261101_be1_age_0001` là head của BE1, còn `20261031_be1_se_0001` không còn là head down-only. |
| Synthetic context thiếu digest hoặc chỉ có digest trong BE1 nhưng claim Vision chỉ mang integer. | Test xác nhận thiếu/không biểu diễn được digest bị từ chối `STALE_CONTEXT` trước provider, không lưu analysis head; nhánh legal không digest giữ hành vi cũ. Đây là fail-closed có chủ đích đến khi hợp đồng claim mang digest được duyệt. |
| Hai fixture `ManagedProfileModel` trong BE1 API không khai báo provenance tuổi bắt buộc. | Thêm `age_revision=1` và `age_source="LEGACY_UNKNOWN"` ở đúng hai fixture. Không thêm server default cho `age_source`. |
| Teardown Lesson Library bỏ sót hàng con không có `organization_id` ở nhiều tầng khóa ngoại. | Fixture lần theo khóa ngoại từ đúng organization ID của nó, rồi xóa hàng fixture theo thứ tự con trước cha. Không dùng wildcard, DROP hay TRUNCATE. |

### Test và kiểm chứng

- Trước fixup, năm regression mục tiêu được tái hiện: 5 failed trong 0.72s. Sau sửa, cả ba module unit liên quan đạt 175 passed; riêng 69 file test liên quan đến T2/T2B/B5, synthetic, BE2, OpenAPI và migration đạt 1,802 passed, 39 skipped, 0 failed. Danh sách 76 file của R6 cũ không được lưu, nên bộ 69 file này là lần chạy tái lập được và không được coi là cùng manifest hay so tổng số trực tiếp.
- `tests/contract/test_live_image_demo_api.py` chạy riêng với `AWS_EC2_METADATA_DISABLED=true`: 32 passed. Không đặt cờ này khiến boto3 thử đọc AWS instance metadata, bị test offline chặn; không có request ra dịch vụ ngoài.
- Thử `pytest tests` toàn bộ không thu thập được: 28 module ngoài bộ chọn lọc lỗi ở collection. Kết quả này không được tính vào số test của bộ 69 file.
- PostgreSQL: `test_be1_postgres_api.py` đạt 3 passed, 1 failed; ca `test_room_code_start_revocation_stage_and_early_outcome_are_durable` trả `409 CONSENT_NOT_EFFECTIVE` vì consent seed đang pending trong khi assertion đòi 200. Giữ nguyên lỗi đã biết, không sửa guard.
- PostgreSQL: age provenance 1 passed; synthetic pilot 4 passed. Lesson Library đạt 5 passed, 1 failed vì `DEPENDENCY_UNAVAILABLE` khi ClamAV không sẵn sàng; không còn lỗi teardown.
- Các hàng fixture mới từ những lần test lỗi đã được dọn riêng theo ID fixture: 9 Lesson Library organization và 36 adult identity, sau đó 4 BE1 acceptance organization và 5 adult identity. Mười synthetic organization có trước vẫn còn; DB sau test có 10 synthetic organization, 6 Lesson Library organization cũ, 24 Lesson Library adult identity cũ và 0 managed profile.
- Với managed-profile count bằng 0, `downgrade be1_core@-1` và `upgrade heads` đều exit 0. `alembic current` có 10 revision; tập revision hiện tại khớp 10 Alembic heads.
- Ruff chỉ còn một `I001` import-order finding ở `test_be1_postgres_api.py`; kiểm tra cùng file từ HEAD cho đúng finding đó. Mypy báo 11 lỗi baseline và cũng báo đúng 11 lỗi trên HEAD shadow-check; lỗi mới bằng 0. Không có file Python mới nên `ruff format --check` không áp dụng.

Các kết quả ở mục này cập nhật trạng thái sau R6 cũ; không sửa product code, migration, adapter BE1FactSource, hay hợp đồng digest Vision/AI Jobs. Không chạy Modal/GPU hoặc luồng end-to-end.

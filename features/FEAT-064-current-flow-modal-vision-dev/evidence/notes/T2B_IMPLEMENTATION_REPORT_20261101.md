# T2B implementation report — 2026-11-01

## Scope and result

T2B was implemented only as an offline, injected BE1 fact reader for one synthetic member in IMAGE_ONLY mode. The reader is not wired into an application runtime or provider. T3 received a decision-recording REV2 plan only; no T3 code was changed.

**Superseded by the follow-up in the last section:** the first run stopped before R5 because the earlier test `tests/unit/test_be2_synthetic_basis.py` had 14 failures (its synthetic `MemberFact` fixtures carried fabricated consent references, contrary to A2). Those fixtures and one projection regression were then fixed by the owner session and the regression set is green; see "Follow-up after R4".

## R0 — preflight and measured baseline

- Branch: `feature/feat063-be-foundation`.
- Starting HEAD: `578f3e5ee53ba841a83352a133141cfe80b8c672`; origin divergence `0 1`; index empty. Current HEAD remains unchanged.
- The three pre-existing owner-local edits were preserved. Seven protected-file hashes remain listed at the end of this report.
- Starting baseline: the fixed CI 5-file set plus T1's two tests: `227 passed, 4 skipped`.
- Starting supplemental set: `61 passed, 16 skipped`.
- `tests/contract/test_live_image_demo_api.py`: `31 failed, 1 passed`. A one-test diagnostic confirmed the test's offline socket guard blocks boto3's metadata-service credential discovery during app initialization (`External access is forbidden in offline API contract tests`). No application or test file in that path was changed.
- Starting strict mypy for the three planned existing source files: `Success: no issues found in 3 source files`.

## R1 — static source and revision inventory

- `AssistanceOwnerPort.members(organization_id, participant_ids, purpose_code)` returns `tuple[MemberFact, ...]`.
- `AnalysisContextPort.current(scope)` returns `ContextDecision`. `VisionContextSourcePort.resolve(pin, source)` is a separate typed-context port; it is not a `current(scope)` method.
- `MemberFact` carries participant, age, consent and optional eligibility metadata. `ContextDecision` carries context revision, consent/purpose booleans, session state, one or more ages and optional eligibility metadata. `ProviderContextMode` is `IMAGE_ONLY` or `TYPED_CONTEXT`.
- In the BE2 fact path reviewed here, context revisions are compared for equality. No ordering comparison or consumer limit above the positive signed 31-bit range was found. The `ai_jobs.context_revision` column is SQLAlchemy `Integer` (`backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py:193`). Monotonic comparisons found in Learning Content and Video Review are separate aggregates and do not compare this BE1 fact revision.
- Static search/AST found profile-age creation writes only at `be1_registry.py:create_profile` (`backend/src/sketch2life/interfaces/http/routers/be1_registry.py:353`) and `core_store.py:create_synthetic_profile` (`backend/src/sketch2life/infrastructure/persistence/core_store.py:503`). No age update assignment was found. The implementation uses `age_revision=1` and `be1-profile-age-v1:{child_id}` and adds an AST guard test.
- The existing image-only gate accepts a one-member synthetic `MemberFact`/`ContextDecision` only when legal booleans remain false and basis/version/evidence/scope are exact. Typed-context synthetic remains denied by the adapter before the typed context snapshot path. REAL/LEGAL_CONSENT remains fail-closed pending B4b.

## R2 — decisions and approval records

- Updated `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md` to APPROVED for this bounded scope, record A1–A6, freeze the digest payload and add the BE2 field mapping.
- Added `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_REV2_20261101.md` with status `DECISIONS RECORDED; CODE NOT APPROVED`, B1–B8, remaining open implementation questions, and source-backed findings: reconnect is still legal-only/turn-bound; the class profile list denies synthetic profiles through the current consent guard; generic Teacher-supplied session configuration is not profile authority.
- Appended separate T2B and T3 entries to `approvals/TASK_APPROVAL.md`. The earlier approval entry was retained unchanged. T3's entry approves documentation only.
- T2B plan SHA-256: `DF95B180ACF702E7374837824BB83DF779B7B201E56EFDDA973369936286436A`.
- T3 REV2 plan SHA-256: `FF8AB4C23AA31B4531AFEF1E6990093C6F1736DE15BF2522AC22A0F881576502`.

## R3 — red-before-code record

The first run of the five new test files, before production implementation, stopped at collection with three import errors: the two planned infrastructure modules did not yet exist, and the new contract test initially imported the existing member gate from the wrong module. That test import was corrected before implementation. Because collection stopped, this run did not provide a complete per-test red count; no failure count is inferred from it.

## R4 — implementation and verification

Implemented the consent-null invariant in `MemberFact`, nullable consent fields plus a typed basis rule in the Teacher consent DTO, and the synthetic-null Teacher projection. Added the canonical 31-bit digest helper and standalone BE1 fact reader. The reader checks exact scope, current synthetic eligibility, proof session/run/time/revocation, active session/profile, admitted membership, one-member audience, and IMAGE_ONLY mode; denials return no partial facts.

| Check | Result |
|---|---|
| Five new T2B tests | `51 passed` |
| Fixed CI 5-file set + 2 T1 tests | `227 passed, 4 skipped` |
| Supplemental prior set | **14 failed, 47 passed, 16 skipped** (was 61 passed, 16 skipped at R0). All 14 failures originate from `test_be2_synthetic_basis.py` constructing synthetic members with fabricated consent refs/revisions. |
| Focused `test_be2_synthetic_basis.py` rerun | **14 failed, 17 passed**; confirms the same fixture/invariant conflict. |
| `test_live_image_demo_api.py` | R0 result remains `31 failed, 1 passed`; root cause is the offline credential metadata socket described above. |
| Ruff check | `All checks passed` on all changed/new Python files, using `backend/pyproject.toml`. |
| Ruff format check | `7 files already formatted` (new Python files only). |
| mypy `--strict` | `Success: no issues found in 5 source files` with a per-run cache under the system temp directory. The default cache location failed to open its database; no source change was made for that tool issue. |
| `validate_harness.py` | `HARNESS_VALID`. |
| `validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` (5,985 publishable files scanned). |
| `validate_architecture.py` | `ARCHITECTURE_VALID`. |
| `git diff --check` | Clean. |

### Digest specification and vector

The helper accepts string-keyed scalar mappings only, serializes sorted compact JSON as UTF-8 with non-ASCII emitted directly, prefixes `sketch2life/context-revision/v1\n`, hashes with SHA-256, reads the first four bytes big-endian, masks with `0x7FFFFFFF`, and maps zero to one. The reader's exact input keys are frozen in §3 of the T2B plan, including consent state and proof revocation metadata. `session.revision` is excluded. One fixed test vector is `{"a":1,"b":true,"c":"x","d":null}` → `212040317`. The approximately 2^-31 collision probability makes this an equality-only stale-data fence, never a signature or authorization credential.

### Changed and created files

| File | SHA-256 |
|---|---|
| `backend/src/sketch2life/domain/assistance.py` | `BE7F33B7D58D825E1167BEE71CDD290C4087E93DBCE9C40A9A9FA1CD081C63F0` |
| `backend/src/sketch2life/contracts/schemas/assistance_requests.py` | `3C6D16420ECE19B3530B9B04BA86303EC733BD0A24D38DFAD6B1584300BA78EA` |
| `backend/src/sketch2life/application/services/assistance.py` | `CDD777E1E93A952AE94E536523A5D8F14F7D40D675FC278B4CDA361333EBD4C6` |
| `backend/src/sketch2life/infrastructure/assistance/context_revision.py` | `14165D3D2B0027A090553424B88F0BB5043C6EE3261C45371FE06CC191F8E7BE` |
| `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py` | `276A6ACF29D46D7550DE92A5BB4B82A27CDBBC371651AB4491B2723CE029CF3D` |
| `backend/tests/unit/test_member_fact_consent_rules.py` | `B8E790075F0C6C337EE67E2BBD3D7DCEC5249C5B0A4A92C7CA289C5138415C08` |
| `backend/tests/unit/test_context_revision.py` | `90776A36F1B0BBE7E4619A6859C7A04E97C816974A5F105B1C4B248A3F3DFCB6` |
| `backend/tests/unit/test_profile_age_invariant.py` | `B1B90D6ED2D7F4540012ECB3889EA457B5D7370FCDBD3F698EF8A6F87836855B` |
| `backend/tests/unit/test_be1_fact_reader.py` | `E7A5FC0D9AF6FBF83058C1D9C8EFB8D64E1F9A94B13A75F1A22BFE5A17865EA3` |
| `backend/tests/contract/test_be1_fact_reader_contract.py` | `DE7EEA3D101E50E018D98AB2670CC152E90246E909577A4EDA826E90D9C233BD` |
| `features/FEAT-064-current-flow-modal-vision-dev/plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md` | `DF95B180ACF702E7374837824BB83DF779B7B201E56EFDDA973369936286436A` |
| `features/FEAT-064-current-flow-modal-vision-dev/plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_REV2_20261101.md` | `FF8AB4C23AA31B4531AFEF1E6990093C6F1736DE15BF2522AC22A0F881576502` |

`approvals/TASK_APPROVAL.md` was appended only; its SHA-256 after the append is `A5488368EDFF435457C14B1850C191331A4B5434080BF6B9C3EB79C962804472`.

## R5 — commit gate

The first run did not stage or commit because the supplemental regression set was failing. See "Follow-up after R4" for the reconciliation and the amend. Nothing was pushed.

## Protected owner-local hashes

| File | SHA-256 |
|---|---|
| `docs/context/SOURCE_REGISTER.md` | `0B43E4BAEFF8D35082755DB5013DE926977AB4D62DDE6965401A9FA120D11498` |
| FEAT-063 `CONTEXT.md` | `E7C8143A80D214FFF7276B91176BB0FF1FF55304780367382FB12139B13C7F14` |
| FEAT-063 `status/STATUS.md` | `F1ADB7937E37866603B8F0C8161AC25824035042B477B3337FF429A23258988B` |
| `evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md` | `8BBFD0EDAA7CD6A2643A60387D701520D11241A0A7FDFA0D5CD18A53063FECB1` |
| `evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md` | `B61B06074665BA710C6FD552568B1F73415308808E464F0D29E9B5EC06B51263` |
| `evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md` | `93374E9643649B67CE4FE03A4CE08ACD3A4D6957C7DCD32C97ABE52667C5B293` |
| `plan/S1_DECISION_CARD_20261030.md` | `4D95D3031F8AF1634FE492D713053A3A0DBB201BD90E7752A4612F16A7564AEA` |

## Not done / not run

- T2C (`CanvasFacts`, `GroupRoster`, `current_turn`), runtime wiring, T3/B5/B6 code, and B4b remain not done.
- PostgreSQL, Alembic application, live end-to-end BE1→BE2, Modal, GPU, network and provider calls were not run.
- No push or real-child-data operation was performed.

## Follow-up after R4 (owner session, 2026-11-01)

Three changes, all inside the owner's instruction to gather the work into the existing unpushed commit:

1. `backend/tests/unit/test_be2_synthetic_basis.py` (from the earlier T2 commit): the base synthetic `MemberFact` now uses `consent_record_ref=None` and `consent_revision=None`; the `_member(**changes)` helper adds a legal consent reference and revision whenever the basis is changed away from `SYNTHETIC_DEV`; the mixed-audience case builds its REAL member through `_member`. Test intent is unchanged. SHA-256 after: `CA6067230001948FF92E62F72F29C9C315B632461A66EE0ABFA90125F693A84D`.
2. `backend/src/sketch2life/application/services/assistance.py` (`teacher_view`): the consent reference projection now emits `eligibility_basis` only when it is not `None`. The first projection change added `"eligibility_basis": null` to every legal consent reference, which broke the pinned FEAT-049 handoff example `tests/contract/test_assistance_request_contracts.py::test_handoff_examples_are_pinned_and_valid` and would have altered the published legal wire shape. SHA-256 after: `95F57BAD16D2310FBE868D59BE8DDC922123F75C39760EE112632C3FDE00A919`.
3. This report was updated to match.

Verification run from `backend/` (PYTHONPATH=src, no `BE1_TEST_DATABASE_URL`): 76 test files covering assistance, vision, child-response, sketch, ai_job, synthetic, BE1 and BE2 suites, lesson library, app composition, session API, OpenAPI catalog and the migration graph: **1964 passed, 19 skipped, 0 failed**. `tests/contract/test_live_image_demo_api.py` is excluded (known offline failure: boto3 S3 client initialisation blocked by the offline socket guard; unrelated to this change). Ruff check passes on the touched source files; mypy `--strict` passes on the four T2B source files; `validate_harness.py`, `validate_architecture.py`, `validate_repository_security.py` pass; `git diff --check` is clean. `test_be2_synthetic_basis.py` keeps one pre-existing Ruff `I001` import-order finding that is identical at HEAD.

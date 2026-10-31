# Task approval

- Status: AWAITING_APPROVAL
- Approver:
- Approved scope:
- Plan revision:
- Approved at:
- Notes:

## T0 - Contract, guard and execution-manifest freeze (documentation only)

- Status: APPROVED for the documentation-only T0 task below. This entry does not approve FEAT-064 implementation; the plan-level status above stays AWAITING_APPROVAL.
- Approver: Project owner, direct instruction on 2026-10-31 to record the T0 approval and run T0.
- Recorded timestamp: 2026-10-31 01:24:34 Asia/Saigon.
- Feature: FEAT-064 - current-flow Modal Vision dev pilot.
- Approved task plan: `plan/T0_CONTRACT_FREEZE_EXECUTION_PLAN_20261031.md`.
- Approved task plan SHA-256: `9C62504CD2AD018B47F7D36B8B64D47016FAE19D3D8C3FADD4C911C98925945E`.
- Parent plan pinned for reference: `plan/PLAN.md` revision 6, SHA-256 `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`; `DECISIONS.md` SHA-256 `FD7B9ED0943509B31C07284B2B42EA9FBA26EE203D68BAA09E512D5CD8230644`.
- Approved scope: produce `evidence/T0_CONTRACT_FREEZE_20261031.md`, `evidence/T0_GUARD_DISPOSITIONS_20261031.csv`, `evidence/T0_METHOD_INVENTORY_20261031.csv` and `evidence/T0_EXECUTION_MANIFEST_20261031.csv`: carry the owner decisions of 2026-10-31 into T0, give every one of the 14 eligibility guard sites a disposition, freeze the synthetic proof and schema representation proposal (option X), the source/render/admission contracts with concrete values, the gateway and status-read contracts, the invocation guard, retry and deadline policy with sourced numbers, the minimal durable-state inventory, the OwnerFenceV1 and analysis-only specification, the Windows witness and run-manifest specification with a draft residual-risk text, and the execution manifest for T1-T12. All items are proposals for the owner; every co-signature stays unsigned.
- Acceptance criteria: the seven checks in section 6 of the hash-identified T0 plan.
- Explicitly excluded: any code, API, schema, migration or Alembic change; tests, builds or any backend, database, MinIO, Modal or GPU operation; editing any approval record other than this entry, the FEAT-064 PLAN.md or DECISIONS.md, the FEAT-063 files, the SRS, register or ADRs; choosing owners, reviewers, signatures or risk acceptance on the owner's behalf; approving T1-T14; deployment; real child data.
- Approval basis: the owner's direct instruction above, applied to the exact documentation-only scope and acceptance criteria in the T0 plan. This entry is recorded before the work; the T0 plan must not change without a new entry. T1 (code), T12 (temporary database) and T13 (live Modal call) each need their own approval entry that pins its own hashes.

## T1 — BE1 synthetic eligibility implementation (B4a)

- Status: APPROVED for the bounded T1 scope below; schema-dependent implementation is blocked until the BE1 confirmation gate is met.
- Task type: code implementation; this approval does not change the plan-level `PLAN.md` status.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction on 2026-10-31 to commit and push T0, add the B4a plan, and record T1 approval.
- Recorded timestamp: 2026-10-31 02:13 Asia/Saigon.
- Approved plan: `plan/B4_T1_ELIGIBILITY_IMPLEMENTATION_PLAN_20261031.md`.
- Approved plan SHA-256: `131DDB39019572E9FFCC1B5CB21ABC848583637803E9227E518BBA3526E01E31`.
- Required T0 evidence SHA-256 pins:
  - `evidence/T0_CONTRACT_FREEZE_20261031.md`: `476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B`.
  - `evidence/T0_GUARD_DISPOSITIONS_20261031.csv`: `B02543FF2591BF4EF3B422E08E64865CF407299B6CE3FBBC88C8863BBD268F69`.
  - `evidence/T0_METHOD_INVENTORY_20261031.csv`: `F1AA5BF4C54FD24D87FAE5454AE1CE4D8E1191C992AAB17EC671FE5AE0DF6191`.
  - `evidence/T0_EXECUTION_MANIFEST_20261031.csv`: `3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`.
- Approved file allowlist (no other paths):
  - Create `backend/src/sketch2life/domain/eligibility.py`.
  - Edit `backend/src/sketch2life/infrastructure/persistence/be1_models.py` and `backend/src/sketch2life/infrastructure/persistence/core_store.py` only for the T0 synthetic-origin/proof representation and its narrow persistence methods.
  - Edit `backend/src/sketch2life/infrastructure/config/settings.py` only to add the synthetic-pilot opt-in, default `false`.
  - Edit `backend/src/sketch2life/interfaces/http/routers/be1_common.py`, `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py`, and `backend/src/sketch2life/interfaces/http/be1_runtime.py` only for the typed decision and selected T0 `SYNTHETIC_TYPED_ONLY` gates in the bounded flow.
  - Create `backend/alembic/versions/20261031_be1_synthetic_eligibility.py` as migration source only; do not execute or apply it.
  - Create `tools/synthetic_eligibility.py` as the local/test-only operator issue/revoke command; no public HTTP issuance path.
  - Create `backend/tests/unit/test_synthetic_eligibility.py` and `backend/tests/contract/test_be1_synthetic_pilot.py`.
  - Create `evidence/notes/T1_IMPLEMENTATION_REPORT_20261031.md`.
  - `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` and `be1_records.py` are read-only for T1; their legal-consent behavior must remain covered by tests.
- Approved checks: the five baseline CI test files, the two new test files above, Ruff and `mypy --strict` on edited Python paths, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check`; pytest `--basetemp` must be outside the repository and `BE1_TEST_DATABASE_URL` must remain unset.
- Approved acceptance: plan §§3–7 and AC1–AC9, including the bounded synthetic-only profile → join → admit → Start → group → turn → append-stroke flow, legal/legacy/pending/revoked denial, unchanged legal API gates, default-off operator issuance, fail-closed typed eligibility, and an implementation evidence report. This does not approve a PostgreSQL integration run, database service, Alembic command/application, BE2 changes, canvas image export, provider/Modal/GPU request, deployment, production-provider change, real child data, or any commit/push of T1 code.
- Required independent-owner gate: T0 records the BE1 schema owner confirmation for option X and the migration dependency as unresolved. The project owner's approval above is not a BE1 co-signature. Before P4 and any schema-dependent eligibility-guard edit, obtain written confirmation from `CaoDat-2410` for the exact `data_origin`/proof representation and migration dependency; if absent, stop at that gate without changing those files. Do not sign for BE1 or for `OwnerFenceV1`.
- Working-tree boundary: preserve the seven pre-existing FEAT-063 owner-local files; record their P0 SHA-256 values and verify unchanged at the end. Stage and commit only after a separate owner instruction for the T1 implementation commit.
- Approval basis: the project owner's direct instruction above, applied only to the pinned plan, exact T0 artifacts, allowlisted paths, checks and acceptance criteria. A plan or T0 hash change requires a new approval entry.

## T1 revision A - BE1 synthetic eligibility, Addendum A (P0-P3 authorized now)

- Status: APPROVED for T1 phases P0-P3 only. Phases P4-P7 stay blocked until the BE1 owner's written confirmation required by Addendum A7. This entry supersedes the earlier T1 entry for code authority. The plan-level status of FEAT-064 stays AWAITING_APPROVAL.
- Task type: code implementation, narrowly bounded to the files listed below.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction on 2026-10-31 to record the T1 revision A approval and to accept owner decisions D1, D2 and D3.
- Recorded timestamp: 2026-10-31 11:41:24 Asia/Saigon.
- Approved plan: `plan/B4_T1_ELIGIBILITY_IMPLEMENTATION_PLAN_20261031.md`, SHA-256 `131DDB39019572E9FFCC1B5CB21ABC848583637803E9227E518BBA3526E01E31`.
- Approved addendum: `plan/B4_T1_ADDENDUM_A_20261031.md`, SHA-256 `A8397E3944DEAF0B693E90248D86A33DCA0755E3CB21F6F52747CA272F2DEAA6`. Where the addendum and the plan disagree, the addendum wins for T1.
- Required T0 evidence SHA-256 pins:
  - `evidence/T0_CONTRACT_FREEZE_20261031.md`: `476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B`.
  - `evidence/T0_GUARD_DISPOSITIONS_20261031.csv`: `B02543FF2591BF4EF3B422E08E64865CF407299B6CE3FBBC88C8863BBD268F69`.
  - `evidence/T0_METHOD_INVENTORY_20261031.csv`: `F1AA5BF4C54FD24D87FAE5454AE1CE4D8E1191C992AAB17EC671FE5AE0DF6191`.
  - `evidence/T0_EXECUTION_MANIFEST_20261031.csv`: `3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`.
- Owner decisions recorded here:
  - D1: add `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` to the T1 scope for the stroke-append call site only, through a separate helper; checkpoint, restore, sync and reconnect keep the legal-only gate. This path is authorized in principle but its edit is part of the blocked phase P5.
  - D2: the existing `consent_ready` parameter is reused and means "eligibility ready"; this is an intentional override of the T0 G13 negative invariant; `application/services/be1_runtime.py` is not changed.
  - D3: a synthetic proof is valid only when its `run_ref` equals `session.configuration["pilot_run_ref"]`; a missing value denies.
- Authorized now (P0-P3), and no other path may be created or edited:
  - Create `backend/src/sketch2life/domain/eligibility.py`.
  - Create `backend/tests/unit/test_synthetic_eligibility.py` (pure domain tests and static migration checks, no database).
  - Create `backend/tests/contract/test_be1_synthetic_pilot.py` (guard-level and static wiring tests; tests that need P5 are strict xfail).
  - Create `features/FEAT-064-current-flow-modal-vision-dev/evidence/notes/T1_IMPLEMENTATION_REPORT_20261031.md`.
- Still blocked: P4 persistence and migration, P5 guard wiring including `be1_canvas.py`, P6 operator tool, P7, and any change to `settings.py`. They open only after the BE1 owner (`CaoDat-2410`) confirms in writing the `data_origin` enum, the proof table shape, the migration parent and the `be1_canvas.py` append change, and a new approval entry authorizes them. An approval by the project owner or a relayed message does not count as that confirmation.
- Explicitly excluded: any database, Alembic, backend service, MinIO, Modal, GPU or network operation; real child data; BE2 changes; editing any approval record other than this entry; editing any file not listed above; commit or push without a later owner instruction.
- Approval basis: the owner's direct instruction above, applied to the exact scope and acceptance criteria in the hash-identified plan and addendum. The plan and addendum must not change without a new entry.

## T1 revision B - BE1 synthetic eligibility, P4-P9 before BE1 confirmation (local working tree only)

- Status: APPROVED for T1 phases P4-P9 in the local working tree only. No stage, commit or push of any T1 file without a later owner instruction. This entry supersedes the P4-P7 block in the T1 revision A entry for code authority. The plan-level status of FEAT-064 stays AWAITING_APPROVAL.
- Task type: code implementation, bounded to the Addendum B file allowlist (B8).
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction on 2026-10-31 ("Ghi approval rồi làm", given after the draft entry text was shown) to record this entry and implement P4-P9 first and correct later.
- Recorded timestamp: 2026-10-31 12:06 Asia/Saigon.
- Approved plan: `plan/B4_T1_ELIGIBILITY_IMPLEMENTATION_PLAN_20261031.md`, SHA-256 `131DDB39019572E9FFCC1B5CB21ABC848583637803E9227E518BBA3526E01E31`.
- Approved addenda: `plan/B4_T1_ADDENDUM_A_20261031.md`, SHA-256 `A8397E3944DEAF0B693E90248D86A33DCA0755E3CB21F6F52747CA272F2DEAA6`; `plan/B4_T1_ADDENDUM_B_20261031.md`, SHA-256 `3D25743B7278186F11D0F6AC3F02F0DF145CED68772FFD9FA41B3140EBEAD402`. Where they disagree, Addendum B wins for P4-P9 and Addendum A wins elsewhere.
- Required T0 evidence SHA-256 pins: same four files and hashes as in the T1 revision A entry.
- Authorized now: exactly the paths in Addendum B section B8, and no other path.
- Deliberate acceptance: the BE1 owner's written confirmation required by Addendum A7 and Addendum B B1 is NOT present. The project owner chooses to proceed using the PROPOSAL values in Addendum B (names, columns, revision id `20261031_be1_se_0001`, parent `20261024_0005`, setting key) and to rework code and migration if `CaoDat-2410` changes any of them. This entry is not a BE1 co-signature and does not sign `OwnerFenceV1`.
- OD-B1 accepted: successful synthetic audit entries are written only at admit, Start, group assignment and turn, and every denial is audited; no successful-audit write per device check or per stroke.
- Explicitly excluded: any database, Alembic command or application, backend service, MinIO, Modal, GPU or network operation; real child data; BE2 changes; editing any approval record other than this entry; editing any file outside B8; any commit or push.
- Approval basis: the owner's direct instruction above, applied to the exact scope and acceptance criteria in the hash-identified plan and addenda. The plan and addenda must not change without a new entry.

## T1 revision C - BE1 synthetic eligibility, recorded deviations after two independent reviews (local working tree only)

- Status: APPROVED as a record of owner decisions on top of the T1 revision B entry. It adds no path to the revision B allowlist (Addendum B section B8), authorizes no new phase, and keeps every restriction of revision B: local working tree only, no stage, commit or push of any T1 file without a later owner instruction. The plan-level status of FEAT-064 stays AWAITING_APPROVAL.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction on 2026-10-31 ("Ghi mục approval") to record this entry, given after the review findings and the two decisions below were shown.
- Recorded timestamp: 2026-10-31 14:35 Asia/Saigon.
- Pinned context, unchanged: plan `plan/B4_T1_ELIGIBILITY_IMPLEMENTATION_PLAN_20261031.md` SHA-256 `131DDB39019572E9FFCC1B5CB21ABC848583637803E9227E518BBA3526E01E31`; Addendum A SHA-256 `A8397E3944DEAF0B693E90248D86A33DCA0755E3CB21F6F52747CA272F2DEAA6`; Addendum B SHA-256 `3D25743B7278186F11D0F6AC3F02F0DF145CED68772FFD9FA41B3140EBEAD402`; the four T0 files as in the T1 revision A entry. The addenda were not edited.
- Decision C1 (session binding is mandatory): a synthetic proof counts only if it names the exact session (`session_id` set and equal to the current session). This is stricter than Addendum A section A4 and Addendum B section B2, where `session_id` is optional, and where the two disagree, this entry wins for T1. Reason: `session.configuration["pilot_run_ref"]` is written by whoever creates the session, so the run alone does not identify the operator's intended session. Implementation: policy in `be1_common.py` (a session-less proof for a `SYNTHETIC_DEV` profile is treated as no proof) and `tools/synthetic_eligibility.py issue` requires `--session-id`. D3 is read accordingly: `pilot_run_ref` must equal the proof's `run_ref` and the proof must be bound to the session; the run value itself is not trusted as a client-independent fact.
- Decision C2 (`policy_version` and issue-time pilot state are audit data): `policy_version` is stored on the proof and `pilot_enabled` at issuance is not stored; neither is an eligibility condition. The pilot setting is re-checked at every decision and the tool refuses to issue while it is off. This resolves the T0 binding list for T1 as audit-only; a matching-`policy_version` requirement would need a new entry.
- Changes made after review that stay inside the revision B allowlist and are recorded here for the reviewer: `eligibility_all_ready` (success audit at Start only after every Child passes); a missing or inactive profile falls back to the pre-existing legal-only lookup and can never be synthetic; the proof table is read only for a `SYNTHETIC_DEV` profile; `consent_is_effective` accepts a missing purpose and returns false; the operator tool and `create_synthetic_profile` accept only `synthetic-` ids with a derived `Synthetic ...` name, and the free-text display-name option was removed; ORM foreign keys carry the migration's names; the proof lookup has an `evidence_id` tiebreaker.
- Still open and not decided here: the BE1 owner's written confirmation of the PROPOSAL names and migration; writer and reviewer for `settings.py`, the migration and the tool (T0 O13, O16); L-3 of the first review (substring `be1_acceptance`, self-declared `issued_by`, no `revoked_by`); every PostgreSQL, Alembic and end-to-end check (T12).
- Explicitly excluded: any database, Alembic command or application, backend service, MinIO, Modal, GPU or network operation; real child data; BE2 changes; editing any file outside Addendum B section B8; editing any approval record other than this entry; any stage, commit or push.
- Approval basis: the owner's direct instruction above, applied to the decisions C1 and C2 and to the list of recorded changes. The plan and addenda must not change without a new entry.

## T2B/T3 owner decisions — documentation and publication only (2026-11-01)

- Status: **APPROVED for recording the selected design decisions, creating the T2B/T3 plans, and one documentation-only commit/push. This does not approve implementation.** The parent FEAT-064 plan remains `DRAFT / NOT_STARTED`.
- Approver: Project owner, direct instruction on 2026-11-01 to “commit and push” after the T2B/T3 decision ballot was answered.
- Recorded at: 2026-11-01, Asia/Saigon.
- Approved decision-record plan: `plan/PLAN_REV2_OWNER_DECISION_RECORD_20261101.md`, SHA-256 `DE455C77CFB687086A01194E628AB00EEC9E851C3E9258915561D4EE186916A2`.
- Decision plans:
  - `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_20261101.md`, SHA-256 `781A561AEC08BF0990AA18CBDBD27DB7CEB84CB23EA3CDD5ABB483A6A10D83C7`.
  - `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_20261101.md`, SHA-256 `D948F8DCAB9FDCF0EACBF3B0D4DB5C88914A6A17BC61D7001E1C3B1C28D61DA2`.
- Approved file scope: exactly the ten paths listed in Plan Rev2 §“Exact file scope” (three plan files, feature source register, decision evidence, decision/context/status ledgers, evidence index and this approval entry).
- Accepted decisions: T2B A1 `Sửa`, A2 `Đồng ý`, A3 `Sửa`, A4/A5 `Để sau`, A6 `Đồng ý`; T3 B1–B4 `Đồng ý`, B5 `Đồng ý A`, B6 `Đồng ý B`, B7 `Đồng ý`, B8 `Sửa/blocked`. Exact conditions and implementation gates are in the pinned decision plans.
- B8 implementation boundary: the original owner-referenced T3 §1 allowlist was unavailable on the base branch and could not be located locally. This documentation approval authorizes no T3 source/test path; restore or separately approve the exact list before implementation.
- A3 contract note: source review found BE2 `ContextDecision.context_revision` is an integer and current comparisons are equality checks. Preserve that field; add an explicit versioned context digest and compare it for whole-context freshness. Do not coerce a digest into the integer field.
- Publication target: `feature/feat063-be-foundation`, based on remote `3ca9c1593d4a0e7d449a65ef08ff33d5c0a5b269`. The reported `578f3e5e` cannot be resolved in this checkout or fetched from origin; this approval authorizes a new forward documentation commit from the current remote tip, not a force-push.
- Explicitly excluded: source/code edits, tests, migration creation/application, PostgreSQL/database setup or access, Docker/MinIO, Modal/GPU/provider calls, real-child data, B4b, sending a message to Hiếu, any T1 implementation commit, or any change beyond the exact file scope above.
- Acceptance criteria: Plan Rev2 AC1–AC7; security validator and `git diff --check` must pass before publication; push normally and verify the remote ref.
- Approval basis: the owner's direct “commit and push” instruction applied to the decisions returned immediately before this entry. T2B/T3 implementation requires separate approvals pinning its own scope and hashes.

## T2 — guard đọc trạng thái và cổng BE2

- Status: APPROVED cho phạm vi local P2 và P3 trong handoff owner ngày 2026-11-01; không cấp quyền tạo HTTP route, adapter production BE1→BE2, DB/Alembic, Modal/GPU, push hoặc thay đổi ngoài allowlist. Plan-level status của FEAT-064 vẫn AWAITING_APPROVAL.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), chỉ thị trực tiếp trong prompt owner ngày 2026-11-01 (quyết định B.2 và cho phép chạy tất cả pha P0–P6 một mạch).
- Approved plan: `plan/T2_ACTOR_AUTHORITY_STATUS_READ_PLAN_20261031.md`, SHA-256 `2E2DC371AAD85AA66DC5B65C556748EF3F145815382FC92FCA02377A292EE2C8`.
- Pinned T0 evidence: `evidence/T0_CONTRACT_FREEZE_20261031.md` SHA-256 `476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B`; `evidence/T0_GUARD_DISPOSITIONS_20261031.csv` SHA-256 `B02543FF2591BF4EF3B422E08E64865CF407299B6CE3FBBC88C8863BBD268F69`; `evidence/T0_METHOD_INVENTORY_20261031.csv` SHA-256 `F1AA5BF4C54FD24D87FAE5454AE1CE4D8E1191C992AAB17EC671FE5AE0DF6191`; `evidence/T0_EXECUTION_MANIFEST_20261031.csv` SHA-256 `3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`.
- Baseline: commit `6910b603daac4f7f75bd090467d57f7ed7ea8ec3`; Addendum A SHA-256 `A8397E3944DEAF0B693E90248D86A33DCA0755E3CB21F6F52747CA272F2DEAA6`; Addendum B SHA-256 `3D25743B7278186F11D0F6AC3F02F0DF145CED68772FFD9FA41B3140EBEAD402`.
- Owner decisions: status-read permits session states `active` and `paused`; perform both Part A and Part B only at the BE2 gate/contract layer; call the same typed `eligibility_ready` decision without a success audit. Synthetic eligibility leaves `consent_effective` and `purpose_granted` false and requires basis version `eligibility-decision-v1`, nonempty evidence reference, and exact request-scope/purpose binding. No production adapter is authorized or claimed.
- Authorized P2 paths: `backend/src/sketch2life/interfaces/http/be1_runtime.py` and new `backend/tests/unit/test_synthetic_status_guard.py`.
- Authorized P3 paths: `backend/src/sketch2life/domain/assistance.py`; `backend/src/sketch2life/domain/vision_analysis.py`; `backend/src/sketch2life/application/ports/assistance.py`; `backend/src/sketch2life/application/ports/vision_analysis.py`; `backend/src/sketch2life/application/services/assistance.py`; `backend/src/sketch2life/application/services/vision_analysis.py`; `backend/src/sketch2life/contracts/schemas/analysis_results.py`; `backend/src/sketch2life/contracts/schemas/analysis_context_results.py`; `backend/src/sketch2life/contracts/schemas/assistance_requests.py`; and new `backend/tests/unit/test_be2_synthetic_basis.py`, `backend/tests/contract/test_be2_synthetic_basis_contract.py`.
- Source pins from handoff §D (SHA-256 prefixes): `be1_runtime.py` DC565DAA2F45FBC9; `domain/assistance.py` AB4DF2971BD403C2; `domain/vision_analysis.py` CB36B2917EC0E906; `application/ports/assistance.py` 5E205659F2ABBE3F; `application/ports/vision_analysis.py` 2F36D096127930A2; `application/services/assistance.py` 5BFFF0481F7D3015; `application/services/vision_analysis.py` F30CCBBB5BE5AF36; `contracts/schemas/analysis_results.py` 46C6F47A37983293; `contracts/schemas/analysis_context_results.py` 3844377F4FA114FD; `contracts/schemas/assistance_requests.py` 2C2DF0B574E2C5BB. The P1 migration-test file and P0 B1/approval inputs were changed only as authorized by the same owner prompt before this entry.
- Explicit exclusions: no DB, Alembic, Modal, GPU, network, route, production BE1→BE2 adapter, UI, `be1_registry.py`, `be1_records.py`, `infrastructure/**/fakes.py`, `context_adapter.py`, Rev36, ADR-0022, or real child data. The missing production adapter remains NOT DONE.
- Approval basis: the owner's direct instruction in this session, applied to the pinned plan, T0 evidence, baseline commit, exact file allowlist, and decisions above. This entry is not a BE1-owner confirmation or co-signature.

## T2B — adapter BE1→BE2 offline

- Status: APPROVED for the bounded T2B inventory/plan and the allowlisted offline adapter attempt; **implementation NOT DONE** because the current BE1 sources do not provide required age/consent/context/roster revision facts and the synthetic `MemberFact` has no honest consent reference. No missing fact is inferred or fabricated.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this chat on 2026-10-31 to execute `CODEX_PROMPT_NEXT2_PG_ADAPTER_T3PLAN_20261101.md` through Q0–Q6 and to append the task approval required by Q2.
- Approved plan: `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md`.
- Approved plan SHA-256: `5830B2E1712615DB10C7775C71A59F13B2B71E013BCBB1BD0EBA1F351CC128AB`.
- Baseline commit: `d7adeec2c23c867edc599c63d8af46cea150bbc3`.
- Pinned current source hashes (SHA-256):
  - `backend/src/sketch2life/domain/assistance.py`: `E0F2A0B680CAEE2B369A46A08341E30632B7E3FD3895B814B019BB59E4548FD2`.
  - `backend/src/sketch2life/domain/vision_analysis.py`: `CB36B2917EC0E9061C21DCA4B1AC27316F57E329FC3CAAFBD78AD1FA41F3DFA5`.
  - `backend/src/sketch2life/application/ports/assistance.py`: `5E205659F2ABBE3F3AD5E5459F05A64139D51DCE8A7DB19B60FD3426BD90E338`.
  - `backend/src/sketch2life/application/ports/vision_analysis.py`: `B0CB4A3466477B7A4394FA4E26D4EBF43A269936A22CFB189DE0B8089226FA2B`.
  - `backend/src/sketch2life/application/services/assistance.py`: `F6A606A70B8705E3FB54505D2E8923BFC3F03ACEF7BBA7563E71F2F89DAA789D`.
  - `backend/src/sketch2life/application/services/vision_analysis.py`: `EF6785E18243F89A352C36C6284B5003B0165718B56E1BDCF744C8A810C431FB`.
  - `backend/src/sketch2life/infrastructure/persistence/be1_models.py`: `735599B638090ABAD59CE3FBFB9630708C3A3DDB2F199994DD3C106B597E38D3`.
  - `backend/src/sketch2life/infrastructure/persistence/core_store.py`: `7E96852E81AEBBAE9985F03E07B49F9F8A94001C220FFEA6236417C90C213FD4`.
  - `backend/src/sketch2life/domain/eligibility.py`: `6B84DD889083959218B8FD32219BD25C20356C20EA49ADDD7361FA4682D7396B`.
  - `backend/src/sketch2life/interfaces/http/routers/be1_common.py`: `40DDE6F9B2AC91A78FE2A2F65B15EFCB1B76D132D49BB5580338710B12B9C45C`.
  - `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`: `A2CFE7C0B5998FAF9D56C33ED5A2C5E7E203892855FDC154BA1996B1A489D8ED`.
  - `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`: `285CBEEDEFDEF30CCF9C0A35DD7014824CBC7D87F66C5C3A03BB9A58BB302B68`.
  - `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py`: `C0CE27189CBFA362CF172BBDC77D5E9C64F98082AC64CAECD99F5EE46E2F1D11`.
  - `backend/src/sketch2life/infrastructure/persistence/core_models.py`: `61418A3F7015862B7A8B2037C9422113DF1E73311124E227DDE4197D12AC6EC3`.
- Allowlist: create this T2B plan; append this approval entry; the proposed future code paths are `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py`, `backend/tests/unit/test_be1_fact_reader.py`, and `backend/tests/contract/test_be1_fact_reader_contract.py`. Those three code files were **not created** in this execution. The only output for T2B is this plan and approval entry.
- Stop disposition: Q2 stopped after the static inventory and plan under its explicit stop clause. The missing source fields and unresolved contract semantics require owner decisions; implementation must not resume by selecting sentinel references, synthetic consent, timestamps, session revisions, or other inferred values. Any schema/contract scope change needs a new plan/approval pin.
- Explicit exclusions remain: router/runtime/composition wiring, BE1/BE2 schema or migration, fakes, database/Alembic, MinIO, Modal/GPU, network, real child data, and provider calls. This approval is not a production-readiness claim.
- Approval basis: the project owner's direct instruction in this chat, applied only to the hash-identified T2B plan, source inventory, stop disposition and exact paths above.

## T2B — adapter BE1→BE2 offline (quyết định A1-A6 ghi)

- Status: APPROVED for the bounded offline implementation and test scope in the owner-approved plan. This approval supersedes the prior T2B stop disposition above only for the paths and behavior named here; it does not approve runtime wiring or live inference.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this chat on 2026-11-01 (the T2B/T3 decision block B).
- Approved plan: `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md`.
- Approved plan SHA-256: `DF95B180ACF702E7374837824BB83DF779B7B201E56EFDDA973369936286436A`.
- Starting HEAD: `578f3e5ee53ba841a83352a133141cfe80b8c672` (Case X; amend of the existing local, unpushed commit is permitted only at the final R5 gate).
- Owner decisions recorded: A1 write-once age, fixed age revision 1 and `be1-profile-age-v1:{child_id}`; A2 consent references/revision are both null iff the basis is `SYNTHETIC_DEV`, enforced in `MemberFact` and Teacher DTO; A3 shared canonical 31-bit context digest with exact payload/schema in the plan; A4 `CanvasFacts`, `GroupRoster`, `current_turn` deferred to T2C; A5 exactly one audience member; A6 synthetic pilot is IMAGE_ONLY, typed context synthetic denied, legal/real paths fail closed pending B4b.
- Pinned input SHA-256:
  - `backend/src/sketch2life/domain/assistance.py`: `E0F2A0B680CAEE2B369A46A08341E30632B7E3FD3895B814B019BB59E4548FD2`.
  - `backend/src/sketch2life/contracts/schemas/assistance_requests.py`: `2C2DF0B574E2C5BB846C8E3C6688F1291966357F94F02AE83356886F7A5B62A2`.
  - `backend/src/sketch2life/application/services/assistance.py`: `F6A606A70B8705E3FB54505D2E8923BFC3F03ACEF7BBA7563E71F2F89DAA789D`.
  - `backend/src/sketch2life/application/services/vision_analysis.py` (read-only): `EF6785E18243F89A352C36C6284B5003B0165718B56E1BDCF744C8A810C431FB`.
  - `backend/src/sketch2life/domain/vision_context.py` (read-only): `9501F2194A2896DF121C50AF2A1DF29B7003C7F2029AF0FEBD461664886E04EB`.
  - `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md`: `DF95B180ACF702E7374837824BB83DF779B7B201E56EFDDA973369936286436A`.
  - `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_DRAFT1_20261101.md` (read-only): `8BD963281672AB97599E2B26CBA500AB629C5F3BAF076ED48B1735E1FEFA1F70`.
- Protected owner-local SHA-256 pins (must remain byte-identical): `docs/context/SOURCE_REGISTER.md` `0B43E4BAEFF8D35082755DB5013DE926977AB4D62DDE6965401A9FA120D11498`; FEAT-063 `CONTEXT.md` `E7C8143A80D214FFF7276B91176BB0FF1FF55304780367382FB12139B13C7F14`; FEAT-063 `status/STATUS.md` `F1ADB7937E37866603B8F0C8161AC25824035042B477B3337FF429A23258988B`; `evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md` `8BBFD0EDAA7CD6A2643A60387D701520D11241A0A7FDFA0D5CD18A53063FECB1`; `evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md` `B61B06074665BA710C6FD552568B1F73415308808E464F0D29E9B5EC06B51263`; `evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md` `93374E9643649B67CE4FE03A4CE08ACD3A4D6957C7DCD32C97ABE52667C5B293`; `plan/S1_DECISION_CARD_20261030.md` `4D95D3031F8AF1634FE492D713053A3A0DBB201BD90E7752A4612F16A7564AEA`.
- Authorized code paths: `backend/src/sketch2life/domain/assistance.py`; `backend/src/sketch2life/contracts/schemas/assistance_requests.py`; only the synthetic-null Teacher projection in `backend/src/sketch2life/application/services/assistance.py`; new `backend/src/sketch2life/infrastructure/assistance/context_revision.py`; new `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py`.
- Authorized test paths: new `backend/tests/unit/test_member_fact_consent_rules.py`, `backend/tests/unit/test_context_revision.py`, `backend/tests/unit/test_profile_age_invariant.py`, `backend/tests/unit/test_be1_fact_reader.py`, and `backend/tests/contract/test_be1_fact_reader_contract.py`.
- Authorized documentation: the approved T2B plan above; new T3 REV2 plan below; new T2B implementation report; this append-only approval entry. No other file may be changed.
- Explicit exclusions: no routes/runtime/composition, fakes, `domain/vision_context.py`, `domain/vision_analysis.py`, BE1 models/core store/Alembic, UI, B5/B6 implementation, T2C, B4b, PostgreSQL, Modal/GPU, network, provider call, or real child data. This approval is not a production-readiness claim.

## T3 — quyết định B1-B8 ghi, code CHƯA duyệt

- Status: APPROVED for recording owner decisions and current blockers in the documentation plan only; T3 implementation remains NOT APPROVED.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this chat on 2026-11-01 (the T3 decision block).
- Approved plan: `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_REV2_20261101.md`.
- Approved plan SHA-256: `FF8AB4C23AA31B4531AFEF1E6990093C6F1736DE15BF2522AC22A0F881576502`.
- The plan records B1–B8 for documentation: square white 1:1 canvas and 1024×1024 RGB export target; width tokens 5/9/14 mapped to ratios and rendered relative to canvas width; no one-point dot and client/server minimum of two points; server-owned `CanvasOperationProfileV1` based on append-time synthetic eligibility and stored on each operation; selected B5 separate read-only Child canvas route for active/paused with current eligibility checks; selected B6 session-scoped Teacher lobby candidate route with proof/session/pilot filters and only child id/display name; B5/B6 before or parallel with T3; exact future T3 file allowlist remains unapproved.
- Verified blockers recorded: reconnect remains legal-only and turn-bound; class-wide profile list is consent-effective-only and rejects synthetic profiles under the current CHECK/lookup; generic Teacher-supplied session configuration does not select a trusted profile or authorize the CanvasOperationProfile.
- No code, route, DTO/schema, migration, UI or test path is approved by this T3 entry. Any implementation needs a separate approval with exact paths and tests.

## Review fixes — T2/T2B/B5 (chỉ thị owner 2026-11-01)

- Status: APPROVED cho phạm vi local sửa các phát hiện của review độc lập (PASS WITH NOTES) về T2, T2B và B5; chỉ gồm test và một thay đổi domain nhỏ nêu dưới đây. Không cấp quyền route, runtime, migration, PostgreSQL, adapter production, push hoặc thay đổi ngoài allowlist. Plan-level status của FEAT-064 vẫn AWAITING_APPROVAL.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), chỉ thị trực tiếp trong prompt owner ngày 2026-11-01 (mục B của `CODEX_PROMPT_REVIEW_FIXES_20261101.md`). Mục này không phải xác nhận hay đồng ký của chủ sở hữu BE1.
- Baseline commit: `f1f977478bd8d015fa83ec148c35d00f3576348a`.
- Allowlist sửa: `backend/tests/unit/test_profile_age_invariant.py`; `backend/tests/unit/test_synthetic_status_guard.py`; `backend/tests/unit/test_be1_fact_reader.py`; `backend/tests/unit/test_be2_synthetic_basis.py`; `backend/src/sketch2life/domain/assistance.py` (chỉ giới hạn audience synthetic); `backend/src/sketch2life/domain/eligibility.py` (chỉ hằng dùng chung `SYNTHETIC_AUDIENCE_SIZE`); `features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.csv` và `.md` (chỉ cột `needs_owner` và câu mô tả của C022-C024); append mục này vào `approvals/TASK_APPROVAL.md`.
- Allowlist tạo mới: `backend/tests/unit/test_synthetic_audience_limit.py`; `backend/tests/unit/test_vision_service_typed_context_synthetic.py`; `evidence/notes/REVIEW_FIXES_REPORT_20261101.md`.
- Không sửa: router/runtime, migration, `be1_fact_reader.py`, `context_revision.py`, `service.py` của Lesson Library, và các file owner-local. Nếu một test mới chứng minh lỗi thật trong `be1_fact_reader.py`/`context_revision.py` thì phải nêu lỗi và tái hiện trong báo cáo trước khi sửa tối thiểu.
- Quyết định owner: L1 giữ như hiện tại (đường legal của `MemberFact` chặt hơn là chấp nhận được). L6 (audit mỗi lần từ chối ở guard trạng thái) và L7 (`revision_source="recorded"` chưa được phát ra): KHÔNG sửa, ghi nhận để làm sau. B5 blocker trong B1 không đổi (B5 mới có test offline, replay PostgreSQL chưa kết luận).
- Chú thích bổ sung cho allowlist T2 (không sửa mục T2 ở trên): `backend/tests/integration/ai_jobs/test_migrations.py` (cập nhật `BE1_CHAIN` cho head `20261031_be1_se_0001`) đã được sửa trong phạm vi T2/P1 và được ghi nhận ở đây như một đường dẫn thuộc allowlist T2.
- Approval basis: the project owner's direct instruction in this session, applied only to the exact paths and decisions above.

## T12-lite — chạy PostgreSQL thật

- Status: APPROVED for the bounded PostgreSQL rehearsal in this entry, per the project owner's direct instruction in this chat on 2026-11-01.
- Database boundary: one disposable local database whose name contains `be1_acceptance`, connected only through loopback; proceed only after the connection and clean-schema checks pass.
- Connection provenance: file local ignore do owner tạo. Its path and value must not be recorded or published.
- Authorized writes: repository Alembic migrations and rows created by the listed T12-lite tests with `synthetic-<uuid>` identifiers or test-owned unique data. Do not DROP/TRUNCATE, delete non-test data, access another database, or connect off loopback.
- Test scope: `tests/integration/test_be1_postgres_api.py`; `tests/integration/lesson_library/test_lesson_library_api.py`; database-gated tests under `tests/integration/`, including `ai_jobs/`; and the new `tests/integration/test_be1_synthetic_pilot_postgres.py` specified by this task.
- Record actual test and migration results even if NOT RUN. Modal/GPU and real child data are excluded.

## T2B rework theo bản ghi owner (chỉ thị owner 2026-11-01)

- Status: APPROVED cho implementation/test offline và rehearsal PostgreSQL có điều kiện trong phạm vi plan được pin bên dưới.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), chỉ thị trực tiếp trong phiên ngày 2026-11-01 yêu cầu thực hiện toàn bộ `CODEX_PROMPT_T2B_REWORK_TO_RECORD_20261101.md`.
- Approved plan: `plan/T2B_REWORK_TO_OWNER_RECORD_PLAN_20261101.md`.
- Approved plan SHA-256: `959C9AB6739826F6C8AB53EB4AC7C49ACAD8DBDF629E5564291A615B86657DE6`.
- Quyết định được pin: cột `age_revision`/`age_source`; enum đúng ba giá trị `LEGACY_UNKNOWN`, `SYNTHETIC_FIXTURE`, `ADULT_DECLARED`; migration `20261101_be1_age_0001` có parent duy nhất `20261031_be1_se_0001`; `ContextDecision.context_digest` dạng `sha256:<64 lowercase hex>` song song với integer `context_revision`; quy tắc synthetic consent và phạm vi A4–A6 giữ như bản ghi owner.
- Allowlist và loại trừ: đúng các đường dẫn và ranh giới trong §4–§5 của plan đã pin. Không mở rộng allowlist nếu consumer cần thay đổi khác.
- Phạm vi DB: một database local dùng một lần, tên chứa `be1_acceptance`, kết nối loopback sau khi mọi safety gate đạt; chỉ migration Alembic của repo và hàng test synthetic có tiền tố `synthetic-`/dữ liệu riêng của test được tạo rồi dọn. Không DROP/TRUNCATE, không xóa dữ liệu khác, không database khác, không Modal/GPU, không provider từ xa, không dữ liệu thật của trẻ.
- Giới hạn: chưa xác nhận end-to-end. Nếu BE2 claim/gateway integer-only không mang digest, digest-bearing synthetic context bị từ chối trước provider; phần truyền digest qua AI Jobs cần approval riêng.
- Basis: chỉ thị owner trực tiếp trong phiên này; đây không phải chữ ký hay xác nhận thay cho người khác.

## T3 B8 — allowlist được owner xác nhận (chưa cho phép code)

- Status: APPROVED chỉ để ghi nhận allowlist tài liệu; T3 implementation remains NOT APPROVED.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), chỉ thị trực tiếp trong phiên ngày 2026-11-01.
- B8 được giải quyết bằng đúng bảng “proposed T3 allowlist” tại §1 của `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_DRAFT1_20261101.md`, SHA-256 `8BD963281672AB97599E2B26CBA500AB629C5F3BAF076ED48B1735E1FEFA1F70`.
- Không thêm đường dẫn nào. T3 code vẫn cần approval riêng pin plan T3 và reviewers; mục này không duyệt code, tests, migration, UI hay runtime.

## T2B rework — điều chỉnh sau review độc lập (chỉ thị owner 2026-11-01)

- Status: APPROVED cho fixup giới hạn dưới đây và rehearsal PostgreSQL local đã mô tả trong prompt owner `CODEX_PROMPT_T2B_FIXUP_20261101.md`.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), chỉ thị trực tiếp trong phiên ngày 2026-11-01. Đây không phải chữ ký hay xác nhận thay cho người khác.
- Allowlist sửa: `backend/tests/unit/test_synthetic_eligibility.py`; `backend/tests/unit/test_be2_synthetic_basis.py`; `backend/tests/unit/test_vision_service_typed_context_synthetic.py`; đúng hai fixture `ManagedProfileModel` trong `backend/tests/integration/test_be1_postgres_api.py`; teardown fixture `lesson_api_acceptance` trong `backend/tests/integration/lesson_library/test_lesson_library_api.py`; bổ sung mục fixup vào `evidence/notes/T2B_REWORK_REPORT_20261101.md`; chỉ append mục approval này. Không cấp quyền sửa product source, migration, plan, owner decision record hay file khác.
- Quyết định: không thêm `server_default='LEGACY_UNKNOWN'` cho `age_source`; writer phải cung cấp provenance. Ghi nhận theo chỉ thị owner rằng các quyết định D-114→D-119 và plan `B4B_REAL_CONSENT_LIFECYCLE_PLAN_20261101.md` trước đó chưa có approval riêng; mục này ghi nhận chúng theo chỉ thị hiện tại. `backend/tests/integration/ai_jobs/test_migrations.py` đã nằm trong allowlist T2/P1 trước đó.
- Phạm vi PostgreSQL: chỉ DB disposable local loopback có tên chứa `be1_acceptance`, chạy migration/test và dọn chính xác hàng synthetic do các test trong lượt này tạo; không DROP/TRUNCATE, không xóa 10 synthetic organization đã tồn tại, không Modal/GPU/provider ngoài.
- Kết quả rehearsal được ghi trong `evidence/notes/T2B_REWORK_REPORT_20261101.md`: các sửa unit regression; BE1 API 3 passed/1 lỗi `CONSENT_NOT_EFFECTIVE` đã biết; age provenance 1 passed; synthetic pilot 4 passed; Lesson Library 5 passed/1 lỗi ClamAV không sẵn sàng; downgrade/upgrade thành công khi profile count bằng 0 và 10 revision hiện tại khớp heads.
- Phạm vi không kết luận production readiness; digest chưa được truyền qua public Vision claim hoặc AI Jobs, PostgreSQL adapter `BE1FactSource`, T2C, UI routes, B4b implementation và luồng BE1→BE2 end-to-end vẫn chưa làm. Không chạy Modal/GPU, không dùng dữ liệu thật của trẻ.

## G1 — BE1 canvas profile, Child reconnect, Teacher pilot profiles

- Status: APPROVED only for the three bounded G1 tasks below, under the project owner's direct instruction in `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` on 2026-11-01. This does not set the overall FEAT-064 plan status to approved or reviewed.
- Owner decision source: §D G1 and §E. The G1 contract there supersedes older T3 draft behavior for profile binding, Child reconnect, and Teacher lookup. No reviewer or co-owner confirmation is claimed.

### T3 — BE1 canvas operation profile

- Approved plan: `plan/T3_BE1_CANVAS_PROFILE_IMPLEMENTATION_PLAN_20261101.md`.
- Approved plan SHA-256: `EA64582E34790177187DA22B7AF5CA8988EA7A19D7338A16613E57426BF06177`.
- Exact allowlist: `backend/src/sketch2life/domain/core_foundation.py`; `backend/src/sketch2life/contracts/schemas/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py`; `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`; `backend/tests/unit/test_core_foundation.py`; `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`; this plan; append-only this approval; `evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md`; and the G1 ledger.
- Pinned behavior: server attaches the immutable versioned 1:1 profile only to newly created sessions in local/test while synthetic pilot is enabled; client cannot select/override it and must echo its version; server stores the profile id with each accepted operation; invalid or mismatched strokes reject before persistence; old unprofiled sessions retain their prior interpretation. Typed eligibility and all existing write guards remain independently required. Point count 2–512, coordinate precision ≤6 decimal places, normalized finite coordinates, five T0 colors, width tokens 5/9/14 and the existing 32 KiB payload limit are fixed by the plan.
- Exclusions: UI, export/render/admission, migrations/schema, checkpoint changes, BE2/provider/Modal/GPU, production configuration, and all paths not listed above. Pillow/1024×1024 image rendering remains T4/T5.

### T2 — Child own-group canvas reconnect

- Approved plan: `plan/T2_CHILD_CANVAS_RECONNECT_IMPLEMENTATION_PLAN_20261101.md`.
- Approved plan SHA-256: `4DFD74DD41B433ED85C9BA3C6FDA4946A4E1B8304E438A136FDD09A8D8657E6B`.
- Exact allowlist: `backend/src/sketch2life/interfaces/http/be1_runtime.py` (documentation only); `backend/src/sketch2life/contracts/schemas/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`; `backend/tests/contract/test_be1_synthetic_pilot.py`; `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`; this plan; append-only this approval; `evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md`; and the G1 ledger.
- Pinned behavior: use `get_verified_device_status` plus `_require_group_eligibility`; allow admitted, eligible Child own-group canvas reads while session is active or paused without requiring an active turn; return nullable `turn_id`; finished session, revoked/rotated grant, foreign scope, non-admitted membership, missing group, or current ineligibility stays denied. Existing write guard and legal-only paths stay unchanged.
- Exclusions: no new permission, no change to write paths or legal consent behavior, no UI, schema migration, artifact/rendering, provider/Modal/GPU, or unlisted path.

### T9 — Teacher session-scoped synthetic pilot profile lookup

- Approved plan: `plan/T9_TEACHER_PILOT_PROFILE_ROUTE_IMPLEMENTATION_PLAN_20261101.md`.
- Approved plan SHA-256: `03A72A63DFE52DDEE616A6B5C39D82512E33BA93D86A50104DFFFEEFFB7622B2`.
- Exact allowlist: `backend/src/sketch2life/contracts/schemas/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`; `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`; this plan; append-only this approval; `evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md`; and the G1 ledger.
- Pinned behavior: new session-scoped lobby route only for assigned Teacher/school admin in local/test with pilot enabled; disclose only `child_id` and `display_name` for active synthetic profiles with an exact-session, current, unrevoked proof. Never use `pilot_run_ref` as a trust boundary. Existing class-wide legal-only profile listing is unchanged.
- Exclusions: no admission or eligibility grant, profile/proof issuance or revocation, UI, migration, composition, provider/Modal/GPU, or unlisted path.

### Shared execution boundary

- PostgreSQL tests may use only the owner-approved disposable local `be1_acceptance` database over loopback; tests create and clean only their own `synthetic-` data. No DROP/TRUNCATE, other DB/service, real child data, Modal, GPU, provider call, or network access.
- The three tasks run in G1 and remain `XONG-CHƯA REVIEW` until an independent review. UI L6 is `DEFERRED-BY-OWNER`; visual AC20 is not included or claimed.
- Approval basis is the owner's direct instruction in this chat via the named goal file; this entry claims no external signature or co-owner sign-off.

### T3 plan path correction before implementation

- The approved T3 plan's unit-test path is `backend/tests/unit/test_canvas_operation_profile.py` (new), not `backend/tests/unit/test_core_foundation.py`; repository inventory showed the latter does not exist. No implementation had started when this correction was made.
- Corrected T3 plan SHA-256: `347CC6C7D8B7DC0877E933A1AB13D68629F6BE849B7AAA3E07E3D1683ABE347A`. This entry supersedes only the prior T3 plan hash and unit-test path; all other T3 scope, allowlist, boundaries, and decisions remain as approved above.
- Basis: same direct owner instruction in `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E, applied before test or code changes.

## T9 — route-surface assertion plan correction (2026-11-01)

- Status: APPROVED for the exact route-surface regression assertion update under the revised T9 plan.
- Approved plan: `plan/T9_TEACHER_PILOT_PROFILE_ROUTE_IMPLEMENTATION_PLAN_20261101.md`.
- Approved plan SHA-256: `D9BD291A35F7C97E07632C7953D2A58469A7D6FE9F52F77D7260B8117FD941BC`.
- This addendum supersedes only the prior T9 plan SHA-256 `03A72A63DFE52DDEE616A6B5C39D82512E33BA93D86A50104DFFFEEFFB7622B2` and adds `backend/tests/contract/test_app_composition.py` to the T9 allowlist. The only permitted change in that file is adding `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles` to the frozen compatibility-app route-surface assertion; no other route or assertion change is approved.
- Basis: owner-authorized G1 execution and task approvals under `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E. The baseline failure showed this exact new route missing from the frozen route set.
- All other T9 scope, behavior, allowlist paths, exclusions, and implementation remain unchanged.

## G1 review fixes (chỉ thị owner 2026-11-01)

- Status: APPROVED for the bounded post-review fixes F1–F4 and the permitted portions of F5/F6 described in the pinned plan. This is an additive, post-review allowlist expansion; it does not replace or rewrite the earlier T2, T3, or T9 approval entries.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in `CODEX_PROMPT_G1_REVIEW_FIXES_20261101.md`, 2026-11-01.
- Approved plan: `plan/G1_REVIEW_FIXES_PLAN_20261101.md`.
- Approved plan SHA-256: `90424CEFDA794A38B21BA2818462BFEAE862C65526B37FC08B0F97997F313E95`.
- Exact allowlist: `backend/src/sketch2life/domain/core_foundation.py` (canvas profile payload validator only); `backend/src/sketch2life/contracts/schemas/be1_runtime.py` (`CanvasReconnectResponse` only); `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` (reconnect response profile version and null-safe append fingerprint only, preserving the three existing Ruff-format-only hunks); `backend/tests/unit/test_canvas_operation_profile.py`; `backend/tests/contract/test_be1_synthetic_pilot.py`; `backend/tests/contract/test_openapi_contract_catalog.py` (explicitly added for F1); `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`; existing T2/T3/T9 evidence reports; `status/PILOT_GOAL_LEDGER_20261101.md` (G1 only); and append-only this approval.
- New paths pinned by the plan: `plan/G1_REVIEW_FIXES_PLAN_20261101.md` and `evidence/G1_REVIEW_FIXES_REPORT_20261101.md`. No new test file is planned.
- Exclusions: G2+, UI/npm, Modal/GPU/provider/external network, real child data, migrations/schema, `openapi_contract.py`, `be1_registry.py`, `be1_sessions.py`, generated contract regeneration, changes to existing guards, the three prior G1 plans/approval items, and all paths not listed above. The work remains TREO KHÔNG COMMIT: no stage, commit, push, reset, checkout, clean, or stash.
- PostgreSQL is restricted to the owner-provided disposable loopback `be1_acceptance` database. The connection value must remain in memory and must never be printed; every `Settings` construction must use `_env_file=None`; only test-owned synthetic rows may be created and cleaned.
- The approval intentionally leaves open whether identical two-point strokes remain valid and whether export size 1024/render parameters belong in profile v1 or T4/T5. No behavior is changed for those questions.

### G1 review-fixes — final evidence hashes (2026-11-01)

This append-only record pins the final plan, report, ledger, and the allowlisted files edited for the G1 review-fixes closeout. It does not expand scope or claim independent review. The approval file is intentionally not self-hashed.

| File | SHA-256 |
|---|---|
| `plan/G1_REVIEW_FIXES_PLAN_20261101.md` | `90424CEFDA794A38B21BA2818462BFEAE862C65526B37FC08B0F97997F313E95` |
| `evidence/G1_REVIEW_FIXES_REPORT_20261101.md` | `396C6D0549B276B33ACF665160ED1ADF9DABED9F8579188820DD0B57B7F3D4E0` |
| `status/PILOT_GOAL_LEDGER_20261101.md` | `B14A6D17A64B181EFEC3DADD094B9E8C056DA4B0EA19E9B5B606BB51A17F78F3` |
| `evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md` | `C812A45AB622F4A6EDE9F95C4AC4E1D6265CDEF5036BF4E49E814F2862E8CDB1` |
| `evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md` | `EFAC25C98AA50D6A3D6E98BFD3C47B64AEE534405D4A6813C2CF9892ACB47FE5` |
| `evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md` | `4943EB093BC1B429243F7187EA53B7A4E2E34BFA1592F6DE2134534CB6151503` |
| `backend/src/sketch2life/domain/core_foundation.py` | `FFC7B8BBAA1AF2CB0D63479AAA598B74AFD1B4FB4DD58088A5706235A16C19B3` |
| `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | `2484A952C7F96ECF46EAB3373DD34E1D206C79F69ABD3D9D9D0BF68C68D51978` |
| `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` | `B679820CDDC8038793BA65B1393E0FAEA11ADD09F8D46999E1309FB465698F6C` |
| `backend/tests/unit/test_canvas_operation_profile.py` | `BCC8FABCEB5EA9A6775D33D3EE333092D0CEFF3D364B679BBE618390384E5983` |
| `backend/tests/contract/test_be1_synthetic_pilot.py` | `03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611` |
| `backend/tests/contract/test_openapi_contract_catalog.py` | `342D78CDE873B72A5CE9A30D999B633ABAD0EBF4331F193976233E2032812806` |
| `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `46E06FD77C6214A7F0822EAEBB9AE54790D307BB26B536165742C5EB97C7B85C` |

## T4 — authoritative canvas source export (G2)

- Status: APPROVED for the bounded T4 implementation described below.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this chat to execute `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md` for scope G2-G6; the referenced `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E authorizes per-task append-only approvals. Date: 2026-11-01.
- Approved plan: `plan/T4_AUTHORITATIVE_CANVAS_EXPORT_PLAN_20261101.md`.
- Approved plan SHA-256: `B009F3F6D01DA5E39269E1D03085447042A64DE2F60804880764D0B7B94C41B0`.
- Exact allowlist: `backend/src/sketch2life/contracts/schemas/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`; new `backend/tests/unit/test_canvas_source_export.py`; `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`; the pinned plan; this append-only approval; `evidence/T4_AUTHORITATIVE_CANVAS_EXPORT_REPORT_20261101.md`; and the T4 entry in `status/PILOT_GOAL_LEDGER_20261101.md`.
- Pinned behavior: internal typed export only; no new route. Export exclusively server-accepted, current-profile operations, in one PostgreSQL statement snapshot, with complete epoch/revision/order/profile checks and canonical document/manifest/source hashes. Reject empty, checkpoint/restore, mixed-epoch, gap, malformed, or otherwise unprovable history without partial output. T5 owns private rendering/artifact/admission and any client-facing route.
- Database scope: only the owner-approved disposable local loopback `*_be1_acceptance` database, for the existing synthetic pilot fixture test. The fixture may create and clean only its own synthetic rows. No schema change, migration, DROP/TRUNCATE, or deletion of unrelated data.
- Exclusions: no edits outside the exact allowlist; no `core_store.py`, persistence model, migration, `be1_artifacts.py`, application service/port, app composition, public route, OpenAPI catalog, T5-T12 implementation, UI, Modal/GPU/provider/network, real child data, staging, commit, or push.
- Approval basis is the owner instruction and goal prompt only; no independent review or co-owner signature is claimed.

### T4 execution evidence pin (2026-11-01; no scope expansion)

- The approved plan remains SHA-256 `B009F3F6D01DA5E39269E1D03085447042A64DE2F60804880764D0B7B94C41B0`.
- Implementation report: `evidence/T4_AUTHORITATIVE_CANVAS_EXPORT_REPORT_20261101.md`, SHA-256 `F1A0B836D3B159AB40059D4A5ADCD6A6DFDD3B37B5325B51700D6E75E4204401`.
- T4 verification recorded: 4 unit tests passed; 53 isolated PostgreSQL synthetic-pilot tests passed; CPU/offline 298 passed / 4 skipped; contract suite excluding live-image 1,381 passed; FEAT-018 evaluation 25 passed. Ruff and repository validators passed; mypy has 3 G1R-baseline diagnostics and 0 new T4 diagnostics.
- This records execution evidence only. It does not change the approved allowlist or authorize T5/G4; each still requires its own plan and append-only approval.

## T5 — canvas render, private artifact, and admission (G2)

- Status: APPROVED for the bounded T5 implementation in the pinned plan.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, 2026-11-01. The detailed owner grant is in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E; no co-owner signature is claimed.
- Approved plan: `plan/T5_CANVAS_RENDER_ARTIFACT_PLAN_20261101.md`.
- Approved plan SHA-256: `6BCC29D243B4D86624D34DA38640E67AA7A988E6ABE290B3C348BA8EF45DB46B`.
- Upstream T4 plan SHA-256: `B009F3F6D01DA5E39269E1D03085447042A64DE2F60804880764D0B7B94C41B0`.
- Exact allowlist: new `backend/src/sketch2life/infrastructure/canvas_render/__init__.py`; new `backend/src/sketch2life/infrastructure/canvas_render/renderer.py`; `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` internal helper only; new `backend/tests/unit/test_canvas_source_render.py`; `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`; this plan; append-only this approval; `evidence/T5_CANVAS_RENDER_ARTIFACT_REPORT_20261101.md`; and the T5 entry in `status/PILOT_GOAL_LEDGER_20261101.md`.
- Pinned export behavior: separate `CanvasExportV1`, 1024×1024 RGB, white background, profile ratio × 1024 rounded with decimal `ROUND_HALF_UP` (13/23/36 pixels), round caps, no defensive one-point dot, retain coincident two-point operations, render only ordered accepted T4 operations, and bind source/spec/renderer/Pillow/content hashes. `CanvasOperationProfileV1` is unchanged; checkpoint JSON is never input.
- Artifact/admission behavior: private opaque image and receipt artifacts, existing metadata model/store only, actual FEAT-018/PyAV admission of exact stored PNG bytes, no admission receipt unless the actual decision is `ADMITTED`, compensating deletion only for this invocation's refs on failure, and trusted internal `CanvasRenderHandoffV1` after metadata commit.
- G4 compatibility boundary: the existing BE2 source port requires a real `CheckpointBinding`, while T4 supplies an operation export and rejects checkpoint history. T5 must not fabricate a checkpoint or alter BE2 contracts outside this plan. Actual BE2 port mapping is BLOCKED pending a separately approved G4 contract; T5 does not claim that mapping is complete.
- Database scope: owner-authorized disposable local loopback `*_be1_acceptance` only; synthetic fixture rows only; no schema changes, migration, DROP/TRUNCATE, or cleanup outside test-owned data.
- Exclusions: no public route/DTO, generic upload/download change, app composition, OpenAPI/catalog update, application/domain BE2 contract change, migration, UI/npm, Modal/GPU/provider/network, real child data, stage, commit, or push.

## T6 — Invocation guard and observation provenance (G3; blocker disposition only)

- Status: APPROVED for the blocker inventory/report and no implementation outside the pinned plan; implementation status is BLOCKED as stated below.
- Approver: Project owner / Person 2 (AnhKhoaa157), direct instruction in .claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md (scope G2-G6), under CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md §E.1, date 2026-11-01. This is not a co-owner signature.
- Approved plan: `plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_20261101.md`.
- Approved plan SHA-256: `C2186576249BA008D30ADEE47DCD132F8C8FCD3588F5E7FC1F87EE61AC7E2A71`.
- Exact write allowlist: the pinned plan; G3 blocker report; this append-only approval entry; and the T6/T7 entry in `status/PILOT_GOAL_LEDGER_20261101.md`. No code, migration, tests, or database writes are approved by this blocker-only disposition.
- Disposition: BLOCKED before implementation: T0 leaves total HTTP wall deadline, completion margin, late-response policy, and transport-bound invocation handshake unresolved.
- Layer status: L1-L2 BLOCKED; L3 NOT RUN; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 NOT RUN.
- Open questions: Owner: set total HTTP deadline/completion margin/cold-start policy; define late complete-response disposition; freeze immutable invocation identity and guard handshake at the transport boundary.
- Database/provider scope: none; no DB/PG, provider, Modal, GPU, or network operation is authorized or performed by this disposition.

## T7a — Minimal durable assistance and analysis state (G3; blocker disposition only)

- Status: APPROVED for the blocker inventory/report and no implementation outside the pinned plan; implementation status is BLOCKED as stated below.
- Approver: Project owner / Person 2 (AnhKhoaa157), direct instruction in .claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md (scope G2-G6), under CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md §E.1, date 2026-11-01. This is not a co-owner signature.
- Approved plan: `plan/T7A_DURABLE_PILOT_STATE_PLAN_20261101.md`.
- Approved plan SHA-256: `6BB50353C244759CB054FF044A9298BC8252B630DA09C2D2A53C93DBFF3B6E6C`.
- Exact write allowlist: the pinned plan; G3 blocker report; this append-only approval entry; and the T6/T7 entry in `status/PILOT_GOAL_LEDGER_20261101.md`. No code, migration, tests, or database writes are approved by this blocker-only disposition.
- Disposition: BLOCKED before implementation: O16 does not name the single schema/migration owner, selected schema/parent/revision, exact durable subset, or writer; T6 remains blocked where shared lifecycle requires its guard contract.
- Layer status: L1 NOT RUN; L2 BLOCKED; L3 BLOCKED; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Open questions: Owner: identify single schema/migration owner, exact migration branch/parent/schema/revision, selected durable method subset, and O16 writer.
- Database/provider scope: none; no DB/PG, provider, Modal, GPU, or network operation is authorized or performed by this disposition.

## T7b — OwnerFenceV1 and acceptance unit of work (G3; blocker disposition only)

- Status: APPROVED for the blocker inventory/report and no implementation outside the pinned plan; implementation status is BLOCKED as stated below.
- Approver: Project owner / Person 2 (AnhKhoaa157), direct instruction in .claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md (scope G2-G6), under CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md §E.1, date 2026-11-01. This is not a co-owner signature.
- Approved plan: `plan/T7B_OWNER_FENCE_UOW_PLAN_20261101.md`.
- Approved plan SHA-256: `D08D62A346D3397A0D7F0ED2FB0012E4C234B9D27505833B9A9410E1B4A020F1`.
- Exact write allowlist: the pinned plan; G3 blocker report; this append-only approval entry; and the T6/T7 entry in `status/PILOT_GOAL_LEDGER_20261101.md`. No code, migration, tests, or database writes are approved by this blocker-only disposition.
- Disposition: BLOCKED before implementation: T7a durable storage and a concrete cross-owner atomic transaction boundary are not established. Per owner instruction §E.3, missing co-signatures are not treated as the blocker and remain unsigned.
- Layer status: L1-L2 BLOCKED; L3 BLOCKED by T7a; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Open questions: Owner: identify the BE1-owned transaction hook/fence publication and exact approved UoW/fence methods; confirm concrete OwnerFenceV1 contract while retaining unsigned status.
- Database/provider scope: none; no DB/PG, provider, Modal, GPU, or network operation is authorized or performed by this disposition.

## T7c — Run manifest, invocation ledger, and host witness (G3; blocker disposition only)

- Status: APPROVED for the blocker inventory/report and no implementation outside the pinned plan; implementation status is BLOCKED as stated below.
- Approver: Project owner / Person 2 (AnhKhoaa157), direct instruction in .claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md (scope G2-G6), under CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md §E.1, date 2026-11-01. This is not a co-owner signature.
- Approved plan: `plan/T7C_RUN_LEDGER_WITNESS_PLAN_20261101.md`.
- Approved plan SHA-256: `C3806A9DE0DB1502E8D971DB76A7CED1D551F503619FD1546313B9CBEF0C50BE`.
- Exact write allowlist: the pinned plan; G3 blocker report; this append-only approval entry; and the T6/T7 entry in `status/PILOT_GOAL_LEDGER_20261101.md`. No code, migration, tests, or database writes are approved by this blocker-only disposition.
- Disposition: BLOCKED before implementation: depends on T7a/T7b and T6; O16 paths/schema/writer remain unresolved and the selected host witness filesystem/durability boundary has not been verified.
- Layer status: L1-L2 BLOCKED; L3 BLOCKED; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Open questions: Owner: freeze manifest issuer and invocation IDs, O16 paths/schema/writer, witness directory/filesystem and accepted Windows durability primitive, and T12 throwaway fault-test identities.
- Database/provider scope: none; no DB/PG, provider, Modal, GPU, or network operation is authorized or performed by this disposition.

## T2C — BE1 canvas, roster and current-turn adapter (G4; blocker disposition only)

- Status: APPROVED for the blocker-only disposition; implementation remains BLOCKED.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, 2026-11-01; authority detailed in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E. This is not a co-owner signature.
- Approved plan: `plan/T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_20261101.md`.
- Approved plan SHA-256: `8E7EACF0C1E8C205A5FBB2FA49F60165A4271F55861A8F5475D5A1CA758064DF`.
- Exact write allowlist: the pinned plan, `evidence/G4_G4_BLOCKERS_REPORT_20261101.md`, this append-only approval entry, and the T2C ledger entry. No adapter, application-port, composition, persistence, route, test, or database change is approved.
- Disposition: BLOCKED before implementation because the existing BE2 member call lacks session/class/purpose-reference scope and the BE1 fact source/snapshot boundary is not established. No child/session identity or purpose-code mapping is inferred. OwnerFenceV1 co-signature remains unsigned; per owner instruction §E.3 it is not treated as the blocker.
- Tests and database/provider scope: NOT RUN; none authorized by this blocker-only disposition.

## T8 — guarded worker (G4; blocker disposition only)

- Status: APPROVED for the blocker-only disposition; implementation remains BLOCKED.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, 2026-11-01; authority detailed in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E. This is not a co-owner signature.
- Approved plan: `plan/T8_GUARDED_WORKER_BLOCKER_PLAN_20261101.md`.
- Approved plan SHA-256: `7F3781DDA34BB22C7DBF55939085A575544FCB3DACD9C6C980268CDFA26DCF0E`.
- Exact write allowlist: the pinned plan, `evidence/G4_G4_BLOCKERS_REPORT_20261101.md`, this append-only approval entry, and the T8 ledger entry. No worker, transport, persistence, analysis, provider, route, test, or database change is approved.
- Disposition: BLOCKED by T6, T7a, T7b, and T2C. T8 cannot enforce the approved no-bypass, one-attempt, UNKNOWN/HOLD, and zero-Sketch rules without the guard, durable state, atomic fence, and scoped source contracts.
- Tests and database/provider scope: NOT RUN; none authorized by this blocker-only disposition.

## T9 — request gateway, cancel and own-status remainder (G4; blocker disposition only)

- Status: APPROVED for the blocker-only disposition; the G4 gateway/status remainder remains BLOCKED. This does not change the completed G1 Teacher pilot-profile route.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, 2026-11-01; authority detailed in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E. This is not a co-owner signature.
- Approved plan: `plan/T9_GATEWAY_STATUS_BLOCKER_PLAN_20261101.md`.
- Approved plan SHA-256: `50C39BA327F26103A822D8706E59046935FEE8EA0EB91D9A91806612A0998BBA`.
- Exact write allowlist: the pinned plan, `evidence/G4_G4_BLOCKERS_REPORT_20261101.md`, this append-only approval entry, and the T9 ledger entry. No route, composition, contract, service, database, UI, or provider change is approved.
- Disposition: BLOCKED by T6/T7/T8 and the absence of an approved mounted request/status surface. The existing fixture-only candidate router does not establish production request, cancel, or Child-own-status behavior; O18 Teacher pending route remains NEW/TBD.
- Tests and database/provider scope: NOT RUN; none authorized by this blocker-only disposition.

## T10 — Child UI handoff contract (G5; documentation only)

- Status: APPROVED for the bounded UI contract draft only; UI implementation is DEFERRED-BY-OWNER and runtime/API integration remains BLOCKED by T9 and the source/request shape mismatch.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, 2026-11-01; detailed scope `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §§B5.2, E. This is not a UI or co-owner signature.
- Approved plan: `plan/T10_CHILD_UI_HANDOFF_CONTRACT_PLAN_20261101.md`.
- Approved plan SHA-256: `96AFC6FB2DF302CB1404FB92CDAEDA85CBEAA58D26FF305F4D61B13E5460B261`.
- Exact write allowlist: the pinned plan; `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`; this append-only approval entry; and the T10 ledger entry. No UI, backend, route, schema, test, database, provider, or composition changes are approved.
- Acceptance boundary: document candidate versus production behavior, source/export binding gap, synthetic examples, body/error constraints, request-ref persistence, no automatic retry, and paused/no-turn policy. UI/npm/visual AC20 and L5 production-route tests remain NOT RUN.

## T11 — Teacher pending-analysis UI contract (G5; documentation only)

- Status: APPROVED for the bounded read-only UI contract draft only; UI implementation is DEFERRED-BY-OWNER and route/DTO integration remains BLOCKED while O18 is NEW/TBD and T9/G3 dependencies remain blocked.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, 2026-11-01; detailed scope `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §§B5.2, E. This is not a UI or co-owner signature.
- Approved plan: `plan/T11_TEACHER_PENDING_UI_CONTRACT_PLAN_20261101.md`.
- Approved plan SHA-256: `F4AF9EA99F73D866190180086B34938E8BC027F3B729B38013D0D6E9D54AFE70`.
- Exact write allowlist: the pinned plan; `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`; this append-only approval entry; and the T11 ledger entry. No UI, backend, route, schema, test, database, provider, or composition changes are approved.
- Acceptance boundary: keep the panel separate from Sketch review, mark the conceptual projection non-wire, document current authorization/read-only semantics and open paused/no-turn behavior. UI/npm/visual AC20 and L5 production-route tests remain NOT RUN.

## T12-partial — isolated PostgreSQL checks for completed pilot work (G6)

- Status: APPROVED for the bounded T12-partial checks only. This does not make the end-to-end BE2/Teacher-pending chain READY_FOR_T13 while T6/T7/T2C/T8/T9 remain blocked.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this session to execute the G2–G6 goal and the referenced T12 procedure, 2026-11-01.
- Execution plan/spec: `.claude/handoff/CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md`; SHA-256 `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C506365D`.
- Database scope: one owner-created disposable local database whose name contains `be1_acceptance`, connected only over loopback. Connection value and local path are intentionally omitted.
- Test allowlist for this partial run: BE1 synthetic-pilot PostgreSQL module; BE1 age-provenance PostgreSQL test; BE1 PostgreSQL API tests except the global retention-worker case; and Lesson Library PostgreSQL API tests. Only synthetic/test-owned rows may be created; tests must clean their own rows. No test/source/migration edits are authorized.
- Migration scope: repository Alembic only. The database was checked at all current heads; do not reapply or downgrade unless the existing T12 cleanup gate passes for the single BE1 head. No DROP/TRUNCATE and no deletion of non-test rows.
- Excluded: PostgreSQL integration tests that create/drop another database, BE2 persistence work blocked by T7, Modal/GPU/provider calls, real child data, B4b and T13.
- Report every phase as done, NOT DONE, or NOT RUN. No commit, stage, or push is authorized by this approval.

## G6 review fixes

- Status: APPROVED for the four bounded test/report fixes F1–F4 in the pinned plan.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this session, 2026-11-01.
- Approved plan: `plan/G6_REVIEW_FIXES_PLAN_20261101.md`.
- Approved plan SHA-256: `F17A53203EFCD901FDA058FFF329D8EEFFBA28A87117D9CCD2D19E26FA62416B`.
- Exact allowlist: `backend/tests/integration/test_be1_postgres_api.py`; `backend/tests/unit/test_canvas_source_render.py` (Ruff import ordering only if required); `backend/tests/contract/test_openapi_contract_catalog.py` (format only if required); append-only `evidence/notes/T12_LITE_POSTGRES_REPORT_20261101.md`; new exact committed-byte copy `evidence/notes/T12_LITE_POSTGRES_REPORT_20261101_RUN1_AS_COMMITTED.md`; new `evidence/G6_REVIEW_FIXES_REPORT_20261101.md`; this plan; append-only `status/PILOT_GOAL_LEDGER_20261101.md`; this approval append; and a new ignored G6R snapshot.
- PostgreSQL scope: only the already owner-created disposable loopback `*_be1_acceptance` database, under `.claude/handoff/CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md` safety gates; only the focused BE1 PostgreSQL tests named in the plan and permitted by that procedure. If safety gates fail, mark PostgreSQL checks NOT RUN; do not create a database.
- F1 may update only the two BE1 route/operation assertions to independently verified counts. F2 may patch the test-local `be1_sessions` and `be1_canvas` consent lookup in the named positive test and add a negative pending-consent canvas test in the same integration file. No product guard or consent behavior may change.
- F3 preserves the committed report bytes and appends a factual comparison only. F4 may change the two named Ruff paths only for findings from the project-compatible installed Ruff.
- Exclusions: M1 (operation/time ceilings), M3 (checkpoint export behavior), all product code under `backend/src`, schema/migration/OpenAPI catalog changes, ClamAV/Lesson Library, Modal/GPU/provider/network, real child data, UI, B4b/B6/B7/T13, stage, commit, and push.
- This approval does not resume or alter the separate G2–G6 goal status.

## G6 F2 expanded patch scope

- Status: APPROVED for the F2 test-only fixture correction and its negative consent check; this approval does not resume or change the separate G2–G6 goal.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this session, 2026-11-01.
- Approved plan: `plan/G6_F2_PLAN_20261101.md`.
- Approved plan SHA-256: `BDE6D64168B6801E023AB305B3F787D46474152C49DB4779A37DE93BB2DF9AF8`.
- Approved owner prompt SHA-256: `446AF8ADB92885282B7CAE26F8D2561A1E01911BD2E97B5995E21DD2F614271D`.
- Scope expansion from `G6 review fixes`: add only the test-local patch `be1_runtime.consent_is_effective` to the already allowed `be1_sessions` and `be1_canvas` patches in `test_room_code_start_revocation_stage_and_early_outcome_are_durable`. The negative pending-consent canvas check remains test-local in the same integration file.
- Exact allowlist: the named F2 test and one negative test in `backend/tests/integration/test_be1_postgres_api.py`; this plan; new `evidence/G6_F2_REPORT_20261101.md`; append-only FEAT-064 approval and ledger entries; one local G6F2 snapshot. F1/F3/F4 files are excluded.
- No product guard/consent code, schema, migration, OpenAPI catalog, other test, Modal/GPU/provider/network, real-child data, stage, commit or push is approved.
- PostgreSQL execution is subject to the T12 procedure hash pinned by the approved owner prompt; no database operation is approved against a mismatching procedure copy.
## Đính chính hash thủ tục T12

- Nguồn: chỉ thị trực tiếp của Project owner / Person 2 (`AnhKhoaa157`) trong phiên ngày 2026-11-01; cho phép tiếp tục lượt chỉ-F2.
- Đính chính hash thủ tục trong mục `T12-partial — isolated PostgreSQL checks for completed pilot work (G6)` (dòng khoảng 463), cùng tham chiếu T12 của `G6 review fixes` và `G6 F2 expanded patch scope` và các tham chiếu liên quan từ prompt F2/G6. Hash ghi `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C506365D` là lỗi chép ký tự cuối.
- Hash SHA-256 thật của thủ tục T12: `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C5063657`; đã đo lại trong lượt này. Owner xác nhận file thủ tục không đổi từ 2026-10-31 23:24. Nội dung thủ tục không đổi; không sửa mục approval cũ.
- Prompt chỉ-F2 giữ SHA-256 `446AF8ADB92885282B7CAE26F8D2561A1E01911BD2E97B5995E21DD2F614271D`; plan F2 giữ SHA-256 `BDE6D64168B6801E023AB305B3F787D46474152C49DB4779A37DE93BB2DF9AF8`. Cổng hash lệch được ghi trong plan nay được đính chính bởi chỉ thị này; dùng hash thật khi kiểm thủ tục.
- Chỉ mở lại phạm vi F2 đã duyệt: kiểm tra pending consent trước hai patch test-local mới, ba alias tổng cộng, trên database local dùng một lần theo thủ tục. Không mở rộng sửa mã sản phẩm, F1/F3/F4 hoặc phạm vi khác; không stage/commit/push.

## G6 F2 assertion rate-limit

- Status: APPROVED; Project owner / Person 2 (`AnhKhoaa157`), chỉ thị trực tiếp trong phiên ngày 2026-11-01.
- Mở rộng đúng phạm vi assertion rate-limit trong test `test_room_code_start_revocation_stage_and_early_outcome_are_durable`: chẩn đoán chỉ SELECT và chỉ in số dòng/độ dài attempts; nếu thiếu WHERE chọn nhầm nguồn, lọc đúng nguồn TestClient theo hàm/cách production và GIỮ kỳ vọng `== 10`. Dòng đúng khác 10 hoặc nguyên nhân khác: dừng.
- Cho phép tối đa hai sửa lỗi phía test tiếp theo cùng loại phụ thuộc dữ liệu/thứ tự hoặc kỳ vọng cũ lỗi thời, mỗi lỗi có chẩn đoán; lỗi sản phẩm hoặc lỗi thứ ba phải dừng. Khi F2 xanh chạy hai module PG đã nêu, giải thích 98/99 bảng.
- Plan F2 sau append: `plan/G6_F2_PLAN_20261101.md`; SHA-256 `6BA7E86D199A7822E57641BAF52E1A255367AC6F840BFEC1EDB6DE505ED2E210`. Mục này bổ sung `G6 F2 expanded patch scope`, không sửa/xóa approval trước. Hash thủ tục T12 thật kết thúc `...3657` theo mục đính chính đã ghi.
- Allowlist chỉ hàm test F2 trong `backend/tests/integration/test_be1_postgres_api.py`, append plan/báo cáo/ledger/approval FEAT-064 và snapshot mới. Không sửa source/schema/migration/guard/consent hay F1/F3/F4; không stage/commit/push.

## M1 — canvas capacity and renderer budget (GOAL A1)

- Status: APPROVED, Project owner / Person2 (`AnhKhoaa157`), direct launch instruction2026-11-01.
- Approved plan: `plan/M1_CANVAS_CAPACITY_RENDER_PLAN_GA1_20261101.md`; SHA-256 `D27E902D268200F954758F26D262DA6E1D3A3D1D3F470AF05A9442D4863B418F`.
- Owner V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; goalA1 SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`. Source is owner launch message confirming V4§4(1)–(6).
- Allowlist: limits.py/renderer.py in infrastructure/canvas_render; be1_canvas.py/be1_artifacts.py routers; new test_canvas_render_limits_ga1.py and test_canvas_capacity_ga1_postgres.py; pinned plan, task evidence, append ledger/approval, snapshots. Exact paths in pinned plan.
- PostgreSQL only owner-created disposable loopback database under corrected T12 SHA…3657, synthetic/test-owned rows only. No migration for M1. No product consent/guard relaxation, core_store/service/profile modification or out-of-scope code.
- OWNER_MODAL_CALL_APPROVED: NO; no Modal/GPU/provider/external network, real child data, stage/commit/push.

## M1 — compatibility addendum (GA1)

- Status: APPROVED under owner GOAL A1 test-corresponding allowlist, direct launch2026-11-01; V4 SHA `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`, goal SHA `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`.
- Plan `plan/M1_FIXTURE_COMPATIBILITY_ADDENDUM_GA1_20261101.md` SHA `49E05F5BEF07A235489DA626D28F40F8F6FC6C2C3DC72B4B2F5A396B149C6723`; original M1 plan remains immutable.
- Add only test fingerprint fake wiring in `backend/tests/unit/test_canvas_operation_profile.py` as specified; original fingerprint assertions and CanvasOperationProfileV1 unchanged. No other new path or source behavior is authorized. Point sum follows whole-canvas V4D1, not an epoch filter.
- No stage/commit/push or provider/network.

## T7a — durable repositories and full ledger (GOAL A1)

- Status: APPROVED, Project owner/Person2 (`AnhKhoaa157`), direct A1 launch2026-11-01 confirming V4§4(1)–(6). V4 SHA `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; goal SHA `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`.
- Plan `plan/T7A_DURABLE_REPOSITORIES_LEDGER_PLAN_GA1_20261101.md` SHA-256 `8A277676DC3DE4DDD19A7B69FFFC14ABF12EA729E9B87254980D71D422C201C7`. Allowlist new vision_analysis tables/codec/repository/ledger, assistance/sql_repository and needed init, new20261102_pilot_vision migration, env metadataregistration, two new testfiles, pinnedplan/evidence and appendapproval/ledger/snapshot. Exactpaths inplan.
- DBscope one owner-created disposable loopback acceptanceDB under corrected T12hash…3657; new pilot_vision branch upgrades and downgrade DROPs only this task's newly created tables/schema explicitly authorized by V4D2. Retain all older table data; remove only task-owned rows. Leave DB at new head.
- Old ai_jobs migrationtest createsanotherDB so not authorized; scopedread-only assertionmay reportactualstaleness. No OwnerFenceBE1signature implied; co-owner review later under ownerinstruction.
- No service/ports ai_jobs/contracts/tables changes, no provider/network/realchilddata/Gitmutations. OWNER_MODAL_CALL_APPROVED: NO.

## GA1 stale revision-count assertion — test-only scope

- Status: APPROVED by Project owner / Person 2 (`AnhKhoaa157`) via the explicit structured reply in this session, 2026-11-01.
- Owner approval text SHA-256: `6718eb16faeeed242440d31868d20868130aa9d2f52f42ac322b894dd9aa84e7`.
- Approved plan: `plan/GA1_REVISION_COUNT_TEST_ALIGNMENT_PLAN_20261101.md`; SHA-256 `B86D35814B73D759049BC06C23D75C050CAA6398CA5252726C2979A8D4C0C158`.
- Exact test edit: in `backend/tests/unit/test_synthetic_eligibility.py`, update only the graph revision-count expectation from 24 to 25 and its adjacent comment to include the pilot-vision revision.
- Allowlist: that test file; the pinned plan; this append-only approval record; one new evidence report; one appended ledger result; and local snapshot `.claude/handoff/snapshots/GA1_TESTFIX_20261101T200313/`.
- Approved checks: the focused failing test, then the established GA1 offline suite using a copied network-blocking runner with `test_canvas_render_limits_ga1.py` and `test_pilot_vision_persistence_ga1.py` as add-ons. Remove database-test configuration; keep pytest temporary files outside the repository. Any failure beyond the stale count is a hard stop.
- Exclusions: no other test or product/migration/schema/runtime path; no T6 before the aggregate regression is green; no PostgreSQL, Modal/GPU/provider, external network, real-child data, stage, commit, or push. `OWNER_MODAL_CALL_APPROVED: NO`.

## GA1 migration graph head expectations — test-only follow-up

- Status: APPROVED by Project owner / Person 2 (`AnhKhoaa157`) via the explicit structured reply in this session, 2026-11-01.
- Owner approval text SHA-256: `d53ba18a53938062d5293b2c34a71b1b1d10d4601b370a352b3e365894ab81ff`.
- Approved plan: `plan/GA1_REVISION_GRAPH_HEAD_ALIGNMENT_PLAN_20261101.md`; SHA-256 `272B7C06546BABB86AFB1DBDCB2CB6CC73B0872CFC3667D9F40A80E9F5D84DF6`.
- Exact test scope: within `backend/tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation`, expect heads `(11, 9)`, assert `20261102_pv_0001` as the dependency-aware terminal head, and correct the adjacent explanatory comment. Retain the previously approved total revision count of 25 and the age revision's down-revision-only assertion.
- Allowlist: the named test file; this plan; this append-only approval record; one new evidence report; one appended FEAT-064 ledger result; and local snapshot `.claude/handoff/snapshots/GA1_HEADFIX_20261101T201542/`.
- Approved checks: the focused test, then the established GA1 offline suite from a copied network-blocking runner with the M1 and T7a unit add-ons. Database-test configuration must be removed and pytest temporary files kept outside the repository. Any other failure is a hard stop.
- Exclusions: no migration/source/schema/runtime change, T6 implementation, PostgreSQL, Modal/GPU/provider, external network, real-child data, stage, commit, or push. `OWNER_MODAL_CALL_APPROVED: NO`.

## T6 — A1 invocation guard and provenance implementation

- Status: APPROVED for the exact T6 implementation scope below under GOAL A1. This does not authorize T13, provider execution, or work in A2/B1/B2.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct GOAL A1 launch instruction in this session, confirming V4 §4 items (1)–(6), 2026-11-01.
- Authority pins: V4 `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md`, SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; Goal A1 `.claude/handoff/CODEX_GOAL_G3G4_A1_20261101.md`, SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`.
- Approved plan: `plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_GA1_20261101.md`; SHA-256 `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`.
- Exact allowlist: the pinned plan; `backend/src/sketch2life/application/ports/vision_analysis.py`; `backend/src/sketch2life/domain/vision_analysis.py`; `backend/src/sketch2life/contracts/schemas/analysis_results.py`; new `backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py`, `transport.py`, and `pilot_policy.py`; `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py` only for V2 failure identity validation; new `backend/tests/unit/test_invocation_guard_transport_ga1.py`; this append-only approval record; new `evidence/T6_INVOCATION_GUARD_IMPLEMENTATION_REPORT_GA1_20261101.md`; append-only `status/PILOT_GOAL_LEDGER_20261101.md`; and one new ignored GA1 snapshot.
- Scope: follow V4 D3 exactly—per-attempt server UUID/run/job/attempt identity, durable T7a invocation ledger claim and `SENT` before HTTP bytes, `http.client` JSON transport with a 160-second monotonic total deadline, no redirects/retries, V2-complete-response terminal classification, `UNKNOWN` after any ambiguous SENT outcome, `LIVE_LEGACY_BRIDGE` evidence, and the named single-attempt pilot retry policy. No `ObservationRequest` or application service change.
- Verification: loopback-only stub tests; focused T6 tests; offline GA1 baseline 618 passed / 4 skipped plus T6 tests; Ruff, mypy, three repository validators, and `git diff --check`. No PostgreSQL operation is in T6 scope.
- Exclusions: all paths outside the exact allowlist; `application/services/vision_analysis.py`; all `ai_jobs` source/policy/service/port/schema; migrations/schema; BE1/canvas; routes, worker, composition; Modal/GPU/provider/external network; real-child data; stage, commit, push, stash, reset, or destructive cleanup. `OWNER_MODAL_CALL_APPROVED: NO`.
- The earlier G3 T6 approval remains the historical blocker-only disposition. This entry authorizes only the above A1 implementation scope under the already owner-approved V4 D3 decisions; it is not a co-owner signature or independent review.

## T6 — independent-review fixes (GOAL A1)

- Status: APPROVED for the three bounded T6 review findings only; no A2 work is authorized.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct launch message in this session, 2026-11-01: “TREO KHÔNG COMMIT — TIẾP TỤC REVIEW-FIX T6 / GOAL A1”.
- Authority pins: V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; Goal A1 SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`; frozen T6 plan SHA-256 `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`.
- Approved review-fix plan: `plan/T6_REVIEW_FIXES_PLAN_GA1_20261101.md`; SHA-256 `30BB0D4778B3CFE81F9DB04E67DE1078483FE2A61E2A3BBC336E7AC0291D0160`.
- Implementation allowlist: `backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py`; `transport.py`; `legacy_v2.py` only for a read-only property exposing the injected transport's guard identity; and `backend/tests/unit/test_invocation_guard_transport_ga1.py`.
- Task records allowed: this append-only approval entry; the pinned review-fix plan; one new evidence report; one append-only GOAL A1 ledger entry; and one new ignored GA1 snapshot.
- Required boundaries: identity mismatch is rejected before bridge invocation; NEW-state outcomes are never downgraded to no-send; no SENT/terminal UNKNOWN is written from NEW; DNS is bounded by the existing 160-second monotonic deadline while HTTPS hostname/certificate verification is preserved; claim-race test synchronizes at the claim boundary. If a provider send remains possible while the bound guard is NEW, stop and report a blocker. Do not edit ledger/schema/migrations or any file outside the allowlist.
- Exclusions: A2, PostgreSQL/Alembic, Modal/GPU/provider, external network, real-child data, stage, commit, push, stash, reset, and destructive cleanup. `OWNER_MODAL_CALL_APPROVED: NO`.

## T6 — bounded DNS resolver capacity follow-up (GOAL A1)

- Status: APPROVED for the exact bounded-resolver follow-up plan and two implementation paths below.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this session, 2026-11-01: “Duyệt plan SHA-256 `2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F`, giới hạn tối đa 2 resolver worker đồng thời trên mỗi Python process.”
- Authority pins: V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; Goal A1 SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`; frozen T6 plan SHA-256 `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`; preceding T6 review-fix plan SHA-256 `30BB0D4778B3CFE81F9DB04E67DE1078483FE2A61E2A3BBC336E7AC0291D0160`; independent-review report SHA-256 `317EEB31B91E0D4A580314E53E0DA89F0F4BF7715C76506E9B93294703F25897`.
- Approved plan: `plan/T6_BOUNDED_DNS_RESOLVER_PLAN_GA1_20261101.md`; SHA-256 `2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F`.
- Owner decision: at most **2 active resolver workers per Python process**, shared across all `HttpJsonTransport` instances; no unbounded queue. Saturation fails closed before HTTP bytes and before SENT. A resolver slot remains occupied until its underlying resolver actually exits, even if the caller deadline has elapsed.
- Exact implementation allowlist: `backend/src/sketch2life/infrastructure/vision_analysis/transport.py`; `backend/tests/unit/test_invocation_guard_transport_ga1.py`.
- Task records allowed: this append-only approval entry, one new evidence report, one appended GOAL A1 ledger entry, and one new ignored snapshot. Previous reports, approvals, plans, ledger entries, and snapshots remain unchanged.
- Verification: focused T6 tests; corrected offline GA1 runner with explicit `test_canvas_render_limits_ga1.py`, `test_pilot_vision_persistence_ga1.py`, and T6 module add-ons; Ruff, mypy, three validators, and `git diff --check`.
- Exclusions: all other source/test files, invocation guard/bridge/ledger/schema/migration/service/worker/route/composition, PostgreSQL/Alembic, Modal/GPU/provider, external network, A2, stage, commit, and push.
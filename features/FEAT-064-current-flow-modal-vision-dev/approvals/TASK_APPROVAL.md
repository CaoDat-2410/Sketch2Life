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

# FEAT-064 B4a / T1 — Addendum B (DRAFT, AWAITING_APPROVAL): phases P4–P9

- Status: **DRAFT.** This addendum specifies phases P4–P9 of T1. It grants nothing. It unblocks nothing by itself: P4–P7 stay blocked until (1) the BE1 owner `CaoDat-2410` has confirmed in writing the items in B1 and (2) the project owner records a new approval entry that pins this addendum's SHA-256 together with the plan, Addendum A, the four T0 hashes and the BE1 confirmation file.
- Pinned context, unchanged: plan `plan/B4_T1_ELIGIBILITY_IMPLEMENTATION_PLAN_20261031.md` (SHA-256 `131DDB39019572E9FFCC1B5CB21ABC848583637803E9227E518BBA3526E01E31`) and Addendum A (`A8397E3944DEAF0B693E90248D86A33DCA0755E3CB21F6F52747CA272F2DEAA6`). Where Addendum B and Addendum A disagree, B wins for P4–P9 only, and each such place is listed in B9.
- Baseline facts (verified on 2026-10-31): `origin/dev` (`f68ed2b5`) and every other local and remote ref contain no `data_origin`, `SYNTHETIC_DEV` or synthetic-proof code, so P4–P9 are new work and cannot be taken from `dev`. The consent CHECK is still `state IN ('pending','revoked')` (`be1_models.py:147`). P0–P3 are done and independently reviewed (PASS WITH NOTES).
- Every name, column and value below marked **PROPOSAL** is a draft for the BE1 owner to confirm or change. Nothing here is a BE1 co-signature.

## B1. Written confirmation required from `CaoDat-2410` (gate for P4–P7)

The confirmation must be a file or PR comment with a stable location and a SHA-256, recorded by the project owner in the approval entry. A relayed message, the owner decision slip or the project owner's approval does not count. It must state, item by item, accept / change:

1. Origin column name and values: `be1_managed_profiles.data_origin` with `REAL`, `SYNTHETIC_DEV`, `LEGACY_UNCLASSIFIED` (**PROPOSAL**; Rev36 S2 used the draft name `SYNTHETIC_TEST`, so one canonical name must be chosen and reused by S2 without a second enum).
2. Proof table: name `be1_synthetic_eligibility_proofs` and the columns in B2 (**PROPOSAL**).
3. Migration: single new revision, parent `20261024_0005`, id `20261031_be1_se_0001`, no `depends_on`, no branch label.
4. `be1_canvas.py`: a separate append-only helper; the five other canvas sites keep the legal-only helper.
5. Whether `consent_id` / `consent_purpose_ref` on the profile table may become nullable under the CHECK in B2.
6. Writer and reviewer for `settings.py`, the migration and the new tool (T0 rows O13 and O16 are `NEEDS_OWNER`), plus a reviewer per edited file (30 `NEEDS_OWNER` rows in `B3_OWNER_MATRIX`).
7. The settings key for the pilot flag (**PROPOSAL**: `synthetic_pilot_enabled`, env `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED`, default `false`).

## B2. P4 — persistence and migration source (no execution)

Files: `be1_models.py`, `core_store.py`, `backend/alembic/versions/20261031_be1_synthetic_eligibility.py`. The migration file is created as source only; Alembic is never run.

- Profile table: add `data_origin` (not null). ORM default `REAL`. Migration adds the column with a temporary server default `LEGACY_UNCLASSIFIED` for existing rows, then drops the server default. Existing consent references and every other stored value are preserved.
- CHECK on the profile table (single-table only): `data_origin IN (REAL, SYNTHETIC_DEV, LEGACY_UNCLASSIFIED)`; `REAL` requires both consent references non-null; `SYNTHETIC_DEV` requires both null. `LEGACY_UNCLASSIFIED` is unconstrained so existing rows stay valid. No cross-table lookup in any CHECK.
- Proof table (**PROPOSAL**), append-only for issuance: `evidence_id` (PK), `schema_version`, `data_origin` fixed to `SYNTHETIC_DEV`, `organization_id`, `class_id`, `child_profile_id` (FK to the profile), `purpose_ref`, `run_ref`, optional `session_id`, `issued_by`, `issued_at`, `expires_at`, `revoked_at`, `revocation_revision`, `policy_version`. CHECK `expires_at > issued_at`. Timestamps are timezone-aware. Revocation sets `revoked_at` once and never edits issuance columns.
- Downgrade fails closed: raise when any `SYNTHETIC_DEV` profile or any proof row exists; otherwise drop the proof table and the new column and CHECKs.
- `core_store.py`: only narrow methods `get_profile_origin`, `get_synthetic_proof`, `issue_synthetic_proof`, `revoke_synthetic_proof`. Missing, unreadable or malformed rows return "no proof", never an exception that could be read as eligible.
- Static checks only (in `test_synthetic_eligibility.py`): parse the revision graph without Alembic and assert exactly one new revision whose only parent is `20261024_0005`, id length <= 32, and head counts by both methods recorded before and after (before: 10 by `down_revision` only, 9 when `depends_on` is counted; derived expectation after: 10 and 10, because the new leaf replaces `20261024_0005` as a `down_revision` leaf and adds one dependency-aware leaf; stop if the computed numbers differ from this derivation); compile the new DDL with the PostgreSQL dialect; assert the downgrade guard by reading the code.

## B3. P5 — guard wiring

Files: `be1_common.py`, `be1_sessions.py`, `be1_runtime.py`, `be1_canvas.py` (append call site only).

- `be1_common.py`: add one typed-eligibility function that fetches facts (profile origin, legal effective result through the callable passed in, proof, session `configuration["pilot_run_ref"]`, session id, `settings.env`, the pilot flag, a clock) and calls `evaluate_eligibility`. Keep `consent_is_effective` as a name in `be1_sessions.py` so the monkeypatch at `test_be1_postgres_api.py:316` keeps working; pass it in as a callable.
- Sites: G03 Start (`_transition`), G04 `admit_device`, G05 `assign_member_to_group`, G07 `start_child_turn`, G08 `get_verified_device`, G18 `append_canvas_operation` through a new separate append helper. D2 applies: `consent_ready` is passed `True` for `LEGAL_CONSENT` or `SYNTHETIC_DEV`; add the one-line comment; `application/services/be1_runtime.py` is not edited.
- A `DENIED` decision keeps today's 409 `CONSENT_NOT_EFFECTIVE` and audit `denied_consent_pending`. Evaluator error or unreadable fact is `DENIED`.
- Untouched, covered by the existing AST tests: progress, help, records, artifacts, registry, and the five other canvas sites (`sync_canvas_operations`, `save_checkpoint`, `read_latest_checkpoint`, `restore_checkpoint`, `reconnect_canvas`).
- Audit (**OWNER_DECISION OD-B1**): write an audit entry (proof id, basis, basis version) on accepted synthetic decisions at state-changing operations only (admit, Start, group assignment, turn) and on every denial; no successful-audit write per device check or per stroke. This narrows Addendum A4's "every accepted synthetic decision"; the owner must accept it in the approval entry.
- Pilot limits to record: one Child per pilot group; `list_profiles` still returns 409 for a class that holds a synthetic profile; sync and reconnect stay legal-only, so the Child UI is not fully working with a synthetic session.

## B4. P6 — operator tool and setting

Files: `tools/synthetic_eligibility.py` (create), `settings.py` (add the flag only, default `false`).

- Local/test only; no HTTP route. Parse the URL with SQLAlchemy `make_url`; inspect the host and the query keys `host` and `hostaddr`; refuse unless the host is loopback or the database name contains `be1_acceptance`; no DNS resolution. Refuse unless `settings.env` is `local` or `test` and the pilot flag is on. Default is dry-run; a write needs an explicit flag. Issue only for profiles whose origin is `SYNTHETIC_DEV`. Never print settings or connection strings.
- Unit tests (no database): default-off, refusal in other environments, URL and host checks, dry-run default, no secret in output.

## B5. P7 — replacement of the fake-flow test (follows Addendum A3)

- No fake HTTP flow and no SQLite shim. Remove the 18 `xfail(strict=True)` markers in `test_be1_synthetic_pilot.py` only after the matching guard is wired, and rebind the append probe to the new separate append helper. Rerun the probe-extraction review noted in the P0–P3 report. The full chain create profile → join → admit → Start → group → turn → append stroke stays **NOT_RUN** until T12.

## B6. P8 — regression and static checks

Re-run the five baseline files (from `backend/`, `PYTHONPATH=src`, no `BE1_TEST_DATABASE_URL`, `--tb=no -q`, `--basetemp` outside the repository; reference 26 passed, 4 skipped), both new test files, Ruff and `mypy --strict` on every edited Python path (separate pre-existing issues from regressions), `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, `git diff --check`, and a whitespace and UTF-8 check on untracked files.

## B7. P9 — evidence

Update `evidence/notes/T1_IMPLEMENTATION_REPORT_20261031.md`: before and after SHA-256 for each edited path, exact commands and results, guard coverage, migration revision, parent and static-only verification, the BE1 confirmation location and SHA-256, the seven owner-local hashes (unchanged), and every NOT_RUN item.

## B8. File allowlist for P4–P9 (no other path)

Create `backend/alembic/versions/20261031_be1_synthetic_eligibility.py` and `tools/synthetic_eligibility.py`. Edit `be1_models.py`, `core_store.py`, `settings.py`, `be1_common.py`, `be1_sessions.py`, `be1_runtime.py`, `be1_canvas.py` (append site only), `backend/tests/unit/test_synthetic_eligibility.py`, `backend/tests/contract/test_be1_synthetic_pilot.py` and the T1 report. `be1_registry.py` and `be1_records.py` stay read-only. P0–P3 outputs `domain/eligibility.py` may be edited only to rename the provisional origin enum if B1 item 1 changes it.

## B9. Where this addendum differs from earlier text

- Audit scope (OD-B1, B3 above) narrows Addendum A4.
- The plan's blanket legacy denial stays superseded by Addendum A4 (legacy keeps the legal path), as implemented in P3.
- Plan P7 and AC5 stay replaced by Addendum A3 (B5 above).

## B10. Acceptance and stop conditions

- Acceptance: the plan's AC1–AC4, AC6–AC9 with the fake-flow criterion AC5 replaced as in B5; additionally the 18 former xfail cases pass, the migration static checks pass, and no file outside B8 changes.
- Stop and report without widening scope if: the BE1 confirmation file or the approval entry is missing or any hash differs; the profile table's consent columns or the revision graph do not match B2; a second Alembic head would appear; a required edit lies outside B8; any step needs a database, Alembic, backend service, MinIO, Modal, GPU or network; or the P1 baseline differs from 26 passed, 4 skipped.
- Not claimed by this task: PostgreSQL acceptance, the end-to-end chain (T12), any Modal call, BE2 behavior (G15 and G16 stay NOT_IN_T1), `OwnerFenceV1` signatures.

## B11. Approval request

The project owner records a new T1 entry that pins this addendum, the plan, Addendum A, the four T0 files and the BE1 confirmation (location and SHA-256), authorizes P4–P9 and B8, and states OD-B1. Until then no P4–P9 edit is allowed.

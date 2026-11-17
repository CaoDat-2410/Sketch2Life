# FEAT-064 B4a / T1 — Addendum A (DRAFT, AWAITING_APPROVAL)

- Status: **DRAFT.** This addendum amends the scope and method of `plan/B4_T1_ELIGIBILITY_IMPLEMENTATION_PLAN_20261031.md` (SHA-256 `131DDB39019572E9FFCC1B5CB21ABC848583637803E9227E518BBA3526E01E31`, unchanged and still pinned by the existing T1 approval). It exists because an independent read-only review of that plan returned NEEDS_REVISION with two P1 findings. It grants nothing until the owner records a new approval entry that pins **both** this addendum's hash and the original plan hash.
- Where this addendum and the original plan disagree, this addendum wins for T1. Everything not mentioned here is unchanged.
- Owner decisions needed are marked `OWNER_DECISION`; each carries a recommended default. Nothing here is a BE1 co-signature.

## A1. Scope correction: the stroke-append route has its own consent gate (review P1-1)

The bounded flow ends with a Child appending a stroke. That route (`backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`, call at line 110) calls `_require_group_consent` (definition at line 208), which independently queries `ConsentRecordModel.state == "effective"` for every Child in the group and for every earlier participant. Changing only `be1_runtime.py` therefore cannot make the stroke succeed. The same helper also guards sync (`:182`), checkpoint (`:287`), restore (`:468`, `:416`) and reconnect (`:592`).

- `OWNER_DECISION` D1 (recommended: yes): add `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` to the T1 allowlist, **for the append call site only**. Implementation must add a narrow, separate path (new helper or explicit keyword that defaults to the current legal-only behavior) so that checkpoint, restore, sync and reconnect keep exactly today's legal-only gate. T0 guard row G11 stays binding for those routes: "generic checkpoint/restore keeps its present gate".
- Writer/reviewer for this file follow the T0 manifest boundary O05 (BE1 owner as writer proposal); the BE1 owner must confirm in writing together with the schema confirmation (A7).
- A group-wide gate means one ineligible Child in the group blocks the group: the pilot group must contain exactly one Child. Record this limit in the T1 report.

## A2. Session start boolean (review P2-3)

`Be1RuntimePolicy.next_session_state` takes `consent_ready`, which `be1_sessions.py` fills from the consent check (T0 row G13). `application/services/be1_runtime.py` stays out of the allowlist.

- `OWNER_DECISION` D2 (recommended: accept): the router passes `True` for that existing parameter when the typed decision is `LEGAL_CONSENT` or `SYNTHETIC_DEV`, and `False` otherwise, with a one-line code comment that the parameter now means "eligibility ready"; no rename and no change to the service file. The decision value is not copied into any consent field. If the owner rejects this, the service file must be added by a further approval before Start can be implemented.

## A3. Replace the unfeasible HTTP-flow test (review P1-2)

The BE1 routers and models are bound to PostgreSQL (JSONB columns, `'{}'::jsonb` defaults, `pg_advisory_xact_lock` on room-code join, a core engine that rejects other drivers, and an existing test that forbids substituting SQLite). The plan's "fake/in-memory HTTP contract" test therefore cannot honestly exercise the flow. Replace plan P2 and P7 and acceptance criterion AC5 with:

1. Pure domain unit tests of the typed decision (all legal, synthetic and denied combinations).
2. Guard-level unit/contract tests that inject fakes at the eligibility seams only (legal lookup, proof lookup, clock, settings): each T0 `SYNTHETIC_TYPED_ONLY` call site on the path (G03, G04, G05, G07, G08 and the append site from A1) must have a positive and a negative test proving the typed decision is consulted and DENIED stays 409 `CONSENT_NOT_EFFECTIVE` with audit `denied_consent_pending`.
3. Static migration checks: parse the revision graph without Alembic, compile the new table/CHECK DDL with the PostgreSQL dialect, assert downgrade behavior by reading the code.
4. The end-to-end flow create profile → join → admit → Start → group → turn → append stroke is **NOT_RUN** until T12 provides an owner-approved disposable PostgreSQL database. It must never be reported as passed. Do not build a SQLite shim.

Design for testability: keep the decision a pure function of already-fetched facts; keep SQL in thin lookup functions that can be replaced in tests.

## A4. Runtime conditions for `SYNTHETIC_DEV` (review P2-5)

A `SYNTHETIC_DEV` decision requires all of: profile origin is `SYNTHETIC_DEV`; a server-issued proof that is unexpired and unrevoked; proof bound to the exact organization, class, Child, purpose and run, and to the current session when the proof carries one; `settings.env` in `{local, test}` and the pilot flag on **at evaluation time** (not only at issue time). Anything else is `DENIED`. A proof attached to a `REAL` or `LEGACY_UNCLASSIFIED` profile is always `DENIED`. The legal branch is untouched, including for `LEGACY_UNCLASSIFIED` profiles (their legal consent lookup behaves as today). The source of "run" at decision time must be stated in the T1 report.

Every accepted synthetic decision writes an audit entry with the proof id, basis version and decision basis, and never writes a consent field.

## A5. Operator tool constraints (review P2-6)

`tools/synthetic_eligibility.py` must default to dry-run, refuse unless the database host is loopback or the database name contains `be1_acceptance`, refuse unless `settings.env` is `local`/`test` and the pilot flag is on, issue only for profiles whose origin is `SYNTHETIC_DEV`, and never print secret values (settings or connection strings). `settings.env` defaults to `local`, so it proves nothing by itself.

## A6. Migration and model corrections (review P2-4, P2-7)

- Revision id at most 32 characters (the Alembic version column defaults to 32); use a short id such as `20261031_be1_se_0001`. The file name may stay as approved. `down_revision` is exactly `20261024_0005`, no `depends_on`, no branch label; verify head counts by both the `down_revision`-only and the dependency-aware methods and record the numbers (10 and 9 at HEAD).
- The registry route that creates legal profiles is read-only in this task: the ORM default for the new origin column must be `REAL`; the migration backfills existing rows to `LEGACY_UNCLASSIFIED` through a server default that is then removed.
- Downgrade must fail closed when synthetic rows exist, and the report must state how.
- No cross-table lookup inside a SQL CHECK.
- Keep the legal branch in `be1_sessions.py` calling the name `consent_is_effective` imported into that module, so the existing monkeypatch at `test_be1_postgres_api.py:316` keeps its effect; pass it into the evaluator as a callable.

## A7. Gates before schema work

P0–P3 (domain, tests of pure logic) may start after approval. P4, P5, P6 and P7 are blocked until the BE1 owner (`CaoDat-2410`) confirms **in writing**: the `data_origin` enum values and name, the proof table shape, the migration parent, and the `be1_canvas.py` append change (A1). The T1 report must cite that confirmation's location and SHA-256; an owner approval, a chat message relayed by the project owner, or the T0 decision slip does not count. Also confirm writer and reviewer for `settings.py` (T0 boundary O13 shows `NEEDS_OWNER`) and for the migration.

## A8. Baseline command (review Q4)

Run from `backend/`, not the repository root (the settings class reads both `backend/.env` and a `.env` in the current directory; running from the root loads the root file as well). From `backend/`, with `PYTHONPATH` set to `src`, no `BE1_TEST_DATABASE_URL`, `--basetemp` outside the repository and `--tb=no -q` (tracebacks can print setting values), run the five files named in the plan. The exact reference result on this machine is **26 passed, 4 skipped**; report exact numbers, not "about". The root-directory cause of earlier failures is a hypothesis, not a verified fact; do not open any `.env` file to check it.

## A9. Housekeeping

- P0 owner-local list: the dirty tracked files are three (`docs/context/SOURCE_REGISTER.md`, FEAT-063 `CONTEXT.md`, FEAT-063 `status/STATUS.md`) plus four untracked notes, seven paths in total; `DEV_REMOTE_HISTORY_COMPARISON_20261030.md` is locally ignored and clean.
- The plan status line saying `READY_FOR_TASK_APPROVAL` is superseded by the approval entry.
- `list_profiles` returns 409 for a whole class when any active profile there lacks legal-effective consent (G02, legal gate kept). A class holding a synthetic profile therefore breaks the Teacher UI profile list; the pilot uses a dedicated class and the report records this.
- No code path can currently create an `effective` legal consent row in a real database (CHECK allows only `pending` or `revoked`), so positive legal-path cases can only be tested with the existing monkeypatch style.

## A10. Approval request

Owner records a new T1 approval entry that pins this addendum's SHA-256 together with the original plan hash and the four T0 hashes, and states D1 and D2. Without it no T1 code edit is allowed. The original T1 approval remains for P0–P3 only if the owner says so explicitly.

# FEAT-064 T1 revision A — P0–P3 implementation evidence

> **Update (revision B):** sections 1–8 below record P0–P3 as they were first delivered. Section 9 records P4–P9, implemented afterwards under the `T1 revision B` approval entry, **before** the BE1 owner's written confirmation. Where section 9 and the P0–P3 text disagree (for example "P4–P7 remain BLOCKED", the 18 strict xfail), section 9 is current.

> Scope: pure domain logic and offline test definitions only, 2026-10-31 Asia/Saigon. This is not completion of T1, BE1 runtime acceptance, or a Modal quality result. P4–P7 remain BLOCKED. The complete profile → join → admit → Start → group → turn → append-stroke flow is **NOT_RUN until T12**. No database, Alembic, backend service, MinIO, Modal, GPU, network or real child data was used. No dotenv or token file was directly inspected or edited. No stage, commit or push was performed.

## 1. Authority and P0

- Branch: `feature/feat063-be-foundation`; baseline HEAD `e669e9c1`.
- The owner-written `T1 revision A` entry in `../approvals/TASK_APPROVAL.md` is APPROVED for P0–P3 only. Its local change is exactly the 26 added lines of that entry. This execution did not edit approval.
- Exact input hashes verified before source/test edits:

| Input relative to FEAT-064 | SHA-256 |
|---|---|
| `plan/B4_T1_ELIGIBILITY_IMPLEMENTATION_PLAN_20261031.md` | `131DDB39019572E9FFCC1B5CB21ABC848583637803E9227E518BBA3526E01E31` |
| `plan/B4_T1_ADDENDUM_A_20261031.md` | `A8397E3944DEAF0B693E90248D86A33DCA0755E3CB21F6F52747CA272F2DEAA6` |
| `evidence/T0_CONTRACT_FREEZE_20261031.md` | `476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B` |
| `evidence/T0_GUARD_DISPOSITIONS_20261031.csv` | `B02543FF2591BF4EF3B422E08E64865CF407299B6CE3FBBC88C8863BBD268F69` |
| `evidence/T0_METHOD_INVENTORY_20261031.csv` | `F1AA5BF4C54FD24D87FAE5454AE1CE4D8E1191C992AAB17EC671FE5AE0DF6191` |
| `evidence/T0_EXECUTION_MANIFEST_20261031.csv` | `3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605` |

P0 status matched the owner allowlist: three tracked local context edits (+12/+12/+16), four untracked FEAT-063 notes/card, the local T1 revision A approval and the untracked Addendum A. All four task output files were absent. `DEV_REMOTE_HISTORY_COMPARISON_20261030.md` is locally ignored, outside the seven dirty owner paths. Its reference prefix is `ADCC6724EBC3C642`.

## 2. What P3 implements

`domain/eligibility.py` contains immutable fetched-fact/scope/proof/decision dataclasses, `EligibilityBasis` with three outcomes (`LEGAL_CONSENT`, `SYNTHETIC_DEV`, `DENIED`), closed `EligibilityReason` values and `basis_version=eligibility-decision-v1`. `ProvisionalDataOrigin` and its values are explicitly **PROVISIONAL**, not a persistence schema approved by BE1.

- No framework, HTTP, storage, provider, environment lookup or implicit clock is imported. The evaluator receives the evaluation time, runtime environment, current pilot flag and fetched proof as inputs; it does not fetch or authenticate them.
- Synthetic requires the exact synthetic origin, valid versioned proof, exact organization/class/Child/purpose/run bindings, optional session binding, current local/test environment and literal boolean `True` pilot opt-in. Missing session run denies. The run source for future P5 wiring is **`session.configuration["pilot_run_ref"]`**, never a client header/body field. That wiring is not implemented here.
- Expiry is exclusive. Future issuance, non-aware clocks, empty identifiers, unsupported versions, any revocation, missing proof and scope/run mismatch deny. Comparisons normalize timestamps to UTC, including repeated DST hours.
- Proof attached to REAL or LEGACY_UNCLASSIFIED always denies, even if the fetched legal result is true. Without proof, the legal branch preserves the existing effective lookup for REAL and LEGACY_UNCLASSIFIED. This follows Addendum A4 and the current owner instruction, which supersede the original plan's blanket legacy denial. Pending/revoked legal lookup returns false; unknown/missing legal eligibility does not grant legal consent.
- The decision has no `consent_effective` field and never mutates its facts or creates consent rows. Synthetic and legal bases remain distinct.

The domain is a policy over **trusted server-fetched facts**. It does not prove proof authenticity or stop a public client by itself. Server proof issuance/storage, current-fact retrieval, default-off settings and HTTP enforcement remain blocked P4–P6 work.

## 3. Files and SHA-256 (P0–P3 only; superseded by section 9.2 for the current hashes)

| Repository-relative output | Before | After |
|---|---|---|
| `backend/src/sketch2life/domain/eligibility.py` | ABSENT | `6B84DD889083959218B8FD32219BD25C20356C20EA49ADDD7361FA4682D7396B` |
| `backend/tests/unit/test_synthetic_eligibility.py` | ABSENT | `7DA333B75D07D601ED6CD702725ACAA229400A5F71B14403D124DA3FCF8DE762` |
| `backend/tests/contract/test_be1_synthetic_pilot.py` | ABSENT | `C1D21CED6834F74CB238AD38878989437E1F0C817A39270E949CD50427E284CB` |
| This implementation report | ABSENT | Final file hash reported to owner after writing; no self-referential hash embedded. |

All BE1, persistence, settings, application, migration, approval, plan and T0 sources remain unedited by this execution. Final protected-file hash verification is recorded in §8.

## 4. P1 baseline and P2 tests-first evidence

P1 ran from `backend/` with the owner's exact command:

```powershell
$env:PYTHONPATH = "src"
Remove-Item Env:BE1_TEST_DATABASE_URL -ErrorAction SilentlyContinue
& .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --tb=no -q --basetemp "$env:TEMP\feat064-t1-baseline" tests/contract/test_app_composition.py tests/contract/test_session_http_api.py tests/unit/test_classroom_stage_policy.py tests/unit/test_session_lock_pool.py tests/integration/test_be1_postgres_api.py
```

Exit 0, **26 passed, 4 skipped** (pytest's configured second quiet flag prints progress without a numeric footer). The four PostgreSQL tests skipped because `BE1_TEST_DATABASE_URL` was absent. This is not a PostgreSQL acceptance result. No dotenv file was opened to diagnose or modify configuration; the existing baseline test code loads its own Settings normally.

Tests-first sequence:

1. Created unit tests before `domain/eligibility.py`. Running that test file with `--tb=no` exited 1 with one collection error. A separate `importlib.util.find_spec` check returned `DOMAIN_MODULE_PRESENT=False`, verifying the missing domain module rather than a configuration failure.
2. Implemented the pure domain module; the initial 90 domain cases passed.
3. Independent read-only review identified the repeated-DST-hour issue. Added three tests first (expiry, issuance and interval); **3 failed, 90 deselected**. Normalizing comparisons to UTC made all three succeed.
4. Contract tests were written against unchanged BE1 sources before any P5 edit. The 18 P5 tests are all `xfail(strict=True, reason="blocked until P5 BE1 confirmation", raises=AssertionError)`. Unexpected exceptions such as NameError/TypeError or source-structure LookupError are not hidden as expected failures.

There are **93 domain cases**, **11 passing static boundary cases**, and **18 strict expected failures** for future P5 wiring. No old test expectation or monkeypatch point was changed.

## 5. Guard coverage and exclusions

| Guard | Exact source function | Current P0–P3 result | Pending P5 tests |
|---|---|---|---|
| G03 Start | `be1_sessions._transition` (Start branch) | Unchanged legal gate; BLOCKED | Typed reachability + synthetic-positive + DENIED/409/audit: 3 strict xfail |
| G04 admit | `be1_sessions.admit_device` | Unchanged legal gate; BLOCKED | Same 3 strict xfail |
| G05 group assignment | `be1_sessions.assign_member_to_group` | Unchanged legal gate; BLOCKED | Same 3 strict xfail |
| G07 turn | `be1_sessions.start_child_turn` | Unchanged legal gate; BLOCKED | Same 3 strict xfail |
| G08 device authority | `be1_runtime.get_verified_device` | Unchanged legal SQL; BLOCKED | Same 3 strict xfail |
| **G18 append gate** (report-only addition, no change to pinned CSV) | `be1_canvas.append_canvas_operation` currently calls `_require_group_consent` | Separate append helper required; BLOCKED | Same 3 strict xfail; append must stop calling the shared legal-only helper |
| G13 Start parameter | Existing application `consent_ready` | Unchanged | D2 is an intentional override: future router may pass eligibility-ready; no synthetic consent field and no service-file edit |
| G15/G16 | BE2 member/analysis gates | **NOT_IN_T1** | No BE2 runtime acceptance |

The 11 passing AST tests verify five other canvas functions retain their exact legal helper call/keywords, the group helper retains its effective-consent SQL, progress/help remain legal-only, registry/records do not reach the typed evaluator, and both artifact routes retain effective-consent SQL.

Exact five canvas exclusions: `sync_canvas_operations`, `save_checkpoint`, `read_latest_checkpoint`, `restore_checkpoint`, `reconnect_canvas`. Other exclusions: `be1_sessions.update_progress`, `request_help`; `be1_records._require_contributors_consent`; registry functions, including `create_profile`; `be1_artifacts.upload_session_artifact` and `download_session_artifact`. Tests traverse source AST and function/from-import call edges without importing HTTP apps or settings.

**Limits of guard probes:** positive/negative probes compile only actual consent-denial clauses from source, injecting a legal lookup returning false, a typed evaluator spy and an in-memory audit sink. They do not run full routes, SQL, device authorization or transactions. Today synthetic-positive gets the old legal denial; typed-negative preserves 409 `CONSENT_NOT_EFFECTIVE`/`denied_consent_pending` but never consults the evaluator. These missing consultations cause expected assertion failures. The append probe currently targets the existing legal group helper; P5 must rebind it to the confirmed separate append helper and review extraction/dataflow for the confirmed lookup seam. Thus these are pending test definitions, not verified synthetic guard behavior or drop-in future acceptance.

## 6. Final checks after P3 (P0–P3 only; superseded by section 9.4)

Commands run from `backend/` for regression; Ruff, mypy and repository validators run from the repository root. Temp paths use the operator's existing temp directory outside the repo.

```powershell
$env:PYTHONPATH = "src"
Remove-Item Env:BE1_TEST_DATABASE_URL -ErrorAction SilentlyContinue
& .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --tb=no -q -o addopts='' --basetemp "$env:TEMP\feat064-t1-regression-final" tests/contract/test_app_composition.py tests/contract/test_session_http_api.py tests/unit/test_classroom_stage_policy.py tests/unit/test_session_lock_pool.py tests/integration/test_be1_postgres_api.py tests/unit/test_synthetic_eligibility.py tests/contract/test_be1_synthetic_pilot.py
```

| Check | Actual result |
|---|---|
| Final seven-file regression | `130 passed, 4 skipped, 18 xfailed in 20.97s`, exit 0; no failed or XPASS cases |
| Ruff on all three new Python files | `All checks passed!`, exit 0 |
| `mypy --strict` on all three new Python files | `Success: no issues found in 3 source files`, exit 0 |
| `python tools/validate_harness.py` | `HARNESS_VALID`, exit 0 |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`, 5944 publishable files scanned, absolute machine paths absent, exit 0 |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID`, exit 0 |
| `git diff --check` | Exit 0, no whitespace errors |
| Whitespace/UTF-8 check on exactly four untracked outputs | 4/4 valid UTF-8 without BOM, final LF present and no trailing whitespace |

Exact static check commands:

```powershell
& backend/.venv/Scripts/python.exe -m ruff check --no-cache --config backend/pyproject.toml backend/src/sketch2life/domain/eligibility.py backend/tests/unit/test_synthetic_eligibility.py backend/tests/contract/test_be1_synthetic_pilot.py
& backend/.venv/Scripts/python.exe -m mypy --strict --cache-dir "$env:TEMP/feat064-t1-mypy" backend/src/sketch2life/domain/eligibility.py backend/tests/unit/test_synthetic_eligibility.py backend/tests/contract/test_be1_synthetic_pilot.py
python tools/validate_harness.py
python tools/validate_repository_security.py
python tools/validate_architecture.py
git diff --check
```

During development, Ruff found import/line-format issues in the new files; these were fixed only there. Strict mypy initially found six dynamic `dataclasses.replace` keyword typing errors, then a missing `tzname` method in the new test-only timezone class. All were fixed. No pre-existing mypy error was encountered by the final three-file check; this is not a claim about the full repository's typing.

## 7. P4–P7 restrictions recorded, not implemented (superseded: P4–P7 were implemented, see section 9)

- P4 persistence/schema/migration, P5 routing/guards, P6 operator command/settings and P7 remain **BLOCKED** until `CaoDat-2410` provides the written confirmation required by Addendum A7, with location and SHA-256, and a new exact-scope approval permits the work. Enum/table shape, migration parent, append helper and migration/settings writer/reviewer still require that confirmation. No such confirmation is claimed here.
- Add a separate append-only helper, not an optional keyword on the common consent helper. The other five canvas sites remain legal-only. G18 above exists only in this report; pinned T0 CSV is untouched.
- Audit successful synthetic eligibility at state-changing operations (admit, Start, assignment, turn) and denial; avoid successful audit writes on every device check/stroke. Include proof id, basis and basis version; never change consent fields. This follows the owner's latest instruction over Addendum A4's generic successful-audit sentence.
- Retain `consent_is_effective` in `be1_sessions` for the existing monkeypatch. G13's parameter interpretation is an explicit owner override; BE2 G15/G16 remain NOT_IN_T1.
- Migration source is **not created**, and no migration is run. Future short revision id is at most 32 characters (proposal `20261031_be1_se_0001`), sole parent `20261024_0005`, no branch label/depends_on. ORM default REAL; classify existing rows LEGACY_UNCLASSIFIED through a temporary server default then remove that default; preserve existing consent references; downgrade fails closed if synthetic rows exist. DDL compilation, downgrade behavior, static new-revision graph checks and DB acceptance are NOT_RUN until their approved phase.
- Future operator tool: SQLAlchemy `make_url`; inspect host and query `host`/`hostaddr`; require loopback host or database name containing `be1_acceptance`; default dry-run; do not resolve DNS; local/test and runtime pilot opt-in required. No tool or setting is edited here.
- Pilot session admits **one Child only**, in a dedicated class/group. A group-wide invalid participant closes the gate. `list_profiles` stays legal-only and returns 409 for a class containing a synthetic profile. Sync/reconnect stay legal-only, so the Child UI cannot be described as fully working with a synthetic session.
- Real PostgreSQL chain from operator profile creation through accepted stroke is **NOT_RUN until T12**. Existing skipped PostgreSQL tests, domain tests, static tests and strict xfails do not replace that chain. No Modal request or provider-quality conclusion.

## 8. Owner-local and protected-file preservation

| Owner-local path (FEAT-063 unless stated) | P0 SHA-256 prefix | Final prefix |
|---|---|---|
| `docs/context/SOURCE_REGISTER.md` | `4746959ECF655EA6` | `4746959ECF655EA6` |
| `CONTEXT.md` | `FF1D43486C0A680C` | `FF1D43486C0A680C` |
| `status/STATUS.md` | `072A72EDB4879C79` | `072A72EDB4879C79` |
| `evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md` | `8BBFD0EDAA7CD6A2` | `8BBFD0EDAA7CD6A2` |
| `evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md` | `B61B06074665BA71` | `B61B06074665BA71` |
| `evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md` | `93374E9643649B67` | `93374E9643649B67` |
| `plan/S1_DECISION_CARD_20261030.md` | `4D95D3031F8AF163` | `4D95D3031F8AF163` |

Separately protected with full SHA-256 before verification: 41 files comprising harness/approval/plan/T0 inputs, existing BE1 router/runtime/settings/persistence sources and all 22 existing migration scripts. Final comparison: **41/41 unchanged**. The seven dirty owner-local files also remain unchanged; the tracked context delta remains +12/+12/+16, approval remains its owner-written +26 revision-A lines, and the index is empty.

## 9. Revision B — P4–P9 (local working tree only; not pushed)

### 9.1 Authority and the missing BE1 confirmation

- Approval: the `T1 revision B` entry in `../approvals/TASK_APPROVAL.md`, recorded 2026-10-31 12:06 at the owner's instruction ("Ghi approval rồi làm"). It pins the plan (`131DDB39…`), Addendum A (`A8397E39…`), Addendum B (`3D25743B7278186F11D0F6AC3F02F0DF145CED68772FFD9FA41B3140EBEAD402`) and the four T0 files, and authorizes exactly Addendum B section B8.
- **BE1 confirmation by `CaoDat-2410`: NOT PRESENT.** The owner chose to proceed on the PROPOSAL values of Addendum B and to rework if they change. Nothing here is a BE1 co-signature.
- Values used (all PROPOSAL): `be1_managed_profiles.data_origin` ∈ {REAL, SYNTHETIC_DEV, LEGACY_UNCLASSIFIED}; table `be1_synthetic_eligibility_proofs`; revision `20261031_be1_se_0001`, sole parent `20261024_0005`; setting `synthetic_pilot_enabled` (env `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED`), default `false`. Rework triggers: a changed name, column, parent or setting key.

### 9.2 What changed

| Path | Change |
|---|---|
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `data_origin` (ORM default `REAL`), `consent_id` and `consent_purpose_ref` now nullable, two single-table CHECKs, new `SyntheticEligibilityProofModel` (CHECKs for origin, interval, revocation) |
| `backend/alembic/versions/20261031_be1_synthetic_eligibility.py` | New migration source, never run. Backfills existing rows to `LEGACY_UNCLASSIFIED` through a temporary server default, then removes it. Downgrade raises before dropping anything if any proof, `SYNTHETIC_DEV` profile or profile without consent references exists |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | `load_profile_origin`, `load_synthetic_proof` (take the request `Session`); store methods `get_profile_origin`, `get_synthetic_proof`, `create_synthetic_profile`, `issue_synthetic_proof` (refuses a non-`SYNTHETIC_DEV` profile), `revoke_synthetic_proof` (one-time) |
| `backend/src/sketch2life/infrastructure/config/settings.py` | `synthetic_pilot_enabled: bool = False` |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | `eligibility_decision` and `eligibility_ready`: fetch current server-side facts, call the pure evaluator; `consent_is_effective` is passed in by the caller and is unchanged |
| `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py` | Typed gate at Start (`_transition`), `admit_device`, `assign_member_to_group`, `start_child_turn`; `consent_ready` now means "eligibility ready" (D2). `consent_is_effective` is still imported by name in this module. Progress and help are unchanged |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py` | `get_verified_device` uses the typed gate; new `runtime` dependency to read settings |
| `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` | Separate `_require_group_eligibility` used only by `append_canvas_operation`; the five other sites still call `_require_group_consent` |
| `tools/synthetic_eligibility.py` | New operator command: `create-profile`, `issue`, `revoke` |
| the two test files | See 9.3 |

SHA-256 before (HEAD) → after:

| Path | Before | After |
|---|---|---|
| `settings.py` | `C2AC5064EC9FEA4B8E3F591CE4B923C72A804DBC4F3EC5E50CFE218A905DBFB6` | `DB1A5FB6E4F7C800F00B4AD1F9386D20AEE7F41DBD35BA54C7F13426D7CDD387` |
| `be1_models.py` | `59957310F62C188BB934E54B76999D885936A48DB8C607DDF10DDBCBC697D683` | `735599B638090ABAD59CE3FBFB9630708C3A3DDB2F199994DD3C106B597E38D3` |
| `core_store.py` | `D32AF10E0FDD76EBE2739E2DFE6386750BEC590D631A3F614E23CFFEBF9C72A3` | `7E96852E81AEBBAE9985F03E07B49F9F8A94001C220FFEA6236417C90C213FD4` |
| `be1_runtime.py` | `E7A990F325FECD79672E4751C287F58914FEB499276312BE6BBC0A7190372A85` | `DC565DAA2F45FBC97577F24BEB48B89A7AED2D5CC7AACD40945D720A632C5763` |
| `be1_canvas.py` | `9D68761473A3C3322E8FD36DD650C8997B9DE13E3B4000A029133AC2C5127A0E` | `A2CFE7C0B5998FAF9D56C33ED5A2C5E7E203892855FDC154BA1996B1A489D8ED` |
| `be1_common.py` | `6EF19F03AF0C74353D6723DB239C6E5059B224C2DF202F3D5BB9B3961C41F07D` | `40DDE6F9B2AC91A78FE2A2F65B15EFCB1B76D132D49BB5580338710B12B9C45C` |
| `be1_sessions.py` | `A7BCA0FCA0217B19E1E0ADE0A3EB67B2FE120188617EA0DD9F3AC1A2B8A4BAAB` | `C0CE27189CBFA362CF172BBDC77D5E9C64F98082AC64CAECD99F5EE46E2F1D11` |
| `20261031_be1_synthetic_eligibility.py` | ABSENT | `421F695FE49193C4A2EDCAC66B4461D8AFCB47B825813918E0083B21BC1483FC` |
| `tools/synthetic_eligibility.py` | ABSENT | `5470F125F9DC4CD9F4826D0C15ABB817B7F178A799CE2033CCCF43C588DED8E1` |
| `domain/eligibility.py` | unchanged | `6B84DD889083959218B8FD32219BD25C20356C20EA49ADDD7361FA4682D7396B` |
| `test_synthetic_eligibility.py` | `7DA333B7…` (P0–P3) | `D6E642E5F561733BE95F8957B99A032E8487C96085C62FF4C838896973CC2942` |
| `test_be1_synthetic_pilot.py` | `C1D21CED…` (P0–P3) | `7B753BA466F36839BA9E2285553B12477C4C8054C0F212BB6416D1B1F5F386D7` |

### 9.3 Decisions and behavior to review

- **Decision inputs.** Profile origin and the most recently issued proof for the exact organization, class, Child and purpose are read inside the request transaction. The run comes only from `session.configuration["pilot_run_ref"]` (D3); a non-string or missing value denies. Settings `None` means the pilot is off, so only the legal basis can grant. A missing or inactive profile is handled as a profile without origin information, so only the pre-existing legal lookup can grant (see M-4 in 9.6); it can never be synthetic. Because the latest proof wins, issuing a new proof after a revocation is the way to re-enable a Child.
- **Legal path.** `REAL` and `LEGACY_UNCLASSIFIED` keep the effective-consent lookup, through the name `consent_is_effective` imported into `be1_sessions` (the monkeypatch at `test_be1_postgres_api.py:316` keeps its effect). A proof attached to a legal profile always denies; an effective legal result on a synthetic profile denies as a conflicting basis. No consent row or field is written or mapped.
- **Denial shape.** `deny_pending_consent` is untouched, so 409 `CONSENT_NOT_EFFECTIVE` and audit `denied_consent_pending` stay. `get_verified_device` keeps its own denial audit and 409.
- **Audit (OD-B1, accepted in the approval).** An accepted synthetic decision writes one audit row (action `<operation>.synthetic_eligibility`, resource type `synthetic_eligibility_proof`, resource id = proof id, decision `allowed_synthetic_dev:eligibility-decision-v1`) at Start, admit, group assignment and turn only. Device checks and strokes write none. The audit table has no metadata column, so proof id, basis and basis version are carried in those three fields; no schema change.
- **Schema consequence to confirm with BE1.** `consent_id` and `consent_purpose_ref` had been NOT NULL; the CHECK keeps them mandatory for `REAL`. Existing rows become `LEGACY_UNCLASSIFIED` and keep their references.
- **Behavior change outside the pilot.** `get_verified_device` and four session routes gained a `runtime` dependency (FastAPI `Depends(get_runtime)`); route paths and responses are unchanged. `get_verified_device` now calls the shared `consent_is_effective` instead of an inline identical query.
- **Order of work.** P5 followed test-first (after wiring, the six reachability tests failed as strict XPASS and the guard probes failed with `NameError`, which showed the old definitions no longer matched). **P4 did not**: the model and migration were written before their static tests, which were added right after. This is a process deviation, not a result.
- **Operator tool.** Dry run is the default and opens no connection; `--apply` writes. It refuses unless `settings.env` is `local`/`test`, the pilot setting is on, `--pilot` is given, and every effective host (URL host plus query `host`/`hostaddr`, no DNS) is loopback **or** the database name contains `be1_acceptance`. It never prints settings or URLs. It was exercised only with fakes; it was **not run** against a database.

### 9.4 Tests and checks (actual results, 2026-10-31)

| Check | Result |
|---|---|
| Baseline, five CI files, from `backend/`, no `BE1_TEST_DATABASE_URL`, `--basetemp` outside the repository | `26 passed, 4 skipped` |
| Seven files (baseline plus the two new) | `227 passed, 4 skipped`, no failed, no xfail (after the review fixes in 9.6; the first run was 209) |
| `test_synthetic_eligibility.py` | 138 passed (domain 93, static migration and model checks, operator tool with fakes) |
| `test_be1_synthetic_pilot.py` | 63 passed: static AST checks (including the 6 reachability cases that were strict xfail and the value checks added after review), 12 guard probes (the other former xfail cases, now active), typed-seam cases with replaced lookups |
| Ruff on all twelve touched Python paths | `All checks passed!` |
| `ruff format --check --config backend/pyproject.toml` on the five new or fully-owned files (run from the repository root, or from `backend/` with `pyproject.toml`) | already formatted. **The project formatter configuration is `backend/pyproject.toml` (line length 100); the repository has no ruff configuration at its root.** Run without `--config` from the root, ruff falls back to its default line length of 88 and reports `tools/synthetic_eligibility.py` (and 32 of the 40 existing `tools/*.py` files) as unformatted; that is a configuration difference, not an unformatted file. The edited existing files were not formatter-clean at HEAD, so they were not reformatted |
| `mypy --strict` on all twelve paths | 4 errors, all pre-existing (checked again with `be1_registry`, `be1_records` and `be1_artifacts` added: only their pre-existing `responses=` errors remain, the new `be1_registry.py:281` error found by the reviewer is gone): the same 4 appear at HEAD in `be1_canvas.py` (router `responses` type, untyped `_record_response`, `rowcount`) and `be1_sessions.py` (router `responses` type) |
| `tests/unit` + `tests/contract`, whole directories | not clean: 25 collection errors (missing modules such as `imageio`, `tools.*` not importable from `backend/`) and failures in unrelated suites. In a HEAD export, the same failing set (plus a few more because untracked assets are absent there) fails too; no failure is new. This is **not** a claim that those suites pass |
| `validate_harness`, `validate_repository_security` (5947 files), `validate_architecture`, `git diff --check` | all valid, exit 0 (the security validator first rejected a test constant named `*_SECRET*`; it was renamed) |

### 9.5 NOT_RUN, limits and blockers

- **No PostgreSQL run.** The migration was not executed, its DDL was only compiled with the PostgreSQL dialect, and its downgrade guard was only read. `test_be1_postgres_api.py` stays skipped. Head counts were computed statically from the revision files: before 10 (by `down_revision`) and 9 (with `depends_on`); after 10 and 10, as derived.
- **End-to-end chain NOT_RUN until T12:** create profile → join → admit → Start → group → turn → append stroke. The guard probes execute only the extracted denial clause with the typed seam replaced; they are not route tests. The seam itself is covered with replaced lookups, not SQL.
- **Pilot limits unchanged.** One Child per pilot group (a group-wide gate); `list_profiles` still returns 409 for a class that holds a synthetic profile; sync and reconnect stay legal-only, so the Child UI is not fully working with a synthetic session.
- **Not touched:** `be1_registry.py`, `be1_records.py`, `application/services/be1_runtime.py`, BE2 (G15 and G16 stay NOT_IN_T1), progress and help, artifacts, the five other canvas sites.
- **Blockers before any push:** BE1 written confirmation of the PROPOSAL values; writer and reviewer for `settings.py`, the migration and the tool (T0 O13, O16); independent review of this revision; a separate owner instruction to commit.
- Seven owner-local file hashes are unchanged (`4746959E`, `FF1D4348`, `072A72ED`, `8BBFD0ED`, `B61B0607`, `93374E96`, `4D95D303`). The tracked context delta is still +12/+12/+16; the approval file now carries +26 (revision A), +15 (revision B) and +13 (revision C, recorded 2026-10-31 14:35, which records decisions C1 session binding is mandatory and C2 `policy_version` is audit-only) lines. Nothing was staged, committed or pushed.

### 9.6 Independent review (separate read-only session) and what was done about it

Verdict of the reviewer: **NEEDS REVISION (light)** — 0 High, 4 Medium, 6 Low, and no path found by which a synthetic Child is accepted without a valid proof. Disposition:

| # | Finding | Status |
|---|---|---|
| M-1 | `session.configuration["pilot_run_ref"]` is set by the teacher who creates the session, and `--session-id` is optional in the tool, so a proof without `session_id` matches any session in the class with the same `purpose_ref` and `run_ref` | **FIXED (owner chose "fix all three").** A proof for a `SYNTHETIC_DEV` profile now counts only if it names a session: `eligibility_decision` in `be1_common.py` drops a session-less proof, so the result is `PROOF_REQUIRED`, and `tools/synthetic_eligibility.py issue` requires `--session-id`. A session-less proof on a `REAL`/`LEGACY` profile is still passed on and denied as before. `domain/eligibility.py` is unchanged (it is outside B8). This is stricter than Addendum B B2/A4, where `session_id` is optional; the pinned documents were not edited, so please note it in the next approval entry. D3 should also state that `pilot_run_ref` is teacher-writable |
| M-2 | `consent_purpose_ref` is now `str \| None` and is passed to `consent_is_effective(purpose_ref: str)` in `be1_registry.py:281`; `mypy --strict` reports a NEW error there (it is outside the twelve paths this report checked) | **FIXED.** `consent_is_effective` in `be1_common.py` now accepts `purpose_ref: str \| None` and returns `False` for `None` (the same result the old `== NULL` query gave). `be1_registry.py` stays untouched and the mypy error is gone |
| M-3 | At Start, audit rows for earlier synthetic Children were committed by `deny_pending_consent` when a later Child was denied | **FIXED.** New `eligibility_all_ready` computes every decision first and audits only if all pass; two tests (all pass: one audit per Child; one denied: no audit, in either order) |
| M-4 | The legal branch now also needs an `active` profile and a non-empty `purpose_ref`; previously only an effective consent row was needed. A Child archived mid-session gets 409 at device check, stroke, turn and Start. The earlier "Legal path unchanged" wording was too strong | **FIXED, with a residual.** When no active profile row is found the Child is treated as `LEGACY_UNCLASSIFIED`, so only the old effective-consent lookup decides (an archived-after-admission Child behaves as before). It cannot become synthetic because that needs a `SYNTHETIC_DEV` row plus a proof that references it. Residual differences: an empty `purpose_ref` is now `INVALID_FACTS` (old code would query with `''`; no session is expected to have one), and an archived `SYNTHETIC_DEV` profile is denied. Still no PostgreSQL test |
| L-1 | Reachability tests checked keyword names only | **FIXED.** They now assert the values (`legal_effective=consent_is_effective`, `settings` per caller, `audit_action` suffix), the `settings` forwarding from `start_session` to `_transition` and from the append route, and that the three modules still bind the shared `consent_is_effective` |
| L-2 | `ORDER BY issued_at DESC LIMIT 1` had no tiebreaker; no row lock, so a stroke can pass between the check and a concurrent revoke | **PARTLY FIXED.** Tiebreaker `evidence_id DESC` added. The race window is accepted for a dev pilot and is not closed |
| L-3 | `be1_acceptance` is a substring test, so a remote host with that name is accepted; `issued_by` is self-declared; no `revoked_by`; no operator audit row | OPEN, low. Matches Addendum A5 as written; tighten later if wanted |
| L-4 | Drift test compared only the five CHECK texts | **FIXED.** It now also compares column nullability, foreign-key names and `ondelete`, the index columns, and which columns the migration relaxes to nullable; the ORM foreign keys were given the names the migration uses |
| L-5 | Sections 3, 6 and 7 contradicted section 9 | **FIXED.** Headings marked as superseded |
| L-6 | `interfaces/http/be1_runtime.py` now imports `routers.be1_common` (cycle risk if `be1_common` ever imports the runtime) | NOTED. Architecture validator is clean |

Not verifiable without PostgreSQL (reviewer and implementer alike): the migration itself, all SQL in `core_store.py`, the skipped PostgreSQL tests, and the full chain. The reviewer also noted that `tests/integration/ai_jobs/test_migrations.py:115-136` assumes the `be1_core` head is `20261014_0004`, which looks stale against `20261024_0005` already at HEAD; it was not run and is unrelated to this change unless a PostgreSQL run is approved.

### 9.7 Second independent review (Codex) and what was done about it

Verdict of the reviewer: **NEEDS REVISION** — 0 High, 1 Medium, 4 Low. It again found no way to make a Child synthetic-eligible without a valid proof, or to turn synthetic into legal consent. All 16 pinned hashes and the 7 owner-local hashes matched; it reproduced 26/4 and 220/4, ruff, the three validators and the known mypy errors, and did not run PostgreSQL, Alembic or an export of HEAD.

| Level | Finding | Status |
|---|---|---|
| Medium | The operator tool accepted a free-text `child_id`, `display_name` and age and stored them under `SYNTHETIC_DEV`, so a real child's name or identifier could be stored under a synthetic label | **FIXED.** `--display-name` was removed (the name is derived: `Synthetic <child_id>`); `create-profile` and `issue` accept only `synthetic-[a-z0-9-]{1,100}`; `PostgresCoreStore.create_synthetic_profile` refuses a non-`synthetic-` id or a name not starting with `Synthetic ` before touching a session. Age stays bounded to 36–155. Tests: namespace cases, no name option, the store guard |
| Low | `load_synthetic_proof` was called for every decision, including `REAL`/`LEGACY`, so a failure reading the proof table could turn a legitimate request into HTTP 500 (Addendum B section 3 says an unreadable proof means "no proof") | **FIXED.** The proof table is read only when the profile origin is `SYNTHETIC_DEV`; legal and missing-profile decisions never touch it (test: the loader raises if called). Consequence to know: a stray proof on a legal profile is no longer looked up at runtime. It cannot be created through the tool or the store (both refuse non-synthetic profiles, the proof references the profile row and the origin has no update path); the evaluator still denies it in the domain unit tests. A failed proof read for a synthetic profile still surfaces as an error, which is fail-closed. A PostgreSQL transaction that failed cannot be continued anyway, so catching the error would not help |
| Low | Session-less proofs are refused although Addendum B section 2 says `session_id` is optional | **KNOWN, needs an approval line.** Stricter than the pinned documents; report and tool state it. Not edited in the pinned files |
| Low | `policy_version` is stored but not passed to the evaluator; `pilot_enabled` at issue time is not stored (T0 lists both as bindings) | **OPEN — owner decision.** Treat both as audit data (current behavior: the pilot setting is re-checked at every decision and the tool refuses to issue when it is off), or have the evaluator also require a matching `policy_version`. Recommended: audit-only, recorded as such in the contract |
| Low | Report said all five owned files pass `ruff format --check` while the reviewer saw one file needing a format | **EXPLAINED, no code change.** The reviewer (and the commit run) invoked `ruff format --check --no-cache` from the repository root without `--config`, which uses ruff's default line length 88 instead of the project's `backend/pyproject.toml` (100). Reproduced both ways: with `--config backend/pyproject.toml` all five files are formatted; without it `tools/synthetic_eligibility.py` is flagged, and so are 32 of the 40 `tools/*.py` files that already exist. The report now states the exact command |

Still not verified: PostgreSQL, Alembic, the full chain (T12), and an independent export-of-HEAD comparison for the unrelated failing suites (the first reviewer's number confirmation only).

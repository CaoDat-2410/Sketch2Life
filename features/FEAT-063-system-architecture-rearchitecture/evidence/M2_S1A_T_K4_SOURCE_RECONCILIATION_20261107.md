# M2 S1a-T K4 source reconciliation

**Status:** SOURCE-ONLY COMPLETE; implementation stopped at a product-scope conflict. No source or test file was changed.

## Owner-reported facts

- D-154 records an owner-run, read-only inventory of `sketch2life` on PostgreSQL 17.11 at loopback port 5433: 117 tables and 82 rows, recorded as 24 existing rows plus 58 synthetic rows. This report does not independently verify the database. The pinned inventory file reports `report_kind=read_only_inventory_observation_not_approval`, uses `alembic_method=static-ast`, and records row counts rather than row values.
- The inventory contains one `SYNTHETIC_DEV` row in `be1_managed_profiles` and one in `be1_synthetic_eligibility_proofs`; it does not expose profile ages. D-154 records the database/source revision discrepancy as K3 FAIL and unresolved. No conclusion about the live Alembic graph is drawn here.
- The owner-reported state of `sketch2life_m2_s1a` is 117 tables, zero rows, and an empty Alembic version table. This is not verified by this source-only review.

## Source facts

- `backend/src/sketch2life/infrastructure/persistence/be1_models.py` defines `be1_managed_profiles.age_months` with a database check of 36–155; the model also restricts `age_source` to `LEGACY_UNKNOWN`, `SYNTHETIC_FIXTURE`, or `ADULT_DECLARED`, and `data_origin` to `REAL`, `SYNTHETIC_DEV`, or `LEGACY_UNCLASSIFIED`. Its consent-reference check permits `SYNTHETIC_DEV` only when both consent references are NULL. These are source declarations, not proof of the live database schema.
- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` currently defines organization-scoped POST and DELETE assignment routes. Its existing `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` handler requires an effective consent, accepts client-supplied child and consent identifiers, calls the shared age validator, and stores `age_source="ADULT_DECLARED"`.
- R5 §2.1 names that exact POST method and path as the Teacher synthetic profile/enrollment route, while D-160 and R5 §2.2 say the existing route using `ADULT_DECLARED` must remain unchanged. The source has only one handler for this method/path. Replacing its behavior with the synthetic-only contract would change the existing route; retaining its current behavior would not implement the R5 synthetic contract on that path.
- `backend/src/sketch2life/contracts/schemas/be1_runtime.py` currently permits `CreateProfileRequest.age_months` from 36 through 155 and lets assignment requests supply role and nullable class ID. `be1_registry.py` implements organization-level assignment authorization and does not enforce one active Teacher per class.
- `backend/src/sketch2life/interfaces/http/routers/be1_common.py` currently returns 404 `CLASS_NOT_FOUND` from `get_class` and uses shared authorization behavior that can return different denial codes. R5 requires uniform 403 `SCOPE_DENIED` for the three M2 class/assignment cases without changing global `authorize_adult` behavior.
- `backend/src/sketch2life/domain/core_foundation.py` defines `validate_age_months` as 36–155. Its callers include the existing registry write path and read/eligibility paths in `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py`, `backend/src/sketch2life/domain/assistance.py`, `backend/src/sketch2life/domain/vision_context.py`, and `backend/src/sketch2life/application/services/vision_analysis.py`. The latter paths validate resolved facts used by assistance and vision decisions. The named regression tests cover these paths, including accepted 155-month values.
- R5 §5 marks `core_foundation.py` R/E, the BE1 request schema and registry router E, and the named assistance/vision reader and policy modules R. Therefore changing the shared validator so its default rejects 121–155 would alter read paths outside the edit allowlist. The BE1 model's 36–155 database check is also read-only under this approval; no migration or schema edit is authorized.
- The allowed tests include existing contract, composition, OpenAPI, and named regression modules plus new S1a-T service, route, and PostgreSQL modules. `test_profile_age_invariant.py` and `test_synthetic_eligibility.py` are read-only under R5. No test or validator was run during this reconciliation.

## Inference

- The R5 method/path collision is a semantic scope conflict, not an implementation detail that can be resolved by a router refactor: one method/path cannot both retain the current consent-bound `ADULT_DECLARED` behavior and implement the specified consent-free `SYNTHETIC_DEV` Teacher behavior. Choosing a second path, replacing the existing behavior, or changing D-160/R5 requires an owner decision and a corresponding approved artifact update. No option is selected here.
- Preserving the shared age validator's existing 36–155 default would avoid rejecting stored values in the read paths; applying the 36–120 bound only when validating new Teacher input could preserve those paths. This is a compatibility observation, not a decision to change the approved contract. The implementation must not proceed until the route conflict is resolved and the exact validator call contract remains consistent with R5.
- R5's one-Teacher race rule requires the class-row lock, active-Teacher count, and assignment insert to occur in the same database transaction. This follows from the specified concurrency invariant and current lack of a database uniqueness constraint; it does not authorize a schema change.

## Unknowns and limits

- The actual ages of the 82 owner-reported database rows, including whether any existing row is 121–155 months, are unknown. The pinned inventory is count-only; no database was queried and no row value was read.
- The live contents and identity of `sketch2life_m2_s1a` are not verified. No database, Alembic command, migration, or launcher was used.
- No runtime route-count or OpenAPI result was obtained in this source-only step. R5's target counts remain acceptance criteria, not observed results.
- No code, test, validator, or static-analysis result is claimed. PostgreSQL tests, the owner launcher, Modal, and providers remain NOT RUN.

## Stop gate

Implementation is **NOT RUN** pending the owner's resolution of the conflict between the R5 Teacher profile method/path and the unchanged `ADULT_DECLARED` route required by D-160/R5. No later phase is opened. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.

## Resolution

**Status:** the source-level route conflict recorded above is resolved by owner decisions D-163 and D-164. This resolution does not change the historical source observations or claim that the implementation has already been performed.

- A fresh cold, read-only independent review of D-163 and Approval Addendum 2 returned **READY, 0 P1 / 0 P2 / 0 P3 new findings** (review thread `01a1bb5a-1364-75f0-90dd-bdfa546deb19`). The reviewer verified the DECISIONS and approval pins, append-only history, and R5 artifact pins.
- D-163 selects the sole existing `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` handler as the Teacher synthetic profile/enrollment operation. Under the approved contract it will create a server-issued child ID, store `SYNTHETIC_DEV` with both consent references NULL, and use `age_source=SYNTHETIC_FIXTURE`, gated to local/test plus `synthetic_pilot_enabled`. The previous consent-bound `ADULT_DECLARED` creation behavior is removed from this method/path. `ADULT_DECLARED` remains valid in the model enum, database CHECK and readers; those are not changed.
- Age compatibility is resolved: keep `validate_age_months` default at 36–155 for existing callers and read paths; apply an explicit 36–120 bound only to new Teacher input and `CreateProfileRequest`. Do not change the database CHECK, use `child_age.py`, or clamp/rewrite existing 121–155 values.
- D-164 classifies Bruno 013 as an in-repository historical artifact like Bruno 004/005. It remains unchanged, outside the edit allowlist, and its old POST body is documentation debt, not PASS; no R6 is opened. The Teacher UI profile service only requests the GET list. Actual POST consumers outside this repository remain NOT VERIFIED.
- Review found `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/scripts/validate_be_full_collection.py` reads collection entries including Bruno 013 from `API_COVERAGE.csv`; no test/runner invoking it was found, and it is not an R5 command. The review did not run this script; it sends no POST. This does not authorize changing Bruno 013 or the validator.
- S1a-T may proceed within the existing R5 scope after the review gate. This is not evidence of implementation completion or PostgreSQL acceptance. The R5 owner launcher remains owner-only and has not been run; no DB, Alembic, Modal or provider work occurred. External consumers remain NOT VERIFIED, and the separate documented K3 revision discrepancy remains unresolved.

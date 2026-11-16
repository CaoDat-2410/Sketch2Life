# M2 S1a-T Closure Record — 2026-11-09

**Status: CLOSURE EVIDENCE COMPLETE — OWNER ACCEPTANCE PENDING.** This record collects the evidence for S1a-T (Teacher / organisation foundation). It does not accept S1a-T, does not append an approval entry and does not open any later phase. Only the owner (Person 2) decides ACCEPTED.

## 1. What was delivered

Within the 76-path R7 allowlist, uncommitted in the working tree at `feature/feat063-be-foundation`, HEAD `dd70685eae58aaaefea3e567f5c23d09345a8513`, empty index:

- One Teacher synthetic profile handler on `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles`: server issues `child_id` as `synthetic-` plus 24 hex characters; the client cannot send `child_id`, `consent_id` or `purpose_ref`; stored as `SYNTHETIC_DEV` with both consent references NULL and `age_source=SYNTHETIC_FIXTURE`; only in local or test environments with the synthetic pilot enabled (D-160, D-163).
- Class-scoped Teacher assignment `POST /api/be1/v1/classes/{class_id}/assignments` with exactly one active Teacher per class inside one transaction (class-row lock, count, insert); a second assignment gets 409 `CLASS_TEACHER_EXISTS` without disclosing identity.
- Uniform 403 `SCOPE_DENIED` for missing class, other-organisation class and missing assignment, without changing `authorize_adult`.
- New-profile age window 36–120 months; the shared `validate_age_months` default stays 36–155 for existing read paths.
- OpenAPI counts (acceptance expectation 128 runtime / 123 catalog / 110 paths / 18 tags): the catalog and composition tests that assert them passed (see section 2); the numbers themselves are not printed in the logs.

Final file hashes of the changed and new backend files are in the implementation report (`M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md`, "Update 2026-11-09" sections). Governance records: D-163 to D-171 in `DECISIONS.md`; Approval Addenda 1 to 7 and the `M2 S1a-T Approval R7` entry in `approvals/TASK_APPROVAL.md`.

## 2. Evidence

| Check | Result | Run by | Evidence |
|---|---|---|---|
| Offline pytest (13 modules, 1 case deselected) | 574 passed, 1 deselected, exit 0 | Codex session, then coordinator reruns after test edits | logs `9d100fc0…`, `r6post_76eaa325…`, `r7post_c6230f11…` under `.claude/handoff/logs/M2_S1A_T_20261107_before_r7_20261109T131714/` |
| Composition / OpenAPI pytest | 9 passed, exit 0 | **Owner**, own PowerShell | log `r6owner_d5281b1e…`; stdout SHA-256 `21BB5CD7E56DCB165321D85CEBCB03BA59251CBA5B81CF9873E74772FF40ECAA`; earlier Codex runs failed or errored and are preserved |
| Strict mypy | exit 1, 255 diagnostics in 50 files; 0 new versus baseline after masking line numbers | Codex session | accepted by D-167 only as a baseline comparison; exit 1 remains NO PASS |
| Ruff (E,F,I,UP,B,SIM, 14 paths) | exit 1, 6 diagnostics, all `I001`, identical to the 6 at HEAD | coordinator | not rerun on the final PostgreSQL test file (NOT VERIFIED) |
| `validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check` | exit 0 each | coordinator | `r7post_c6230f11…`; not rerun after the last test edit (NOT VERIFIED) |
| Independent reviews (fresh, cold, read-only) | round 1 READY WITH NOTES (0/3/10); round 2 BLOCKED (1/2/6, fixed by D-171); final READY WITH NOTES (0 P1, 0 P2, 5 P3) | Claude sessions | session ids in the R7 approval entry |
| **PostgreSQL acceptance (R7 launcher)** | **`1 passed in 5.81s`, pytest exit 0, official summary present, post-run inventory `MARKER_COUNTS_MATCH`** | **Owner, once** | `.claude/handoff/logs/M2_S1A_T_20261107/f7fe88273c7f4dd89b3913efeac6f8fb/` |

### 2.1 PostgreSQL run details (read from the log folder)

- Run id `f7fe88273c7f4dd89b3913efeac6f8fb`, target `sketch2life_m2_s1a`, command `.venv\Scripts\python.exe -m pytest tests\integration\test_m2_s1a_teacher_postgres.py -p no:cacheprovider --basetemp …`, cwd `backend`, timeout ceiling 1800 s. Database URL recorded only as `CHILD_ENV_ONLY;VALUE_REDACTED`.
- Pre-run inventory: `PASS_EMPTY`; 117 tables, 0 rows in every table (including `public.alembic_version`).
- Post-run inventory: 117 tables, 29 rows in total; `marker_total` 29; status `MARKER_COUNTS_MATCH`. Rows by table: `be1_adult_identities` 6, `be1_classrooms` 3, `be1_enrollments` 2, `be1_managed_profiles` 2, `be1_organization_assignments` 5, `be1_organizations` 2, `core_aggregate_revisions` 3, `core_audit_entries` 3, `core_outbox_events` 3, `be1_synthetic_eligibility_proofs` 0. This equals the marker table derived independently by two reviews (29 rows).
- The single test function covers: concurrent teacher assignment (one 201, one 409), school_admin / org-wide Teacher / other-class Teacher / other-organisation Teacher denied with identical `SCOPE_DENIED`, ages 35 and 121 rejected, ages 36 and 120 accepted, persisted `SYNTHETIC_DEV` with NULL consent references and `SYNTHETIC_FIXTURE`, and `CONSENT_NOT_EFFECTIVE` on the portfolio lookup.
- `PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED` (a known, declared limit of the launcher).

Log file SHA-256 values: `pytest.stdout.txt` `8A213423263398829547BD3CE3433679569F6A18BBB068692D2651BD73A8E9D0`; `inventory.pre.json` `7BD9311AB95CCDC1B5AA8A464396569F11086C52E959A7396605C8E3A14E40BD`; `inventory.post.json` `710F4A42FA817FA2EC27DC154BF6023F35FD51C012BBACA39782320357D8737E`; `runner-status.txt` `ED776CB348A3E4843DC10169BF2E147891C7A89D1A943F6FB052ABB351DBD65B`; `pytest.exit.txt` `9A271F2A916B0B6EE6CECB2426F0B3206EF074578BE55D9BC94F6F3FE3AB86AA`.

## 3. Consequences for later phases

- **The task database is no longer empty.** `sketch2life_m2_s1a` now holds the 29 synthetic rows above (D-156 and the launcher design keep them; no cleanup is authorised). A later phase launcher that stops when any table has rows needs either a fresh schema-only copy or an owner-approved accounting of these rows. This is an owner decision for the S1a-P approval.
- The `.claude/handoff/logs/M2_S1A_T_20261107` folder now holds only this run; the earlier logs are in the `_before_r7_20261109T131714` folders.

## 4. Not covered, not run, not verified

- NOT COVERED by the spec's own partial status: capacity (`CLASS_CAPACITY_REACHED`) and expected class revision in M2-AT-04A/04B; Platform Admin / Operator / content-admin negative tests (no representation in the identity model).
- NOT VERIFIED: external consumers of the Teacher-profile POST outside this repository; Bruno request 013 and `validate_be_full_collection.py` are not updated (D-164, documentation debt); the K3 revision discrepancy remains unresolved; Ruff / `validate_repository_security.py` / `git diff --check` on the final PostgreSQL test; launcher child-process enumeration.
- Recorded debt (D-170): earlier review P3 items 5 to 9 (swapped verification strings and operation-count constant in `openapi_contract.py`; class lock before authorization check; `flush()` without `IntegrityError` mapping; `IDENTITY_ISSUER_MISMATCH` not mapped to `SCOPE_DENIED`).
- No Modal, provider, GPU or network action occurred. `OWNER_MODAL_CALL_APPROVED=NO`. S1a-P, S1b, S2, S3 and M3–M6 remain closed.

## 5. Open for the owner

1. **ACCEPTED or not** for S1a-T on this evidence.
2. Accept the six residual Ruff `I001` diagnostics (already present at HEAD) as lint debt, with Ruff exit 1 still recorded as NO PASS.
3. Confirm the extra offline pytest runs executed by the coordinator after the B009 and P3 edits.
4. Authorise committing S1a-T as one commit (the working tree is uncommitted).

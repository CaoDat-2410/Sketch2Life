# M2 S1a-P Implementation Report — Update 2026-11-10

## Status

S1a-P implementation is present in the working tree. This update records the owner-requested post-install offline measurements and the installed Firebase Admin SDK source check. The D-180-authorized additional post-implementation verification set remains pending its required fresh independent review. Gate A is NOT LAUNCHED; Gate B is NOT LAUNCHED. No phase is closed by this report.

## Repository state at this update

- Branch: `feature/feat063-m2-parent-teacher-foundation`.
- HEAD: `4b7f07cc283721f01f64e41ff2d81f135f63ad29`.
- Git index: empty.
- The working tree contains the previously authorized S1a-P implementation and plan changes. The separate untracked status update belonging to another session was left untouched.
- `DECISIONS.md`: SHA-256 `7EDA20DEE56092CF9AAE3720E5ED31433943DDB6C620903D45CC0FBA37543D6E`.
- `approvals/TASK_APPROVAL.md`: SHA-256 `428D9254FB0431A943BE93851680D59E17AF7EB5C64DB7631F043C29AE8052F4`.
- Offline wrapper: `evidence/scripts/m2_s1a_p_offline_checks_20261109.py`, SHA-256 `456744ED4C7923973B380D6AF47046D05E495A0B4894CF7875222E29056DEB6B`.

## Installed Firebase Admin SDK source check

The installed distribution metadata reports `firebase_admin` version `7.7.0`. Source was read without importing or executing the SDK:

- `backend/.venv/Lib/site-packages/firebase_admin/_token_gen.py`, SHA-256 `61BD04C07D3676A1EB05E265A679B2FBF3CD878868ACE472ABAB9262FDA341BF`.
- `ExpiredIdTokenError` is defined at line 434 as a subclass of `_auth_utils.InvalidIdTokenError`.
- The token generator is configured with this exception type at line 282. In the verified-token path, lines 407–408 detect the SDK's expired-token condition and raise the configured exception with the original error as `cause`.
- `firebase_admin/auth.py` re-exports the same class at line 122.

This verifies the concrete installed exception type and its source-level cause behavior. No SDK import, network request, Firestore access, or Storage access was performed.

## Post-install mypy measurement

The approved wrapper step `baseline-mypy` ran once on 2026-11-10. At that time, the S1a-P implementation was already present in the worktree; this is therefore a post-install measurement of the current implementation tree, not a pre-implementation source baseline.

- Log directory: `.claude/handoff/logs/M2_S1A_P_20261109/20261110T024637Z_baseline-mypy_e4ddd1e7dae3/`.
- Command: strict mypy over `src/sketch2life` and `tests`, with the cache under the unique log directory.
- Process exit: `1`.
- Official summary: `Found 6723 errors in 308 files (checked 964 source files)`.
- Safety scan: 37 URI-scheme occurrences in stdout were classified by the wrapper as benign mypy documentation references; unsafe-scheme, userinfo, password assignment, PGPASSWORD, bearer-token, and auth-key counts were all zero. Stderr was empty and all corresponding scan counts were zero.
- This result is not PASS and must not be presented as a pre-code baseline.

| Log file | Bytes | SHA-256 |
|---|---:|---|
| `command.txt` | 248 | `AA2119D78EFDCF946620DF718766CA3743F6AA0BA7C230399DFCD97845492025` |
| `stdout.txt` | 987166 | `93ADB9E17F636EEBC59BE768B5C90BEA920001C62E8FA45F494470AC5B49AA14` |
| `stderr.txt` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `exit-code.txt` | 2 | `4355A46B19D348DC2F57C046F8EF63D4538EBB936000F3C9EE954A27460DD865` |
| `safety-scan.json` | 461 | `65DAE0BBFD500138968FC9727284A85496D7F5FB4F57AC23DC5B898DCA8E9DED` |

## Corrected offline pytest measurement

The approved wrapper step `baseline-pytest` ran once on 2026-11-10 using the argument list recorded in its `command.txt`; no extra `-q` was added. As with the mypy measurement above, S1a-P implementation edits were already present, so this is not a pre-implementation test baseline.

- Log directory: `.claude/handoff/logs/M2_S1A_P_20261109/20261110T024747Z_baseline-pytest_a6d80fbd2e52/`.
- Official summary: `242 passed in 47.27s`.
- Process exit: `0`.
- Safety scan: all URI-scheme, userinfo, password assignment, PGPASSWORD, bearer-token, and auth-key counts were zero in stdout and stderr.

| Log file | Bytes | SHA-256 |
|---|---:|---|
| `command.txt` | 535 | `C908D02FB31B5E13FD354A238AC9CE8023C7BFC94AE5B2396AB24B0753E5C5EB` |
| `stdout.txt` | 346 | `3077C7BCC9840A6DDDFB74D240BD1A28E14B7BEB974099C7292A00AEEA1717A3` |
| `stderr.txt` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `exit-code.txt` | 2 | `9A271F2A916B0B6EE6CECB2426F0B3206EF074578BE55D9BC94F6F3FE3AB86AA` |
| `safety-scan.json` | 459 | `E8D54FE88E21B557CDF63751F7CEAC936E70170F7E8466EFF54470953D98D1A1` |

## Remaining verification and gates

- A read-only Python AST parse of the 24 modified or new S1a-P Python source, test, migration, and offline-runner files returned `AST_PARSE_OK=24`. This parsed syntax only; it did not import project modules or execute tests.

- D-180 authorizes one additional run each of Ruff, `validate_repository_security.py`, post-implementation mypy, post-implementation pytest, and `git diff --check`. A fresh cold independent read-only review of the exact append-only rerun addendum must return READY or READY WITH NOTES with 0 P1 and 0 P2 before any of those five invocations. The addendum has not been appended, and those additional invocations are NOT RUN.
- The prior `create_thread` operation for that review remains `outcome_unknown` with `retrySafe=false`; thread discovery returned a transport error. No reviewer session or verdict can currently be confirmed. No new create request was sent.
- PostgreSQL, Alembic, Gate A, Gate B, the launchers, Docker, Modal/provider, and network operations were NOT RUN.
- No approval, closure, or phase acceptance is recorded here. `OWNER_MODAL_CALL_APPROVED=NO`; S1b remains DEFERRED; S2, S3, and M3–M6 remain closed pending their own approvals.


## D-184 remediation update — 2026-11-10

This append-only update supersedes earlier status text that described the D-180 verification addendum or an independent review as still pending. It does not close or accept S1a-P.

### Independent code review before remediation

A cold independent code review of the S1a-P implementation returned **NEEDS_REVISION — 0 P1, 5 P2, 2 P3** (review session `01a1c3d8-d7b8-7a11-9716-5bb1b46be86c`). The findings were:

1. `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py`: successful PATCH responses returned only a profile reference instead of the D-174 profile projection; the router and OpenAPI catalog declared the same narrow shape.
2. `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py`: a replayed `STALE_REVISION` body retained its original `request_id`, while `X-Request-ID` was set from the retry request.
3. `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_gate_a_20261109.py`: Gate A rejected the approved append-only `DECISIONS.md` and progress-report suffixes because the pinned hashes describe their exact Draft 8 prefixes.
4. The same Gate A script rejected approved pre-existing untracked documentation under its broad scope prefixes, including Draft 8 and documents owned by another session.
5. The same Gate A script inferred schema presence only from table names, so an empty `parent` schema could pass preflight and make the one-shot migration fail after launch.
6. `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_IMPLEMENTATION_REPORT_20261109.md`: the report retained stale review, command, and governance status.
7. `backend/src/sketch2life/interfaces/http/openapi_contract.py`: GET `/v1/parent/profiles/{profile_id}` omitted the `400 INVALID_REQUEST` response used for malformed UUID input.

The owner selected remediation for all seven findings. D-184 and the append-only `M2 S1a-P Remediation Addendum — 2026-11-10` authorize only these corrections within the unchanged Draft 8 allowlist. The approval addendum pins the exact Draft 8 prefix hashes for `DECISIONS.md` and the progress report, their current full hashes, and the exact hashes of the pre-existing untracked Markdown documents Gate A may recognize. No untracked source, test, migration, or script path is exempted.

### Remediation applied, awaiting independent review

- PATCH now returns and stores the full `ParentProfileView` projection; its router response model, OpenAPI contract, route assertion, and owner-run PostgreSQL assertion use that projection.
- A replayed error response uses the stored body `request_id` for `X-Request-ID`, falling back to the current request ID when the body has no request ID. Contract and owner-run assertions cover a retry with a different request ID.
- Gate A verifies the two append-only suffixes against both the Draft 8 line-boundary prefix hash and the exact current full-file hashes recorded in the D-184 addendum. It validates the hashes for the exact pre-existing untracked documentation manifest and continues to reject other untracked paths.
- Gate A inventory now reads whether the `parent` namespace exists, and preflight stops if it exists even when it contains no tables.
- The GET Parent-profile OpenAPI contract now declares `400 ParentErrorResponse`; the catalog assertion checks that response. The route contract test covers malformed UUID input.
- The Draft 8 allowlist is unchanged. The text of the untracked status update owned by another session was not displayed or interpreted; its SHA-256 was checked read-only against the exact manifest, and the file was not modified.

### Prior D-183 offline results (not verification of this remediation)

These are the recorded results from the earlier D-183 verification set; they precede D-184 code changes and do not establish the current remediation result:

| Check | Log | Recorded result |
|---|---|---|
| Ruff | `20261110T050127Z_ruff_6ebccbaa7874/` | Exit 1; exactly one existing `I001` at `backend/tests/contract/test_openapi_contract_catalog.py:3:1`; accepted only as D-176 lint debt, not PASS. |
| Offline post-implementation pytest | `20261110T050139Z_post-pytest_211cd89283f0/` | `262 passed in 54.37s`; exit 0. |
| Repository security validator | `20261110T050245Z_validate-security_4fef07a74f26/` | `REPOSITORY_SECURITY_VALID`; 7,108 files; exit 0. |
| `git diff --check` | `20261110T050312Z_diff-check_bda3c5db495a/` | No output; exit 0. |
| Strict mypy | — | NOT RE-RUN under D-183. The recorded pre-remediation measurement remains 6,723 errors in 308 files and is not a PASS. |

### D-184 review and verification gates

The required fresh cold independent read-only review of the exact D-184/addendum and remediation diff is **PENDING**. The five D-184 one-time checks (Ruff, offline post-implementation pytest, repository-security validator, strict post-implementation mypy, and `git diff --check`) are **NOT RUN** until that review returns READY or READY WITH NOTES with 0 P1 and 0 P2. No retry is authorized.

PostgreSQL, Alembic, Gate A, Gate B, the launchers, Docker, Modal/provider, network access, stage, commit and push are **NOT RUN**. `OWNER_MODAL_CALL_APPROVED=NO`; S1a-P remains unaccepted; S1b remains DEFERRED; S2, S3 and M3–M6 remain closed pending their own approvals.

## Owner disposition after D-184 review — 2026-11-10

- The fresh cold independent review session `01a1c3fe-95d0-7453-8ef2-935c9b5cebe5` returned **NEEDS_REVISION — 0 P1, 1 P2, 1 P3**.
- The owner directed that the P3 be corrected as part of D-184 finding 1, without scope expansion. Only the PATCH assertions in `backend/tests/contract/test_parent_profiles_routes.py` and `backend/tests/integration/test_m2_s1a_parent_postgres.py` were strengthened to assert the complete `ParentProfileView`, including identifiers, revision fields, age-band fields, `interests_summary`, state, and origin. The owner-run PostgreSQL test remains unrun.
- The owner directed that the P2 concerning the three concurrent S2/S3 Markdown files remain outside the D-184 manifest. They belong to another active session, may still change, and were not opened, edited, moved, or pinned. They do not block the five D-184 offline checks. No new decision row, approval entry, or Gate A script change is made for this disposition.
- Before any future Gate A launch, a separate Gate A launch addendum must reconcile the then-current untracked-file manifest (or the owner must first move/resolve those documents), pin the then-current `DECISIONS.md` and Gate A script hashes, and pass a separate cold independent review. This disposition does not open Gate A or Gate B.
- The P3 assertion correction has not been independently reviewed yet. The five D-184 one-time checks remain **NOT RUN** pending a fresh cold independent review of the final remediation state. No test, validator, Ruff, mypy, or `git diff --check` was run for this update.
- `OWNER_MODAL_CALL_APPROVED=NO`; S1a-P remains unaccepted; S1b remains DEFERRED; S2, S3, and M3–M6 remain closed pending their own approvals.

## D-184 one-time offline verification results — 2026-11-10

The five checks below were run once each, in the approved order, through the pinned offline wrapper. No retry was made.

| Check | Log directory | Official result |
|---|---|---|
| Ruff | `.claude/handoff/logs/M2_S1A_P_20261109/20261110T063604Z_ruff_7189b6ecea39/` | Exit 1, **NO PASS**. The only diagnostic was the permitted existing `I001` at `backend/tests/contract/test_openapi_contract_catalog.py:3:1`. No other diagnostic appeared. Safety scan: 0 matches. |
| Offline post-implementation pytest | `.claude/handoff/logs/M2_S1A_P_20261109/20261110T063619Z_post-pytest_64adb3f752c9/` | `264 passed in 55.92s`; exit 0. Official summary present. Safety scan: 0 matches. |
| Repository-security validator | `.claude/handoff/logs/M2_S1A_P_20261109/20261110T063734Z_validate-security_311a6ab44fe1/` | `REPOSITORY_SECURITY_VALID`; `publishable_files_scanned=7115`; exit 0. Safety scan: 0 matches. |
| Strict post-implementation mypy | `.claude/handoff/logs/M2_S1A_P_20261109/20261110T063758Z_post-mypy_d823ae979f8b/` | `Found 6723 errors in 308 files (checked 964 source files)`; exit 1; **not a PASS**. The wrapper found 37 scheme URLs, all classified as `https://mypy.readthedocs.io/` documentation links; `unsafe_scheme_url=0` and all credential-pattern counts were 0. |
| `git diff --check` | `.claude/handoff/logs/M2_S1A_P_20261109/20261110T063843Z_diff-check_fb8f258209f5/` | No stdout or stderr; exit 0. Safety scan: 0 matches. |

These results verify only the authorized offline checks. PostgreSQL, Alembic, Gate A, Gate B, the launchers, Docker, Modal/provider, and network access remain NOT RUN. S1a-P remains unaccepted and awaits the separate owner-run Gate A approval and launch. `OWNER_MODAL_CALL_APPROVED=NO`; S1b remains DEFERRED; S2, S3, and M3–M6 remain closed pending their own approvals.

## Independent review follow-up — 2026-11-10

- A fresh cold independent read-only review of the exact D-184 remediation, its addendum, and the two PATCH assertion corrections returned **READY WITH NOTES — 0 P1, 0 P2, 0 P3** in session `01a1c419-9e2b-7a00-99cf-db88516dfc68`.
- The reviewer verified the seven D-184 remediation items, the complete `ParentProfileView` assertions in both the route and owner-run PostgreSQL tests, and the unchanged Draft 8 allowlist. The owner-run PostgreSQL test remains NOT RUN.
- The reviewer noted that the preceding paragraph's statement that review was PENDING is superseded by this result. The report records the owner disposition for the P2 concerning three concurrent S2/S3 Markdown files: they were not opened, modified, moved, or hashed; they remain outside D-184 and do not block its five offline checks. A separate Gate A launch addendum must reconcile the then-current untracked-file manifest (or the owner must first resolve those documents), pin then-current `DECISIONS.md` and Gate A script hashes, and pass a separate cold review before Gate A may be launched.
- The five one-time D-184 checks are authorized by the review gate and have not yet run in this follow-up. No database, Alembic, Gate A/B, launcher, Docker, Modal/provider, network, stage, commit, or push action is authorized here.
- `OWNER_MODAL_CALL_APPROVED=NO`; S1a-P remains unaccepted; S1b remains DEFERRED; S2, S3, and M3–M6 remain closed pending their own approvals.

## Final D-184 status - 2026-11-10

- The earlier sentence in "Independent review follow-up" stating that the five checks had not yet run described the state at that time and is superseded by the completed results recorded above. Each of the five authorized checks completed exactly once; no retry was made.
- The cold review returned READY WITH NOTES with 0 P1, 0 P2, and 0 P3. The owner disposition of the three concurrent S2/S3 documents remains unchanged; they were not opened, modified, moved, or hashed. A separate reviewed Gate A launch addendum is still required before any Gate A launch.
- PostgreSQL, Alembic, Gate A, Gate B, launchers, Docker, Modal/provider, network access, stage, commit, and push remain NOT RUN. S1a-P remains unaccepted; OWNER_MODAL_CALL_APPROVED=NO.

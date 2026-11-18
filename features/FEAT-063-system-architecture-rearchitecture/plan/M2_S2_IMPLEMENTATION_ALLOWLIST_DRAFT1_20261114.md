# FEAT-063 M2 S2 Implementation Allowlist — Draft 1

**Status: DRAFT FOR INDEPENDENT REVIEW / NOT LAUNCHED.** This allowlist draft does not authorize implementation until an owner approval is recorded and a pinned launch prompt is supplied. `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Authority and approved scope boundary

The working product SRS is FEAT-063 v2.7-draft Rev67, adopted by D-203 and still unsigned. The Draft 18 plan file itself remains DRAFT / NOT APPROVED; the separate D-205 approval record approves it only as a bounded S2 specification with the deviations listed below. This is not a claim that the scoped S2 implementation conforms to every Rev67 Parent-flow requirement. D-204 fixes the route-specific cancel-success body; D-205 approves the specification only; D-206 fixes the route-specific stale-cancel error field. D-199 through D-206 remain controlling.

Implement only the integrated Parent StoryRun path. Do not add a StoryRun-lite adapter, additive DDL, migration, a job-ID route, purge worker, provider cancellation, AI-job cancellation, mobile change, or new run state. Use the existing state `DELETE_PENDING`.

### Required behavior

1. Add `run_revision` as an output-only integer sourced from the existing `story.runs.revision` in the shared `ParentStoryRunResponseV1`; do not add `purge_state` to `ParentStoryRunResponseV1` or `ParentStoryRunEnvelopeV1`.
2. Add only `POST /v1/story-runs/{run_id}/cancel`. Require `Idempotency-Key` and JSON `expected_revision`. Return HTTP 202 with exactly `{request_id, story_run, purge_state}`; `request_id` is the existing UUID field defined by `ParentStoryRunEnvelopeV1` in `backend/src/sketch2life/contracts/schemas/parent_story_runs.py:136-138`, using the established request-ID generation pattern; do not invent a new ID field or type. `story_run` is the existing response type with `run_state=DELETE_PENDING` and `run_revision`; `purge_state` is `PENDING`. Persist that exact body, including `request_id`, in the `CANCEL_RUN` receipt. Replay the same body for the same key/run/request before checking `expected_revision`.
3. Preserve D-200 mismatch behavior: HTTP 400 `INVALID_IDEMPOTENCY_KEY` for a changed request fingerprint, including cross-run reuse. For stale cancel `expected_revision`, return HTTP 409 `STALE_REVISION` with top-level integer `current_version` equal to the current `story.runs.revision`; include it only in this error on the cancel route. Preserve the other Rev67 §9.8 fields. Refuse the specified wrong-state cases with HTTP 409; do not invent other public error codes or fields.
4. Add the D-201/D-202 pre-write `DELETE_PENDING` guards to artwork-analysis failure/unknown and story-generation success/failure/unknown paths. Each newly guarded path returns HTTP 409 `INVALID_STATE_TRANSITION` without changing run columns or writing a result, story revision, or receipt. Preserve the already-guarded artwork-analysis success code `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING`.
5. Forward these guard errors from the existing Parent AI routes through the top-level Rev67 §9.8 envelope. Use the existing safe Vietnamese message map/fallback in `app.py`; do not invent a new user-facing string. Preserve the exact existing artwork route and scope any formatter branch to that route only.
6. Keep AT-10 on trusted stored age for **new-run admission only**: 36 and 120 months accepted, 121 and 155 rejected before repository writes with HTTP 422 `INVALID_REQUEST`. Existing-profile completion, legacy-draft access, notices, edits, archive, and migration remain outside S2 acceptance per Draft 18 and Rev67 §31.10(16). Do not modify other age or profile lifecycle behavior; if the pinned code contradicts the new-run rule, stop for owner direction.
7. AT-09 adds compatibility tests for the three named existing assistance operations only. No assistance route or behavior changes.

### Rev67 §21.4 stale-revision crosswalk correction under D-206

Draft 18 AT-08 and its Section 6 cancel crosswalk recorded the stale status and code but omitted the current version required by Rev67 §21.4. D-206 resolves that omission for this implementation: the cancel route's HTTP 409 `STALE_REVISION` uses the standard Section 9.8 error envelope and must include optional top-level integer `current_version` equal to current `story.runs.revision`. The field is emitted only for that stale-cancel error; no other error or route changes. D-201's `run_revision` remains the field in the successful `story_run`; D-204's HTTP 202 body remains exactly `{request_id, story_run, purge_state}`. The existing Parent profile error contract and mobile parser already use `current_version`; the mobile lane remains read-only and is not in this allowlist.

### Recorded Rev67 deviations to preserve

The S2 implementation does not reorder the Parent flow to image-first, add mandatory pre-story activity selection or its recovery, implement the deferred context snapshot or lesson pin, add post-playback activity retrieval, add `GET /v1/jobs/{job_id}`, or run purge/provider/job cancellation after `DELETE_PENDING`. These remain recorded deviations under D-196/D-198/D-199 and D-203; do not call them SRS-conformant or silently expand this allowlist to close them.

## 2. Exact file allowlist

`E` means an existing file may be edited. `N` means a new file may be created. Every E file is hard-pinned to the current bytes below; stop before editing on any mismatch. N files must be absent at launch. No other path may be edited or created.

### E — existing files allowed to edit

| Repository-relative path | Last-observed bytes | SHA-256 | Permitted purpose |
|---|---:|---|---|
| `backend/src/sketch2life/application/ports/parent_story_runs.py` | 6,140 | `374E2B4003164C90A2C55F06DE8A9FE8F970BE393806D143C9DF4BF6E06BF77F` | Add run revision to the existing record contract and carry optional current-version metadata on the specified stale-cancel error. |
| `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 7,309 | `C026A1566500EE7B7C2705DFCE6C4E0D0EC7B397E9FE93F11A237A416F768B19` | Add shared `run_revision`, cancel request and route-specific cancel success/error response typing if needed; keep `current_version` optional and cancel-error-specific; keep purge state route-specific. |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 64,452 | `407D2843A93C31BD54202A1E504DE938FB085E67730C199FD4E9B9505E72B832` | Map revision, persist cancel receipt/body transactionally, enforce revision/replay ordering and late-result guards; attach current revision only to stale cancel failure. |
| `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 12,698 | `32C707515032FC7BEF08A12D0B1D8E6DD4271FF1B9C55891072BA76E150D6B60` | Map revision in existing reads, forward `current_version` only when present on stale cancel, and add the single cancel route. |
| `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | 21,869 | `8EEDD486148E16350885DBD737C5A3A0F7A4E0906AD473165FBEDB84C7CAC1FE` | Map `run_revision` in `_story_response` and forward only the specified new late-result guard errors. |
| `backend/src/sketch2life/interfaces/http/app.py` | 73,534 | `262CB4583ED545F92DF784B69D426C834D5D7BD23179A61C5C818E6C50F4C298` | Add exact-artwork-route handling to the existing safe top-level error envelope; add `current_version` only for HTTP 409 `STALE_REVISION` on the cancel route; reuse the existing Vietnamese safe-message map and preserve all other route/error bodies. |
| `backend/tests/contract/test_parent_story_run_request_contract.py` | 10,299 | `50178038EFD7BBBC792DDEA5D5610D7AE74165757A28EC3950B2BDF0FD12DF4E` | Request validation and response contract assertions. |
| `backend/tests/contract/test_app_composition.py` | 13,451 | `B738F3BF89D233544FB062D5DB50AED6A8B6DD7A92C0B7020E72E138569D877B` | Existing route composition and generated OpenAPI assertions. |
| `backend/tests/contract/test_assistance_request_contracts.py` | 6,345 | `30B6EEDC5AD11D7B26746782E59794614BF9FEEDC440E5894EC694F0D2C05FFC` | The three existing assistance compatibility operations only. |
| `backend/tests/contract/test_assistance_requests_api.py` | 8,306 | `7DD80544C9FD6F142C2510108D669298DE6E0D87D94B61B373BD7C5901D3DF8A` | The same three existing assistance compatibility operations only. |
| `backend/tests/unit/test_parent_story_run_create_service.py` | 2,112 | `71AB2706ED10AD0F36F02C0C5103444ADB400C54D9887924592E74FE6F33708C` | Trusted-age boundary regression coverage; no unrelated service changes. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,721 | `B585C2A87DC50FE6B9571B0AA5DDFB0D0F2918FE69D04749EAE5C9BAEC998255` | Reconcile the existing route catalog if required by the one cancel path. |
| `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | 9,157 | `A0CB85E214E80BED8EE9AEEF665CC9979F579553BD9117D0D8D682DF641AD8F5` | Add the exact cancel route to the route baseline only. |
| `docs/context/PROJECT_CONTEXT.md` | 83,183 | `317D947803D78F1F78D2DA9BEA8E9DF3F718DE8965DFD57E1A665A0A5F1BE612` | Append concise S2 implementation status after the work. |
| `docs/context/SOURCE_REGISTER.md` | 115,027 | `0093F8CCE26A526D72C8B940BE8CCE250DB78A9AE852B4834F3ABB639965081A` | Append concise implementation evidence and status pointers after the work. |

### N — new files allowed

| Repository-relative path | Launch state | Permitted purpose |
|---|---|---|
| `backend/tests/unit/test_parent_story_run_cancel_repository.py` | Must be absent | Offline repository-level cancellation, receipt, revision, and late-result guard tests using fakes only. |
| `backend/tests/contract/test_parent_story_run_cancel_route.py` | Must be absent | Cancel request/response, replay ordering, stale revision including the required `current_version` field and its absence from other errors, owner scope, and HTTP status/body contract tests. |
| `backend/tests/contract/test_parent_ai_late_result_guards.py` | Must be absent | Parent AI guard forwarding and top-level localized error-envelope tests for the specified paths. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | Must be absent | Pins, changed files, test/check outputs, limitations and final status. |

### R — read-only hard-pinned references

| Repository-relative path | Bytes | SHA-256 |
|---|---:|---|
| `backend/src/sketch2life/application/services/parent_story_runs.py` | 7,630 | `FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14` |
| `backend/src/sketch2life/interfaces/http/parent_runtime.py` | 5,203 | `4329F4E775B2954C53268A836D4A7A30C2923F77E6EDD9B3AACFA7D05E47FA49` |
| `backend/src/sketch2life/infrastructure/story_run_lite/repository.py` | 132,748 | `58952C2A210785DBC6459C6FAC6203C5F5460DFEDD7852CD1375E12821E709D5` |
| `backend/alembic/versions/20261102_story_run_lite.py` | 28,335 | `D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143` |
| `backend/alembic/versions/20261112_parent_story_context.py` | 8,251 | `CFC7A92436066191134E27F1579B54109057CBAC43ABEB72B84C0F2D6CBFD9DF` |
| `backend/pyproject.toml` | 3,383 | `35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2` |

### H — hard-frozen paths

Do not edit `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`, `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`, Draft 18, the SRS artifact, `docs/context/SRS_AUTHORITY.md`, `.gitattributes`, migrations, any file under `.worktrees/mobile`, or any file outside E/N. The FE lane inputs remain informational and are not eligible for edits.

## 3. Command ceilings and execution boundary

Use only the already-installed local Python tools; do not install/sync dependencies. Run commands from the specified directory. A combined pytest invocation counts as one test run.

| Check | Maximum runs | Exact selection |
|---|---:|---|
| Targeted backend unit/contract tests | 2 total: run 1 initial, run 2 final after fixes | From `backend/`: `python -m pytest -q tests/contract/test_parent_story_run_request_contract.py tests/contract/test_parent_story_run_cancel_route.py tests/contract/test_parent_ai_late_result_guards.py tests/contract/test_app_composition.py tests/contract/test_assistance_request_contracts.py tests/contract/test_assistance_requests_api.py tests/contract/test_openapi_contract_catalog.py tests/unit/test_parent_story_run_create_service.py tests/unit/test_parent_story_run_cancel_repository.py` |
| Strict typecheck | 2 total: run 1 initial, run 2 final after fixes | From `backend/`: `python -m mypy src/sketch2life` |
| Ruff | 2 total: run 1 initial, run 2 final after fixes | From `backend/`: `python -m ruff check src/sketch2life/application/ports/parent_story_runs.py src/sketch2life/contracts/schemas/parent_story_runs.py src/sketch2life/infrastructure/persistence/parent_story_repository.py src/sketch2life/interfaces/http/routers/parent_story_runs.py src/sketch2life/interfaces/http/routers/parent_ai.py src/sketch2life/interfaces/http/app.py` |
| Harness validator | 1 final run | From worktree root: `python tools/validate_harness.py` |
| Architecture validator | 1 final run | From worktree root: `python tools/validate_architecture.py` |
| Repository security validator | 1 final run | From worktree root: `python tools/validate_repository_security.py` |
| Whitespace check | 1 final run | From worktree root: `git diff --check` |

No database or migration access, Docker, provider, network, Modal, Android, install, stage, commit, or push is authorized by this allowlist. No runtime, task-database, concurrency-under-PostgreSQL, Gate A, Gate B, or production BE1 role-adapter success may be claimed. `D-190` remains NOT COVERED; K3 remains NOT VERIFIED; `OWNER_MODAL_CALL_APPROVED=NO`. If a selected test reaches a database/provider/network or cannot run with installed tools, stop and report it; do not substitute a different test or install dependencies. Any needed command that the implementer cannot run must be returned as a ready-to-run command card for the owner.

## 4. Stop conditions

Stop before editing if branch, HEAD, any hard pin, route composition, receipt columns, migration graph, or required writer inventory differs from this approval; if any required behavior needs DDL, a new state, a route beyond cancel, a response field beyond D-204's exact 202 body and D-206's stale-error `current_version`, or another owner contract decision; if a file outside E/N is needed; if a test exceeds the stated boundary; or if evidence cannot distinguish known failure from unknown provider outcome. Preserve working-tree changes and report the exact blocker. Do not call partial implementation complete or READY.

# M2 S1a-P2 real-PostgreSQL evidence addendum

```yaml
record_type: EVIDENCE_ADDENDUM
audience: AI agents and validators reading repository state (machine-oriented; not a message to a person)
subject: S1a-P2 known gap "Real-PostgreSQL PATCH, DELETE, and list are NOT VERIFIED"
amends: NONE (append-only; the closure record is cited, never edited)
closure_record: features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_CLOSURE_RECORD_20261112.md
closure_record_status_at_time_of_writing: ACCEPTED WITH KNOWN GAP
this_record_status: SUPPORTING_EVIDENCE_ONLY
approval_record: NO
owner_acceptance_of_gap_closure: NOT_RECORDED
date: 2026-11-13
owner_modal_call_approved: NO
modal_calls_made: 0
```

## 1. Boundary of this record

- This file is supporting evidence. It is not an approval, a decision, or a closure. Do not treat the known gap as closed until the owner records that in `approvals/TASK_APPROVAL.md` through the normal append-only path.
- Do not edit the closure record or any pinned record to reflect this file.
- The environment below is a scratch database inside a local Docker Compose project. It is not the M2 task database and not production.

## 2. Build and environment under test

| key | value |
|---|---|
| code_commit_tested | `9dfdd2d7` (integration of S1a-P2 `77cf761d` over the dev Parent story flow) |
| repository_file_under_test | `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py` |
| repository_file_bytes_sha256 | 19813 B / `1AF38B44ACBB40C94BD0B77F54A1BF0B1C90AE5F8C9F9D9A95DA055B5F4D1742` (equals the Current pin in the closure record; re-hashed at the pushed tip) |
| backend_runtime | Docker Compose project `s2l-int`, services api and postgres, started with `--no-deps` |
| database | scratch PostgreSQL in that project, host port 55432 on loopback only |
| migrations | `alembic upgrade heads` (multiple heads) |
| env_flags | `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true` via a local override file that is not in the repository |
| auth | real Firebase project; client signs in, then `GET /api/auth/v1/me` |
| client | Android emulator, native app in `apps/ui-mobile`, backend reached through the emulator host alias |
| modal | not called; no provider call of any kind |

## 3. Results observed

| id | operation | observed result | evidence source | verified_by |
|---|---|---|---|---|
| E1 | `GET /v1/parent/profiles?limit=25` | HTTP 200 | backend api log lines during the session | owner-run, owner-observed |
| E2 | `POST /v1/parent/profiles` | HTTP 201 (synthetic profile) | backend api log lines during the session | owner-run, owner-observed |
| E3 | `PATCH /v1/parent/profiles/{id}` | HTTP 200 | backend api log lines during the session | owner-run, owner-observed |
| E4 | `DELETE /v1/parent/profiles/{id}` | HTTP 202 (`DELETE_PENDING`) | backend api log lines during the session | owner-run, owner-observed |
| E5 | `POST /v1/story-runs` | HTTP 201 (run created) | backend api log lines during the session | owner-run, owner-observed |
| E6 | `POST /v1/story-runs/{id}/context-confirmation` | HTTP 200 | backend api log lines during the session | owner-run, owner-observed |
| E7 | `GET /v1/story-runs/active/current` | HTTP 200 (after re-login) | api log excerpt quoted in the test log | owner-run, owner-observed |
| E8 | `GET /api/auth/v1/me` | HTTP 200 (role gate passed) | api log excerpt quoted in the test log | owner-run, owner-observed |

- E3 and E4 are the operations the closure record lists as NOT VERIFIED on PostgreSQL. They returned success on the build that contains the ownership pre-check transaction fix.
- Raw api log files for E1 to E6 were not archived in the repository. Treat E1 to E6 as owner-observed, not machine-reproducible from repository artifacts. Only the E7 and E8 log lines are quoted in the supporting test log.

## 4. Not verified by this record

| id | item | status |
|---|---|---|
| N1 | second `DELETE` of the same profile returning 409 | NOT RUN |
| N2 | field-validation 400 on profile create or patch | NOT RUN |
| N3 | backend `409 ACTIVE_RUN_EXISTS` on a second run | NOT RUN against PostgreSQL (the mobile UI blocked the action before any request; covered by offline route tests only) |
| N4 | production BE1 role adapter | NOT COVERED (still open under D-190 as in the closure record); the role gate here ran on the scratch database |
| N5 | cursor pagination beyond one page | NOT RUN (one page only) |
| N6 | Gate P2 runner second attempt | NOT AUTHORIZED; the original approval remains CONSUMED |
| N7 | any Modal or AI provider behavior | NOT RUN (`OWNER_MODAL_CALL_APPROVED=NO`) |

## 5. Related facts for downstream readers

- A run created in this session sat in `run_state = INPUT_PROCESSING` after context confirmation, and the mobile client cannot resume that state. See the supporting test log and `plan/BE_AI_HANDOFF_FOR_AI_AGENT_20261113.md` (open questions BQ-1 and BQ-2).
- Two test runs were set to `FAILED` by hand in the scratch database to unblock new runs. This was a manual data edit, not a product path.
- Supporting test log: `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REAL_FLOW_NO_MODAL_TEST_LOG_20261113.md`.

## 6. Machine-readable summary

```yaml
gap_item: real_postgresql_patch_delete_list
status_evidence: OBSERVED_SUCCESS_ON_SCRATCH_DB
patch: 200
delete: 202
list: 200
create: 201
raw_logs_archived: false
formal_gap_closure_recorded: false
next_action_owner: Person 2 (records or declines gap closure in TASK_APPROVAL.md)
```

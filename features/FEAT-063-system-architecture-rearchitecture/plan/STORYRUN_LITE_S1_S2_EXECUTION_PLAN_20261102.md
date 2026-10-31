# StoryRun-lite S1 → S2 execution plan — 2026-11-02

Status: **APPROVED / IN_PROGRESS by the owner's launch instruction below**. This is one continuous goal. S2 starts when S1's code and offline acceptance are ready; no M0 review or owner gate is inserted between them. This plan does not call V12 `ACCEPTED` and does not authorize live Modal/provider execution.

## Authority and baseline

- Owner instruction: current-thread `/goal` request to execute the full S1→S2 launch prompt and its pinned master goal without a pause between stages; prompt SHA-256 `13067726F17892EDD4E8A10EF0EF24DE65ED4F8FAB913FE1C7753612177A070C`.
- Master goal: `STORYRUN_LITE_S1_S2_MASTER_GOAL_20261102.md`, SHA-256 `C5E8B15839FA3470596DAC4B964450BD56428D481EA1A78B8AEC70B2E6A02B42`.
- Requirements: V12 SHA-256 `D0560C4B7821EA76A50780D00161DE1D1AC9917168B9C975547077C457FB448B`, with §10 taking precedence over older fixture-only/5 MB/4 MP statements and §9 applying otherwise; Goal 1 plan SHA-256 `0447E054079CA2FF3595773DE4C7A3B77EE41FF28E23831A47103D93FC7B083A`; V11 review SHA-256 `755FF00669104900B1F728C35107ABEE123BC31B65D258900508A7CA3C51F1A5`; Owner Decisions V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Baseline verified: branch `feature/feat063-be-foundation`, HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, index empty. The pre-change Git-visible local inventory is `evidence/STORYRUN_LITE_S1_S2_LOCAL_CHANGE_BASELINE_20261102.md`, SHA-256 `0BB9B961D2EFF556D3535F2506A4BBA75E313788779DC166326C408C238A931E` (83 paths; includes all 3 FEAT-061 local documents and the A2/FEAT-064 work). Those entries remain protected and are not part of this plan's implementation allowlist.
- Sources were hash-checked before planning. SRS/DTR and A1 source are design inputs, not evidence of runtime readiness.

## Outcome and architecture

Deliver a local synthetic Parent backend: 10 versioned API operations; upload 1–5 contiguous parts of at most 4 MiB each and at most 20 MiB / 20,971,520 bytes total; JPEG/PNG/WebP, at most 40,000,000 pixels; immutable original snapshot, server hashes, local quarantine, ClamAV-before-parser gate, isolated normalization to a V2-compatible JPEG/PNG input, lineage, fake Vision (S1), then the same typed photo binding through the existing A1 ledger/guard/HTTP transport against HTTP loopback only (S2). Story CONFIRM/cancel, CAS revisions, dual Core/Story command receipts, exact replay, crash hold/recovery, OpenAPI and Bruno handoff are in scope.

Photo input will have its own typed source binding and adapter. It will not manufacture canvas/checkpoint data or modify `ObservationRequest`, `application/services/vision_analysis.py`, canvas codecs/call sites, Modal deployment, or A1 migrations. The photo invocation service will use the existing `InvocationLedgerGuard`, `InvocationLedger`, and `HttpJsonTransport`; it persists a validated Story result receipt/revision before finalizing that same A1 invocation. This is the additive seam equivalent to a `before_finalize` hook and keeps A1 canvas defaults unchanged. The V2 adapter currently caps its input at 5,000,000 bytes and accepts JPEG/PNG; the derived model input must be checked against that contract, while the original remains unchanged.

## Environment findings before implementation

- Python 3.12.10 and `backend/.venv` are present; Pillow, PyAV, psycopg, SQLAlchemy, Alembic, pytest, Ruff and mypy are installed; Pillow reports WebP support.
- Windows 10 build 26200.9168. Docker CLI exists but the Docker daemon is unavailable. `clamscan`, `clamdscan`, PostgreSQL client executables, and `pywin32` Job Object bindings were not found. PostgreSQL 17 and 18 services report `Running`; no DB has yet been connected or modified. A unique goal-owned disposable database must be created and its owner verified before any migration/test connection; never use a configured/default DB or A2 database.
- ClamAV service availability and Windows Job Object enforcement are **NOT VERIFIED**. Implement fail-closed scanner and worker boundaries; do not represent stub verdicts as scanner CLEAN. If a real local scanner or enforceable worker cap cannot be verified, continue independent code and loopback work and mark the corresponding readiness gate NOT VERIFIED.

## Exact initial file allowlist

Only create or change the following paths. New modules are additive; existing local-dirty paths are excluded. If investigation requires another source path, amend this plan and approval before touching it.

### Contract and UI handoff artifacts

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/bruno.json`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/environments/local.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/01-create-run.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/02-create-upload.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/03-upload-part.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/04-complete-upload.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/05-get-upload.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/06-attach-asset.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/07-get-run.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/08-confirm-subject.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/09-cancel-run.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/requests/10-abort-upload.bru`

### Backend implementation and migration

- `backend/src/sketch2life/domain/story_run_lite.py`
- `backend/src/sketch2life/application/ports/story_run_lite.py`
- `backend/src/sketch2life/application/services/story_run_lite.py`
- `backend/src/sketch2life/contracts/schemas/story_run_lite.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/__init__.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/tables.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/repository.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/quarantine.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/clamav.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/image_worker.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/fake_vision.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/composition.py`
- `backend/src/sketch2life/infrastructure/persistence/core_models.py` (typed Core asset owner columns only)
- `backend/alembic/env.py` (register the new metadata only)
- `backend/alembic/versions/20261102_story_run_lite.py` (new additive `story_run_lite` branch; no old migration edits)
- `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py`
- `backend/src/sketch2life/interfaces/http/story_run_lite_app.py` (separate loopback demo app; preserve Rev37 app/catalog)
- `backend/tools/run_story_run_lite.py` (requires explicit goal-owned disposable DB name/owner; binds loopback)

### Focused tests

- `backend/tests/unit/test_story_run_lite_domain.py`
- `backend/tests/unit/test_story_run_lite_image_worker.py`
- `backend/tests/unit/test_story_run_lite_photo_bridge.py`
- `backend/tests/contract/test_story_run_lite_api.py`
- `backend/tests/integration/test_story_run_lite_postgres.py`
- `backend/tests/integration/test_story_run_lite_loopback.py`

### Project records and evidence

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` (append only; preserve the pre-existing local text)
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md` (append only; preserve the pre-existing local text)
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (append this approval only)
- `features/FEAT-063-system-architecture-rearchitecture/evidence/STORYRUN_LITE_S1_S2_ENVIRONMENT_20261102.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/STORYRUN_LITE_S1_CHECKPOINT_20261102.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/STORYRUN_LITE_S2_READINESS_20261102.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/STORYRUN_LITE_S1_S2_FINAL_20261102.md`
- `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_20261102/files.txt`
- `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_20261102/hashes.csv`
- `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_20261102/diff.patch`

## Tasks, dependencies and acceptance

| Task | Stage | Acceptance |
|---|---|---|
| SL-0 | Baseline | Pinned hashes, branch/HEAD/index and all pre-existing Git-visible local file hashes recorded; no protected file changed. |
| SL-1 | S1 | Contract JSON plus Bruno artifacts define the 10 operations, limits, errors, idempotency, ETag/revision and cancel/UNKNOWN behavior before backend implementation. |
| SL-2 | S1 | Additive DTR amendment names both receipt authorities and updates ownership, counts, relationships, integrity/indexes and crosswalk consistently; migration adds bounded owner-scoped Core upload/asset lineage and Story run/result/decision/receipt tables. |
| SL-3 | S1 | Upload uses contiguous 1–5 parts, server per-part/aggregate hashes and an immutable bounded snapshot; quarantine/scanner/decoder fail closed; exact replay and part conflict behavior are durable. |
| SL-4 | S1 | Story create/attach/get/confirm/cancel persists expected revisions, active-owner serialization, command receipts, exact replay, `202` confirmation, stale `409`, and cancel/late-result CAS semantics. Fake Vision is explicitly fake. |
| SL-5 | S1 gate | Focused domain/API tests and goal-owned PostgreSQL migration/transaction tests pass where runnable; S1 checkpoint records scanner and worker as VERIFIED or NOT VERIFIED. Then proceed directly to S2 without review pause. |
| SL-6 | S2 | Typed photo binding calls the V2-compatible adapter only through A1 ledger/guard/transport; only HTTP loopback is allowed. Valid Story result receipt/revision commits before ledger terminalization; no retry after SENT/UNKNOWN. |
| SL-7 | S2 | Loopback tests cover one-send success, guard denial zero-send, same-tuple race ≤1, post-SENT failure/invalid response UNKNOWN, receipt-before-finalize, cancel/stale CAS, and A1 canvas default regression. |
| SL-8 | S2 handoff | OpenAPI/Bruno match runtime; synthetic JPEG/PNG/WebP with distinct content/hash are evidenced; tests/lints/validators are recorded honestly; final snapshot verifies every initial local-change hash is preserved. |

S1 acceptance includes exact one/two/five-part coverage; 20,971,520/20,971,521 byte and 40 MP bounds; malformed/unsupported/multi-frame/decoder failure zero dispatch; scanner stub CLEAN/INFECTED/ERROR/timeout/unavailable branches; legacy organization reads/updates, new legacy-shaped writes blocked, Parent typed scope; Core/Story crash windows with stable receipt replay and no redispatch; full `SUBJECT_REVIEW → CONFIRM 202 → PREPARATION_REVIEW` replay and stale revision 409. Use generated bytes only at upload-boundary tests; never feed limit-only payloads to decoders/model code.

S2 acceptance is offline loopback only: success one send; refusals zero; same tuple race at most one; no resend after SENT, timeout/reset/3xx/5xx/401/malformed V2; separate raw-body and canonical-result hashes; cancel/late result cannot advance run head; default A1 canvas behavior remains unchanged. Q3-B+ remains process-scoped and may allow overlap across distinct runs; no provider-wide quota, global zero-send or cancellation-of-provider claim is made.

## Verification, data and stop rules

- Generate only synthetic fixtures and record generator/provenance, dimensions, media type, distinct SHA-256 and inspection method. They are test/demo inputs, never a product hash allowlist.
- ClamAV is required before any parser/decoder or Vision dispatch. A stub is test-only and never yields a real CLEAN verdict. If a real local compatible scanner cannot be verified, affected readiness is NOT VERIFIED.
- Run image metadata/probe/decode/orientation/color normalization in a killable worker. Windows Job Object or a demonstrably capped container is required; verify process kill and OS-enforced memory/CPU limits with measurements on supported large synthetic input. Docker is currently unavailable, so Job Object is the intended path; if enforcement cannot be proven, mark readiness FAIL/NOT VERIFIED.
- PostgreSQL may be used only after this session creates a unique `storyrun_lite_*` database on loopback and verifies its owner. Set the migration/test URL to that database only. Record create, owner verification, migration heads, test result and cleanup; drop only that exact verified goal-owned database. Do not inspect, connect to, migrate, use, or clean A2 DBs or any pre-existing application DB.
- Never use Modal, GPU, remote provider, external inference, real child data, Teacher/UI/story-video, or A2/B1/B2; do not stage, commit, push, merge, deploy, reset, checkout, clean, or stash.
- Run focused tests and the project harness/security/architecture validators plus `git diff --check` as required by the pinned plan. Fix only regressions caused by this goal; record unrelated baseline failures without modifying A2.
- If any required file falls outside the allowlist, amend this plan and append a scoped authorization before changing that file. At S1 and S2, save a checkpoint and exact resume state; at final, report each gate as PASS/FAIL/NOT VERIFIED/NOT RUN.


## Owner-approved SL-0/SL-8 roadmap rebaseline amendment — 2026-11-02

- Owner disposition: the owner explicitly selected **B — Rebaseline 875** in this thread after reviewing the provenance report.
- Acceptance exception: use the exact current roadmap bytes with SHA-256 `875E93C59085DA9C38923DB85EEE50D15945CBD38EC27EC0B6389B93B3ECB8D4` as the accepted baseline for this one pre-existing local path for SL-0/SL-8 only.
- Preserve the original manifest and its captured `B88188B846C62FF086AB067DB7EC7F9678967847D43BED9598274387E2B93A07` unchanged. This decision does not claim that the original bytes were preserved and does not authorize editing/restoring the roadmap contents.
- Record SL-0 and SL-8 as PASS only with the explicit owner-approved rebaseline exception. Keep the 79 byte-identical paths, three approved FEAT-063 append-only paths and 35/35 protected FEAT-061/FEAT-064 paths separately enumerated; do not merge these categories into a claim that all original hashes match.
- The previous S1→S2 snapshot remains immutable. Capture the post-decision state additively at `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REBASELINE_20261102/`.
- Scope is documentation and local snapshot only. The roadmap, implementation source, tests, migrations, A2 and FEAT-061/FEAT-064 contents remain untouched by this amendment. No database/provider operation or Git index/commit operation is authorized.

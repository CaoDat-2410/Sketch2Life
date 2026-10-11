# FEAT-018 P2-T2 offline checkpoint — public status summary

- Evidence ID: `EV-018-P2T2-PUBLICATION-OFFLINE-STATUS-20261011`
- Type: derived public summary (review/decision record).
- Related task: FEAT-018 Person 2 Task 2 (P2-T2), offline Lightning development work.
- Date: 2026-10-11 (Asia/Saigon). Recorder: Claude Code session acting for Person 2.
- Publication authority, owner decisions and fresh verification:
  [FEAT-043 offline publication](../../../FEAT-043-feat018-p2t2-offline-publication/evidence/README.md).

This note is a **derived summary**. It does not replace, re-pin or edit any original record.
The originals it summarizes stay local because they contain machine locators, attachment paths
or protected approval history. They are cited below by repository-relative path, size and
SHA-256 only and are **not available on the remote**. Nothing here turns a historical `FAIL` or
`NEEDS_REMEDIATION` into a `PASS`.

## 1. What this checkpoint publishes

| Commit | Subject | Content |
|---|---|---|
| `cab2d72` | `fix(security): guard repository text reads and declare exclusions` | `tools/validate_repository_security.py`; `backend/tests/unit/test_repository_security_validator.py` |
| `e85d2c7` | `feat(feat018): add offline binding and execution contracts` | `contracts/schemas/feat018_live_binding.py`, `benchmark/feat018_live_lightning_execution.py`, `benchmark/feat018_live_lightning_binding.py` and their two tests |
| `d94e1a8` | `feat(feat018): add preflight and runtime observations` | `contracts/schemas/feat018_live_wiring.py`, `benchmark/feat018_live_preflight.py`, `benchmark/feat018_live_session_checks.py` and their three tests |
| `c3b941a` | `feat(feat018): add guarded SSH development attempt` | `infrastructure/ai/feat018_lightning_ssh.py`, `interfaces/cli/feat018_lightning_dev_attempt.py` and their two tests |
| (this commit) | `docs(feat018): publish offline checkpoint and remaining gates` | `plan/P2_T2_LIGHTNING_DEV_ATTEMPT_PLAN_20261006.md`, this summary, the evidence-index entry and the FEAT-043 records |

Sources are under `backend/src/sketch2life/`, tests under `backend/tests/unit/`. Each published
file is byte-identical to its selected local original. None of the 18 originals contains CRLF,
so the Git blob content equals the raw bytes and the raw SHA-256 values below apply unchanged.

## 2. Status that remains in force

- **Offline only.** Public host/session/CLI entries deny real effects. No live run, Studio,
  account, SSH, provider, model, GPU or service-network action is authorized or was performed.
- **D1/D11 unresolved. D6 not finally resolved. Stage 4 NOT READY. Live entry NOT_AUTHORIZED.**
  The reviewed runtime binding and the live-plan `CURRENT` section are unchanged.
- **Repository security.** On exit 0 the scanner prints
  `REPOSITORY_SECURITY_VALID_WITH_DECLARED_CONTENT_EXCLUSIONS` and
  `mandatory_gate=NOT_ESTABLISHED_WITHOUT_OWNER_SEMANTICS_ACCEPTANCE`. Person 2's acceptance of
  those exclusion semantics is recorded in FEAT-043 (decision A). It covers only the five
  checkpoint commit trees: exactly 231 listed baseline files plus 8 empty FEAT-043 `.gitkeep`
  files. It is not a general security PASS and closes neither Security S3, C1–C7 nor any live
  gate. Five baseline binaries (2 `.png`, 2 `.wav`, 1 `.jar`) were not content-checked.
- **Residual (Medium, unfixed).** Malformed JSON passed to the direct upstream
  `TypeAdapter.validate_json()` path reproduces a disclosed residual. Untrusted JSON must use the
  protected `model_validate_json()` ingress, and integrations using the direct path require
  reassessment before use.
- **POSIX UNVERIFIED.** Four POSIX-only tests skip on Windows: process-group signal escalation and
  three raw AF_UNIX frame cases. No POSIX run exists.
- The old repository-security runner remains `ABANDONED / STOP / NOT FROZEN`.

## 3. Historical records (not re-run here)

| Record (local, not published) | Bytes | SHA-256 | Outcome as recorded |
|---|---:|---|---|
| `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_OFFLINE_BINDING_SNAPSHOT_OWNER_ACCEPTANCE_20261006.md` | 3471 | `cef7847f57ef7d20ac5cfa4b112eda925443ea27abe772e34f90fd88ce7f41dd` | 2026-10-06 owner risk acceptance of an exact five-file snapshot, OFFLINE WITH A DISCLOSED MEDIUM RESIDUAL. Historical `NEEDS_REMEDIATION` preserved; reported 1104 passed / 4 POSIX skips (historical). |
| `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_LIGHTNING_DEV_ATTEMPT_OFFLINE_20261006.md` | 37949 | `764da186e71d1984117c2c70a4d04fc1c53d05f52e036aeaf97c3ccf7ff84296` | A-OFFLINE-R1/R2/R3 author runs (1487/4, 1502/4, 1523/4). Supplied independent R3 review `PASS_SCOPED_OFFLINE` (reviewer identity UNKNOWN). On 2026-10-07 Person 2 accepted the exact eight R3 tuples only within `PASS_SCOPED_OFFLINE`, retaining I1–I6 and the Medium residual. |
| `tmp/feat018-p2t2-dlane-w1r3-review-20261009/REVIEW.md` | 25231 | `04bb15d6c3a47eaa4bdaa072b8fd4a42826a4e94838cbc188e76bf2a8912d27e` | A-LIVE-W1 (commit-3 files) static independent re-review: `PASS WITH LIMITATIONS` (0 Blocking/Moderate/Low, 3 Info). Static only. Person 2 accepted it as the W1 review gate; the W1 approval record is deferred under the FEAT-018 approval-write hold. |

Historical acceptances remain bound to their historical bytes. How they relate to the published
files:

- **Eight R3 files: accepted exactly as published** (2026-10-07, `PASS_SCOPED_OFFLINE`):

| File | Bytes | SHA-256 |
|---|---:|---|
| `contracts/schemas/feat018_live_binding.py` | 61618 | `a47f7b118a9bdc94f8a2e9bcd9af586db7f2f1d7b277d90f7ad7c8c71249d41a` |
| `benchmark/feat018_live_lightning_execution.py` | 388646 | `b4fed9b4721669d6c308aaf48fe3f6edbf055d41b6ab952fbcb32ba67bf16555` |
| `infrastructure/ai/feat018_lightning_ssh.py` | 33493 | `f7a807b87f0aa80cc18282525e1e766910c86b7a0b45a39f23388d4f12e006bc` |
| `interfaces/cli/feat018_lightning_dev_attempt.py` | 60778 | `bee746126b5e3d8bfd0bac3bd019b01ad8ebf999c98687fdc4ebdad4ab4b2c09` |
| `tests/unit/test_feat018_live_lightning_binding.py` | 136297 | `9ffbda6f4af66bfb2c2e9c035e019eef406ef6c0bb0ca96e7e33caba9ba8acaa` |
| `tests/unit/test_feat018_live_lightning_execution.py` | 403868 | `7f5c981b557e03e18d1fad84722fd35339af78d073cc46f9310d727ff5a97189` |
| `tests/unit/test_feat018_lightning_ssh.py` | 36834 | `35a95187d5cb185094f6a73b424d74b462ee125ee214a3d5289d0f6af11b4745` |
| `tests/unit/test_feat018_lightning_dev_attempt.py` | 67582 | `245f8d9199a929ca13f2a06f98936218f189d704551a7077cad596c861c99c65` |

- **Binding wrapper: unchanged, under the separate five-file acceptance.**
  `benchmark/feat018_live_lightning_binding.py` (25943 bytes,
  `682598aa1d43d28152f831084e52454191edf888ce368bd1592869594c77f6ca`) is not one of the eight
  R3 tuples. It is the one file of the 2026-10-06 five-file snapshot whose bytes are unchanged.
  The other four snapshot files changed afterwards, so that acceptance does not extend to them.
- **Commit-3 (W1) files: static review gate only, no byte acceptance recorded.**

| File | Bytes | SHA-256 |
|---|---:|---|
| `contracts/schemas/feat018_live_wiring.py` | 14247 | `8e342f1a9043182cdbdd4a2910608173d178b2f423f51037339ac2ffec293cd9` |
| `benchmark/feat018_live_preflight.py` | 14741 | `3f91925a2511dda40e337b9fadb2a64238bf00d9ff052f4767ba9cfae8bbb814` |
| `benchmark/feat018_live_session_checks.py` | 17421 | `0d7629585f78d64c5a627ce79ee92009be746ff8dff6622f488039ce735c5d2e` |
| `tests/unit/test_feat018_live_wiring_contracts.py` | 16026 | `d54216e087d3bc87c9ae8fa695c673f87448a9aa0b13251aee43bb40bfdac0e7` |
| `tests/unit/test_feat018_live_preflight.py` | 21866 | `0f39ec9b44eea0a1440a0554c7d6e0785341c4bd3230660f2dafb5674b3a95c7` |
| `tests/unit/test_feat018_live_session_checks.py` | 17662 | `7a16ee8cc43f8983663922436c04e403d32754a4ded0726c398bcd102ee92f38` |

- **Commit-1 scanner pair: no historical review PASS applies.** These identities
  (`tools/validate_repository_security.py` 24792 bytes
  `4c8733f65cf507c6c3276d03ad8bd530e982839d75605d72e292d4f1520cfb5c`;
  `backend/tests/unit/test_repository_security_validator.py` 39828 bytes
  `a202c01969cfdc686c62efda0dae28922381a279216ff8d8b2ec30188bb8478e`) received a fresh,
  non-independent review recorded in FEAT-043.

## 4. Fresh verification for this publication (2026-10-11)

These checks ran on each exact intermediate tree (baseline `44af2e4` plus only the commits up to
that point). The four code commits have exactly the verified tree IDs. Environment: Windows,
Python 3.12.10, pytest 8.4.2, Ruff 0.16.4, mypy 1.20.2. Bytecode and pytest cache were disabled,
temporary fixtures were private, and project imports were pinned to the tree under test (an
origin guard counted 0 modules loaded from elsewhere). Synthetic/fake I/O only.

| After commit | Targeted tests | Scanner (exit, paths) |
|---|---|---|
| `cab2d72` | scanner suite: 22 passed, 1 skipped (Windows symlink privilege) | 0, 1037 |
| `e85d2c7` | binding, execution, Qwen ×4, Raw, Raw contract: 1330 passed, 4 POSIX skips | 0, 1040 |
| `d94e1a8` | + wiring/preflight/session: 1499 passed, 5 skipped (4 POSIX, 1 symlink privilege) | 0, 1046 |
| `c3b941a` | all 13 suites: 1692 passed, 5 skipped | 0, 1050 |

The `c3b941a` targeted result equals the historical R3 ten-suite figure (1523/4) plus the W1
author figure (169/1), now reproduced on the published bytes. These are new results; they are
not independent reviews and do not replace the historical numbers in section 3.

Full backend suite on the `c3b941a` tree: **3138 passed, 12 skipped, 9 failed**. All 9
failures are baseline:
- the same nine test names in `test_vision_v3_quality_benchmark.py` and
  `test_vision_v3_quality_execution.py` fail on the untouched baseline;
- they fail with the same cause there:
  `V3QualityFixtureIntegrityError: Phase 8 fixture.image_ref must resolve inside the package`.

No other failure occurred.

Checks recorded as **FAIL** and kept under owner publication exceptions (FEAT-043):

- `tools/validate_architecture.py` (decision B1): the unchanged baseline finding
  `application/services/backend_ai_workflow.py imports an outer layer`. FEAT-020 handles the fix
  separately.
- Ruff and mypy with the backend configuration (decision C1). Whole-backend Ruff reports 550
  findings, 547 of them new in the commit-2 and commit-4 files (520 line-length). mypy strict
  reports 115 errors, 112 of them new in the schema, execution, SSH and CLI modules. The
  commit-3 files add none. Spot checks of selected clusters found no runtime defect; this is
  not a claim that every finding is a false positive. Fixing them changes accepted bytes and
  needs its own identity, review and acceptance.

## 5. Not published in this checkpoint

`CONTEXT.md`, `DECISIONS.md`, `approvals/TASK_APPROVAL.md` and the live execution plan keep their
local uncommitted changes (mixed D6/offline content; protected approval history under an
approval-write hold). D6/C01 rebind material, security preparation/trace history, the two
acceptance originals, the PUB-P1 draft plan and its inventory stay local. Publishing any of them
needs a separate selection and review.

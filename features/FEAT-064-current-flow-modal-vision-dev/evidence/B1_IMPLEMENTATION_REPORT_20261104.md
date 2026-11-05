# FEAT-064 GOAL B1 — implementation report

- **State:** `B1 XONG-CHƯA REVIEW`. This is an implementation handoff, not independent acceptance.
- **Authority:** owner launch for `CHAIN_B1_REV2_PLAN_20261103.md`; plan SHA-256 `BAA53AC8DB529107C3C9EB340FE2C900251535AB0D183209C157B6F4082A62B4`; V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- **Execution base:** branch `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`, empty index. Baseline snapshot: `.claude/handoff/snapshots/GB1_BASE_20261103T225233/manifest.json` (91 dirty paths; B1 approval pins this snapshot).

## B1 delta from the approved baseline

New files:

- `backend/src/sketch2life/infrastructure/vision_analysis/analysis_only.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/pilot_queue.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py`
- `backend/tests/unit/test_assistance_analysis_only_b1.py`
- `backend/tests/unit/test_pilot_queue_composition_b1.py`

Modified files:

- `backend/src/sketch2life/interfaces/http/be1_runtime.py`: adds `pilot_vision` defaulting to `None`; the factory is called only with an engine, an injected factory, local/test environment, and the synthetic pilot flag enabled.
- `backend/tests/contract/test_app_composition.py`: adds the default-off assertion. Its unrelated route-surface changes were already present in the baseline and were preserved.

`assistance.py`, `domain/assistance.py`, `ports/assistance.py`, and A2's `be1_canvas_source_adapter.py` are byte-identical to the B1 baseline; the last is reused read-only.

## Acceptance evidence

- Analysis-only blocks Sketch intent/request, cache write, and the second event while preserving `hand_off`. It binds the A2 source export and verified receipt to the complete analysis bindings and rejects a foreign organization.
- T8 composition is a separate, default-off pilot using BE1 authorization/eligibility, its own bounded in-process queue, one-attempt policy, repository, guard, and worker. Audit, artifact, capability, and ID in-memory adapters are explicitly named `PILOT_FAKE_*`; these remain non-durable pilot dependencies. The guard must reach `SUCCEEDED` before successful output is accepted.
- The focused tests cover analysis-only/source binding, bounded FIFO/default-off wiring, invalid scope, current synthetic eligibility and digest matching, guarded result acceptance, and local synthetic runtime gating. All focused checks below used synthetic fixtures; no production or live provider call was made.

## Verification — actual commands and results

| Check | Command / scope | Result |
|---|---|---|
| Analysis-only unit | `backend\.venv\Scripts\python.exe -m pytest -o addopts= -q --tb=no backend/tests/unit/test_assistance_analysis_only_b1.py` | `3 passed in 0.32s`, exit 0 |
| Queue/composition unit | `backend\.venv\Scripts\python.exe -m pytest -o addopts= -q --tb=no backend/tests/unit/test_pilot_queue_composition_b1.py` | `8 passed in 0.81s`, exit 0 |
| Default-off app contract | `python -c` injected `Settings(env='test', _env_file=None)` and no database URL, then ran `test_compatibility_app_keeps_be1_and_demo_services_on_app_state` with `-o addopts= -q --tb=no` | `1 passed, 1 warning in 2.64s`, exit 0; warning was pytest's already-imported `anyio` assert-rewrite warning |
| Pinned offline regression + three add-ons | Launch: `backend\.venv\Scripts\python.exe .claude\handoff\snapshots\GB1_20261104T003700\run_offline_with_b1_addons.py .claude\handoff\snapshots\GB1_20261104T003700\offline_check.py`. Effective arguments and exact output: `.claude/handoff/snapshots/GB1_20261104T003700/offline-latest.txt`. Runner SHA-256 `3A714AB27A926672B7C65A35A17CE0F312E46C914AFFA08C806CFC19E4D184B9`. | 19 pinned GA2 modules plus `test_canvas_render_limits_ga1.py`, `test_pilot_vision_persistence_ga1.py`, `test_invocation_guard_transport_ga1.py`: `460 passed in 20.12s`, exit 0 |
| Ruff lint | `ruff check --no-cache --config backend/pyproject.toml` on the seven B1 source/test paths | `All checks passed!`, exit 0 |
| Ruff format | `ruff format --check --no-cache --config backend/pyproject.toml` on the six B1 source/unit-test paths, excluding the contract file's inherited formatting | `6 files already formatted`, exit 0 |
| Ruff format inherited contract file | Same format check on current `test_app_composition.py` and its baseline snapshot copy | Both exit 1 with the same one pre-existing comprehension reformat; outputs matched. No unrelated formatting change was made. |
| Strict mypy | `mypy --config-file backend/pyproject.toml --strict --no-incremental --cache-dir backend/.mypy_cache_gb1` on the seven B1 source/test paths | `Success: no issues found in 7 source files`, exit 0 |
| Repository validators | `python tools/validate_harness.py`; `python tools/validate_repository_security.py`; `python tools/validate_architecture.py` | `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (6402 publishable files scanned); `ARCHITECTURE_VALID`, all exit 0 |
| Diff whitespace | `git diff --check` | Exit 0; Git emitted only CRLF-to-LF working-copy notices for existing dirty documents. |

## B1 file hashes

| Path | SHA-256 |
|---|---|
| `backend/src/sketch2life/infrastructure/vision_analysis/analysis_only.py` | `7E26FEE161D053EC70F2B834F7C47F01A2FB125922E4F8EB857682B1B3235AFE` |
| `backend/src/sketch2life/infrastructure/vision_analysis/pilot_queue.py` | `105B24CB9591907FE7DC5BA6BE1640F2795ADF999B05141711CEFE931D2C3CF2` |
| `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py` | `D6731A9221DA65712BC9CC7AE79A441E398D72A1813810010AC7FFA878886E09` |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py` | `A74B5885A2B7B5B430D4D76D61E437FBA6DD686F8B8AC388118BFF7DD86067AA` |
| `backend/tests/unit/test_assistance_analysis_only_b1.py` | `A634C42ECDEB169B7DB8FD8690E8A0A98E399628DB42050ACA58669AF1DA5680` |
| `backend/tests/unit/test_pilot_queue_composition_b1.py` | `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4` |
| `backend/tests/contract/test_app_composition.py` | `7717BD672F98D413E5489855F58A13BF453BF6366905FA785BD116250A5A5207` |

## Limits and next gate

- PostgreSQL, Alembic, Modal, GPU, provider calls, external network, T9, T12, T13, and B2 were not run or started.
- The queue and fake audit/artifact/capability/ID adapters are process-local and non-durable; a process loss can lose queued pilot work. This is not production readiness or a live-provider quality claim.
- Independent review is still required. Stop here at `B1 XONG-CHƯA REVIEW`; B2 requires a separate owner launch after independent `ACCEPTED`.

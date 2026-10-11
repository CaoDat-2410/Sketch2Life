# Publication verification — FEAT-018 P2-T2 offline checkpoint (2026-10-11)

- Evidence ID: `EV-043-PUBLICATION-VERIFICATION-20261011`
- Type: test, review and decision evidence. Related: AC-043-01 to AC-043-06.
- Performed by: a Claude Code session acting for Person 2. This is not an independent review.
- Environment: Windows (win32), Python 3.12.10, pytest 8.4.2, Ruff 0.16.4, mypy 1.20.2; the
  existing backend virtual environment.
- Run settings: `-B`, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, `-o addopts=''`;
  private TEMP and basetemp outside the repository.
- Import pinning: `PYTHONPATH`/`MYPYPATH` pointed at the tree under test. A local pytest plugin
  (origin guard) failed the run if any `sketch2life`/`tools` module loaded from outside that
  tree. Every run reported 0 outside.
- Actions excluded: no SSH, Studio, provider, model, GPU or network action.

Local logs and helper scripts stay in the operator's session workspace and are not published.

## 1. Identities checked before execution

- All 76 PUB-P1 inventory files matched (size, raw SHA-256, CRLF count, LF projection; 0
  mismatches), both at preparation and again at 2026-10-11T05:38:43Z.
- The scanner and the exclusion list (`../metrics/SCANNER_EXCLUSIONS_T1_T4.tsv`, SHA-256
  `a40f8fed3f693462481d82ce69bccdc8814e5d28681ce6db38582fc4c2468c02`) matched the owner-approved
  values.
- The remote tip equalled baseline `44af2e4f9a75064df327496f033c75f9fe0d0f5d`.

## 2. Commits 1–4: actual trees equal the freshly verified intermediate trees

The commits were built in a separate publication worktree on the local branch
`publication/feat018-p2t2-offline-20261011`.

Gates for each commit:

- each file copied byte-for-byte with a hash check;
- only the planned paths staged, with no residue;
- `git diff --cached --check` clean;
- `git write-tree` equal to the tree verified earlier on an exact intermediate tree;
- scanner exit 0 immediately before the commit;
- exclusion rows identical to the approved list.

| Commit | Tree | Staged | Import closure | Scanner paths (scanned text) | Targeted suites |
|---|---|---:|---|---|---|
| `cab2d72aa88dca184028dcfd2ac02dd950a69aba` | `4ad83a8e997f99fee8f0c83ef6d45363a753dbe8` | 2 | 402 imports / 0 problems | 1037 (806) | scanner suite from repo root: 22 passed, 1 skipped (symlink privilege) |
| `e85d2c780bef95449d55de717c3c231a8e5d3761` | `4edb9badf605b378708b485cfe2d462d92b38604` | 7 | 446 / 0 | 1040 (809) | 8 suites: 1330 passed, 4 POSIX skips |
| `d94e1a817d61c46162eac86b5473cfabf8cb8600` | `421a80eda4ea5b5172dddd4aa04be354b2fa0de4` | 13 | 475 / 0 | 1046 (815) | 11 suites: 1499 passed, 5 skipped |
| `c3b941a67c2592750f889ec11b52b1241c700fa3` | `402328cdfa656abb1c85b37e4824ef7d3ac4c7ae` | 17 | 490 / 0 | 1050 (819) | 13 suites: 1692 passed, 5 skipped |

On every tree:

- the scanner printed `REPOSITORY_SECURITY_VALID_WITH_DECLARED_CONTENT_EXCLUSIONS` and
  `mandatory_gate=NOT_ESTABLISHED_WITHOUT_OWNER_SEMANTICS_ACCEPTANCE`;
- the exclusion count was 16 images and 215 non-allowlisted, with 0 symlink, non-regular,
  forbidden-path or read-failure counts;
- the harness and skeleton validators passed;
- full collection from the repository root succeeded (1920 / 2796 / 2966 / 3159 tests).

The import closure is a static AST check, function-level imports included. Neither commit 2
nor commit 3 references a later group's module. The binding wrapper's six imports
(`D11OfflineConfig`, `LightningAdapterDispatchV1`, `LightningResourceObserverV1`,
`LightningSessionControllerV1`, `_validate_terminal_publication_privacy`,
`run_offline_live_smoke`) exist only in the new execution module, which is why they ship
together.

Suites used:

- Commit 2: `test_feat018_live_lightning_binding`, `test_feat018_live_lightning_execution`,
  `test_qwen_vision_adapter`, `test_qwen_vision_runtime_config`,
  `test_qwen_vision_environment_readiness`, `test_qwen_vision_schema_path_diagnostic`,
  `test_raw_understanding` and `tests/contract/test_raw_understanding_contract`.
- Commit 3 adds `test_feat018_live_wiring_contracts`, `test_feat018_live_preflight` and
  `test_feat018_live_session_checks`.
- Commit 4 adds `test_feat018_lightning_ssh` and `test_feat018_lightning_dev_attempt`.

Skips:

- 4 POSIX-only skips in `test_feat018_live_lightning_execution.py`: line 2156, line 8659 (×2)
  and line 8682;
- 1 skip in `test_feat018_live_session_checks.py:374` (symbolic links unavailable to the test
  process).

Full backend suite on tree `402328cd` (repository root; `SKETCH2LIFE_RUN_REAL_AI_E2E` unset, so
the real-AI e2e test skips): **3138 passed, 12 skipped, 9 failed**. The nine failures are:

- `test_vision_v3_quality_benchmark.py::test_schema_failures_cannot_produce_quality_ready`
- `::test_forged_equal_experiment_identity_cannot_produce_quality_ready`
- `::test_wrong_or_reordered_fixture_identity_cannot_produce_quality_ready[reordered]`
- `::test_wrong_or_reordered_fixture_identity_cannot_produce_quality_ready[wrong_hash]`
- `::test_ambiguous_overprediction_fails_explicit_upper_bound`
- `::test_fake_quality_pass_is_cleaned_and_serializes_only_safe_values`
- `::test_raw_output_hook_is_required_and_scratch_is_cleaned`
- `::test_two_fake_passes_produce_quality_verdict_only`
- `test_vision_v3_quality_execution.py::test_no_gpu_pair_uses_qwen_mapping_and_returns_safe_quality_report`

All nine failed with `V3QualityFixtureIntegrityError: Phase 8 fixture.image_ref must resolve
inside the package`. The same two files run on the untouched baseline fail with the same nine
names and the same cause, so they are attributed to the baseline (decision C1). No other
failure occurred.

## 3. Checks kept as FAIL under owner exceptions

| Check | Baseline `44af2e4` | Commit 4 tree | Owner decision |
|---|---|---|---|
| `tools/validate_architecture.py` | FAIL: `application/services/backend_ai_workflow.py` imports an outer layer | identical | B1. A prepared minimal fix (port + adapter) passed locally but is not included; FEAT-020 owns it. |
| Ruff, backend config, whole backend | 3 findings | 550 (547 new: 520 E501, 8 I001, 6 SIM105, 6 B009, 2 F401, 2 B905, 1 UP047, 1 UP035, 1 E731) | C1 |
| mypy strict, backend config | 3 errors / 2 files | 115 errors / 6 files (112 new) | C1 |

The new Ruff findings by file:

| File | New findings |
|---|---:|
| `test_feat018_live_lightning_binding.py` | 138 |
| `feat018_live_lightning_execution.py` | 105 |
| `test_feat018_live_lightning_execution.py` | 99 |
| `test_feat018_lightning_dev_attempt.py` | 68 |
| `feat018_live_binding.py` | 67 |
| `feat018_lightning_dev_attempt.py` | 51 |
| `feat018_lightning_ssh.py` | 9 |
| `test_feat018_lightning_ssh.py` | 7 |
| `feat018_live_lightning_binding.py` | 3 |

The new mypy errors by file:

| File | New errors |
|---|---:|
| `feat018_live_binding.py` | 50 |
| `feat018_live_lightning_execution.py` | 40 |
| `feat018_lightning_dev_attempt.py` | 12 |
| `feat018_lightning_ssh.py` | 10 |

The commit-3 files add none. The scanner file in `tools/` is outside these backend-wide runs.
The two-path Ruff and strict mypy checks of the scanner pair pass; a forced backend-config Ruff
run on the scanner flags one E501.

The main mypy root causes are:

- the runtime-computed pydantic metaclass;
- `*args/**kwargs: object` forwarding wrappers;
- POSIX- or Windows-only stdlib attributes;
- `Literal[float]`;
- narrowing performed through `getattr` or separate variables.

Spot checks of selected clusters found false positives rather than runtime defects:

- reuse of a deleted `except ... as error` name;
- `preflight`/`finalizer` guarded by `callable(getattr(...))`;
- narrowing through `live_result`.

This does not show that every finding is a false positive.

## 4. Exclusions accepted for this checkpoint (decision A)

The 231 baseline rows in `../metrics/SCANNER_EXCLUSIONS_T1_T4.tsv` were identical in every tree.
Each row is the same blob as at the remote tip `44af2e4`. Breakdown:

- 14 `.svg`
- 2 `.png`
- 2 `.wav`
- 1 `.ipynb`
- 1 `.jar`
- 211 `.gitkeep` (193 zero-byte, 18 one-byte)

The **five baseline binaries were not content-checked by the scanner**:

- `features/FEAT-017-live-ai-dev-integration/evidence/screenshots/android-emulator-ui-20260907.png`
- `features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png`
- `features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/media/narration.wav`
- `features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav`
- `apps/mobile/android/gradle/wrapper/gradle-wrapper.jar`

Commit 5 adds exactly these 8 zero-byte template placeholders:

- `features/FEAT-043-feat018-p2t2-offline-publication/assets/applied/.gitkeep`
- `features/FEAT-043-feat018-p2t2-offline-publication/assets/approved/.gitkeep`
- `features/FEAT-043-feat018-p2t2-offline-publication/assets/generated/.gitkeep`
- `features/FEAT-043-feat018-p2t2-offline-publication/evidence/metrics/.gitkeep`
- `features/FEAT-043-feat018-p2t2-offline-publication/evidence/notes/.gitkeep`
- `features/FEAT-043-feat018-p2t2-offline-publication/evidence/raw/.gitkeep`
- `features/FEAT-043-feat018-p2t2-offline-publication/evidence/screenshots/.gitkeep`
- `features/FEAT-043-feat018-p2t2-offline-publication/src/.gitkeep`

## 5. Commit 5 checks on the final documentation tree

Run on the final commit-5 index and worktree, after every document was added (parent
`c3b941a6`). Commit 5 changes only `features/` paths: 20 files. No source, test, tool or
configuration path changes, so the commit-4 test, Ruff and mypy results above apply unchanged.

| Check | Result |
|---|---|
| Staged set | 20 paths: the selected plan original (18563 bytes, `4cf64c9f…e76b`), the derived summary, the FEAT-018 evidence-index entry and 17 FEAT-043 files; no residue |
| `git diff --check`, `git diff --cached --check` (vs parent and vs baseline) | clean |
| `tools/validate_harness.py` | exit 0, `HARNESS_VALID` |
| `tools/validate_repository_security.py` | exit 0: `REPOSITORY_SECURITY_VALID_WITH_DECLARED_CONTENT_EXCLUSIONS`; `mandatory_gate=NOT_ESTABLISHED_WITHOUT_OWNER_SEMANTICS_ACCEPTANCE`; 1069 paths; 830 text content-scanned; 16 image and 223 non-allowlisted skipped; 0 symlink, non-regular, forbidden-path or read-failure |
| Exclusion delta vs the approved 231 | exactly the 8 FEAT-043 `.gitkeep` paths in section 4, each 0 bytes (empty blob `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`) |
| `tools/validate_architecture.py` | exit 1, the unchanged baseline finding only (decision B1) |
| `tools/validate_skeleton.py` | exit 0, `SKELETON_VALID` (new feature folder) |
| Relative links in the 12 new or changed documents | all resolve inside the tree |
| Machine-locator/credential sweep of the same documents | no machine path or credential. The only matches are inside the verbatim owner quote in `approvals/TASK_APPROVAL.md`: the redaction placeholder wording and the quoted `{T4_RESULT}` token |

The scanner exclusion list in `../metrics/SCANNER_EXCLUSIONS_T1_T4.tsv` is byte-identical to the
owner-approved file (SHA-256 `a40f8fed…8c02`).

## 6. Limits

- These are author-side fresh checks, not independent reviews.
- POSIX behaviour remains UNVERIFIED.
- The scanner acceptance is scoped to this checkpoint and is not a repository-security PASS.
- Post-push identities (the commit 5 hash and the remote verification) cannot be inside commit 5.
  They are reported to the owner and kept in a local post-publication record.

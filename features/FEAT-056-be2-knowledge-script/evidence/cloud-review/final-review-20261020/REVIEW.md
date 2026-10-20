# BE2-07 final review — 2026-10-20

**Verdict: PASS.**

- No P0, P1 or P2 is open in the offline scope.
- Every P3 is either fixed with a regression or carries an approved, evidenced disposition.
- All 42 acceptance IDs map to fresh passing JUnit nodes. Each node has a concrete assertion
  and calls real product code.
- Every required check that can run in this environment passed.
- The approved 56-module batch could not run here because dependencies are missing. It is
  NOT_RUN on cloud, and section 4 gives its evidence status.
- No source or test change was needed in this review.

## 1. Identity

| Item | SHA |
|---|---|
| Base (BE2-07 task base) | `23acf9e83e181305edfeb345be9a8e7eb9dbef88` |
| Source `feature/be2-07-knowledge-script` (reviewed HEAD, equals origin) | `763a17cf39bf7343044d69d887597905d55644fd` |
| Target `feature/be2-01-07` at review start (equals origin) | `23acf9e83e181305edfeb345be9a8e7eb9dbef88` |
| Frozen plan revision 1 | `PLAN_REV1_APPROVED.md` SHA256 `6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36` (unchanged) |
| Task approval | `TASK_APPROVAL.md` SHA256 `0010271d9db68dbbe8b9675021540df3e2cd420f636c0f7a8113ea9b91da2078` (unchanged) |

- **Starting state:** the checkout was clean at `f6db0d5`, an ancestor of the source. It was
  moved to `763a17c` with `git merge --ff-only`.
- **New commit since the previous review:** `763a17c` (Codex), docs only. It touches 4 files
  (BE2-07 `CONTEXT.md`, `evidence/README.md`, `status/STATUS.md` and the new
  `CODEX_POST_CLOUD_REREVIEW_20261020.md`). It changes no backend, test or config file.
- **Range reviewed:** the full `23acf9e..763a17c` range, 168 files and 18 commits. The 12
  original publication commits, the N1/N2 follow-up (`f2c59b4`, `9b7a6bc`, `1d731c5`), the R1
  fix (`b3f7573`, `f6db0d5`) and `763a17c`.
- **Hashes:** `source-pins.json` pins the current SHA256 and size of the 16 product
  source/test files and the reference files at `763a17c`.

## 2. Disposition matrix for every earlier finding

| Finding | Disposition | Regression / basis (fresh at 763a17c) |
|---|---|---|
| P2-1 product test froze 572 shared files and the task07 module count | FIX_CONFIRMED | No product test pins shared-file hashes or the profile. Immutability is now an evidence gate (X01/X02). Earlier copy probes: a harmless shared edit leaves 262 passing; an extra module gives 263. Fresh X02 check uses git invariants (section 3) |
| P2-2 imagined-to-fact literal bypass (punctuation, whitespace, Cf, full-width) | FIX_CONFIRMED | Shared `imagined_literal_overlap`, used by the domain, the DTO and the handler. Tests `test_tiny_imagined_literal_variants_cannot_become_facts`, `test_full_basis_record_rejects_tiny_imagined_literal_variants`, `test_imagined_fact_tiny_variants_reject_after_selection_removed` and `test_fact_fragment_of_longer_imagined_literal_rejects_without_writes` pass (N02: 108 nodes) |
| P2-3 no assertion on the requested hash in `resolve_exact` | FIX_CONFIRMED | `test_actual_exact_resolver_rejects_mismatched_requested_pins_without_writes` (hash, unknown id, other bundle id, version). Mutant M07 killed |
| P3-1 six surviving service mutants | FIX_CONFIRMED | M01, M04, M06, M07, M09 and M10 are each killed by assertions on a copy of `763a17c`, with 0 errors (`mutants-summary.json`) |
| P3-2 resubmitted claim re-attributed to the editor | FIX_CONFIRMED | `test_unchanged_claim_resubmission_is_noop_and_mixed_edit_preserves_original_attestor` and `test_unchanged_attested_claim_reuses_trusted_author_but_changed_claim_uses_editor`. Mutants N01 and N02 killed |
| P3-3 mutation pause blocked read/resolve | FIX_CONFIRMED | `test_mutation_only_pause_preserves_current_reads_and_replay_but_denies_new_writes` and `test_mutation_pause_preserves_every_other_current_read_and_exact_guard` (13 families). Mutants N14, N15, N16 and N20 killed |
| P3-4 recall cannot be repaired in place | DISPOSITION_VALID | Frozen plan §9 R01 says "Source recall commit trước finalunit → command/resolve deny". `test_recalled_bundle_requires_new_bundle_with_eligible_sources` passes |
| P3-5 readiness/action mismatch | FIX_CONFIRMED | `test_structural_content_readiness_table`, contract readiness/action tests and `test_story_only_record_and_resolver_return_fact_section_content_action`. Mutants N10–N13 killed |
| P3-6 hygiene | FIX_CONFIRMED, frozen exception kept | H1 comes first in the routing docs. The whitespace audit over 168 changed files reports only `TASK_APPROVAL.md` EOF_BLANK. That is the frozen approval, deliberately preserved and now unchanged (`0010271d…2078`) |
| P3-N1 invisible non-Cf characters; C1/DEL accepted | FIX_CONFIRMED | `test_default_ignorable_literal_obfuscation_is_not_a_fact`, `test_text_controls_include_del_and_c1`, `test_text_controls_allow_line_feed_tab_and_vietnamese_combining_marks`, `test_obfuscated_trusted_imagined_text_cannot_become_fact` and `test_edit_handler_rejects_del_and_c1_without_writes`. Mutants S05, S07 and S08 killed |
| P3-N2 verifier passes under -O | FIX_CONFIRMED | On the historical snapshot (section 3), -O and -OO exit 2 with no success token for valid, wrong-commit and tampered input. Normal mode: valid input exits 0, wrong commit and tampering exit 1 |
| P3-R1 default-ignorable used as a word separator | FIX_CONFIRMED (fixed in `b3f7573`) | `test_default_ignorable_word_separator_is_not_a_fact`, `test_default_ignorable_separator_keeps_token_boundaries`, plus separator cases in the service and contract tests. Mutants S01–S04 killed |
| Observation: S06 (filter before NFKC removed) survives | No finding | Equivalent mutant. The exhaustive probe (4,206 points, 50,472 comparisons) gives identical results. Behaviour is unchanged |

No new finding came out of this review.

## 3. Fresh checks run on `763a17c`

All results below are new executions. `checks.json` gives the commands, exit codes and
hashes. Raw logs are in the ignored `evidence/local/claude-final-review-20261020/`.

**Six BE2-07 modules:** exit 0; **360 collected, 360 passed**, 0 failed, 0 errors, 0 skipped.

**42-ID acceptance matrix** (`acceptance-matrix.json`):

- Every one of the 506 node references (286 unique nodes) in
  `ACCEPTANCE_MAP_BE207_20261020_POST_CLOUD_P3.json` is present in the fresh JUnit and
  passed.
- An AST audit confirmed that each mapped test function has `assert` or `pytest.raises` and
  calls real product code.
- A few functions were flagged by the heuristic and then read manually. They exercise real
  handlers or adapters through helpers (`handler_create`, `build_knowledge_examples`,
  `_assert_full_basis_literal_rejected`) or check pinned digest vectors.
- X01 and X02 are evidence gates with supporting product nodes; both nodes pass. X02 was
  checked freshly with git (next item). X01's combined batch is covered in section 4.

**X02 git invariants (base..source):**

- The backend gained 16 new files and modified no existing backend file.
- Only 4 pre-existing files were modified, append-only with 0 removed lines: `.gitignore`,
  `PROJECT_CONTEXT.md`, `SOURCE_REGISTER.md` and `BE2_EXECUTION_TRACKER.md`.
- Every metrics, notes, plan, approval and artifact file is touched by exactly one commit.
  The exception is `cloud-review/verify_evidence.py` and `EXPORT_PROVENANCE.json`, which the
  approved N2 commit `9b7a6bc` changed.
- The frozen plan and task approval hashes are unchanged.

**Mutants (copies of `763a17c`):** baseline 360/360. 27 mutants, 26 killed by assertions with 0
collection errors; S06 is the equivalent mutant above. The real tree was unchanged afterwards.

**Ruff:** `ruff check` and `ruff format --check` over the 16 task07 files, plus `ruff check` on
the verifier: exit 0 / 0 / 0.

**Strict mypy** (`--strict --no-incremental`) on the 10 task07 source files: exit 0.

**Validators:** harness, architecture, skeleton and repository security: exit 0 each.

**`git diff --check`:**

- Worktree: 0.
- `23acf9e..763a17c`: exit 2. The only item is the frozen `TASK_APPROVAL.md` EOF exception.
- Same range excluding that file: 0.

**Portable verifier:**

- `verify_evidence.py --expected-commit 763a17c…`: exit 1. The historical `f0359c4` product
  pins reject exactly the 5 files that the approved fixes `f2c59b4`/`b3f7573` changed. The 14
  other pins match (`pin-delta.txt`). This behaviour is documented; the old pins were not
  rewritten. `source-pins.json` here pins the final SHA.
- On a temporary detached `f0359c4` checkout with the current verifier and provenance
  overlaid: normal mode exits 0 for valid input (one success token), 1 for a wrong commit and
  1 for a tampered byte. -O and -OO exit 2 with no success token in all three cases. The
  temporary checkout was removed afterwards.

## 4. NOT_RUN / NOT_VERIFIABLE_ON_CLOUD

**Approved 56-module profile** (`OFFLINE_BATCH_PROFILE_POST_CLOUD_P3.json`, 50 + 6): NOT_RUN on
cloud.

- **Cause:** fastapi, sqlalchemy, structlog, boto3, redis, rq, alembic, psycopg, firebase_admin,
  pydantic_settings and httpx are missing, and installs are forbidden.
- **Diagnostic attempt** (not counted as a result): 1,444 passed, 17 failed, 8 collection
  errors. All 25 non-passes come from the missing modules or from FEAT-044 nested-collection
  failures caused by them. No BE2-07 module failed.
- **Latest real execution of this check:** Codex's independent run on `f6db0d5`, whose backend,
  tests and config are byte-identical to `763a17c`: 1,685 collected, 1,682 passed, 3 Pillow
  skips, 0 failures or errors. It is recorded in `CODEX_POST_CLOUD_REREVIEW_20261020.md`. The
  count matches the earlier 1,663 cases plus the 22 R1 regressions. Its receipts are local to
  Codex and are not re-verified here.
- **Plan §10:** after a final batch, documentation-only changes do not require a rerun.

**Other checks:**

- The three Pillow-dependent live-app checks and `test_lightning_vision_v2_server.py`:
  NOT_RUN.
- Runtime, provider, HTTP, DB, Lightning, actual08 adoption and fence, production policy:
  NOT_RUN (out of scope).
- The 572-file baseline manifest and the foreign or external checkout invariants: their
  original inputs are local, so they are NOT_VERIFIABLE_ON_CLOUD. X02 is covered by git
  invariants instead.

**Environment:** Python 3.13.16, unicodedata 15.1.0, pydantic 2.13.5, pytest 9.1.1 and mypy
2.3.1 (both outside the pyproject dev ranges), ruff 0.16.9. Nothing was installed.

## 5. Gate assessment

| Gate | Result |
|---|---|
| No open P0/P1/P2 in the offline scope | PASS |
| No P3 violating acceptance; remaining dispositions approved and evidenced | PASS (P3-4 under R01; P3-6 frozen exception; S06 is not a defect) |
| All 42 IDs matched to real evidence | PASS. 40 product IDs and X02 checked freshly. X01's product node passes freshly; its combined batch rests on Codex's execution over the identical product tree (section 4) |
| Every runnable required check passes, with no historical PASS standing in for a fresh run | PASS. The non-runnable batch is labelled NOT_RUN and not counted as PASS |
| Source SHA and evidence match, tree clean, security validator passes | PASS |
| Source or test changes in this review | None |

Component acceptance, if recorded, covers only KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE. The card stays
IN_PROGRESS / NOT_DONE. Runtime, Lightning, provider, HTTP, DB, actual08 adoption and fence, and
integration gates remain open.

# BE2 publication selection — temporary classification

- Date: 2026-10-15, Asia/Saigon.
- Scope: branch `feature/be2-01-ai-job-foundation`, initial Git status **426 files**.
- User requests a temporary GitHub-versus-local selection; this is not commit/push or Phase B implementation approval.
- Acceptance: all426 original paths classified once; local originals preserved; no staging; Phase A source/approved-plan/approval hashes unchanged; security and relevant documentation checks recorded.
- Initial split: **364 GitHub candidates / 61 local diagnostics / 1 separate Android change**.

| Group | GitHub candidate | Local only | Hold separately |
|---|---:|---:|---:|
| Android wrapper | 0 | 0 | 1 |
| Project context/register | 2 | 0 | 0 |
| Backend source | 14 | 0 | 0 |
| Backend tests | 6 | 0 | 0 |
| Feature plan/governance/runners | 25 | 0 | 0 |
| Feature evidence | 226 | 61 | 0 |
| Synthetic fixtures | 91 | 0 | 0 |

## What belongs in each group

Publish source/tests, synthetic fixtures/manifest/examples, runners, feature plans/status/provenance, proposed Phase B docs with their unapproved labels, reviews/gate records, before/after repros and selected final/checkpoint receipts. Do not blanket-ignore raw/metrics/JSON/TXT: many are acceptance evidence.

Keep61 repeated intermediate diagnostics local: Phase A run1/run2, Q00-follow-up initial/run2 and the installed RQ extract. phase_a_run3, q00a_run3, codex_q00a_final, repro sources/results and immutable review summaries remain publication candidates.

All426 original files decode as UTF-8 text or empty placeholders; no binary media/external originals or detected credential matches were observed. Fixture manifest declares synthetic_only. Current ignored environment/cache/model/external-source rules remain in place.

TASK_APPROVAL.md remains byte-identical and is a provenance candidate. Its verbatim instruction includes a workspace directory path without a personal username or credential; it is not silently redacted or replaced by new approval.

`apps/ui-mobile/android/gradle/wrapper/gradle-wrapper.properties` stays a tracked change outside this BE2 allowlist: 8.10.2-all → 9.7.1-bin plus generated timestamp. It is not hidden by ignore rules. The repo root branch has five separate status entries and is untouched.

## Local diagnostic disposition

Complete local originals stay at the same paths. GitHub readers can use the clean run3/final checkpoint summaries; historical intermediate receipt references are operator-local. Names/hashes below preserve their provenance.

RQ extract is local installed-dependency inspection, not project source. Original reviews retain its version/source analysis. This selection does not change those review results.

| Local path relative to feature | sha256 before triage |
|---|---|
| evidence/metrics/phase_a_run1_checks.json | 488ccc9f232a6935178a2ce91e0286ce460b893ea31476942ea6934967bf3760 |
| evidence/metrics/phase_a_run2_checks.json | 2d8c0cd929ac2b58c3f5e9ce039ba034edc1359a53fbef0da1bc7696a60aa6bd |
| evidence/metrics/q00a_checks.json | b4d83b2d4ee43092a3a3de3b4c898735c0be8e9ae82cc43f2264ee7a96df9a8b |
| evidence/metrics/q00a_run2_checks.json | 5820b42f4bb4b8387222019962a90026a2661705018703e4e48e7dc171a9ea84 |
| evidence/raw/phase_a_run1_architecture.txt | d22d7f600dcee8a6f266625df1ff5e2530b63848da66ef3fbf1814c45347ce62 |
| evidence/raw/phase_a_run1_diff_check.txt | 10ffcf12527cb2904bb5a9eb88b885bddc458b82638289242d84275906190bcf |
| evidence/raw/phase_a_run1_harness.txt | ca8ed7333d1877ecf95a38b96408a362e8dcc9c169caec10e48023b5da4f6a4f |
| evidence/raw/phase_a_run1_module_origin.txt | 513879d3e4e6f62d10f67ccf8dde019dbda0bb8d65061c282bf1ce9d54b57e6b |
| evidence/raw/phase_a_run1_mypy.txt | 176e98ae7ea1a8019e075767f2bef7c39ef8cc2651794008ad07b54d34d60e0d |
| evidence/raw/phase_a_run1_pytest_new.txt | 6e689a69636b2801ec40bde7255769b593875a43b605c622543dd34113e1f9a1 |
| evidence/raw/phase_a_run1_pytest_regressions.txt | 3c6cc643489c85ba548c162cf0ee70de7655a4fa75f51e0ac9c6b710286cab06 |
| evidence/raw/phase_a_run1_ruff.txt | 70b78ccc808155d182092c66263f42f7931380edc4ea8915e54bad1ab429d60c |
| evidence/raw/phase_a_run1_runner_default_python.txt | d989ff57f87d97688cf4afa767639f4aef07b958e1d7b9289d70036e04343cd1 |
| evidence/raw/phase_a_run1_runner_report.json | 437855d2ff6a5772bf50bb203f8de7543a84866cdb51ee1687afadd6403185e4 |
| evidence/raw/phase_a_run1_runner_report_http.json | 16dd46055745d420e9e3a14f878dd01008829099bf5d55dcdc88eb2811a56eae |
| evidence/raw/phase_a_run1_runner_venv_with_http.txt | a8d4492bf3acb4cbbb218bdc3314e6f70f5b595e563e9247e39833ca37bf74d6 |
| evidence/raw/phase_a_run1_security.txt | 5a2f44060be373aa27aec7face024d7a4e9cf9116da4baba3858847ce70e9000 |
| evidence/raw/phase_a_run1_skeleton.txt | 27cba6f2bf9acfd2b760ee6141d2ab70192ad96bd09bf21cfda8ad5b79c322a1 |
| evidence/raw/phase_a_run2_architecture.txt | 8d99e34d545c1da4425ec4fd1c6bb43b87ead29d6c92b608b5593a3cf4cd0dfa |
| evidence/raw/phase_a_run2_diff_check.txt | 6f1c059ab5eb4b3c4ac041596d666c89e160e081a7b05cc10f7822f4298f8f24 |
| evidence/raw/phase_a_run2_harness.txt | 99240b65570780c3dc38fe41be7b900e3c5da943cd5f924b2898af38b5956721 |
| evidence/raw/phase_a_run2_module_origin.txt | 68787a726f2cc77c61d9aa70b83c641bb5d6b8138d7bb7d11ffecc97a611f14d |
| evidence/raw/phase_a_run2_mypy.txt | 9cd1be7b410076870536b1ddff90c18fea72896cc68031c8a3b1758999b0fb25 |
| evidence/raw/phase_a_run2_pytest_new.txt | de458102a8fbb615c0eae84f252bc2580a22bbe559ea8116ba7f689d2eadaf8b |
| evidence/raw/phase_a_run2_pytest_regressions.txt | 8d89e3111c51eb3f80cc99cdb685bcae50c3343ac8cd4cdc5fbdbdfa1b7cd032 |
| evidence/raw/phase_a_run2_ruff.txt | f68318c8ad187501c00a78779b3fea945bb466eff3ee8d459267cd1e446ad063 |
| evidence/raw/phase_a_run2_runner_default_python.txt | b5119ebb134e8d463fb9518de6d3a1ac1d8f6f1a618d5ac05f07fa4ae2906a16 |
| evidence/raw/phase_a_run2_runner_report.json | d673153c96ae1f9fc826c4cd46c52c0b032e558dc3a329d3f247f73a306060a2 |
| evidence/raw/phase_a_run2_runner_report_http.json | 328d1f5972c870809844967eea836da83d04c3a365baf55ec3684b7f6584fd0c |
| evidence/raw/phase_a_run2_runner_venv_with_http.txt | c6055c30902fb2902ba9b542078a8c46ddde433100970e2d69e649cc1899a40b |
| evidence/raw/phase_a_run2_security.txt | e56bdb7d4ca1e41f5d5de51a6d42cea8ef697d36c878bea8eb4b9cce9b65ca5a |
| evidence/raw/phase_a_run2_skeleton.txt | 9ba74c376a63eb13eb84c0867fe8c2fb380f15647b582b22caec916d920a6658 |
| evidence/raw/phase_b_review_rq_source.txt | 59858cf6a9f9ae73ed674c383d68b6999ff46e4b53ee50023d4a749a7c93885e |
| evidence/raw/q00a_architecture.txt | c44459399233e31e280557aabf26932675f7d22769dddd9cf62c6dae796610ab |
| evidence/raw/q00a_diff_check.txt | 0a5be2f637e58f21e901562c5008c75422109e002ca2955959a86b144b0460f5 |
| evidence/raw/q00a_harness.txt | 7fa78d0e45bc1ac70e288d3451385bd3b5518a17578b53c7867a1c0aa767c494 |
| evidence/raw/q00a_module_origin.txt | 2565863909a43e97de136a4d5bd35b529dfcd3d4f46b8de597e63ca74e33fad3 |
| evidence/raw/q00a_mypy.txt | 77fc525035af34dddc501a47835349e19cbbed3a896c031be14e08b09a8bcfc1 |
| evidence/raw/q00a_pytest_new.txt | bb4d5367933340a4f9b3095aec7a7b7cc77ca45b14f95e281fabe0fe7bcf7b6c |
| evidence/raw/q00a_pytest_regressions.txt | 3761ca9a2590c14f7846f77e84cb5f281dfccd0faff5b5e668a67fefeadbbb23 |
| evidence/raw/q00a_ruff.txt | 814da1bed11c0ab3d2acd323ea05d809b54a7ea599519cd916d967e2b8ac3649 |
| evidence/raw/q00a_run2_architecture.txt | 7c3a39d3bd4e9337c97be08e6cd463905305e9c35772e3e50444d33968e24073 |
| evidence/raw/q00a_run2_diff_check.txt | 3faef4f4b509fb94931b52a112667d4bfc54b25035a5a0f3df2aa4ce2888a8c4 |
| evidence/raw/q00a_run2_harness.txt | 42460d3ac74133adc2b3f4672cbbb9750985b11b1ae00510f863221fed7dd967 |
| evidence/raw/q00a_run2_module_origin.txt | 6730a6da3e1aa2a9ca987607258ffe307dd5a18765620508731c9cb6b27a42d2 |
| evidence/raw/q00a_run2_mypy.txt | 645363a1b3adf3e676f064664ebf34b6d89625510c1906158e58e4e82d390a30 |
| evidence/raw/q00a_run2_pytest_new.txt | dc2a5a16c2b57fa21c89ae50d338bad03220b9686008eaade46bdc8ba46f214e |
| evidence/raw/q00a_run2_pytest_regressions.txt | 8ac92ce4be83a0976807be1cff306bc1a140ea20814aa4f7b03e05ccd7bc36fe |
| evidence/raw/q00a_run2_ruff.txt | 896e6f7ed5ea33aac20ed49765ffa6912ac7b3c460a70ded3551e6f247a70585 |
| evidence/raw/q00a_run2_runner_default_python.txt | c8bdf2aedd1c60c77365d42ff14cd32dac59005ef55fad6b8a264165d74f852c |
| evidence/raw/q00a_run2_runner_report.json | 3fe758f967c2760d7cb34ac0e64735a7862fb26196070cb66bc595fa6fe4ad43 |
| evidence/raw/q00a_run2_runner_report_http.json | b814eb7a68a0da8a04d973bf7236cc2666130fba5599268a3f551d64eeffda19 |
| evidence/raw/q00a_run2_runner_venv_with_http.txt | 8c96e104e41025bec7e37111e53a3bfd4f658d46f24dad7c97153d521474fa91 |
| evidence/raw/q00a_run2_security.txt | c2b063f16714c8080f5680a9ef171694a581167a6080f77450f9fe899f7a1e4f |
| evidence/raw/q00a_run2_skeleton.txt | ec48236229da5b0f6cbefee0ca7b9fcc5181a4770c4348296b8fe08664438dcf |
| evidence/raw/q00a_runner_default_python.txt | d9b56e70b02658908c144091a5692b28814cfe26878649198116a64e1f9092fe |
| evidence/raw/q00a_runner_report.json | 3fe758f967c2760d7cb34ac0e64735a7862fb26196070cb66bc595fa6fe4ad43 |
| evidence/raw/q00a_runner_report_http.json | b814eb7a68a0da8a04d973bf7236cc2666130fba5599268a3f551d64eeffda19 |
| evidence/raw/q00a_runner_venv_with_http.txt | b461c28131f8a826b57b92498e9f345e7d47d8cec18f44314e2488bf24014787 |
| evidence/raw/q00a_security.txt | 9cc4c1561a64d8dbea900c3311b573ac6ea8bfbc49d71cdc7647fb899f394e41 |
| evidence/raw/q00a_skeleton.txt | 6a084b24f07b590a6c0dc77649eabcfc0ca69391b5890d58f99997ce11a133a7 |

<details>
<summary>Original 364 GitHub-candidate paths</summary>

```text
docs/context/PROJECT_CONTEXT.md
docs/context/SOURCE_REGISTER.md
backend/src/sketch2life/application/ports/ai_jobs.py
backend/src/sketch2life/application/services/ai_jobs.py
backend/src/sketch2life/application/services/provider_copy_lifecycle.py
backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py
backend/src/sketch2life/contracts/schemas/ai_jobs.py
backend/src/sketch2life/domain/ai_jobs/__init__.py
backend/src/sketch2life/domain/ai_jobs/completion.py
backend/src/sketch2life/domain/ai_jobs/model.py
backend/src/sketch2life/domain/ai_jobs/provider_copy.py
backend/src/sketch2life/infrastructure/ai_jobs/__init__.py
backend/src/sketch2life/infrastructure/ai_jobs/fakes.py
backend/src/sketch2life/infrastructure/ai_jobs/harness.py
backend/src/sketch2life/interfaces/http/ai_jobs_fixture_app.py
backend/src/sketch2life/interfaces/http/routers/ai_jobs.py
backend/tests/contract/test_ai_job_contracts.py
backend/tests/contract/test_ai_job_polling.py
backend/tests/unit/test_ai_job_application.py
backend/tests/unit/test_ai_job_lifecycle.py
backend/tests/unit/test_ai_job_q00_followups.py
backend/tests/unit/test_ai_job_review_regressions.py
features/FEAT-044-be2-ai-job-foundation/CONTEXT.md
features/FEAT-044-be2-ai-job-foundation/DECISIONS.md
features/FEAT-044-be2-ai-job-foundation/approvals/TASK_APPROVAL.md
features/FEAT-044-be2-ai-job-foundation/assets/REVIEW.md
features/FEAT-044-be2-ai-job-foundation/assets/applied/.gitkeep
features/FEAT-044-be2-ai-job-foundation/assets/approved/.gitkeep
features/FEAT-044-be2-ai-job-foundation/assets/generated/.gitkeep
features/FEAT-044-be2-ai-job-foundation/evidence/README.md
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/.gitkeep
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/BE2_ROADMAP_REV2_CHECKS.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/CLAUDE_HANDOFF_CHECKS.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/CODEX_INDEPENDENT_REVIEW_20261014.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/CODEX_Q00_CLOSURE_REVIEW_20261014.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/CODEX_Q00_FINAL_CODE_REVIEW_20261014.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/PHASE_B_PLAN_REVIEW_CHECKS_20261014.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/PHASE_B_REV2_CLOSURE_REVIEW_CHECKS_20261015.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/PLANNING_CHECKS.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/Q00_ACCEPTANCE_PROMPT_CHECKS_20261014.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/Q00_DELIVERY_REVIEW_CHECKS_20261014.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00_closure_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00_closure_original_repro.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00_closure_pytest.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00_closure_runner.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00_closure_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00a_final_diff.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00a_final_followup_repro.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00a_final_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00a_final_original_repro.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00a_final_pytest.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00a_final_runner.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_q00a_final_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_review_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_review_pytest.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_review_runner.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/codex_review_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/handoff_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/handoff_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_a_final_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_a_run3_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_codex_review_diff.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_codex_review_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_codex_review_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_plan_docs_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_plan_rev2_docs_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_plan_rev2_docs_final_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_plan_rev2_frozen_hashes.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_plan_rev3_docs_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_plan_rev3_frozen_hashes.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_rev2_codex_diff.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_rev2_codex_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/phase_b_rev2_codex_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/planning_architecture.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/planning_diff.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/planning_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/planning_harness_corrected.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/planning_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/planning_skeleton.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_accept_docs_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_accept_live_route_attempt.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_acceptance_prompt_diff.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_acceptance_prompt_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_acceptance_prompt_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_delivery_review_diff.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_delivery_review_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_delivery_review_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00_final_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00a_final_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/q00a_run3_checks.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/roadmap_rev2_diff.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/roadmap_rev2_harness.json
features/FEAT-044-be2-ai-job-foundation/evidence/metrics/roadmap_rev2_security.json
features/FEAT-044-be2-ai-job-foundation/evidence/notes/.gitkeep
features/FEAT-044-be2-ai-job-foundation/evidence/notes/BE2_ROADMAP_REV1_ARCHIVE_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/BE2_ROADMAP_REV2_VALIDATION_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/CLAUDE_HANDOFF_REVIEW.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/INDEPENDENT_REVIEW.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_HANDOFF.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_IMPLEMENTATION_EVIDENCE.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_Q00_FIX_EVIDENCE.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_Q00_FOLLOWUP_FIX_EVIDENCE.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_B_PLAN_CODEX_REVIEW_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_B_PLAN_REV1_ARCHIVE_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_B_PLAN_REV2_ARCHIVE_20261015.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_B_PLAN_REV3_EVIDENCE.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_B_PLAN_REVISION_EVIDENCE.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_B_REV2_CLOSURE_REVIEW_20261015.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/Q00_ACCEPTANCE_DELIVERY_REVIEW_20261014.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/SOURCE_AUDIT.md
features/FEAT-044-be2-ai-job-foundation/evidence/notes/VALIDATION.md
features/FEAT-044-be2-ai-job-foundation/evidence/raw/.gitkeep
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_followup_probe_source.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_followup_probes.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_original_repro.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_pytest.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_runner.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00_closure_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_diff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_followup_repro.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_followup_repro.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_original_repro.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_original_repro.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_pytest.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_runner.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_q00a_final_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_boundary_probe_source.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_boundary_probes.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_probes.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_pytest.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_runner.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/codex_review_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/handoff_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/handoff_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_final_architecture.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_final_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_final_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_final_runner_default_python.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_final_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_final_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_final_skeleton.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_architecture.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_module_origin.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_mypy.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_pytest_new.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_pytest_regressions.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_ruff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_runner_default_python.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_runner_report_http.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_runner_venv_with_http.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_a_run3_skeleton.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_codex_review_diff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_codex_review_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_codex_review_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_docs_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_docs_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_docs_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev2_docs_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev2_docs_final_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev2_docs_final_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev2_docs_final_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev2_docs_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev2_docs_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev3_docs_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev3_docs_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_plan_rev3_docs_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_rev2_codex_diff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_rev2_codex_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/phase_b_rev2_codex_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/planning_architecture.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/planning_diff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/planning_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/planning_harness_corrected.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/planning_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/planning_skeleton.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_accept_docs_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_accept_docs_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_accept_docs_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_accept_live_route_attempt.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_acceptance_prompt_diff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_acceptance_prompt_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_acceptance_prompt_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_architecture.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_delivery_review_diff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_delivery_review_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_delivery_review_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_final_architecture.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_final_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_final_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_final_runner_default_python.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_final_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_final_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_final_skeleton.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_module_origin.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_mypy.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_pytest_new.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_pytest_regressions.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_repro_after.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_repro_before.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_repro_source.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_ruff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_runner_default_python.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_runner_report_http.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_runner_venv_with_http.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00_skeleton.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_final_architecture.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_final_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_final_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_final_runner_default_python.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_final_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_final_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_final_skeleton.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_original_r01_r11_repro.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_repro_after.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_repro_before.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_repro_source.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_architecture.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_diff_check.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_module_origin.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_mypy.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_pytest_new.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_pytest_regressions.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_ruff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_runner_default_python.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_runner_report.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_runner_report_http.json
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_runner_venv_with_http.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/q00a_run3_skeleton.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/roadmap_rev2_diff.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/roadmap_rev2_documentation.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/roadmap_rev2_documentation_source.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/roadmap_rev2_harness.txt
features/FEAT-044-be2-ai-job-foundation/evidence/raw/roadmap_rev2_security.txt
features/FEAT-044-be2-ai-job-foundation/evidence/screenshots/.gitkeep
features/FEAT-044-be2-ai-job-foundation/fixtures/MANIFEST.json
features/FEAT-044-be2-ai-job-foundation/fixtures/consumer_examples/p1_job_poll_sequence.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/negative/audience_kind_mismatch.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/negative/audience_session_mismatch.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/negative/bad_target_hash.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/negative/child_approve_shortcut.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/negative/library_without_dimension.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/negative/reject_without_reason.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/negative/sketch_in_library.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/positive/library_request_changes.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data24/positive/session_sketch_approve.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/attempt_zero.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/bad_input_hash.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/cancelled_with_refs.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/extra_provider_url.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/missing_correlation_id.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/naive_timestamp.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/percentage_null.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/percentage_over_100.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/queued_refs_without_disposition.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/queued_with_refs.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/refs_with_stale_disposition.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/revision_as_string.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/running_with_disposition.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/stale_as_state.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/succeeded_without_disposition.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/terminal_keeps_polling.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/negative/unknown_progress_with_zero.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/blocked_unsafe.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/cancelled_by_teacher.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/cancelled_consent_revoked.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/failed_exhausted.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/failed_retryable.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/queued.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/running_percentage.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/running_stages.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/running_unknown_progress.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/succeeded_accepted.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/succeeded_admin_projection.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25/positive/succeeded_stale_context.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25_child/negative/child_failed_without_failure.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25_child/negative/child_succeeded_with_failure.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25_child/negative/child_terminal_keeps_polling.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25_child/negative/child_with_request_ref.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25_child/negative/child_with_result_refs.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25_child/positive/failed_exhausted_device_projection.json
features/FEAT-044-be2-ai-job-foundation/fixtures/data25_child/positive/succeeded_device_projection.json
features/FEAT-044-be2-ai-job-foundation/fixtures/error_catalogue.json
features/FEAT-044-be2-ai-job-foundation/fixtures/policies/fixture.job_poll.v0.json
features/FEAT-044-be2-ai-job-foundation/fixtures/policies/fixture.job_retry.v0.json
features/FEAT-044-be2-ai-job-foundation/fixtures/provider_copy/negative/deleted_without_receipt.json
features/FEAT-044-be2-ai-job-foundation/fixtures/provider_copy/negative/fixture_labelled_deleted.json
features/FEAT-044-be2-ai-job-foundation/fixtures/provider_copy/negative/pending_claims_actual.json
features/FEAT-044-be2-ai-job-foundation/fixtures/provider_copy/negative/unmarked_fixture_report.json
features/FEAT-044-be2-ai-job-foundation/fixtures/provider_copy/positive/fixture_scope_purge.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-21.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-22.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-23.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-26.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-27.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-28.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-29.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative/DATA-33.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-21__request_reason__dict.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-21__request_reason__list.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-21__request_reason__null.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-21__request_reason__number.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-23__display_mode__dict.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-23__display_mode__list.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-23__display_mode__null.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-23__display_mode__number.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-27__strategy__dict.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-27__strategy__list.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-27__strategy__null.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-27__strategy__number.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-28__action__dict.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-28__action__list.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-28__action__null.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-28__action__number.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-33__action__dict.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-33__action__list.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-33__action__null.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/negative_types/DATA-33__action__number.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-21.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-22.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-23.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-26.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-27.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-28.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-29.json
features/FEAT-044-be2-ai-job-foundation/fixtures/shapes/positive/DATA-33.json
features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md
features/FEAT-044-be2-ai-job-foundation/plan/BE2_ROADMAP.md
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_BE2_HANDOFF.md
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_PHASE_A_FIX_PROMPT.md
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_PHASE_B_PLANNING_PROMPT.md
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_PHASE_B_REV2_COMPLETION_PROMPT.md
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_Q00_ACCEPTANCE_PROMPT.md
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_Q00_FOLLOWUP_FIX_PROMPT.md
features/FEAT-044-be2-ai-job-foundation/plan/PHASE_A_CANDIDATE_SPEC.md
features/FEAT-044-be2-ai-job-foundation/plan/PHASE_B_ADR_PROPOSAL.md
features/FEAT-044-be2-ai-job-foundation/plan/PHASE_B_PLAN.md
features/FEAT-044-be2-ai-job-foundation/plan/PHASE_B_PORT_REVIEW.md
features/FEAT-044-be2-ai-job-foundation/plan/PLAN.md
features/FEAT-044-be2-ai-job-foundation/src/.gitkeep
features/FEAT-044-be2-ai-job-foundation/src/fixture_catalog.py
features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py
features/FEAT-044-be2-ai-job-foundation/status/STATUS.md
```

</details>

## Operator outputs and verification

Full classification/hash manifest, GITHUB_CANDIDATES.txt, KEEP_LOCAL.txt, HOLD_SEPARATELY.txt, documentation snapshots and actual checks live in `evidence/local/publication-triage-20261015/` (ignored, feature-local).

The allowlist additionally includes two new housekeeping candidates: .gitignore and this note. No file was moved/deleted, staged, committed or pushed. Only documentation receipt disposition, an outdated BE2 context pointer and ignore rules changed; source/tests/fixtures/runners/approved PLAN.md/TASK_APPROVAL.md are preserved.

Before actual publication review the exact staged allowlist and run required gates. Candidate status does not close product gates or authorize publishing.

Final verification: Git status367 paths =366 allowlisted candidates (364 originals + .gitignore + this note) and1 separate Gradle change. All61 local diagnostics match their original hashes and are ignored; no candidate is ignored. All24 reviewed Phase A source/test/runner/approved-plan/approval hashes and the repo root's five status entries are unchanged; staging remains empty. Harness, repository security and git diff --check PASS. No implementation tests were repeated for this documentation/ignore change.

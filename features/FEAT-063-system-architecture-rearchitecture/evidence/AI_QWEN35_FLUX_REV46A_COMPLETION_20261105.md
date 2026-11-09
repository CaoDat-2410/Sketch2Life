# Qwen3.5-only profile and FLUX.3 Rev46A completion ? 2026-11-05

## Outcome

- The active FEAT-063 Qwen VLM/LLM model is pinned `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Qwen2.5 is retired from active source/configuration. Historical decisions, call records, and shared Modal model storage remain preserved.
- Root cause of both Rev46 image failures: the FLUX checkpoint downloader omitted Diffusers `transformer/` and `vae/` component files, while the marker allowed a partial checkpoint to look complete. Diffusers then encountered a missing transformer (`NoneType.dtype`). This was not a Hugging Face Secret authorization failure or GPU scheduling delay.
- The downloader now stages the component directories, verifies required nonempty transformer/VAE files, and continues staging if a valid old marker exists over an incomplete checkpoint. Model revision and worker contracts are unchanged.
- Post-fix: checkpoint staging and both previously failed synthetic image workloads passed once each. No Qwen story/drawing/deck/suggestion, TTS/ASR, SAM2, product HTTP API, or video inference was called in this revision.

## Modal execution

The FLUX dev app was deployed at approximately `2026-11-05 23:00` and stopped at `2026-11-05 23:03` Asia/Saigon. The full runner window was 2026-11-05T23:00:31.990+07:00 to 2026-11-05T23:03:27.844+07:00 (about 175.9 seconds). The final Modal app list showed the new app `stopped`, with 0 active tasks. Model and scratch Volumes were retained. The runner never read or stored the value of `huggingface-secret`; the Modal function received the Secret with required key `HF_TOKEN` only for model download.

| Stage | Modal call ID | Duration | Result |
|---|---|---:|---|
| Download missing pinned Diffusers files | `fc-01M6P720ANWE1EF7NFZXHMP2K3` | 61.472s | Passed; `downloaded`; FLUX.3 revision `09561231f44e41381c461caf53d5452005a60ac9` and PUP revision `a57899549f8f6f64c6c4d88db30827d496ff76d0` |
| Parent Sketch Guide | `fc-01M6P73WY59DN5FY9S8XZ7J7VA` | 65.772s | Passed; synthetic 3-panel butterfly guide, 768?512, DRAFT, review required |
| Lesson visual | `fc-01M6P760MQCHW7YCJR5Q0QB3J8` | 47.206s | Passed; synthetic 3-panel butterfly guide, 768?432, DRAFT, review required; lesson revision and content hash matched |

## Output review and limitations

- Parent image: [`parent_sketch_guide_candidate.png`](assets/flux_component_retest_rev46a_20261105/parent_sketch_guide_candidate.png), SHA-256 `ee22f36b5b9a465bffd08c826f52bd8570436a7f900aca01dce08a4105d0686d`. The three panels show a butterfly progressively. This is only a generic candidate; ordering/usability for children was not evaluated.
- Lesson image: [`lesson_visual_candidate.png`](assets/flux_component_retest_rev46a_20261105/lesson_visual_candidate.png), SHA-256 `a5ca6981ec5418d9cfa13aa86a5adcf347753307d9111d79760f6f95365288b2`. The first panel is a simple body/head, followed by wings and details. The rendered image passed the contract, but panel-to-step pedagogical clarity still needs an educator's review.
- Both outputs are private DRAFT candidates. They are not safety-approved, registered product assets, or publishable, and were not generated from a child's image or profile.
- These are direct Modal worker calls, not end-to-end authenticated product API tests. All product workload flags remain disabled. Video remains untested.

## Verification

- `pytest deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py -q --basetemp=.pytest-temp-modal-rev46a`: 27 passed.
- Ruff: passed for the FLUX worker, contract tests, and Rev46A runner.
- Python `compileall`: passed for the same files.
- Active-source search across backend/deployment found no Qwen2 model selection in `.py`, `.json`, `.toml`, or YAML files. A regression test asserts that every Qwen candidate in `workloads.json` is the pinned Qwen3.5 profile.
- Runner report: [`run_report.json`](assets/flux_component_retest_rev46a_20261105/run_report.json). Dispatch and result records are preserved alongside the two generated PNGs.
- Repository security validator: passed across 6,581 publishable files. `git diff --check`: passed.
- Official component layout reference: [BFL FLUX.3 transformer files](https://huggingface.co/black-forest-labs/flux-3-image-klein/tree/main/transformer), [BFL FLUX.3 VAE files](https://huggingface.co/black-forest-labs/flux-3-image-klein/tree/main/vae), and [Diffusers FLUX.3 modular pipeline](https://huggingface.co/docs/diffusers/v0.42.0/api/pipelines/flux3).

## Decision boundary

D-142 remains the active model decision: Qwen3.5 only for FEAT-063 Qwen development workloads; no production model approval. D-143 records the FLUX component completeness rule. Shared volumes and older Qwen2.5 evidence were intentionally preserved; this work removes Qwen2.5 from active source/configuration, not from historical records or stored shared volumes.

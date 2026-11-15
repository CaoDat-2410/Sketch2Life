# Plan Rev85 — Dataset-conditioned Qwen SVG illustration quality

**Status:** APPROVED — exact hash and scope are recorded in `approvals/TASK_APPROVAL.md` under the owner's direct request to improve Qwen SVG output with a dataset.

**Date:** 2026-11-13<br>
**Requirements baseline:** FEAT-063 v2.7-draft Rev69, unsigned; §§1–31 remain authoritative.<br>
**Worktree:** `codex/feat063-parent-docker-modal-seed-20261111`<br>
**Objective:** Improve Teacher SVG illustration drafts by giving the existing pinned Qwen3.5 worker a small, curated, license-traceable SVG reference set and a subject-aware composition brief, then render one real result through the existing Teacher UI.

## 1. Basis and observed quality issue

Rev84 exercised one real Teacher Web → backend → Modal → Qwen3.5 → sanitized SVG → browser-rendered draft. The 18-path deer was recognizable, but its anatomy was assembled from geometric circles, the head/body proportions were weak, some facial details were misplaced, and grass elements floated apart from the subject. Rev84 correctly limits this observation to one sample; it is not a broad quality assessment.

The canonical SRS distinguishes SVG illustration drafts for Teacher presentations from progressive line-sketch guides. This plan changes only Teacher SVG illustration generation. It does not change Parent/Teacher line-guide generation, the SVG catalog, lesson presentation persistence, or video.

## 2. Dataset choice and limits

### Selected source

- Dataset: [`yoavf/svg-animal-illustrations`](https://huggingface.co/datasets/yoavf/svg-animal-illustrations), pinned to Hub commit `d7ab3149308746a4b17e7cbee30f1f054f6c49df`; the public card lists 1,416 prompt/SVG pairs, 791 kB total, and CC0 1.0.
- The dataset card describes the examples as model-generated and systematically varied, with simple, flat animal illustrations. It is a compact source of structural examples, not a human-graded quality benchmark or a guaranteed style target.
- Before importing samples, resolve and record the immutable Hub commit SHA. A floating `main` branch is not acceptable. Preserve each selected row's original prompt/SVG, row identity, source commit, per-row SHA-256, and CC0/source URLs alongside the derived reference.

### Explicitly excluded sources

- Do not copy the full OpenClipart HF mirror: its card describes about 178,604 rows and 22.3 GB of mixed SVG content. It is too broad and heterogeneous for this latency-sensitive single-worker POC. Individual OpenClipart items can be evaluated in a separate curated-catalog task.
- Do not use KidDraw/children's drawing datasets: the previously identified license is CC BY-NC-SA and the samples are children's artwork. They are unnecessary for Teacher presentation illustration generation.
- Do not use Quick, Draw! as illustration exemplars: its timestamped child-drawn strokes are relevant to stroke/line-guide research, not polished colored presentation art.
- Do not use any repository fixture, previously generated product SVG, or Rev84 output as a dataset example.

### Intended use

Use retrieval/in-context examples only. Do not fine-tune Qwen, change its checkpoint, or claim the source data teaches a general artistic style. Keep no more than 12 validated examples and 64 KiB of compact reference data in the worker image. The full source dataset is not included in the Modal image or request payload.

## 3. Proposed runtime design

1. A one-time local curation step downloads the pinned public dataset revision and selects animal examples with topic match, a compact drawable structure, at least four visibly distinct parts, no executable/remote content, and successful conversion through the existing SVG sanitizer.
2. Preserve a small source snapshot and a derived `SvgDocumentV1` reference pack. Each derived record includes a stable reference ID, source prompt when the selected source row has one (the dataset's named `samples/*.svg` preview files have none, so mark prompt absent and use only their sample filename as the subject label), animal class, visual/style tags, source commit, row hash if available, source asset hash, and sanitizer/canonical hash. Before the existing sanitizer, permit only bounded deterministic normalization: strip non-semantic `title`/`desc` and cosmetic stroke-cap/join attributes, expand a simple `rotate(angle,cx,cy)` on an ellipse into cubic path geometry, normalize short hex colors, and convert rounded rectangles to path geometry. Reject scripts, external references, CSS classes/style blocks, arbitrary transforms, unsupported elements/attributes, non-finite geometry, or any construct that cannot be preserved safely. Keep source bytes unchanged and record every normalization applied; never relax the sanitizer or hide a rejection.
3. At request time, use a deterministic, bounded taxonomy lookup over the request's non-personal `topic`. Select at most one closest example. Exact animal-family matches rank above broad archetypes; unknown topics use no example. No remote retrieval occurs inside a Modal request.
4. Add the selected example as a compact **structural** reference in the Qwen prompt. Instruct Qwen to create a new subject-specific image and not reproduce the example's species, pose, colors, labels, paths, or incidental scenery. The final response remains structured `SvgIllustrationContentV1`, never raw SVG/XML.
5. Add concise anatomy/layout guidance to the existing prompt: prioritize one connected, readable subject silhouette; attach body parts at plausible joints; scale head/body/limbs consistently; keep markings on the body; avoid detached decorative elements and unrelated ground props. For a deer topic, call out torso, neck, head, antlers/ears, four grounded legs and coat spots as subject-specific components, without forcing a deer-only layout onto other topics.
6. Preserve backend sanitation, existing JSON schema, DRAFT/review-required/non-persisted response, role/scope checks, local-only gates and the pinned Qwen3.5 checkpoint. No output is auto-approved, persisted, or published.

## 4. Scope

- Create a pinned dataset source manifest and a compact curated reference pack under the Modal worker source tree.
- Add a small deterministic retrieval/selection helper and subject-aware prompt integration for `teacher.svg-illustration.generate` only.
- Include the reference pack only in the Teacher SVG Modal function image; avoid changing the shared image for unrelated language/audio workers.
- Add runtime logs containing reference ID/source revision/hash and selected taxonomy class, without logging the full source SVG or user credentials.
- Keep the existing Teacher SVG UI and API. Use the real UI form to request one new result for the same non-personal deer topic, age band and style as Rev84, so the old saved output is a comparable baseline.
- Capture the actual API result and browser render, plus elapsed time, worker phases, selected dataset reference, hashes, and final Modal container state in new FEAT-063 evidence.
- Update FEAT-063 context, decisions, source register, status, evidence index and SRS §32 after observing actual implementation/runtime results. Do not change SRS §§1–31 or claim formal SRS sign-off.

## 5. Out of scope

- No FLUX, raster generation, Parent flow, line-sketch/Sketch Deck changes, video, TTS/ASR, unrelated Qwen workloads, new API route, migration, catalog import, lesson persistence, or frontend redesign.
- No fine-tuning, LoRA, model/checkpoint switch, whole-dataset indexing at request time, external retrieval request, or new Modal Secret.
- No synthetic/fixed SVG as the live result, no fixture-as-success, no previously generated output reuse as the new result, and no retries.
- No consent/profile/child data; the UI input is a non-personal topic only.
- No public release, educator approval, generated asset adoption into the product, production-auth use, destructive Docker/database action, `.env` edit, commit, push, or merge.

## 6. Acceptance criteria

### Dataset and runtime contract

- Dataset commit SHA is immutable and recorded before import; if it cannot be resolved or the pinned source cannot be fetched, stop before source/dataset integration.
- Selected source records are traceable to their original rows and hashes; the source license is recorded as CC0 as declared by the dataset card. Do not imply that the dataset has been independently legal-audited.
- Every derived exemplar passes the existing sanitizer and renderer after only the listed deterministic normalizations; the source snapshot remains unchanged. No scripts, external references, unsupported SVG nodes, or malformed geometry reach the reference pack. Each record lists the normalization actions and is marked as a prompt reference, not an approved product asset.
- The pack has ≤12 examples and ≤64 KiB; no source artwork is copied into a Teacher lesson or public catalog.
- Retrieval is deterministic, local, and bounded to zero or one example. Unmatched topic => no reference and normal generation; no hidden canned/fallback SVG.
- Worker-to-backend output schema and response state remain unchanged. AI output stays `DRAFT`, `review_required=true`, `persisted=false`.

### One real UI generation

- Start/check only the existing local services required by Rev84; use the existing local synthetic Teacher account and real authenticated UI/API path.
- Confirm the deployed language/audio app and pinned Qwen checkpoint with one CPU `/health` call. If an update is required, update only `sketch2life-srs23-language-audio-dev` once.
- Trigger exactly one new UI inference for topic `con hươu sao`, age 60 months, style `warm_storybook`; no warmup call, retry, or additional topic.
- Compare the actual new render with Rev84's saved baseline using the same five qualitative checks: recognizable deer anatomy, coherent body/head proportions, connected/grounded limbs, markings/details attached to the subject, and no detached/unrelated objects. Record evidence and limitations; do not claim a population-level quality pass from one image.
- If inference fails, times out, has unknown outcome, fails sanitation, or renders worse/unclear, stop. Preserve the error/evidence; do not retry or relax safety/schema gates in this plan.
- Verify the local capability flag is disabled after the run, task-used local processes are shut down, Modal GPU containers have scaled to zero, and shared Modal Apps are left deployed. Never stop shared apps.

## 7. Bounded cost and operational limits

- Maximum one public dataset fetch/curation operation, one update of the existing Modal language/audio app, one CPU `/health` request, and one new UI-triggered GPU inference.
- No GPU warmup, no second deployment, no idle minimum containers (`min_containers=0`), no request retry, and no additional AI workload. One Qwen call is expected to include a cold start if the app has scaled to zero; prior Rev84 generation took 221.684 s end-to-end, including 180.536 s model inference. Actual new elapsed time must be recorded.
- Keep the prior hard request cap at 1,800 seconds. A timeout or uncertain outcome is terminal.
- Do not stop or modify other Modal applications or shared containers. Do not print or record any secret, token, authorization header, or personal data.

## 8. Exact file manifest

Only the following paths may be changed under this plan; preserve all existing worktree changes. If dataset review requires another path, update this plan and its approval hash before editing that path.

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV85_TEACHER_SVG_DATASET_QUALITY_20261113.md`
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
3. `deployment/modal/srs_v23/language_audio_app.py`
4. `deployment/modal/srs_v23/workloads.json`
5. `deployment/modal/srs_v23/data/teacher_svg_illustration/README.md`
6. `deployment/modal/srs_v23/data/teacher_svg_illustration/dataset-manifest.json`
7. `deployment/modal/srs_v23/data/teacher_svg_illustration/source-examples.jsonl`
8. `deployment/modal/srs_v23/data/teacher_svg_illustration/reference-pack-v1.json`
9. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/REPORT.md`
10. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/generated-svg-draft.json`
11. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/generated-svg-draft.svg`
12. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/teacher-svg-draft.png`
13. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append dated §32 evidence only)
14. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
15. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
16. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
17. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
18. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

## 9. Execution sequence

1. Record owner approval of this exact plan hash and path manifest.
2. Resolve the dataset commit; fetch into a temporary location; inspect license/source metadata and filter candidate rows. Stop if source hash, license metadata, or retrieval rights are unclear.
3. Sanitize/render candidates locally, choose at most 12, and record source plus derived hashes. Create the reference pack and source manifest.
4. Integrate deterministic retrieval and prompt guidance into the Teacher SVG function only; preserve schema and backend contracts. Update workload metadata.
5. Perform only non-test static checks necessary to ensure paths/hashes/config are well-formed; do not run the repository test suite under this plan.
6. Check Docker/API/UI and the existing Modal app read-only. Start task-local processes only if absent and needed; do not reset persisted services.
7. If required, deploy the single existing language/audio Modal app once; call CPU `/health` once; trigger exactly one real authenticated UI inference.
8. Save the actual response and browser render, record the five-point comparison against Rev84, shut down task-local processes, confirm Modal scale-to-zero, disable the capability, then update the evidence/context/status and SRS §32.
9. Report what changed, dataset provenance, actual quality comparison, runtime/cost boundary and any unresolved issues. Do not commit or push.

## 10. Known limitations

- The selected dataset is synthetic/model-generated and limited to pet species. It may provide reusable layout patterns but cannot guarantee realism or exact wild-animal anatomy. For a deer, Qwen still needs the subject brief; a pet exemplar must not override deer morphology.
- One output provides a user-reviewable comparison, not the owner-approved M3-B evaluation across 40–70 cases and educators. AI flags remain disabled by default; this plan only enables the already existing local test flag temporarily.
- The prior Rev84 SVG remains a saved evidence baseline and is not used as a prompt, fallback, catalog source, or live result.

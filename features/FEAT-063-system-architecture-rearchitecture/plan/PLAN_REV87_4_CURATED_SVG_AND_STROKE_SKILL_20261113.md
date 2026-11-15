# Plan Rev87.4 — Curated SVG reference plus stroke-authoring skill

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct direction to use a proper curated SVG source and install a skill that authors progressive strokes from it.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §6.2.1, BR-42/46, FR-P-11, FR-T-18/20, FR-AI-14/15, AC-34/44 and AT-15/18. Update SRS §32 as-built evidence only.

## 1. Superseded sources and diagnosis

- Quick, Draw! is user-created doodle data and is rejected for this product illustration use. No Quick, Draw! files or output may be retained.
- Openclipart item `330236` was inspected and rejected before packaging because it defaults to filled silhouettes rather than visible stroke paths.
- Tabler's outline `cat.svg` is a small UI icon rather than a complete child drawing source. It was inspected but not packaged.
- The current Qwen worker is instructed to emit SVG paths directly from topic text; it can satisfy JSON/path gates while still composing detached geometric blocks. The missing capability is a good, non-child reference illustration plus an authoring procedure that turns it into meaningful drawable paths and order.

## 2. Dataset and skill choice

### Curated SVG source

Use Arcadia Science's **Free Organism Illustration Library v1.0**, Zenodo DOI `10.5281/zenodo.17203578`, public archive `arcadia-organism-library-v1.0.zip` (41.2 MB; published archive MD5 `a845bf16730238334f39c7cfbc1d4703`). The project publishes professional vector/raster illustrations for 71 organisms and declares CC0. It provides silhouette and “tricolor + stroke” SVG variants. Select only the archive member `Gallus-gallus-tricolorstroke.svg` (dataset taxon label `Gallus gallus`, common topic “gà”) for this first guide; do not bundle the 41.2 MB archive, unrelated raster files, or unrelated organisms.

Treat the dataset asset as a visual/anatomical reference, **not as a pre-authored stroke order**. Preserve the selected original SVG byte-for-byte, record its archive member path, exact SHA-256, dataset DOI, CC0 license and attribution in the source manifest/README. Keep the source image separate from the derived child-facing stroke guide. Do not use a child's drawing as source or training data.

### Stroke authoring skill

Install the public Agent Skill `whiteboard-animation` from `iart-ai/explainer-video-skills/skills/whiteboard-animation` into project-local `.agents/skills/whiteboard-animation/`. The upstream project is MIT licensed. Preserve its `SKILL.md`, required references and license/attribution. Apply only the useful guidance: use open drawable paths, keep one intentional pen action per path, order paths as a person would draw them, animate each path with stroke-dash reveal, lift between pen actions, and review the resulting shape at start/mid/end.

This is an **authoring skill for the agent**, not an installable Modal model or runtime service. Port the relevant constraints into the Qwen worker prompt and the SVG engine contract; do not send the skill markdown as a hidden model capability or claim that Modal executes it.

## 3. Runtime and authoring flow

1. Add a small Modal source pack containing only the curated chicken SVG reference and provenance metadata. Add pinned CairoSVG `2.7.1` plus its Cairo runtime library only to the stroke-guide worker image; render the source to an in-memory PIL image for the already pinned Qwen3.5 multimodal worker. Do not send user photos, lesson files, child/account/profile/session identifiers, exact age, voice or transcript.
2. Use the worker's multimodal input with the visual source and adult-selected generic topic/difficulty. Apply the skill-derived prompt: create child-drawable continuous linework that follows the reference anatomy, with one actual path per pen action; no circles/rectangles as stand-ins for the animal, no disconnected shape pile, no fills, no background, no extra props. Use 4–8 meaningful stages, prior strokes retained, current strokes highlighted, future strokes hidden.
3. For matching chicken topics, Qwen returns structured path geometry, semantic parts, order and short Vietnamese child-facing instructions. The geometry must be new line paths in the normalized engine viewBox, not copied raster or embedded source illustration. Include source asset/hash and Qwen revision provenance. If the worker cannot produce a recognizable chicken from the visual reference, reject the draft; never fall back to the previous text-only block generation for this topic. Other topics retain the existing generation path until a matching source is added; the chicken reference is never reused for them.
4. Keep the current explicit Parent path: exact lesson/catalog lookup first; only after an adult's explicit request on a catalog miss can AI draft generation run. Parent draft remains private, ephemeral, adult-reviewed and skippable. Capture remains mandatory and available after a failed/disabled guide.
5. Keep the separate authenticated Teacher SVG-stroke-guide draft UI; it receives an unpersisted private draft and must show source provenance. Static Teacher SVG illustrations remain a separate capability.
6. If the dataset has a suitable reviewed SVG for another topic in a future amendment, add it to the source pack with exact provenance; do not silently substitute a visually unrelated species.

## 4. Quality gates and bounded run

- Keep SVG sanitization and 4–8-stage validation. Require `fill=none`, valid visible path strokes, stable path IDs, finite in-bounds geometry, no scripts/external references/embedded raster, no duplicate paths, each path assigned exactly once, each stage adding new paths, and final-stage coverage of all paths.
- Require visually identifiable chicken anatomy from the reference: connected body/head/neck, beak and comb, two grounded legs, wing and tail; stages must reveal these as actual drawn contours/details. Metadata labels alone do not pass. Do not lower any existing parser or sanitizer to accept a sample.
- Keep the existing deer hard gate for any generated deer topic. No animal source may be substituted across topics.
- Use one existing Modal app update, one CPU `/health`, and one authenticated real Parent UI-triggered GPU inference for the exact dataset-supported topic `gà`. No warmup, retry, second topic, video, FLUX, test suite, `.env`/secret edit, production identity, real child data, DB migration, publication, shared app stop, commit, push or merge. Keep the 1,800-second cap and restore the local capability flag to false.
- If the official archive, attribution/license, chosen SVG member, skill installation, modal health, live UI or single inference fails or is unknown, stop and report; do not retry or switch to a different source in this run.

## 5. Acceptance criteria

1. Project-local skill files are installed from the approved upstream repository with MIT attribution; the worker prompt and engine apply the stroke-authorship rules relevant to this product.
2. The packaged source is an exact Arcadia CC0 chicken SVG from the v1.0 archive; archive and selected-file hashes are recorded; no raw archive, raster, rejected dataset or user drawing is packaged.
3. A real UI-triggered Qwen3.5-VL request receives the curated SVG rendered in memory and returns new stroke-only geometry with source/model provenance. Output paths differ from the source image's filled shapes and are not canned/fixture output.
4. The final drawing clearly reads as a chicken and reveals recognizable parts progressively across 4–8 stages. It contains no block pile, filled primitive assembly, future-visible path or whole completed image on the first step.
5. Parent and Teacher previews use the real response; backend hard gates pass; the result remains an unpersisted private draft. Evidence contains actual source/output hashes, request/response, actual rendered steps, timings, worker phases/logs and visual verdict.

## 6. Exact cumulative file manifest

Rev87 §6 source/UI manifest remains in force with Rev87.1–Rev87.3 dataset/skill source choices superseded. Active additions for this amendment:

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_4_CURATED_SVG_AND_STROKE_SKILL_20261113.md` (new)
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
3. `.agents/skills/whiteboard-animation/` (new; only upstream skill files/references required for the skill and its license)
4. `backend/src/sketch2life/contracts/schemas/svg_engine.py`
5. `backend/src/sketch2life/domain/svg_engine.py`
6. `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
7. `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py`
8. `deployment/modal/srs_v23/language_audio_app.py`
9. `deployment/modal/srs_v23/workloads.json`
10. `apps/ui-mobile/src/parent/domain/svgGuide.ts`
11. `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
12. `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
13. `apps/teacher-ui/src/domain/svgGuide.ts`
14. `apps/teacher-ui/src/services/svgGuideDraftService.ts`
15. `apps/teacher-ui/src/pages/TeacherSvgStrokeGuideDraftPage.tsx`
16. `deployment/modal/srs_v23/data/arcadia_organism_strokes/gallus-gallus-source.svg` (new byte-preserved source)
17. `deployment/modal/srs_v23/data/arcadia_organism_strokes/gallus-gallus-v1.json` (new selected source/provenance pack)
18. `deployment/modal/srs_v23/data/arcadia_organism_strokes/README.md` (new attribution/license record)
19. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md` (new)
20. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/source-manifest.json` (new)
21. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide-draft.json` (actual response only)
22. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide.svg` (actual serialized response only)
23. Actual progressive-render screenshots under the same evidence folder.
24. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 as-built evidence only)
25. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
26. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
27. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
28. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
29. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

All other Rev87 source paths remain allowed only as listed in Rev87 §6. No Quick, Draw!, Openclipart or Tabler source files may be packaged. No other path may change without another explicit amendment.

## 7. Stop conditions

Stop before deployment if the official archive/hash/license does not match, the selected chicken SVG is unavailable or unsuitable, the upstream skill contents/license cannot be verified, or the project-local skill path is unavailable. Stop after the single attempt if any source, worker, health, API, UI, parser or visual gate fails. Preserve diagnostics, restore the local flag to false and do not retry.

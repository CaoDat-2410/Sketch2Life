# Plan Rev87.2 — Clean SVG stroke reference amendment

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct correction to replace Quick, Draw! with a clean SVG source suitable for the SVG stroke engine. This amendment supersedes Rev87.1's Quick, Draw! dataset choice; it does not authorize retaining Quick, Draw! data in the repository.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §6.2.1, BR-42/46, FR-P-11, FR-T-18/20, FR-AI-14/15, AC-34/44 and AT-15/18. Update SRS §32 as-built evidence only.

## 1. Problem and source decision

Quick, Draw! contains user-created doodles and its paths are not polished SVG teaching artwork. The owner rejected it for this purpose. Use one curated, clean, line-art SVG from Openclipart instead: **“cute simple cat sitting”**, Openclipart item `330236`, downloadable source `https://openclipart.org/download/330236`, detail/attribution page `https://openclipart.org/detail/330236/cute-simple-cat-sitting`. The page identifies the work as donated to the public domain by Colleen O'Dell/StarGlade and tags it simple cat sitting, line art, black-and-white and outline. Openclipart's FAQ says uploads use CC0 1.0.

The supplied `sketch2life_svg_stroke_guide_demo.html` remains only a visual reference for clean contours and progressive reveal. Do not copy or package its embedded paths. Do not use Quick, Draw!, child/user doodles, filled illustration packs, generated block primitives, or raster tracing as stroke geometry.

## 2. Source validation and curation

Fetch only the single Openclipart SVG named above. Preserve its original bytes and SHA-256. Before adding it to the Modal image, parse and inspect the SVG locally and require:

- XML parses as SVG; no scripts, event handlers, external resources, image/base64, foreign objects, filters, text, or animation.
- The cat is recognizably line art: actual visible `stroke`/`fill="none"` path geometry; no filled primitive assembly used as the guide.
- It has enough independent, meaningful path/subpath groups to form 4–8 ordered stages. Tiny decoration is not counted toward the minimum.
- The source is simple enough that path order/grouping can be reviewed by an adult and does not produce a cluttered or misleading step sequence.
- If compound paths must be split, the split is deterministic at existing SVG subpath boundaries only; do not invent, trace, or geometrically redraw paths. Reject sources that cannot meet this condition.

Store the byte-preserved source at `deployment/modal/srs_v23/data/openclipart_stroke_references/cat-source.svg`. Store a compact sanitized and normalized path pack, per-path provenance, license/source metadata, and source/selected-pack digests at `deployment/modal/srs_v23/data/openclipart_stroke_references/cat-v1.json`. The adjacent README records upstream title, item ID, uploader and original artist attribution as shown by the source page, CC0 1.0, source URLs, access date, source SHA-256, curation transformations and the fact that no stroke-order or teaching semantics were supplied by Openclipart.

Do not include the Quick, Draw! temporary file, any child/user drawings, contributor metadata from Quick, Draw!, or the supplied demo HTML in the repository.

## 3. Runtime behavior

- Keep Parent's approved catalog/lesson lookup first. Only after a successful miss and an adult's explicit request may the existing SVG guide feature flag dispatch the worker. Inputs contain the generic topic and coarse difficulty only; no child/profile/account/session identifiers, exact age, lesson files, photo, drawing, voice, or transcript.
- For exact topic `mèo`/`cat`, construct the SVG document from the sanitized Openclipart line paths. Qwen3.5 may select/assign existing path IDs into 4–8 semantic parts/stages, order them progressively and write concise Vietnamese instructions. Qwen may not emit or alter geometry. The engine returns only allowlisted source paths in the original SVG's line-art style, deterministically normalized to the engine viewBox.
- For other topics, preserve the current Rev87 generated-SVG fallback and strict gates. It must still produce actual continuous line paths, not detached circle/rectangle primitives. Do not use the cat source for another topic. No fallback to FLUX or a filled/static illustration.
- Preserve source and license provenance in the API response and Teacher preview: `source_kind=OPENCLIPART_SVG`, source item/URI, CC0-1.0, source hash, normalized pack hash and Qwen model/prompt revision. Parent/Teacher outputs remain private ephemeral drafts (`DRAFT`, `review_required=true`, `persisted=false`). Parent adult preview and explicit accept/skip remain required; capture remains available if guidance fails.
- Renderer reveals prior strokes solid, current strokes highlighted/dashed and optionally animated, future strokes hidden. The final cat appears only on the final step. Respect reduced-motion settings.

## 4. Quality and runtime gates

- Keep existing SVG sanitizer, schema and topic-guide path/stage gates unchanged or stricter. The source pack is validated both when curated and at worker startup. Every path is valid, non-empty, in bounds, stroke-only, nonduplicate, and assigned exactly once; each stage adds paths; final stage covers the source drawing.
- Retain the Rev87 deer anatomy gates for generated deer fallback. Do not lower thresholds to accept this source or any model output.
- Treat Openclipart's license statement as source-provided provenance, not an independent legal opinion. Retain the item page and original attribution in the data README.
- At most one update of existing `sketch2life-srs23-language-audio-dev`, one CPU `/health`, and one authenticated Parent UI-triggered GPU inference for `mèo`. No warm-up, retry, second topic, video, FLUX call, test suite, `.env`/secret edit, production identity, real child data, database migration, publication, shared Modal app stop, commit, push or merge. Keep request cap at 1,800 seconds and restore the local capability flag to false.
- If the source cannot be fetched, license/provenance is unclear, source has insufficient independent stroked paths, path semantics are not reviewable, Modal/model/UI is unavailable, or any hard gate rejects output, stop and report the blocker. Do not substitute Quick, Draw!, a fixture or a blocky Qwen fallback for the cat case; do not retry.

## 5. Acceptance criteria

1. The packaged source is the byte-preserved Openclipart item `330236`, with verifiable source and pack hashes, CC0 attribution and no Quick, Draw! content.
2. On `mèo`, actual UI flow first performs real catalog lookup and only dispatches the AI request after adult action. The Modal worker groups only the packaged SVG source paths; the response geometry is deterministically identical to the normalized source pack.
3. Rendered output is a recognizable line-art cat whose parts appear as meaningful progressive strokes over 4–8 stages; no block shapes, filled regions, full-image-at-first-step, unrelated subject, fixture or copied demo path is accepted.
4. Backend schema, sanitizer, geometry, source-lineage and stage gates pass. API response exposes source and model provenance and remains an unpersisted private draft. Parent UI shows adult review, accept and skip-to-capture; Teacher preview identifies source provenance.
5. Evidence contains the original source hash/attribution, curated pack hash, actual request/response, actual serialized SVG, rendered progressive-step screenshots, timings, logs and visual gate verdict. No other inference is performed.

## 6. Exact cumulative file manifest

The Rev87 source/UI manifest in §6 remains active, with the Rev87.1 Quick, Draw! data paths **removed** and replaced by the files below. Preserve all existing unrelated worktree changes.

Additional/updated paths for this amendment:

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_2_OPENCLIPART_SVG_STROKE_REFERENCE_AMENDMENT_20261113.md` (new)
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
3. `backend/src/sketch2life/contracts/schemas/svg_engine.py`
4. `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
5. `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py`
6. `deployment/modal/srs_v23/language_audio_app.py`
7. `deployment/modal/srs_v23/workloads.json`
8. `apps/ui-mobile/src/parent/domain/svgGuide.ts`
9. `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
10. `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
11. `apps/teacher-ui/src/domain/svgGuide.ts`
12. `apps/teacher-ui/src/services/svgGuideDraftService.ts`
13. `apps/teacher-ui/src/pages/TeacherSvgStrokeGuideDraftPage.tsx`
14. `deployment/modal/srs_v23/data/openclipart_stroke_references/cat-source.svg` (new byte-preserved source)
15. `deployment/modal/srs_v23/data/openclipart_stroke_references/cat-v1.json` (new curated vector pack)
16. `deployment/modal/srs_v23/data/openclipart_stroke_references/README.md` (new provenance/license record)
17. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-98_OPENCLIPART_SVG_STROKE_GUIDE_20261113/REPORT.md` (new)
18. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-98_OPENCLIPART_SVG_STROKE_GUIDE_20261113/source-manifest.json` (new)
19. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-98_OPENCLIPART_SVG_STROKE_GUIDE_20261113/generated-guide-draft.json` (actual response only)
20. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-98_OPENCLIPART_SVG_STROKE_GUIDE_20261113/generated-guide.svg` (actual serialized response only)
21. Actual progressive-render screenshots under the same evidence folder.
22. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 as-built evidence only)
23. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
24. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
25. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
26. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
27. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

Other Rev87 implementation paths remain allowed only as originally listed in Rev87 §6. No Quick, Draw! data file may be added. No other path may change without another explicit amendment.

## 7. Stop conditions

Stop if source validation fails before deployment, if any source geometry is not stroke-only/reviewable, if provenance is incomplete, if health or the single UI inference fails/has unknown outcome, if the renderer cannot demonstrate genuine progressive linework, or if the final image does not read as a cat. Preserve diagnostics, leave Modal deployed, restore the capability flag to false, and do not retry.

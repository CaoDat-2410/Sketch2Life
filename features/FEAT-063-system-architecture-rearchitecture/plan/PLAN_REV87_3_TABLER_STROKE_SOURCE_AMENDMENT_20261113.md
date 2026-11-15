# Plan Rev87.3 — True-stroke SVG source amendment

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct instruction to replace the rejected doodle/filled-shape sources with a proper stroke SVG.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §6.2.1, BR-42/46, FR-P-11, FR-T-18/20, FR-AI-14/15, AC-34/44 and AT-15/18. Update SRS §32 as-built evidence only.

## 1. Previous source rejections

- Quick, Draw! was rejected by the owner because its user-created doodles are not the clean SVG drawing source required here. No Quick, Draw! content may be packaged or returned.
- Openclipart item `330236` was fetched for the approved Rev87.2 source check, then rejected before packaging: its SVG has eight path elements but inherits black fill, has no stroke attributes, and encodes filled silhouettes rather than line strokes. Do not package that asset or treat the page's “line art” tags as proof of stroke geometry.
- The user-provided demo HTML remains visual guidance only; do not copy its paths.

## 2. Selected source

Use the **official Tabler Icons outline cat SVG** from `https://github.com/tabler/tabler-icons/blob/main/icons/outline/cat.svg` (raw source: `https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/cat.svg`). The official repository describes its icons as editable plain SVG, with 2px strokes, and licenses the set under MIT. Fetch only this one icon source. Record the source hash and retrieval date; preserve the exact original bytes.

The selected SVG is not accepted merely because it comes from an icon set. Validate it before packaging. It must explicitly use unfilled stroke geometry; it must be a recognizable cat; it must yield at least four independent meaningful stroke paths after splitting only existing SVG `<path>` elements and existing `M/m` subpaths. Preserve source path order and geometry. If this icon cannot yield 4–8 clear teaching stages, stop before deployment and report that no suitable source was found; do not substitute Quick, Draw!, Openclipart, a fixture, or generated geometry.

## 3. Curation and engine behavior

- Preserve source SVG at `deployment/modal/srs_v23/data/tabler_stroke_references/cat-source.svg` byte-for-byte.
- Store a compact sanitized dataset pack at `deployment/modal/srs_v23/data/tabler_stroke_references/cat-v1.json`, containing source path/subpath IDs, original path data, deterministic normalized path data, source and pack SHA-256, source URL, repository revision/tag if available, MIT license reference and license text reference.
- README records Tabler Icons authorship/project attribution, official repository, MIT license, selected icon path, exact source/pack hashes, normalization/splitting rules and the limits: the source is an icon, not an educator-authored stroke-order lesson.
- Accept only unfilled visible line paths (`fill=none`, explicit stroke); reject fills, images, scripts, external references, hidden paths, unsupported transforms, foreign objects, filters and animation. Normalize coordinates by a deterministic affine transform into the existing engine `viewBox`; do not close, trace, smooth into a different contour, add circles/rectangles, or alter stroke topology.
- When exact topic is cat/mèo, backend constructs the SVG document from this pack. Qwen3.5 receives only generic topic/difficulty and non-personal path IDs plus compact structural descriptions. It returns semantic grouping, 4–8 progressive stages and child-facing Vietnamese instructions only; it cannot return path geometry or modify source paths.
- Preserve the existing catalog/lesson-first lookup and explicit adult action before AI. No child/profile/account/session identifiers, exact age, photo/drawing/audio/transcript, or lesson file is sent. Parent/Teacher results remain private, ephemeral drafts with review required and not persisted. Adult preview/accept/skip remains; capture must remain available if guide generation fails.
- For non-cat topics, retain the Rev87 Qwen generated-line fallback and its strict gates, but never use the cat icon as another subject or fall back to static/filled SVG or FLUX.
- Renderer shows prior paths solid, current path highlighted/dashed/animated, future paths hidden, and the complete cat only on the final step. Respect reduced motion.

## 4. Hard gates and one-run limit

- Keep the SVG sanitizer and path/stage gates unchanged or stricter. Add only the SVG path commands proven necessary by this source, with parser coverage for their parameter arity, bounds and finite values. Do not loosen gates to make a result pass.
- Every source path must be assigned once; every stage adds an unseen path; final stage covers every path; path IDs and source hash are returned as provenance. No generated path geometry is accepted for this dataset-hit branch.
- Retain the Rev87 deer anatomy gates for generated deer output.
- At most one update of the existing Modal language/audio app, one CPU `/health`, and one authenticated Parent UI-triggered GPU inference for `mèo`. No warmup, retry, second topic, video, FLUX, test suite, `.env`/secret edit, production identity, real child data, database migration, publication, shared app stop, commit, push or merge. Request cap remains 1,800 seconds; capability flag is restored to false.
- If source validation, hard gates, Modal health, live UI or the single inference fails or has unknown outcome, stop and report. Do not retry or switch source in this run.

## 5. Acceptance criteria

1. Source is the official Tabler outline cat SVG, with byte-preserved source and reproducible source/pack hashes; no Quick, Draw! or Openclipart asset is packaged.
2. Source and API output are unfilled, visible stroke paths, not assembled filled shapes. Output geometry equals deterministic normalized source geometry exactly.
3. The real Parent UI path does a catalog lookup first and dispatches one AI request only after explicit adult action. Qwen chooses only stage/group metadata and Vietnamese instructions.
4. Rendered final image clearly reads as a cat. Earlier steps reveal meaningful parts progressively; no complete image at step one, no detached block shapes, no future paths, no fixture or copied demo path.
5. API passes existing strict source, sanitizer, parser, stage and lineage gates; response remains private and unpersisted. Evidence records source/pack hashes, actual API response, SVG, UI-rendered step screenshots, timing/logs and visual verdict.

## 6. Exact cumulative file manifest

Rev87 §6 remains in effect. Rev87.1 and Rev87.2 source additions are superseded and their Quick, Draw!/Openclipart data paths are excluded. The active cumulative manifest for this attempt is:

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_3_TABLER_STROKE_SOURCE_AMENDMENT_20261113.md` (new)
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
3. `backend/src/sketch2life/contracts/schemas/svg_engine.py`
4. `backend/src/sketch2life/domain/svg_engine.py`
5. `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
6. `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py`
7. `deployment/modal/srs_v23/language_audio_app.py`
8. `deployment/modal/srs_v23/workloads.json`
9. `apps/ui-mobile/src/parent/domain/svgGuide.ts`
10. `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
11. `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
12. `apps/teacher-ui/src/domain/svgGuide.ts`
13. `apps/teacher-ui/src/services/svgGuideDraftService.ts`
14. `apps/teacher-ui/src/pages/TeacherSvgStrokeGuideDraftPage.tsx`
15. `deployment/modal/srs_v23/data/tabler_stroke_references/cat-source.svg` (new byte-preserved source)
16. `deployment/modal/srs_v23/data/tabler_stroke_references/cat-v1.json` (new curated source pack)
17. `deployment/modal/srs_v23/data/tabler_stroke_references/README.md` (new provenance/license record)
18. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-100_TABLER_STROKE_GUIDE_20261113/REPORT.md` (new)
19. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-100_TABLER_STROKE_GUIDE_20261113/source-manifest.json` (new)
20. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-100_TABLER_STROKE_GUIDE_20261113/generated-guide-draft.json` (actual response only)
21. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-100_TABLER_STROKE_GUIDE_20261113/generated-guide.svg` (actual serialized response only)
22. Actual progressive-render screenshots under the same evidence folder.
23. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 as-built evidence only)
24. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
25. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
26. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
27. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
28. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

All other Rev87 source paths remain allowed only as listed in Rev87 §6. No file from rejected datasets may be added. No other path may change without another explicit amendment.

## 7. Stop conditions

Stop before deployment if the Tabler asset does not meet explicit stroke-only source validation, has too few meaningful paths for 4–8 stages, or does not visually read as a cat. Stop after the single attempt on any health, inference, parser, UI or quality failure. Preserve diagnostics, restore the local flag to false, and do not retry.

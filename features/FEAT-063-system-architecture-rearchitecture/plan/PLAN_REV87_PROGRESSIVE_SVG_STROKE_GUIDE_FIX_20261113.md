# Plan Rev87 — Fix progressive SVG stroke guides

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED for this bounded implementation by the owner's direct instruction “fix”, after reviewing the unusable Rev86 deer output.<br>
**Requirements source:** FEAT-063 v2.7-draft SRS, especially §6.2.1, BR-42/46, FR-P-11, FR-T-18/19/20, FR-AI-14/15, AC-34/44 and AT-15/18. SRS remains unsigned; update §32 as-built evidence only.

## 1. Problem and diagnosis

The previous UI called `teacher.svg-illustration.generate`. That workload returns a filled static `SvgDocumentV1`; it has no ordered stroke/step contract. Its 19 paths cannot be treated as 19 teaching strokes. The sample deer read as a rabbit and did not provide a progressive drawing procedure. The separate Parent `/sketch-guides` path still calls FLUX and returns a raster contact sheet, while the Expo Parent screen only looks up catalog/lesson guides and has no SVG AI fallback when the catalog is empty. The current filled dog/rabbit preview pack has no ordered teaching strokes and must not be used as if it were stroke-order data.

This plan adds a distinct topic-to-stroke-guide capability. Static SVG illustration remains a separate optional presentation asset. The guide must be line-only, staged, understandable to a child, and rejected before display when its structural/hard anatomy checks fail.

## 2. Outcome and behavior

### Parent

1. Keep the current optional guide entry point. Search the exact lesson guide first, then the approved Parent SVG catalog.
2. If neither has a guide and the adult explicitly asks for one, call the new Qwen3.5 `svg.topic-stroke-guide.generate` workload only when its independent capability flag is enabled.
3. Send only the adult-selected topic and a coarse `beginner` difficulty. Never send profile, exact age, lesson file, drawing/photo, audio, transcript, name, or child/account identifiers.
4. Return an ephemeral `DRAFT` (`review_required=true`, `persisted=false`). The adult previews and explicitly chooses “Cho trẻ xem” or skips. A failed/disabled/quality-rejected guide never blocks the mandatory capture step.
5. Render prior strokes solid, current-step strokes dashed/highlighted, and future strokes hidden. Instructions are concise Vietnamese child-facing directions.

### Teacher

Add a distinct “Tạo hướng dẫn nét SVG” draft page that calls an organization-authorized Teacher endpoint and previews the same progressive guide contract. Keep the existing “Minh họa SVG AI” screen explicitly labeled as a static illustration tool; never present its filled paths as a child's line guide. Generated guide drafts are not inserted into a lesson or catalog in this task. Teacher must use the existing manual/review flow for lesson persistence/publication.

## 3. Contracts and hard gates

Add versioned `SvgTopicStrokeGuideDraftV1` request/response DTOs and one shared Modal workload `svg.topic-stroke-guide.generate` on the existing language/audio Modal app, pinned to the existing Qwen3.5 revision. Keep the old FLUX app deployed for unrelated historical/current workloads; remove its Parent line-guide call from the active API path only. Do not remove the app or FLUX packages in this change.

The structured response contains model/prompt provenance, topic/difficulty hashes, a canonical `SvgDocumentV1`, semantic parts, and 4–8 ordered stages. Every drawable path is an unfilled line (`fill=none`) with a bounded stroke; each path is assigned once, each stage adds new paths, the final stage covers all paths, and the stage order is monotonic. Free-form XML/SVG/HTML/script, backgrounds, raster panels, fills and external references are rejected. Reuse the existing deterministic sanitizer/serializer and stage renderer.

Hard topic checks:

- For deer terms, require body, connected neck/head, four leg parts, face/details, left antler and right antler; each antler must contain one main beam plus at least two branch strokes. Branch endpoints must connect to a beam within the validator tolerance. A metadata label alone does not satisfy this topology check.
- Reject missing, duplicate, future-visible, repeated, empty, unassigned or out-of-order paths; reject guides outside 4–8 stages or with long/teacher-facing instructions.
- Validate bounds, path count/length, coordinate range, path syntax, stroke width, and no unrelated detached props. Do not relax an existing sanitizer/parser to pass a model result.
- Keep `SVG_TOPIC_STROKE_GUIDE_GENERATION_ENABLED=false` by default. Disabled requests return `CAPABILITY_DISABLED` without Modal dispatch. The test enables it only in the API process environment; do not edit `.env`.

The current static animal pack is deliberately not passed as stroke-order training data. Quick, Draw! exposes per-drawing ordered pen strokes under CC BY 4.0, but its doodles are not educator-authored lessons and do not establish Montessori pedagogy; no public data is downloaded or bundled in Rev87. It can be evaluated separately with attribution and human curation if needed.

## 4. Acceptance criteria

1. Backend Parent API uses lesson/catalog first and calls Qwen only on catalog miss, explicit request, and enabled capability. The Parent UI displays the real draft as a stepwise line guide with adult preview/accept/skip; capture remains available on any guide failure.
2. Teacher Web has a separate authenticated topic-to-stroke-guide draft page using the same contract and renderer. Static illustration UI remains separate.
3. A real Modal output must pass the strict output schema and deterministic hard gates before either UI shows it. For the approved deer sample, the final preview must visibly read as a deer with two branched antlers, a connected body/neck/head and four attached legs. If it fails, preserve the failure and stop; do not retry or lower gates.
4. No product persistence, catalog approval, lesson publication, child-data use, video, FLUX call, or parent profile/consent change.
5. Evidence includes actual request/response, SVG and actual rendered progressive-step screenshots, exact timings/worker phases and the visual hard-gate verdict. No fixture or previously generated SVG may satisfy acceptance.

## 5. Bounded runtime and cleanup

- At most one update of the existing `sketch2life-srs23-language-audio-dev` app, one CPU `/health` call, and one authenticated real UI-triggered GPU inference. Use the existing synthetic Parent/Auth Emulator and local Docker stack. No retry, warm-up, second topic, or alternate workload. Keep a 1,800-second request cap.
- If the API's usual host port is occupied, do not stop or alter the user's other API. Use an isolated task API on a verified free port or stop before inference and report the blocker. Do not modify root `.env`, secrets, database data, or named volumes.
- After the one inference, restore the SVG guide capability to false, close task-started UI/emulator/browser processes, leave the shared Modal app deployed, and do not claim scale-to-zero unless observed.
- Do not run the full test suite. Build/static checks and the single live acceptance request are allowed. No commit, push or merge.

## 6. Exact file manifest

Only the following paths may be changed. Preserve every pre-existing dirty file outside this list. If another source path is required, stop and request a separately approved amendment.

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_PROGRESSIVE_SVG_STROKE_GUIDE_FIX_20261113.md`
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
3. `backend/src/sketch2life/contracts/schemas/svg_engine.py`
4. `backend/src/sketch2life/contracts/schemas/modal_ai.py`
5. `backend/src/sketch2life/domain/svg_engine.py`
6. `backend/src/sketch2life/infrastructure/config/settings.py`
7. `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
8. `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
9. `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py`
10. `deployment/modal/srs_v23/contracts.py`
11. `deployment/modal/srs_v23/language_audio_app.py`
12. `deployment/modal/srs_v23/workloads.json`
13. `apps/ui-mobile/src/parent/domain/svgGuide.ts`
14. `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts`
15. `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`
16. `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
17. `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
18. `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
19. `apps/teacher-ui/src/domain/svgGuide.ts`
20. `apps/teacher-ui/src/services/svgGuideDraftService.ts` (new)
21. `apps/teacher-ui/src/pages/TeacherSvgStrokeGuideDraftPage.tsx` (new)
22. `apps/teacher-ui/src/App.tsx`
23. `apps/teacher-ui/src/components/TeacherLayout.tsx`
24. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-97_PROGRESSIVE_SVG_STROKE_GUIDE_FIX_20261113/REPORT.md` (new)
25. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-97_PROGRESSIVE_SVG_STROKE_GUIDE_FIX_20261113/generated-guide-draft.json` (actual response only)
26. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-97_PROGRESSIVE_SVG_STROKE_GUIDE_FIX_20261113/generated-guide.svg` (actual serialized response only)
27. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-97_PROGRESSIVE_SVG_STROKE_GUIDE_FIX_20261113/` actual progressive-render screenshots (actual UI output only)
28. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 as-built evidence only; do not edit §§1–31)
29. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
30. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
31. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
32. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
33. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

## 7. Stop conditions

Stop without a second call if the modal app/credential/model readiness is unavailable, the parser/hard gate rejects the response, the UI path cannot be completed on real local services, request outcome is unknown, or the final deer anatomy is visibly not recognizable. The workload remains disabled by default and the result remains a draft even if the one sample passes.

# FEAT-083 Plan Rev1 — Qwen3.8, everyday content quality, and rotating Parent catalog

**Date:** 2026-11-23
**Status:** APPROVED for implementation by the owner’s direct request in this conversation.
**Product authority:** FEAT-063 SRS v2.7-draft, unsigned; amend the working SRS as Rev68 and keep it unsigned.

## 1. Objective

Make the active AI pipeline use one Qwen checkpoint, improve the usefulness and visual/story continuity of generated content, and make Parent topic/subject suggestions varied and non-repeating. Preserve the current Parent workflow and its adult confirmation, catalog access, age, safety, video admission, and privacy rules.

## 2. Owner decisions captured

1. All active Qwen calls use Qwen3.8, including drawing-image understanding.
2. AI-created activities, scripts, and video instructions should feel coherent, concrete, age-appropriate, and connected to ordinary child life; avoid shallow repetitions such as “look at the animal and a leaf.”
3. Parent sees three topic cards at a time from a rotating catalog of 15–20 topic groups. Use 18 groups, and do not repeat topic cards until the cycle is exhausted.
4. Each catalog topic has varied drawable-subject cards that rotate without repeats until their topic cycle is exhausted.
5. Keep the free-text topic field. A typed topic matching the catalog uses that catalog’s subject cards. A topic outside the catalog requires the adult to enter the object/animal; Qwen validates whether it belongs to that topic. If not, explain and request a correction or a catalog topic choice.

## 3. Scope

### 3.1 Model pin and Modal workers

- Align drawing VLM with the already pinned `Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81` checkpoint and shared Modal Volume path/manifest.
- Restrict the drawing worker to a GPU with sufficient VRAM for the 27B FP8 vision model; never silently route to Qwen3.5.
- Align backend model provenance, workload registry, health/readiness output and deployment notes so every active Qwen request reports the same exact model ID/revision.
- Keep Whisper ASR, VieNeu TTS and LTX-2.5 video unchanged as dedicated non-Qwen workloads. Keep legacy disabled model examples clearly marked historical/disabled.

### 3.2 Curated catalog and rotation

- Move topic content into one versioned Vietnamese catalog resource with exactly 18 topic groups and at least nine distinct subject cards per group. Use familiar Vietnamese and everyday-life topics suitable for ages 3–10; retain a smaller imaginative topic subset only where it stays drawable and age-appropriate.
- Rotate three unseen topic IDs per request using adult-account state. Rotate three unseen subject IDs within the chosen topic. Reset a cycle only after all entries in that cycle were shown.
- Use an atomic state update and request replay key (`adult account + draft ID + suggestion kind + topic scope`) so retries return the same set without advancing twice and concurrent devices do not allocate duplicates.
- Store only internal account UUID, draft UUID, catalog IDs/revision, cycle state, opaque set IDs and timestamps. Do not store custom topic text, child profile, image, voice or story data.
- Add a forward Alembic migration and SQLAlchemy model for rotation state/replay receipts. No existing rows are rewritten or deleted.

### 3.3 Custom topic and subject flow

- Resolve typed text against canonical catalog names/aliases. A recognized catalog topic returns its own rotating three-subject set.
- An unrecognized topic returns `CUSTOM_INPUT_REQUIRED` with no generated subject cards; the UI shows a subject input and asks the adult to name what the child wants to draw.
- Validate that topic/subject pair with Qwen3.8 using generic text only. `ON_TOPIC` enables continuation. `OUT_OF_TOPIC` and `NEEDS_CLARIFICATION` keep the user on the step and offer edit/topic-switch actions.
- Preserve current PII rejection, adult confirmation, SVG guide opt-in, required drawing capture, image-topic mismatch handling, and activity/story order.

### 3.4 Content quality

- Parent activity fallback: ask Qwen for three distinct, complete activities with an everyday place/context, child-led concrete actions, age-fit materials, clear preparation, 3–5 actionable steps, a learning/observation outcome, and relevant adult safety guidance. Keep catalog-first selection and exact three-item fallback behavior when no eligible catalog activity exists.
- Parent story: use a coherent beginning, goal, meaningful action/change, consequence and resolution; ground events in the confirmed drawing, topic/lesson facts, adult-confirmed idea and selected activity. Replace overly restrictive micro-copy limits where they cause generic fragments, while retaining the current response contract and adult-review gate.
- Video: version the LTX prompt compiler. Keep the source drawing as the exact first frame, preserve line style/colors/composition and all identified entities/props across scene transitions, and describe only the approved scene action/camera motion. No new object/action may be invented by the video prompt. Keep the existing silent candidate and all safety/admission checks.
- Add moderate quality validation for empty/vague/repeated activity steps and non-progressing story beats. Hard validation remains schema/privacy/safety/grounding; stylistic quality checks must not cause brittle rejection of otherwise valid child-safe content.

### 3.5 SRS and feature records

- Update FEAT-063 SRS document history and relevant current target paragraphs as Rev68: Qwen3.8 development model across Qwen workloads; topic rotation/custom-topic behavior; narrative/activity/video grounding expectations. Keep the SRS unsigned and do not change production model approval status.
- Update FEAT-063 source register/context/decisions/status and FEAT-083 source register/decisions/status with implementation facts separately from target requirements.

## 4. Exact implementation file scope

- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/story_visual_plan.py`
- `deployment/modal/srs_v23/workloads.json`
- `deployment/modal/srs_v23/README.md`
- `backend/src/sketch2life/application/services/parent_topic_suggestions.py`
- `backend/src/sketch2life/contracts/schemas/parent_topic_suggestions.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_topic_suggestions.py`
- `backend/src/sketch2life/infrastructure/persistence/be1_models.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/src/sketch2life/contracts/schemas/modal_ai.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/alembic/versions/20261123_parent_topic_rotation.py`
- `apps/ui-mobile/src/parent/domain/types.ts`
- `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts`
- `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts`
- `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/DrawingSubjectScreen.tsx`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `docs/context/SOURCE_REGISTER.md`
- `features/FEAT-083-qwen38-everyday-quality-topic-rotation/**`
- One versioned catalog data file under `backend/src/sketch2life/resources/`.

Any newly discovered required source file must first be listed in a dated plan amendment; no unrelated branch merge or UI redesign is included.

## 5. Acceptance criteria

- **AC1 Model consistency:** every active Qwen workload emits and validates the exact Qwen3.8 model ID/revision; drawing image understanding runs through the Qwen3.8 multimodal model path; there is no automatic Qwen3.5 fallback.
- **AC2 Catalog breadth:** the catalog has 18 unique topics and at least nine distinct drawable subjects for every topic, with Vietnamese titles/aliases and stable IDs.
- **AC3 Rotation:** a parent sees three distinct topic cards; subsequent requests for the same account do not repeat a topic or topic-subject card until that cycle is exhausted. Replaying the same draft returns the same cards and does not advance state.
- **AC4 Custom input:** known typed topics resolve to catalog cards. Unknown topics show no AI-invented subject cards and require subject input. Qwen3.8 validates the pair and the UI provides correction/topic-switch paths.
- **AC5 Activity quality:** fallback returns exactly three non-duplicate activities with concrete, safe, everyday materials and instructions, without disturbing catalog-first candidate selection or age filtering.
- **AC6 Story quality:** five-scene current response remains schema-valid and adult-reviewable; scenes progress through a concrete causal arc, use confirmed facts/selected activity, and avoid repetitive observation-only filler.
- **AC7 Video continuity:** prompt version changes; each scene is tied to the approved action and continuity plan, the exact drawing remains visually anchored, and the prompt adds no unapproved props/actions. Existing gates remain unchanged.
- **AC8 Privacy:** topic rotation stores only internal account/draft/catalog identifiers; no raw child, profile, image, voice, story, or custom topic data is stored or sent to the generic topic-subject worker.
- **AC9 SRS traceability:** SRS Rev68 records the owner clarification and remains explicitly unsigned; implementation status is clearly separated from target requirements.

## 6. Exclusions and operating limits

- No FLUX, new image model, new ASR/TTS/video model, new GPU family, Docker-hosted model, or production workload enablement.
- No changes to consent, quota/payment, publication, safety policy, child age range, Parent step ordering, video safety gates, or SRS sign-off state.
- No real child data, secrets, account seeds, service-account files, or Modal tokens.
- No Modal deployment, model download, GPU inference or database migration execution is authorized by this implementation request; these are separate runtime operations. The code must remain ready for the existing Modal dev Volume and Qwen3.8 checkpoint.
- Do not commit/push unless separately requested.

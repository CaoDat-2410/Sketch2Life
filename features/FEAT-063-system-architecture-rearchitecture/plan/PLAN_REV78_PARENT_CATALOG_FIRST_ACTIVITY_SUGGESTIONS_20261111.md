# Plan Rev78 — Parent catalog-first activity suggestions

## Status

APPROVED for the bounded product-contract, implementation, and verification scope below. This is an owner clarification to the unsigned FEAT-063 v2.7-draft SRS; it does not constitute formal SRS sign-off.

## Owner direction

The owner clarified that Parent activity suggestions must first use the existing activity catalog. Send the eligible catalog candidates to AI so it can select activities using the child profile, image-derived context, selected topic, and the child's narration/idea. If no catalog activity is suitable, AI may draft three suggestions, subject to a real quality gate.

## Finding this plan addresses

The current Parent StoryRun endpoint either returns every activity from a pinned lesson without AI selection, or asks Qwen3.5 Modal to invent exactly three outdoor activities from confirmed subject, visible drawing features, and age band. It does not retrieve the general activity catalog and does not pass profile interests, topic, or the saved adult-confirmed idea/narration. A separate supervised P1 route has catalog filtering and AI ranking, but is demo-actor/session scoped and is not the authenticated Parent StoryRun contract. The current Rev62 SRS describes the free-form/no-catalog behavior and must be amended explicitly.

## Approved behavior

1. The Parent preview remains optional, skippable, and non-blocking for story/video.
2. Before Modal invocation, the backend retrieves only currently eligible, renderable activity candidates from published lesson versions that this Parent can view (PUBLIC or active SHARED grant). Eligibility uses the accepted profile age in exact months, selected topic, confirmed drawing subject/visible features, outdoor suitability, and the applicable publication/safety constraints.
   Because lesson target-age references are currently opaque strings, only references that explicitly encode a valid month range (`age-{min}-{max}-months-v{n}` with a matching stored version) can prove age eligibility. Unknown legacy values such as `age-3-6` are excluded; no range is inferred from their label.
3. If a lesson version is pinned, only activities from that exact immutable version/hash are candidates for this preview. If no lesson is pinned, candidates come from the Parent-authorized published/shared lesson catalog, each preserving its exact lesson version/hash. The static ACT demo catalog is not a product source. A generated fallback is a temporary Parent preview draft only; it never mutates the lesson catalog, a pinned lesson, or the pinned lesson's post-video activity list.
4. The Modal worker receives a bounded candidate payload plus minimized context: age band, allowed interest summary/tags, selected topic, adult-confirmed subject, visible features derived from the image, and the saved adult-confirmed idea/transcript where present. It receives no image bytes, child name, profile ID, Firebase identity, or raw audio.
5. When one or more catalog candidates are suitable, AI returns only request-scoped candidate IDs, order, and short match reasons. The backend verifies every ID belongs to the submitted eligible set and returns canonical activity content from its exact published/shared lesson version; AI cannot rewrite a catalog activity.
6. If the eligible set is empty or the model judges that none is suitable, AI may produce exactly three structured fallback drafts. A backend quality gate rejects malformed, duplicate, age-inappropriate, unsafe, non-outdoor, unsupported, or non-child-centered proposals. A distinct AI review result may supplement, but cannot override, hard backend safety rules. Rejected output fails closed and leaves the Parent free to skip.
7. Every result is marked as catalog-derived or AI-generated draft, remains adult-reviewable, and has provenance sufficient to distinguish the exact lesson version/hash and activity position, or a generated draft. Generated fallback output is not published or added to reusable lesson content.
8. Do not use Lightning adapters or the standalone demo P1 endpoint for the Parent implementation. Use the existing catalog/domain logic behind a Parent-owned application boundary and Qwen3.5 hosted on the existing Modal language/audio app.

## Scope

- Amend the canonical FEAT-063 SRS with a Rev63 owner clarification and reconcile the conflicting Parent activity statements, trace rows, O-13, and Rev62 no-catalog wording.
- Add a Parent application-level catalog retrieval/eligibility boundary and connect the existing Parent API to catalog-first selection and bounded fallback generation.
- Version the Parent activity request/output contract and the Modal worker contract; preserve the existing Parent route path unless source review proves a compatibility-safe additive route is required.
- Preserve the selected lesson's exact target age-band reference/version in the immutable StoryRun pin snapshot so pinned candidates can pass the same fail-closed age eligibility check without re-reading a mutable or newly published lesson version. This is a JSONB snapshot contract change; it requires no database migration.
- Add the Parent UI's source and match-reason presentation, without changing the mandatory drawing, subject-confirmation, story, or video order.
- Add focused contract, safety-gate, API, worker, and UI type checks. Then run one synthetic Android-connected catalog-first Parent activity inference and one synthetic fallback inference if both paths can be arranged from testable eligibility contexts without using real-child data. No video API or Modal workload may be called.
- Record results and screenshots in the existing feature-local Rev77 evidence folder; update FEAT-063 context/status/registers and SRS authority pointers after review.

## Acceptance criteria

- AC1: Canonical SRS says catalog-first and no longer claims that Parent no-preset preview never queries the activity catalog; historical Rev62 remains traceable as superseded by the Rev63 clarification.
- AC2: Parent server constructs the eligible candidate set and sends only minimized allowed context and bounded candidate data to Modal.
- AC3: Catalog-mode worker output contains only eligible catalog references; API hydrates canonical versioned content and rejects unknown/duplicate IDs.
- AC4: Fallback is invoked only when the eligible/AI-suitable set is empty; it produces exactly three draft proposals or fails closed.
- AC5: Backend quality gate enforces the hard child-safety, age, Montessori, outdoor, schema, and duplication rules; adult review remains required.
- AC6: A pinned lesson's immutable activity list and its post-video behavior remain unchanged by preview ranking or generated fallback.
- AC7: Parent UI labels provenance and explains catalog match reasons; skip and failure continue to story without retrying automatically.
- AC8: No image/audio bytes or direct child/account identifiers reach the activity worker; all runtime tests use generated artwork and synthetic profiles.
- AC9: Focused tests pass, one catalog selection and one fallback case are verified, and no video route is called.
- AC10: A newly pinned lesson snapshot preserves its exact age-band reference/version; pin eligibility never reads or silently substitutes a newer lesson version, and the JSONB contract change requires no migration.

## Exact implementation/documentation paths

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `docs/context/SRS_AUTHORITY.md`
- `docs/context/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV78_PARENT_CATALOG_FIRST_ACTIVITY_SUGGESTIONS_20261111.md`
- `backend/src/sketch2life/contracts/schemas/modal_ai.py`
- `backend/src/sketch2life/contracts/schemas/parent_story_runs.py`
- `backend/src/sketch2life/application/ports/parent_activity_catalog.py`
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/src/sketch2life/infrastructure/lesson_library/service.py`
- `backend/src/sketch2life/infrastructure/lesson_library/parent_activity_catalog.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py`
- `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/tests/unit/` (Parent activity quality-gate/contract tests)
- `backend/tests/integration/lesson_library/test_lesson_library_api.py`
- `backend/tests/integration/parent_ai/test_parent_activity_suggestions.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/workloads.json`
- `apps/ui-mobile/src/parent/domain/types.ts`
- `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`
- `apps/ui-mobile/src/parent/application/`
- `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/navigation/`
- `apps/ui-mobile` focused tests as needed by the existing Parent activity contract
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-87_PARENT_FULL_API_UI_E2E_20261111/`

No file outside these paths may be changed without a scoped plan amendment.

## Limits

- Synthetic/dev data only; no real child, actual child image/audio, identity, or production data.
- No video workload/API, no Lightning adapter, no Firebase/S3/Modal secret inspection or mutation, no root `.env` change, no commit/push.
- Do not stop or redeploy the Modal language/audio app while the already-running story request is still active. After it completes, deploy only the approved language/audio app revision and stop only apps newly deployed for this task, after confirming zero active calls.
- Preserve the pinned lesson and all unrelated local changes.

## Owner source clarification

The owner selected “Published/shared lessons” as the source of the existing activity catalog. The Parent implementation must use only versions the Parent can currently view, respecting PUBLIC scope or an active shared grant. The static ACT catalog is demo-only and is excluded from this Parent source.

## Approval basis

The project owner directly specified the catalog-first behavior and the three-draft fallback with a quality gate in the 2026-11-11 conversation, then selected Parent-accessible published/shared lessons as the catalog source. The approval applies only to this amended plan and its listed paths/acceptance criteria.

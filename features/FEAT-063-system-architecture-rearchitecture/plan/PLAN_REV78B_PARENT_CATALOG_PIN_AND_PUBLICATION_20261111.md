# Plan Rev78B — Parent catalog pin persistence and publication

## Status

**APPROVED** for this bounded implementation closeout and publication. The owner directly requested: “commit và push, sau đó merge nhánh này vào dev.” This addendum supersedes the no-migration assumption in Rev78 and the no-commit/push limits in Rev78/Rev78A only for the paths and operations listed here.

## Authority and recorded product direction

- Canonical working SRS remains FEAT-063 v2.7-draft Rev60, unsigned, per `docs/context/SRS_AUTHORITY.md` and the repository instructions supplied by the owner.
- The owner’s direct Rev78 clarification is: use Parent-accessible published/shared lesson activities as candidates; have Qwen select and explain matches using minimized child/profile, confirmed drawing, topic and adult-confirmed narration context; if none are suitable, return exactly three temporary AI drafts through the hard quality gate.
- The Rev60 SRS leaves no-preset Parent catalog behavior open. This implementation records the later owner direction in this feature plan and decision log; it does not silently rewrite or sign the SRS. Formal SRS reconciliation remains open.

## Scope

1. Complete the approved Rev78/Rev78A Parent activity contract and quality-gate implementation, including the Expo Parent activity/story screens and app composition files required to render and exercise that flow.
2. Persist the immutable lesson pin, including exact lesson version/hash, age-band reference/version and activities, on each StoryRun input revision. The clean `dev` baseline does not contain these columns; add nullable JSONB snapshot/hash columns with a 1 MiB bound through Alembic migration `20261110_parent_lesson_pin`, after `20261110_parent_profile_story_context`. Preserve prior snapshots when artwork creates a new input revision.
3. Regenerate the workspace `pnpm-lock.yaml` for the Expo package manifest.
4. Carry the Rev78/Rev78A plans, approval record, feature context/decision/source/status updates and synthetic-only report/runtime/screenshots into FEAT-063.
5. Run the focused Parent activity tests, static checks and repository security validator. Do not claim a live post-fix Modal/API/UI acceptance: the one approved Rev78A inference was cancelled after 976.326 seconds before returning output; the dev lesson catalog had zero eligible entries; migration has not been applied to a real PostgreSQL database.
6. Create one conventional feature commit on `codex/feat063-parent-catalog-20261111`, push that branch, merge it into `dev` without rewriting history, run the security validator on the merged tree, and push `dev`. Preserve the dirty backup checkout and all unrelated work.

## Acceptance and explicit limits

- Catalog-first selection and three-draft fallback match the owner’s recorded direction; AI cannot rewrite catalog content, fallback remains a temporary reviewable draft, and hard backend safety/business gates remain fail-closed.
- A pinned run uses its stored immutable lesson snapshot and never substitutes a newer version. Migration graph/source checks must pass; no claim of a real database upgrade is made unless a disposable PostgreSQL database is available and explicitly used.
- Focused tests and static checks pass, or any unavailable/failed check is stated exactly in the closeout.
- The feature branch and `dev` remote refs are verified after publication. No force-push, deletion, video generation, extra Modal inference/deployment, secret or `.env` operation, Firebase identity operation, real-child data, or unrelated edits.
- SRS Rev60 remains unsigned and unchanged. The catalog-first discrepancy with its open no-preset activity text is carried as an open SRS reconciliation item.

## Exact implementation paths

- `apps/ui-mobile/App.tsx`
- `apps/ui-mobile/android/app/build.gradle`
- `apps/ui-mobile/android/app/src/main/AndroidManifest.xml`
- `apps/ui-mobile/android/app/src/main/java/com/sketch2life/mobile/MainActivity.kt` (remove obsolete native entry point)
- `apps/ui-mobile/android/app/src/main/java/com/sketch2life/mobile/MainApplication.kt` (remove obsolete native entry point)
- `apps/ui-mobile/android/app/src/main/java/com/sketch2life/parentexpo/`
- `apps/ui-mobile/android/app/src/main/res/values/strings.xml`
- `apps/ui-mobile/android/gradle.properties`
- `apps/ui-mobile/android/settings.gradle`
- `apps/ui-mobile/app.config.js`
- `apps/ui-mobile/app.json`
- `apps/ui-mobile/index.ts`
- `apps/ui-mobile/package.json`
- `apps/ui-mobile/src/parent/`
- `apps/ui-mobile/tests/storyDraft.test.ts`
- `pnpm-lock.yaml`
- `backend/alembic/versions/20261110_parent_lesson_pin.py`
- `backend/src/sketch2life/application/ports/parent_activity_catalog.py`
- `backend/src/sketch2life/application/ports/parent_story_runs.py`
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/src/sketch2life/application/services/parent_story_runs.py`
- `backend/src/sketch2life/contracts/schemas/lesson_library.py`
- `backend/src/sketch2life/contracts/schemas/modal_ai.py`
- `backend/src/sketch2life/contracts/schemas/parent_story_runs.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/infrastructure/lesson_library/parent_activity_catalog.py`
- `backend/src/sketch2life/infrastructure/lesson_library/service.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/tables.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py`
- `backend/tests/unit/test_parent_activity_suggestions.py`
- `backend/tests/unit/test_parent_activity_worker_contract.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/workloads.json`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-87_PARENT_FULL_API_UI_E2E_20261111/`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV78_PARENT_CATALOG_FIRST_ACTIVITY_SUGGESTIONS_20261111.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV78A_PARENT_ACTIVITY_GATE_REFINEMENT_20261111.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV78B_PARENT_CATALOG_PIN_AND_PUBLICATION_20261111.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `docs/context/SOURCE_REGISTER.md`

No path outside this manifest may be included in the feature commit.

## Publication authorization

The owner’s direct request authorizes the feature branch commit/push and merge into `dev`, followed by pushing `dev`. The local `dev` baseline contains 21 commits not yet on `origin/dev`; publication will include those existing commits as part of the fast-forward update. No history rewrite is authorized.

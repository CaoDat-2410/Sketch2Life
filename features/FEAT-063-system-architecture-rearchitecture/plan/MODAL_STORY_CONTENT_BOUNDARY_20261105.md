# Modal Parent story content and metadata boundary

**Plan revision:** 1  
**Status:** APPROVAL RECORDED / IN PROGRESS  
**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063  
**Worktree:** `codex/feat063-modal-backend-completion-20261103`

## Goal

Fix the Parent Modal story generation mismatch observed in the first parser-alignment run, while preserving the canonical public `sketch2life.story-revision.v1` contract and every backend/SRS validation rule.

## Basis and approval

The owner directed: “tiếp tục fix, đảm bảo đúng parser”. The previous approved plan revision 39 authorized and used one synthetic inference; its call was rejected with `SCENE_FIELDS_INVALID`. This separate plan records the next bounded implementation and one new verification call. It does not authorize retries within that call or video inference.

## Scope

1. Keep the public story output schema, FEAT-063 SRS v2.3-draft, backend `StoryRevisionDraftV1`, educational fact checks, adult-review gate, model identity/revision, API envelope, and business rules unchanged.
2. Change only the internal Parent story generation format. Ask Qwen for story-level text and five scenes of narrative content (`title`, `action`, `visual_prompt`, `narration`, `character_anchors`). Do not ask the model to emit scene indices or timing metadata.
3. Strictly parse the internal content JSON: reject duplicate keys, extra/missing keys, wrong types, blank/overlong text, invalid anchor lists, and any scene count other than five. Do not coerce, truncate, repair, or request another model output.
4. After internal content validation, deterministically assemble the unchanged public draft: five sequential indices; `start_ms` values 0, 6000, 12000, 18000, and 24000; each scene `duration_ms=6000`; total `duration_ms=30000`; existing version and language fields. This is application-owned metadata, not completion of missing model content.
5. Pass the assembled object through the existing strict `_parse_story_output`, backend `StoryRevisionDraftV1`, and butterfly lifecycle guard. The public parser remains authoritative and must not be weakened. Add only safe, fixed reason codes if needed to identify internal-content rejection; never log model text or prompts.
6. Extend focused local tests for the internal content contract, deterministic assembly, rejection cases, JSON-schema constraint, unchanged public parser rules, backend Pydantic compatibility, and butterfly fact validation.
7. Run focused tests, Ruff, Python compilation, and sensitive-data/diff review before deployment. Deploy only the FEAT-063 `dev` language/audio app and dispatch exactly one fresh synthetic Parent story call. The client wait cap is 300 seconds. No retry, duplicate, or other AI call.
8. Save intent before dispatch, persist call ID/result without raw story text, collect safe logs, stop the task-owned app, and verify stopped state with zero tasks. Preserve shared Modal Volumes.

## Explicit exclusions

No video, FLUX, VLM, SAM2, TTS, ASR, Teacher Deck, lesson suggestion, backend/API/domain/SRS/schema change, model or dependency pin change, real child/profile data, environment/secret edits, persistent scaling change, GPU snapshot, Volume deletion, commit, push, or merge. Do not dispatch if local checks fail. Do not make a second call if this call times out, is ambiguous, or returns invalid content.

## Acceptance criteria

- The internal constrained schema contains content fields only and is pinned to exactly five scenes.
- Valid internal output is assembled deterministically into the exact public contract and accepted by the unchanged worker parser, backend Pydantic model, and butterfly lifecycle check for the synthetic butterfly fixture.
- Invalid internal output fails closed without repair; existing public parser rejection tests continue to pass.
- Focused tests, Ruff, Python compilation, source allowlist review, and evidence privacy review pass before deployment.
- Exactly one fresh synthetic inference is dispatched and either returns a contract-valid story or records its terminal safe failure reason within the 300-second cap; no video is called.
- The task-owned Modal dev app is stopped and reports zero tasks after the call.
- Evidence contains no prompt, raw model output, child/profile data, token, or credential.

## Verification sequence

1. Confirm the first call's safe failure reason and stopped-app evidence; check the canonical SRS/backend contract and current worktree.
2. Add the internal content parser/schema and deterministic metadata builder; retain the public validation path.
3. Run focused tests, Ruff, `py_compile`, source diff/allowlist review, and evidence privacy scan.
4. Persist fresh synthetic dispatch intent, deploy the dev worker, dispatch exactly one call, and wait no longer than 300 seconds.
5. Save only safe result metadata/logs, stop the task-owned app, verify zero tasks, and update FEAT-063 records.

## Files in scope

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `features/FEAT-063-system-architecture-rearchitecture/plan/MODAL_STORY_CONTENT_BOUNDARY_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_STORY_CONTENT_BOUNDARY_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/modal_story_content_boundary_20261105/`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_modal_story_content_boundary_20261105.py`

Any necessary path outside this allowlist requires an amended plan and approval before implementation.

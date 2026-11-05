# Modal Parent story parser alignment

**Plan revision:** 2  
**Status:** APPROVED / IN PROGRESS  
**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063  
**Worktree:** `codex/feat063-modal-backend-completion-20261103`

## Goal

Make the Modal Parent `story.generate` worker produce and validate the existing `sketch2life.story-revision.v1` contract consistently, and identify any remaining rejection reason without storing or logging generated story text.

## Approved-by-owner request basis

The owner directed: ?ti?p t?c fix, ??m b?o ??ng parser? (continue fixing and ensure it matches the parser). This plan narrows that direction to the existing Parent story worker and one synthetic verification request.

## Scope

1. Preserve the FEAT-063 SRS v2.3-draft workflow, schema version, exact output fields, 5?15 scene range, 30?90 second duration, contiguous timeline, character anchors, adult review, and educational safety/fact checks. Do not weaken, silently coerce, truncate, or bypass validation. Do not change Qwen/model or dependency pins except for the one exact constrained-decoding package pin in item 2.
2. Add `lm-format-enforcer==0.10.11` to the story-only Modal image and apply a JSON Schema token constraint matching `StoryRevisionDraftV1` field names/types, required keys, no extra properties, string bounds, and list bounds. The constrained decoder is an output-format aid; all existing semantic, timeline, and factual checks remain authoritative.
3. Update only the Parent story prompt/generation call. Request the exact Vietnamese JSON contract and give the model clear, simple timeline instructions. Supply an explicit attention mask for the single unpadded prompt and clear sampling-only generation flags from a copied generation config while retaining greedy decoding. Do not alter Teacher Deck inference.
4. Make the worker parser align with backend `StoryRevisionDraftV1`: exact top-level/story/scene keys; JSON-only input; nonblank and bounded title/story/scene strings; 5?15 ordered scenes; valid integer timing and anchor bounds; contiguous timeline and exact total; existing butterfly lifecycle check. Normalize outer whitespace only as the backend contract explicitly does through `str_strip_whitespace=True`; perform no other coercion, truncation, or bypass. Keep the external safe failure code `MODAL_MODEL_OUTPUT_INVALID`. Internally distinguish safe fixed reason codes for JSON, shape, field, timeline, and education-fact failures. Log only the reason code, output byte/token count, and SHA-256; never log/store raw output, prompt, or child/profile data.
5. Add focused local tests for accepted contract output, each parser rejection category, exact contract bounds, prompt constraints, and the schema supplied to the constrained decoder. Cross-check the worker contract against the existing backend Pydantic contract; do not edit backend behavior or the SRS.
6. Run static checks and focused parser tests before deployment. Then deploy only the FEAT-063 dev language/audio app and dispatch exactly one fresh synthetic Parent story request with unique identifiers. Persist dispatch intent and returned Modal call ID before polling; cap client wait at 300 seconds. No video, no other AI workload, no duplicate call, and no retry for an unknown or invalid outcome.
7. After a terminal result or the 300-second bound, stop the task-owned language/audio app and verify it is stopped with zero tasks/containers. Retain shared model Volumes and checkpoints. Record test, deployment, call, timings, parser category, and shutdown evidence under this feature.

## Explicit exclusions

- No changes to canonical SRS, backend/API/domain rules, database, activity ordering, product workload enablement, model identity/revision, GPU fallback order, scale-to-zero settings, or Teacher Deck.
- No weakening/normalization of the strict story contract to make output pass. No model-output repair pass or second AI request.
- No video generation, FLUX, drawing VLM, SAM2, lesson suggestion, TTS, ASR, real child/profile data, secret/env edits, shared Volume deletion, commit, push, or merge.

## Acceptance criteria

- The worker-side parser enforces all structural, field-length, timeline, and factual rules already required by the backend contract/SRS. Invalid output remains rejected under the existing public worker error code.
- The constrained decoder is pinned and wired only into the Parent story worker; local tests confirm its schema aligns with backend field constraints without relaxing semantic/timeline checks.
- Focused local tests, Ruff, and Python compilation pass before deployment.
- At most one fresh synthetic story request is dispatched. It either returns a result accepted by the unchanged contract, or records a precise safe rejection reason / bounded runtime failure without retry.
- The task-owned Modal app is stopped after execution, with zero active tasks/containers; no video or unrelated call occurs.
- No prompt, raw model output, child/profile data, token, or credential is persisted in evidence.

## Verification sequence

1. Confirm the FEAT-063 canonical SRS, current backend `StoryRevisionDraftV1`, prior story latency evidence, worker contract, and existing worktree changes.
2. Add parser/schema unit tests and implement the allowed Parent worker changes.
3. Run focused tests, Ruff, `py_compile`, diff/allowlist review, and inspect all logs/evidence for sensitive content. Do not deploy if any local acceptance check fails.
4. Record a fresh synthetic dispatch intent and call ID before waiting. Poll only that call, with a 300-second hard cap.
5. Stop the dev app and verify no task-owned containers remain; then update the task report and FEAT-063 records.

## Files in scope

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py` (new)
- `features/FEAT-063-system-architecture-rearchitecture/plan/MODAL_STORY_PARSER_ALIGNMENT_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_STORY_PARSER_ALIGNMENT_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/modal_story_parser_alignment_20261105/`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_modal_story_parser_alignment_20261105.py` (new)

Any required path outside this allowlist stops implementation pending an updated plan and approval.


## Revision 2 note

This additive revision clarifies that outer-whitespace normalization must match the existing backend Pydantic contract (`str_strip_whitespace=True`). All output validation remains strict and no missing/invalid value is repaired.

# Plan Rev78A — Parent activity fallback quality-gate refinement

## Status

APPROVED under the project owner's direct instruction: “chạy lại đi, fix quality gate cho dễ qua hơn hoặc ấy”. This is a bounded operational refinement to Rev78; it does not change the catalog-first product behavior or the unsigned SRS.

## Problem

The first synthetic Qwen3.5 fallback produced three outdoor drafts, but several fields reached the old character limits mid-sentence. The service then required every prose field—including materials and observation notes—to end with sentence punctuation. This rejected concise list-like fields and made clipped output harder to distinguish from harmless fragments. The previous worker schema also demanded sentence punctuation at the old high field limits.

## Approved behavior and limits

1. Keep the Parent catalog-first flow and exactly-three-draft fallback unchanged.
2. Ease formatting requirements only for `materials_text` and `observation_notes`: permit concise phrases or list-like fragments without terminal punctuation.
3. Keep `objective`, `preparation_text`, `instructions_text`, and `safety_notes` sentence-complete. Lower their generation budgets and update the prompt to request one concise sentence or a small number of short steps.
4. Preserve the hard business and safety gates: age 36–120 months and exact band, outdoor activity, child choice/agency, exploration, adult supervision/support, explicit safety guidance, no unsafe actions, topic/drawing-context match, exactly three distinct suggestions, duplicate/catalog similarity checks, no contact PII, and Vietnamese Latin script.
5. Keep Modal JSON Schema compatible with LM Format Enforcer: do not combine a string `pattern` with `minLength` or `maxLength`; retain backend/worker parser length checks.
6. Align the backend worker response model, Modal schema, worker parser and application gate on the revised field limits and fragment rules.
7. Add focused tests proving concise materials/observation fragments can pass, while an incomplete core instruction/safety sentence and existing safety/business violations still fail.
8. After local verification, run at most one fresh synthetic fallback inference against the deployed Qwen3.5 Modal worker and pass that output through the actual application service. No video, real child, UI/device, extra inference, or automatic retry.
9. Record the exact model/revision, Modal call ID, elapsed time, gate result and limitations in the existing feature-local Rev78 evidence folder. Leave already-live baseline Modal apps running; do not inspect or change secrets or `.env`.

## Acceptance criteria

- AC1: Only formatting requirements for materials and observation notes are relaxed; their content remains subject to safety, context, language, PII and duplication checks.
- AC2: Core objective, preparation, instructions and safety fields remain bounded and sentence-complete; insufficient safety, outdoor, child-agency, adult-support, Montessori exploration, age, context, uniqueness or unsafe-action checks still fail closed.
- AC3: Worker prompt, JSON schema, parser and backend limits agree, and the schema does not combine `pattern` with length keywords.
- AC4: Focused tests cover accepted fragments and rejected incomplete/unsafe outputs; touched Python files pass Ruff and `py_compile`.
- AC5: At most one fresh synthetic Modal inference is recorded. A failure is diagnosed and reported without another inference.
- AC6: No video call, real-child data, UI/device run, unrelated edit, secret/`.env` change, commit or push occurs.

## Exact paths

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV78A_PARENT_ACTIVITY_GATE_REFINEMENT_20261111.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/src/sketch2life/contracts/schemas/modal_ai.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `backend/tests/unit/test_parent_activity_suggestions.py`
- `backend/tests/unit/test_parent_activity_worker_contract.py`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-87_PARENT_FULL_API_UI_E2E_20261111/runtime/` (new Rev78A artifacts only)
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-87_PARENT_FULL_API_UI_E2E_20261111/API_PARENT_E2E_REPORT.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`

No path outside this list may be changed for this task. Preserve unrelated existing work in all listed files.

## Verification

- Run the Parent activity service and Modal worker contract unit tests.
- Run Ruff and Python compilation on the touched source/tests.
- If local checks pass, deploy only the language/audio Modal app required for this worker, confirm zero active calls immediately before deployment, and make one synthetic invocation through the existing Rev78 retest harness. Send the returned worker result to the real application service gate in that harness.
- Record whether the fresh inference passes. Do not retry if it fails.

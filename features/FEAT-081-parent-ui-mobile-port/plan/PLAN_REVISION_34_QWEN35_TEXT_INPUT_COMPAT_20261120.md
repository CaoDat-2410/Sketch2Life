# FEAT-081 — Plan Revision 34: Qwen3.5 text input compatibility

- **Status:** APPROVED under the owner's direct, continuing instruction on 2026-11-20: “fix tiếp đi, nào nó chạy đc hết thig dùng”.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 current working SRS. This operational fix does not change product requirements.
- **Relationship:** bounded amendment after Revision 33's one activity attempt ended in a terminal worker error. Revision 34 grants at most two additional, distinct UI-driven activity attempts, only after the specific code fix below; it does not authorize repeating the failed build/request.

## 1. Goal

Make Qwen3.5-9B's text-only Parent activity workload accept the text processor inputs, preserve the existing catalog-first response contract, and continue the real Android Parent flow if the activity stage succeeds.

## 2. Failure evidence

- UI-driven Modal call `fc-01M7V6B8Z31YNHR5SPSERRMTHE`, initiated at `2026-11-20T00:40:08Z`, reached the deployed text-only `Qwen3_5ForCausalLM` worker.
- Runtime facts: L4-class GPU (compute capability 8.6), pinned Qwen3.5-9B revision unchanged; model load 16,886 ms, prompt encoding 58 ms, constrained-decoder setup 3,804 ms.
- Generation failed in 2 ms before producing tokens. Transformers rejected processor metadata `mm_token_type_ids` because `Qwen3_5ForCausalLM.generate()` does not accept that multimodal-only keyword. Modal emitted terminal `worker_failed` / `WORKER_VALUE_ERROR`; backend returned `MODAL_WORKER_FAILED_TERMINAL`. No activity response/receipt was persisted.
- Sanitized worker logs and before/after screenshots are stored beside this plan under `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`.

## 3. Implementation and acceptance criteria

### M1 — filter text-processor metadata

- Add one small helper that turns the processor `BatchFeature` into generation kwargs for the pinned text-only model, removing `mm_token_type_ids` while preserving `input_ids`, `attention_mask`, and all other actual text-generation inputs.
- Apply it consistently to text-only Qwen generation calls (Parent activities, Parent topic-subject suggestions, Parent story, Teacher deck/lesson text, and decoder probes) so the same incompatibility cannot reappear in adjacent workloads.
- Do not change prompt content, checkpoint ID/revision, catalog ranking, schema, age/safety/quality gates, output lengths, or generation sampling behavior.
- Add focused unit/AST coverage: multimodal metadata is removed; text inputs remain unchanged; every text-only `model.generate` call uses the helper.

### M2 — validate and deploy

- Run Python compilation and focused offline worker/workload tests.
- Redeploy only `sketch2life-srs23-language-audio-dev` from this worktree; rerun CPU decoder readiness without loading checkpoint weights or acquiring GPU.
- Verify API health and the existing emulator session before any inference.

### M3 — bounded real verification

- Make one real Android UI-driven activity request after the fix, with an 8-minute wall-clock cap. Do not call the worker directly or replay any previous run.
- If it reaches a new, fast terminal worker error with an actionable cause, permit one additional UI-driven activity request only after a distinct code fix and focused tests. Maximum: **two new activity requests under Rev34**, stop immediately after the first valid response or after the second failure. Never retry the same code/input after a timeout.
- If activity succeeds: select and persist one activity through the UI, make one story-generation request and complete the adult review/confirmation. A single silent video request remains conditional on all earlier gates passing and the existing Rev25 allowance; video is not required to diagnose this text input contract.
- Preserve synthetic-only use, adult confirmation, catalog-first activity selection and all existing quality/safety checks. No quota/payment mutation or bypass, direct DB edits, fixture/mock, account/profile creation, drawing inference, secrets or `.env` edits, migration, commit, push or unrelated-service shutdown.
- Keep emulator online. After evidence capture, stop only services started/owned for this task.


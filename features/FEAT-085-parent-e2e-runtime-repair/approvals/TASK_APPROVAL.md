# FEAT-085 task approval

## Plan Rev1 — Parent real E2E runtime repair

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation (2026-11-23): fix the unresolved Parent runtime and rerun the full end-to-end flow.
- **Approved scope:** The sequence, boundaries, focused source areas, synthetic-only data, real Expo/Backend/Modal execution, and evidence requirements in plan/PLAN_REV1_PARENT_E2E_RUNTIME_REPAIR_20261123.md.
- **Runtime authorization:** Start/restart the Android emulator and Metro; use existing synthetic Parent credentials privately from the ignored root .env; use healthy local Docker services; call real Modal AI/video workloads as needed, minimizing retries; create only synthetic data if a required record is absent.
- **Safety constraints:** No real-child data; never expose credentials/tokens; do not delete existing seed accounts or unrelated data; do not bypass auth, consent, schema, safety, or video admission; do not stop Docker services that were already running.
- **Delivery constraints:** No commit or push requested.

## Addendum 1 — current-branch backend runtime

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation (2026-11-23) to fix the blockers and complete the real Parent E2E.
- **Approved scope:** Build and run the backend from the active `feature/fe-mobile-remediation` worktree on an unused local port with a fresh isolated synthetic database and storage volumes. Apply this branch's current Alembic heads to that fresh DB. Update only the API URL value in the existing root `.env` after the new backend passes health and route checks.
- **Preservation:** Do not stop/recreate existing API containers, alter older database volumes, print or replace credential values, create extra `.env` files, or bypass identity/consent/schema/safety/admission gates.

## Addendum 2 — use the newly selected Modal workspace

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction on 2026-11-23: “chạy đi, vừa đổi modal workspace”, followed by authorization for full runtime access and instruction not to use Computer Use.
- **Approved scope:** Use the selected local Modal profile `hieuptse184252` for this task. The project `.env` and running FEAT-085 API currently resolve to `anhkhoa14155`, whose workspace returns `workspace ... is disabled`; the selected profile has no deployed apps or model volumes. Provision only the resources required to complete this Parent E2E in the selected `dev` environment: model/scratch volumes, the language/audio app for Qwen3.8 Parent activities/story, and the video app for the pinned LTX-2.5 candidate. Stage the pinned checkpoints through the existing Modal download functions and use the existing `huggingface-secret`; do not use FLUX or send narration.
- **Runtime handling:** Keep the existing root `.env` credential values unchanged. Pass the selected profile credentials only to the task runtime in memory, without printing or persisting them. Recreate only the isolated FEAT-085 API container if needed to use that profile. Do not recreate/stop unrelated services.
- **E2E boundaries:** Resume the existing synthetic run through the Android UI. Make at most one new request for each workload after the current deployment is ready. Keep authentication, consent, schemas, parser, quality, safety, and video admission gates enabled; no quota/payment bypass. Do not delete the run or seed account. Capture sanitized logs and UI evidence in this feature folder. No commit or push.

## Addendum 3 — repair the current activity output failure

- **Status:** APPROVED
- **Approver:** Project owner, standing direct instruction in this conversation to fix runtime bugs and continue until a video is generated, most recently “thử lại đi” (2026-11-23).
- **Observed failure:** The single activity inference on the newly selected workspace completed without timeout (Qwen3.8-27B-FP8, 1,949 output tokens, 356,234 ms), but the worker rejected only `fallback_activities[2].preparation_text` with safe reason `dangling_word`; API request `e9c0e399-88be-4fa4-b8ed-dcb53a246f22`, Modal call `fc-01M84DC0GTJ3P44TRAJ2C0WHD3`, run `c8ab4140-739e-496f-8b11-1c58e4a857a3`.
- **Approved scope:** Make a narrow prompt-only repair to require a short, complete preparation sentence that ends with its actual action/object rather than a dangling Vietnamese connector; add focused prompt-contract coverage; run the relevant offline checks; deploy only the language/audio app; then make one fresh Parent UI activity request for this existing synthetic run.
- **Preserved gates:** Do not weaken parser completeness, output schema, backend quality, outdoor setting, age, child-agency, adult-support, safety, privacy, authorization, or admission rules. Do not repeat drawing or delete/reseed the run. No new story/video request until the activity set is accepted. No commit or push.

## Addendum 4 — align child-agency recognition with explicit inquiry actions

- **Status:** APPROVED
- **Approver:** Project owner, standing direct instruction to fix the Parent E2E until video works, reiterated in the current conversation with “thử lại đi”.
- **Observed failure:** The second real activity request completed Qwen3.8 generation and worker parsing (1,555 tokens; 416,357 ms inference; 4,884-byte JSON), then the backend returned `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` / `CHILD_AGENCY_NOT_EXPLICIT`. Request `82a93aeb-acdf-4e41-b67b-db7cee089d20`, Modal call `fc-01M84E2W0BZ61DN3H5TC0JFAC7`, run `c8ab4140-739e-496f-8b11-1c58e4a857a3`. Generated text is not retained, so this finding does not establish whether wording was absent or merely outside the matcher.
- **Approved scope:** Extend the backend matcher only to recognize explicit affirmative child-subject inquiry actions already covered by the separate exploration vocabulary (look closely, follow, listen, notice/discover, count, record, ask questions, and equivalent current markers). Require an explicit child actor and reject negated actions. Align the Qwen prompt with the accepted examples. Add focused positive and negative tests; run relevant offline checks; rebuild only the isolated FEAT-085 API and redeploy only the language/audio Modal app; then make one fresh activity request through the Android UI for the existing synthetic run. Update the task-owned API launcher to require the selected Modal profile and pass its credentials from local Modal CLI config into Compose memory only, without changing the shared `.env` or printing values. If accepted, continue the normal story review and video path under existing gates.
- **Preserved gates:** Do not infer the unseen generated text or weaken child agency, exploration, outdoor setting, adult support, age, context, safety, privacy, authorization, schema, parser, or video admission. Do not repeat drawing, delete/reseed the run, issue duplicate requests, bypass quota/admission, or commit/push. If another predicate fails, record its safe diagnostic before any further repair.

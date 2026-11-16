# Plan Rev67 — Parent Android profile, consent, and AI workflow

- **Status:** APPROVED for the expanded scope below.
- **Authority:** FEAT-063 canonical working SRS v2.7-draft, Rev60, unsigned, plus its Data Table Register. Relevant targets include §§5.1, 7.2 (FR-P-02/03/04/06/07/08/10/11), Parent data ownership/context in DTR §5.3 and story ownership/input snapshots in DTR §5.5. Older Parent mockups/feature contexts are historical implementation evidence only.
- **Owner authorization:** direct request: “fix tiếp luồng parent … nối API vào UI”, followed by “merge dev”; scope clarification: “Làm luôn profile, consent và migration”; owner then confirmed “duyệt, bỏ qua cái đó đi” when asked about consent policy approval.
- **Baseline:** isolated worktree on `codex/feat063-parent-flow-fix`, based on `800c8e9f19ed7fac416901ab24d86e07dbfd555b`. `origin/dev` is an ancestor of the feature branch; no duplicate commits exist after the merge base.

## Problem

The authenticated Parent Android surface is only an AI demo: it uses an in-app digital canvas, requires manually entered age, discards the adult’s story idea, hard-codes revisions, has no Parent-owned child profile or data-authorization API, does not persist a StoryRun/context snapshot, renders raw story JSON, and reduces terminal Modal drawing errors to a generic code.

## Scope

1. Replace the WebView drawing canvas with physical-paper capture from Android camera or photo library using `react-native-image-picker`; resize/compress before base64 transfer, preview/retake, handle cancel/error, and keep image bytes out of logs.
2. Add Parent-owned profile APIs and UI: list/create/read/update/archive a child profile; profile updates create immutable revisions. Persist age in months (36–120), display name, and bounded interests summary. Do not store date of birth, infer age bands, join to Teacher profiles, or send display name to AI.
3. Add versioned `parent.data_authorizations` acceptance and revoke. The API returns the currently configured purpose, policy version and consent text; profile creation and new runs require explicit acceptance for that exact policy version. Read the policy from the single repository-root `.env` through backend settings and Compose. If its version or text is absent, fail closed. Store only policy/text hashes and consent metadata, never copy the full consent text into audit logs. The owner’s approval is recorded; the text/version remain runtime-configurable rather than being invented as a legal policy in source.
4. Create authenticated Parent StoryRuns from an owned profile and active authorization. Persist the selected profile revision and minimal, versioned, adult-confirmed context in `story.run_inputs` according to the DTR; preserve drawing asset refs/hash/media provenance using the existing private object-storage adapter and `core.asset_metadata` owner scope. AI requests resolve profile/context from the server-owned run, not client-supplied age or profile facts.
5. Extend Parent drawing analysis and story APIs to require/resolve the run, enforce current ownership/authorization, and persist understanding/story revisions using existing Story tables. Adult subject correction creates a new interpretation revision. Story rewrites remain capped at three and no direct scene editing is introduced. Persist adult script confirmation before any future video admission; video itself remains excluded.
6. Extend the additive PostgreSQL migration and persistence metadata for `parent.child_profiles`, `parent.profile_revisions`, `parent.data_authorizations`, and DTR-aligned `story.run_inputs` context fields. Preserve historical/demo rows and never fabricate consent during migration. Keep age bands unset until the owner-defined catalog is available.
7. Render the existing `sketch2life.story-revision.v1` result as a readable title, opening/middle/ending, and 5–15 numbered scenes. Do not expose visual prompts or raw JSON as product copy. Show the run’s saved state rather than a local-only confirmation.
8. Preserve the optional Parent line-sketch toggle; when off it dispatches no request and sends no profile, run, age, idea, photo or artwork. Preserve no-auto-retry behavior for expensive or outcome-unknown requests.
9. Preserve safe Modal worker terminal codes in structured logs/API error responses when they match the existing safe-code grammar; do not expose prompt, generated text, image/audio bytes, secrets, or provider internals.
10. Add a versioned Parent API contract and update FEAT-063 context/decision/source/status/evidence records. After implementation, run only non-test static checks (mobile TypeScript typecheck, Python compile/lint for touched Python, `git diff --check`, and repository security validation before commit). No test suite, synthetic Firebase account, live Modal inference, video call, or Docker lifecycle operation is included.
11. Review the feature history and integrate it into local `dev` only after implementation and commit. Do not push.

## Explicit limits and unresolved requirements

- No video generation or video pipeline changes; no live Modal calls or model/timeout changes.
- No voice recording/Whisper integration in this slice; adult text idea is supported.
- No Teacher profile linkage/profile-share grants, cross-organization sharing, profile context-entry/support-needs CRUD, or Parent activity catalogue behavior. Parent activities remain after video; the no-preset activity policy remains open.
- Age bands are not defined in the SRS; use exact `age_months` and keep the band reference/version nullable.
- Existing AI calls remain synchronous. Do not claim durable AI job polling/reconciliation or full product workflow completion beyond the implemented boundary.
- No Firebase Storage/Firestore/Realtime Database; private drawing assets use the existing MinIO/S3-compatible backend only.
- No credentials, `.env`, seed accounts, or real child data in the repository/evidence.

## Acceptance criteria

- Parent can create/select/update/archive an owned child profile after explicitly accepting the configured consent policy; a consent revoke immediately blocks new runs and AI dispatch for that profile.
- The profile stores only age in months (36–120), display name and bounded interests summary; revisions are immutable and ownership checks prevent cross-account access.
- A Parent can resume the account's active StoryRun after reopening the app; status and saved story/understanding are read from backend persistence.
- Parent can create a run that pins the profile revision. The backend stores a bounded, versioned context snapshot and drawing asset lineage in Story/Core records, and AI requests read it from that run.
- Parent can take/select a physical drawing, preview/replace it, submit valid JPEG/PNG, confirm the proposed subject, and generate/review a structured story draft. The backend rejects a missing/stale run, profile, consent or revision.
- Adult script confirmation is persisted against the story revision. No video request is sent.
- Optional line sketch is only requested when enabled and remains independent of the selected child/profile/run.
- API errors surface a safe message, code and request ID; an unknown timeout never triggers an automatic duplicate request.
- Static checks pass. Repository security validator passes before commit. Feature commits are integrated by fast-forward into local `dev`; remote `origin/dev` is unchanged.

## Allowed implementation files

- `apps/mobile/package.json`
- `apps/mobile/android/app/build.gradle`
- `pnpm-lock.yaml`
- `apps/mobile/src/features/parent/ParentWorkflowScreen.tsx`
- `apps/mobile/src/infrastructure/api/parentWorkflowApi.ts`
- `backend/src/sketch2life/contracts/schemas/modal_ai.py`
- `backend/src/sketch2life/contracts/schemas/parent_profiles.py` (new)
- `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` (new)
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py` (new)
- `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` (new)
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_models.py` (new)
- `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py` (new)
- `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` (new)
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/tables.py`
- `backend/src/sketch2life/application/ports/parent_profiles.py` (new)
- `backend/src/sketch2life/application/ports/parent_story_runs.py` (new)
- `backend/src/sketch2life/application/services/parent_profiles.py` (new)
- `backend/src/sketch2life/application/services/parent_story_runs.py` (new)
- `backend/src/sketch2life/domain/parent_profiles.py` (new)
- `backend/alembic/env.py`
- One new additive migration under `backend/alembic/versions/`.
- Root `.env.example` and `compose.yaml` (only the non-secret consent-policy environment mapping).
- One versioned Parent API contract under FEAT-063 `artifacts/`.
- This plan, `approvals/TASK_APPROVAL.md`, and FEAT-063 context/decision/source/status/evidence records.

No other implementation paths are approved by this plan.

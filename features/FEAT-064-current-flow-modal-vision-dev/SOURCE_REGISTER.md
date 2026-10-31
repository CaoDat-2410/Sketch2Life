# FEAT-064 source register

## T2B/T3 owner decision record — 2026-11-01

- Owner decision ballot: the user's T2B/T3 worksheet in the conversation dated 2026-11-01; exact outcomes are recorded in `DECISIONS.md` D-10–D-12.
- Documentation/publication plan: `plan/PLAN_REV2_OWNER_DECISION_RECORD_20261101.md`, SHA-256 `DE455C77CFB687086A01194E628AB00EEC9E851C3E9258915561D4EE186916A2`.
- T2B design plan: `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_20261101.md`, SHA-256 `781A561AEC08BF0990AA18CBDBD27DB7CEB84CB23EA3CDD5ABB483A6A10D83C7`.
- T3 design plan: `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_20261101.md`, SHA-256 `D948F8DCAB9FDCF0EACBF3B0D4DB5C88914A6A17BC61D7001E1C3B1C28D61DA2`.
- Contract baseline: `evidence/T0_CONTRACT_FREEZE_20261031.md` §§3–5 and `plan/PLAN.md` revision 6. The baseline explicitly treats these as proposed design until task-specific approval.
- Source facts checked for A3: `backend/src/sketch2life/application/ports/vision_analysis.py` (`ContextDecision.context_revision: int`); `backend/src/sketch2life/domain/vision_context.py` (integer revision equality checks and existing typed context digest); `backend/src/sketch2life/application/services/vision_analysis.py` (revision equality checks and typed digest stale check). No ordered comparison was found in the reviewed paths.
- Source facts checked for T3: `backend/src/sketch2life/infrastructure/persistence/be1_models.py` (session JSON configuration and managed profile age); `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py`; `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`; `backend/src/sketch2life/contracts/schemas/be1_runtime.py`; `apps/child-ui/app/index.tsx`; `apps/child-ui/src/services/sessionClient.ts`; T3's closed future allowlist is in plan §1.
- Branch baseline: remote `feature/feat063-be-foundation` at `3ca9c1593d4a0e7d449a65ef08ff33d5c0a5b269`. The reported `578f3e5e` was not a local Git object and `git fetch origin 578f3e5e` returned “couldn't find remote ref”.
- B8 source gate: the original T3 §1 allowlist referenced by the owner ballot is absent from this branch and the related refs searched; the new T3 plan intentionally authorizes no source/test paths until the exact list is restored or explicitly approved.
- Evidence and publication limits: `evidence/OWNER_DECISIONS_T2B_T3_20261101.md`. No implementation, tests, migration or runtime action is claimed.

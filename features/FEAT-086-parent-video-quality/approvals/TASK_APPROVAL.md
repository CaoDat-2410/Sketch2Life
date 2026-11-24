# FEAT-086 task approval

## Plan Rev1 — Parent story/video quality repair

- **Status:** APPROVED
- **Approver:** Project owner, direct request on 2026-11-24: improve the returned story JSON and video generation, use a source that looks like a child's drawing, remove text beneath the video, and investigate a suitable LTX repository/skill.
- **Approval basis:** The owner's direct instruction to fix these points authorizes the scoped implementation and verification in Plan Rev1. No separate approval is inferred for unrelated product changes.
- **Plan SHA-256:** `69EFA4C9C91BE60F8ABC657713738AE43322A6EB11E16F9F148CE3CFE5564307`
- **Approved scope:** Exact implementation paths, milestones, acceptance criteria, and limits in `plan/PLAN_REV1_PARENT_VIDEO_QUALITY.md`.
- **Runtime authorization:** Run focused offline tests. If the current local backend and selected Modal profile are available, run at most one real synthetic Parent story/video validation using the existing FEAT-061 crayon asset. Use the existing hard gates; do not retry, create real-child data, or delete/overwrite existing records.
- **Preservation:** Keep the existing JSON keys and story-review gate. Do not alter SRS requirements, quota/payment, auth, consent, safety, DB schema, or unrelated files. Preserve all pre-existing worktree changes.
- **Delivery:** No commit or push requested.

## Plan Rev2 — Detailed LTX scene prompts

- **Status:** APPROVED
- **Approver:** Project owner, direct follow-up request on 2026-11-24: research established AI-video prompting practice and make the scene prompt more detailed and clear about how to render the video.
- **Approval basis:** The direct request authorizes the bounded prompt research, Rev2 implementation, and focused verification. The existing Rev1 authorization for at most one real synthetic candidate remains conditional on runtime availability; no new inference is authorized if Docker/Modal status remains unreachable.
- **Plan SHA-256:** `5D239B9BE4F495FE9F1D58A05595F5915E35F0136F6E676517377B4D2EF52531`
- **Approved scope:** Exact files and acceptance criteria in `plan/PLAN_REV2_DETAILED_LTX_SCENE_PROMPTS.md`.
- **Preservation:** Keep public story schema version/keys, adult approval, all current gates, and no extra conditioning image. Backend public story schema already supports 900 characters; align its internal video adapter/worker plan limit to that maximum. Do not alter public API/SRS.
- **Delivery:** No commit or push requested.

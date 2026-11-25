# Task approval

- Status: APPROVED
- Approver: Product owner (explicit chat approval, 2026-11-25: "Duyệt, O8 dùng local")
- Plan revision: Rev 2 with Amendment A — `plan/PLAN_REV2_PARENT_VIDEO_MODAL_PIPELINE.md`
- Approved scope: milestones M0–M11 of Rev 2 as written, with the values proposed in the plan (age table section 6, role scoring weights
  section 5, GPU budget section 13: at most 40 scene renders and 12 full videos), decision D7 (keep T-1a, retire the candidate path after M10),
  and O8 resolved as **local notifications only** (no server push, no stored push token).
- Answered by the owner: O1 (gated access granted), O3 (narration optional, captions exact), O6 (`expo-notifications` yes), O7 (device storage).
- Prerequisite still owned by the owner: P1 — a Hugging Face read token stored as a Modal Secret (needed before the FLUX download job in M5).
- Not approved: any production release, real-child data, a third GPU container, server push, commit/push to a remote.
- Plan changes after this point need a new revision and a new approval.

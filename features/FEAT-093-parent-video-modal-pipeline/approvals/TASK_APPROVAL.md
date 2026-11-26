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
- Amendment B (SRS BR-24 alignment: 30–90 s, 5–15 scenes, voice and captions always in the file, age table 5/7/9 scenes) approved by the owner
  on 2026-11-25 ("fix theo srs"). Recorded in plan section 16.
- Amendment C (`plan/PLAN_AMENDMENT_C_SPEED_AND_RELIABILITY.md`): instructed by the owner in chat on 2026-11-26: "fix cả cái này đi, sao lại có
  cái rule cố định cho 1 loại thế này? bỏ đi và cải thiện cái tạo vid cho bớt lỗi, chạy nhanh hơn; thử nén kv cache, giới hạn context, bật
  speculative decoding/mtp, kiểm tra định dạng lượng tử hóa xem, nói chung là kiếm cách cho nó nhanh hơn […] fix cái vid và chuyện lại đi, đảm
  bảo gen ra hợp lý, chuyên nghiệp, hạn chế khả năng failed" (spelling normalised). The numeric limits in the amendment (retry counts, GPU
  budget, 3x adoption threshold) are the implementer's proposal and were not separately confirmed.
- Amendment D (`plan/PLAN_AMENDMENT_D_FAILURE_AUDIT.md`): instructed by the owner in chat on 2026-11-26: "thử rà lại hết 1 lần cái tạo vid,
  tạo câu chuyện, hoạt động đi, sài vllm, mấy cái như trên để tối ưu thời gian hết đi, ngoài ra thì rà lại, cái nào có thể gây lỗi, thì sửa
  luôn 1 lần đi, rồi test lại" (spelling normalised).

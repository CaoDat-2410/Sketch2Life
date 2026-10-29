# FEAT-064 evidence index

- `notes/SOURCE_REVIEW_20261029.md`: baseline, chỉ đạo owner, nguồn và điểm chặn đã đọc.
- Plan, contract outline và owner path map là DRAFT, không phải implementation evidence.
- `notes/PLAN_REVIEW_AND_CHECKS_20261029.md`: hai review draft, các sửa material và static checks thực tế. Skeleton/security đạt; harness chung còn lỗi paths FEAT-043/063, không lỗi FEAT-064 được báo. Chưa có application/DB/provider test mới.
- `notes/PLAN_REV1_REVIEWED_20261029.md`: bản rev1 nguyên bytes mà Claude review, superseded; không dùng để cấp approval rev2.
- `notes/CLAUDE_PLAN_REVIEW_REV2_20261029.md`: verdict NEEDS_REVISION của rev1, source verification, disposition F1–F7 và checks cho rev2. Chưa có Claude PASS hoặc owner approval cho rev2.
- `notes/PLAN_REV2_REVIEWED_20261029.md`: bản rev2 nguyên bytes mà Claude review; đã superseded bởi rev3.
- `notes/CLAUDE_PLAN_REVIEW_REV3_20261029.md`: review rev2, disposition và verification của rev3; không phải runtime evidence hay task approval.
- `notes/PLAN_REV3_REVIEWED_20261029.md` và `notes/CLAUDE_PLAN_REVIEW_REV4_20261029.md`: bản rev3 được review và disposition của rev4; review không thay approval.
- `notes/CLAUDE_REVIEW_REV4_PASS_20261029.md`: Claude PASS rev4 và P3-C đưa vào T0; cần phân biệt absence ledger sau DB restore với bằng chứng chưa gửi.
- `notes/PLAN_REV4_REVIEWED_20261029.md` và `notes/CLAUDE_PLAN_REVIEW_REV5_20261029.md`: bản rev4 đã review và disposition rev5 theo OD-3=B; chưa có review rev5.
- `notes/PLAN_REV5_REVIEWED_20261029.md` và `notes/CLAUDE_PLAN_REVIEW_REV6_20261029.md`: bản rev5 được Claude review và sửa P3 ở rev6. Chưa có review rev6.
- `notes/CLAUDE_REVIEW_REV6_PASS_20261029.md`: Claude review đúng rev6, PLAN_REVIEW_PASS, không cấp task approval.
- raw/screenshots/metrics được scaffold cho evidence sau này, hiện chưa có live/visual approval.

Khi triển khai, lưu evidence theo task/AC: source/render/admission; identity/eligibility; lifecycle/dedup/race/restart; scoped UI; fresh live-cap và shutdown. Không đưa secret, `.env`, device key, raw provider body hoặc real child data vào Git. Receipt/budget FEAT-061 cũ giữ nguyên.

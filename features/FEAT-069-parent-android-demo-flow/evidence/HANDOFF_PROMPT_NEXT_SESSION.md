# Prompt bàn giao sang phiên mới — Parent Android demo FEAT-069

Bạn tiếp tục công việc Sketch2Life từ trạng thái hiện tại. Đọc hết prompt này trước khi sửa file.

## Mục tiêu và quyết định của chủ dự án

Chủ dự án yêu cầu chỉ tập trung vào luồng Parent Mobile để tránh trộn với các phần khác. Giữ mock data trong ứng dụng để có demo cho tới khi ghép API, nhưng gom dữ liệu và hành vi demo vào một boundary để sau này thay adapter thuận tiện. Người dùng đã yêu cầu triển khai phạm vi Parent Android demo.

Không triển khai backend/API, Firebase, tài khoản thật, dịch vụ AI/provider, native camera/gallery/microphone, upload thật, thông báo thật, quota billing hay phát video thật trong phạm vi này. Không commit, push hoặc deploy. Không chạy tests/builds/device launch theo phê duyệt hiện có; chỉ làm nếu chủ dự án yêu cầu và phê duyệt rõ ở lượt mới.

## Worktree và nhánh bắt buộc

- Worktree làm việc: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation
- Branch: feature/fe-ui-full-remediation
- Repo chính: F:/Github/Sketch2Life, branch feature/feat063-m2-parent-teacher-foundation. Không chuyển implementation sang repo chính.
- FEAT-069 và apps/mobile đã được xác minh nằm trong worktree trên; các thư mục tương ứng không nằm trong repo chính.
- Có worktree khác tên fe-ui-web-remediation. Không sửa worktree đó khi xử lý phạm vi mobile này.

Luôn chạy git status từ worktree đích, xác nhận branch trước khi làm. Giữ nguyên các thay đổi chưa commit có sẵn, đặc biệt FEAT-036, FEAT-067, FEAT-068, apps/parent-ui, apps/shared, approvals/TASK_APPROVAL.md và các ghi chú Parent Web. Chúng là công việc ngoài phạm vi Parent Android hiện tại; không reset, checkout, dọn hoặc ghi đè chúng.

## SRS và governance

- Đọc docs/context/SRS_AUTHORITY.md trước khi thay đổi hoặc kết luận yêu cầu sản phẩm.
- Canonical working SRS: features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5.
- SRS vẫn là draft, chưa có owner sign-off. Không dùng SRS cũ hoặc feature context cũ làm yêu cầu hiện hành.
- Đọc features/FEAT-069-parent-android-demo-flow/CONTEXT.md, plan/PLAN.md, DECISIONS.md, approvals/TASK_APPROVAL.md, status/STATUS.md và evidence/IMPLEMENTATION_NOTE.md.
- FEAT-069 Plan revision 1 đã được phê duyệt. SHA-256 phải tiếp tục khớp A4AE73D60354453BD8C6C42FE61C62557908DA9A3B2C510A118F626D798887DC. Không sửa plan đã duyệt nếu chưa có yêu cầu/phê duyệt mới.
- SRS-UI-01 trong FEAT-066 xác nhận trước đây apps/mobile/src/app/AppRoot.tsx chỉ mount FixtureFlowScreen; FEAT-069 đã xử lý bằng Parent demo mặc định và giữ fixture lab riêng.
- Chính sách account creation và no-preset activity catalog còn mở. Registration chỉ là UI demo theo yêu cầu chủ dự án; không suy diễn thành policy tài khoản thật. Không thêm hoạt động trước khi video sẵn sàng. apps/ui-mobile chỉ là reference, không thay thế luồng Parent Android.

## Đã triển khai trong FEAT-069

Các file mới chính:

- apps/mobile/src/features/parent-flow/parentWorkflowPort.ts — typed screen/state/command/query boundary.
- apps/mobile/src/features/parent-flow/ParentFlowScreen.tsx — UI Parent tiếng Việt, responsive phone/tablet.
- apps/mobile/src/features/parent-flow/index.ts.
- apps/mobile/src/infrastructure/demo/ParentDemoWorkflowAdapter.ts — state machine và hành vi demo.
- apps/mobile/src/infrastructure/demo/parentDemoFixtures.ts — hồ sơ, transcript/subject mặc định, story, guide, context, hoạt động, reminder và quota tổng hợp.
- apps/mobile/src/infrastructure/demo/legacyFixtureFixtures.ts — fixture contracts của luồng fixture cũ, tách khỏi Parent demo.

Các file được cập nhật:

- apps/mobile/src/app/AppRoot.tsx — mở Parent demo mặc định; FixtureFlowScreen còn ở route Fixture lab.
- apps/mobile/src/app/composition/dependencies.ts — chọn ParentDemoWorkflowAdapter qua composition; apiClient null trong demo.
- apps/mobile/src/features/fixture/fixtureFlow.ts — lấy contract cũ từ module fixture riêng.
- apps/mobile/README.md — mô tả boundary và cấu trúc mới.

FEAT-069 records:

- CONTEXT.md, DECISIONS.md, approvals/TASK_APPROVAL.md, status/STATUS.md.
- plan/PLAN.md giữ nguyên nội dung/hash đã duyệt.
- evidence/IMPLEMENTATION_NOTE.md và evidence/HANDOFF_PROMPT_NEXT_SESSION.md ghi phạm vi, kết quả và giới hạn.

Luồng demo hiện có: sign-in, registration/recovery demo, chọn/tạo hồ sơ, một run đang hoạt động, ý tưởng chữ/voice placeholder, guide tùy chọn, chọn tranh camera/gallery giả lập, mô phỏng upload ngắt/tiếp tục, rà soát transcript/chủ thể/context, tối đa 3 lần rewrite story, xác nhận script, trạng thái video lỗi/thử lại và playback placeholder, tối đa 2 lần yêu cầu thay thế, hoạt động sau video, lịch sử/mở/xóa, quota, reminder, hủy/hoàn tất run và sign-out/reset.

Mock content và trạng thái Parent được đưa qua ParentWorkflowPort/ParentWorkflowSnapshot. ParentFlowScreen không import trực tiếp fixture. Điểm thay adapter nằm ở apps/mobile/src/app/composition/dependencies.ts và app composition. Legacy fixture contracts tách riêng. State demo chỉ nằm trong bộ nhớ; reload khởi tạo demo mới.

Responsive UI dùng breakpoint 760 px, giới hạn chiều rộng tablet, xếp dọc trên điện thoại, wrap card/grid và touch target tối thiểu 44 px. Đây là source implementation, chưa xác minh trên thiết bị.

## Xác minh đã làm và giới hạn

- Đã chạy git diff --check trong đúng worktree; không còn lỗi whitespace.
- Không chạy automated tests, build, emulator/device launch hoặc visual runtime QA do phạm vi approval hiện hành loại trừ các việc đó.
- Không có API, Firebase, provider hay native media operation.
- Không commit/push/deploy.
- FEAT-069 status đang là IMPLEMENTED_SOURCE_REVIEWED; điều đó chỉ ghi nhận source review, không có nghĩa Android package/runtime đã được xác minh.
- Các thay đổi trước đó của Parent Web/FEAT-036/067/068 vẫn còn trong worktree và phải được bảo toàn.

## Cách tiếp tục

1. Bắt đầu bằng git status --short và git branch --show-current tại F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation. Xác nhận đúng branch feature/fe-ui-full-remediation và bảo toàn các thay đổi sẵn có.
2. Đọc lại governance/SRS authority và FEAT-069 records nêu trên. Kiểm tra plan hash trước khi định sửa requirement hoặc đổi phạm vi.
3. Không làm lại phần đã triển khai. Nếu có yêu cầu mới, xác định nó thuộc apps/mobile và FEAT-069 hay ngoài scope; ghi plan/approval/evidence theo governance trước khi implementation nếu scope cần mở rộng.
4. Với yêu cầu tiếp tục logic/UI, xem adapter và port trước, sau đó cập nhật UI qua contract thay vì import fixture trực tiếp.
5. Không tự chạy tests/build/device QA/commit/push/deploy theo approval hiện có. Nếu chủ dự án yêu cầu rõ ở lượt mới, thực hiện đúng phần được yêu cầu và ghi kết quả trung thực.
6. Nêu rõ mọi open question của SRS thay vì tự áp dụng yêu cầu cũ.
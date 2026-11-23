# FEAT-066 goal v3 Phase B - Android Parent wiring: evidence note (2026-11-21)

Status: implemented, checked, one independent review round plus one re-check done; one commit on `claude/v3-phase-b-mobile-wiring-f8044d`; not pushed. Plan: `plan/PHASE_B_MOBILE_WIRING_PLAN_20261121.md`. SRS authority: `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (SHA-256 prefix `443A3CA3`, the copy in the backend worktree); lines are `l.N`. Backend range read (read only): `feature/backend-srs-api-v3` `bb73e958..00d5ee60` and its evidence notes. Records (TASK_APPROVAL.md, DECISIONS.md) are not changed.

## 1. What changed (all under `apps/ui-mobile`)

- Brought in the minimum Android fix of integration commit `2a8a7ef1` (9 files; one conflict in `ParentApi.ts` resolved to the visible-ASCII 1-128 key rule).
- New pure application modules: `application/parentPhaseB.ts` (answer readers, drawing/rewrite/transcript classifiers, video panel, playback source builder), `parentRunUploads.ts` (upload-session orchestration, base64), `parentRunWait.ts` (2 s to 10 s run wait, background pause, abort).
- `infrastructure/http/ParentApi.ts`: `attachRunAssetV1`, `addRunIdeaV1`, `getRunTranscriptV1`, `confirmRunTranscriptV1`, `createStoryRewriteV1`, `requestVideoGenerationV1`, `markVideoUnsuitableV1`, `completeRunV1`, `openPlaybackV1`; keys of the `/v1/story-runs` commands are 1-128 visible ASCII (were 256); legacy unavailable audio stubs removed.
- `infrastructure/device/ParentMediaDevice.ts` (expo-crypto SHA-256, expo-file-system bytes), wired in `ParentModule.ts` with the Phase A `GenericUploadSessionsApi`.
- `ParentLearningUseCases`: attach drawing (upload session then attach), voice idea (fresh run revision, one retry on 409), text idea, transcript read/correct/confirm, async rewrite, video request, unsuitable, complete, playback.
- `useParentController`: drawing through upload sessions and a wait on the run; one retake; voice idea; new `transcript` step; subject `RERUN_REQUESTED` waits for the new revision and asks for the second confirmation; async story rewrite with failure recovery; new `video` step (request, follow, play, unsuitable, complete); resume routing for every Phase B state; busy ownership and `leaveWait`.
- Screens: new `VideoScreen`, rewritten `TranscriptReviewScreen`, `StoryScreen` (async rewrite, rewrite after a spent video, "Tiếp tục tạo video"), labels for the video states in Home and History; the platform hook no longer keeps unavailable video stubs, capabilities `video` and `job-status` follow the API configuration.
- Tests: `parentPhaseBWiring.test.ts` (new, 36 tests); `parentPhaseBContract.test.ts`, `parentSrsBehavior.test.ts` updated where behaviour intentionally changed (pins on the removed legacy route use, the unavailable video stubs, transcript screen, story screen).

## 2. Checks (actual results, final state)

- `apps/ui-mobile`: `npm test` 16 files, 206 tests passed, then `UI_COPY_AND_RECOVERY_VALID`; `npm run typecheck` 0 errors.
- Worktree root: `validate_harness.py` `HARNESS_VALID`; `validate_repository_security.py` `REPOSITORY_SECURITY_VALID`; `validate_architecture.py` `ARCHITECTURE_VALID`; `git diff --check` exit 0.
- No API, database, Docker, Firebase or server was run; tests use mocks. NOT CHECKED on a device or emulator: the upload of real photos, the recorder file read, the `expo-av` Video player with headers, the AppState pause.

## 3. Review

- Round 1, Sonnet 5.5 (`model sonnet`, effort high), read-only: NOT ACCEPTABLE, 2 P1 (voice idea with a stale `expected_run_revision`; resume of a fresh run waiting 8 minutes), 7 P2 (resume during `SCRIPT_GENERATING`; resume at `SCRIPT_REVIEW` with a draft; wait cancellation and busy ownership; user trapped on wait screens; spent-script flag set too early and lost on restart; transcript TOO_LONG message) and P3 notes.
- Every P1/P2 and the cheap P3 were fixed (revision read after the upload with one retry; `awaiting-drawing` state; `rewriteRangeForRun`; resume for draft and failed rewrite; abort check after read; `beginBusy`/`endBusy`/`leaveWait`; `scriptSpentByVideo` with `known`/`likely`; https for the playback source; one retake; run-specific copy).
- Re-check (same model and effort, once): ACCEPT WITH NOTES, no P1; F1, F2, F3, F4, F7a, F9 FIXED; F7b/c and F8 PARTIAL with 3 small P2, all fixed afterwards (retake and confirmed-revision memory reset per workflow; `likely` never blocks the request, also at revision 4; a leave blocks waits started by an action already in flight) plus P3 (admission rejected keeps the script reusable; understood drawing is server work; Understanding screen back uses `leaveWait`). The fixes of the last step were re-run through the tests and validators but not reviewed again (one round rule).
- Left as follow-ups (P3): `playVideo`, `markVideoUnsuitable`, `completeRun`, `requestStory`, `confirmStory` still use plain `setBusy`; the resume at `SCRIPT_GENERATING` shows the story screen with the "choose an activity" reason while waiting; `SCRIPT_GENERATION_UNKNOWN` is not routed on resume; `retakeUsed` is lost on app restart (the server then answers 409); `setPhoto` still locks on `current_input_revision > 1`; `VideoScreen` has no history shortcut when no request or rewrite is left; no controller-level (React) tests, only pure-function, use-case, API and source-pin tests.

## 4. Open questions for the owner

1. First-story trigger: `activitySelectionPersisted` is still false (no API stores the chosen activity), so the first story cannot be requested from the phone. The Phase B screens (rewrite, video) are reachable by resuming a run that already has a story (created elsewhere). SRS l.445 (no activity before the video) and l.888/l.394 (activity pinned before the story) disagree; the backend keeps the legacy `story-revisions` route (TD-27).
2. Job route: story jobs return no job reference (Q-J); the app follows `GET /v1/story-runs/{id}` (single source of truth) and does not use the Phase A `JobStatusPoller` for them.
3. After `video-unsuitable`/failed video the way back costs one of the three rewrites; at revision 4 there is no way back (T-1b revision-4 corner, backend OPEN). The app says "dừng buổi học trong lịch sử".
4. After completion or idle closeout the video cannot be replayed (T-1c-DEC-4, Q5 backend OPEN).
5. A first-story failure ends the run `FAILED` (T-2d-fix Q3) and other technical video failures end the run `FAILED` (T-1d1-fix Q2b); copy follows that.
6. Text idea route (`/idea` with `text`) is implemented in the port and use case and tested but no screen sends it (the typed idea is part of run creation); it is used only to retype an idea when the voice transcript failed with no row.
7. `quota` of the run detail is the constant `UNAVAILABLE`; the quota screen stays unavailable (quota build dropped).
8. Env note: the task asked for temp files under `D:\GitHub\Sketch2Life\tmp\v3b-mobile-wiring\`; the worktree hook blocks writes there, so scratch files were kept in the session scratchpad.

## 5. Vietnamese copy for owner review

The SRS gives no string for any of the lines below (the SRS is the source for behaviour and states, not for these sentences); all are new, calm and child-safe, and need owner review. The list is extracted from the added string literals of the change (`strings.py` over the diff); file names are relative to the worktree.

### `apps/ui-mobile/src/parent/application/parentRunHistory.ts`
- Chờ xem lại ảnh và ý tưởng
- Video đang chờ xử lý
- Đang tạo video
- Đang kiểm tra video
- Video đã sẵn sàng
- Video chưa qua kiểm tra

### `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts`
- Chụp hoặc chọn ảnh tranh trước khi tiếp tục.
- Câu trả lời gắn ảnh không khớp buổi học.
- Chưa có bản ghi âm để gửi.
- Câu trả lời ý tưởng không khớp buổi học.
- Ý tưởng cần có nội dung, tối đa 500 ký tự.
- Chưa đọc được bản chép lời.
- Kiểm tra lại nội dung đã nhận dạng.
- Chưa xác nhận được bản chép lời.
- Chưa có kịch bản để viết lại.
- Đã dùng hết lượt viết lại.
- Gợi ý viết lại tối đa 400 ký tự, không xuống dòng.
- Câu trả lời viết lại không khớp buổi học.
- Hãy xác nhận kịch bản trước khi tạo video.
- Hãy chọn lý do khi tạo lại video.
- Câu trả lời tạo video không khớp buổi học.
- Chưa có video sẵn sàng để đánh dấu.
- Chỉ hoàn tất được khi video đã sẵn sàng.
- Tải tệp lên chưa sẵn sàng.

### `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts`
- Hệ thống đang xem lại bức tranh theo chủ thể bạn vừa sửa. Hãy chờ một lát rồi mở lại buổi học để xác nhận kết quả mới.
- Định dạng tệp chưa được hỗ trợ. Hãy chọn ảnh JPEG hoặc PNG, hoặc ghi âm lại.
- Tệp quá lớn. Hãy chọn tệp nhỏ hơn.
- Bản ghi âm quá dài hoặc quá lớn. Hãy ghi lại trong 2 phút hoặc nhập ý tưởng bằng chữ.
- Ảnh quá lớn để xử lý. Hãy chọn ảnh nhỏ hơn.
- Tệp tải lên chưa khớp với bản gốc. Hãy thử lại.
- Nội dung tệp không đúng định dạng đã chọn. Hãy chọn tệp khác.
- Tệp chưa tải lên đủ. Hãy thử lại.
- Tệp này không an toàn nên không được dùng. Hãy chọn tệp khác.
- Kho lưu trữ tạm thời chưa sẵn sàng. Hãy thử lại sau ít phút.
- Phiên tải lên đã đóng. Hãy thử lại từ đầu.
- Chưa xác nhận được tệp đã tải lên. Hãy thử lại.
- Chưa xác nhận được ý tưởng vừa gửi. Hãy kiểm tra buổi học trước khi gửi lại.
- Ý tưởng cần có nội dung, tối đa 500 ký tự.
- Chưa có bản ghi âm để gửi.
- Chưa đọc được bản chép lời. Hãy tải lại.
- Kiểm tra lại nội dung đã nhận dạng.
- Gợi ý viết lại tối đa 400 ký tự và không xuống dòng.
- Chưa xác nhận được yêu cầu viết lại. Hãy kiểm tra buổi học trước khi gửi lại.
- Hãy chọn lý do khi tạo lại video.
- Chưa xác nhận được yêu cầu tạo video. Hãy kiểm tra buổi học trước khi gửi lại.
- Video chưa tạo xong trong thời gian cho phép. Lượt này vẫn được tính.
- Video gặp lỗi kỹ thuật. Lượt này vẫn được tính.
- Video chưa qua kiểm tra an toàn nên không được phát.
- Chưa mở được video. Hãy thử lại sau ít phút.
- Dịch vụ tạo nội dung không phản hồi kịp. Hãy thử lại.
- Đã dừng thao tác.
- Buổi học đã tự đóng sau 7 ngày không thao tác.
- Buổi học đã hoàn tất.
- Buổi học đã dừng. Bạn có thể xem lịch sử hoặc bắt đầu buổi học mới.
- Thao tác này không khớp với lần gửi trước. Hãy kiểm tra buổi học rồi thử lại.
- Thao tác chưa thể gửi. Vui lòng bắt đầu lại thao tác.

### `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- Định dạng bản ghi âm chưa được hỗ trợ. Bạn vẫn có thể nhập ý tưởng bằng chữ.
- Chưa xem lại được bức tranh theo chủ thể bạn sửa. Bạn có thể xác nhận kết quả hiện tại hoặc sửa lại.
- Việc nhận diện đang mất lâu hơn dự kiến. Ảnh đã được gửi; hãy quay lại sau để xem kết quả.
- Vẫn chưa nhận diện được bức tranh. Bạn có thể hủy buổi học trong lịch sử rồi bắt đầu lại.
- Chưa nhận diện được bức tranh. Bạn có thể chụp lại một lần.
- Buổi học đang chờ bạn xem lại ảnh và ý tưởng.
- Chưa gửi được bản ghi âm. Bạn vẫn có thể tiếp tục bằng ý tưởng đã nhập. ${safeRunMessage(cause)}
- Chưa có bản chép lời mới để xác nhận. Hãy thử tải lại.
- Ý tưởng đã nhập và nội dung chép lời dài quá 500 ký tự. Hãy rút gọn bản chép lời rồi xác nhận lại.
- Việc viết lại đang mất lâu hơn dự kiến. Câu chuyện hiện tại vẫn được giữ; hãy quay lại sau.
- Chưa viết lại được. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể thử lại.
- Chưa viết lại được. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể xác nhận câu chuyện này hoặc dừng buổi học.
- Chưa xác nhận được kết quả viết lại. Không gửi lại yêu cầu; hãy kiểm tra lại sau.
- Video đang được tạo. Bạn có thể rời màn hình này và quay lại sau.
- Chưa thể tạo video ở trạng thái hiện tại. Hãy mở lại buổi học để xem trạng thái mới nhất.
- Kịch bản này đã được dùng để tạo video. Hãy viết lại kịch bản, xác nhận lại rồi tạo video mới.
- Chưa phát được video. Hãy thử mở lại.
- Lần viết lại trước chưa thành công. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể thử lại.
- Lần viết lại trước chưa thành công. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể xác nhận câu chuyện này hoặc dừng buổi học.
- Buổi học đã thay đổi. Hãy mở lại buổi học để xem trạng thái mới nhất.
- Gói dịch vụ hiện tại chưa cho phép tạo video.
- Chưa mở được video. Hãy thử lại sau ít phút.
- Video này không còn phát được trong ứng dụng.
- Video chưa sẵn sàng hoặc không còn phát được.

### `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx`
- Chờ xem lại ảnh và ý tưởng
- Video đang chờ xử lý
- Đang tạo video
- Đang kiểm tra video
- Video đã sẵn sàng
- Video chưa qua kiểm tra

### `apps/ui-mobile/src/parent/presentation/screens/StoryHistoryScreen.tsx`
- Chờ xem lại ảnh và ý tưởng
- Video đang chờ xử lý
- Đang tạo video
- Đang kiểm tra video
- Video đã sẵn sàng
- Video chưa qua kiểm tra

### `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`
- Đang viết lại câu chuyện. Câu chuyện hiện tại vẫn được giữ cho đến khi bản mới sẵn sàng.
- Video lần trước chưa dùng được. Hãy viết lại câu chuyện, xác nhận bản mới rồi tạo video.
- Thêm gợi ý để tạo bản câu chuyện mới.
- Gợi ý viết lại · còn ${props.rewritesLeft}
-  text={props.rewriteAfterVideo ? 'Bạn đã dùng hết số lần viết lại. Bạn có thể dừng buổi học trong lịch sử.' : 'Bạn đã dùng hết số lần viết lại cho câu chuyện này. Hãy xác nhận câu chuyện hiện tại hoặc dừng buổi học.'} tone=
- Xác nhận câu chuyện này
- Tiếp tục tạo video

### `apps/ui-mobile/src/parent/presentation/screens/TranscriptReviewScreen.tsx`
- CHƯA NHẬN DẠNG ĐƯỢC
- CẦN XÁC NHẬN
- Chưa chuyển được giọng nói thành chữ. Bạn có thể gõ lại ý tưởng bên dưới.
- Dùng ý tưởng này
- Lưu chỗ sửa và xác nhận
- Xác nhận bản chép lời
- Đang chuyển giọng nói thành chữ
- Chưa có bản chép lời
- Việc này có thể mất một lúc. Nội dung chỉ được dùng sau khi người lớn xem lại.
- Bạn có thể thử tải lại bản chép lời.
- Chưa có bản ghi âm nào cho buổi học này.
- Tải lại

### `apps/ui-mobile/src/parent/application/parentPhaseB.ts`
- Hình hoặc tiếng chưa rõ
- Chưa đúng với câu chuyện
- Nội dung chưa phù hợp với bé
- Lý do khác
- Đang chờ
- Đang tạo
- Đã xong
- Chưa tạo được
- Chưa có buổi học để tạo video.
- Buổi học đã hoàn tất.
- Video không phát lại trong ứng dụng sau khi hoàn tất. Nội dung được giữ cho đến khi bạn xóa buổi học.
- Buổi học đã tự đóng.
- Buổi học không có thao tác trong 7 ngày nên được đóng lại. Nội dung được giữ cho đến khi bạn xóa buổi học.
- Buổi học đã dừng.
- Buổi học đang được xóa.
- Yêu cầu xóa đang chờ máy chủ xác nhận.
- Buổi học đã được xóa.
- Video này chưa qua kiểm tra an toàn nên không được phát.
- Bạn có thể hủy buổi học trong lịch sử rồi bắt đầu một buổi học mới.
- Đang xác nhận yêu cầu tạo video…
- Chưa gửi lại yêu cầu. Máy chủ đang kiểm tra lượt tạo video.
- Video đang chờ tới lượt xử lý.
- Bạn có thể rời màn hình này; tiến độ vẫn được máy chủ giữ.
- Đang tạo video cho bé…
- Đã xong ${done} / ${total} cảnh.
- Việc này có thể mất vài phút.
- Đang kiểm tra video trước khi phát…
- Chỉ video qua kiểm tra mới được phát.
- Video đã sẵn sàng.
- Video đã tạo xong nhưng chưa thể phát.
- Xem video, rồi hoàn tất buổi học hoặc đánh dấu video chưa phù hợp.
- Hãy tải lại sau ít phút.
- Hãy hoàn tất các bước trước khi tạo video.
- Cần xác nhận chủ thể, ngữ cảnh và kịch bản của buổi học.
- Hãy xác nhận kịch bản trước khi tạo video.
- Video chỉ được tạo từ kịch bản người lớn đã xác nhận.
- Đã dùng hết lượt tạo video của buổi học này.
- Bạn có thể hủy hoặc xóa buổi học trong lịch sử.
- Đã hết lượt viết lại kịch bản. Bạn có thể dừng buổi học trong lịch sử.
- Chưa nhận được yêu cầu tạo video.
- Lượt này không bị tính. Bạn có thể thử lại sau ít phút.
- Kịch bản đã xác nhận. Sẵn sàng tạo video.
- Còn ${remaining} lượt tạo video cho buổi học này.
- Bạn đã đánh dấu video chưa phù hợp.
- Hãy viết lại kịch bản, xác nhận lại rồi tạo video mới.
- Video chưa tạo xong trong thời gian cho phép.
- Lượt này vẫn được tính. Hãy viết lại kịch bản, xác nhận lại rồi tạo video mới.
- Video lần trước chưa tạo được.
- Hãy viết lại và xác nhận kịch bản nếu muốn tạo lại.
- Video không tạo xong trong thời gian cho phép nên buổi học đã dừng.
- Video gặp lỗi kỹ thuật nên buổi học đã dừng.
- Video chưa qua kiểm tra an toàn.
- Dịch vụ tạo nội dung không phản hồi kịp. Bạn có thể bắt đầu buổi học mới.
- Bạn có thể xem lịch sử buổi học hoặc bắt đầu buổi học mới.
- Chờ xem lại ảnh và ý tưởng
- Đang tạo câu chuyện
- Chờ xác nhận kịch bản
- Đang xác nhận yêu cầu tạo video
- Video đang chờ xử lý
- Đang tạo video
- Đang kiểm tra video
- Video đã sẵn sàng
- Video chưa qua kiểm tra
- Đã hoàn tất
- Đã tự đóng

### `apps/ui-mobile/src/parent/application/parentRunUploads.ts`
- Định dạng tệp chưa được hỗ trợ.
- Tệp quá lớn hoặc trống.
- Máy chủ trả về cấu hình tải lên không khớp.
- Phiên tải lên không còn mở.
- Đã dừng tải lên.
- Chưa xác nhận được tệp đã tải lên.
- Không đọc được dữ liệu tệp.

### `apps/ui-mobile/src/parent/presentation/screens/VideoScreen.tsx`
- Video của bé
- Video chỉ được phát sau khi qua kiểm tra.
- Kiểm tra lại
- Video câu chuyện của bé
- Mở video
- Mở lại video
- Video chưa phù hợp vì sao?
- Vì sao tạo lại video?
- Tạo lại video
- Tạo video
- Đánh dấu video chưa phù hợp
- Không đánh dấu
- Hoàn tất buổi học
- Video chưa phù hợp
- Xem lại kịch bản
- Xem lịch sử buổi học

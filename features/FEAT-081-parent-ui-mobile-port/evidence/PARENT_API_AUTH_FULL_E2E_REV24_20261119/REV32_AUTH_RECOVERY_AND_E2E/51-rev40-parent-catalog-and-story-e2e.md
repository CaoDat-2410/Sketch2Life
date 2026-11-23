# Rev40 — Parent activity catalog and story E2E

Date: 2026-11-20. Real Android emulator UI; synthetic Parent/profile/run/drawing only. No fixture or direct API call.

## Parent activity catalog source

The Parent activity endpoint did query its configured catalog. The live path is `LessonLibraryParentActivityCatalogAdapter` → `LessonLibraryService.list_parent_activity_catalog` and returns only lesson versions the authenticated Parent currently has access to. Runtime counts for the unpinned turtle run were all zero: accessible lessons `0`, age/access-eligible lessons `0`, age/access-eligible activities `0`, relevance matches `0`, and candidates sent to Qwen `0`.

The worker therefore received no candidates, returned `NO_MATCH`, and generated three adult-reviewable fallback drafts. The backend persisted the set; the UI showed the drafts. This was a catalog miss, not a skipped lookup.

The repository separately contains static files under `data/activity-catalog/{mvp,golden,curated}`. They are not wired as Parent's product source. FEAT-063 SRS Rev63/67 specifies Parent-accessible PUBLIC/SHARED lesson activities (or the exact pinned lesson version) and identifies the static ACT demo catalog as not being the Parent product source. The MVP catalog itself is marked synthetic/provisional and requires qualified Montessori review before production. No policy or source change was made.

Catalog implementation/count evidence: `38-rev40-catalog-source-check.md`, `36-rev40-api-activity-log.txt`, `36-rev40-modal-activity-log.txt`.

## Persisted activity selection

- StoryRun: `ec455bbb-8211-49d5-8cef-9889df809de2`.
- Suggestion set: `80e56b80-674f-4719-a0b8-500d523cc4c5`, revision 1; three Qwen fallback drafts.
- The user-selected activity was “Phân loại thẻ con rùa”. The UI showed “Đã lưu lựa chọn cho buổi học này.” and the real `POST /api/parent/v1/ai/story-runs/{run_id}/activity-selection` returned HTTP 200.
- UI evidence: `43-rev40b-activity-selected.png`, `44-rev40b-selection-bottom.png` and XML counterparts.

## Real story generation

- The Continue action opened the story draft screen. The user tapped “Tạo câu chuyện” once; no retry was sent. The request used the persisted run/activity and the real Parent UI.
- Backend request ID: `5753e117-31c9-4ced-b104-f907fd04d2b2`.
- Modal call ID: `fc-01M7VEYF77EX3HV1MM80K4TC27`; job `f6e7380740069663`; generation `44000bb75bb97963`; attempt `6c5f55a182fc4635`.
- Model: `Qwen/Qwen3.5-9B`, pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; GPU: NVIDIA A10. It loaded in `14.614s`, generated `1,371` tokens in `132.886s`, and produced a 6,233-byte JSON result. Placement log showed CPU offload `0`, disk offload `0`. Output parsing and business-rule validation passed; Modal emitted `worker_succeeded`. API returned HTTP 200 and the app rendered the story review draft.
- The UI exposed five storyboard scenes, meeting the SRS minimum. Story title: “Khám phá màu sắc con rùa ngoài trời”; it used the selected card-sorting activity and turtle context. No adult script confirmation or video request was performed; the app remains on the review screen.
- Main review screenshot/XML: `47-rev40-story-result.png/.xml`; visible scene evidence: `48-rev40-story-scenes-1.png/.xml`. Correlated logs: `49-rev40-api-story-selection-log.txt`, `50-rev40-modal-story-log.txt`.

## Remaining observed issues

1. The code and Metro bundle contain the Rev40B safe fallback copy; all 125 mobile tests and typecheck pass. The emulator did not apply Fast Refresh or the supported development reload action, so `39-rev40b-activity-result.png` still shows the old technical `candidate_activities` reason. The app was not reinstalled/restarted because in-memory activity suggestions would be lost and a second inference is not authorized.
2. The API wait-completion diagnostic snapshot reported `worker_started_without_terminal_event`, although the correlated Modal log later reported `worker_succeeded` and the UI received HTTP 200. This appears to be a worker-log visibility/timing mismatch, not an inference failure.
3. The story review display visibly has stray numeric fragments appended to some scene action/narration text (for example `68` and `69`). This needs a separate contract/output presentation review; no schema or quality gate was changed during this run.

No video, quota/payment call or mutation, fixture, seed, migration, direct DB edit, additional activity inference, commit or push.

After evidence capture, the task's `sketch2life-srs23-language-audio-dev` Modal app was stopped; Modal lists it stopped with zero tasks. The unrelated drawing and video apps were not changed. The Android emulator remains on the story review screen.

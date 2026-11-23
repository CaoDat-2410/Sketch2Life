# Rev40 — Parent activity catalog source check

Date: 2026-11-20

## Result

The real Parent activity request queried the backend catalog. It did not query the repository's static `data/activity-catalog` files.

The live path is:

`POST /api/parent/v1/ai/story-runs/{run_id}/activity-suggestions` → `LessonLibraryParentActivityCatalogAdapter` → `LessonLibraryService.list_parent_activity_catalog(parent_principal_ref, limit=500)` → age/access/renderability/relevance filters → Qwen3.5 only for matched candidates or the documented no-match fallback.

The adapter reads current Parent-accessible lesson versions. A pinned run uses its exact pinned lesson snapshot; an unpinned run uses lesson versions the Parent can currently access.

## Live request evidence

- Request: `404c1fe0-be88-4b0c-9690-90df95e71926`
- StoryRun: `ec455bbb-8211-49d5-8cef-9889df809de2`
- Modal call: `fc-01M7VDSRE9NJ5K74YQ1T13CN59`
- Backend counts: accessible lessons `0`; age/access-eligible lessons `0`; eligible activities `0`; relevance matches `0`; candidates sent `0`.
- Worker: `candidate_count_received=0`, `decision=NO_MATCH`, returned three fallback activities; API persisted the three drafts as suggestion set `80e56b80-674f-4719-a0b8-500d523cc4c5`.
- The request completed successfully; it did not time out and was not retried.

Raw sanitized logs and UI evidence are alongside this note: `36-rev40-api-activity-log.txt`, `36-rev40-modal-activity-log.txt`, `36-rev40-activity-result.png`, and `37-rev40-activity-result-scroll.png`.

## Why the static repository catalog was not used

The repository has static catalogs under `data/activity-catalog/` for earlier/demo catalog workflows. The canonical Parent flow in FEAT-063 SRS Rev63/67 uses activities from currently Parent-accessible PUBLIC/SHARED lesson versions, or the exact version of a pinned lesson. The SRS also identifies the static ACT demo catalog as not being the Parent product source. The MVP catalog metadata describes its content as synthetic/provisional and requiring qualified Montessori review before production.

Therefore, the correct live behavior for this request was: query the Parent lesson catalog; when there are no eligible/matching activities, invoke the AI fallback for three reviewable drafts. The logs confirm that behavior. Connecting the static dataset as a Parent source would change product/data-source policy and needs a separate SRS/plan decision; it was not silently added here.

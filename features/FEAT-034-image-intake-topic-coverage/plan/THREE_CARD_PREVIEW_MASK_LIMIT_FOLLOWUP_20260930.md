# Approved follow-up: activity preview and SAM mask limit

Status: APPROVED. Owner requested correction of excess visible recommendations and invalid masks, then explicitly selected “3 mục trước, có ‘Xem thêm’”. This supplements, without modifying, the pinned revision-1 plan.

## Plan and acceptance

1. Initially render at most three ordered eligible activity cards. A “Xem thêm” action reveals all remaining cards; retain backend candidates, ranking and adult selection. Reset expansion for a new session/profile/topic. Show the selected title if asynchronous ranking moves it outside the preview.
2. Fix the measured SAM/Pixi area-policy mismatch: runtime mask occupied 81.595% of a 335×597 image; worker accepted up to 85%, renderer rejects over 75%. Set the worker maximum to 75%, preserving multimask selection of a valid alternative and fail-closed rejection when none exists. Do not truncate masks, weaken renderer validation, add retries or animate the whole image.
3. Verify mobile types/copy and synthetic SAM multimask regression; retain only aggregate mask metrics, not images, capabilities or profile data.

Deployment boundary: local Metro picks up UI changes. The external Lightning worker must receive/restart with the updated source before its candidate selection changes. No claim of successful live segmentation without a fresh user run.

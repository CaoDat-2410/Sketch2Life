# FEAT-070 implementation and preview evidence

- Date: 2026-11-10
- Source: apps/parent-ui
- Preview: isolated local Vite server on http://127.0.0.1:5172, mobile viewport 430×932, isolated Edge profile.
- Data: synthetic Parent UI state; the preview banner stated that changes are not saved.
- Product authority: FEAT-063 SRS v2.7-draft Rev57. The Parent Web target-client and quota-amount questions remain open.

## Source review

- confirmScriptAndStartVideo now returns false when quota is exhausted and true after accepting the request and consuming one unit.
- The confirmation button navigates to /p07-video-job-status only when that command returns true.
- The confirmation copy uses the post-use remaining count, clamped at zero.
- The P06 exhausted-quota gate remains in place.

## Manual UI walkthrough

Two complete synthetic flows were driven through the visible UI controls:

1. Initial quota 2 → confirmation stated one remaining after use → accepted and navigated to P07 → video reached READY → P08 playback → P08b activity → P08c feedback → P01.
2. Initial quota 1 → confirmation stated zero remaining after use → accepted and navigated to P07 → video reached READY → P08 playback → P08b activity → P08c feedback → P01.

After both units were used, a third attempt reached P06 and showed the exhausted-quota message and “Mua thêm lượt tạo” action. The create-video action was absent.

Screenshot evidence: [last-unit confirmation](demo-last-quota-confirmation.png).

## Verification limits

- No automated tests or build were run, as excluded by the approved plan.
- No API, backend, billing, authentication, or provider integration was added.
- The local preview run does not settle the SRS's open Parent Web client or commercial quota questions.
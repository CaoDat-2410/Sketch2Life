# FEAT-072 decisions

## D-072-01 — Keep the quota screen adult-facing

Use a warm, child-centered visual tone that fits the Parent product, while keeping quota amounts, package selection, and simulated checkout clear to the adult account owner. Do not gamify payment or make purchase controls look like a child activity.

## D-072-02 — Show remaining quota and both buckets

Make the current remaining count the primary summary and show included and top-up balances separately. Remove the used/total ring because the local aggregate does not establish a clear monthly denominator when top-up units may carry forward. Keep the distinction between periodic and purchased units visible.

## D-072-03 — Keep all package values explicitly synthetic

Retain the existing +3/+5/+10 packs and their current mock price fixtures for the FE demo only. Label packages, prices, and checkout as simulated. Do not treat MoMo/VNPAY labels as production payment integration or infer approved package pricing.

## D-072-04 — Use accessible native choices

Use labeled radio groups for pack and method selection, visible selected/focus states, touch-sized choice cards, and a live status region for pending/result feedback.

## D-072-05 — Scope responsive layout to P12

Use a P12-specific class and tablet selectors. Remove the old .gauge hook from this page so tablet grid rules for the previous layout no longer apply. Leave other screens and shared layout selectors untouched.

## D-072-06 — No external visual assets

Build the visual treatment from existing Sketch2Life icons, app tokens, and CSS shapes. No bitmap asset is needed; therefore there is no asset to route through generated/approved/applied folders.

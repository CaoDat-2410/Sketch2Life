# FEAT-067 — Decisions

## D-067-01 — Activate tablet layout by viewport shape

Use a tablet width range plus viewport shape/orientation for fine-pointer browsers, with a coarse-pointer path for touch tablets that use wider ratios. This keeps iPad layouts active in desktop responsive previews while preserving the existing composition on common wide desktop viewports.

## D-067-02 — Give portrait and landscape different navigation proportions

Keep a centered, tablet-width shell and bottom tab bar in portrait. In landscape, use a narrow vertical navigation rail beside the content area. Authentication, recovery, and registration use the full landscape width without the rail.

## D-067-03 — Use route-specific two-column layouts where they improve reading

Keep text and cards within readable widths in portrait. In landscape, arrange suitable media, controls, and supporting content into two zones; keep long content scrollable and preserve the existing route order and actions. Set explicit grid rows for the outdoor activity layout so its illustration and family guidance remain visible together.

## D-067-04 — Reuse the Parent visual language and interaction sizes

Use existing Parent tokens, typography, colors, and components. Increase tablet control hit areas and spacing in the responsive stylesheet instead of creating a new design system.

## D-067-05 — Presentation-only change

Do not infer tablet-specific product requirements from older feature records. Keep Parent flows, auth, data, API contracts, and backend behavior unchanged; treat the signed-off product behavior as outside this responsive styling scope. The current canonical SRS remains a v2.7-draft awaiting owner sign-off.

# FEAT-068 — Decisions

## D-068-01 — Keep the navbar icons inside the existing SVG system

Add five dedicated navigation glyph names to the existing Parent icon map and map only the navbar to them. This avoids a new runtime dependency and keeps existing uses of generic icons unchanged.

## D-068-02 — Use recognizable rounded outline symbols

Use a house with chimney for home, clock with rewind arrow for history, camera with plus for create, stacked coins for creation credits, and horizontal sliders for settings. Keep all paths in the existing 24×24 viewBox and use the shared rounded stroke style.

## D-068-03 — Preserve navigation behavior and accessibility

Keep route labels and links untouched. Decorative SVGs remain hidden from assistive technology; the create button keeps its descriptive accessible name.

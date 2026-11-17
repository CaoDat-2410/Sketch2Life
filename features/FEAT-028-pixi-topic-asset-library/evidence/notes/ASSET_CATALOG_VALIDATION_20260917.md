# FEAT-028 revision-2 catalog and atlas validation

- Evidence ID: EV-028-ASSET-02
- Plan revision/hash: 2 / SHA-256 D943333F8B268D7B8B1E87556677F867A445D73C5C87717C2F8C2F05CC62CCBA
- Date: 2026-09-17 (Asia/Saigon)
- Branch: codex/feat-018-contract-plan
- Scope: catalog and file integrity only; this is not visual approval.

## Commands and results

- backend/.venv/Scripts/python.exe features/FEAT-028-pixi-topic-asset-library/tools/build_asset_catalog_v2.py — generated assets/generated/asset-catalog.v2.json from preserved catalog v1 plus the 12 revision-2 packs.
- Backend load_topic_asset_catalog() against v2 — PASS: 144 unique descriptors, 24 atlases, all source files present, atlas SHA-256 values match, and every frame lies within its PNG bounds.
- Generation-manifest cross-check — PASS: all 12 new rows match the catalog atlas hashes.
- Image inspection using the bundled image-capable Python/Pillow runtime — PASS for file structure: all 12 new PNGs are RGBA, top-left alpha is 0, and all six nominal cells contain pixels. Eleven images are 1024x1536; science/technology is 1024x1535 and catalog v2 stores 511px height for the last-row frames.

## State and limitations

- All 144 entries remain REVIEW_PENDING, runtimeEligible=false, and licenseStatus=REVIEW_REQUIRED. No approved/applied/runtime copy exists.
- The one-pixel science atlas height difference is represented honestly in frame bounds; it was not edited. Several assets touch cell edges and need owner crop review.
- The earlier asset-catalog.v1.json remains unchanged. No child artwork, reference child image, external asset source, or provider call was used.
- The files have not received per-frame visual/rights approval. Hash/frame validation does not prove semantic accuracy, crop quality, or suitability for a specific child's drawing.

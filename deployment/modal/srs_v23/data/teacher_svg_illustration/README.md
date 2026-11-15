# Teacher SVG illustration reference pack

This folder holds a small, pinned, CC0 reference subset for the Teacher SVG illustration Qwen workload. It is used as an in-context structural example only. It is not a product catalog, approved presentation asset, model-training corpus, or user-facing fallback.

## Source

- Dataset: [yoavf/svg-animal-illustrations](https://huggingface.co/datasets/yoavf/svg-animal-illustrations)
- Immutable Hub revision: `d7ab3149308746a4b17e7cbee30f1f054f6c49df`
- License shown in the dataset card and repository metadata: CC0 1.0. The dataset card describes the illustrations as generated with Claude Sonnet 4.5 and systematically varied. The license statement is recorded as the publisher's declaration; it has not been independently audited.
- Source files are the dataset's own `samples/*.svg` previews. These sample files have no paired text prompt, so their original prompt is recorded as absent. The small subject label comes from the source filename.
- The original six sample files are retained, byte-for-byte, in `source-examples.jsonl` with source URL, revision and per-SVG SHA-256.

## Curated references

`reference-pack-v1.json` contains two examples: dog (quadruped layout) and rabbit (lagomorph). The cat source preview is preserved in the raw snapshot but excluded from the active pack because path-026 has stroke_width=20, above the worker's unchanged maximum of 12; the source geometry and style were not altered.

Before passing examples through the existing backend sanitizer, the one-time curation normalized only rendering details that do not require arbitrary SVG execution: removed `title`/`desc` and stroke cap/join/miter attributes, expanded a simple ellipse rotation to cubic paths, expanded rounded rectangles to quadratic paths, and expanded short `#RGB` colors to `#RRGGBB`. The original source strings remain unchanged. The sanitizer output, normalization list and canonical hash are included in each record. Other samples requiring CSS classes/styles, arbitrary group transforms, or unsupported constructs were not selected.

## Integrity

See `dataset-manifest.json` for source and derived file hashes, accepted records, path counts, normalizations, and records not selected from the six-file preview subset. Keep this provenance with the files if they are moved or included in a worker image.

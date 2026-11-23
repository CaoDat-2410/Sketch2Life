# Arcadia organism SVG reference

This pack contains one SVG selected from Arcadia Science's **Free Organism
Illustration Library v1.0**, archived at [Zenodo record 17203578](https://doi.org/10.5281/zenodo.17203578).
The library identifies its content as CC0 1.0. The original archive was checked
against its published MD5 before extraction; both archive and selected-file
hashes are recorded in `gallus-gallus-v1.json`.

`gallus-gallus-source.svg` is the dataset's `Tricolor + stroke` illustration
for `Gallus gallus`. It is a visual/anatomical reference for the generic topic
“gà”; it does **not** define a child-friendly stroke order. The Qwen3.5 worker
renders this SVG in memory and uses it only as a visual input. Its generated
guide must contain new open paths and a deliberate pen order; it must not copy
the reference paths or return the colored illustration as a drawing guide.

This pilot asset only supports the normalized topics listed in the provenance
JSON. Other topics fail closed until a matching, reviewed source is added.

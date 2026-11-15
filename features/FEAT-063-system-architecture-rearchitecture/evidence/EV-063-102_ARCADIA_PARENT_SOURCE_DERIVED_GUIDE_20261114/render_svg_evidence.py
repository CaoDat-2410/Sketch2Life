from pathlib import Path

import cairosvg


DIRECTORY = Path(__file__).resolve().parent
SOURCES = sorted(DIRECTORY.glob("parent-chicken-stroke-step-*.svg")) + [
    DIRECTORY / "parent-chicken-source-derived.svg",
    DIRECTORY / "parent-chicken-reference-illustration.svg"
]

for source in SOURCES:
    cairosvg.svg2png(
        url=str(source),
        write_to=str(source.with_suffix(".png")),
        output_width=1024,
        output_height=1024,
    )

print(f"Rendered {len(SOURCES)} actual SVG artifacts at 1024x1024.")

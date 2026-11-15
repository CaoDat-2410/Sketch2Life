from pathlib import Path

import cairosvg


DIRECTORY = Path(__file__).resolve().parent
SOURCES = sorted(DIRECTORY.glob("parent-chicken-v4-step-*.svg")) + [
    DIRECTORY / "parent-chicken-v4-final-strokes.svg",
    DIRECTORY / "parent-chicken-v4-reference-separate.svg",
]

if len(SOURCES) != 8 or any(not source.is_file() for source in SOURCES):
    raise SystemExit("Expected six construction steps, final strokes and separate reference SVGs.")

for source in SOURCES:
    cairosvg.svg2png(
        url=str(source),
        write_to=str(source.with_suffix(".png")),
        output_width=1024,
        output_height=1024,
    )

print(f"Rendered {len(SOURCES)} actual V4 API-derived SVG artifacts at 1024x1024.")

from pathlib import Path

import cairosvg


DIRECTORY = Path(__file__).resolve().parent
SOURCES = sorted(DIRECTORY.glob("parent-chicken-v3-step-*.svg")) + [
    DIRECTORY / "parent-chicken-v3-final-overlay.svg",
    DIRECTORY / "parent-chicken-v3-reference.svg",
]

if len(SOURCES) != 8 or any(not source.is_file() for source in SOURCES):
    raise SystemExit("Expected six steps, final overlay and full-color reference SVGs.")

for source in SOURCES:
    cairosvg.svg2png(
        url=str(source),
        write_to=str(source.with_suffix(".png")),
        output_width=1024,
        output_height=1024,
    )

print(f"Rendered {len(SOURCES)} actual API-derived SVG artifacts at 1024x1024.")

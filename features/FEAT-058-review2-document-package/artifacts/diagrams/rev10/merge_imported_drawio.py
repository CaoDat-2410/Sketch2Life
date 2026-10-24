"""Merge Draw.io Desktop Mermaid imports into one editable review diagram file."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
IMPORTED = HERE / "imported"
OUTPUT = HERE / "drawio" / "Sketch2Life-Review2-State-and-Activity.drawio"

PAGES = [
    ("Session-Lifecycle", "SM-01 Session Lifecycle"),
    ("Session-Pause-Recovery-Companion", "SM-02 Session Pause and Recovery"),
    ("Session-Early-Termination-Companion", "SM-03 Session Early Termination"),
    ("Shared-Learning-Stage-Lifecycle", "SM-04 Shared Learning Stage"),
    ("Group-Progress-Lifecycle", "SM-05 Group Progress"),
    ("Participant-Admission", "SM-06 Participant Admission"),
    ("Device-Connection", "SM-07 Device Connection"),
    ("Device-Grant-Revocation-Companion", "SM-08 Device Grant Revocation"),
    ("Draft-Sync-Lifecycle", "SM-09 Draft Synchronization"),
    ("Sketch-Pipeline-Lifecycle", "SM-10 Sketch Pipeline"),
    ("Child-Suggestion-Response-Lifecycle", "SM-11 Child Suggestion Response"),
    ("Knowledge-Editorial-Lifecycle", "SM-12 Knowledge Editorial"),
    ("AI-Media-Job", "SM-13 AI / Media Job"),
    ("Video-Delivery", "SM-14 Video Delivery"),
    ("Activity-Execution-Lifecycle", "SM-15 Activity Execution"),
    ("Observation-Lifecycle", "SM-16 Observation"),
    ("Content-Publication-Lifecycle", "SM-17 Content Publication"),
    ("Data-Request-Lifecycle", "SM-18 Data Request"),
    ("WF-01-Prepare-Admit", "AD-01 WF-01 Prepare and Admit"),
    ("WF-02-Collaborative-Drawing", "AD-02 WF-02 Collaborative Drawing and Recovery"),
    ("WF-03-AI-Sketch-Review", "AD-03 WF-03 Request and Review AI Sketch"),
    ("WF-04-Reviewed-Learning-Close", "AD-04 WF-04 Reviewed Learning and Session Close"),
]


def main() -> None:
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "2026-10-24T00:00:00.000Z",
            "agent": "Sketch2Life Review 2 Rev10",
            "version": "32.6.1",
        },
    )
    for index, (basename, name) in enumerate(PAGES, start=1):
        source = IMPORTED / f"{basename}.drawio"
        if not source.exists():
            raise FileNotFoundError(source)
        root = ET.parse(source).getroot()
        diagrams = root.findall("diagram")
        if len(diagrams) != 1:
            raise ValueError(f"Expected exactly one imported page in {source.name}, found {len(diagrams)}")
        diagram = diagrams[0]
        diagram.set("id", f"rev10-page-{index:02d}")
        diagram.set("name", name)
        mxfile.append(diagram)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(mxfile, space="  ")
    ET.ElementTree(mxfile).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"{OUTPUT} pages={len(PAGES)}")


if __name__ == "__main__":
    main()

"""FEAT-099 research: what kind of movement does each suggested subject need? A hand-made judgement, then counted.

Run from backend/:  PYTHONPATH=src python ../features/FEAT-099-video-motion-and-guide-level/evidence/classify_topics.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from sketch2life.resources.parent_topic_catalog_vi_v2 import TOPICS

# Movement family -> subject ids. "turtle" is a walker on land and a swimmer in the ocean topic.
FAMILIES = {
    "legs": "cat dog rabbit horse elephant deer turtle cow chicken pig goat sparrow parrot owl dove peacock duck "
    "ant ladybug grasshopper beetle crab unicorn astronaut doll teddy-bear",
    "wings": "butterfly bee dragonfly firefly dragon fairy",
    "swim": "fish whale dolphin octopus seahorse swan starfish",
    "crawl": "snail caterpillar",
    "wheels": "car bicycle train bus scooter ambulance truck school-bus tractor toy-train toy-car carriage",
    "path": "airplane boat rocket satellite comet kite ball hay-bale",
    "spin": "planet windmill fan spinning-top clock",
    "light": "sun moon star lightning rainbow lamp streetlight traffic-light crown wand",
    "weather": "cloud raindrop puddle kettle watering-can thermometer",
    "plant": "flower tree leaf mushroom pot vase pinecone carrot corn",
    "play": "drum guitar flute piano tambourine maracas xylophone bell trumpet blocks puzzle magic-book",
}
# Everything else is a thing that stands where it is: it can only be shown (presence, glow, parts named).


def main() -> None:
    family_of = {subject: family for family, ids in FAMILIES.items() for subject in ids.split()}
    per_family: dict[str, list[str]] = defaultdict(list)
    per_topic: dict[str, Counter] = {}
    for topic in TOPICS:
        title, subjects = topic["title_vi"], topic["subjects"]
        counter: Counter = Counter()
        for subject in subjects:
            key = subject[0]
            family = family_of.get(key, "still")
            if key == "turtle" and "dương" in str(title):
                family = "swim"
            counter[family] += 1
            per_family[family].append(f"{title}: {subject[1]}")
        per_topic[str(title)] = counter
    total = sum(len(v) for v in per_family.values())
    result = {
        "total": total,
        "families": {family: len(items) for family, items in sorted(per_family.items(), key=lambda kv: -len(kv[1]))},
        "topics": {title: dict(counter) for title, counter in per_topic.items()},
        "subjects": per_family,
    }
    Path(__file__).with_name("topic_families.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(total, result["families"])
    for title, counter in result["topics"].items():
        print(title, counter)


if __name__ == "__main__":
    main()

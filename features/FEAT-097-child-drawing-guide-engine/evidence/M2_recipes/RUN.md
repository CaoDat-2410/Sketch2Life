# Phase 2: the other 36 subjects (2026-11-27)

Code not committed. Synthetic data only; no GPU or model used.

## What was added

- 72 recipes (36 subjects at two levels), 80 in all, in `backend/src/sketch2life/resources/drawing_recipes/`.
- A `rect` shape (top-left corner, width, height), allowed at both levels. Vehicles, doors and windows need it.
- Matching: three longer names that contain a recipe name but mean something else get no picture ("xe máy xúc",
  "máy bay trực thăng", "cây cầu").

## Pictures for the owner's review

Local drawings of the data by `render_batches.py`, not app screenshots. Per batch: `*_finished.png` (finished pictures
at both levels), `*_beginner.png` and `*_simple.png` (every step).

| Batch | Subjects |
|---|---|
| `batch1_animals_birds` (13) | cat, deer, elephant, fish, horse, rabbit, dove, duck, owl, parrot, peacock, sparrow, swan |
| `batch2_insects_plants` (8) | ant, bee, caterpillar, dragonfly, ladybug, flower, snail, tree |
| `batch3_sea_vehicles` (15) | crab, dolphin, octopus, seahorse, starfish, whale, airplane, ambulance, bicycle, boat, bus, car, scooter, train, truck |

The plan's six groups were drawn as these three batches. Claude looked at the finished pictures and reshaped the weak
ones (among others the elephant trunk, horse mane, peacock tail, dove twig, and the wheels of bicycle and scooter,
which are drawn in two steps because separate wheels would float). **The owner has not judged any of them.**

Weaker in Claude's view: seahorse 3 to 5, starfish 3 to 5 (reads as a star with a face and hat), dove at both levels,
peacock 6 to 10 (can be read as a butterfly).

## Checks

- 155 tests pass: recipe rules, library (all 80 files against their level rules, every catalog drawing card), guide
  service and guide route. Ruff passes on the changed Python files. Security validator passed.
- Inside the rebuilt API container all 40 subjects build at both levels.
- Emulator: the horse guide was opened from the catalog card "Ngựa con"; step 6 of 6 (3 to 5) and step 8 of 8
  (6 to 10) match the sheets (`device_horse_*.webp`). The other new subjects were not opened on the device, and no
  recipe with a rectangle was seen there.
- App code did not change in this phase; app tests were not run again.

## Limits

- The catalog has 156 different drawing cards over 18 topics; 46 of them have a recipe. The other cards answer
  "no guide" (for example "chiếc lá" and "vỏ sò").
- A name inside a longer sentence is matched by whole words only. Other look-alike compounds may still exist.
- When a catalog card is chosen, it wins over the words typed in the idea box (unchanged from phase 1).

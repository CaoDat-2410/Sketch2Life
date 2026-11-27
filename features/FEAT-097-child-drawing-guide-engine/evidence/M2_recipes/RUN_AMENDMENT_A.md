# Amendment A: every catalog drawing card has a guide (2026-11-27)

Code not committed. Synthetic data only; no GPU or model used.

## What was added

- 220 recipes (110 subjects at two levels): 300 in all, 150 subjects. The 156 different cards of the 18 catalog topics
  all find a recipe; toy train, toy car and the school bus card use the train, car and bus recipes.
- Name matching (`recipe_guide.py`):
  - Of two names that share words, the one with more words wins; if as long, the one that ends later
    ("cái cây cầu" is the bridge).
  - Of names that are apart, the first is the subject ("bông hoa trong chậu cây" is the flower).
  - A list of look-alike names gets no picture ("xe máy xúc", "con sáo", "nàng tiên cá", "bóng đèn", "cầu thang",
    "đèn lồng", "áo dài" and others).
- The shoes recipe is titled "Vẽ chiếc giày": it draws one shoe.

## Pictures for the owner's review

Drawn from the data by `render_batches.py` (not app screenshots), per batch `*_finished.png`, `*_beginner.png`,
`*_simple.png`.

| Batch | Subjects |
|---|---|
| `batch4_sky_nature` (25) | leaf to beetle: nature, sky, space, weather, nest, three insects |
| `batch5_tales_toys` (16) | fairy tales and toys |
| `batch6_home_kitchen` (18) | things at home and in the kitchen |
| `batch7_food_school` (17) | food and school |
| `batch8_town_farm` (16) | neighbourhood and farm |
| `batch9_clothes_music` (18) | clothes and music |

Claude looked at the finished pictures of every batch and reshaped the beginner banana, corn, street lamp and dress
afterwards. Step-by-step sheets of these six batches were drawn but not looked at one by one. **The owner has not
judged any picture.** Weaker in Claude's view: banana 3 to 5 (thin), socks 3 to 5, shoes 3 to 5, dress 3 to 5.

## Checks

- 393 tests pass (recipe rules, all 300 files against their level rules, every catalog card finds its own recipe,
  look-alike names, guide service and route). Ruff passes on the changed Python files. Security validator passed.
- Rebuilt API container: loads 300 recipes; a guide built for all 162 card entries at both levels. (That run was
  before the last two picture edits; after them the container loaded the 300 recipes again.)
- Emulator: the water bottle guide (new, drawn with rectangles) was opened from its card, steps 1 and 5 of 5.
  No other new subject was opened on the device.
- App code did not change; app tests were not run again.
- `tests/unit/test_parent_topic_suggestions.py` has 7 failing tests. This work does not touch that test, the service,
  the catalog or the route; the tests call an older signature of the service.

## Limits

- A topic or object typed by the adult that is not in the library still answers "no guide" (phase 3, not approved).
- One-word names match only when the text is that name; the look-alike list covers the cases found, not all.

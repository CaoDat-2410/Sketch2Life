# Phases 0 and 1: recipes and display (2026-11-27)

Code not committed. Synthetic data only; no GPU or model used.

## What was built

| Part | Where |
|---|---|
| Recipe rules, path builder, level checks | `backend/src/sketch2life/domain/drawing_recipe.py` |
| 8 recipes (chicken, butterfly, turtle, dog at two levels) | `backend/src/sketch2life/resources/drawing_recipes/` |
| Topic matching and guide building | `backend/src/sketch2life/infrastructure/svg/recipe_guide.py` |
| Parent route uses only the recipes; level passed through | `parent_svg_guide.py`, `parent_ai.py`, contract method `AUTHORED_SHAPE_RECIPE_V1` |
| App: start dot, arrow, number, dashed new strokes, one stroke after another, replay | `ProgressiveSvgGuide.tsx`, `domain/svgGuide.ts` |
| App: level from the profile age, adult can switch; chosen drawing subject looked up first | `SketchGuideScreen.tsx`, `useParentController.ts`, `sketchGuideFlow.ts` |

## Checks

- Recipe, library, guide service and guide route tests pass (86 in the group run); app tests 319 passed, 5 failed
  (`parentSrsBehavior`, failing before this work); type check clean.
- Inside the rebuilt API container the chicken and dog guides build and an unrelated topic returns none.
- `recipes_beginner.png`, `recipes_simple.png`: every step drawn from the data by `render_recipes.py`. These are not
  app screenshots. Claude looked at them and reshaped the beginner dog; **the owner has not judged them**.

## Differences from the plan

- A stroke inside the box of an earlier part counts as attached (needed for eyes inside open outlines).
- The finished picture is not shown beside the last step for recipes (it would repeat the same drawing).
- Openclipart, OpenMoji and Arcadia files stay in the repository; the Parent route no longer uses them.

## Seen on the emulator (`../M1_device/`, the same day)

Dog guide opened from the drawing session (topic animals, chosen subject), child profile of 4 years:

- Level 3 to 5 chosen from the age; start dot, arrow and dashed new stroke show; the finished picture of the older level
  reads as a dog.
- Strokes draw one after another and "Xem lại cách vẽ" replays them (screen recording, `animation_frames_before_fixes.png`).
- Switching to 6 to 10 and back loads the other recipe; on this slow emulator it took a few seconds.
- Three defects found and fixed, then checked again on the device: the dashed eye dot looked like a horseshoe (dots are
  solid now); a single "1" showed beside a step with one marked stroke (numbers need two); the selected level looked
  disabled. The recipe notice was shortened to one line.

## Not verified

- Chicken, butterfly and turtle on the device.
- Whether children draw better with these guides (not measured, plan section 6).

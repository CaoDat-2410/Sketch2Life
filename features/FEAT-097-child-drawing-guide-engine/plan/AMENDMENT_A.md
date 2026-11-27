# Plan Rev 1, amendment A: a recipe for every catalog drawing card (2026-11-27)

## Why

The Parent app suggests drawing cards from `parent_topic_catalog_vi_v2`: three of 18 topics, then three of that topic's
nine cards, rotated evenly, so every card can be offered. After phase 2 only 46 of the 156 different cards had a guide.

## Scope

- Write recipes at both levels for the 110 cards without one, in the existing format and level rules.
- Toy train, toy car and the school bus card keep using the train, car and bus recipes.
- Adjust name matching where the new names would collide, with tests.
- Rebuild the local API; contact sheets per batch for the owner's review.
- Out of scope: topics typed by the adult (phase 3), model or GPU use, app changes, SRS changes, commit.

## Acceptance

1. Every drawing card of all 18 topics finds its own recipe at both levels.
2. Every recipe passes the rules of its level; the library refuses to load otherwise.
3. A name inside a sentence picks the longer or later compound (for example "cái cây cầu" is the bridge).
4. Recipe, matching, service and route tests pass; the API container builds every subject.
5. The owner receives pictures of every new recipe; the owner's judgement is recorded when given.

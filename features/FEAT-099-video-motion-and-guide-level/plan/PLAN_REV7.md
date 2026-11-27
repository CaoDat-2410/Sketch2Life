# FEAT-099 plan, revision 7: a video that fits the child

Rev 5 (templates) and Rev 6 (any subject) stay. This revision decides **which facts, shown how**, from age, interests
and the adult's notes. Research: `../research/PERSONALISATION_RESEARCH.md`. Nothing is built until approved.

## 1. Rule

| Input | May change | May never change |
|---|---|---|
| Age | which facts, wording, templates, counting range, pace | whether a fact is true |
| Interests | the comparison object, the background | which things are true; no extra characters or decoration |
| Curious about | which facts come first | — |
| Leave out | facts, comparisons and backgrounds that show it | — |
| Viewing settings | pace, amount of motion, highlight style, label size | facts |
| Already taught | new facts first, one repeated for memory | — |

## 2. Age profiles (one versioned table, the SRS bands)

Scene, word and fact counts stay as FEAT-098 set them. What differs is the content. Values are proposals.

| | 36–71 months | 72–107 months | 108–120 months |
|---|---|---|---|
| Goal | name, look, count | what a part does, compare | why it works, compare two things |
| Fact aspects first | what it is, parts, colour and count, home | part and job, use, how it moves, size | cause and result, growth or change, size with numbers |
| Templates | name, count, part-job, move, recap | + use, compare, change | + cause chain (new) |
| Count shown | up to 5 (to 59 months), up to 10 after | up to 20 | what the picture can hold, numbers as labels |
| Compare | bigger, smaller, more, fewer | against a familiar thing | numbers with units, only from a checked source |
| Words | one new word per scene, said twice | new word with a short meaning | the proper term, then why |
| Sentences | one idea, at most 8 words (target) | one idea | may join cause and result |
| Screen | picture and subtitle | + key word large | + key word and one number |
| Pace | slowest, one thing moving | one thing moving | one thing moving, shorter holds |

The writing model gets these rules for its band, and code checks what it can (word and sentence length, count limit,
templates, number of cause or compare facts).

## 3. What the adult gives

All optional, all off until chosen, all editable and deletable.

| Field | Form | Stored | Leaves the backend |
|---|---|---|---|
| Interests | chips, about 20 (adds vehicles, space, dinosaurs, sport, stories, cooking, machines). Typed text only **suggests** chips; only ticked ones count | profile revision | up to 8 chips, as today |
| Leave out | chips: dark, loud scenes, large animals, insects, deep water, storms, others as found | profile revision | only the excluded topic names, no reason (needs an ADR) |
| Viewing settings | switches: slower, calmer motion, larger text, highlight without relying on colour | profile revision | never (used by the renderer) |
| Curious about today | one chip per video: how it moves, what its parts do, where it lives, what it is for, how it grows, how big | run snapshot | only through the facts chosen |
| Free notes and observations | kept for the adult | profile revision | never |

No diagnosis field and no guessing from behaviour (BR-20). The app words these as choices about the video.

Food and eating are not offered as a "curious about" chip: the current safety rule keeps them out of facts.

## 4. Choosing the facts (CPU, deterministic)

1. Pool: checked facts for the subject (card, or Rev 6 tiers), each tagged with youngest and oldest band, aspect,
   whether it depends on colour, and topics.
2. Remove: wrong age; anything in "leave out"; colour-dependent facts when that switch is on.
3. Order: curious-about aspect first (one or two facts), then not yet taught, then parts seen in the drawing.
4. Interest: pick the background, and a comparison only from an **approved comparison list** (a comparison is a claim
   too). No match means no comparison.
5. Drafted facts (no card) follow the same tags; a fact without tags is treated as for the band it was drafted for.

At script review the adult sees one line per choice, for example "5 tuổi: đếm đến 5", "thích xe cộ: nền công trường",
"bỏ qua: tiếng to", and can switch any of them off. A new video rewrites the script from the new choices.

## 5. Optional: an invitation to look or count

For 36–71 months, one pause of about 1.5 s: "Mình cùng đếm nhé", then the answer on screen. Today's script rule
forbids asking the child anything (approved in FEAT-094), so **this needs the owner's decision**. Without it the recap
only repeats.

## 6. Data and consent

- A personalisation consent screen by the adult: what is used, where it is processed, off by default, one tap to remove.
- The video's record keeps the chip IDs and fact IDs used, no free text.
- Before release, a legal check of: viewing settings and "leave out" as sensitive data; consent of a child aged 7 or
  more; processing on a cloud GPU outside Vietnam. These apply partly to today's product too. Not legal advice.

## 7. Work packages

| # | Package | Needs | GPU |
|---|---|---|---|
| P0 | Fix the interest filter (accents, punctuation, wider list); test on the 12 sentences | nothing; works in today's product | 0 |
| P1 | Age profile table, band writing rules and checks | works with Rev 2 or Rev 5 (template gating only Rev 5) | 0 |
| P2 | Chips, "leave out", viewing settings: contracts, migration, app screen, consent | ADR; legal check before release | 0 |
| P3 | Fact tags, selection, history, "this video used" lines | P1, P2 | 0 |
| P4 | Card content: about 4 facts a card for the two older bands (about 160) and the comparison list; owner or curator approves | cards are all still DRAFT | 0 |
| P5 | Test: 3 drawings × 3 profiles (4, 7, 10 years, different choices) = 9 videos | the engine of Rev 5 | about 18 to 27 L40S min (estimate at 2 to 3 a video) |

Order: P0 and P1 first (they help the current videos), then the Rev 5/6 engine, then P2 to P5. P5 replaces part of the
Rev 5/6 test rather than adding a separate build; together the estimate rises to about 60 L40S minutes (cap 75, about
2.5 USD at an unverified 2 USD an hour).

## 8. Acceptance

1. The 12 sample sentences give the expected chips, with no accent mix-up (automated).
2. Same subject, three ages: facts, wording, counting range and templates differ as in section 2 (automated, no GPU).
3. Only interests differ: the fact list is identical; only comparison and background differ (automated).
4. A "leave out" topic appears in no sentence or picture (automated check, then the owner).
5. The model request holds no name, free text, viewing setting or history (automated payload test).
6. Everything used is listed to the adult and can be switched off; nothing is on by default.
7. Of the 9 videos the owner can say which age each is for in at least 8, and finds no false statement.

## 9. Limits

- Research support is mostly from older learners; no test with children is planned here.
- Content is the main cost: new facts and comparisons need a person's approval.
- Chips cannot express everything in a note; what does not fit stays with the adult.
- Age values (counting range, sentence length) are proposals without a measured basis for narrated video.

# FEAT-099 plan, revision 6: any subject, also one nobody prepared

Rev 5 stays (templates, pictures, layers, gates). This revision adds the path for a subject without a profile or card.
Research: `../research/UNKNOWN_SUBJECT_RESEARCH.md`. Nothing is built until approved.

## 1. Promise

Every drawing gets a video. It never states a fact that nobody and nothing checked, and it never waits on a model
getting a part right.

## 2. Sorting the subject

After the adult confirms the name, the story model sorts it into one of four kinds (fixed choices; the adult sees the
choice and can change it):

| Kind | Examples | Facts from | Notes |
|---|---|---|---|
| known | the suggested subjects and carded names, with synonyms | the card | Rev 5 as it is |
| new real thing | dinosaur, crane, octopus robot arm | source first (section 3) | marked until approved |
| invented | unicorn, a cat with wings, a monster | the drawing and the story | said as story ("in this story"), never as science |
| people | me, my family | the drawing only | no facts about real persons; no names stored beyond today's rules |

Unsure counts as invented: the floor.

## 3. Facts in three tiers

| Tier | What | Always available | Check |
|---|---|---|---|
| F1 drawing | colours, shapes, size, parts the adult named, counts of those | **yes** | read from pixels and the adult's taps |
| F2 source | a few facts from a stored copy of Wikidata and Vietnamese Wikipedia, rewritten for the age | only if an entry matches | each sentence must follow from the source text (model check), then the adult approves, source shown |
| F3 adult | the adult's own lesson notes, or their edits | if given | the adult is the author |

A video needs at least three facts: F2 and F3 first, F1 fills up. No source and no notes gives an observation lesson
(colours, counting, shapes, where the child put things), which suits young children and cannot be false. Nothing about
the child is sent anywhere: the source copy is local.

## 4. Parts: the adult points, the code cuts

At script review the app shows the drawing with the pieces found by shape. **Optional:** the adult taps a piece and
picks its name from a short list (leg, wing, wheel, tail, head, fin, eye, other). A mask is cut from the tap (SAM 2.1
point prompt). Then:

- named parts pass the Rev 4 gates and may move or be counted;
- the vision model's own part guesses are only suggestions drawn on the picture, never used untapped for a new
  subject;
- no tap: the whole drawing moves (L3), and the video is complete.

## 5. Movement and effects

The adult (or the sorter, confirmed) picks how it gets about: walks, flies, swims, rolls, spins, sways, stays. This
chooses the L3 motion and effects. Default: stays, with camera, reveal and circles.

## 6. Pictures

Templates that need only the drawing: name, count, colour and shape, compare with a child outline, whole-object
movement, recap. "Use" and "change" need new stills: made during review, checked by the vision model, shown to the
adult, used only if approved; otherwise the fallback template.

## 7. What is kept for next time

An approved new subject becomes a **draft card for that family only**: name, approved facts with sources, approved
generated pictures, movement choice. No drawing, no child data. Sharing it with other families needs a curator's
review. The app lists new subjects often asked for, as counts of the subject name only, so cards can be written; this
needs the owner's approval as data collection.

## 8. What the adult does, and time

| Subject | Extra steps at review | If skipped |
|---|---|---|
| known | none (approve as today) | — |
| new real | read facts and sources, approve pictures (about a minute, estimate) | observation lesson |
| invented, people | optionally tap parts | whole-drawing motion |

GPU for a new subject: tap masks and a few stills during review (estimate 1 L40S minute more than a known one).

## 9. Added work packages (inside Rev 5)

| # | Package | GPU |
|---|---|---|
| U1 | F1 observation facts and the drawing-only templates, sorter, tests | 0 |
| U2 | Review screen: found pieces, tap to name, movement choice | 0 |
| U3 | Local source copy, fact drafting and checking, source display | about 3 L40S min for checks |
| U4 | Family draft cards and reuse | 0 |
| T | 12 unprepared subjects (4 new real, 4 invented, 2 people, 2 odd), owner watches | about 6 L40S min |

U1 goes first, right after the engine core: it is the floor for everything. GPU total with Rev 5: about 45 L40S minutes
(cap 55, about 1.8 USD).

## 10. Acceptance

1. All 12 unprepared subjects give a complete video, with and without any tap or source.
2. In those videos the owner finds no false statement; every F2 sentence shows its source before approval.
3. A tapped part is cut correctly in at least 8 of 10 taps on the test drawings; a failed cut leaves the part still.
4. An invented subject's video contains no sentence presented as real-world fact.

## 11. Limits

- Without a source or notes, a new subject teaches observation only, not knowledge about the thing.
- Facts approved by a parent are as good as their reading of the source.
- A stored source copy ages and takes work to maintain; coverage of Vietnamese everyday names is unmeasured.
- Tapping is extra work; many adults may skip it.
- Whether SAM cuts crayon parts well from one tap is untested.

# FEAT-099 plan, revision 5: a video that shows each fact

Builds on Rev 4 (layers L1 to L4 and its gates stay); adds the missing core: **what each scene shows to teach its
fact**. Research: `../research/KNOWLEDGE_VIDEO_RESEARCH.md`. Needs the same SRS amendment as Rev 3 section 1. The
drawing-guide part is Rev 1 section 3. Nothing is built until approved.

## 1. The unit of the video

A scene = **one fact** + **one picture template** that shows it + motion (Rev 4 layers) + the voice. The template's
event starts when the word it shows is spoken.

## 2. Picture templates

| Template | Shows | Example | Needs | Falls back to |
|---|---|---|---|---|
| name | what it is, where it lives | circle the subject; its home fades in | subject mask, a place | — |
| part-job | a part and what it does | zoom to the part, light it, show the effect (flower for the proboscis, waves for ears) | part box; effect picture | name the part with a circle |
| count | how many | number each part as counted | parts found, count equal to the fact | part-job |
| move | how it moves | gait, wing beat, wheels (L4) with a trail | parts passing gates | whole-object motion |
| use | eats, helps, is used for | the object arrives, the subject reaches it | object picture | name with the object beside |
| change | sequence, cycle, before and after | season or life stages with a marker; parts grow or fall | stages (parts or pictures) | pictures side by side |
| compare | bigger, faster, heavier | side by side with a child outline; a short race; bars | reference picture | two labelled pictures |
| recap | asks, waits, answers | "how many legs?" pause, then the count | earlier events | — |

One visual idea per sentence; no decoration that moves while a fact is being shown.

## 3. Who decides what is shown

- **Knowledge cards (241 facts):** each fact gets a `visual` entry (template, parts, pictures, trigger words), written
  into the card and reviewed with it. The card is the authority.
- **Drafted or lesson facts:** the story model picks a template and fills its slots from fixed choices. Code rejects
  what cannot be shown (a count that does not match the parts found, an unknown picture) and uses the fallback.
- The adult sees, at script review, a still picture of each scene (CPU, seconds) next to its sentence, with "drafted by
  AI" marks as today. What is approved is what the video shows. This extends the SRS storyboard approval.

## 4. Pictures

1. The child's own drawing and its parts.
2. A **picture library** in crayon style: made once on the GPU for the cards' facts (estimate 120 to 150 pictures),
   each checked (question check by the vision model, then a person), stored with source, prompt, model and licence.
3. On demand for custom subjects: a few stills during script review, checked the same way, shown to the adult; without
   approval the fallback template is used.

Before building the library, the image model's licence is checked (research section 5).

## 5. Where the GPU is used

| Step | GPU |
|---|---|
| Painted background, subject mask, part boxes (during review) | yes, as today plus parts |
| Library pictures | once, offline |
| Pictures for custom subjects | a few stills, during review |
| Motion, templates, captions, assembly | **none** (CPU) |

## 6. Gates

Rev 4 gates, plus per scene: the template event begins within 0.5 s of its trigger word; counts equal the fact; every
picture used is approved; text and numbers do not cover the subject's face; at most one template event at a time. A
failed gate uses the fallback column, never an unchecked picture. The share of scenes on their intended template is
reported.

## 7. Work packages

| # | Package | GPU |
|---|---|---|
| W0 | SRS amendment draft; licence check of the image model; owner sign-off | 0 |
| W1 | Engine core and Rev 4 layers L1 to L3 | 0 |
| W2 | Templates name, part-job, count, use, change, compare, recap; timing to words; gates | 0 |
| W3 | Visual entries for the first 12 cards (about 70 facts); library pictures for them | about 12 L40S min |
| **T1** | **The owner watches 12 videos muted and with sound** | 0 |
| W4 | L4 parts (legs, wheels, swim, wings, spin) and the move template | mask job about 5 L40S min |
| W5 | Story model template choice, review stills in the app, pipeline switch | 0 |
| W6 | The other 28 cards and their pictures; drawing guide (one level) | about 15 L40S min |
| T2 | One video through the app | about 4 L40S min |

GPU to build and test: about 36 L40S minutes (cap 45, about 1.5 USD), in three batched jobs. Per product video:
estimate 2 to 3 L40S minutes (background, masks, checks), measured in T2.

## 8. Acceptance

1. **Muted test:** for each of the 12 first cards, the owner, watching without sound, can say what at least 4 of every
   5 scenes teach.
2. Every fact scene shows its template event at its word; the share on the intended template is at least 80% for the 12
   cards, and every other scene shows the fallback cleanly.
3. No picture reaches a video without approval; no count differs from its fact.
4. Rev 4 acceptance items 1, 4, 5 and 6 (every golden drawing gives a video; request to ready at most 2.5 minutes;
   `ltx` selectable; one drawing-guide level).

## 9. Risks and limits

- Template pictures can look repetitive across subjects; the library and recap variation reduce this, not remove it.
- Abstract facts may only be spoken; they are counted and reported.
- Visual entries and pictures are manual review work for the owner (about 241 facts); this is the main cost, not GPU.
- Prototype evidence is one drawing with hand-written choices; part finding on other drawings is unmeasured.
- Whether children learn more from these videos is not tested by this plan; the muted test checks that pictures carry
  the fact.

# FEAT-099 research, sixth pass: a subject nobody prepared (2026-11-27)

## 1. The question

The suggested subjects have profiles and cards. What happens with anything else (a dinosaur, a crane, an invented
creature, "our family")?

## 2. How such a subject reaches the video today

- The custom-subject check asks the story model when the catalogue cannot decide
  (`routers/parent_topic_suggestions.py`), and the adult may rename the recognised subject, so any label can arrive.
- All 40 knowledge cards are still `DRAFT`, so **every** subject today, suggested or not, gets facts drafted by the
  model and checked by the same model (`learning_story.py` `_draft_facts`), marked "AI draft" for the adult.

## 3. What can a model be trusted with on a drawing?

- Part localisation on sketches is weak in the one study read: for small open vision-language models on part-annotated
  object sketches, pointing accuracy 0.23 to 0.46, and 0.06 to 0.11 at a strict overlap; models also do not say that
  an asked part is absent ([arXiv 2610.34037](https://arxiv.org/abs/2610.34037); the grounding numbers come from an
  automated reading of the table, the method reads attention rather than asking for boxes, and our Qwen model was not
  tested). A 2026 benchmark reports limited fine-grained grounding even in large models
  ([EPIC-Bench](https://arxiv.org/pdf/2605.17070)).
- Facts: a small grounded-or-not checker scores about 76% balanced accuracy on its authors' benchmarks
  ([HalluGuard](https://arxiv.org/pdf/2510.00880)). A checker helps; it does not replace a person.
- Sources that can be used without sending anything out: Wikidata dumps (CC0,
  [dataset](https://huggingface.co/datasets/philippesaade/wikidata)); Vietnamese Wikipedia text (CC BY-SA, dump; not
  researched further here).

## 4. Probe: one generic routine on drawings it was not written for

`evidence/unknown_subject_probe.py`, result `evidence/unknown_probe.png`, about 2 s a drawing on the CPU. No knowledge
of the subject: find it, split off thin parts, read colours.

| Drawing | Thin parts found | Colours read | Judgement |
|---|---|---|---|
| Turtle | head side, tail, two feet | black, green, yellow | feet right; parts unnamed |
| Hen (pencil) | two legs, beak, comb piece | black | legs right |
| Butterfly | feelers only; wings stay in the trunk | pink, orange, purple, yellow, blue | colours right; wings missed |
| Bicycle | saddle, handlebar, pedal, flower | red, black | wheels missed; the flower taken as a part |

Four synthetic drawings, judged by the author. Reading: colours and "there are thin pieces here" can be had from any
drawing; **what a piece is cannot**, and large parts are missed. A person naming a part is far more reliable than
either the shapes or a model.

## 5. Reading

A new subject needs an answer for four things, each with a floor that is always true:

| Need | Best source | Floor that cannot be wrong |
|---|---|---|
| What it is | the adult's confirmed name | "your drawing" |
| Facts | a trusted source, then the adult's approval | what is in the drawing: colours, shapes, counts the adult confirms |
| Parts | the adult taps and names them | the whole drawing |
| Pictures | new stills, checked and approved | templates that use only the drawing |

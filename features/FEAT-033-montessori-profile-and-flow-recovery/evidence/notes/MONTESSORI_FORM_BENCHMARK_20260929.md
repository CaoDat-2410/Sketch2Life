# Montessori product/form benchmark — 2026-09-29

## Purpose and limitations

Reviewed public documentation and product pages from Montessori Compass, Transparent Classroom, the Association Montessori Internationale (AMI), and the American Montessori Society (AMS) to challenge the current Sketch2Life form design. This is a desk review of public sources, not a hands-on audit of authenticated vendor accounts or a claim that any vendor's interface is a Montessori standard. Vendor feature descriptions are self-reported. Do not copy proprietary curriculum content or assume another product's workflow automatically fits Sketch2Life's SRS.

## What the systems/documentation emphasize

### Montessori Compass

- Its Quick Add lesson record is tied to a real child, date, named lesson, measurable elements/objectives and an assessment level; notes are optional, and entries can be edited. The documented default levels are Presented, Working, and Mastered, with school customization available.
- Its Scope & Sequence materials are searchable, linked to measurable objectives, and described as a flexible framework rather than a rigid checklist.
- Design implication: a progress entry should represent an actual presentation/work/observation and its objective, not a hard-coded “child has progressed” example in a profile form. If Sketch2Life adds history later, it needs an actual event source and an explicit distinction between introduced, practicing, and observed independent mastery; session-only mock examples must not look like known child history.

### Transparent Classroom

- Public product material describes progress as a visual grid across children and lessons, with lesson planning organized by child/day/lesson, on-the-fly recording, observations, and links between photos and lesson progress.
- Its tutorials distinguish lesson planning/recording by classroom level (including Primary/Toddler) and include follow-up notes.
- Design implication: the useful unit is an activity/lesson and its observation in context; users should navigate to relevant work instead of seeing a large unfiltered set of readiness labels.

### AMI and AMS pedagogical references

- AMI guidance says a child's interest does not cancel prerequisite knowledge: explain the prerequisite and offer the prior material; younger children receive more age-appropriate choices, while older children can discuss the reasons for choices.
- AMI's observation guidance calls for objective, non-judgmental notes focused on the child's actions and interactions, with observations informing support/readiness.
- AMS describes individual interests and pace, while the adult guide observes and supports; age/date alone does not establish readiness.
- Design implication: use interest as one adult-reviewed signal, not a diagnostic or override. Preserve prerequisite and readiness gates, state why an activity fits, and distinguish direct observation from adult interpretation. Unknown readiness must not count as “ready.”

## Comparison to the current Sketch2Life form

| Current element | Evidence-based concern | Direction for FEAT-033 |
|---|---|---|
| Fixed interest/dislike chip taxonomy | Makes the adult translate a real observation into the developer's labels. | The owner chose free text for relatively stable preferences declared by the adult; AI proposes only reviewed topic concepts, and the adult confirms/edits them before use. Keep raw text session-only and do not treat preferences as readiness or a diagnosis. |
| Three hard-coded progress examples on child profile | They are not actual recorded lessons or observations; no real child history exists in catalog/session fixture. | Remove from current form. A future progress event must point to an actual selected activity/objective and adult observation; separate it from profile preference input. |
| Twenty readiness chips in one large wall | Detached from a concrete lesson and burdens the adult with catalog terminology. | Ask only criteria relevant to the small age/topic candidate set and record observed state per criterion before final hard filtering/ranking. |
| “Adult supervision available” as a child-profile setting | Conflates a child property with who is present and the concrete activity's supervision requirement. | Confirm an adult is participating in this session; show and enforce candidate-specific supervision, including direct caregiver supervision where SRS requires it. |
| Entire available materials list/search | Can be long and is not tied to a selected candidate. | Keep availability as a safety/feasibility input but progressively disclose only required materials for the bounded candidate set; do not default unknown to available. |

## Sources

- Montessori Compass, “Quick Add Record a Lesson”: https://help.montessoricompass.com/support/solutions/articles/68000030011-quick-add-record-a-lesson
- Montessori Compass, “Montessori Scope and Sequence”: https://www.montessoricompass.com/montessori-scope-and-sequence/
- Montessori Compass Help Center, “Student Cards”: https://help.montessoricompass.com/support/solutions/articles/68000030016-student-cards
- Transparent Classroom, official product page: https://www.transparentclassroom.com/?locale=en&school_id=1571
- Transparent Classroom, official tutorials: https://www.transparentclassroom.com/tutorials?locale=en
- AMI, “Supporting Developmentally Appropriate Choices”: https://montessori-ami.org/questions/supporting-developmentally-appropriate-choices
- AMI, “See, Support, Share: Observation and Intervention” (AMI Voices PDF): https://montessori-ami.org/sites/default/files/downloads/voices/ObservationandIntervention.pdf
- AMS, “What Is Montessori?”: https://amshq.org/about-montessori/press-kit/what-is-montessori/

## Owner-confirmed product semantics and remaining question

The owner confirmed that interests/dislikes are relatively stable preferences declared by the adult, AI-proposed tags must be shown for adult confirmation/editing before use, and recommendations must stay anchored to the confirmed drawing topic (interests only affect ranking among related activities). The readiness question was explained as checking only whether a concrete activity's authored prerequisite has been observed—not a general child score or developmental label. The approved plan specifies: ask only when an activity has a prerequisite; unknown excludes only activities that require it; support counts only if the activity permits it; and other eligible alternatives remain. Example: for a small watering-can activity, ask only whether the adult has observed the child pour/water with the required control.

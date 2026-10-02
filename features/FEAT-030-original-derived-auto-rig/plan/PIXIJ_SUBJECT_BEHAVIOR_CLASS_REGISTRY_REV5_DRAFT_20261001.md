# Subject-family and behavior-class registry — Pixi show plan revision 5 (approved)

- Feature: FEAT-030 original-derived auto-rig, with FEAT-028 topic assets
- Status: APPROVED FOR IMPLEMENTATION — scope authorized; asset and runtime gates remain separate
- Parent: approved plan revision 4, `PIXI_SPRITE_SHOW_AND_AI_MOTION_MATCHING_20261001.md`
- Date: 2026-10-01
- Change type: additive scope proposal; revision 4 remains unchanged and its approval/hash remains intact

## Owner request

Extend the approved Pixi show plan with explicit, reusable subject and movement classes covering
the supported animals, people, plants, vehicles, objects, and scene elements—for example walker,
flyer, swimmer, crawler, slitherer, and roller—so the planner can choose truthful motion and matching
sprite assets instead of treating each drawing as one of a few coarse archetypes.

The owner also approved the visual appearance of all seven generated motion sheets (28 proposed
frames) on 2026-10-01. That approval is visual only. Rights, crop/pivot/loop QA, catalog registration,
renderer support, and runtime eligibility remain separate gates; see FEAT-028 `assets/REVIEW.md`.

## Problem this revision addresses

Revision 4 correctly separates structural rig archetype from locomotion behavior, but its current
behavior examples and compiler mapping are narrow. In the current backend, `pixi_show_compiler.py`
has a closed subject-hint/behavior map and action map; the typed enums and renderer capabilities do
not yet cover a complete, audited taxonomy. The rig archetypes (`bird`, `fish`, `biped`, `flower`,
`rigid`, and others) describe mask/bone layout, not what the subject can do. A bird may fly or walk;
a car may roll; a flower may sway; a person may walk, run, wave, or reach. These dimensions must not
be collapsed into one label.

Source audit: the current Pixi show enum has six behavior classes (`WALKER`, `FLYER`, `SWIMMER`,
`CRAWLER`, `ROLLER`, `STATIONARY`) and nine subject hints. The compiler maps birds/insects/fish,
quadrupeds/bipeds, plants, vehicles, objects, and unknown subjects into those classes. Human gestures,
plant animation, and several scene/object behaviors are not currently first-class motion classes.

## Goal

Create an auditable, versioned registry and coverage matrix that maps every currently supported
subject/topic to (a) a semantic subject family, (b) a structural rig archetype where relevant, and
(c) zero or more truthful behavior capabilities. The planner may recommend only a behavior and
action the validated source masks, renderer, or eligible animation sprite can actually perform.
Static/unknown is a valid honest outcome; “cover all supported topics” must never mean inventing
motion for an unsupported subject.

## Approved registry model

Keep three independent identifiers:

1. `subjectFamilyId`: semantic category derived from the Gate-A-confirmed subject, such as person,
   biped animal, quadruped, bird, fish/aquatic animal, insect, reptile/amphibian, plant, vehicle,
   rigid prop, environmental element, effect, or unknown.
2. `rigArchetypeId`: structural segmentation/skeleton template (for example biped, bird, fish,
   butterfly, flower/tree-branch, rigid, generic-organic, or unknown). It governs mask roles and
   geometry only; it is not an action permission.
3. `behaviorClassId`: a versioned motion capability validated for this subject and show. Candidate
   groups below are proposals, not yet frozen enum values:

| Family | Candidate behavior classes | Example eligible subjects |
|---|---|---|
| Locomotion | `walker.biped`, `walker.quadruped`, `runner`, `hopper`, `flyer`, `glider`, `swimmer`, `crawler`, `slitherer`, `climber` | People and animals, with morphology-specific variants |
| Human/character gestures | `waver`, `reacher`, `dancer`, `turner` | Person/character, only when drawing parts or a reviewed sprite support the action |
| Plant/nature | `swaying_plant`, `growing`, `blooming`, `drifting`, `falling`, `flowing`, `flickering` | Plants and scene elements such as leaves, clouds, water, rain, or fire; only if included in scope |
| Mechanical/object motion | `roller`, `spinner`, `rotator`, `swinger`, `bouncer`, `slider`, `opener_closer` | Vehicles, wheels, balls, doors, toys, and rigid objects with visible/mechanical support |
| Safe terminal | `still`, `unknown`, `unsupported` | Static props, unrecognized subjects, or any class lacking trustworthy motion evidence |

This list should be deduplicated and defined as behavior classes plus bounded action primitives (for
example `flap`, `glide`, `step`, `wave`, `rotate`) rather than one class per species. A behavior may
have bounded variants, such as biped/quadruped gait, without creating separate classes for every
animal. The final registry should remain compact, versioned, and extensible through reviewed catalog
changes—not runtime-created by AI.

## Scope

1. **Inventory and ontology coverage.** Audit Gate-A subject labels/tags, FEAT-030 rig archetypes,
   FEAT-028 catalog entries/tags, and currently supported Pixi primitives. Cover animals, people,
   plants, vehicles, rigid objects, environmental elements, and visual effects currently in the
   supported taxonomy; produce a traceable
   `subject label/topic → subject family → rig archetype (if applicable) → compatible behavior
   classes → evidence/assets required` matrix. Include each current catalog topic, not only the
   seven motion-sheet examples.
2. **Registry contract proposal.** For each class define stable ID/version, plain-language
   definition, eligible/excluded subject families, allowed action primitives, required mask roles
   or animation-ready asset frames, motion bounds, still/unknown behavior, provenance, and test
   fixtures. Separate semantic compatibility from actual renderer readiness.
3. **Readiness state.** Give each class a measured state such as `SUPPORTED_SOURCE_RIG`,
   `SUPPORTED_APPROVED_SPRITE`, `STATIC_ONLY`, `PLANNED`, or `UNSUPPORTED`. Only supported states
   may reach a show plan. A visually approved sprite is not “supported” until rights/catalog gates,
   frame crops/pivots/loop QA, renderer playback, and tests pass.
4. **AI and deterministic enforcement.** AI returns only registry IDs and bounded action/beat IDs.
   The backend verifies Gate-A identity, family/class compatibility, required part-mask quality or
   eligible sprite sequence, and renderer readiness. AI cannot create a class, infer anatomy from a
   supplemental sprite, grant rights, or convert a single-pose static asset into a walk/flap cycle.
   A mismatch returns the existing typed error/reconfirmation outcome; preserve the original drawing.
5. **Complete sprite-motion coverage.** Change the earlier gap-only policy: every non-static motion
   class enabled for AI/Pixi must have at least one usable, reviewed motion-sprite cycle, and every
   supported subject-family/motion pairing must map to a compatible cycle or an explicitly
   documented variant. Create one or more reusable cycles per behavior class and share them across
   compatible subjects; author family/class variants where anatomy, silhouette, style, or action
   makes reuse misleading. The seven visually approved concept sheets cover only initial examples
   (biped/quadruped walking, flying, swimming, crawling, slithering, rolling); they are not complete
   coverage. `STILL`, `UNKNOWN`, and `UNSUPPORTED` remain honest no-motion outcomes and need no
   motion cycle. No motion class may be advertised as supported while its required sequence is
   absent or technically ineligible. New sheets require provenance, technical frame/crop/pivot/loop QA,
   separate visual approval, rights review, catalog registration, and renderer verification before use.
6. **Coverage and regression tests.** Add synthetic fixtures spanning every family and behavior,
   including ambiguous and unsupported labels, multi-capability subjects, unsupported actions,
   absent/invalid masks, static catalog assets, and unknown long-tail topics. No real child drawings
   or personal data in fixtures/evidence.
7. **Versioned integration.** Review whether the behavior registry belongs in a versioned backend
   domain/application contract and how an additive renderer contract consumes it. Do not silently
   change FEAT-018 V1/V2 or existing public contracts; record required ADR/SRS/contract addenda before
   implementation or activation.

## Proposed behavior selection rules

- Gate A remains authoritative for the subject; Gate B remains authoritative for the chosen
  activity/experience. AI may suggest a compatible class and visual beats only within those bounds.
- Keep subject family, rig archetype, behavior class, action primitive, and asset role as distinct
  typed fields; reject cross-field contradictions.
- A subject can have multiple *capabilities* in the registry (for example, a bird can walk and fly),
  but each show/beat must select a single validated action at a time. Whether the runtime plan may
  combine multiple behavior classes in one show is an owner question below.
- Require evidence for the chosen motion: accepted source-derived masks/parts with adequate quality,
  or a rights-cleared, approved animation-ready sprite sequence. Static sprites may enter only as
  static scene companions/props; they do not confer source-rig capabilities.
- If no supported class matches, return a visible typed `NO_SUPPORTED_BEHAVIOR`/existing equivalent
  and preserve the source image; no fake micro-motion, automatic fallback show, or silent subject
  remapping.
- Unknown subjects use a safe `unknown`/still state until adult correction or a reviewed registry
  update. AI cannot expand the registry at runtime.

## Phases and gates

| Phase | Deliverable | Gate |
|---|---|---|
| 0. Owner scope closure | Resolve taxonomy coverage, multi-capability policy, and inclusion of plants/scene effects; freeze revision and hash | COMPLETE — owner decisions and exact-plan approval are recorded in `approvals/TASK_APPROVAL.md` |
| 1. Baseline audit | Subject ontology, rig archetype, behavior enums/compiler, catalog tags, and current renderer capability inventory | Every uncovered topic is listed; no assumptions from sprite names alone |
| 2. Registry and coverage matrix | Versioned class definitions, eligibility matrix, readiness states, mask/asset requirements, typed unknown/static path | Domain/contract review; no frozen-contract change |
| 3. Full sprite-motion coverage | Map the seven approved concepts and determine all additional cycles/variants needed to cover every supported non-static motion class and compatible subject pairing | Visual approval is not technical/legal clearance; no motion class ships without its eligible motion sequence |
| 4. Implementation proposal | Testable domain registry, AI enum/schema updates, deterministic validator/compiler and additive renderer adapter plan, plus a sequenced asset-production/review schedule | Separate explicit task approval and ADR/contract gates |
| 5. Verification | Synthetic compatibility, rejection, multi-capability, static/unknown, frame/capability and Android playback tests | No live activation before privacy, rights, performance, and Android evidence gates |

## Acceptance criteria proposed

- **AC-REG-01:** Every currently supported Gate-A subject label/topic maps to a stable subject family;
  every FEAT-028 catalog entry/topic is mapped to one or more compatible behavior classes or explicitly
  marked static-only/unsupported. There are no silent coverage gaps.
- **AC-REG-02:** Subject family, rig archetype, behavior class, action primitive, and asset role are
  separate fields with versioned definitions and validation rules.
- **AC-REG-03:** The matrix identifies allowed and forbidden combinations for people, supported
  animal groups, plants/nature, vehicles, rigid objects, environmental elements, effects, and unknowns.
- **AC-REG-04:** AI output is restricted to supplied registry IDs; server-side checks independently
  enforce subject compatibility, quality evidence, asset rights/runtime state, and renderer readiness.
- **AC-REG-05:** Every non-static motion class marked supported has at least one rights-cleared,
  catalog-eligible, animation-ready sprite cycle, matching deterministic renderer action template,
  and synthetic regression fixture; unimplemented/uncovered classes cannot be selected. `STILL`,
  `UNKNOWN`, and `UNSUPPORTED` are explicit no-motion outcomes, not animation classes.
- **AC-REG-06:** Unsupported, ambiguous, and unknown subjects preserve the original drawing and
  return an honest typed outcome; no motion class is inferred solely from a sprite or topic keyword.
- **AC-REG-07:** Static assets never count as animation cycles; every supported subject-family /
  motion pairing maps to a valid motion cycle or documented compatible class-level reuse. Every
  sequence has stable per-frame IDs, provenance/hash, crop/pivot/loop QA, separate visual approval,
  rights clearance, catalog registration, and renderer verification.
- **AC-REG-08:** Tests cover every supported class, forbidden combinations, absent/bad masks, asset
  eligibility, Gate-A/B drift, and any approved multi-class show composition.
- **AC-REG-09:** FEAT-018 frozen contracts remain unchanged unless an exact additive contract proposal
  receives its own review/approval; old clients and failure behavior remain covered.
- **AC-REG-10:** Repository security validator passes; no real child media, credentials, or unreviewed
  assets are introduced into runtime or evidence.

## Risks and controls

- **“All kinds” becomes unbounded:** cover the current supported ontology/catalog exhaustively and
  provide a safe unknown path; new families/classes enter only through a reviewed registry update.
- **Semantic label mistaken for movement evidence:** require masks/parts or eligible animation frames;
  a bird label alone does not prove a usable wing rig.
- **Class explosion/overlap:** define reusable class families and explicit action primitives; avoid
  one class per species or duplicate synonyms. Reuse motion cycles where truthful, but author
  family-specific variants when anatomy/action differs; asset coverage must not be reduced to a few
  unrelated representative examples.
- **AI invents incompatible movement:** closed enums, deterministic compatibility matrix, validator,
  and renderer allowlist.
- **Visual approval mistaken for runtime approval:** preserve the separate visual, provenance/rights,
  technical QA, catalog, and runtime gates recorded by FEAT-028.
- **Contract drift:** keep registry/domain planning additive; review versioned FEAT-018/030 contracts
  before any renderer-facing change.

## Owner decisions received — 2026-10-01

1. **Coverage boundary:** cover the complete Gate-A and FEAT-028 taxonomy currently in scope, with a
   reviewed extension path and safe unknown state; do not claim to predefine every imaginable
   creature/object.
2. **Multiple capabilities:** yes. Store all compatible capabilities for a subject (for example,
   bird = flyer + walker; person = walker + runner + waver); AI may select a suitable class per show
   beat, subject to verified masks/assets and renderer support.
3. **Scene elements:** yes. Include plants and relevant non-living scene/effect motion (such as
   flower sway, cloud drift, water flow, and wheel roll), as well as people, animals, and objects;
   use `still/unknown` where movement is unsuitable or unsupported.
4. **Sprite-cycle granularity:** create one or more reusable motion cycles for every non-static
   motion class; reuse them across compatible subjects and add variants where morphology or action
   differs. A unique cycle for every individual catalog entry is not required.

## Approval and implementation boundary

The owner approved this exact revision and hash on 2026-10-01; the record is in
`approvals/TASK_APPROVAL.md`. Approved revision 4 remains unchanged. The implementation record is
`evidence/notes/BEHAVIOR_REGISTRY_IMPLEMENTATION_20261001.md`: the domain registry, all-current-topic
mapping, tests, and draft cycle coverage are implemented locally. The 30 newly generated sheets
remain pending owner visual review. The earlier 28-frame visual approval is not rights clearance,
technical crop/pivot/loop approval, catalog registration, renderer verification, or runtime eligibility.
No frozen FEAT-018 contract, provider configuration, or runtime asset state was changed.

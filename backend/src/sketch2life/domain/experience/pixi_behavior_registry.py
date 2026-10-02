"""Closed FEAT-030 subject/behavior ontology, independent of transport and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SubjectFamilyId(StrEnum):
    PERSON = "person"
    BIPED_ANIMAL = "animal.biped"
    QUADRUPED = "animal.quadruped"
    BIRD = "animal.bird"
    AQUATIC_ANIMAL = "animal.aquatic"
    INSECT = "animal.insect"
    MOLLUSK = "animal.mollusk"
    REPTILE_AMPHIBIAN = "animal.reptile_amphibian"
    PLANT = "plant"
    VEHICLE = "vehicle"
    RIGID_OBJECT = "object.rigid"
    ENVIRONMENT = "environment"
    EFFECT = "effect"
    FANTASY_CREATURE = "fictional_creature"
    UNKNOWN = "unknown"


class RigArchetypeId(StrEnum):
    BIPED = "biped"
    BIRD = "bird"
    FISH = "fish"
    AQUATIC_MAMMAL = "aquatic_mammal"
    BUTTERFLY = "butterfly"
    INSECT = "insect"
    FLOWER = "flower"
    TREE_BRANCH = "tree_branch"
    GENERIC_ORGANIC = "generic_organic"
    RIGID = "rigid"
    UNKNOWN = "unknown"


class BehaviorClassId(StrEnum):
    WALKER_BIPED = "walker.biped"
    WALKER_QUADRUPED = "walker.quadruped"
    WALKER_AVIAN = "walker.avian"
    RUNNER_BIPED = "runner.biped"
    RUNNER_QUADRUPED = "runner.quadruped"
    HOPPER = "hopper"
    FLYER = "flyer"
    GLIDER = "glider"
    SWIMMER = "swimmer"
    CRAWLER = "crawler"
    SLITHERER = "slitherer"
    CLIMBER = "climber"
    WAVER = "waver"
    REACHER = "reacher"
    DANCER = "dancer"
    TURNER = "turner"
    SWAYING_PLANT = "swaying_plant"
    GROWING = "growing"
    BLOOMING = "blooming"
    DRIFTING = "drifting"
    FALLING = "falling"
    FLOWING = "flowing"
    FLICKERING = "flickering"
    ROLLER = "roller"
    ROTATOR = "rotator"
    SWINGER = "swinger"
    BOUNCER = "bouncer"
    SLIDER = "slider"
    OPENER_CLOSER = "opener_closer"


class ActionPrimitiveId(StrEnum):
    STEP = "step"
    RUN = "run"
    WADDLE = "waddle"
    HOP = "hop"
    FLAP = "flap"
    GLIDE = "glide"
    SWIM = "swim"
    CRAWL = "crawl"
    SLITHER = "slither"
    CLIMB = "climb"
    WAVE = "wave"
    REACH = "reach"
    DANCE = "dance"
    TURN = "turn"
    SWAY = "sway"
    GROW = "grow"
    BLOOM = "bloom"
    DRIFT = "drift"
    FALL = "fall"
    FLOW = "flow"
    FLICKER = "flicker"
    ROLL = "roll"
    ROTATE = "rotate"
    SWING = "swing"
    BOUNCE = "bounce"
    SLIDE = "slide"
    OPEN_CLOSE = "open_close"


class MotionReadiness(StrEnum):
    VISUAL_REVIEW_PENDING = "VISUAL_REVIEW_PENDING"
    VISUAL_APPROVED_PENDING_CLEARANCE = "VISUAL_APPROVED_PENDING_CLEARANCE"
    RIGHTS_TECHNICAL_REVIEW_PENDING = "RIGHTS_TECHNICAL_REVIEW_PENDING"
    RUNTIME_ELIGIBLE = "RUNTIME_ELIGIBLE"
    NO_MOTION = "NO_MOTION"


class NoMotionOutcomeId(StrEnum):
    STILL = "still"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class BehaviorDefinition:
    behavior_class_id: BehaviorClassId
    action_primitive_id: ActionPrimitiveId
    eligible_subject_families: frozenset[SubjectFamilyId]
    required_source_roles: frozenset[str]
    cycle_ids: tuple[str, ...]
    readiness: MotionReadiness


@dataclass(frozen=True, slots=True)
class SubjectProfile:
    subject_family_id: SubjectFamilyId
    rig_archetype_id: RigArchetypeId
    behavior_capability_ids: tuple[BehaviorClassId, ...]
    static_only: bool
    mapping_rule_id: str
    no_motion_outcome_id: NoMotionOutcomeId


_PERSON = frozenset({SubjectFamilyId.PERSON})
_BIPED = frozenset(
    {SubjectFamilyId.PERSON, SubjectFamilyId.BIPED_ANIMAL, SubjectFamilyId.RIGID_OBJECT}
)
_QUADRUPED = frozenset({SubjectFamilyId.QUADRUPED, SubjectFamilyId.REPTILE_AMPHIBIAN})
_BIRDS = frozenset({SubjectFamilyId.BIRD})
_INSECTS = frozenset({SubjectFamilyId.INSECT})
_AQUATIC = frozenset(
    {
        SubjectFamilyId.AQUATIC_ANIMAL,
        SubjectFamilyId.REPTILE_AMPHIBIAN,
        SubjectFamilyId.FANTASY_CREATURE,
    }
)
_FLYING_REPTILES = frozenset({SubjectFamilyId.REPTILE_AMPHIBIAN})
_MOLLUSKS = frozenset({SubjectFamilyId.MOLLUSK})
_REPTILES = frozenset({SubjectFamilyId.QUADRUPED, SubjectFamilyId.REPTILE_AMPHIBIAN})
_PLANTS = frozenset({SubjectFamilyId.PLANT})
_SCENERY = frozenset({SubjectFamilyId.ENVIRONMENT, SubjectFamilyId.EFFECT})
_RIGID = frozenset({SubjectFamilyId.RIGID_OBJECT, SubjectFamilyId.VEHICLE})
_FANTASY = frozenset({SubjectFamilyId.FANTASY_CREATURE})


def _definition(
    behavior: BehaviorClassId,
    action: ActionPrimitiveId,
    families: frozenset[SubjectFamilyId],
    roles: frozenset[str],
    *cycle_ids: str,
    readiness: MotionReadiness = MotionReadiness.VISUAL_REVIEW_PENDING,
) -> BehaviorDefinition:
    return BehaviorDefinition(behavior, action, families, roles, tuple(cycle_ids), readiness)


BEHAVIOR_REGISTRY_V1: tuple[BehaviorDefinition, ...] = (
    _definition(
        BehaviorClassId.WALKER_BIPED,
        ActionPrimitiveId.STEP,
        _BIPED,
        frozenset({"leg", "legs"}),
        "motion.walker-child.v2",
        readiness=MotionReadiness.VISUAL_APPROVED_PENDING_CLEARANCE,
    ),
    _definition(
        BehaviorClassId.WALKER_QUADRUPED,
        ActionPrimitiveId.STEP,
        _QUADRUPED | _FANTASY,
        frozenset({"leg", "legs"}),
        "motion.walker-corgi.v2",
        readiness=MotionReadiness.VISUAL_APPROVED_PENDING_CLEARANCE,
    ),
    _definition(
        BehaviorClassId.WALKER_AVIAN,
        ActionPrimitiveId.WADDLE,
        _BIRDS,
        frozenset({"leg", "legs"}),
        "motion.walker-avian.v1",
    ),
    _definition(
        BehaviorClassId.RUNNER_BIPED,
        ActionPrimitiveId.RUN,
        _BIPED,
        frozenset({"leg", "legs"}),
        "motion.runner-biped.v1",
    ),
    _definition(
        BehaviorClassId.RUNNER_QUADRUPED,
        ActionPrimitiveId.RUN,
        _QUADRUPED,
        frozenset({"leg", "legs"}),
        "motion.runner-quadruped.v1",
    ),
    _definition(
        BehaviorClassId.HOPPER,
        ActionPrimitiveId.HOP,
        _QUADRUPED | _INSECTS,
        frozenset({"leg", "legs"}),
        "motion.hopper-rabbit.v1",
        "motion.hopper-frog.v1",
    ),
    _definition(
        BehaviorClassId.FLYER,
        ActionPrimitiveId.FLAP,
        _BIRDS | _INSECTS | _FANTASY | _FLYING_REPTILES,
        frozenset({"wing", "left-wing", "right-wing"}),
        "motion.flyer-songbird.v2",
        "motion.flyer-insect.v1",
        readiness=MotionReadiness.VISUAL_APPROVED_PENDING_CLEARANCE,
    ),
    _definition(
        BehaviorClassId.GLIDER,
        ActionPrimitiveId.GLIDE,
        _BIRDS | _INSECTS | _RIGID | _FANTASY | _FLYING_REPTILES,
        frozenset({"wing", "left-wing", "right-wing"}),
        "motion.glider-bird.v1",
        "motion.glider-aircraft.v1",
    ),
    _definition(
        BehaviorClassId.SWIMMER,
        ActionPrimitiveId.SWIM,
        _AQUATIC | _QUADRUPED | _BIRDS,
        frozenset({"tail", "fin", "body"}),
        "motion.swimmer-goldfish.v1",
        "motion.swimmer-marine.v1",
        "motion.swimmer-marine.v1",
        readiness=MotionReadiness.VISUAL_APPROVED_PENDING_CLEARANCE,
    ),
    _definition(
        BehaviorClassId.CRAWLER,
        ActionPrimitiveId.CRAWL,
        _INSECTS | _MOLLUSKS | _QUADRUPED | _AQUATIC,
        frozenset({"body", "leg", "legs"}),
        "motion.crawler-snail.v2",
        "motion.crawler-insect.v1",
        "motion.crawler-insect.v1",
        readiness=MotionReadiness.VISUAL_APPROVED_PENDING_CLEARANCE,
    ),
    _definition(
        BehaviorClassId.SLITHERER,
        ActionPrimitiveId.SLITHER,
        _REPTILES,
        frozenset({"body", "tail"}),
        "motion.slitherer-snake.v2",
        readiness=MotionReadiness.VISUAL_APPROVED_PENDING_CLEARANCE,
    ),
    _definition(
        BehaviorClassId.CLIMBER,
        ActionPrimitiveId.CLIMB,
        _BIPED | _QUADRUPED | _INSECTS,
        frozenset({"leg", "legs", "arm", "arms"}),
        "motion.climber-character.v1",
    ),
    _definition(
        BehaviorClassId.WAVER,
        ActionPrimitiveId.WAVE,
        _PERSON,
        frozenset({"arm", "left-arm", "right-arm"}),
        "motion.gesture-wave.v1",
    ),
    _definition(
        BehaviorClassId.REACHER,
        ActionPrimitiveId.REACH,
        _PERSON,
        frozenset({"arm", "left-arm", "right-arm"}),
        "motion.gesture-reach.v1",
    ),
    _definition(
        BehaviorClassId.DANCER,
        ActionPrimitiveId.DANCE,
        _PERSON,
        frozenset({"arm", "leg", "legs"}),
        "motion.gesture-dance.v1",
    ),
    _definition(
        BehaviorClassId.TURNER,
        ActionPrimitiveId.TURN,
        _PERSON,
        frozenset({"body", "head"}),
        "motion.gesture-turn.v1",
    ),
    _definition(
        BehaviorClassId.SWAYING_PLANT,
        ActionPrimitiveId.SWAY,
        _PLANTS,
        frozenset({"stem", "branch", "leaf"}),
        "motion.plant-sway.v1",
    ),
    _definition(
        BehaviorClassId.GROWING,
        ActionPrimitiveId.GROW,
        _PLANTS,
        frozenset({"stem", "branch", "leaf"}),
        "motion.plant-grow.v1",
    ),
    _definition(
        BehaviorClassId.BLOOMING,
        ActionPrimitiveId.BLOOM,
        _PLANTS,
        frozenset({"flower", "petal"}),
        "motion.plant-bloom.v1",
    ),
    _definition(
        BehaviorClassId.DRIFTING,
        ActionPrimitiveId.DRIFT,
        _SCENERY | _PLANTS | _RIGID | _AQUATIC,
        frozenset({"root", "body"}),
        "motion.scene-drift.v1",
    ),
    _definition(
        BehaviorClassId.FALLING,
        ActionPrimitiveId.FALL,
        _SCENERY | _PLANTS,
        frozenset({"root", "body"}),
        "motion.scene-fall.v1",
        "motion.effect-fall.v1",
    ),
    _definition(
        BehaviorClassId.FLOWING,
        ActionPrimitiveId.FLOW,
        _SCENERY | _RIGID,
        frozenset({"wave", "stream", "body"}),
        "motion.scene-flow.v1",
    ),
    _definition(
        BehaviorClassId.FLICKERING,
        ActionPrimitiveId.FLICKER,
        _SCENERY,
        frozenset({"effect", "body"}),
        "motion.effect-flicker.v1",
        "motion.lightning-flicker.v1",
    ),
    _definition(
        BehaviorClassId.ROLLER,
        ActionPrimitiveId.ROLL,
        _RIGID,
        frozenset({"wheel", "left-wheel", "right-wheel"}),
        "motion.roller-car.v1",
        readiness=MotionReadiness.VISUAL_APPROVED_PENDING_CLEARANCE,
    ),
    _definition(
        BehaviorClassId.ROTATOR,
        ActionPrimitiveId.ROTATE,
        _RIGID | _SCENERY,
        frozenset({"pivot", "root"}),
        "motion.object-rotate.v1",
        "motion.object-spin.v1",
    ),
    _definition(
        BehaviorClassId.SWINGER,
        ActionPrimitiveId.SWING,
        _RIGID,
        frozenset({"pivot", "root"}),
        "motion.object-swing.v1",
    ),
    _definition(
        BehaviorClassId.BOUNCER,
        ActionPrimitiveId.BOUNCE,
        _RIGID | _SCENERY,
        frozenset({"root", "body"}),
        "motion.object-bounce.v1",
    ),
    _definition(
        BehaviorClassId.SLIDER,
        ActionPrimitiveId.SLIDE,
        _RIGID,
        frozenset({"root", "body"}),
        "motion.object-slide.v1",
    ),
    _definition(
        BehaviorClassId.OPENER_CLOSER,
        ActionPrimitiveId.OPEN_CLOSE,
        _RIGID,
        frozenset({"hinge", "lid", "cover"}),
        "motion.object-open-close.v1",
    ),
)

BEHAVIOR_BY_ID: dict[BehaviorClassId, BehaviorDefinition] = {
    definition.behavior_class_id: definition for definition in BEHAVIOR_REGISTRY_V1
}

_FAMILY_BY_TOPIC_PREFIX: dict[str, tuple[SubjectFamilyId, RigArchetypeId]] = {
    "topic.animal": (SubjectFamilyId.QUADRUPED, RigArchetypeId.GENERIC_ORGANIC),
    "topic.person": (SubjectFamilyId.PERSON, RigArchetypeId.BIPED),
    "topic.plant": (SubjectFamilyId.PLANT, RigArchetypeId.TREE_BRANCH),
    "topic.vehicle": (SubjectFamilyId.VEHICLE, RigArchetypeId.RIGID),
    "topic.effect": (SubjectFamilyId.EFFECT, RigArchetypeId.GENERIC_ORGANIC),
    "topic.weather": (SubjectFamilyId.ENVIRONMENT, RigArchetypeId.GENERIC_ORGANIC),
    "topic.environment": (SubjectFamilyId.ENVIRONMENT, RigArchetypeId.GENERIC_ORGANIC),
    "topic.place": (SubjectFamilyId.ENVIRONMENT, RigArchetypeId.RIGID),
    "topic.food": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.object": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.material": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.imaginative": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.GENERIC_ORGANIC),
    "topic.science-technology": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.dinosaurs-prehistory": (SubjectFamilyId.QUADRUPED, RigArchetypeId.GENERIC_ORGANIC),
    "topic.farm-animals": (SubjectFamilyId.QUADRUPED, RigArchetypeId.GENERIC_ORGANIC),
    "topic.wild-animals": (SubjectFamilyId.QUADRUPED, RigArchetypeId.GENERIC_ORGANIC),
    "topic.ocean-life": (SubjectFamilyId.AQUATIC_ANIMAL, RigArchetypeId.FISH),
    "topic.insects-small-creatures": (SubjectFamilyId.INSECT, RigArchetypeId.BUTTERFLY),
    "topic.music-instruments": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.sports-outdoor-play": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.construction-tools": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.home-kitchen": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.clothing-accessories": (SubjectFamilyId.RIGID_OBJECT, RigArchetypeId.RIGID),
    "topic.celebrations-seasons-creative-play": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
    ),
}

_TOPIC_OVERRIDES: dict[str, tuple[SubjectFamilyId, RigArchetypeId, tuple[BehaviorClassId, ...]]] = {
    "topic.person.child-a.v1": (
        SubjectFamilyId.PERSON,
        RigArchetypeId.BIPED,
        (
            BehaviorClassId.WALKER_BIPED,
            BehaviorClassId.RUNNER_BIPED,
            BehaviorClassId.WAVER,
            BehaviorClassId.REACHER,
            BehaviorClassId.DANCER,
            BehaviorClassId.TURNER,
        ),
    ),
    "topic.person.child-b.v1": (
        SubjectFamilyId.PERSON,
        RigArchetypeId.BIPED,
        (
            BehaviorClassId.WALKER_BIPED,
            BehaviorClassId.RUNNER_BIPED,
            BehaviorClassId.WAVER,
            BehaviorClassId.REACHER,
            BehaviorClassId.DANCER,
            BehaviorClassId.TURNER,
        ),
    ),
    "topic.person.caregiver.v1": (
        SubjectFamilyId.PERSON,
        RigArchetypeId.BIPED,
        (
            BehaviorClassId.WALKER_BIPED,
            BehaviorClassId.WAVER,
            BehaviorClassId.REACHER,
            BehaviorClassId.TURNER,
        ),
    ),
    "topic.person.teacher.v1": (
        SubjectFamilyId.PERSON,
        RigArchetypeId.BIPED,
        (
            BehaviorClassId.WALKER_BIPED,
            BehaviorClassId.WAVER,
            BehaviorClassId.REACHER,
            BehaviorClassId.TURNER,
        ),
    ),
    "topic.person.gardener.v1": (
        SubjectFamilyId.PERSON,
        RigArchetypeId.BIPED,
        (
            BehaviorClassId.WALKER_BIPED,
            BehaviorClassId.REACHER,
            BehaviorClassId.TURNER,
        ),
    ),
    "topic.person.doctor.v1": (
        SubjectFamilyId.PERSON,
        RigArchetypeId.BIPED,
        (
            BehaviorClassId.WALKER_BIPED,
            BehaviorClassId.REACHER,
            BehaviorClassId.TURNER,
        ),
    ),
    "topic.animal.butterfly.v1": (
        SubjectFamilyId.INSECT,
        RigArchetypeId.BUTTERFLY,
        (BehaviorClassId.FLYER, BehaviorClassId.CRAWLER),
    ),
    "topic.animal.cat.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (
            BehaviorClassId.WALKER_QUADRUPED,
            BehaviorClassId.RUNNER_QUADRUPED,
            BehaviorClassId.CLIMBER,
        ),
    ),
    "topic.animal.dog.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.animal.fish.v1": (
        SubjectFamilyId.AQUATIC_ANIMAL,
        RigArchetypeId.FISH,
        (BehaviorClassId.SWIMMER,),
    ),
    "topic.animal.rabbit.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (
            BehaviorClassId.WALKER_QUADRUPED,
            BehaviorClassId.RUNNER_QUADRUPED,
            BehaviorClassId.HOPPER,
        ),
    ),
    "topic.animal.songbird.v1": (
        SubjectFamilyId.BIRD,
        RigArchetypeId.BIRD,
        (BehaviorClassId.FLYER, BehaviorClassId.GLIDER, BehaviorClassId.WALKER_AVIAN),
    ),
    "topic.plant.oak-tree.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.TREE_BRANCH,
        (BehaviorClassId.SWAYING_PLANT, BehaviorClassId.GROWING),
    ),
    "topic.plant.pine-tree.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.TREE_BRANCH,
        (BehaviorClassId.SWAYING_PLANT, BehaviorClassId.GROWING),
    ),
    "topic.plant.sunflower.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.FLOWER,
        (BehaviorClassId.SWAYING_PLANT, BehaviorClassId.GROWING, BehaviorClassId.BLOOMING),
    ),
    "topic.plant.tulip.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.FLOWER,
        (BehaviorClassId.SWAYING_PLANT, BehaviorClassId.GROWING, BehaviorClassId.BLOOMING),
    ),
    "topic.plant.potted-cactus.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.FLOWER,
        (BehaviorClassId.GROWING,),
    ),
    "topic.plant.leafy-vine.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.TREE_BRANCH,
        (BehaviorClassId.SWAYING_PLANT, BehaviorClassId.GROWING),
    ),
    "topic.weather.cloud.v1": (
        SubjectFamilyId.ENVIRONMENT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.weather.raindrops-puddle.v1": (
        SubjectFamilyId.ENVIRONMENT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.FALLING,),
    ),
    "topic.weather.snowflake.v1": (
        SubjectFamilyId.ENVIRONMENT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.FALLING,),
    ),
    "topic.weather.lightning.v1": (
        SubjectFamilyId.EFFECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.FLICKERING,),
    ),
    "topic.environment.lake-reeds.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.TREE_BRANCH,
        (BehaviorClassId.SWAYING_PLANT,),
    ),
    "topic.environment.ocean-wave.v1": (
        SubjectFamilyId.ENVIRONMENT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.FLOWING,),
    ),
    "topic.vehicle.bicycle.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.ROLLER,),
    ),
    "topic.vehicle.car.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.ROLLER,),
    ),
    "topic.vehicle.city-bus.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.ROLLER,),
    ),
    "topic.vehicle.sailboat.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.vehicle.airplane.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.GLIDER,),
    ),
    "topic.vehicle.train.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.ROLLER,),
    ),
    "topic.object.ball.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.BOUNCER, BehaviorClassId.ROLLER),
    ),
    "topic.object.picture-book.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.OPENER_CLOSER,),
    ),
    "topic.object.umbrella.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.OPENER_CLOSER,),
    ),
    "topic.material.wooden-blocks.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.SLIDER,),
    ),
    "topic.material.number-rods.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.SLIDER,),
    ),
    "topic.material.counting-beads.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.SLIDER,),
    ),
    "topic.material.sorting-bowls.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.SLIDER,),
    ),
    "topic.material.pitcher-cup.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.FLOWING,),
    ),
    "topic.material.shape-puzzle.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.SLIDER,),
    ),
    "topic.imaginative.rocket.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.GLIDER,),
    ),
    "topic.imaginative.ringed-planet.v1": (
        SubjectFamilyId.ENVIRONMENT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.ROTATOR,),
    ),
    "topic.imaginative.astronaut.v1": (
        SubjectFamilyId.PERSON,
        RigArchetypeId.BIPED,
        (BehaviorClassId.WALKER_BIPED, BehaviorClassId.WAVER, BehaviorClassId.REACHER),
    ),
    "topic.imaginative.submarine.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.imaginative.dragon.v1": (
        SubjectFamilyId.FANTASY_CREATURE,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.FLYER),
    ),
    "topic.imaginative.mermaid.v1": (
        SubjectFamilyId.AQUATIC_ANIMAL,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.SWIMMER,),
    ),
    "topic.effect.bubbles.v1": (
        SubjectFamilyId.EFFECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.effect.confetti.v1": (
        SubjectFamilyId.EFFECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.FALLING,),
    ),
    "topic.effect.dust-puff.v1": (
        SubjectFamilyId.EFFECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.effect.leaf-swirl.v1": (
        SubjectFamilyId.EFFECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.effect.sparkles.v1": (
        SubjectFamilyId.EFFECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.FLICKERING,),
    ),
    "topic.effect.motion-streaks.v1": (
        SubjectFamilyId.EFFECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.dinosaurs-prehistory.tyrannosaurus.v1": (
        SubjectFamilyId.BIPED_ANIMAL,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_BIPED, BehaviorClassId.RUNNER_BIPED),
    ),
    "topic.dinosaurs-prehistory.triceratops.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.dinosaurs-prehistory.stegosaurus.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED,),
    ),
    "topic.dinosaurs-prehistory.long-neck-dinosaur.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED,),
    ),
    "topic.dinosaurs-prehistory.pteranodon.v1": (
        SubjectFamilyId.REPTILE_AMPHIBIAN,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.FLYER, BehaviorClassId.GLIDER),
    ),
    "topic.dinosaurs-prehistory.dinosaur-footprint.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (),
    ),
    "topic.farm-animals.cow.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.farm-animals.pig.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.farm-animals.sheep.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.farm-animals.horse.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.farm-animals.hen-chick.v1": (
        SubjectFamilyId.BIRD,
        RigArchetypeId.BIRD,
        (BehaviorClassId.WALKER_AVIAN, BehaviorClassId.FLYER),
    ),
    "topic.farm-animals.duck.v1": (
        SubjectFamilyId.BIRD,
        RigArchetypeId.BIRD,
        (BehaviorClassId.WALKER_AVIAN, BehaviorClassId.FLYER, BehaviorClassId.SWIMMER),
    ),
    "topic.wild-animals.elephant.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED,),
    ),
    "topic.wild-animals.lion.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.wild-animals.giraffe.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED,),
    ),
    "topic.wild-animals.monkey.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.CLIMBER),
    ),
    "topic.wild-animals.tiger.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED, BehaviorClassId.RUNNER_QUADRUPED),
    ),
    "topic.wild-animals.bear.v1": (
        SubjectFamilyId.QUADRUPED,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.WALKER_QUADRUPED,),
    ),
    "topic.ocean-life.whale.v1": (
        SubjectFamilyId.AQUATIC_ANIMAL,
        RigArchetypeId.AQUATIC_MAMMAL,
        (BehaviorClassId.SWIMMER,),
    ),
    "topic.ocean-life.dolphin.v1": (
        SubjectFamilyId.AQUATIC_ANIMAL,
        RigArchetypeId.AQUATIC_MAMMAL,
        (BehaviorClassId.SWIMMER,),
    ),
    "topic.ocean-life.sea-turtle.v1": (
        SubjectFamilyId.REPTILE_AMPHIBIAN,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.SWIMMER, BehaviorClassId.WALKER_QUADRUPED),
    ),
    "topic.ocean-life.octopus.v1": (
        SubjectFamilyId.AQUATIC_ANIMAL,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.SWIMMER, BehaviorClassId.CRAWLER),
    ),
    "topic.ocean-life.crab.v1": (
        SubjectFamilyId.AQUATIC_ANIMAL,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.CRAWLER,),
    ),
    "topic.ocean-life.jellyfish.v1": (
        SubjectFamilyId.AQUATIC_ANIMAL,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.SWIMMER, BehaviorClassId.DRIFTING),
    ),
    "topic.insects-small-creatures.bee.v1": (
        SubjectFamilyId.INSECT,
        RigArchetypeId.INSECT,
        (BehaviorClassId.FLYER, BehaviorClassId.CRAWLER),
    ),
    "topic.insects-small-creatures.ladybug.v1": (
        SubjectFamilyId.INSECT,
        RigArchetypeId.INSECT,
        (BehaviorClassId.FLYER, BehaviorClassId.CRAWLER),
    ),
    "topic.insects-small-creatures.caterpillar.v1": (
        SubjectFamilyId.INSECT,
        RigArchetypeId.INSECT,
        (BehaviorClassId.CRAWLER,),
    ),
    "topic.insects-small-creatures.snail.v1": (
        SubjectFamilyId.MOLLUSK,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.CRAWLER,),
    ),
    "topic.insects-small-creatures.frog.v1": (
        SubjectFamilyId.REPTILE_AMPHIBIAN,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.HOPPER, BehaviorClassId.SWIMMER, BehaviorClassId.WALKER_QUADRUPED),
    ),
    "topic.insects-small-creatures.dragonfly.v1": (
        SubjectFamilyId.INSECT,
        RigArchetypeId.INSECT,
        (BehaviorClassId.FLYER, BehaviorClassId.CRAWLER),
    ),
    "topic.sports-outdoor-play.soccer-ball.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.BOUNCER, BehaviorClassId.ROLLER),
    ),
    "topic.sports-outdoor-play.basketball.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.BOUNCER, BehaviorClassId.ROLLER),
    ),
    "topic.sports-outdoor-play.jump-rope.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.SWINGER,),
    ),
    "topic.sports-outdoor-play.playground-swing.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.SWINGER,),
    ),
    "topic.construction-tools.excavator.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.ROLLER, BehaviorClassId.ROTATOR),
    ),
    "topic.construction-tools.tower-crane.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.ROTATOR, BehaviorClassId.SWINGER),
    ),
    "topic.construction-tools.dump-truck.v1": (
        SubjectFamilyId.VEHICLE,
        RigArchetypeId.RIGID,
        (BehaviorClassId.ROLLER,),
    ),
    "topic.home-kitchen.cooking-pot.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.OPENER_CLOSER,),
    ),
    "topic.clothing-accessories.scarf.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.celebrations-seasons-creative-play.autumn-leaf.v1": (
        SubjectFamilyId.PLANT,
        RigArchetypeId.TREE_BRANCH,
        (BehaviorClassId.DRIFTING, BehaviorClassId.FALLING),
    ),
    "topic.celebrations-seasons-creative-play.balloons.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.GENERIC_ORGANIC,
        (BehaviorClassId.DRIFTING,),
    ),
    "topic.celebrations-seasons-creative-play.gift-box.v1": (
        SubjectFamilyId.RIGID_OBJECT,
        RigArchetypeId.RIGID,
        (BehaviorClassId.OPENER_CLOSER,),
    ),
}


def behavior_definition(behavior_class_id: BehaviorClassId) -> BehaviorDefinition:
    """Return the one closed definition; unknown IDs are not accepted by this domain API."""
    return BEHAVIOR_BY_ID[behavior_class_id]


def behavior_is_compatible(
    subject_family_id: SubjectFamilyId,
    behavior_class_id: BehaviorClassId,
) -> bool:
    definition = BEHAVIOR_BY_ID.get(behavior_class_id)
    return definition is not None and subject_family_id in definition.eligible_subject_families


def is_behavior_runtime_selectable(topic_id: str, behavior_class_id: BehaviorClassId) -> bool:
    """Require both an exact topic capability and completed sprite/provenance gates."""
    profile = topic_subject_profile(topic_id)
    definition = BEHAVIOR_BY_ID.get(behavior_class_id)
    return (
        behavior_class_id in profile.behavior_capability_ids
        and definition is not None
        and profile.subject_family_id in definition.eligible_subject_families
        and definition.readiness is MotionReadiness.RUNTIME_ELIGIBLE
        and bool(definition.cycle_ids)
    )


def topic_subject_profile(topic_id: str) -> SubjectProfile:
    """Resolve a catalog topic through a closed prefix map and reviewed per-topic exceptions."""
    override = _TOPIC_OVERRIDES.get(topic_id)
    if override is not None:
        family, rig, behaviors = override
        return SubjectProfile(
            family,
            rig,
            behaviors,
            not behaviors,
            "exact-topic-v1",
            NoMotionOutcomeId.STILL,
        )

    prefix = ".".join(topic_id.split(".")[:2])
    family_rig = _FAMILY_BY_TOPIC_PREFIX.get(prefix)
    if family_rig is None or not topic_id.startswith("topic."):
        return SubjectProfile(
            SubjectFamilyId.UNKNOWN,
            RigArchetypeId.UNKNOWN,
            (),
            True,
            "safe-unknown-v1",
            NoMotionOutcomeId.UNKNOWN,
        )
    family, rig = family_rig
    return SubjectProfile(
        family,
        rig,
        (),
        True,
        "closed-prefix-static-v1",
        NoMotionOutcomeId.STILL,
    )


def supported_behavior_ids() -> tuple[BehaviorClassId, ...]:
    """List classes whose sprite and rights gates are complete; currently intentionally empty."""
    return tuple(
        definition.behavior_class_id
        for definition in BEHAVIOR_REGISTRY_V1
        if definition.readiness is MotionReadiness.RUNTIME_ELIGIBLE
    )


__all__ = [
    "ActionPrimitiveId",
    "BEHAVIOR_BY_ID",
    "BEHAVIOR_REGISTRY_V1",
    "BehaviorClassId",
    "BehaviorDefinition",
    "MotionReadiness",
    "NoMotionOutcomeId",
    "RigArchetypeId",
    "SubjectFamilyId",
    "SubjectProfile",
    "behavior_definition",
    "behavior_is_compatible",
    "is_behavior_runtime_selectable",
    "supported_behavior_ids",
    "topic_subject_profile",
]

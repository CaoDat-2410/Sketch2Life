"""FEAT-030 auto-rig application services."""

from .rig_builder import (
    build_animation_plan,
    build_template_rig,
    classify_archetype,
    validate_rig_geometry,
)
from .service import AutoRigPackageUnavailable, AutoRigService

__all__ = [
    "build_animation_plan",
    "build_template_rig",
    "classify_archetype",
    "validate_rig_geometry",
    "AutoRigPackageUnavailable",
    "AutoRigService",
]

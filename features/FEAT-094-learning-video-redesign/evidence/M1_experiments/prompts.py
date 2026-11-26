"""Actions and the new motion-only prompt used by the phase 1 experiments (no third-party imports)."""

BIKE = (
    "The red crayon bicycle rolls slowly to the right across the grass, both black wheels turning steadily, "
    "while the small yellow flower beside the back wheel nods gently."
)
CHICK = (
    "The yellow crayon chick hops forward once and dips its beak down toward the grass, then lifts its head, "
    "its three tail feathers swaying."
)


def motion_prompt(action: str) -> str:
    """The new motion-only prompt: one paragraph, action first, no prohibitions, static camera."""

    return (
        f"{action} The movement is smooth and continuous from the first moment to the last. The drawing keeps its "
        "crayon strokes, colours and paper texture exactly as in the first frame. The camera remains static throughout."
    )
